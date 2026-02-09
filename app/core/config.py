"""
应用配置模块
整合 YAML 配置和环境变量
"""

import os
import pathlib
from app.core.config_loader import get_config

# 初始化配置加载器
config = get_config()

# ==================== 路径自适应系统 ====================
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

# 导入路径适配器
from app.core.path_adapter import PathAdapter, PathType, get_env_path

# 初始化路径适配器
path_adapter = PathAdapter(BASE_DIR)

# 是否启用自动路径检测
AUTO_DETECT = config.get("paths.auto_detect", True)
AUTO_MIGRATE = config.get("paths.auto_migrate", False)

def setup_adaptive_paths():
    """设置自适应路径"""
    global DATA_DIR, APP_DATA_DIR, CACHE_DIR
    
    print("\n🔍 启动路径自适应系统...")
    
    # ==================== 数据目录 ====================
    # 优先级: 环境变量 > 配置文件 > 自动检测
    env_data_dir = get_env_path("NOVELVOICE_DATA_DIR")
    if env_data_dir:
        print(f"   📌 使用环境变量指定的数据目录: {env_data_dir}")
        DATA_DIR = env_data_dir
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    elif AUTO_DETECT:
        # 自动检测可用路径
        data_config = config.get("paths.data_dir")
        data_candidates = path_adapter.get_candidates(PathType.DATA, data_config)
        DATA_DIR = path_adapter.find_writable_path(data_candidates)
        
        if not DATA_DIR:
            print("❌ 无法找到可写的数据目录!")
            import sys
            sys.exit(1)
        
        # 检测旧数据
        old_data = path_adapter.detect_old_data(DATA_DIR, data_candidates)
        if old_data:
            print(f"   📦 检测到旧数据: {old_data}")
            print(f"   💡 新路径: {DATA_DIR}")
            
            # 根据配置决定是否自动迁移
            should_migrate = AUTO_MIGRATE
            if not AUTO_MIGRATE and os.getenv("ENV") != "production":
                # 开发环境询问用户
                try:
                    response = input("   ❓ 是否迁移数据? (y/n): ")
                    should_migrate = response.lower() == 'y'
                except:
                    should_migrate = False
            
            if should_migrate:
                if path_adapter.migrate_data(old_data, DATA_DIR):
                    # 迁移成功,更新配置
                    from app.core.config_loader import save_config_to_yaml
                    rel_path = path_adapter.get_relative_path(DATA_DIR)
                    if rel_path:
                        save_config_to_yaml({"paths": {"data_dir": rel_path}})
    else:
        # 使用配置文件路径
        data_dir_str = config.get("paths.data_dir", "data")
        DATA_DIR = BASE_DIR / data_dir_str if not pathlib.Path(data_dir_str).is_absolute() else pathlib.Path(data_dir_str)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ==================== 应用数据目录 ====================
    env_app_data_dir = get_env_path("NOVELVOICE_APP_DATA_DIR")
    if env_app_data_dir:
        # 用户显式指定了 APP_DATA_DIR
        APP_DATA_DIR = env_app_data_dir
    elif env_data_dir:
        # DATA_DIR 来自环境变量，优先使用 DATA_DIR/app
        APP_DATA_DIR = DATA_DIR / "app"
    elif AUTO_DETECT:
        # 自动检测可用路径
        app_data_config = config.get("paths.app_data_dir")
        app_candidates = path_adapter.get_candidates(PathType.APP_DATA, app_data_config)
        APP_DATA_DIR = path_adapter.find_writable_path(app_candidates) or DATA_DIR / "app"
    else:
        # 使用配置文件路径
        app_data_dir_str = config.get("paths.app_data_dir", "data/app")
        APP_DATA_DIR = BASE_DIR / app_data_dir_str if not pathlib.Path(app_data_dir_str).is_absolute() else pathlib.Path(app_data_dir_str)
    
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ==================== 缓存目录 ====================
    env_cache_dir = get_env_path("NOVELVOICE_CACHE_DIR")
    if env_cache_dir:
        # 用户显式指定了 CACHE_DIR
        CACHE_DIR = env_cache_dir
    elif env_data_dir:
        # DATA_DIR 来自环境变量，优先使用 DATA_DIR/cache
        CACHE_DIR = DATA_DIR / "cache"
    elif AUTO_DETECT:
        # 自动检测可用路径
        cache_config = config.get("paths.cache_dir")
        cache_candidates = path_adapter.get_candidates(PathType.CACHE, cache_config)
        CACHE_DIR = path_adapter.find_writable_path(cache_candidates) or DATA_DIR / "cache"
    else:
        # 使用配置文件路径
        cache_dir_str = config.get("paths.cache_dir", "data/cache")
        CACHE_DIR = BASE_DIR / cache_dir_str if not pathlib.Path(cache_dir_str).is_absolute() else pathlib.Path(cache_dir_str)
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ 路径自适应完成:")
    print(f"   📁 数据目录: {DATA_DIR}")
    print(f"   📁 应用数据: {APP_DATA_DIR}")
    print(f"   📁 缓存目录: {CACHE_DIR}")

# 执行路径设置
setup_adaptive_paths()

