# NovelVoice 项目结构

```
NovelVoice/
├── README.md                   # 项目说明
├── requirements.txt            # Python 依赖 (Python 3.12+)
├── .python-version             # Python 版本标识
├── .gitignore                  # Git 忽略规则
│
├── deploy/                     # 部署相关 (v1.3.1+)
│   └── docker/
│       ├── Dockerfile          # Docker 镜像构建文件
│       ├── docker-compose.build.yml  # 源码构建配置
│       ├── entrypoint.sh       # 容器启动脚本
│       ├── docker-compose.dev.yml    # 本地开发配置
│       └── docker-compose.standalone.yml # 极简配置模板
├── docker-compose.yml          # 便捷部署配置 (根目录)
├── .dockerignore               # Docker 构建排除文件
│
├── app/                        # 应用代码
│   ├── main.py                 # FastAPI 主程序
│   │
│   ├── api/                    # API 路由
│   │   ├── api.py              # 路由注册
│   │   └── endpoints/          # API 端点
│   │       ├── books.py        # 书籍管理 API
│   │       ├── tasks.py        # 任务管理 API
│   │       ├── voice.py        # 语音相关 API
│   │       ├── config.py       # 配置管理 API
│   │       └── version.py      # 版本检查 API ⭐
│   │
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置常量
│   │   ├── config_loader.py    # YAML 配置加载器
│   │   ├── path_adapter.py     # 路径自适应系统 ⭐
│   │   └── state.py            # 全局状态管理
│   │
│   ├── schemas/                # 数据模型
│   │   ├── book.py             # 书籍数据模型
│   │   └── config.py           # 配置数据模型
│   │
│   └── services/               # 业务逻辑
│       ├── parsers/        # 书籍解析器 ⭐
│       │   ├── factory.py  # 解析器工厂
│       │   ├── epub.py     # EPUB 解析 (Spine/TOC)
│       │   ├── txt.py      # TXT 解析 (正则)
│       │   └── base.py     # 解析器基类
│       │
│       ├── book_manager.py     # 书籍管理 (调用 Parsers)
│       ├── tts_engine.py       # TTS 引擎
│       ├── notifier.py         # Bark 通知
│       └── version_checker.py  # 版本检查服务 ⭐
│
│   ├── db/                 # 数据库目录 (v1.3.0+) ⭐
│   │   └── novelvoice.db   # SQLite 数据库文件
│   └── cache/              # 缓存文件
│
├── static/                     # 静态文件
│   └── index.html              # Web 界面 (Vue 3 + TailwindCSS)
│
└── docs/
    ├── README.md               # 项目说明
    ├── quickstart.md           # 快速开始
    ├── config.md               # 配置指南
    ├── docker.md               # Docker 部署指南 ⭐
    └── structure.md            # 本文档
```

## 核心模块说明

### API 端点

- **books.py** - 书籍上传、列表、删除
- **tasks.py** - TTS 任务管理、进度查询
- **voice.py** - 语音列表、预览
- **config.py** - 配置读取、保存
- **version.py** - 版本检查、更新提示 ⭐

### 核心服务

- **book_manager.py** - 书籍解析、章节管理
- **tts_engine.py** - TTS 合成、并发控制
- **notifier.py** - Bark 推送通知
- **version_checker.py** - 版本检查、PyPI 查询 ⭐

### 配置系统

- **config_loader.py** - YAML 配置加载
- **path_adapter.py** - 路径自适应、数据迁移 ⭐
- **config.py** - 配置常量、环境变量

## 数据目录结构

```
data/
├── config/
│   └── config.yml              # 主配置文件
├── db/                         # 数据库目录 (v1.3.0+)
│   └── novelvoice.db           # 任务状态数据库
├── app/
│   └── books/
│       ├── 三体/
│       │   ├── metadata.json   # 书籍元数据
│       │   ├── chapters/       # 章节文本
│       │   │   ├── 001.txt
│       │   │   └── 002.txt
│       │   └── audio/          # 音频文件
│       │       ├── 001.mp3
│       │       └── 002.mp3
│       └── 另一本书/
└── cache/                      # 预览音频缓存
```

## 配置文件位置

**主配置**: `data/config/config.yml`  
**配置示例**: `data/config/config.example.yml`

## 快速开始

### 本地运行

```bash
# 1. 安装依赖 (Python 3.12+)
pip install -r requirements.txt

# 2. 配置应用 (可选)
cp data/config/config.example.yml data/config/config.yml

# 3. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
# 1. 启动服务
docker-compose up -d

# 2. 访问应用
open http://localhost:8000
```

详细说明请查看 [docker.md](docker.md)

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 + TailwindCSS
- **TTS**: Microsoft Edge TTS
- **数据库**: SQLite (v1.3.0 引入,取代 JSON)
- **文件处理**: ebooklib + BeautifulSoup4
- **配置**: PyYAML
- **容器化**: Docker + Docker Compose
