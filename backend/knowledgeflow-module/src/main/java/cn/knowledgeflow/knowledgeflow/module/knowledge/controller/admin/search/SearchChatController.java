package cn.knowledgeflow.module.knowledge.controller.admin.search;

import cn.knowledgeflow.framework.common.pojo.CommonResult;
import cn.knowledgeflow.framework.security.core.util.SecurityFrameworkUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.search.vo.ChatReqVO;
import cn.knowledgeflow.module.knowledge.controller.admin.search.vo.SearchReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.querylog.QueryLogDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.querylog.QueryLogMapper;
import cn.knowledgeflow.module.knowledge.framework.ai.AiServiceProperties;
import cn.knowledgeflow.module.knowledge.service.kb.KnowledgeBaseService;
import cn.knowledgeflow.module.knowledge.service.aiconfig.AiApiConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ExecutorService;

import static cn.knowledgeflow.framework.common.pojo.CommonResult.error;
import static cn.knowledgeflow.framework.common.pojo.CommonResult.success;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.AI_SERVICE_ERROR;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.AI_SERVICE_UNAVAILABLE;

/**
 * 搜索与问答 API（任务书 T2.4）
 *
 * 统一入口转发 Python AI 服务（T4.0 契约）：
 *   POST /api/search        → POST {base-url}/ai/search
 *   POST /api/chat          → POST {base-url}/ai/chat
 *   GET  /api/chat/stream   → GET  {base-url}/ai/chat/stream（SSE 流式转发）
 * Python 未启动时返回 HTTP 503 + 明确错误信息；查询日志落 kb_query_log。
 */
@Slf4j
@Tag(name = "管理后台 - 搜索与问答（AI 转发）")
@RestController
@RequestMapping("/api")
@Validated
public class SearchChatController {

    @Resource
    private RestTemplate aiServiceRestTemplate;
    @Resource
    private AiServiceProperties aiServiceProperties;
    @Resource
    private KnowledgeBaseService knowledgeBaseService;
    @Resource
    private QueryLogMapper queryLogMapper;
    @Resource(name = "aiStreamExecutor")
    private ExecutorService aiStreamExecutor;
    @Resource
    private AiApiConfigService aiApiConfigService;

    @PostMapping("/search")
    @Operation(summary = "语义搜索（转发 Python /ai/search，落 kb_query_log）")
    public ResponseEntity<CommonResult<Object>> search(@Valid @RequestBody SearchReqVO reqVO) {
        knowledgeBaseService.validateViewPermission(reqVO.getKbId());
        long start = System.currentTimeMillis();
        try {
            ResponseEntity<Object> resp = aiServiceRestTemplate.postForEntity(
                    aiServiceProperties.getBaseUrl() + "/ai/search",
                    new org.springframework.http.HttpEntity<>(reqVO, buildAiHeaders()), Object.class);
            Object body = resp.getBody();
            int hitCount = parseHitCount(body, "results");
            saveQueryLog(reqVO.getKbId(), reqVO.getQuery(), start, hitCount);
            return ResponseEntity.ok(success(body));
        } catch (ResourceAccessException e) {
            log.warn("[search][AI 服务不可达 kbId({})]", reqVO.getKbId(), e);
            return ResponseEntity.status(503)
                    .body(error(AI_SERVICE_UNAVAILABLE, e.getMessage()));
        } catch (org.springframework.web.client.HttpStatusCodeException e) {
            return ResponseEntity.status(e.getStatusCode().value())
                    .body(error(AI_SERVICE_ERROR, e.getStatusCode().value(), e.getResponseBodyAsString()));
        }
    }

