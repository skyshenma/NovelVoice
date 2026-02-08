# NovelVoice - AI 有声书生成器

基于 Microsoft Edge TTS 的智能有声书生成工具,支持 TXT/EPUB 格式,提供现代化 Web 界面。

---

## ✨ 特性

- 🎙️ **高质量语音合成** - 基于 Microsoft Edge TTS,支持 31 种语音(中文、英语、日语)
- 📚 **多格式支持** - TXT/EPUB 文件自动解析和章节识别
- 🌐 **现代 Web 界面** - 美观易用的单页应用
- ⚡ **并发处理** - 多章节并行合成,提升效率
- 🔄 **自动重试** - 网络异常自动重试,确保稳定性
- 🔧 **配置热重载** - 无需重启即可应用新配置
- 📱 **Bark 推送** - 支持 iOS Bark 通知
- 🐳 **Docker 支持** - 一键部署,开箱即用
- 🔍 **版本检查** - 自动检测核心引擎更新

---

## 📋 环境要求

- **Python**: 3.12+
- **Docker**: 20.10+ (可选)
- **操作系统**: Windows / macOS / Linux

---

## 🚀 快速开始

### 方式一: Docker 部署 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd NovelVoice

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
open http://localhost:8000
```

详细说明请查看 [Docker 部署指南](DOCKER.md)

### 方式二: 本地运行

**快速安装** (macOS/Linux):

```bash
# 1. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置应用 (可选)
cp data/config/config.example.yml data/config/config.yml
# 编辑 data/config/config.yml 自定义配置

# 4. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 访问应用
open http://localhost:8000
```

**详细安装指南**:
- [Windows 安装](INSTALL.md#-windows-安装)
- [macOS 安装](INSTALL.md#-macos-安装)
- [Linux 安装](INSTALL.md#-linux-安装)

---

## 📖 使用指南

### 1. 上传书籍

- 支持格式: `.txt` / `.epub`
- 拖拽或点击上传
- 自动识别章节

### 2. 配置语音

- 选择发音人
- 调整语速、音量、音调
- 试听效果

### 3. 生成音频

- 选择要合成的章节
- 点击"开始合成"
- 实时查看进度

### 4. 下载音频

- 单章下载
- 批量下载
- 自动打包

---

## ⚙️ 配置

### 配置文件

编辑 `data/config/config.yml`:

```yaml
# TTS 配置
tts:
  default_voice: "zh-CN-XiaoxiaoNeural"  # 默认语音
  default_rate: "+0%"                     # 语速
  concurrency_limit: 2                    # 并发数

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8000

# Bark 推送
bark:
  enabled: false
  api_key: ""
```

### 配置热重载

修改配置文件后,无需重启服务即可应用新配置:

1. 编辑 `data/config/config.yml` 文件
2. 在 Web 界面点击"重载配置"按钮(位于配音设置标题栏)
3. 配置立即生效,正在运行的任务不受影响

> 💡 **提示**: 配置重载功能支持 YAML 格式验证,如果配置文件格式错误,会保留原配置并提示错误信息。

**支持的语音** (共31种):
- 🇨🇳 **普通话**: `zh-CN-XiaoxiaoNeural` (女-温暖), `zh-CN-YunxiNeural` (男-通用), `zh-CN-YunyangNeural` (男-专业) 等
- 🗣️ **方言**: `zh-CN-liaoning-XiaobeiNeural` (辽宁-女-幽默), `zh-CN-shaanxi-XiaoniNeural` (陕西-女-明亮)
- 🇭🇰 **粤语**: `zh-HK-HiuGaaiNeural`, `zh-HK-WanLungNeural` 等
- 🇹🇼 **台湾国语**: `zh-TW-HsiaoChenNeural`, `zh-TW-YunJheNeural` 等
- 🇺🇸 **美式英语**: `en-US-AvaNeural`, `en-US-AndrewNeural`, `en-US-JennyNeural` 等
- 🇬🇧 **英式英语**: `en-GB-LibbyNeural`, `en-GB-RyanNeural` 等
- 🇨🇦 **加拿大英语**: `en-CA-ClaraNeural`, `en-CA-LiamNeural`
- 🇯🇵 **日语**: `ja-JP-NanamiNeural`, `ja-JP-KeitaNeural`

完整列表请查看 [配置指南](CONFIG_GUIDE.md)

详细配置说明请查看 [配置指南](CONFIG_GUIDE.md)

### 环境变量

```bash
# Docker 环境变量
NOVELVOICE_DATA_DIR=/data
NOVELVOICE_HOST=0.0.0.0
NOVELVOICE_PORT=8000
```

---

## 📁 项目结构

```
NovelVoice/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 主程序
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── schemas/           # 数据模型
│   └── services/          # 业务逻辑
├── data/                  # 数据目录
│   ├── config/           # 配置文件
│   ├── app/              # 书籍和音频
│   └── cache/            # 缓存文件
├── static/               # Web 界面
├── Dockerfile            # Docker 镜像
├── docker-compose.yml    # Docker Compose
└── requirements.txt      # Python 依赖
```

详细说明请查看 [项目结构](PROJECT_STRUCTURE.md)

---

## 🔧 开发

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行开发服务器

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 代码规范

- Python 3.12+
- 使用类型注解
- 遵循 PEP 8

---

## 🐳 Docker

### 构建镜像

```bash
docker build -t novelvoice:latest .
```

### 运行容器

```bash
docker run -d \
  --name novelvoice \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  novelvoice:latest
```

### 使用 Docker Compose

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

详细说明请查看 [Docker 部署指南](DOCKER.md)

---

## 📊 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 + TailwindCSS
- **TTS**: Microsoft Edge TTS
- **文件处理**: ebooklib + BeautifulSoup4
- **容器化**: Docker + Docker Compose

---

## 🔍 版本检查

应用启动时会自动检查 edge-tts 核心引擎的版本更新:

- 自动检测最新版本
- Web UI 弹窗提示
- 提供更新命令

---

## 📝 文档

- [安装指南](INSTALL.md) - Windows/macOS/Linux 详细安装步骤
- [快速开始](QUICKSTART.md) - 快速上手指南
- [配置指南](CONFIG_GUIDE.md) - 详细配置说明
- [安全指南](SECURITY.md) - 配置文件安全管理
- [Docker 部署](DOCKER.md) - Docker 部署指南
- [项目结构](PROJECT_STRUCTURE.md) - 代码结构说明

---

## 🆘 故障排查

### 服务无法启动

```bash
# 检查端口占用
lsof -i :8000

# 查看日志
docker-compose logs
```

### 音频生成失败

- 检查网络连接
- 增加重试次数
- 降低并发数

### 配置不生效

- 重启服务
- 检查配置文件格式
- 查看启动日志

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Microsoft Edge TTS](https://github.com/rany2/edge-tts) - 核心 TTS 引擎
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Vue.js](https://vuejs.org/) - 前端框架
