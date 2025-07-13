"""配置管理模組"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    """應用程式配置"""
    
    # Amazon 設定
    amazon_email: str = Field(..., env="AMAZON_EMAIL")
    amazon_password: str = Field(..., env="AMAZON_PASSWORD")
    amazon_base_url: str = Field(default="https://www.amazon.com", env="AMAZON_BASE_URL")
    
    # 瀏覽器設定
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30, env="BROWSER_TIMEOUT")
    
    # 監控設定
    monitor_interval: int = Field(default=300, env="MONITOR_INTERVAL")  # 5分鐘
    price_check_enabled: bool = Field(default=True, env="PRICE_CHECK_ENABLED")
    max_price: Optional[float] = Field(default=None, env="MAX_PRICE")
    
    # 購買設定
    auto_buy_enabled: bool = Field(default=False, env="AUTO_BUY_ENABLED")
    buy_quantity: int = Field(default=1, env="BUY_QUANTITY")
    
    # 目標商品
    target_products: List[str] = Field(default_factory=list, env="TARGET_PRODUCTS")
    
    # 日誌設定
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/amazonbuyer.log", env="LOG_FILE")
    
    # 輸出設定
    output_dir: str = Field(default="output", env="OUTPUT_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"