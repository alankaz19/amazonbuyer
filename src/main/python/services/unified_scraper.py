"""統一爬蟲介面 - 支援 Playwright 和 Selenium"""

from typing import Optional, Union
from loguru import logger

from core.config import Config
from models.product import Product
from services.playwright_scraper import PlaywrightAmazonScraper
from services.amazon_scraper import AmazonScraper


class UnifiedAmazonScraper:
    """統一的 Amazon 爬蟲介面 - 自動選擇最佳引擎"""
    
    def __init__(self, config: Config):
        self.config = config
        self.scraper: Optional[Union[PlaywrightAmazonScraper, AmazonScraper]] = None
        self._initialize_scraper()
    
    def _initialize_scraper(self):
        """根據配置初始化適當的爬蟲"""
        if self.config.browser_engine.lower() == "playwright":
            try:
                self.scraper = PlaywrightAmazonScraper(self.config)
                logger.info("使用 Playwright 爬蟲引擎")
            except ImportError:
                logger.warning("Playwright 未安裝，回退到 Selenium")
                self.scraper = AmazonScraper(self.config)
        else:
            self.scraper = AmazonScraper(self.config)
            logger.info("使用 Selenium 爬蟲引擎")
    
    def start_driver(self):
        """啟動瀏覽器驅動"""
        if isinstance(self.scraper, PlaywrightAmazonScraper):
            self.scraper.start_sync()
        else:
            self.scraper.start_driver()
    
    def stop_driver(self):
        """停止瀏覽器驅動"""
        if isinstance(self.scraper, PlaywrightAmazonScraper):
            self.scraper.stop_sync()
        else:
            self.scraper.stop_driver()
    
    def login(self) -> bool:
        """登入 Amazon"""
        if isinstance(self.scraper, PlaywrightAmazonScraper):
            return self.scraper.login_sync()
        else:
            return self.scraper.login()
    
    def get_product_info(self, asin: str) -> Optional[Product]:
        """獲取商品資訊"""
        if isinstance(self.scraper, PlaywrightAmazonScraper):
            return self.scraper.get_product_info_sync(asin)
        else:
            return self.scraper.get_product_info(asin)
    
    def add_to_cart(self, asin: str) -> bool:
        """加入購物車"""
        if isinstance(self.scraper, PlaywrightAmazonScraper):
            return self.scraper.add_to_cart_sync(asin)
        else:
            return self.scraper.add_to_cart(asin)
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲"""
        self.scraper.random_delay(min_seconds, max_seconds)
    
    # 上下文管理器支援
    def __enter__(self):
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_driver()


class AsyncUnifiedAmazonScraper:
    """異步統一 Amazon 爬蟲介面"""
    
    def __init__(self, config: Config):
        self.config = config
        self.scraper: Optional[PlaywrightAmazonScraper] = None
    
    async def _initialize_scraper(self):
        """初始化 Playwright 爬蟲（異步版本僅支援 Playwright）"""
        try:
            self.scraper = PlaywrightAmazonScraper(self.config)
            await self.scraper.start_async()
            logger.info("使用異步 Playwright 爬蟲引擎")
        except ImportError:
            raise ImportError("異步模式需要安裝 Playwright")
    
    async def login(self) -> bool:
        """異步登入 Amazon"""
        if self.scraper:
            return await self.scraper.login_async()
        return False
    
    async def get_product_info(self, asin: str) -> Optional[Product]:
        """異步獲取商品資訊"""
        if self.scraper:
            return await self.scraper.get_product_info_async(asin)
        return None
    
    async def add_to_cart(self, asin: str) -> bool:
        """異步加入購物車"""
        if self.scraper:
            return await self.scraper.add_to_cart_async(asin)
        return False
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲"""
        if self.scraper:
            self.scraper.random_delay(min_seconds, max_seconds)
    
    # 異步上下文管理器支援
    async def __aenter__(self):
        await self._initialize_scraper()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.scraper:
            await self.scraper.stop_async()