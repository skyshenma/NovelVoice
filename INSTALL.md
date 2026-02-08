# NovelVoice 本地安装指南

本文档提供 Windows、macOS 和 Linux 三个平台的详细安装步骤。

---

## 📋 系统要求

- **Python**: 3.12 或更高版本
- **磁盘空间**: 至少 500MB
- **内存**: 建议 2GB 以上
- **网络**: 需要访问 Microsoft Edge TTS 服务

---

## 🪟 Windows 安装

### 1. 安装 Python 3.12

**方式一: 从官网下载**

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.12+ 安装包
3. 运行安装程序
   - ✅ 勾选 "Add Python to PATH"
   - 点击 "Install Now"

**方式二: 使用 winget**

```powershell
# 使用 Windows Package Manager
winget install Python.Python.3.12
```

**验证安装**

```powershell
python --version
# 应显示: Python 3.12.x
```

### 2. 下载项目

```powershell
# 使用 Git (推荐)
git clone https://github.com/yourusername/NovelVoice.git
cd NovelVoice

# 或下载 ZIP 并解压
```

### 3. 创建虚拟环境

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 激活后,命令提示符前会显示 (.venv)
```

### 4. 安装依赖

```powershell
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 5. 配置应用 (可选)

```powershell
# 复制配置示例
copy data\config\config.example.yml data\config\config.yml

# 使用记事本编辑配置
notepad data\config\config.yml
```

### 6. 启动服务

```powershell
# 启动应用
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用开发模式(支持热重载)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. 访问应用

打开浏览器访问: http://localhost:8000

### Windows 故障排查

**问题: Python 命令未找到**
```powershell
# 检查 Python 是否在 PATH 中
where python

# 如果没有,手动添加到环境变量
# 控制面板 → 系统 → 高级系统设置 → 环境变量
```

**问题: 权限错误**
```powershell
# 以管理员身份运行 PowerShell
# 或修改执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**问题: 端口被占用**
```powershell
# 查看端口占用
netstat -ano | findstr :8000

# 使用其他端口
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 🍎 macOS 安装

### 1. 安装 Python 3.12

**方式一: 使用 Homebrew (推荐)**

```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.12
brew install python@3.12

# 验证安装
python3.12 --version
```

**方式二: 从官网下载**

1. 访问 https://www.python.org/downloads/
2. 下载 macOS 安装包
3. 运行 .pkg 文件安装

### 2. 下载项目

```bash
# 使用 Git (推荐)
git clone https://github.com/yourusername/NovelVoice.git
cd NovelVoice

# 或使用 curl 下载
curl -L https://github.com/yourusername/NovelVoice/archive/main.zip -o NovelVoice.zip
unzip NovelVoice.zip
cd NovelVoice-main
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3.12 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 激活后,命令提示符前会显示 (.venv)
```

### 4. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 5. 配置应用 (可选)

```bash
# 复制配置示例
cp data/config/config.example.yml data/config/config.yml

# 使用 vim 或其他编辑器编辑
vim data/config/config.yml
# 或
nano data/config/config.yml
# 或
open -a TextEdit data/config/config.yml
```

### 6. 启动服务

```bash
# 启动应用
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用开发模式(支持热重载)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. 访问应用

打开浏览器访问: http://localhost:8000

或使用命令:
```bash
open http://localhost:8000
```

### macOS 故障排查

**问题: 权限被拒绝**
```bash
# 给脚本添加执行权限
chmod +x docker-entrypoint.sh

# 检查目录权限
ls -la data/
```

**问题: 端口被占用**
```bash
# 查看端口占用
lsof -i :8000

# 杀死占用进程
kill -9 <PID>

# 或使用其他端口
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**问题: SSL 证书错误**
```bash
# 安装证书
/Applications/Python\ 3.12/Install\ Certificates.command
```

---

## 🐧 Linux 安装

### 1. 安装 Python 3.12

**Ubuntu/Debian**

```bash
# 更新包列表
sudo apt update

# 安装依赖
sudo apt install -y software-properties-common

