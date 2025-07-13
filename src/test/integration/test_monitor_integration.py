"""監控整合測試"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import tempfile
import os

from core.config import Config
from services.product_monitor import ProductMonitor
from services.amazon_scraper import AmazonScraper
from models.product import Product, ProductHistory


class TestMonitorIntegration:
    """監控整合測試類"""
    
    @pytest.fixture
    def mock_config(self):
        """模擬配置"""
        config = Mock(spec=Config)
        config.target_products = ["B08N5WRWNW", "B0932HKQCT"]
        config.monitor_interval = 10
        config.max_price = 100.0
        config.output_dir = tempfile.mkdtemp()
        return config
    
    @pytest.fixture
    def mock_scraper(self):
        """模擬爬蟲"""
        scraper = Mock(spec=AmazonScraper)
        return scraper
    
    @pytest.fixture
    def monitor(self, mock_config, mock_scraper):
        """建立監控器實例"""
        return ProductMonitor(mock_config, mock_scraper)
    
    def test_monitor_initialization(self, monitor, mock_config):
        """測試監控器初始化"""
        assert monitor.config == mock_config
        assert monitor.monitoring is False
        assert monitor.products_history == {}
        assert monitor.callbacks == []
        assert os.path.exists(mock_config.output_dir)
    
    def test_add_remove_products(self, monitor):
        """測試添加和移除監控商品"""
        # 添加商品
        monitor.add_product_to_monitor("TEST001")
        assert "TEST001" in monitor.products_history
        assert monitor.products_history["TEST001"] == []
        
        # 移除商品
        monitor.remove_product_from_monitor("TEST001")
        assert "TEST001" not in monitor.products_history
    
    def test_get_monitored_products(self, monitor):
        """測試獲取監控商品列表"""
        monitor.add_product_to_monitor("TEST001")
        monitor.add_product_to_monitor("TEST002")
        
        products = monitor.get_monitored_products()
        assert set(products) == {"TEST001", "TEST002"}
    
    def test_check_product_success(self, monitor, mock_scraper):
        """測試成功檢查商品"""
        # 模擬商品資訊
        mock_product = Product(
            asin="TEST001",
            title="Test Product",
            price=50.0,
            availability="In Stock",
            url="https://amazon.com/dp/TEST001"
        )
        mock_scraper.get_product_info.return_value = mock_product
        
        # 檢查商品
        result = monitor.check_product("TEST001")
        
        assert result is not None
        assert result.asin == "TEST001"
        assert "TEST001" in monitor.products_history
        assert len(monitor.products_history["TEST001"]) == 1
        
        # 驗證歷史記錄
        history = monitor.products_history["TEST001"][0]
        assert history.asin == "TEST001"
        assert history.price == 50.0
        assert history.availability == "In Stock"
    
    def test_check_product_failure(self, monitor, mock_scraper):
        """測試檢查商品失敗"""
        mock_scraper.get_product_info.return_value = None
        
        result = monitor.check_product("TEST001")
        
        assert result is None
    
    def test_callback_system(self, monitor, mock_scraper):
        """測試回調函數系統"""
        # 添加回調函數
        callback_called = []
        
        def test_callback(product):
            callback_called.append(product)
        
        monitor.add_callback(test_callback)
        
        # 模擬商品資訊（這是第一次檢查，應該觸發回調）
        mock_product = Product(
            asin="TEST001",
            title="Test Product",
            price=50.0,
            availability="In Stock",
            url="https://amazon.com/dp/TEST001"
        )
        mock_scraper.get_product_info.return_value = mock_product
        
        monitor.check_product("TEST001")
        
        assert len(callback_called) == 1
        assert callback_called[0].asin == "TEST001"
    
    def test_significant_change_detection(self, monitor):
        """測試重要變更檢測"""
        # 添加歷史記錄
        asin = "TEST001"
        monitor.products_history[asin] = [
            ProductHistory(asin=asin, price=100.0, availability="In Stock")
        ]
        
        # 測試庫存變更
        product1 = Product(
            asin=asin,
            title="Test",
            price=100.0,
            availability="Out of Stock",
            url="https://test.com"
        )
        assert monitor._is_significant_change(asin, product1) is True
        
        # 測試價格變更
        monitor.products_history[asin].append(
            ProductHistory(asin=asin, price=100.0, availability="Out of Stock")
        )
        product2 = Product(
            asin=asin,
            title="Test",
            price=95.0,  # 5% 變化
            availability="Out of Stock",
            url="https://test.com"
        )
        assert monitor._is_significant_change(asin, product2) is True
        
        # 測試無重要變更
        monitor.products_history[asin].append(
            ProductHistory(asin=asin, price=95.0, availability="Out of Stock")
        )
        product3 = Product(
            asin=asin,
            title="Test",
            price=95.50,  # 小幅變化
            availability="Out of Stock",
            url="https://test.com"
        )
        assert monitor._is_significant_change(asin, product3) is False
    
    def test_data_persistence(self, monitor, mock_config):
        """測試資料持久化"""
        # 添加歷史記錄
        asin = "TEST001"
        history = ProductHistory(
            asin=asin,
            price=50.0,
            availability="In Stock"
        )
        monitor.products_history[asin] = [history]
        
        # 儲存資料
        monitor._save_history()
        
        # 驗證檔案存在
        history_file = os.path.join(mock_config.output_dir, "product_history.json")
        assert os.path.exists(history_file)
        
        # 驗證資料內容
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert asin in data
        assert len(data[asin]) == 1
        assert data[asin][0]['price'] == 50.0
        assert data[asin][0]['availability'] == "In Stock"
    
    def test_statistics_generation(self, monitor):
        """測試統計資料生成"""
        asin = "TEST001"
        
        # 添加多筆歷史記錄
        from datetime import timedelta
        now = datetime.now()
        
        monitor.products_history[asin] = [
            ProductHistory(
                asin=asin,
                price=50.0,
                availability="In Stock",
                timestamp=now - timedelta(days=5)
            ),
            ProductHistory(
                asin=asin,
                price=55.0,
                availability="In Stock",
                timestamp=now - timedelta(days=3)
            ),
            ProductHistory(
                asin=asin,
                price=45.0,
                availability="Out of Stock",
                timestamp=now - timedelta(days=1)
            ),
        ]
        
        stats = monitor.get_product_statistics(asin, days=7)
        
        assert stats['asin'] == asin
        assert stats['period_days'] == 7
        assert stats['total_checks'] == 3
        assert stats['min_price'] == 45.0
        assert stats['max_price'] == 55.0
        assert stats['avg_price'] == 50.0
        assert stats['current_price'] == 45.0
        assert stats['availability_rate'] == 66.67  # 2/3 有庫存
    
    def test_report_generation(self, monitor):
        """測試報告生成"""
        # 添加測試資料
        asin = "TEST001"
        monitor.products_history[asin] = [
            ProductHistory(asin=asin, price=50.0, availability="In Stock")
        ]
        
        report = monitor.generate_report(days=7)
        
        assert "Amazon 商品監控報告" in report
        assert asin in report
        assert "檢查次數: 1" in report