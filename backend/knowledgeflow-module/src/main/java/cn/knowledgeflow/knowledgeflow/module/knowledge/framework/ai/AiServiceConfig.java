package cn.knowledgeflow.module.knowledge.framework.ai;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * AI 转发层配置：RestTemplate（连接超时 3s，读取超时 60s，适配流式/长响应）
 */
@Configuration
@EnableConfigurationProperties(AiServiceProperties.class)
public class AiServiceConfig {

    @Bean
    public RestTemplate aiServiceRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(3000);
        factory.setReadTimeout(60000);
        return new RestTemplate(factory);
    }

    /**
     * SSE 流式转发线程池（守护线程，不阻塞应用关闭）
     */
    @Bean("aiStreamExecutor")
    public ExecutorService aiStreamExecutor() {
        return Executors.newFixedThreadPool(8, r -> {
            Thread thread = new Thread(r, "ai-stream-forward");
            thread.setDaemon(true);
            return thread;
        });
    }

}
