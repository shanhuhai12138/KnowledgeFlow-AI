package cn.iocoder.yudao.module.knowledge.controller.admin.cleanup;

import cn.iocoder.yudao.framework.common.pojo.CommonResult;
import cn.iocoder.yudao.module.knowledge.service.task.KnowledgeCleanupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.framework.common.pojo.CommonResult.success;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_CLEANUP_TYPE_ERROR;

/**
 * 运行时治理手动触发（T6）
 *
 * 定时任务默认每日 cron 执行；本接口提供运维/验收时手动触发。
 * POST /knowledge/cleanup/run?type=stream|querylog|version|orphan
 */
@Tag(name = "管理后台 - 运行时治理（手动触发）")
@RestController
@RequestMapping("/knowledge/cleanup")
@Validated
public class KnowledgeCleanupController {

    @Resource
    private KnowledgeCleanupService knowledgeCleanupService;

    @PostMapping("/run")
    @Operation(summary = "手动触发清理任务（stream/querylog/version/orphan）")
    @Parameter(name = "type", description = "清理类型", required = true, example = "orphan")
    public CommonResult<Object> run(@RequestParam("type") String type) {
        switch (type) {
            case "stream":
                return success(knowledgeCleanupService.trimDocPipeline());
            case "querylog":
                return success(knowledgeCleanupService.cleanQueryLog());
            case "version":
                return success(knowledgeCleanupService.cleanDocumentVersions());
            case "orphan":
                return success(knowledgeCleanupService.cleanOrphanVectors());
            default:
                throw exception(KNOWLEDGE_CLEANUP_TYPE_ERROR, type);
        }
    }

}
