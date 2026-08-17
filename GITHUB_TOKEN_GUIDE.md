# GitHub Token 配置指南

## 问题
推送失败，错误：
```
refusing to allow a Personal Access Token to create or update workflow `.github/workflows/ci.yml` without `workflow` scope
```

## 解决方案

### 步骤 1: 生成新 Token

1. 访问: https://github.com/settings/tokens
2. 点击: **Generate new token** → **Generate new token (classic)**
3. 填写:
   - **Note**: `KnowledgeFlow-AI`
   - **Expiration**: 选择合适日期
4. **必须勾选的 Scopes**:
   - ✅ `repo` (完整仓库访问)
   - ✅ `workflow` (GitHub Actions 工作流权限)
   - ✅ `read:org` (读取组织信息)
5. 点击 **Generate token**
6. **立即复制 Token** (只显示一次!)

### 步骤 2: 配置并推送

在 PowerShell 中执行 (替换 `YOUR_TOKEN`):

```powershell
cd "D:\The World\KnowledgeFlow-AI"

# 配置 Git 用户信息
git config user.name "shanhuhai12138"
git config user.email "shanhuhai12138@users.noreply.github.com"

# 使用新 Token 更新远端 URL
git remote set-url origin https://YOUR_TOKEN@github.com/shanhuhai12138/KnowledgeFlow-AI.git

# 推送代码
git push origin main

# 验证
git log --oneline origin/main -5
```

## 安全提示

- Token 只用于本项目
- 不要将 Token 提交到代码仓库
- 定期轮换 Token
