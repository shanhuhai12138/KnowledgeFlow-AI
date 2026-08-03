package cn.iocoder.yudao.module.knowledge.controller.admin.document;

import cn.hutool.core.io.IoUtil;
import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.module.knowledge.controller.admin.document.vo.DocumentPageReqVO;
import cn.iocoder.yudao.module.knowledge.controller.admin.document.vo.DocumentRespVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.document.DocumentDO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.iocoder.yudao.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.iocoder.yudao.module.knowledge.service.document.DocumentService;
import cn.iocoder.yudao.module.system.api.user.AdminUserApi;
import cn.iocoder.yudao.module.system.api.user.dto.AdminUserRespDTO;
import io.minio.GetObjectResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.IOUtils;
import org.springframework.http.MediaType;
import org.apache.commons.lang3.StringUtils;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;

@Slf4j
@Tag(name = "管理后台 - 知识库文档")
@RestController
@RequestMapping("/knowledge/document")
@Validated
public class DocumentController {

    @Resource
    private DocumentService documentService;
    @Resource
    private KnowledgeBaseMapper knowledgeBaseMapper;
    @Resource
    private AdminUserApi adminUserApi;

    @PostMapping("/upload")
    @Operation(summary = "上传文档（存 MinIO + 落库 pending + 投递 doc-pipeline）")
    public CommonResult<DocumentRespVO> uploadDocument(@RequestParam("kbId") Long kbId,
                                                       @RequestParam("file") MultipartFile file,
                                                       @RequestParam(value = "tags", required = false) String tags) {
        DocumentDO document = documentService.uploadDocument(kbId, file, tags);
        return success(convert(document));
    }

    @GetMapping("/page")
    @Operation(summary = "获得文档分页（筛选：KB/格式/状态/文件名）")
    public CommonResult<PageResult<DocumentRespVO>> getDocumentPage(@Validated DocumentPageReqVO pageReqVO) {
        PageResult<DocumentDO> pageResult = documentService.getDocumentPage(pageReqVO);
        return success(convertPage(pageResult));
    }

    @GetMapping("/get")
    @Operation(summary = "获得文档")
    @Parameter(name = "id", description = "文档编号", required = true, example = "1")
    public CommonResult<DocumentRespVO> getDocument(@RequestParam("id") Long id) {
        return success(convert(documentService.getDocument(id)));
    }

    @DeleteMapping("/delete")
    @Operation(summary = "批量删除文档（级联删 MinIO 对象 + documentCount 减一）")
    @Parameter(name = "ids", description = "文档编号列表", required = true)
    public CommonResult<Boolean> deleteDocuments(@RequestParam("ids") List<Long> ids) {
        documentService.deleteDocuments(ids);
        return success(true);
    }

    @GetMapping("/download")
    @Operation(summary = "下载文档（MinIO 流式）")
    @Parameter(name = "id", description = "文档编号", required = true, example = "1")
    public void downloadDocument(@RequestParam("id") Long id, HttpServletResponse response) throws IOException {
        DocumentDO document = documentService.getDocument(id);
        try (GetObjectResponse object = documentService.downloadDocument(id)) {
            response.setContentType(MediaType.APPLICATION_OCTET_STREAM_VALUE);
            String encoded = URLEncoder.encode(document.getFilename(), StandardCharsets.UTF_8.name()).replace("+", "%20");
            response.setHeader("Content-Disposition", "attachment; filename*=UTF-8''" + encoded);
            response.setContentLengthLong(document.getFileSize() == null ? -1 : document.getFileSize());
            IoUtil.copy(object, response.getOutputStream());
            response.getOutputStream().flush();
        } catch (Exception e) {
            log.error("[downloadDocument][下载失败 documentId({})]", id, e);
            response.sendError(500, "下载失败");
        }
    }

    // ==================== DO → VO（契约字段映射） ====================

    private PageResult<DocumentRespVO> convertPage(PageResult<DocumentDO> pageResult) {
        List<DocumentDO> list = pageResult.getList();
        // 批量查 kb 名称 + 上传者昵称
        Set<Long> kbIds = list.stream().map(DocumentDO::getKbId).collect(Collectors.toSet());
        Set<Long> userIds = list.stream().map(DocumentDO::getUploaderId).collect(Collectors.toSet());
        Map<Long, String> kbNames = kbIds.isEmpty() ? Collections.emptyMap()
                : knowledgeBaseMapper.selectBatchIds(kbIds).stream()
                        .collect(Collectors.toMap(KnowledgeBaseDO::getId, KnowledgeBaseDO::getName, (a, b) -> a));
        Map<Long, String> usernames = userIds.isEmpty() ? Collections.emptyMap()
                : adminUserApi.getUserList(userIds).stream()
                        .collect(Collectors.toMap(AdminUserRespDTO::getId, AdminUserRespDTO::getUsername, (a, b) -> a));
        List<DocumentRespVO> voList = list.stream().map(d -> convert(d, kbNames, usernames)).collect(Collectors.toList());
        return new PageResult<>(voList, pageResult.getTotal());
    }

    private DocumentRespVO convert(DocumentDO document) {
        // 单文档接口（上传/get）也做联查：kbName + uploader 用户名
        KnowledgeBaseDO kb = knowledgeBaseMapper.selectById(document.getKbId());
        String kbName = kb == null ? "" : kb.getName();
        String username = String.valueOf(document.getUploaderId());
        AdminUserRespDTO user = adminUserApi.getUser(document.getUploaderId());
        if (user != null && user.getUsername() != null) {
            username = user.getUsername();
        }
        return convert(document, Collections.singletonMap(document.getKbId(), kbName),
                Collections.singletonMap(document.getUploaderId(), username));
    }

    private DocumentRespVO convert(DocumentDO document, Map<Long, String> kbNames, Map<Long, String> usernames) {
        DocumentRespVO respVO = new DocumentRespVO();
        respVO.setId(document.getId());
        respVO.setKbId(document.getKbId());
        respVO.setKbName(kbNames.getOrDefault(document.getKbId(),
                Objects.toString(knowledgeBaseMapper.selectById(document.getKbId()) == null
                        ? "" : knowledgeBaseMapper.selectById(document.getKbId()).getName(), "")));
        respVO.setFilename(document.getFilename());
        respVO.setFileType(document.getFileType());
        respVO.setFileSize(document.getFileSize());
        respVO.setPageCount(document.getPageCount());
        respVO.setStatus(document.getStatus());
        respVO.setUploader(usernames.getOrDefault(document.getUploaderId(),
                Objects.toString(document.getUploaderId(), "")));
        respVO.setTags(splitTags(document.getTags()));
        respVO.setCreatedAt(document.getCreateTime());
        respVO.setUpdatedAt(document.getUpdateTime());
        return respVO;
    }

    /**
     * 逗号分隔标签 → 字符串数组（去空）
     */
    private String[] splitTags(String tags) {
        if (StringUtils.isBlank(tags)) {
            return new String[0];
        }
        return Stream.of(tags.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .toArray(String[]::new);
    }

}
