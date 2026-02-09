# 更新日志

NovelVoice 的所有重要更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
并且本项目遵循 [语义化版本控制](https://semver.org/lang/zh-CN/)。

## [未发布]

## [1.3.1] - 2026-02-09

### Fixed
- **TTS 参数清理**: 优化了 `TTSProcessor` 中的 `clean_param` 逻辑，修复了语速/音量调整时可能出现的重复百分号（如 `+0%%`）导致合成失败的问题。
- **预览接口同步**: 同步更新了试听预览接口，确保参数传递的一致性。

### Changed
- **本地开发环境优化**: 重构了 `docker-compose.dev.yml`，默认支持代码挂载热重载（Hot-reload），并优化了数据目录挂载结构。

## [1.3.0] - 2026-02-09

### Added
- **SQLite 数据库**: 引入 SQLite 替代 JSON 文件进行任务管理，显著提升大章节并发处理的稳定性，并解决文件损坏风险。
- **自动数据迁移**: 启动时自动将旧版的 `tasks.json` 数据同步至 SQLite 数据库。
- **Docker 部署优化**: 优化了 Docker Compose 配置，明确了 `TZ` 环境变量与 `/etc/localtime` 挂载的优先级关系。
- **双层部署模型**: 在根目录提供一键运行的 `docker-compose.yml`（直接拉取镜像），并将高级构建与开发工具移入 `deploy/docker/`。

### Changed
- **项目结构重组**: 将根目录的所有 Markdown 文档移至 `docs/` 文件夹，清理根目录杂碎。
- **链接与路径同步**: 全面更新了 `README.md` 及所有文档中的链接和 Docker 运行指令。

### Fixed
- **后台任务静默失败**: 修复了 `app/api/endpoints/tasks.py` 中由于变量遮蔽导致的后台 TTS 任务无法正常启动的问题。
- **配置冗余**: 移除了 `config.yml` 中重复的 `logging` 配置节。

### Removed
- **环境清理**: 删除了所有测试残留文件、macOS 系统元数据 (`.DS_Store`) 以及 Python 缓存目录。

## [1.2.2] - 2024-03-21

### Added
- 支持更多语言和语音。
- 增强了进度显示。

## [1.2.1] - 2024-03-20

### Fixed
- 修复了 Docker 环境下的路径配置问题。

## [1.2.0] - 2024-03-15

### Changed
- 重构配置系统，全面移除硬编码值。
