import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import (
    LOG_DIR, LOG_LEVEL, LOG_FORMAT, 
    LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    APP_LOG_FILE, ERROR_LOG_FILE
)

def setup_logger():
    """
    配置全局日志系统
    - app.log: 记录所有 >= 配置等级的日志
    - error.log: 仅记录 >= ERROR 等级的日志
    - 控制台: 输出所有日志 (方便调试)
    """
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取根 Logger (或指定 'app' Logger)
    # 使用根 Logger 可以捕获所有模块的日志
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)
    
    # 清除现有的 handlers (避免重复)
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT)
    
    # ==================== 1. 应用主日志 (app.log) ====================
    # 记录所有 >= LOG_LEVEL 的日志
    app_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    app_handler.setLevel(LOG_LEVEL)
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)
    
    # ==================== 2. 错误日志 (error.log) ====================
    # 仅记录 >= ERROR 的日志
    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # ==================== 3. 控制台输出 ====================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ==================== 4. WebSocket 输出 ====================
    from app.core.log_manager import log_manager
    
    class WebSocketLogHandler(logging.Handler):
        def emit(self, record):
            try:
                msg = self.format(record)
                log_manager.put_log(msg)
            except Exception:
                self.handleError(record)

    ws_handler = WebSocketLogHandler()
    ws_handler.setLevel(LOG_LEVEL)
    ws_handler.setFormatter(formatter)
    logger.addHandler(ws_handler)
    
    # 记录启动信息
    logging.info(f"🚀 日志系统初始化完成")
    logging.info(f"📝 日志目录: {LOG_DIR}")
    logging.info(f"🎚️ 日志等级: {LOG_LEVEL}")
    
    return logger
