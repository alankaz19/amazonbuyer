#!/usr/bin/env python3
"""
Amazon 商品自動購買工具主程式
"""

from core.config import Config
from core.logger import setup_logger
from services.amazon_scraper import AmazonScraper
from services.product_monitor import ProductMonitor
from services.auto_buyer import AutoBuyer


def main():
    """主程式入口"""
    # 初始化配置和日誌
    config = Config()
    logger = setup_logger(config.log_level)
    
    logger.info("Amazon 自動購買工具啟動")
    
    try:
        # 初始化服務
        scraper = AmazonScraper(config)
        monitor = ProductMonitor(config, scraper)
        buyer = AutoBuyer(config, scraper)
        
        # 開始監控和購買流程
        monitor.start_monitoring()
        
    except Exception as e:
        logger.error(f"程式執行錯誤: {e}")
        raise
    
    logger.info("程式執行完成")


if __name__ == "__main__":
    main()