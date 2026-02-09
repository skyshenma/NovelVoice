# 快速开始指南

本指南帮助您快速部署和使用 NovelVoice。

---

## 🐳 方式一: Docker 部署 (推荐)

**最简单的方式** - 一键启动,无需配置:

```bash
# 1. 创建数据目录
mkdir -p novelvoice/data && cd novelvoice

# 2. 拉取并运行
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  skyshenma2024/novelvoice:latest

# 3. 访问应用
open http://localhost:8000
```

**就这么简单!** 应用已经运行,包含完整的默认配置。

### 使用 Docker Compose

```bash
# 1. 下载配置文件
curl -O https://raw.githubusercontent.com/skyshenma/NovelVoice/main/docker-compose.simple.yml

# 2. 启动服务
docker-compose -f docker-compose.simple.yml up -d

# 3. 访问应用
open http://localhost:8000
```

---
详细说明请查看 [docker.md](docker.md)

---

## 🔧 方式二: 本地运行

### 1. 创建虚拟环境

```bash
# 使用 Python 3.12
python3.12 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置应用 (可选)

```bash
# 复制配置示例
cp data/config/config.example.yml data/config/config.yml

# 编辑配置
vim data/config/config.yml
```

详细配置说明请查看 [config.md](config.md)

### 4. 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或使用开发模式(支持热重载):

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问应用

打开浏览器访问: http://localhost:8000

---

## 📖 基本使用

### 1. 上传书籍

- 点击或拖拽上传 TXT/EPUB 文件
- 等待自动解析章节

### 2. 配置语音

- 选择发音人
- 调整语速、音量、音调
- 点击"试听"测试效果

### 3. 生成音频

- 选择要合成的章节
- 点击"开始合成"
- 查看实时进度

### 4. 下载音频

- 单章下载: 点击章节的下载按钮
- 批量下载: 选择多章后点击"批量下载"

---

## ⚙️ 常用配置

### 修改默认语音

```yaml
tts:
  default_voice: "zh-CN-YunxiNeural"  # 男声-通用
  # 或选择其他语音:
  # zh-CN-XiaoxiaoNeural  # 女-温暖 (推荐听书)
  # zh-CN-YunyangNeural   # 男-专业 (新闻播报)
  # zh-CN-liaoning-XiaobeiNeural  # 女-幽默 (东北方言)
  # en-US-JennyNeural     # 英语-女-友好
  # ja-JP-NanamiNeural    # 日语-女-友好
```

**支持 31 种语音**,包括普通话、方言、粤语、台湾国语、英语、日语等。
完整列表请查看 `data/config/config.example.yml`

### 修改服务器端口

```yaml
server:
  port: 9000
```

### 提高合成速度

```yaml
tts:
  concurrency_limit: 3  # 增加并发数
  default_rate: "+20%"  # 加快语速
```

### 启用 Bark 推送通知

```yaml
bark:
  enabled: true
  api_key: "your_bark_key"
  web_base_url: "http://your_server_ip:8000"
```

更多配置选项请参考 [config.md](config.md)

---

## 🆘 常见问题

### Q: 服务启动失败?
A: 检查端口是否被占用: `lsof -i :8000`

### Q: 音频生成失败?
A: 检查网络连接,或增加重试次数和超时时间

### Q: 配置修改不生效?
A: 需要重启服务才能加载新配置

### Q: 如何更新到最新版本?
A: 应用会自动检查 edge-tts 核心引擎更新并提示。对于 NovelVoice 自身的更新,请关注 GitHub Release 或拉取最新镜像。v1.3.0+ 版本在升级时会自动迁移旧的任务数据。

---

## 📚 更多文档

- [配置指南](config.md) - 详细配置说明
- [Docker 部署](docker.md) - Docker 部署指南
- [项目结构](structure.md) - 代码结构说明
