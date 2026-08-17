# KnowledgeFlow-AI 完善计划

> 制定时间：2026-08-17  
> 项目路径：D:\The World\KnowledgeFlow-AI

---

## 一、项目现状总结

### 1.1 已完成功能

| 模块 | 功能 | 状态 |
|------|------|------|
| 知识库管理 | 创建/编辑/删除/分页查询 | ✅ 完成 |
| 文档管理 | 上传/下载/预览/删除 | ✅ 完成 |
| RAG 问答 | 文档检索 + AI 回答 | ✅ 完成 |
| 成员管理 | 添加/移除成员 | ✅ 完成（admin 无法添加为成员，因 owner 隐式拥有权限） |
| 通知系统 | 实时通知推送 | ✅ 完成 |
| 报表导出 | CSV 导出 | ✅ 完成 |
| 文档版本历史 | 版本记录 | ✅ 完成 |
| 标签系统 | 文档标签管理 | ✅ 完成 |

### 1.2 技术栈

**后端**：
- Spring Boot 2.7.18 + Java 17
- MyBatis Plus 3.5.5
- Redis（消息队列 + 缓存）
- MinIO（对象存储）
- Qdrant（向量数据库）

**前端**：
- Vue 3.4.x + TypeScript 5.x
- Element Plus 2.14.3
- Vite 8.2.0

**部署**：
- Docker Compose（7 个服务）
- Nginx 反代

---

## 二、完善计划（按优先级排序）

### Phase 1：数据清理（预计 30 分钟）

#### 1.1 清理无效种子数据

**问题**：数据库中存在文档 ID 9001-9005，其 MinIO 对象已不存在（或为空）。

**实施方案**：
```sql
-- 1. 检查无效文档
SELECT id, filename, object_name, file_size, status
FROM kb_document
WHERE id BETWEEN 9001 AND 9005;

-- 2. 删除无效文档（级联删除版本记录）
DELETE FROM kb_document_version WHERE document_id BETWEEN 9001 AND 9005;
DELETE FROM kb_document WHERE id BETWEEN 9001 AND 9005;

-- 3. 验证清理结果
SELECT COUNT(*) FROM kb_document WHERE id BETWEEN 9001 AND 9005;
```

**验收标准**：
- 9001-9005 文档已从数据库删除
- 前端知识库页面不再显示这些文档
- 相关统计数字正确更新

---

### Phase 2：CI/CD 流水线（预计 2 小时）

#### 2.1 GitHub Actions 配置

**文件**：`.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven
      - name: Build Backend
        run: cd backend && mvn clean package -DskipTests
      - name: Upload Build Artifact
        uses: actions/upload-artifact@v4
        with:
          name: backend-jar
          path: backend/knowledgeflow-server/target/*.jar

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Dependencies
        run: cd frontend && npm ci
      - name: Build Frontend
        run: cd frontend && npm run build
      - name: Upload Build Artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: frontend/dist

  docker-build:
    needs: [backend-build, frontend-build]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker Images
        run: |
          cd deploy
          docker-compose build --no-cache
      - name: Run Health Check
        run: |
          cd deploy
          docker-compose up -d
          sleep 30
          docker-compose ps
```

**验收标准**：
- Push 到 main 分支自动触发构建
- 后端 JAR 包构建成功
- 前端 dist 构建成功
- Docker 镜像构建成功

---

### Phase 3：单元测试（预计 4 小时）

#### 3.1 后端测试框架配置

**pom.xml 依赖**：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <scope>test</scope>
</dependency>
```

**测试目录结构**：
```
backend/
└── knowledgeflow-module/
    └── src/
        └── test/
            └── java/
                └── cn/knowledgeflow/module/knowledge/
                    ├── service/
                    │   ├── document/
                    │   │   └── DocumentServiceImplTest.java
                    │   └── kb/
                    │       └── KnowledgeBaseServiceImplTest.java
                    └── controller/
                        └── DocumentControllerTest.java
```

#### 3.2 核心测试用例

**DocumentServiceImplTest.java**：
```java
@ExtendWith(MockitoExtension.class)
class DocumentServiceImplTest {

    @Mock
    private DocumentMapper documentMapper;
    @Mock
    private MinioClient minioClient;
    @Mock
    private StringRedisTemplate stringRedisTemplate;

    @InjectMocks
    private DocumentServiceImpl documentService;

    @Test
    void uploadDocument_success() {
        // 测试文档上传成功场景
    }

