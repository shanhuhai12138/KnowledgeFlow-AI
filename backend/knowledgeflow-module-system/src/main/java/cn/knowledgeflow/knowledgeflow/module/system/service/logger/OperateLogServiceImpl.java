package cn.knowledgeflow.module.system.service.logger;

import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.framework.common.biz.system.logger.dto.OperateLogCreateReqDTO;
import cn.knowledgeflow.module.system.api.logger.dto.OperateLogPageReqDTO;
import cn.knowledgeflow.module.system.controller.admin.logger.vo.operatelog.OperateLogPageReqVO;
import cn.knowledgeflow.module.system.dal.dataobject.logger.OperateLogDO;
import cn.knowledgeflow.module.system.dal.mysql.logger.OperateLogMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

/**
 * 操作日志 Service 实现类
 *
 * @author 芋道源码
 */
@Service
@Validated
@Slf4j
public class OperateLogServiceImpl implements OperateLogService {

    @Resource
    private OperateLogMapper operateLogMapper;

    @Override
    public void createOperateLog(OperateLogCreateReqDTO createReqDTO) {
        OperateLogDO log = BeanUtils.toBean(createReqDTO, OperateLogDO.class);
        operateLogMapper.insert(log);
    }

    @Override
    public OperateLogDO getOperateLog(Long id) {
        return operateLogMapper.selectById(id);
    }

    @Override
    public PageResult<OperateLogDO> getOperateLogPage(OperateLogPageReqVO pageReqVO) {
        return operateLogMapper.selectPage(pageReqVO);
    }

    @Override
    public PageResult<OperateLogDO> getOperateLogPage(OperateLogPageReqDTO pageReqDTO) {
        return operateLogMapper.selectPage(pageReqDTO);
    }

}
