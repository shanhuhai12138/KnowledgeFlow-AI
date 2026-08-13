package cn.knowledgeflow.module.knowledge.controller.admin.kb;

import cn.knowledgeflow.framework.common.pojo.CommonResult;
import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBasePageReqVO;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseRespVO;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseSaveReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.knowledgeflow.module.knowledge.service.kb.KnowledgeBaseService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

import static cn.knowledgeflow.framework.common.pojo.CommonResult.success;

@Tag(name = "管理后台 - 知识库")
@RestController
@RequestMapping("/knowledge/kb")
@Validated
public class KnowledgeBaseController {

    @Resource
    private KnowledgeBaseService knowledgeBaseService;

    @PostMapping("/create")
    @Operation(summary = "创建知识库（创建者即所有者）")
    public CommonResult<Long> createKnowledgeBase(@Valid @RequestBody KnowledgeBaseSaveReqVO createReqVO) {
        return success(knowledgeBaseService.createKnowledgeBase(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "修改知识库（仅所有者或 ADMIN 成员）")
    public CommonResult<Boolean> updateKnowledgeBase(@Valid @RequestBody KnowledgeBaseSaveReqVO updateReqVO) {
        knowledgeBaseService.updateKnowledgeBase(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除知识库（仅所有者或 ADMIN 成员，级联删除成员）")
    @Parameter(name = "id", description = "知识库编号", required = true, example = "1")
    public CommonResult<Boolean> deleteKnowledgeBase(@RequestParam("id") Long id) {
        knowledgeBaseService.deleteKnowledgeBase(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得知识库（非成员访问私有库返回 403）")
    @Parameter(name = "id", description = "知识库编号", required = true, example = "1")
    public CommonResult<KnowledgeBaseRespVO> getKnowledgeBase(@RequestParam("id") Long id) {
        return success(convert(knowledgeBaseService.getKnowledgeBase(id)));
    }

    @GetMapping("/page")
    @Operation(summary = "获得知识库分页（仅返回当前用户可见）")
    public CommonResult<PageResult<KnowledgeBaseRespVO>> getKnowledgeBasePage(@Validated KnowledgeBasePageReqVO pageReqVO) {
        PageResult<KnowledgeBaseDO> pageResult = knowledgeBaseService.getKnowledgeBasePage(pageReqVO);
        return success(new PageResult<>(pageResult.getList().stream()
                .map(this::convert).collect(Collectors.toList()), pageResult.getTotal()));
    }

    @GetMapping("/list")
    @Operation(summary = "获得当前用户可见的全部知识库（前端快捷列表/下拉）")
    public CommonResult<List<KnowledgeBaseRespVO>> getKnowledgeBaseList() {
        List<KnowledgeBaseRespVO> list = knowledgeBaseService.getKnowledgeBaseList().stream()
                .map(this::convert).collect(Collectors.toList());
        return success(list);
    }

    // ==================== 内部方法：DO → VO（契约字段映射） ====================

    /**
     * DO → RespVO：框架 BaseDO 是 createTime/updateTime，契约要求 createdAt/updatedAt，此处显式映射
     */
    private KnowledgeBaseRespVO convert(KnowledgeBaseDO knowledgeBase) {
        KnowledgeBaseRespVO respVO = BeanUtils.toBean(knowledgeBase, KnowledgeBaseRespVO.class);
        if (respVO != null) {
            respVO.setCreatedAt(formatIso(knowledgeBase.getCreateTime()));
            respVO.setUpdatedAt(formatIso(knowledgeBase.getUpdateTime()));
        }
        return respVO;
    }

    private String formatIso(LocalDateTime time) {
        return time == null ? null : time.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }

}
