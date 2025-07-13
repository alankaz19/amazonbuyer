"""Amazon 網站爬蟲服務"""

import time
import random
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger
from bs4 import BeautifulSoup
import requests

from core.config import Config
from models.product import Product


class AmazonScraper:
    """Amazon 網站爬蟲"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """設定 requests session"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
        })
    
    def _setup_driver(self) -> webdriver.Chrome:
        """設定 Chrome WebDriver"""
        options = Options()
        
        if self.config.browser_headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 設定 User-Agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def start_driver(self):
        """啟動瀏覽器驅動"""
        if not self.driver:
            self.driver = self._setup_driver()
            logger.info("Chrome WebDriver 已啟動")
    
    def stop_driver(self):
        """停止瀏覽器驅動"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome WebDriver 已停止")
    
    def login(self) -> bool:
        """登入 Amazon 帳戶
        
        Returns:
            登入是否成功
        """
        if not self.driver:
            self.start_driver()
        
        try:
            logger.info("開始登入 Amazon")
            
            # 前往登入頁面
            self.driver.get(f"{self.config.amazon_base_url}/ap/signin")
            
            # 輸入 email
            email_input = WebDriverWait(self.driver, self.config.browser_timeout).until(
                EC.presence_of_element_located((By.ID, "ap_email"))
            )
            email_input.send_keys(self.config.amazon_email)
            
            # 點擊繼續
            continue_btn = self.driver.find_element(By.ID, "continue")
            continue_btn.click()
            
            # 輸入密碼
            password_input = WebDriverWait(self.driver, self.config.browser_timeout).until(
                EC.presence_of_element_located((By.ID, "ap_password"))
            )
            password_input.send_keys(self.config.amazon_password)
            
            # 點擊登入
            signin_btn = self.driver.find_element(By.ID, "signInSubmit")
            signin_btn.click()
            
            # 等待登入完成，檢查是否成功
            WebDriverWait(self.driver, self.config.browser_timeout).until(
                lambda driver: "signin" not in driver.current_url.lower()
            )
            
            logger.info("Amazon 登入成功")
            return True
            
        except TimeoutException:
            logger.error("登入超時")
            return False
        except Exception as e:
            logger.error(f"登入失敗: {e}")
            return False
    
    def get_product_info(self, asin: str) -> Optional[Product]:
        """獲取商品資訊
        
        Args:
            asin: Amazon 商品 ASIN
            
        Returns:
            商品資訊物件，失敗時返回 None
        """
        url = f"{self.config.amazon_base_url}/dp/{asin}"
        
        try:
            # 首先嘗試使用 requests
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                product_info = self._parse_product_page(soup, asin)
                if product_info:
                    return product_info
            
            # 如果 requests 失敗，使用 Selenium
            if not self.driver:
                self.start_driver()
            
            logger.info(f"正在獲取商品資訊: {asin}")
            self.driver.get(url)
            
            # 等待頁面載入
            WebDriverWait(self.driver, self.config.browser_timeout).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            
            # 解析商品資訊
            return self._parse_product_page_selenium(asin)
            
        except Exception as e:
            logger.error(f"獲取商品資訊失敗 {asin}: {e}")
            return None
    
    def _parse_product_page(self, soup: BeautifulSoup, asin: str) -> Optional[Product]:
        """解析商品頁面 (BeautifulSoup 版本)"""
        try:
            # 商品標題
            title_elem = soup.find('span', {'id': 'productTitle'})
            title = title_elem.get_text().strip() if title_elem else "Unknown"
            
            # 價格
            price = self._extract_price_bs4(soup)
            
            # 庫存狀態
            availability = self._extract_availability_bs4(soup)
            
            # 商品圖片
            image_elem = soup.find('img', {'id': 'landingImage'})
            image_url = image_elem.get('src') if image_elem else None
            
            return Product(
                asin=asin,
                title=title,
                price=price,
                currency="USD",
                availability=availability,
                image_url=image_url,
                url=f"{self.config.amazon_base_url}/dp/{asin}"
            )
            
        except Exception as e:
            logger.error(f"解析商品頁面失敗: {e}")
            return None
    
    def _parse_product_page_selenium(self, asin: str) -> Optional[Product]:
        """解析商品頁面 (Selenium 版本)"""
        try:
            # 商品標題
            title_elem = self.driver.find_element(By.ID, "productTitle")
            title = title_elem.text.strip()
            
            # 價格
            price = self._extract_price_selenium()
            
            # 庫存狀態
            availability = self._extract_availability_selenium()
            
            # 商品圖片
            try:
                image_elem = self.driver.find_element(By.ID, "landingImage")
                image_url = image_elem.get_attribute("src")
            except NoSuchElementException:
                image_url = None
            
            return Product(
                asin=asin,
                title=title,
                price=price,
                currency="USD",
                availability=availability,
                image_url=image_url,
                url=f"{self.config.amazon_base_url}/dp/{asin}"
            )
            
        except Exception as e:
            logger.error(f"解析商品頁面失敗: {e}")
            return None
    
    def _extract_price_bs4(self, soup: BeautifulSoup) -> Optional[float]:
        """提取價格 (BeautifulSoup 版本)"""
        price_selectors = [
            'span.a-price-whole',
            'span#price_inside_buybox',
            'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
            'span.a-price.a-text-price.a-size-base',
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text().strip()
                return self._parse_price_text(price_text)
        
        return None
    
    def _extract_price_selenium(self) -> Optional[float]:
        """提取價格 (Selenium 版本)"""
        price_selectors = [
            "span.a-price-whole",
            "span#price_inside_buybox",
            "span.a-price.a-text-price.a-size-medium.apexPriceToPay",
            "span.a-price.a-text-price.a-size-base",
        ]
        
        for selector in price_selectors:
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                return self._parse_price_text(price_text)
            except NoSuchElementException:
                continue
        
        return None
    
    def _parse_price_text(self, price_text: str) -> Optional[float]:
        """解析價格文字為數值"""
        try:
            # 移除非數字字符，保留小數點
            import re
            price_clean = re.sub(r'[^\d.]', '', price_text)
            return float(price_clean) if price_clean else None
        except ValueError:
            return None
    
    def _extract_availability_bs4(self, soup: BeautifulSoup) -> str:
        """提取庫存狀態 (BeautifulSoup 版本)"""
        availability_selectors = [
            '#availability span',
            '#merchant-info',
            '#buybox-availability-message',
        ]
        
        for selector in availability_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text().strip().lower()
                if any(keyword in text for keyword in ['in stock', 'available', '有庫存']):
                    return "In Stock"
                elif any(keyword in text for keyword in ['out of stock', 'unavailable', '缺貨']):
                    return "Out of Stock"
        
        return "Unknown"
    
    def _extract_availability_selenium(self) -> str:
        """提取庫存狀態 (Selenium 版本)"""
        availability_selectors = [
            "#availability span",
            "#merchant-info",
            "#buybox-availability-message",
        ]
        
        for selector in availability_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip().lower()
                if any(keyword in text for keyword in ['in stock', 'available', '有庫存']):
                    return "In Stock"
                elif any(keyword in text for keyword in ['out of stock', 'unavailable', '缺貨']):
                    return "Out of Stock"
            except NoSuchElementException:
                continue
        
        return "Unknown"
    
    def add_to_cart(self, asin: str) -> bool:
        """將商品加入購物車
        
        Args:
            asin: 商品 ASIN
            
        Returns:
            是否成功加入購物車
        """
        if not self.driver:
            self.start_driver()
        
        try:
            url = f"{self.config.amazon_base_url}/dp/{asin}"
            self.driver.get(url)
            
            # 等待並點擊加入購物車按鈕
            add_to_cart_btn = WebDriverWait(self.driver, self.config.browser_timeout).until(
                EC.element_to_be_clickable((By.ID, "add-to-cart-button"))
            )
            add_to_cart_btn.click()
            
            logger.info(f"商品 {asin} 已加入購物車")
            return True
            
        except Exception as e:
            logger.error(f"加入購物車失敗 {asin}: {e}")
            return False
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲以模擬人類行為"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_driver()