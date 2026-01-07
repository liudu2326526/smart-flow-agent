import logging
from pathlib import Path

# 获取项目根目录 (假设 utils 在 backend/app/utils)
# PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
# 或者硬编码路径，根据之前的文件内容，路径是 /Users/macbook/cursor/smart-flow-agent
LOG_ROOT = Path("/Users/macbook/cursor/smart-flow-agent/logs")
LOG_ROOT.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, filename: str = "app.log") -> logging.Logger:
    """
    获取配置好的 Logger
    :param name: Logger 名称，通常传入 __name__
    :param filename: 日志文件名，默认为 app.log
    :return: logging.Logger
    """
    logger = logging.getLogger(name)
    
    # 如果 logger 已经有 handler，说明已经配置过，直接返回避免重复日志
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # File Handler
    file_handler = logging.FileHandler(LOG_ROOT / filename)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console Handler (Optional: 输出到控制台)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
