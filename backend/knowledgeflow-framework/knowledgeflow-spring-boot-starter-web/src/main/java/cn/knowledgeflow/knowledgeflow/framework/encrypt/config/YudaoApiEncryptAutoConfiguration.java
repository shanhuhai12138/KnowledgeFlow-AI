package cn.knowledgeflow.framework.encrypt.config;

import cn.knowledgeflow.framework.common.enums.WebFilterOrderEnum;
import cn.knowledgeflow.framework.encrypt.core.filter.ApiEncryptFilter;
import cn.knowledgeflow.framework.web.config.WebProperties;
import cn.knowledgeflow.framework.web.core.handler.GlobalExceptionHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import static cn.knowledgeflow.framework.web.config.YudaoWebAutoConfiguration.createFilterBean;

@AutoConfiguration
@Slf4j
@EnableConfigurationProperties(ApiEncryptProperties.class)
@ConditionalOnProperty(prefix = "yudao.api-encrypt", name = "enable", havingValue = "true")
public class YudaoApiEncryptAutoConfiguration {

    @Bean
    public FilterRegistrationBean<ApiEncryptFilter> apiEncryptFilter(WebProperties webProperties,
                                                                     ApiEncryptProperties apiEncryptProperties,
                                                                     RequestMappingHandlerMapping requestMappingHandlerMapping,
                                                                     GlobalExceptionHandler globalExceptionHandler) {
        ApiEncryptFilter filter = new ApiEncryptFilter(webProperties, apiEncryptProperties,
                requestMappingHandlerMapping, globalExceptionHandler);
        return createFilterBean(filter, WebFilterOrderEnum.API_ENCRYPT_FILTER);

    }

}
