# Docker 部署指南

本文档介绍如何使用 Docker 部署 NovelVoice。

---

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (可选)

---

## 🚀 快速开始

### 方式一: 一键启动 (最简单)

**直接从 Docker Hub 拉取并运行**,无需克隆代码:

```bash
# 1. 创建数据目录
mkdir -p novelvoice/data && cd novelvoice

# 2. 拉取并运行
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  skyshenma2024/novelvoice:latest

# 3. 查看日志
docker logs -f novelvoice

# 4. 访问应用
open http://localhost:8000
```

**就这么简单!** 应用已经运行,包含完整的默认配置。

### 方式二: 使用 Docker Compose (推荐用于生产)

```bash
# 1. 下载配置文件
curl -O https://raw.githubusercontent.com/skyshenma/NovelVoice/main/docker-compose.simple.yml

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问应用
open http://localhost:8000
```

### 方式三: 本地构建镜像

如果你想自己构建镜像:

```bash
# 1. 克隆项目
git clone https://github.com/skyshenma/NovelVoice.git
cd NovelVoice

# 2. 构建镜像
docker build -t novelvoice:latest -f deploy/docker/Dockerfile .

# 3. 运行容器
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  novelvoice:latest
```

---

## 📁 数据持久化

### 数据卷说明

```yaml
volumes:
  - ./data:/data                # 所有数据目录
  - ./data/config:/data/config  # 配置文件
  - ./data/db:/data/db          # 数据库目录 (v1.3.0+)
```

### 目录结构

```
.
├── deploy/                 # 部署相关 (v1.3.1+)
│   └── docker/
│       ├── Dockerfile      # 构建文件
│       ├── docker-compose.build.yml  # 源码构建配置
│       ├── docker-compose.dev.yml    # 开发调试配置
│       ├── docker-compose.standalone.yml # 独立镜像部署配置
│       └── entrypoint.sh   # 启动脚本
├── docker-compose.yml      # 便捷部署配置 (根目录)
├── docker-compose.simple.yml # 单文件部署示例 (根目录)
├── data/                   # 数据根目录
│   ├── config/
│   │   └── config.yml      # 配置文件
│   ├── db/
│   │   └── novelvoice.db   # SQLite 数据库
│   ├── app/
│   │   └── books/          # 书籍数据
│   │       ├── book1/
│   │       │   ├── metadata.json
│   │       │   ├── chapters/
│   │       │   └── audio/
│   │       └── book2/
│   └── cache/              # 缓存文件
└── ...
```

---

## ⚙️ 配置说明

### 默认配置

**Docker 镜像已包含完整的默认配置,可以直接运行,无需任何配置文件!**

默认配置包括:
- ✅ TTS 语音: zh-CN-XiaoxiaoNeural (晓晓)
- ✅ 并发限制: 2
- ✅ 数据目录: /data
- ✅ 服务端口: 8000
- ✅ 所有核心功能

### 自定义配置

如果需要自定义配置,有三种方式:

#### 方式一: 使用环境变量 (推荐)

在 `docker run` 命令中添加 `-e` 参数:

```bash
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e NOVELVOICE_TTS_VOICE=zh-CN-YunxiNeural \
  -e NOVELVOICE_TTS_CONCURRENCY=4 \
  -e NOVELVOICE_BARK_ENABLED=true \
  -e NOVELVOICE_BARK_API_KEY=your_bark_key_here \
  skyshenma2024/novelvoice:latest
```

或在 `docker-compose.yml` 中配置:

```yaml
environment:
  - NOVELVOICE_TTS_VOICE=zh-CN-YunxiNeural
  - NOVELVOICE_TTS_CONCURRENCY=4
  - NOVELVOICE_BARK_ENABLED=true
  - NOVELVOICE_BARK_API_KEY=your_bark_key_here
```

#### 方式二: 使用 .env 文件

创建 `.env` 文件:

