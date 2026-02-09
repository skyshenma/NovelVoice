# NovelVoice 本地开发指南

本文档说明如何使用本地 Docker Compose 配置进行开发和调试。

## 快速开始

### 1. 启动本地开发环境

```bash
# 使用本地配置启动
docker-compose -f deploy/docker/docker-compose.dev.yml up -d

# 查看日志
docker-compose -f deploy/docker/docker-compose.dev.yml logs -f
```

### 2. 停止服务

```bash
docker-compose -f deploy/docker/compose.local.yml down
```

### 3. 重新构建镜像

当你修改了代码后，需要重新构建镜像：

```bash
# 停止并删除容器
docker-compose -f deploy/docker/docker-compose.dev.yml down

# 重新构建并启动
docker-compose -f deploy/docker/docker-compose.dev.yml up -d --build

# 或者分步执行
docker-compose -f deploy/docker/docker-compose.dev.yml build
docker-compose -f deploy/docker/docker-compose.dev.yml up -d
```

> **⚠️ 重要提示**：修改静态文件（如 `static/index.html`）后，**必须使用 `--build` 参数重新构建镜像**，简单的 `restart` 命令不会更新静态文件。这是因为静态文件在构建时被复制到 Docker 镜像中。


## 配置说明

### docker-compose.local.yml

本地开发版配置文件，主要特点：

- ✅ 使用本地构建 (`build: .`)
- ✅ 容器名称为 `novelvoice-local`
- ✅ 挂载 `data` 目录用于数据持久化 (包含 `data/db` 数据库)
- ✅ 挂载 `config.yml` 方便本地编辑配置
- ✅ 从 `.env` 文件加载环境变量
- ✅ 更宽松的资源限制 (4GB 内存)
- ✅ 保留更多日志 (50MB × 5 个文件)

### .env

本地环境变量配置文件，包含：

- 服务器配置 (端口 8000)
- TTS 配置 (默认中文语音)
- Bark 通知 (开发环境默认禁用)

**注意**: `.env` 文件已添加到 `.gitignore`，不会被提交到 Git。

## 开发工作流

### 修复 Bug 的典型流程

1. **修改代码**
   ```bash
   # 在本地编辑器中修改代码
   vim app/services/tts_engine.py
   ```

2. **重新构建并测试**
   ```bash
   # 重新构建镜像
   docker-compose -f deploy/docker/docker-compose.dev.yml up -d --build
   
   # 查看日志确认修复
   docker-compose -f deploy/docker/docker-compose.dev.yml logs -f
   ```

3. **测试验证**
   - 访问 http://localhost:8000
   - 测试相关功能
   - 检查日志输出

4. **提交代码**
   ```bash
   git add .
   git commit -m "fix: 修复 XXX 问题"
   ```

5. **准备发布** (等你通知后再执行)
   ```bash
   # 构建生产镜像
   docker build -t skyshenma2024/novelvoice:latest .
   
   # 推送到 Docker Hub
   docker push skyshenma2024/novelvoice:latest
   
   # 提交到 GitHub
   git push origin main
   ```

## 新功能说明

### 文件管理器

从 v1.2.0 开始，NovelVoice 提供了文件管理器功能，替代了 Docker 环境下无法使用的"打开文件夹"功能。

**如何使用：**

1. 进入书籍详情页面
2. 点击顶部的 **"📂 文件管理"** 按钮
3. 在弹出的文件管理器中可以：
   - 📋 查看所有已生成的音频文件
   - ⬇️ 下载单个文件（点击文件右侧的"下载"按钮）
   - 📦 批量下载为 ZIP（选择文件后点击"下载选中"）
   - 📦 下载全部文件为 ZIP
   - 🔢 使用范围筛选（如输入 "1-5,8" 选择第1-5章和第8章）
   - ☑️ 使用"全选"快速选择所有文件
   - 🔗 合并音频文件

**技术细节：**
- 文件列表通过 `/api/files/{book_name}` 端点获取
- 单文件下载通过 `/api/file/{book_name}/{file_id}` 端点
- ZIP 下载使用现有的 `/api/download/{book_name}` 端点


## 实时代码挂载 (可选)

如果你想在不重新构建镜像的情况下测试代码修改，可以启用代码挂载：

1. 编辑 `docker-compose.local.yml`
2. 取消以下行的注释：
   ```yaml
   # - ./app:/app/app:ro
   # - ./static:/app/static:ro
   ```
3. 重启容器

**注意**: 这种方式适合快速测试，但某些修改可能需要重启容器才能生效。

## 常用命令

```bash
# 查看容器状态
docker-compose -f docker-compose.local.yml ps

# 进入容器
docker-compose -f docker-compose.local.yml exec novelvoice bash

# 查看实时日志
docker-compose -f docker-compose.local.yml logs -f

# 重启服务
docker-compose -f docker-compose.local.yml restart

# 清理所有数据 (谨慎使用!)
docker-compose -f docker-compose.local.yml down -v
```

## 与生产环境的区别

| 配置项 | 本地开发 | 生产环境 |
|--------|---------|---------|
| 镜像来源 | 本地构建 | Docker Hub |
| 容器名称 | novelvoice-local | novelvoice |
| 内存限制 | 4GB | 2GB |
| 日志大小 | 50MB × 5 | 10MB × 5 |
| Bark 通知 | 默认禁用 | 可选启用 |
| 代码挂载 | 可选支持 | 不支持 |

## 故障排查

### 端口已被占用

```bash
# 检查端口占用
lsof -i :8000

# 修改端口 (编辑 .env 或 docker-compose.local.yml)
NOVELVOICE_PORT=8001
```

### 容器无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.local.yml logs

# 检查配置文件
docker-compose -f docker-compose.local.yml config
```

### 日志文件位置

日志文件存储在挂载的 `data/logs` 目录下：
- `data/logs/app.log`: 主程序日志
- `data/logs/error.log`: 错误日志

可以使用 `tail -f data/logs/app.log` 实时查看。

### 数据丢失

确保 `./data` 目录已正确挂载：

```bash
# 检查挂载
docker-compose -f docker-compose.local.yml exec novelvoice ls -la /data
```

## 下一步

- 修复你发现的 bug
- 测试验证修复效果
- 准备好后通知我，我会帮你推送到 GitHub 和 Docker Hub