# ==================== TTS 配置 ====================
DEFAULT_VOICE = config.get("tts.default_voice", "zh-CN-XiaoxiaoNeural")
DEFAULT_RATE = config.get("tts.default_rate", "+0%")
DEFAULT_VOLUME = config.get("tts.default_volume", "+0%")
DEFAULT_PITCH = config.get("tts.default_pitch", "+0Hz")
MAX_CHARS = config.get("tts.max_chars", 8000)
CONCURRENCY_LIMIT = config.get("tts.concurrency_limit", 2)
MAX_RETRIES = config.get("tts.max_retries", 3)
TTS_TIMEOUT = config.get("tts.timeout", 30)

# ==================== 文本处理配置 ====================
CHAPTER_PATTERN = config.get("text_processing.chapter_pattern", r"^\s*第.{1,7}[章节回].*")
CHUNK_SIZE = config.get("text_processing.chunk_size", 5000)
MIN_CHUNK_LENGTH = config.get("text_processing.min_chunk_length", 50)

# ==================== 语音列表 ====================
voices_config = config.get_section("voices")
if voices_config:
    # 转换为旧格式以保持兼容性
    VOICES_LIST = [
        {
            "ShortName": v.get("short_name", ""),
            "Gender": v.get("gender", ""),
            "Style": v.get("style", "")
        }
        for v in voices_config
    ]
else:
    # 默认语音列表
    VOICES_LIST = [
        {"ShortName": "zh-CN-XiaoxiaoNeural", "Gender": "Female", "Style": "温暖"},
        {"ShortName": "zh-CN-YunxiNeural", "Gender": "Male", "Style": "稳重"},
        {"ShortName": "zh-CN-YunjianNeural", "Gender": "Male", "Style": "运动"},
        {"ShortName": "zh-CN-XiaoyiNeural", "Gender": "Female", "Style": "可爱"},
        {"ShortName": "zh-CN-YunyangNeural", "Gender": "Male", "Style": "新闻"},
        {"ShortName": "zh-CN-Liaoning-XiaobeiNeural", "Gender": "Female", "Style": "东北话"},
        {"ShortName": "zh-CN-Shaanxi-XiaoniNeural", "Gender": "Female", "Style": "陕西话"},
        {"ShortName": "zh-HK-HiuMaanNeural", "Gender": "Female", "Style": "粤语"},
        {"ShortName": "zh-TW-HsiaoChenNeural", "Gender": "Female", "Style": "台湾"},
    ]

# ==================== Bark 通知配置 ====================
# 环境变量优先,然后是配置文件
BARK_ENABLED = os.getenv("BARK_ENABLED", str(config.get("bark.enabled", "false"))).lower() == "true"
BARK_SERVER_URL = os.getenv("BARK_SERVER_URL", config.get("bark.server_url", "https://api.day.app"))
BARK_API_KEY = os.getenv("BARK_API_KEY", config.get("bark.api_key", ""))
WEB_BASE_URL = os.getenv("WEB_BASE_URL", config.get("bark.web_base_url", "http://localhost:8000"))

# ==================== 服务器配置 ====================
SERVER_HOST = config.get("server.host", "0.0.0.0")
SERVER_PORT = config.get("server.port", 8000)
SERVER_RELOAD = config.get("server.reload", False)

# ==================== 日志配置 ====================
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志级别 (支持 DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = config.get("logging.level", "INFO").upper()

# 日志格式
LOG_FORMAT = config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 日志轮转配置
LOG_MAX_BYTES = config.get("logging.max_bytes", 10 * 1024 * 1024)  # 默认 10MB
LOG_BACKUP_COUNT = config.get("logging.backup_count", 5)           # 默认保留 5 个文件

# 内存日志限制 (用于前端显示)
MAX_LOGS = config.get("logging.max_logs", 200)

# 文件名配置
APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

# 打印配置加载信息
print("=" * 60)
print("📋 NovelVoice 配置信息")
print("=" * 60)
print(f"📁 数据目录: {DATA_DIR}")
print(f"📁 应用数据目录: {APP_DATA_DIR}")
print(f"📁 缓存目录: {CACHE_DIR}")
print(f"📝 日志目录: {LOG_DIR}")
print(f"🎤 默认语音: {DEFAULT_VOICE}")
print(f"⚡ 并发限制: {CONCURRENCY_LIMIT}")
print(f"📱 Bark 通知: {'启用' if BARK_ENABLED else '禁用'}")
print(f"🌐 服务器: {SERVER_HOST}:{SERVER_PORT}")
print("=" * 60)

# 启动时检查路径可写性
print("\n🔍 检查路径权限...")
from app.core.config_loader import check_paths_writable

path_errors = check_paths_writable([DATA_DIR, APP_DATA_DIR, CACHE_DIR])
if path_errors:
    print("\n❌ 路径权限检查失败:")
    for path, error in path_errors.items():
        print(f"  - {path}: {error}")
    print("\n⚠️  应用可能无法正常运行,请检查目录权限!")
    print("💡 提示: 请确保应用对数据目录有读写权限\n")
else:
    print("✅ 所有路径权限检查通过\n")

