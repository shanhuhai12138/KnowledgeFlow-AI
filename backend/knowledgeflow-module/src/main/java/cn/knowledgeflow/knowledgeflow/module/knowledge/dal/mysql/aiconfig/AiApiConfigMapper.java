package cn.knowledgeflow.module.knowledge.dal.mysql.aiconfig;

import cn.knowledgeflow.framework.mybatis.core.mapper.BaseMapperX;
import cn.knowledgeflow.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.knowledgeflow.module.knowledge.dal.dataobject.aiconfig.AiApiConfigDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AiApiConfigMapper extends BaseMapperX<AiApiConfigDO> {

    default AiApiConfigDO selectByConfigKey(String configKey) {
        return selectOne(new LambdaQueryWrapperX<AiApiConfigDO>()
                .eq(AiApiConfigDO::getConfigKey, configKey));
    }

}
