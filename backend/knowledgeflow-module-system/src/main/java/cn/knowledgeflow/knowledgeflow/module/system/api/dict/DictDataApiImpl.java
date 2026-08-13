package cn.knowledgeflow.module.system.api.dict;

import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.framework.common.biz.system.dict.dto.DictDataRespDTO;
import cn.knowledgeflow.module.system.dal.dataobject.dict.DictDataDO;
import cn.knowledgeflow.module.system.service.dict.DictDataService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Collection;
import java.util.List;

/**
 * 字典数据 API 实现类
 *
 * @author 芋道源码
 */
@Service
public class DictDataApiImpl implements DictDataApi {

    @Resource
    private DictDataService dictDataService;

    @Override
    public void validateDictDataList(String dictType, Collection<String> values) {
        dictDataService.validateDictDataList(dictType, values);
    }

    @Override
    public List<DictDataRespDTO> getDictDataList(String dictType) {
        List<DictDataDO> list = dictDataService.getDictDataListByDictType(dictType);
        return BeanUtils.toBean(list, DictDataRespDTO.class);
    }

}
