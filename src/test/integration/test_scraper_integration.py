"""爬蟲整合測試"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.config import Config
from services.amazon_scraper import AmazonScraper
from models.product import Product


class TestScraperIntegration:
    """爬蟲整合測試類"""
    
    @pytest.fixture
    def mock_config(self):
        """模擬配置"""
        config = Mock(spec=Config)
        config.amazon_email = "test@example.com"
        config.amazon_password = "password123"
        config.amazon_base_url = "https://www.amazon.com"
        config.browser_headless = True
        config.browser_timeout = 30
        return config
    
    @pytest.fixture
    def scraper(self, mock_config):
        """建立爬蟲實例"""
        return AmazonScraper(mock_config)
    
    def test_session_setup(self, scraper):
        """測試 session 設定"""
        assert scraper.session is not None
        assert 'User-Agent' in scraper.session.headers
        assert 'Mozilla' in scraper.session.headers['User-Agent']
    
    @patch('services.amazon_scraper.webdriver.Chrome')
    def test_driver_setup(self, mock_chrome, scraper):
        """測試 WebDriver 設定"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        scraper.start_driver()
        
        assert scraper.driver is not None
        mock_chrome.assert_called_once()
        mock_driver.execute_script.assert_called_once()
    
    @patch('services.amazon_scraper.webdriver.Chrome')
    def test_driver_lifecycle(self, mock_chrome, scraper):
        """測試驅動程式生命週期"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # 啟動驅動程式
        scraper.start_driver()
        assert scraper.driver is not None
        
        # 停止驅動程式
        scraper.stop_driver()
        mock_driver.quit.assert_called_once()
        assert scraper.driver is None
    
    @patch('requests.Session.get')
    def test_get_product_info_requests(self, mock_get, scraper):
        """測試使用 requests 獲取商品資訊"""
        # 模擬 HTML 回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
        <html>
            <span id="productTitle">Test Product Title</span>
            <span class="a-price-whole">99</span>
            <div id="availability"><span>In Stock</span></div>
            <img id="landingImage" src="https://example.com/image.jpg" />
        </html>
        '''
        mock_get.return_value = mock_response
        
        product = scraper.get_product_info("B08N5WRWNW")
        
        assert product is not None
        assert product.asin == "B08N5WRWNW"
        assert product.title == "Test Product Title"
        assert product.price == 99.0
        assert product.availability == "In Stock"
        assert product.image_url == "https://example.com/image.jpg"
    
    @patch('services.amazon_scraper.webdriver.Chrome')
    @patch('requests.Session.get')
    def test_get_product_info_selenium_fallback(self, mock_get, mock_chrome, scraper):
        """測試 Selenium 回退機制"""
        # requests 失敗
        mock_get.return_value.status_code = 404
        
        # 設定 Selenium mock
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # 模擬頁面元素
        mock_title = Mock()
        mock_title.text = "Selenium Product Title"
        mock_driver.find_element.return_value = mock_title
        
        # 模擬 WebDriverWait
        with patch('services.amazon_scraper.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = mock_title
            
            with patch.object(scraper, '_extract_price_selenium', return_value=149.99):
                with patch.object(scraper, '_extract_availability_selenium', return_value="In Stock"):
                    product = scraper.get_product_info("B08N5WRWNW")
        
        assert product is not None
        assert product.title == "Selenium Product Title"
        assert product.price == 149.99
    
    def test_parse_price_text(self, scraper):
        """測試價格文字解析"""
        assert scraper._parse_price_text("$99.99") == 99.99
        assert scraper._parse_price_text("99") == 99.0
        assert scraper._parse_price_text("$1,234.56") == 1234.56
        assert scraper._parse_price_text("No price") is None
        assert scraper._parse_price_text("") is None
    
    def test_random_delay(self, scraper):
        """測試隨機延遲"""
        import time
        
        start_time = time.time()
        scraper.random_delay(0.1, 0.2)
        end_time = time.time()
        
        delay = end_time - start_time
        assert 0.1 <= delay <= 0.3  # 允許一些執行時間誤差
    
    @patch('services.amazon_scraper.webdriver.Chrome')
    def test_context_manager(self, mock_chrome, scraper):
        """測試上下文管理器"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        with scraper as s:
            assert s.driver is not None
        
        mock_driver.quit.assert_called_once()