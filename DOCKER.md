# Docker 部署指南

本文档介绍如何使用 Docker 部署 NovelVoice。

---

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (可选)

---

## 🚀 快速开始

### 方式一: 使用 Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd NovelVoice

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问应用
open http://localhost:8000
```

### 方式二: 使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t novelvoice:latest .

# 2. 运行容器
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  novelvoice:latest

# 3. 查看日志
docker logs -f novelvoice
```

---

## 📁 数据持久化

### 数据卷说明

```yaml
volumes:
  - ./data:/data              # 所有数据目录
  - ./data/config:/data/config  # 配置文件
```

### 目录结构

```
data/
├── config/
│   └── config.yml          # 配置文件
├── app/
│   └── books/              # 书籍数据
│       ├── book1/
│       │   ├── metadata.json
│       │   ├── chapters/
│       │   └── audio/
│       └── book2/
└── cache/                  # 缓存文件
```

---

## ⚙️ 配置

### 环境变量

在 `docker-compose.yml` 中配置:

```yaml
environment:
  ### 常用环境变量
  # TTS 配置
  - NOVELVOICE_TTS_VOICE=zh-CN-XiaoxiaoNeural  # 默认语音
  - NOVELVOICE_TTS_RATE=+0%                     # 语速
  - NOVELVOICE_TTS_CONCURRENCY=2                # 并发数

  # 服务器配置
  - NOVELVOICE_HOST=0.0.0.0
  - NOVELVOICE_PORT=8000

  # Bark 推送
  - NOVELVOICE_BARK_ENABLED=false
  - NOVELVOICE_BARK_API_KEY=your_key_here
```

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

### 服务管理

```bash
# 启动服务
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

### 端口冲突

修改 `docker-compose.yml` 中的端口映射:

```yaml
ports:
  - "8080:8000"  # 使用 8080 端口
```

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
docker-compose logs -f
```

---

## 🆘 获取帮助

- 查看日志: `docker-compose logs -f`
- 进入容器: `docker-compose exec novelvoice bash`
- 健康检查: `curl http://localhost:8000/api/books`
