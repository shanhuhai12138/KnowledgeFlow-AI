package cn.knowledgeflow.module.knowledge.controller.admin.stat;

import cn.knowledgeflow.framework.common.pojo.CommonResult;
import cn.knowledgeflow.module.knowledge.controller.admin.stat.vo.StatOverviewRespVO;
import cn.knowledgeflow.module.knowledge.dal.mysql.document.DocumentMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.querylog.QueryLogMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;

import static cn.knowledgeflow.framework.common.pojo.CommonResult.success;

/**
 * 看板统计（T3.3 前端看板数据源，聚合 kb_document / kb_query_log / kb_knowledge_base）
 *
 * 多租户隔离：原生 @Select 由框架 TenantLineInnerInterceptor 自动追加 tenant_id 条件。
 */
@Tag(name = "管理后台 - 知识库统计（看板）")
@RestController
@RequestMapping("/knowledge/stat")
@Validated
public class StatController {

    @Resource
    private DocumentMapper documentMapper;
    @Resource
    private QueryLogMapper queryLogMapper;
    @Resource
    private KnowledgeBaseMapper knowledgeBaseMapper;

    @GetMapping("/overview")
    @Operation(summary = "看板总览：文档数/查询数/LLM 调用数/知识库数")
    public CommonResult<StatOverviewRespVO> getOverview() {
        StatOverviewRespVO vo = new StatOverviewRespVO();
        vo.setDocumentCount(documentMapper.selectCount(null).intValue());
        vo.setQueryCount(queryLogMapper.selectCountAll().intValue());
        vo.setLlmCallCount(vo.getQueryCount()); // LLM 调用暂以查询次数近似
        vo.setKbCount(knowledgeBaseMapper.selectCountAll().intValue());
        return success(vo);
    }

    @GetMapping("/trend")
    @Operation(summary = "N 日搜索趋势（按日计数）")
    @Parameter(name = "days", description = "天数", example = "7")
    public CommonResult<List<Map<String, Object>>> getTrend(@RequestParam(value = "days", defaultValue = "7") Integer days) {
        return success(queryLogMapper.selectTrend(Math.min(days, 90)));
    }

    @GetMapping("/doc-types")
    @Operation(summary = "文档类型分布（按 file_type 分组）")
    public CommonResult<List<Map<String, Object>>> getDocTypes() {
        return success(documentMapper.selectDocTypes());
    }

    @GetMapping("/hot")
    @Operation(summary = "热门查询 Top")
    @Parameter(name = "limit", description = "条数", example = "5")
    public CommonResult<List<Map<String, Object>>> getHot(@RequestParam(value = "limit", defaultValue = "5") Integer limit) {
        return success(queryLogMapper.selectHot(Math.min(limit, 50)));
    }

}
