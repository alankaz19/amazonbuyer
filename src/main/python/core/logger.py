"""日誌配置模組"""

import os
from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: str = "logs/amazonbuyer.log") -> logger:
    """設定日誌系統
    
    Args:
        log_level: 日誌級別
        log_file: 日誌檔案路徑
        
    Returns:
        配置好的 logger 實例
    """
    # 確保日誌目錄存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 移除預設處理器
    logger.remove()
    
    # 控制台輸出
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 檔案輸出
    logger.add(
        sink=log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )
    
    return logger