    @PostMapping("/chat")
    @Operation(summary = "智能问答（转发 Python /ai/chat，落 kb_query_log）")
    public ResponseEntity<CommonResult<Object>> chat(@Valid @RequestBody ChatReqVO reqVO) {
        knowledgeBaseService.validateViewPermission(reqVO.getKbId());
        long start = System.currentTimeMillis();
        try {
            ResponseEntity<Object> resp = aiServiceRestTemplate.postForEntity(
                    aiServiceProperties.getBaseUrl() + "/ai/chat",
                    new org.springframework.http.HttpEntity<>(reqVO, buildAiHeaders()), Object.class);
            Object body = resp.getBody();
            int hitCount = parseHitCount(body, "sources");
            saveQueryLog(reqVO.getKbId(), reqVO.getMessage(), start, hitCount);
            return ResponseEntity.ok(success(body));
        } catch (ResourceAccessException e) {
            log.warn("[chat][AI 服务不可达 kbId({})]", reqVO.getKbId(), e);
            return ResponseEntity.status(503)
                    .body(error(AI_SERVICE_UNAVAILABLE, e.getMessage()));
        } catch (org.springframework.web.client.HttpStatusCodeException e) {
            return ResponseEntity.status(e.getStatusCode().value())
                    .body(error(AI_SERVICE_ERROR, e.getStatusCode().value(), e.getResponseBodyAsString()));
        }
    }

    @GetMapping("/chat/stream")
    @Operation(summary = "流式问答 SSE（转发 Python /ai/chat/stream，四事件 meta/content/sources/done）")
    @Parameter(name = "sessionId", description = "会话编号", example = "s1")
    @Parameter(name = "kbId", description = "知识库编号", required = true, example = "1")
    @Parameter(name = "message", description = "用户消息", required = true, example = "什么是 RAG？")
    public SseEmitter streamChat(@RequestParam("sessionId") String sessionId,
                                 @RequestParam("kbId") Long kbId,
                                 @RequestParam("message") String message,
                                 HttpServletResponse response) throws IOException {
        knowledgeBaseService.validateViewPermission(kbId);
        // 1. 同步建立与 Python 的连接（失败 → 503 + 明确错误；成功才返回 SseEmitter）
        String url = aiServiceProperties.getBaseUrl() + "/ai/chat/stream"
                + "?sessionId=" + urlEncode(sessionId) + "&kbId=" + kbId + "&message=" + urlEncode(message);
        HttpURLConnection conn;
        try {
            conn = (HttpURLConnection) new URL(url).openConnection();
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(300000); // T6.3：下游 5 分钟读超时，防线程永久阻塞
            conn.setRequestMethod("GET");
            // T7：DB 有配置的 Key 则带 X-API-Key（DB 优先于环境变量）
            String apiKey = aiApiConfigService.getConfigValue("llm");
            if (apiKey != null) {
                conn.setRequestProperty("X-API-Key", apiKey);
            }
            int code = conn.getResponseCode();
            if (code != 200) {
                // 透传 Python 侧的错误详情（如「请配置 API Key」）
                String detail = "ai-service 返回非 200";
                try (java.io.InputStream errorStream = conn.getErrorStream()) {
                    if (errorStream != null) {
                        detail = cn.hutool.core.io.IoUtil.readUtf8(errorStream).trim();
                    }
                } catch (Exception ignore) {
                }
                conn.disconnect();
                writeJsonError(response, code, error(AI_SERVICE_ERROR, code, detail));
                return null;
            }
        } catch (IOException e) {
            log.warn("[streamChat][AI 服务不可达 kbId({})]", kbId, e);
            writeJsonError(response, 503, error(AI_SERVICE_UNAVAILABLE, e.getMessage()));
            return null;
        }
        // 2. 连接成功：开线程逐事件转发
        long start = System.currentTimeMillis();
        SseEmitter emitter = new SseEmitter(300_000L); // 5 分钟超时（T6.3：防残留线程）
        // T6.3：注册释放逻辑，客户端断开/超时/异常时确保 complete 与资源清理
        emitter.onTimeout(() -> {
            log.info("[streamChat][SSE 超时关闭 kbId({})]", kbId);
            emitter.complete();
        });
        emitter.onError(e -> log.warn("[streamChat][SSE 异常关闭 kbId({})] {}", kbId, e.getMessage()));
        emitter.onCompletion(() -> log.info("[streamChat][SSE 完成关闭 kbId({})]", kbId));
        HttpURLConnection finalConn = conn;
        aiStreamExecutor.execute(() -> forwardStream(emitter, finalConn, kbId, message, start));
        return emitter;
    }

