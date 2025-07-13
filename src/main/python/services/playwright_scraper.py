"""Playwright Amazon 網站爬蟲服務 - 支援 amazon.jp"""

import time
import random
import asyncio
from typing import Optional, Dict, Any, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.sync_api import sync_playwright, Browser as SyncBrowser, BrowserContext as SyncBrowserContext, Page as SyncPage
from loguru import logger
from bs4 import BeautifulSoup
import requests

from core.config import Config
from models.product import Product


class PlaywrightAmazonScraper:
    """使用 Playwright 的 Amazon 網站爬蟲 - 專為 amazon.jp 優化"""
    
    def __init__(self, config: Config):
        self.config = config
        self.playwright = None
        self.browser: Optional[Union[Browser, SyncBrowser]] = None
        self.context: Optional[Union[BrowserContext, SyncBrowserContext]] = None
        self.page: Optional[Union[Page, SyncPage]] = None
        self.session = requests.Session()
        self._setup_session()
        
        # Amazon.jp 特定設定
        self.jp_selectors = self._get_jp_selectors()
        self.jp_text_patterns = self._get_jp_text_patterns()
    
    def _setup_session(self):
        """設定 requests session"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        
        if self.config.amazon_region == "jp":
            headers['Accept-Language'] = 'ja,en-US;q=0.9,en;q=0.8'
        
        self.session.headers.update(headers)
    
    def _get_jp_selectors(self) -> Dict[str, list]:
        """獲取 amazon.jp 特定的選擇器"""
        return {
            'title': [
                '#productTitle',
                'h1.a-size-large',
                'h1#title',
            ],
            'price': [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#price_inside_buybox',
                '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
                '.a-price.a-text-price.a-size-base .a-offscreen',
                '#corePrice_feature_div .a-offscreen',
                '.a-price-range .a-offscreen',
            ],
            'availability': [
                '#availability span',
                '#merchant-info',
                '#buybox-availability-message',
                '.a-alert-content',
                '#availability .a-color-state',
            ],
            'image': [
                '#landingImage',
                '#imgTagWrapperId img',
                '.a-image.a-image-main img',
            ],
            'add_to_cart': [
                '#add-to-cart-button',
                'input[name="submit.add-to-cart"]',
                '#buy-now-button',
            ],
            'quantity': [
                '#quantity',
                'select[name="quantity"]',
                '#quantityDisplayValueSection',
            ]
        }
    
    def _get_jp_text_patterns(self) -> Dict[str, list]:
        """獲取日文文字模式"""
        return {
            'in_stock': ['在庫あり', 'すぐに発送', '即日発送', '通常配送無料', 'あと', '個の在庫'],
            'out_of_stock': ['在庫切れ', '一時的に在庫切れ', '入荷時期未定', '現在在庫切れ'],
            'price_symbols': ['￥', '円', 'JPY'],
        }
    
    async def start_async(self):
        """啟動異步瀏覽器"""
        self.playwright = await async_playwright().start()
        
        browser_type = getattr(self.playwright, self.config.browser_type)
        self.browser = await browser_type.launch(
            headless=self.config.browser_headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        self.context = await self.browser.new_context(
            locale=self.config.browser_locale,
            timezone_id='Asia/Tokyo' if self.config.amazon_region == 'jp' else None,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 添加反檢測腳本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()
        
        # 設定超時
        self.page.set_default_timeout(self.config.browser_timeout * 1000)
        
        logger.info("Playwright 異步瀏覽器已啟動")
    
    def start_sync(self):
        """啟動同步瀏覽器"""
        self.playwright = sync_playwright().start()
        
        browser_type = getattr(self.playwright, self.config.browser_type)
        self.browser = browser_type.launch(
            headless=self.config.browser_headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        self.context = self.browser.new_context(
            locale=self.config.browser_locale,
            timezone_id='Asia/Tokyo' if self.config.amazon_region == 'jp' else None,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 添加反檢測腳本
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = self.context.new_page()
        
        # 設定超時
        self.page.set_default_timeout(self.config.browser_timeout * 1000)
        
        logger.info("Playwright 同步瀏覽器已啟動")
    
    async def stop_async(self):
        """停止異步瀏覽器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Playwright 異步瀏覽器已停止")
    
    def stop_sync(self):
        """停止同步瀏覽器"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        logger.info("Playwright 同步瀏覽器已停止")
    
    async def login_async(self) -> bool:
        """異步登入 Amazon.jp"""
        try:
            logger.info("開始登入 Amazon.jp")
            
            await self.page.goto(f"{self.config.amazon_base_url}/ap/signin")
            
            # 等待並輸入 email
            await self.page.wait_for_selector('#ap_email')
            await self.page.fill('#ap_email', self.config.amazon_email)
            
            # 點擊繼續
            await self.page.click('#continue')
            
            # 等待並輸入密碼
            await self.page.wait_for_selector('#ap_password')
            await self.page.fill('#ap_password', self.config.amazon_password)
            
            # 點擊登入
            await self.page.click('#signInSubmit')
            
            # 等待登入完成
            await self.page.wait_for_function(
                "() => !window.location.href.toLowerCase().includes('signin')",
                timeout=self.config.browser_timeout * 1000
            )
            
            logger.info("Amazon.jp 登入成功")
            return True
            
        except Exception as e:
            logger.error(f"登入失敗: {e}")
            return False
    
    def login_sync(self) -> bool:
        """同步登入 Amazon.jp"""
        try:
            logger.info("開始登入 Amazon.jp")
            
            self.page.goto(f"{self.config.amazon_base_url}/ap/signin")
            
            # 等待並輸入 email
            self.page.wait_for_selector('#ap_email')
            self.page.fill('#ap_email', self.config.amazon_email)
            
            # 點擊繼續
            self.page.click('#continue')
            
            # 等待並輸入密碼
            self.page.wait_for_selector('#ap_password')
            self.page.fill('#ap_password', self.config.amazon_password)
            
            # 點擊登入
            self.page.click('#signInSubmit')
            
            # 等待登入完成
            self.page.wait_for_function(
                "() => !window.location.href.toLowerCase().includes('signin')",
                timeout=self.config.browser_timeout * 1000
            )
            
            logger.info("Amazon.jp 登入成功")
            return True
            
        except Exception as e:
            logger.error(f"登入失敗: {e}")
            return False
    
    async def get_product_info_async(self, asin: str) -> Optional[Product]:
        """異步獲取商品資訊"""
        url = f"{self.config.amazon_base_url}/dp/{asin}"
        
        try:
            logger.info(f"正在獲取商品資訊: {asin}")
            
            await self.page.goto(url, wait_until='domcontentloaded')
            
            # 等待主要內容載入
            await self.page.wait_for_selector('#productTitle', timeout=10000)
            
            # 解析商品資訊
            title = await self._extract_title_async()
            price = await self._extract_price_async()
            availability = await self._extract_availability_async()
            image_url = await self._extract_image_async()
            
            return Product(
                asin=asin,
                title=title,
                price=price,
                currency=self.config.amazon_currency,
                availability=availability,
                image_url=image_url,
                url=url
            )
            
        except Exception as e:
            logger.error(f"獲取商品資訊失敗 {asin}: {e}")
            return None
    
    def get_product_info_sync(self, asin: str) -> Optional[Product]:
        """同步獲取商品資訊"""
        url = f"{self.config.amazon_base_url}/dp/{asin}"
        
        try:
            logger.info(f"正在獲取商品資訊: {asin}")
            
            self.page.goto(url, wait_until='domcontentloaded')
            
            # 等待主要內容載入
            self.page.wait_for_selector('#productTitle', timeout=10000)
            
            # 解析商品資訊
            title = self._extract_title_sync()
            price = self._extract_price_sync()
            availability = self._extract_availability_sync()
            image_url = self._extract_image_sync()
            
            return Product(
                asin=asin,
                title=title,
                price=price,
                currency=self.config.amazon_currency,
                availability=availability,
                image_url=image_url,
                url=url
            )
            
        except Exception as e:
            logger.error(f"獲取商品資訊失敗 {asin}: {e}")
            return None
    
    async def _extract_title_async(self) -> str:
        """異步提取商品標題"""
        for selector in self.jp_selectors['title']:
            try:
                element = await self.page.wait_for_selector(selector, timeout=5000)
                if element:
                    title = await element.text_content()
                    return title.strip() if title else "Unknown"
            except:
                continue
        return "Unknown"
    
    def _extract_title_sync(self) -> str:
        """同步提取商品標題"""
        for selector in self.jp_selectors['title']:
            try:
                element = self.page.wait_for_selector(selector, timeout=5000)
                if element:
                    title = element.text_content()
                    return title.strip() if title else "Unknown"
            except:
                continue
        return "Unknown"
    
    async def _extract_price_async(self) -> Optional[float]:
        """異步提取價格"""
        for selector in self.jp_selectors['price']:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    price_text = await element.text_content()
                    if price_text:
                        return self._parse_jp_price(price_text.strip())
            except:
                continue
        return None
    
    def _extract_price_sync(self) -> Optional[float]:
        """同步提取價格"""
        for selector in self.jp_selectors['price']:
            try:
                element = self.page.query_selector(selector)
                if element:
                    price_text = element.text_content()
                    if price_text:
                        return self._parse_jp_price(price_text.strip())
            except:
                continue
        return None
    
    def _parse_jp_price(self, price_text: str) -> Optional[float]:
        """解析日文價格文字"""
        try:
            import re
            
            # 移除日文價格符號和格式
            price_text = price_text.replace('￥', '').replace('円', '').replace('JPY', '')
            price_text = price_text.replace(',', '').replace(' ', '')
            
            # 提取數字
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                price_str = price_match.group().replace(',', '')
                return float(price_str)
                
        except Exception as e:
            logger.warning(f"價格解析失敗: {price_text}, 錯誤: {e}")
        
        return None
    
    async def _extract_availability_async(self) -> str:
        """異步提取庫存狀態"""
        for selector in self.jp_selectors['availability']:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        return self._parse_jp_availability(text.strip())
            except:
                continue
        return "Unknown"
    
    def _extract_availability_sync(self) -> str:
        """同步提取庫存狀態"""
        for selector in self.jp_selectors['availability']:
            try:
                element = self.page.query_selector(selector)
                if element:
                    text = element.text_content()
                    if text:
                        return self._parse_jp_availability(text.strip())
            except:
                continue
        return "Unknown"
    
    def _parse_jp_availability(self, availability_text: str) -> str:
        """解析日文庫存狀態"""
        text_lower = availability_text.lower()
        
        # 檢查有庫存的模式
        for pattern in self.jp_text_patterns['in_stock']:
            if pattern in availability_text:
                return "In Stock"
        
        # 檢查缺貨的模式
        for pattern in self.jp_text_patterns['out_of_stock']:
            if pattern in availability_text:
                return "Out of Stock"
        
        # 英文回退檢查
        if any(keyword in text_lower for keyword in ['in stock', 'available']):
            return "In Stock"
        elif any(keyword in text_lower for keyword in ['out of stock', 'unavailable']):
            return "Out of Stock"
        
        return "Unknown"
    
    async def _extract_image_async(self) -> Optional[str]:
        """異步提取商品圖片"""
        for selector in self.jp_selectors['image']:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    src = await element.get_attribute('src')
                    if src:
                        return src
            except:
                continue
        return None
    
    def _extract_image_sync(self) -> Optional[str]:
        """同步提取商品圖片"""
        for selector in self.jp_selectors['image']:
            try:
                element = self.page.query_selector(selector)
                if element:
                    src = element.get_attribute('src')
                    if src:
                        return src
            except:
                continue
        return None
    
    async def add_to_cart_async(self, asin: str) -> bool:
        """異步加入購物車"""
        try:
            url = f"{self.config.amazon_base_url}/dp/{asin}"
            await self.page.goto(url)
            
            # 尋找並點擊加入購物車按鈕
            for selector in self.jp_selectors['add_to_cart']:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=5000)
                    if button and await button.is_enabled():
                        await button.click()
                        logger.info(f"商品 {asin} 已加入購物車")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"加入購物車失敗 {asin}: {e}")
            return False
    
    def add_to_cart_sync(self, asin: str) -> bool:
        """同步加入購物車"""
        try:
            url = f"{self.config.amazon_base_url}/dp/{asin}"
            self.page.goto(url)
            
            # 尋找並點擊加入購物車按鈕
            for selector in self.jp_selectors['add_to_cart']:
                try:
                    button = self.page.wait_for_selector(selector, timeout=5000)
                    if button and button.is_enabled():
                        button.click()
                        logger.info(f"商品 {asin} 已加入購物車")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"加入購物車失敗 {asin}: {e}")
            return False
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    # 上下文管理器支援
    async def __aenter__(self):
        await self.start_async()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_async()
    
    def __enter__(self):
        self.start_sync()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_sync()