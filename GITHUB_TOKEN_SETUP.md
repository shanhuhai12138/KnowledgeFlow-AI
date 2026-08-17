# GitHub Token 修复指南

## 问题
推送代码到 GitHub 失败，错误信息：
```
refusing to allow a Personal Access Token to create or update workflow `.github/workflows/ci.yml` without `workflow` scope
```

## 解决方案

### 步骤 1: 生成新的 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写 Token 信息:
   - **Note**: KnowledgeFlow-AI Push Token
   - **Expiration**: 选择合适日期
4. **Scopes** (必须勾选):
   - ✅ `repo` - 完整仓库访问
   - ✅ `workflow` - GitHub Actions 工作流权限
   - ✅ `read:org` - 读取组织信息

5. 点击 "Generate token"
6. **立即复制 Token** (只显示一次!)

### 步骤 2: 配置本地 Git

```powershell
# 进入项目目录
cd "D:\The World\KnowledgeFlow-AI"

# 配置 Git 用户信息 (如果还没配置)
git config user.name "shanhuhai12138"
git config user.email "shanhuhai12138@users.noreply.github.com"

# 使用 Token 配置远端 URL (替换 YOUR_TOKEN)
git remote set-url origin https://YOUR_TOKEN@github.com/shanhuhai12138/KnowledgeFlow-AI.git
```

### 步骤 3: 推送代码

```powershell
git push origin main
```

### 步骤 4: 验证

```powershell
git log --oneline origin/main -5
```

应该显示最新的提交记录。

## 安全提示

- Token 只用于本项目，不要分享给他人
- 不建议将 Token 提交到代码仓库
- 定期轮换 Token

## 替代方案: 使用 SSH

如果不想使用 Token，可以配置 SSH:

```powershell
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub: Settings → SSH and GPG keys → New SSH key

# 修改远端 URL 为 SSH
git remote set-url origin git@github.com:shanhuhai12138/KnowledgeFlow-AI.git
```

## 联系支持

如有问题，请查看:
- GitHub Docs: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
