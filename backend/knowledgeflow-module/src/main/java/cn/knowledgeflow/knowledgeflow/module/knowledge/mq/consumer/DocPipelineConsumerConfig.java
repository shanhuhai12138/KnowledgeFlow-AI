package cn.knowledgeflow.module.knowledge.mq.consumer;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.stream.Consumer;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.stream.StreamMessageListenerContainer;
import org.springframework.data.redis.stream.StreamMessageListenerContainer.StreamMessageListenerContainerOptions;

import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * doc-pipeline 消费者容器配置（任务书 T2.5）
 *
 * 消费者组：doc-pipeline-group / ingest-consumer（契约）；失败重试由 DocPipelineConsumer 内部
 * XACK + 重新入队 attempt+1 实现；单线程顺序消费避免并发竞态。
 */
@Slf4j
@Configuration
public class DocPipelineConsumerConfig {

    /**
     * 消费线程（单线程顺序处理，保证同一文档消息有序）
     */
    private final ExecutorService consumerExecutor =
            Executors.newSingleThreadExecutor(r -> {
                Thread thread = new Thread(r, "doc-pipeline-consumer");
                thread.setDaemon(true);
                return thread;
            });

    @Bean(destroyMethod = "stop")
    public StreamMessageListenerContainer<String, MapRecord<String, String, String>> docPipelineContainer(
            RedisConnectionFactory factory, StringRedisTemplate stringRedisTemplate,
            DocPipelineConsumer consumer) {
        // 1. 创建消费者组（幂等：已存在则忽略；MKSTREAM 保证 stream 存在；从头开始以消费历史消息）
        try {
            stringRedisTemplate.opsForStream().createGroup(DocPipelineConsumer.STREAM,
                    org.springframework.data.redis.connection.stream.ReadOffset.from("0"), DocPipelineConsumer.GROUP);
            log.info("[docPipelineContainer][创建消费者组 {}/{} 完成（从头消费）]", DocPipelineConsumer.STREAM, DocPipelineConsumer.GROUP);
        } catch (Exception e) {
            log.info("[docPipelineContainer][消费者组已存在，跳过创建] {}", e.getMessage());
        }
        // 2. 构建容器（Spring Data Redis 2.7：扁平字符串消息默认即 MapRecord，无需 targetType；
        //    builder() 泛型为 raw，需 cast）
        @SuppressWarnings({"unchecked", "rawtypes"})
        StreamMessageListenerContainerOptions options =
                StreamMessageListenerContainerOptions.builder()
                        .pollTimeout(Duration.ofSeconds(2))
                        .batchSize(10)
                        .executor(consumerExecutor)
                        .errorHandler(t -> log.error("[docPipelineContainer][消费异常]", t))
                        .build();
        StreamMessageListenerContainer<String, MapRecord<String, String, String>> container =
                (StreamMessageListenerContainer) StreamMessageListenerContainer.create(factory, options);
        // 3. 订阅：从最后消费位置开始
        container.receive(Consumer.from(DocPipelineConsumer.GROUP, DocPipelineConsumer.CONSUMER),
                StreamOffset.create(DocPipelineConsumer.STREAM, ReadOffset.lastConsumed()), consumer);
        container.start();
        log.info("[docPipelineContainer][消费者容器已启动]");
        return container;
    }

}
