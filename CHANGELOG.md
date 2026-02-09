# 更新日志

NovelVoice 的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
并且本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [未发布]

## [1.2.2] - 2026-02-08

### 新增
- **增强日志系统**：
  - 统一日志管理：所有日志集中存储在 `data/logs` 目录
  - 新增 `app.log` (主程序日志) 和 `error.log` (错误日志)
  - 支持日志自动轮转（默认 10MB/个，保留 5 个备份）
  - 支持在 `config.yml` 中配置日志等级 (`logging.level`)
  - 优化日志格式，包含时间戳、模块名和日志等级

### 修复
- **TTS 任务生成失败**：修复了 `run_tts_task` 中的变量命名冲突导致后台任务静默失败的问题（点击生成按钮无反应）
- **配置文件冲突**：修复了 `config.yml` 中可能存在的重复日志配置项
- **Docker 路径配置问题**：修复在 Docker 环境中设置 `NOVELVOICE_DATA_DIR` 后，`APP_DATA_DIR` 和 `CACHE_DIR` 未正确使用该路径的问题
  - 现在当设置 `NOVELVOICE_DATA_DIR=/data` 时，系统会自动使用 `/data/app` 和 `/data/cache`
  - 简化 Docker 配置，用户只需设置一个环境变量即可

## [1.2.1] - 2026-02-08

### 改进
- **配置加载优化**：默认配置从 `config.example.yml` 动态加载，不再硬编码
  - 更新默认配置只需修改 `config.example.yml`，无需修改代码
  - 减少约 80 行硬编码配置，提高可维护性
  - 保留最小化硬编码配置作为最后的后备方案
- **全面移除硬编码值**：所有配置参数现在都从 `config.yml` 读取
  - TTS 引擎：`max_chars`、`timeout`、`max_logs` 从配置读取
  - Bark 通知：静默时间段（`silent_hours`）和 HTTP 超时（`http_timeout`）可配置
  - 文本处理：`chunk_size` 从配置读取
  - 新增配置项：`logging.max_logs`、`bark.silent_hours`、`bark.http_timeout`、`tts.timeout`

## [1.2.0] - 2026-02-08

### 新增
- 书籍详情页面新增章节筛选功能，支持按状态筛选（全部/已完成/失败/等待中）
- 筛选器显示各状态的章节数量，方便快速定位
- "全选"功能智能适配当前筛选器，只选中可见章节
- **文件管理弹窗**：新增文件管理器模态框，替代Docker环境下无法使用的"打开文件夹"功能
  - 查看所有已生成的音频文件列表
  - 支持单个文件下载
  - 支持批量选择和ZIP打包下载
  - 支持章节范围筛选（如 "1-5,8"）
  - 显示文件大小和选中数量
  - 集成合并音频功能

### 改进
- 将"打开文件夹"按钮更名为"文件管理"，提供更友好的文件管理体验
- 新增 `/api/files/{book_name}` 端点用于获取文件列表
- 新增 `/api/file/{book_name}/{file_id}` 端点用于下载单个文件

## [1.1.2] - 2026-02-08

### 修复
- 修复前端请求 TTS 任务时语速和音量参数错误 (去除重复的百分号后缀)，解决 "Invalid rate '+0%%'" 导致生成失败的问题
- 增强后端 TTS 参数处理逻辑，防止因参数为空导致的 "rate must be str" 错误

## [1.1.1] - 2026-02-08

### 修复
- 修复 Docker 环境下配置文件路径识别错误的问题 (优先使用 `NOVELVOICE_DATA_DIR` 环境变量)

## [1.1.0] - 2026-02-08


### 优化
- 重构 EPUB 解析逻辑：优先使用结构化元数据 (Spine/TOC)，修复章节乱序和层级丢失问题
- 引入 ParserFactory 模式，分离不同格式的解析逻辑

### 修复
- 修复配置在后端未开启热重载时无法持久化的问题 (通过前端强制重载实现)
- 修复版本更新弹窗无法关闭及样式问题
- 修复侧边栏布局，将高级设置移至更合适的位置
- 修复启动时语音列表可能为空的问题

### 新增
- NovelVoice 初始版本
- 支持 TXT/EPUB 文件格式
- 集成 Microsoft Edge TTS
- 基于 Vue 3 的现代 Web 界面
- Docker 支持
- 自动版本检查
- Bark 通知支持
- 多章节并发处理
- 自动重试机制

### 特性
- 🎙️ 高质量语音合成
- 📚 多格式支持 (TXT/EPUB)
- 🌐 现代 Web 界面
- ⚡ 并发处理
- 🔄 自动重试
- 📱 Bark 推送通知
- 🐳 Docker 支持
- 🔍 版本检查

## [1.0.0] - 2026-02-07

### 新增
- 第一个稳定版本
- 完整的文档
- Docker Hub 支持
- GitHub Actions CI/CD

---

## 发布说明

### v1.0.0 - 初始版本

**核心特性:**
- 基于 Microsoft Edge TTS 的 AI 有声书生成
- 支持 TXT 和 EPUB 格式
- 自动章节检测和解析
- 现代单页 Web 应用
- 实时进度跟踪
- 批量下载支持

**技术栈:**
- Python 3.12+
- FastAPI + Uvicorn
- Vue 3 + TailwindCSS
- Docker + Docker Compose
- Microsoft Edge TTS

**部署:**
- 支持本地安装
- 支持 Docker 部署
- 详尽的文档

---

[未发布]: https://github.com/skyshenma/NovelVoice/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.2.2
[1.2.1]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.2.1
[1.2.0]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.2.0
[1.1.2]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.1.2
[1.1.1]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.1.1
[1.1.0]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.1.0
[1.0.0]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.0.0
