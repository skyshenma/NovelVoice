# 配置文件安全指南

本文档说明如何安全地管理 NovelVoice 的配置文件,保护敏感信息(如 Bark API Key)不被泄露到 Git 仓库。

## 🔒 安全策略

### 1. 配置文件层级

NovelVoice 支持多层配置,优先级从高到低:

1. **环境变量** (最高优先级)
2. **config.yml** (主配置文件)
3. **config.example.yml** (示例配置,仅供参考)
4. **代码默认值** (最低优先级)

### 2. 文件说明

| 文件 | 用途 | 是否提交到 Git | 包含敏感信息 |
|------|------|----------------|--------------|
| `config.example.yml` | 配置示例模板 | ✅ 是 | ❌ 否 |
| `config.yml` | 实际使用的配置 | ❌ 否 | ✅ 是 |
| `.env.example` | 环境变量示例 | ✅ 是 | ❌ 否 |
| `.env` | 实际环境变量 | ❌ 否 | ✅ 是 |

## 📋 推荐使用方式

### 方式一: 使用 config.yml (本地开发推荐)

```bash
# 1. 复制示例配置
cp data/config/config.example.yml data/config/config.yml

# 2. 编辑配置文件,添加你的敏感信息
nano data/config/config.yml

# 3. 配置文件会被 .gitignore 自动忽略,不会提交到 Git
```

**优点**:
- ✅ 简单直观,所有配置集中在一个文件
- ✅ 支持配置热重载
- ✅ 自动被 Git 忽略

### 方式二: 使用环境变量 (Docker 部署推荐)

```bash
# 1. 复制环境变量示例
cp .env.example .env

# 2. 编辑 .env 文件,设置敏感信息
nano .env

# 示例内容:
# NOVELVOICE_BARK_ENABLED=true
# NOVELVOICE_BARK_API_KEY=your_real_api_key_here

# 3. .env 文件会被 .gitignore 自动忽略
```

**优点**:
- ✅ 适合 Docker 部署
- ✅ 符合 12-Factor App 原则
- ✅ 易于 CI/CD 集成
- ✅ 自动被 Git 忽略

### 方式三: 混合使用 (生产环境推荐)

```bash
# 1. 使用 config.yml 存储非敏感配置
cp data/config/config.example.yml data/config/config.yml

# 2. 使用环境变量覆盖敏感配置
export NOVELVOICE_BARK_API_KEY=your_real_api_key_here
export NOVELVOICE_BARK_ENABLED=true

# 3. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**优点**:
- ✅ 最安全的方式
- ✅ 敏感信息只存在于环境变量
- ✅ 配置文件可以部分提交(去除敏感部分)

## 🛡️ 安全检查清单

在提交代码前,请确认:

- [ ] `config.yml` 已添加到 `.gitignore`
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 没有在代码中硬编码 API Key
- [ ] `config.example.yml` 中的敏感字段使用占位符(如 `""` 或 `your_key_here`)
- [ ] `.env.example` 中的敏感字段使用占位符

## 🔍 检查是否泄露敏感信息

```bash
# 检查 Git 暂存区
git status

# 查看即将提交的内容
git diff --cached

# 搜索可能的 API Key
git grep -i "api.key\|api_key\|apikey" data/config/

# 检查历史记录中是否有敏感信息
git log --all --full-history --source -- data/config/config.yml
```

## 🚨 如果已经泄露了敏感信息

如果不小心将包含敏感信息的文件提交到了 Git:

### 1. 立即更换泄露的密钥

```bash
# 立即更换 Bark API Key 或其他敏感信息
```

### 2. 从 Git 历史中删除敏感文件

```bash
# 使用 git filter-branch 删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch data/config/config.yml" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

### 3. 清理本地仓库

```bash
# 清理引用
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## 📚 Docker 环境配置

### 使用 .env 文件

```bash
# 1. 创建 .env 文件
cp .env.example .env

# 2. 编辑 .env
nano .env

# 3. Docker Compose 会自动加载 .env
docker-compose up -d
```

### docker-compose.yml 配置

```yaml
services:
  novelvoice:
    # 自动加载 .env 文件
    env_file:
      - .env
    
    environment:
      # 这里的值会覆盖 .env 中的值
      - NOVELVOICE_HOST=0.0.0.0
```

## 💡 最佳实践

1. **永远不要提交包含真实密钥的文件**
2. **使用环境变量存储敏感信息**
3. **定期检查 .gitignore 是否生效**
4. **在团队中分享 .env.example,而不是 .env**
5. **使用配置热重载功能,避免频繁重启服务**

## 🔗 相关文档

- [配置指南](CONFIG_GUIDE.md)
- [Docker 部署](DOCKER.md)
- [快速开始](QUICKSTART.md)