    // ==================== 内部方法 ====================

    /**
     * T7：构建转发 Python 的请求头（DB 有配置的 Key 则带 X-API-Key，DB 优先于环境变量）
     */
    private org.springframework.http.HttpHeaders buildAiHeaders() {
        org.springframework.http.HttpHeaders headers = new org.springframework.http.HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        String apiKey = aiApiConfigService.getConfigValue("llm");
        if (apiKey != null) {
            headers.set("X-API-Key", apiKey);
        }
        return headers;
    }

    /**
     * 手动写 JSON 错误响应（配合 SseEmitter 返回类型：失败时无法返回 ResponseEntity，直接写 response）
     */
    private void writeJsonError(HttpServletResponse response, int status, CommonResult<?> result) throws IOException {
        response.setStatus(status);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.getWriter().write(cn.hutool.json.JSONUtil.toJsonStr(result));
    }

    /**
     * 读取 Python SSE 流（event/data 行），逐事件转发给前端；流结束后落 kb_query_log
     */
    private void forwardStream(SseEmitter emitter, HttpURLConnection conn, Long kbId, String message, long start) {
        int hitCount = 0;
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            String event = "message";
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("event:")) {
                    event = line.substring(6).trim();
                } else if (line.startsWith("data:")) {
                    String data = line.substring(5).trim();
                    if ("sources".equals(event)) {
                        hitCount = parseSseHitCount(data);
                    }
                    emitter.send(SseEmitter.event().name(event).data(data, MediaType.APPLICATION_JSON));
                    event = "message";
                } else if (line.trim().isEmpty()) {
                    event = "message";
                }
            }
            emitter.complete();
        } catch (Exception e) {
            log.warn("[forwardStream][SSE 转发中断 kbId({}) message({})]", kbId, message, e);
            emitter.completeWithError(e);
        } finally {
            conn.disconnect();
            saveQueryLog(kbId, message, start, hitCount);
        }
    }

    /**
     * 从 Python 响应 Map 中解析命中数（search→results，chat→sources）
     */
    @SuppressWarnings("unchecked")
    private int parseHitCount(Object body, String key) {
        if (body instanceof Map) {
            Object list = ((Map<String, Object>) body).get(key);
            if (list instanceof java.util.Collection) {
                return ((java.util.Collection<?>) list).size();
            }
        }
        return 0;
    }

    /**
     * 从 SSE sources 事件 data（JSON 数组或对象）解析命中数
     */
    private int parseSseHitCount(String data) {
        try {
            Object parsed = com.fasterxml.jackson.databind.json.JsonMapper.builder().build().readValue(data, Object.class);
            if (parsed instanceof java.util.Collection) {
                return ((java.util.Collection<?>) parsed).size();
            }
            if (parsed instanceof Map) {
                Object sources = ((Map<String, Object>) parsed).get("sources");
                if (sources instanceof java.util.Collection) {
                    return ((java.util.Collection<?>) sources).size();
                }
            }
        } catch (Exception ignore) {
        }
        return 0;
    }

    /**
     * 落 kb_query_log（用户/知识库/查询/耗时/命中数）
     */
    private void saveQueryLog(Long kbId, String queryText, long start, int hitCount) {
        try {
            QueryLogDO log = new QueryLogDO();
            log.setUserId(SecurityFrameworkUtils.getLoginUserId());
            log.setKbId(kbId);
            log.setQueryText(queryText);
            log.setTookMs((int) (System.currentTimeMillis() - start));
            log.setHitCount(hitCount);
            queryLogMapper.insert(log);
        } catch (Exception e) {
            log.warn("[saveQueryLog][落库失败 kbId({})]", kbId, e);
        }
    }

    private String urlEncode(String value) {
        return URLEncoder.encode(value == null ? "" : value, StandardCharsets.UTF_8);
    }

}