# 添加 deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# 安装 Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 验证安装
python3.12 --version
```

**Fedora/RHEL/CentOS**

```bash
# Fedora
sudo dnf install -y python3.12 python3.12-devel

# RHEL/CentOS (需要 EPEL)
sudo yum install -y epel-release
sudo yum install -y python312 python312-devel
```

**Arch Linux**

```bash
# 安装 Python
sudo pacman -S python

# 验证版本
python --version
```

### 2. 下载项目

```bash
# 使用 Git (推荐)
git clone https://github.com/yourusername/NovelVoice.git
cd NovelVoice

# 或使用 wget
wget https://github.com/yourusername/NovelVoice/archive/main.tar.gz
tar -xzf main.tar.gz
cd NovelVoice-main
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3.12 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 激活后,命令提示符前会显示 (.venv)
```

### 4. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 5. 配置应用 (可选)

```bash
# 复制配置示例
cp data/config/config.example.yml data/config/config.yml

# 使用编辑器编辑
vim data/config/config.yml
# 或
nano data/config/config.yml
```

### 6. 启动服务

```bash
# 启动应用
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或使用开发模式(支持热重载)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. 访问应用

打开浏览器访问: http://localhost:8000

或使用命令:
```bash
xdg-open http://localhost:8000  # 大多数桌面环境
```

### Linux 故障排查

**问题: Python 版本不匹配**
```bash
# 检查可用的 Python 版本
ls /usr/bin/python*

# 使用特定版本
python3.12 -m venv .venv
```

**问题: 权限问题**
```bash
# 修改文件权限
chmod -R 755 data/

# 给脚本添加执行权限
chmod +x docker-entrypoint.sh
```

**问题: 端口被占用**
```bash
# 查看端口占用
sudo lsof -i :8000
# 或
sudo netstat -tulpn | grep :8000

# 杀死占用进程
sudo kill -9 <PID>
```

**问题: 防火墙阻止**
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 8000/tcp

# Fedora/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## 🔧 通用配置

### 修改默认端口

编辑 `data/config/config.yml`:

```yaml
server:
  port: 9000  # 改为其他端口
```

### 修改默认语音

编辑 `data/config/config.yml`:

```yaml
tts:
  default_voice: "zh-CN-YunxiNeural"  # 男声-通用
  # 更多选项:
  # zh-CN-XiaoxiaoNeural  # 女-温暖 (推荐听书)
  # zh-CN-YunyangNeural   # 男-专业 (新闻播报)
  # zh-CN-liaoning-XiaobeiNeural  # 女-幽默 (东北方言)
  # zh-CN-shaanxi-XiaoniNeural    # 女-明亮 (陕西方言)
  # zh-HK-HiuGaaiNeural   # 粤语-女-友好
  # en-US-JennyNeural     # 英语-女-友好
  # ja-JP-NanamiNeural    # 日语-女-友好
```

**支持 31 种语音**,包括:
- 普通话 (6种)
- 中国方言 (2种: 辽宁、陕西)
- 粤语 (3种)
- 台湾国语 (3种)
- 英语 (15种: 美国、英国、加拿大)
- 日语 (2种)

完整列表请查看 `data/config/config.example.yml`

### 启用 Bark 推送

```yaml
bark:
  enabled: true
  api_key: "your_bark_key"
  web_base_url: "http://localhost:8000"
```

---

## 🚀 开发模式

### 启用热重载

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 查看日志

```bash
# 应用会在控制台输出日志
# 错误日志会保存到 error.log
```

---

## 📦 更新应用

```bash
# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
```

---

## 🆘 获取帮助

- 查看 [README.md](README.md) - 项目概览
- 查看 [QUICKSTART.md](QUICKSTART.md) - 快速开始
- 查看 [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - 配置指南
- 查看 [DOCKER.md](DOCKER.md) - Docker 部署
- 提交 [Issue](https://github.com/yourusername/NovelVoice/issues) - 报告问题

---

## ✅ 安装成功检查

访问 http://localhost:8000 应该看到:
- ✅ NovelVoice Web 界面
- ✅ 可以上传书籍
- ✅ 可以选择语音
- ✅ 可以生成音频

如果遇到问题,请查看上方的故障排查部分。
