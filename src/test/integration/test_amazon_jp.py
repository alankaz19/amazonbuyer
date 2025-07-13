"""Amazon.jp 整合測試"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from core.config import Config
from services.unified_scraper import UnifiedAmazonScraper, AsyncUnifiedAmazonScraper
from services.playwright_scraper import PlaywrightAmazonScraper


class TestAmazonJpIntegration:
    """Amazon.jp 整合測試類"""
    
    @pytest.fixture
    def jp_config(self):
        """Amazon.jp 配置"""
        config = Mock(spec=Config)
        config.amazon_email = "test@example.com"
        config.amazon_password = "password123"
        config.amazon_base_url = "https://www.amazon.co.jp"
        config.amazon_region = "jp"
        config.amazon_currency = "JPY"
        config.browser_engine = "playwright"
        config.browser_type = "chromium"
        config.browser_headless = True
        config.browser_timeout = 30
        config.browser_locale = "ja-JP"
        return config
    
    def test_jp_price_parsing(self, jp_config):
        """測試日文價格解析"""
        scraper = PlaywrightAmazonScraper(jp_config)
        
        # 測試各種日文價格格式
        test_cases = [
            ("￥1,234", 1234.0),
            ("1,234円", 1234.0),
            ("¥999", 999.0),
            ("5,678 円", 5678.0),
            ("12,345JPY", 12345.0),
            ("￥12,345.67", 12345.67),
        ]
        
        for price_text, expected in test_cases:
            result = scraper._parse_jp_price(price_text)
            assert result == expected, f"Failed to parse {price_text}"
    
    def test_jp_availability_parsing(self, jp_config):
        """測試日文庫存狀態解析"""
        scraper = PlaywrightAmazonScraper(jp_config)
        
        # 測試有庫存的情況
        in_stock_cases = [
            "在庫あり",
            "すぐに発送できます",
            "通常配送無料",
            "あと3個の在庫があります",
        ]
        
        for text in in_stock_cases:
            result = scraper._parse_jp_availability(text)
            assert result == "In Stock", f"Failed to parse in stock: {text}"
        
        # 測試缺貨的情況
        out_of_stock_cases = [
            "在庫切れ",
            "一時的に在庫切れです",
            "入荷時期未定",
            "現在在庫切れです",
        ]
        
        for text in out_of_stock_cases:
            result = scraper._parse_jp_availability(text)
            assert result == "Out of Stock", f"Failed to parse out of stock: {text}"
    
    def test_unified_scraper_selection(self, jp_config):
        """測試統一爬蟲選擇機制"""
        # 測試 Playwright 選擇
        jp_config.browser_engine = "playwright"
        scraper = UnifiedAmazonScraper(jp_config)
        assert isinstance(scraper.scraper, PlaywrightAmazonScraper)
        
        # 測試 Selenium 回退
        jp_config.browser_engine = "selenium"
        scraper2 = UnifiedAmazonScraper(jp_config)
        # 應該會選擇 AmazonScraper 作為回退
        assert not isinstance(scraper2.scraper, PlaywrightAmazonScraper)
    
    def test_jp_selectors(self, jp_config):
        """測試 Amazon.jp 選擇器"""
        scraper = PlaywrightAmazonScraper(jp_config)
        
        selectors = scraper.jp_selectors
        
        # 驗證重要選擇器存在
        assert 'title' in selectors
        assert 'price' in selectors
        assert 'availability' in selectors
        assert 'image' in selectors
        assert 'add_to_cart' in selectors
        
        # 驗證選擇器不為空
        for selector_type, selector_list in selectors.items():
            assert isinstance(selector_list, list)
            assert len(selector_list) > 0
    
    def test_jp_text_patterns(self, jp_config):
        """測試日文文字模式"""
        scraper = PlaywrightAmazonScraper(jp_config)
        
        patterns = scraper.jp_text_patterns
        
        # 驗證文字模式存在
        assert 'in_stock' in patterns
        assert 'out_of_stock' in patterns
        assert 'price_symbols' in patterns
        
        # 驗證模式不為空
        assert len(patterns['in_stock']) > 0
        assert len(patterns['out_of_stock']) > 0
        assert len(patterns['price_symbols']) > 0
    
    @pytest.mark.asyncio
    async def test_async_scraper_initialization(self, jp_config):
        """測試異步爬蟲初始化"""
        try:
            async_scraper = AsyncUnifiedAmazonScraper(jp_config)
            
            # 測試初始化
            await async_scraper._initialize_scraper()
            
            # 驗證爬蟲類型
            assert isinstance(async_scraper.scraper, PlaywrightAmazonScraper)
            
            # 清理
            await async_scraper.scraper.stop_async()
            
        except ImportError:
            pytest.skip("Playwright 未安裝，跳過異步測試")
    
    def test_currency_formatting(self, jp_config):
        """測試貨幣格式化"""
        from models.product import Product
        
        # 測試日圓格式化
        product_jpy = Product(
            asin="TEST001",
            title="Test Product",
            price=1234.0,
            currency="JPY",
            url="https://test.com"
        )
        
        formatted = product_jpy.get_formatted_price()
        assert formatted == "¥1,234"
        
        # 測試美元格式化
        product_usd = Product(
            asin="TEST002",
            title="Test Product",
            price=12.34,
            currency="USD",
            url="https://test.com"
        )
        
        formatted_usd = product_usd.get_formatted_price()
        assert formatted_usd == "$12.34"
    
    def test_jp_config_defaults(self):
        """測試 Amazon.jp 預設配置"""
        # 模擬環境變數
        with patch.dict('os.environ', {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD': 'password123'
        }):
            config = Config()
            
            # 驗證預設值
            assert config.amazon_base_url == "https://www.amazon.co.jp"
            assert config.amazon_region == "jp"
            assert config.amazon_currency == "JPY"
            assert config.browser_engine == "playwright"
            assert config.browser_locale == "ja-JP"


def test_real_amazon_jp_product():
    """測試真實的 Amazon.jp 商品頁面結構"""
    # 這是一個可選的真實測試
    # 需要謹慎使用，避免對 Amazon 造成負擔
    
    # 使用一個已知的日本商品 ASIN 進行測試
    # 例如：Echo Dot 在日本的 ASIN 可能是 B084J4WR8D
    
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # 使用 requests 獲取頁面內容
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TestBot/1.0)',
            'Accept-Language': 'ja,en;q=0.9'
        }
        
        # 使用一個公開的測試 ASIN
        test_asin = "B084J4WR8D"  # 這只是示例，實際使用時需要確認
        url = f"https://www.amazon.co.jp/dp/{test_asin}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 檢查基本頁面元素是否存在
            title_element = soup.find('span', {'id': 'productTitle'})
            price_elements = soup.find_all(class_='a-price')
            
            # 如果找到了這些元素，說明頁面結構符合預期
            if title_element or price_elements:
                print("✅ Amazon.jp 頁面結構測試通過")
                return True
            else:
                print("⚠️ Amazon.jp 頁面結構可能有變化")
                return False
        else:
            print(f"⚠️ 無法訪問 Amazon.jp: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Amazon.jp 連接測試失敗: {e}")
        return False


if __name__ == "__main__":
    # 運行基本的頁面結構測試
    test_real_amazon_jp_product()