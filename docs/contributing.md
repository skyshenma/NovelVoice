# Contributing to NovelVoice

感谢您对 NovelVoice 的贡献!

## 🤝 如何贡献

### 报告 Bug

如果您发现了 Bug,请创建一个 Issue 并包含:

- 清晰的标题和描述
- 重现步骤
- 预期行为和实际行为
- 环境信息 (OS, Python 版本, Docker 版本等)
- 相关日志或截图

### 提出新功能

如果您有新功能建议:

1. 先搜索现有 Issues,避免重复
2. 创建新 Issue 描述功能需求
3. 说明使用场景和预期效果
4. 等待维护者反馈

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/yourusername/NovelVoice.git
   cd NovelVoice
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发和测试**
   ```bash
   # 创建虚拟环境
   python3.12 -m venv .venv
   source .venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 运行测试
   python -m uvicorn app.main:app --reload
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   # 或
   git commit -m "fix: fix bug description"
   ```

5. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 代码规范

### Python 代码

- 使用 Python 3.12+
- 遵循 PEP 8 规范
- 使用类型注解
- 添加必要的注释和文档字符串

### 提交信息

使用语义化提交信息:

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例:
```
feat: add support for PDF format
fix: resolve chapter parsing issue
docs: update installation guide
```

### 代码审查

所有 PR 需要:

- 通过 CI/CD 检查
- 至少一位维护者审查
- 解决所有评论和建议
- 保持提交历史清晰

## 🏗️ 项目结构

请参考 [structure.md](structure.md) 了解项目结构。

## 🧪 测试

在提交 PR 前,请确保:

- [ ] 代码能正常运行
- [ ] 没有引入新的 Bug
- [ ] 文档已更新
- [ ] Docker 镜像能正常构建

## 📚 文档

如果您的更改影响用户使用,请更新相关文档:

- README.md
- quickstart.md
- config.md
- docker.md

## ❓ 需要帮助?

- 查看 [文档](README.md)
- 搜索现有 [Issues](https://github.com/yourusername/NovelVoice/issues)
- 创建新 Issue 提问

## 📄 许可证

贡献的代码将采用 [MIT License](LICENSE)。

---

再次感谢您的贡献! 🎉
