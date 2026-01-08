import logging
import os
from pathlib import Path
from app.core.config import settings

# 获取项目根目录，并创建日志目录
# 根据项目结构，logs 目录应该在 backend 目录下
LOG_DIR = Path(os.getcwd()) / settings.LOG_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOG_DIR / settings.LOG_FILE

def get_logger(name: str) -> logging.Logger:
    """
    获取配置好的 Logger，所有 Logger 统一输出到 settings.LOG_FILE
    :param name: Logger 名称，通常传入 __name__
    :return: logging.Logger
    """
    logger = logging.getLogger(name)
    
    # 如果 logger 已经有 handler，说明已经配置过，直接返回避免重复日志
    if logger.handlers:
        return logger
        
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 统一的日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # File Handler - 统一写入到 app.log
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console Handler - 同时输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 防止日志向上级传播导致重复
    logger.propagate = False
    
    return logger