```bash
NOVELVOICE_TTS_VOICE=zh-CN-YunxiNeural
NOVELVOICE_TTS_CONCURRENCY=4
NOVELVOICE_BARK_ENABLED=true
NOVELVOICE_BARK_API_KEY=your_bark_key_here
```

在 `docker-compose.yml` 中引用:

```yaml
env_file:
  - .env
```

#### 方式三: 挂载配置文件

创建 `config.yml` 并挂载:

```bash
# 1. 下载示例配置
curl -O https://raw.githubusercontent.com/skyshenma/NovelVoice/main/data/config/config.example.yml

# 2. 重命名并编辑
mv config.example.yml config.yml
nano config.yml

# 3. 挂载配置文件
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/config.yml:/data/config/config.yml \
  skyshenma2024/novelvoice:latest
```

### 配置优先级

配置加载优先级(从高到低):
1. **环境变量** (最高优先级)
2. **config.yml** (如果挂载)
3. **默认配置** (内置)

---

**语音选项** (共31种):
- `zh-CN-XiaoxiaoNeural` - 普通话-女-温暖 (推荐)
- `zh-CN-YunxiNeural` - 普通话-男-通用
- `zh-CN-YunyangNeural` - 普通话-男-专业
- `zh-CN-liaoning-XiaobeiNeural` - 东北话-女-幽默
- `zh-CN-shaanxi-XiaoniNeural` - 陕西话-女-明亮
- `zh-HK-HiuGaaiNeural` - 粤语-女-友好
- `en-US-JennyNeural` - 英语-女-友好
- `ja-JP-NanamiNeural` - 日语-女-友好

完整列表请查看 `data/config/config.example.yml`

### 配置文件

首次启动时,会自动从 `config.example.yml` 创建 `config.yml`。

编辑配置文件:

```bash
# 编辑配置
vim data/config/config.yml

# 重启服务使配置生效
docker-compose restart
```

---

## 🔧 常用命令

### 进入项目目录
# 启动服务 (推荐)
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止并删除容器
docker-compose down
```

### 镜像管理

```bash
# 构建镜像
docker-compose build

# 重新构建镜像
docker-compose build --no-cache

# 查看镜像
docker images | grep novelvoice

# 删除镜像
docker rmi novelvoice:latest
```

### 数据管理

```bash
# 备份数据
tar -czf novelvoice-data-backup.tar.gz data/

# 恢复数据
tar -xzf novelvoice-data-backup.tar.gz

# 清理缓存
rm -rf data/cache/*
```

---

## 🐛 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查容器状态
docker-compose ps

# 进入容器调试
docker-compose exec novelvoice bash
```

### 权限问题

```bash
# 修复数据目录权限
chmod -R 755 data/
```

> [!IMPORTANT]
> **本地构建用户**: 如果您修改了源码并想在本地构建运行,请使用:
> `docker-compose -f deploy/docker/docker-compose.build.yml up -d --build`

---

## 📊 资源限制

在 `docker-compose.yml` 中配置资源限制:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # 最多使用 2 个 CPU
      memory: 2G       # 最多使用 2GB 内存
    reservations:
      cpus: '0.5'      # 保留 0.5 个 CPU
      memory: 512M     # 保留 512MB 内存
```

---

## 🔒 安全建议

1. **不要暴露到公网**: 默认配置仅用于本地使用
2. **使用反向代理**: 生产环境建议使用 Nginx/Traefik
3. **定期备份数据**: 重要数据定期备份
4. **更新镜像**: 定期更新到最新版本

---

## 🌐 生产部署

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 使用 HTTPS

```bash
# 使用 Let's Encrypt
certbot --nginx -d your-domain.com
```

---

## 📝 更新应用

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose -f deploy/docker/compose.yml logs -f
```

---

## 🆘 获取帮助

- 查看日志: `docker-compose logs -f`
- 进入容器: `docker-compose exec novelvoice bash`
- 健康检查: `curl http://localhost:8000/api/books`
