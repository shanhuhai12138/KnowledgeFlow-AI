package cn.knowledgeflow.module.knowledge.controller.admin.kb;

import cn.knowledgeflow.framework.common.pojo.CommonResult;
import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberPageReqVO;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberRespVO;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberSaveReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
import cn.knowledgeflow.module.knowledge.service.kb.KnowledgeBaseMemberService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import jakarta.validation.Valid;
import java.time.format.DateTimeFormatter;
import java.util.stream.Collectors;

import static cn.knowledgeflow.framework.common.pojo.CommonResult.success;

@Tag(name = "管理后台 - 知识库成员")
@RestController
@RequestMapping("/knowledge/kb-member")
@Validated
public class KnowledgeBaseMemberController {

    @Resource
    private KnowledgeBaseMemberService knowledgeBaseMemberService;

    @PostMapping("/create")
    @Operation(summary = "添加成员（仅所有者或 ADMIN 成员）")
    public CommonResult<Long> createMember(@Valid @RequestBody KnowledgeBaseMemberSaveReqVO createReqVO) {
        return success(knowledgeBaseMemberService.createMember(createReqVO));
    }

    @DeleteMapping("/delete")
    @Operation(summary = "移除成员（仅所有者或 ADMIN 成员）")
    @Parameter(name = "id", description = "成员记录编号", required = true, example = "1")
    public CommonResult<Boolean> deleteMember(@RequestParam("id") Long id) {
        knowledgeBaseMemberService.deleteMember(id);
        return success(true);
    }

    @GetMapping("/page")
    @Operation(summary = "获得知识库成员分页")
    public CommonResult<PageResult<KnowledgeBaseMemberRespVO>> getMemberPage(@Validated KnowledgeBaseMemberPageReqVO pageReqVO) {
        PageResult<KnowledgeBaseMemberDO> pageResult = knowledgeBaseMemberService.getMemberPage(pageReqVO);
        return success(new PageResult<>(pageResult.getList().stream()
                .map(this::convert).collect(Collectors.toList()), pageResult.getTotal()));
    }

    @GetMapping("/get")
    @Operation(summary = "获得成员记录")
    @Parameter(name = "id", description = "成员记录编号", required = true, example = "1")
    public CommonResult<KnowledgeBaseMemberRespVO> getMember(@RequestParam("id") Long id) {
        return success(convert(knowledgeBaseMemberService.getMember(id)));
    }

    private KnowledgeBaseMemberRespVO convert(KnowledgeBaseMemberDO member) {
        KnowledgeBaseMemberRespVO respVO = BeanUtils.toBean(member, KnowledgeBaseMemberRespVO.class);
        if (respVO != null) {
            respVO.setCreatedAt(member.getCreateTime() == null ? null
                    : member.getCreateTime().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        }
        return respVO;
    }

}