    @Test
    void uploadDocument_emptyFile_throwsException() {
        // 测试空文件上传抛出异常
    }

    @Test
    void getDocumentContent_notExists_throwsException() {
        // 测试文档不存在时抛出异常
    }
}
```

**验收标准**：
- 核心 Service 类测试覆盖率 > 60%
- 所有测试用例通过
- 测试执行时间 < 30 秒

---

### Phase 4：前端测试（预计 2 小时）

#### 4.1 Vitest 配置

**vitest.config.ts**：
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

#### 4.2 核心测试用例

**KbView.spec.ts**：
```typescript
describe('KbView', () => {
  it('should render knowledge base cards', async () => {
    // 测试知识库卡片渲染
  })

  it('should open member dialog on click', async () => {
    // 测试成员对话框打开
  })

  it('should add member successfully', async () => {
    // 测试添加成员功能
  })
})
```

**验收标准**：
- 核心组件测试覆盖率 > 50%
- 所有测试用例通过

---

### Phase 5：API 文档完善（预计 1 小时）

#### 5.1 Swagger 注解优化

**DocumentController.java**：
```java
@Tag(name = "管理后台 - 知识库文档", description = "文档 CRUD + 上传下载预览")
@RestController
@RequestMapping("/admin-api/knowledge/document")
public class DocumentController {

    @Operation(
        summary = "上传文档",
        description = "上传文档到 MinIO，返回文档 ID 和对象名称",
        responses = {
            @ApiResponse(responseCode = "200", description = "上传成功"),
            @ApiResponse(responseCode = "400", description = "文件为空或类型不支持"),
            @ApiResponse(responseCode = "403", description = "无权限")
        }
    )
    @PostMapping("/upload")
    public CommonResult<DocumentRespVO> uploadDocument(...) {
        // ...
    }
}
```

**验收标准**：
- 所有 Controller 方法都有 @Operation 注解
- API 文档可正常访问：http://localhost:8080/swagger-ui.html

---

### Phase 6：监控告警（预计 3 小时）

#### 6.1 Spring Boot Actuator 配置

**application.yaml**：
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

#### 6.2 Prometheus 配置

**deploy/prometheus.yml**：
```yaml
scrape_configs:
  - job_name: 'knowledgeflow-backend'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['backend:48080']
```

#### 6.3 Grafana Dashboard

创建监控面板：
- JVM 内存使用
- CPU 使用率
- HTTP 请求延迟
- 错误率
- 文档处理队列长度

**验收标准**：
- Prometheus 可抓取后端指标
- Grafana 有可用的监控面板
- 关键指标可配置告警规则

---

## 三、实施顺序

| 阶段 | 任务 | 优先级 | 预计时间 |
|------|------|--------|----------|
| Phase 1 | 清理无效种子数据 | P0 | 30 分钟 |
| Phase 2 | CI/CD 流水线 | P1 | 2 小时 |
| Phase 3 | 后端单元测试 | P1 | 4 小时 |
| Phase 4 | 前端测试 | P2 | 2 小时 |
| Phase 5 | API 文档完善 | P2 | 1 小时 |
| Phase 6 | 监控告警 | P3 | 3 小时 |

**总计**：约 12.5 小时

---

## 四、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试代码质量低 | 维护成本高 | 遵循 TDD 原则，测试即文档 |
| CI/CD 构建失败 | 无法自动部署 | 本地先验证，逐步完善 |
| 监控指标不完整 | 无法有效告警 | 先实现基础指标，逐步完善 |

---

## 五、验收标准

### 5.1 功能验收
- [ ] 所有核心功能正常运行
- [ ] 文档预览无下载问题
- [ ] 成员管理功能正常（除 admin 外）
- [ ] 通知系统正常工作

### 5.2 质量验收
- [ ] 后端测试覆盖率 > 60%
- [ ] 前端测试覆盖率 > 50%
- [ ] 无严重安全漏洞
- [ ] 代码符合规范

### 5.3 部署验收
- [ ] Docker Compose 一键部署成功
- [ ] CI/CD 流水线自动构建
- [ ] 监控告警正常触发

---

## 六、后续优化方向

1. **性能优化**
   - 文档处理并行化
   - 缓存策略优化
   - 数据库查询优化

2. **功能扩展**
   - 文档OCR识别
   - 多语言支持
   - 移动端适配

3. **架构优化**
   - 微服务拆分
   - 消息队列升级
   - 分布式部署

---

*计划制定完毕，等待执行*
