package cn.knowledgeflow.module.knowledge.framework.ai;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * AI 服务（Python FastAPI）转发配置（yudao.ai-service.*，见 application-local.yaml）
 */
@Data
@ConfigurationProperties(prefix = "yudao.ai-service")
public class AiServiceProperties {

    /**
     * Python AI 服务地址（默认本地开发端口 8000）
     */
    private String baseUrl = "http://localhost:8000";

    /**
     * Qdrant REST 地址（T6.5 孤儿向量扫描用）
     */
    private String qdrantUrl = "http://localhost:6333";

}
