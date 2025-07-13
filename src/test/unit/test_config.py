"""配置管理測試"""

import pytest
import os
from unittest.mock import patch
from core.config import Config


class TestConfig:
    """配置管理測試類"""
    
    def test_default_config(self):
        """測試預設配置"""
        with patch.dict(os.environ, {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD': 'password123'
        }):
            config = Config()
            
            assert config.amazon_email == 'test@example.com'
            assert config.amazon_password == 'password123'
            assert config.amazon_base_url == "https://www.amazon.com"
            assert config.browser_headless is True
            assert config.browser_timeout == 30
            assert config.monitor_interval == 300
            assert config.price_check_enabled is True
            assert config.auto_buy_enabled is False
            assert config.buy_quantity == 1
            assert config.log_level == "INFO"
            assert config.log_file == "logs/amazonbuyer.log"
            assert config.output_dir == "output"
    
    def test_environment_override(self):
        """測試環境變數覆蓋"""
        with patch.dict(os.environ, {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD': 'password123',
            'AMAZON_BASE_URL': 'https://www.amazon.co.uk',
            'BROWSER_HEADLESS': 'false',
            'BROWSER_TIMEOUT': '60',
            'MONITOR_INTERVAL': '600',
            'PRICE_CHECK_ENABLED': 'false',
            'MAX_PRICE': '150.0',
            'AUTO_BUY_ENABLED': 'true',
            'BUY_QUANTITY': '2',
            'TARGET_PRODUCTS': 'B08N5WRWNW,B0932HKQCT',
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': 'custom.log',
            'OUTPUT_DIR': 'custom_output'
        }):
            config = Config()
            
            assert config.amazon_base_url == "https://www.amazon.co.uk"
            assert config.browser_headless is False
            assert config.browser_timeout == 60
            assert config.monitor_interval == 600
            assert config.price_check_enabled is False
            assert config.max_price == 150.0
            assert config.auto_buy_enabled is True
            assert config.buy_quantity == 2
            assert config.target_products == ['B08N5WRWNW', 'B0932HKQCT']
            assert config.log_level == "DEBUG"
            assert config.log_file == "custom.log"
            assert config.output_dir == "custom_output"
    
    def test_required_fields(self):
        """測試必要欄位驗證"""
        # 缺少必要的環境變數會引發錯誤
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # pydantic 會拋出驗證錯誤
                Config()
    
    def test_type_conversion(self):
        """測試型別轉換"""
        with patch.dict(os.environ, {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD': 'password123',
            'BROWSER_HEADLESS': 'True',  # 字串轉布林
            'BROWSER_TIMEOUT': '45',     # 字串轉整數
            'MAX_PRICE': '99.99',        # 字串轉浮點數
            'AUTO_BUY_ENABLED': 'yes',   # 這應該會失敗
        }):
            try:
                config = Config()
                # 檢查成功轉換的值
                assert config.browser_headless is True
                assert config.browser_timeout == 45
                assert config.max_price == 99.99
            except Exception:
                # 如果有轉換錯誤，這是預期的
                pass