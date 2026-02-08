# GitHub 开源和 Docker Hub 发布指南

本文档详细说明如何将 NovelVoice 开源到 GitHub 并发布 Docker 镜像到 Docker Hub。

---

## 📋 准备工作

### 1. GitHub 账号准备

确保您有 GitHub 账号: https://github.com

### 2. Docker Hub 账号准备

1. 注册 Docker Hub 账号: https://hub.docker.com
2. 创建 Access Token:
   - 登录 Docker Hub
   - Account Settings → Security → New Access Token
   - 保存生成的 Token

---

## 🚀 发布到 GitHub

### 1. 创建 GitHub 仓库

```bash
# 在 GitHub 网站上创建新仓库
# 仓库名: NovelVoice
# 描述: AI-powered audiobook generator using Microsoft Edge TTS
# 公开仓库
# 不要初始化 README (我们已经有了)
```

### 2. 初始化 Git 仓库

```bash
cd /Users/sky/Downloads/NovelVoice

# 初始化 Git
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "feat: initial commit - NovelVoice v1.0.0"

# 添加远程仓库 (替换 yourusername 为您的 GitHub 用户名)
git remote add origin https://github.com/yourusername/NovelVoice.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 3. 配置 GitHub Secrets

在 GitHub 仓库设置中添加 Secrets:

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 添加以下 Secrets:
   - `DOCKER_HUB_USERNAME`: 您的 Docker Hub 用户名
   - `DOCKER_HUB_TOKEN`: Docker Hub Access Token

### 4. 创建第一个 Release

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release v1.0.0 - Initial stable release"

# 推送标签
git push origin v1.0.0
```

在 GitHub 网站上:
1. 进入仓库 → Releases → Create a new release
2. 选择标签 `v1.0.0`
3. 填写 Release 标题和说明
4. 发布 Release

---

## 🐳 发布到 Docker Hub

### 方式一: 自动发布 (推荐)

GitHub Actions 会自动构建和推送镜像:

1. **推送代码到 main 分支** → 自动构建 `latest` 标签
2. **创建版本标签** (如 `v1.0.0`) → 自动构建版本标签

```bash
# 推送代码触发自动构建
git push origin main

# 或创建版本标签触发
git tag v1.0.1
git push origin v1.0.1
```

### 方式二: 手动发布

```bash
# 1. 登录 Docker Hub
docker login

# 2. 构建镜像 (替换 yourusername)
docker build -t yourusername/novelvoice:latest .
docker build -t yourusername/novelvoice:1.0.0 .

# 3. 推送镜像
docker push yourusername/novelvoice:latest
docker push yourusername/novelvoice:1.0.0
```

### 多架构构建 (amd64 + arm64)

```bash
# 创建 buildx builder
docker buildx create --name multiarch --use

# 构建并推送多架构镜像
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/novelvoice:latest \
  -t yourusername/novelvoice:1.0.0 \
  --push .
```

---

## 📝 更新 README 添加徽章

在 README.md 顶部添加:

```markdown
# NovelVoice - AI 有声书生成器

[![GitHub release](https://img.shields.io/github/v/release/yourusername/NovelVoice)](https://github.com/yourusername/NovelVoice/releases)
[![Docker Image](https://img.shields.io/docker/v/yourusername/novelvoice?label=docker)](https://hub.docker.com/r/yourusername/novelvoice)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/novelvoice)](https://hub.docker.com/r/yourusername/novelvoice)
[![License](https://img.shields.io/github/license/yourusername/NovelVoice)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

基于 Microsoft Edge TTS 的智能有声书生成工具,支持 TXT/EPUB 格式,提供现代化 Web 界面。
```

---

## 🔄 版本发布流程

### 1. 更新版本号

编辑 `CHANGELOG.md`:

```markdown
## [1.0.1] - 2026-02-08

### Added
- 新功能描述

### Fixed
- Bug 修复描述
```

### 2. 提交更改

```bash
git add .
git commit -m "chore: bump version to 1.0.1"
git push origin main
```

### 3. 创建标签

```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

### 4. 自动构建

GitHub Actions 会自动:
- 构建 Docker 镜像
- 推送到 Docker Hub
- 打上版本标签

---

## 📦 Docker Hub 仓库设置

### 1. 创建仓库

1. 登录 Docker Hub
2. Create Repository
3. 仓库名: `novelvoice`
4. 描述: AI-powered audiobook generator
5. 公开仓库

### 2. 更新仓库说明

Docker Hub 仓库说明会自动从 README.md 同步 (通过 GitHub Actions)。

### 3. 添加标签

在 Docker Hub 仓库中添加标签:
- `latest` - 最新稳定版
- `v1.0.0` - 具体版本
- `1.0` - 主要版本
- `1` - 大版本

---

## 🎯 使用发布的镜像

### 从 Docker Hub 拉取

```bash
# 拉取最新版本
docker pull yourusername/novelvoice:latest

# 拉取特定版本
docker pull yourusername/novelvoice:1.0.0

# 运行容器
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  yourusername/novelvoice:latest
```

### 使用 Docker Compose

更新 `docker-compose.yml`:

```yaml
services:
  novelvoice:
    image: yourusername/novelvoice:latest
    # ... 其他配置
```

---

## 📊 监控和维护

### GitHub

- 查看 Actions 构建状态
- 处理 Issues 和 PR
- 更新文档

### Docker Hub

- 查看镜像拉取统计
- 管理镜像标签
- 更新仓库说明

---

## 🆘 故障排查

### GitHub Actions 构建失败

1. 检查 Secrets 配置
2. 查看构建日志
3. 验证 Dockerfile 语法

### Docker Hub 推送失败

1. 验证 Access Token
2. 检查仓库权限
3. 确认网络连接

### 多架构构建失败

1. 确保 QEMU 正确设置
2. 检查平台兼容性
3. 查看 buildx 日志

---

## 📚 相关链接

- [GitHub 仓库](https://github.com/yourusername/NovelVoice)
- [Docker Hub](https://hub.docker.com/r/yourusername/novelvoice)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Hub 文档](https://docs.docker.com/docker-hub/)

---

## ✅ 检查清单

发布前确认:

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
- [ ] LICENSE 文件存在
- [ ] .gitignore 配置正确
- [ ] GitHub Secrets 已配置
- [ ] Docker 镜像构建成功
- [ ] README 徽章已添加
- [ ] 版本号正确

---

祝发布顺利! 🎉
