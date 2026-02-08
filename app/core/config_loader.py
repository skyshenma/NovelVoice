"""
配置加载器模块
从 config.yml 加载配置,支持环境变量覆盖
"""

import os
import pathlib
import yaml
from typing import Any, Dict, Optional


class ConfigLoader:
    """YAML 配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径,默认为 data/config/config.yml
        """
        if config_path is None:
            # 默认配置文件路径
            base_dir = pathlib.Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "data" / "config" / "config.yml"
        
        self.config_path = pathlib.Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            print(f"⚠️  配置文件不存在: {self.config_path}")
            print(f"📝 使用默认配置")
            self._config = self._get_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            print(f"✅ 成功加载配置文件: {self.config_path}")
        except yaml.YAMLError as e:
            print(f"❌ YAML 格式错误: {e}")
            print(f"⚠️  配置文件格式不正确,使用默认配置")
            print(f"💡 请检查 {self.config_path} 的 YAML 语法")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            print(f"📝 使用默认配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": False
            },
            "tts": {
                "default_voice": "zh-CN-XiaoxiaoNeural",
                "default_rate": "+0%",
                "default_volume": "+0%",
                "default_pitch": "+0Hz",
                "max_chars": 8000,
                "concurrency_limit": 2,
                "max_retries": 3,
                "timeout": 30
            },
            "text_processing": {
                "chapter_pattern": r"^\s*第.{1,7}[章节回].*",
                "chunk_size": 5000,
                "min_chunk_length": 50
            },
            "paths": {
                "data_dir": "data",
                "app_data_dir": "data/app",
                "cache_dir": "data/cache"
            },
            "bark": {
                "enabled": False,
                "server_url": "https://api.day.app",
                "api_key": "",
                "web_base_url": "http://localhost:8000"
            },
            "voices": [
                # 中国大陆 (普通话)
                {"short_name": "zh-CN-XiaoxiaoNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Female", "gender_cn": "女", "style": "温暖", "name": "xiaoxiao", "description": "[温暖] 普通话 - 中国大陆 - 女 - xiaoxiao"},
                {"short_name": "zh-CN-XiaoyiNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Female", "gender_cn": "女", "style": "通用", "name": "xiaoyi", "description": "[通用] 普通话 - 中国大陆 - 女 - xiaoyi"},
                {"short_name": "zh-CN-YunjianNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Male", "gender_cn": "男", "style": "通用", "name": "yunjian", "description": "[通用] 普通话 - 中国大陆 - 男 - yunjian"},
                {"short_name": "zh-CN-YunxiNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Male", "gender_cn": "男", "style": "通用", "name": "yunxi", "description": "[通用] 普通话 - 中国大陆 - 男 - yunxi"},
                {"short_name": "zh-CN-YunxiaNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Male", "gender_cn": "男", "style": "通用", "name": "yunxia", "description": "[通用] 普通话 - 中国大陆 - 男 - yunxia"},
                {"short_name": "zh-CN-YunyangNeural", "locale": "zh-CN", "language": "普通话", "region": "中国大陆", "gender": "Male", "gender_cn": "男", "style": "专业", "name": "yunyang", "description": "[专业] 普通话 - 中国大陆 - 男 - yunyang"},
                # 中国方言
                {"short_name": "zh-CN-liaoning-XiaobeiNeural", "locale": "zh-CN-liaoning", "language": "东北官话", "region": "中国辽宁", "gender": "Female", "gender_cn": "女", "style": "幽默", "name": "xiaobei", "description": "[幽默] 东北官话 - 中国辽宁 - 女 - xiaobei"},
                {"short_name": "zh-CN-shaanxi-XiaoniNeural", "locale": "zh-CN-shaanxi", "language": "中原官话", "region": "中国陕西", "gender": "Female", "gender_cn": "女", "style": "明亮", "name": "xiaoni", "description": "[明亮] 中原官话 - 中国陕西 - 女 - xiaoni"},
                # 中国香港 (粤语)
                {"short_name": "zh-HK-HiuGaaiNeural", "locale": "zh-HK", "language": "粤语", "region": "中国香港", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "hiugaai", "description": "[友好] 粤语 - 中国香港 - 女 - hiugaai"},
                {"short_name": "zh-HK-HiuMaanNeural", "locale": "zh-HK", "language": "粤语", "region": "中国香港", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "hiumaan", "description": "[友好] 粤语 - 中国香港 - 女 - hiumaan"},
                {"short_name": "zh-HK-WanLungNeural", "locale": "zh-HK", "language": "粤语", "region": "中国香港", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "wanlung", "description": "[友好] 粤语 - 中国香港 - 男 - wanlung"},
                # 中国台湾 (台湾国语)
                {"short_name": "zh-TW-HsiaoChenNeural", "locale": "zh-TW", "language": "台湾国语", "region": "中国台湾", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "hsiaochen", "description": "[友好] 台湾国语 - 中国台湾 - 女 - hsiaochen"},
                {"short_name": "zh-TW-YunJheNeural", "locale": "zh-TW", "language": "台湾国语", "region": "中国台湾", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "yunjhe", "description": "[友好] 台湾国语 - 中国台湾 - 男 - yunjhe"},
                {"short_name": "zh-TW-HsiaoYuNeural", "locale": "zh-TW", "language": "台湾国语", "region": "中国台湾", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "hsiaoyu", "description": "[友好] 台湾国语 - 中国台湾 - 女 - hsiaoyu"},
                # 美国 (英语)
                {"short_name": "en-US-AvaNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Female", "gender_cn": "女", "style": "通用", "name": "ava", "description": "[通用] 英语 - 美国 - 女 - ava"},
                {"short_name": "en-US-AndrewNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Male", "gender_cn": "男", "style": "温暖", "name": "andrew", "description": "[温暖] 英语 - 美国 - 男 - andrew"},
                {"short_name": "en-US-EmmaNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Female", "gender_cn": "女", "style": "开朗", "name": "emma", "description": "[开朗] 英语 - 美国 - 女 - emma"},
                {"short_name": "en-US-BrianNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Male", "gender_cn": "男", "style": "通用", "name": "brian", "description": "[通用] 英语 - 美国 - 男 - brian"},
                {"short_name": "en-US-AriaNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Female", "gender_cn": "女", "style": "积极", "name": "aria", "description": "[积极] 英语 - 美国 - 女 - aria"},
                {"short_name": "en-US-JennyNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "jenny", "description": "[友好] 英语 - 美国 - 女 - jenny"},
                {"short_name": "en-US-GuyNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Male", "gender_cn": "男", "style": "通用", "name": "guy", "description": "[通用] 英语 - 美国 - 男 - guy"},
                {"short_name": "en-US-MichelleNeural", "locale": "en-US", "language": "英语", "region": "美国", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "michelle", "description": "[友好] 英语 - 美国 - 女 - michelle"},
                # 英国 (英语)
                {"short_name": "en-GB-LibbyNeural", "locale": "en-GB", "language": "英语", "region": "英国", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "libby", "description": "[友好] 英语 - 英国 - 女 - libby"},
                {"short_name": "en-GB-MaisieNeural", "locale": "en-GB", "language": "英语", "region": "英国", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "maisie", "description": "[友好] 英语 - 英国 - 女 - maisie"},
                {"short_name": "en-GB-RyanNeural", "locale": "en-GB", "language": "英语", "region": "英国", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "ryan", "description": "[友好] 英语 - 英国 - 男 - ryan"},
                {"short_name": "en-GB-SoniaNeural", "locale": "en-GB", "language": "英语", "region": "英国", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "sonia", "description": "[友好] 英语 - 英国 - 女 - sonia"},
                {"short_name": "en-GB-ThomasNeural", "locale": "en-GB", "language": "英语", "region": "英国", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "thomas", "description": "[友好] 英语 - 英国 - 男 - thomas"},
                # 加拿大 (英语)
                {"short_name": "en-CA-ClaraNeural", "locale": "en-CA", "language": "英语", "region": "加拿大", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "clara", "description": "[友好] 英语 - 加拿大 - 女 - clara"},
                {"short_name": "en-CA-LiamNeural", "locale": "en-CA", "language": "英语", "region": "加拿大", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "liam", "description": "[友好] 英语 - 加拿大 - 男 - liam"},
                # 日本 (日语)
                {"short_name": "ja-JP-KeitaNeural", "locale": "ja-JP", "language": "日语", "region": "日本", "gender": "Male", "gender_cn": "男", "style": "友好", "name": "keita", "description": "[友好] 日语 - 日本 - 男 - keita"},
                {"short_name": "ja-JP-NanamiNeural", "locale": "ja-JP", "language": "日语", "region": "日本", "gender": "Female", "gender_cn": "女", "style": "友好", "name": "nanami", "description": "[友好] 日语 - 日本 - 女 - nanami"}
            ],
            "logging": {
                "max_logs": 200,
                "error_log_file": "error.log"
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值,支持点号分隔的路径,环境变量优先
        
        Args:
            key_path: 配置键路径,如 "tts.default_voice"
            default: 默认值
            
        Returns:
            配置值
            
        Examples:
            >>> config.get("tts.default_voice")
            "zh-CN-XiaoxiaoNeural"
            >>> config.get("server.port")
            8000
        """
        # 检查环境变量 (转换为大写并用下划线连接)
        env_key = key_path.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            # 尝试转换类型
            return self._convert_type(env_value)
        
        # 从配置文件获取
        keys = key_path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _convert_type(self, value: str) -> Any:
        """尝试转换字符串类型"""
        # 布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # 数字
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置段
        
        Args:
            section: 配置段名称,如 "tts", "server"
            
        Returns:
            配置段字典
        """
        return self._config.get(section, {})
    
    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config
    
    async def reload(self) -> Dict[str, Any]:
        """
        异步重新加载配置文件
        
        Returns:
            dict: 包含状态、消息和配置的字典
        """
        from datetime import datetime
        
        try:
            # 检查配置文件是否存在
            if not self.config_path.exists():
                return {
                    "success": False,
                    "message": f"配置文件不存在: {self.config_path}",
                    "config": self._config
                }
            
            # 读取新配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                new_config = yaml.safe_load(f)
            
            # 验证配置格式
            if not isinstance(new_config, dict):
                return {
                    "success": False,
                    "message": "配置文件格式错误:根节点必须是字典",
                    "config": self._config
                }
            
            # 保存旧配置用于变更检测
            old_config = self._config.copy()
            
            # 更新内存配置
            self._config = new_config
            
            # 检测配置变更
            changes = self._get_config_changes(old_config, new_config)
            
            # 记录日志
            print(f"[NovelVoice] User triggered manual config reload from disk.")
            print(f"[NovelVoice] Config reloaded successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if changes:
                print(f"[NovelVoice] Detected {len(changes)} config section(s) changed: {', '.join(changes.keys())}")
            
            return {
                "success": True,
                "message": "配置已从磁盘同步成功",
                "config": self._config,
                "changes": changes
            }
            
        except yaml.YAMLError as e:
            error_msg = f"YAML 格式错误: {str(e)}"
            print(f"[NovelVoice] {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "config": self._config
            }
        except Exception as e:
            error_msg = f"重载失败: {str(e)}"
            print(f"[NovelVoice] Config reload error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": error_msg,
                "config": self._config
            }
    
    def _get_config_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测配置变更
        
        Args:
            old_config: 旧配置
            new_config: 新配置
        
        Returns:
            变更的配置段
        """
        changes = {}
        
        # 检查主要配置段
        sections = ['tts', 'bark', 'server', 'text_processing', 'paths', 'voices']
        
        for section in sections:
            old_val = old_config.get(section)
            new_val = new_config.get(section)
            
            if old_val != new_val:
                changes[section] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes


# 全局配置实例
_config_loader: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """获取全局配置实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def reload_config(config_path: Optional[str] = None):
    """重新加载配置"""
    global _config_loader
    _config_loader = ConfigLoader(config_path)


# ==================== 配置验证和保存功能 ====================

def validate_tts_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    验证 TTS 配置参数
    
    Returns:
        错误字典,键为字段名,值为错误信息
    """
    errors = {}
    
    # 验证并发数
    if 'concurrency_limit' in config:
        val = config['concurrency_limit']
        if not isinstance(val, int) or not (1 <= val <= 10):
            errors['concurrency_limit'] = '并发数必须在 1-10 之间'
    
    # 验证重试次数
    if 'max_retries' in config:
        val = config['max_retries']
        if not isinstance(val, int) or not (0 <= val <= 10):
            errors['max_retries'] = '重试次数必须在 0-10 之间'
    
    # 验证超时时间
    if 'timeout' in config:
        val = config['timeout']
        if not isinstance(val, int) or not (10 <= val <= 120):
            errors['timeout'] = '超时时间必须在 10-120 秒之间'
    
    # 验证语速
    if 'default_rate' in config:
        try:
            val = int(config['default_rate'].replace('%', '').replace('+', '').replace('-', ''))
            if not (-50 <= val <= 100):
                errors['default_rate'] = '语速必须在 -50% 到 +100% 之间'
        except:
            errors['default_rate'] = '语速格式错误'
    
    # 验证音量
    if 'default_volume' in config:
        try:
            val = int(config['default_volume'].replace('%', '').replace('+', '').replace('-', ''))
            if not (-50 <= val <= 50):
                errors['default_volume'] = '音量必须在 -50% 到 +50% 之间'
        except:
            errors['default_volume'] = '音量格式错误'
    
    # 验证音调
    if 'default_pitch' in config:
        try:
            val = int(config['default_pitch'].replace('Hz', '').replace('+', '').replace('-', ''))
            if not (-50 <= val <= 50):
                errors['default_pitch'] = '音调必须在 -50Hz 到 +50Hz 之间'
        except:
            errors['default_pitch'] = '音调格式错误'
    
    return errors


def save_config_to_yaml(config_updates: Dict[str, Any], config_path: Optional[pathlib.Path] = None) -> bool:
    """
    保存配置到 YAML 文件
    
    Args:
        config_updates: 要更新的配置字典
        config_path: 配置文件路径,默认使用全局配置路径
        
    Returns:
        是否保存成功
    """
    import yaml
    
    loader = get_config()
    if config_path is None:
        config_path = loader.config_path
    
    try:
        # 读取现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
        else:
            current_config = loader._get_default_config()
        
        # 深度合并配置
        def deep_merge(base, updates):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(current_config, config_updates)
        
        # 确保配置目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"✅ 配置已保存到: {config_path}")
        return True
        
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_paths_writable(paths: list) -> Dict[str, str]:
    """
    检查路径是否可写
    
    Args:
        paths: 要检查的路径列表
        
    Returns:
        错误字典,键为路径,值为错误信息
    """
    errors = {}
    
    for path in paths:
        path = pathlib.Path(path)
        
        try:
            # 确保目录存在
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            # 测试写入权限
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            
        except PermissionError:
            errors[str(path)] = "权限不足,无法写入"
        except Exception as e:
            errors[str(path)] = f"检查失败: {str(e)}"
    
    return errors

