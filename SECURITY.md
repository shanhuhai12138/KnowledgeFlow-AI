# Security Policy

## Supported Versions

| 版本 | 支持状态 |
|------|----------|
| 2.0.x | ✅  actively supported |
| < 2.0 | ❌ 不再支持 |

## Reporting a Vulnerability

如果你发现安全漏洞，请:

1. **不要** 在公开 Issue 中报告
2. 通过以下方式报告:
   - GitHub Security Advisory: [Report a vulnerability](https://github.com/shanhuhai12138/KnowledgeFlow-AI/security/advisories/new)
   - Email: shanhuhai12138@users.noreply.github.com

3. 包含以下信息:
   - 漏洞描述
   - 复现步骤
   - 影响范围
   - 建议的修复方案

我们将在 72 小时内响应。

## Security Best Practices

### 部署前必读

1. **修改默认密码**:
   - MySQL: `knowledgeflow` → 自定义密码
   - MinIO: 修改默认 Access Key
   - Redis: 设置密码

2. **配置环境变量**:
   ```bash
   cp deploy/.env.example deploy/.env
   # 编辑 .env 文件，设置所有敏感信息
   ```

3. **使用 HTTPS**:
   - 在生产环境中配置 SSL 证书
   - 使用反向代理 (Nginx) 终止 TLS

### API 安全

- 所有 API 需要认证 (JWT Token)
- API Key 使用 AES 加密存储
- 敏感操作记录审计日志

### 数据安全

- 定期备份数据库
- 敏感文件加密存储
- 最小权限原则
