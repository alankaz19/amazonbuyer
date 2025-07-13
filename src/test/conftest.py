"""測試配置和共用夾具"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock

from core.config import Config


@pytest.fixture
def temp_dir():
    """建立臨時目錄"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    """建立範例配置"""
    config = Mock(spec=Config)
    config.amazon_email = "test@example.com"
    config.amazon_password = "password123"
    config.amazon_base_url = "https://www.amazon.com"
    config.browser_headless = True
    config.browser_timeout = 30
    config.monitor_interval = 300
    config.price_check_enabled = True
    config.max_price = 100.0
    config.auto_buy_enabled = False
    config.buy_quantity = 1
    config.target_products = ["B08N5WRWNW", "B0932HKQCT"]
    config.log_level = "INFO"
    config.log_file = "logs/test.log"
    config.output_dir = "test_output"
    return config


@pytest.fixture
def sample_product_data():
    """建立範例商品資料"""
    from models.product import Product
    
    return [
        Product(
            asin="B08N5WRWNW",
            title="Amazon Echo Dot (4th Gen)",
            price=49.99,
            currency="USD",
            availability="In Stock",
            url="https://amazon.com/dp/B08N5WRWNW"
        ),
        Product(
            asin="B0932HKQCT",
            title="Amazon Fire TV Stick",
            price=39.99,
            currency="USD",
            availability="Out of Stock",
            url="https://amazon.com/dp/B0932HKQCT"
        ),
    ]


@pytest.fixture
def mock_web_driver():
    """模擬 WebDriver"""
    from unittest.mock import Mock
    
    driver = Mock()
    driver.current_url = "https://amazon.com"
    driver.page_source = "<html><body>Mock page</body></html>"
    
    # 模擬元素
    mock_element = Mock()
    mock_element.text = "Mock text"
    mock_element.get_attribute.return_value = "Mock attribute"
    mock_element.is_enabled.return_value = True
    
    driver.find_element.return_value = mock_element
    driver.find_elements.return_value = [mock_element]
    
    return driver


def pytest_configure(config):
    """pytest 配置"""
    # 確保測試輸出目錄存在
    test_output_dir = "test_output"
    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)


def pytest_unconfigure(config):
    """pytest 清理"""
    # 清理測試輸出目錄
    test_output_dir = "test_output"
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)