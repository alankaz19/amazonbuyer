"""商品資料模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    """商品資訊模型"""
    
    asin: str = Field(..., description="Amazon 商品 ASIN")
    title: str = Field(..., description="商品標題")
    price: Optional[float] = Field(None, description="商品價格")
    currency: str = Field(default="USD", description="價格幣別")
    availability: str = Field(default="Unknown", description="庫存狀態")
    image_url: Optional[str] = Field(None, description="商品圖片 URL")
    url: str = Field(..., description="商品頁面 URL")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    def is_available(self) -> bool:
        """檢查商品是否有庫存"""
        return self.availability.lower() in ["in stock", "available", "有庫存"]
    
    def is_price_valid(self) -> bool:
        """檢查價格是否有效"""
        return self.price is not None and self.price > 0
    
    def meets_price_criteria(self, max_price: Optional[float] = None) -> bool:
        """檢查是否符合價格條件
        
        Args:
            max_price: 最高價格限制
            
        Returns:
            是否符合價格條件
        """
        if not self.is_price_valid():
            return False
        
        if max_price is not None and self.price > max_price:
            return False
        
        return True
    
    def get_formatted_price(self) -> str:
        """獲取格式化的價格字串"""
        if not self.is_price_valid():
            return "價格未知"
        
        if self.currency == "JPY":
            return f"¥{self.price:,.0f}"
        elif self.currency == "USD":
            return f"${self.price:.2f}"
        elif self.currency == "GBP":
            return f"£{self.price:.2f}"
        elif self.currency == "EUR":
            return f"€{self.price:.2f}"
        else:
            return f"{self.price:.2f} {self.currency}"
    
    def should_buy(self, max_price: Optional[float] = None) -> bool:
        """判斷是否應該購買
        
        Args:
            max_price: 最高價格限制
            
        Returns:
            是否應該購買
        """
        return self.is_available() and self.meets_price_criteria(max_price)


class ProductHistory(BaseModel):
    """商品歷史記錄模型"""
    
    asin: str = Field(..., description="商品 ASIN")
    timestamp: datetime = Field(default_factory=datetime.now, description="記錄時間")
    price: Optional[float] = Field(None, description="價格")
    availability: str = Field(default="Unknown", description="庫存狀態")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }