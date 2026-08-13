package cn.knowledgeflow.module.system.api.logger;

import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.framework.common.biz.system.logger.dto.OperateLogCreateReqDTO;
import cn.knowledgeflow.module.system.api.logger.dto.OperateLogPageReqDTO;
import cn.knowledgeflow.module.system.api.logger.dto.OperateLogRespDTO;
import cn.knowledgeflow.module.system.dal.dataobject.logger.OperateLogDO;
import cn.knowledgeflow.module.system.service.logger.OperateLogService;
import org.dromara.core.trans.anno.TransMethodResult;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

/**
 * 操作日志 API 实现类
 *
 * @author 芋道源码
 */
@Service
@Validated
public class OperateLogApiImpl implements OperateLogApi {

    @Resource
    private OperateLogService operateLogService;

    @Override
    public void createOperateLog(OperateLogCreateReqDTO createReqDTO) {
        operateLogService.createOperateLog(createReqDTO);
    }

    @Override
    @TransMethodResult
    public PageResult<OperateLogRespDTO> getOperateLogPage(OperateLogPageReqDTO pageReqDTO) {
        PageResult<OperateLogDO> operateLogPage = operateLogService.getOperateLogPage(pageReqDTO);
        return BeanUtils.toBean(operateLogPage, OperateLogRespDTO.class);
    }

}
