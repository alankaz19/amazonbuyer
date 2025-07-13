"""商品模型測試"""

import pytest
from datetime import datetime
from models.product import Product, ProductHistory


class TestProduct:
    """商品模型測試類"""
    
    def test_product_creation(self):
        """測試商品建立"""
        product = Product(
            asin="B08N5WRWNW",
            title="Test Product",
            price=99.99,
            currency="USD",
            availability="In Stock",
            url="https://amazon.com/dp/B08N5WRWNW"
        )
        
        assert product.asin == "B08N5WRWNW"
        assert product.title == "Test Product"
        assert product.price == 99.99
        assert product.currency == "USD"
        assert product.availability == "In Stock"
        assert product.url == "https://amazon.com/dp/B08N5WRWNW"
        assert isinstance(product.last_updated, datetime)
    
    def test_is_available(self):
        """測試庫存檢查"""
        # 有庫存
        product1 = Product(
            asin="TEST001",
            title="Available Product",
            availability="In Stock",
            url="https://test.com"
        )
        assert product1.is_available() is True
        
        # 無庫存
        product2 = Product(
            asin="TEST002",
            title="Unavailable Product",
            availability="Out of Stock",
            url="https://test.com"
        )
        assert product2.is_available() is False
        
        # 其他狀態
        product3 = Product(
            asin="TEST003",
            title="Unknown Product",
            availability="Unknown",
            url="https://test.com"
        )
        assert product3.is_available() is False
    
    def test_is_price_valid(self):
        """測試價格有效性檢查"""
        # 有效價格
        product1 = Product(
            asin="TEST001",
            title="Valid Price Product",
            price=50.0,
            url="https://test.com"
        )
        assert product1.is_price_valid() is True
        
        # 無效價格 - None
        product2 = Product(
            asin="TEST002",
            title="No Price Product",
            price=None,
            url="https://test.com"
        )
        assert product2.is_price_valid() is False
        
        # 無效價格 - 零
        product3 = Product(
            asin="TEST003",
            title="Zero Price Product",
            price=0.0,
            url="https://test.com"
        )
        assert product3.is_price_valid() is False
        
        # 無效價格 - 負數
        product4 = Product(
            asin="TEST004",
            title="Negative Price Product",
            price=-10.0,
            url="https://test.com"
        )
        assert product4.is_price_valid() is False
    
    def test_meets_price_criteria(self):
        """測試價格條件檢查"""
        product = Product(
            asin="TEST001",
            title="Test Product",
            price=75.0,
            url="https://test.com"
        )
        
        # 無價格限制
        assert product.meets_price_criteria() is True
        
        # 價格在限制內
        assert product.meets_price_criteria(max_price=100.0) is True
        
        # 價格超過限制
        assert product.meets_price_criteria(max_price=50.0) is False
        
        # 無效價格
        product.price = None
        assert product.meets_price_criteria(max_price=100.0) is False
    
    def test_should_buy(self):
        """測試購買決策邏輯"""
        # 符合購買條件
        product1 = Product(
            asin="TEST001",
            title="Good Product",
            price=50.0,
            availability="In Stock",
            url="https://test.com"
        )
        assert product1.should_buy(max_price=100.0) is True
        
        # 無庫存
        product2 = Product(
            asin="TEST002",
            title="No Stock Product",
            price=50.0,
            availability="Out of Stock",
            url="https://test.com"
        )
        assert product2.should_buy(max_price=100.0) is False
        
        # 價格過高
        product3 = Product(
            asin="TEST003",
            title="Expensive Product",
            price=150.0,
            availability="In Stock",
            url="https://test.com"
        )
        assert product3.should_buy(max_price=100.0) is False
        
        # 無價格資訊
        product4 = Product(
            asin="TEST004",
            title="No Price Product",
            price=None,
            availability="In Stock",
            url="https://test.com"
        )
        assert product4.should_buy(max_price=100.0) is False


class TestProductHistory:
    """商品歷史記錄測試類"""
    
    def test_history_creation(self):
        """測試歷史記錄建立"""
        history = ProductHistory(
            asin="B08N5WRWNW",
            price=99.99,
            availability="In Stock"
        )
        
        assert history.asin == "B08N5WRWNW"
        assert history.price == 99.99
        assert history.availability == "In Stock"
        assert isinstance(history.timestamp, datetime)
    
    def test_history_json_serialization(self):
        """測試 JSON 序列化"""
        history = ProductHistory(
            asin="TEST001",
            price=50.0,
            availability="Available"
        )
        
        data = history.dict()
        
        assert data['asin'] == "TEST001"
        assert data['price'] == 50.0
        assert data['availability'] == "Available"
        assert 'timestamp' in data