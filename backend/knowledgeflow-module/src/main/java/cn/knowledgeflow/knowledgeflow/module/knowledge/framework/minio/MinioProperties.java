package cn.knowledgeflow.module.knowledge.framework.minio;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * MinIO 对象存储配置（yudao.minio.*，见 application-local.yaml）
 */
@Data
@ConfigurationProperties(prefix = "yudao.minio")
public class MinioProperties {

    /**
     * MinIO 服务地址（S3 API）
     */
    private String endpoint = "http://localhost:9000";
    /**
     * Access Key
     */
    private String accessKey = "minioadmin";
    /**
     * Secret Key
     */
    private String secretKey = "minioadmin";
    /**
     * 桶名称
     */
    private String bucket = "knowledgeflow";

}
