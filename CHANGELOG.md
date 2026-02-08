# 更新日志

NovelVoice 的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
并且本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [未发布]


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

[未发布]: https://github.com/skyshenma/NovelVoice/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/skyshenma/NovelVoice/releases/tag/v1.0.0
