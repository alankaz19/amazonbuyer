"""商品監控服務"""

import time
import asyncio
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger
import json
import os

from core.config import Config
from models.product import Product, ProductHistory
from services.amazon_scraper import AmazonScraper


class ProductMonitor:
    """商品價格和庫存監控服務"""
    
    def __init__(self, config: Config, scraper: AmazonScraper):
        self.config = config
        self.scraper = scraper
        self.monitoring = False
        self.products_history: Dict[str, List[ProductHistory]] = {}
        self.callbacks: List[Callable[[Product], None]] = []
        self.history_file = os.path.join(config.output_dir, "product_history.json")
        
        # 確保輸出目錄存在
        os.makedirs(config.output_dir, exist_ok=True)
        
        # 載入歷史資料
        self._load_history()
    
    def add_callback(self, callback: Callable[[Product], None]):
        """添加產品狀態變更回調函數
        
        Args:
            callback: 當商品狀態變更時調用的函數
        """
        self.callbacks.append(callback)
    
    def _load_history(self):
        """載入歷史資料"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for asin, history_list in data.items():
                        self.products_history[asin] = [
                            ProductHistory(**item) for item in history_list
                        ]
                logger.info(f"已載入 {len(self.products_history)} 個商品的歷史資料")
        except Exception as e:
            logger.warning(f"載入歷史資料失敗: {e}")
    
    def _save_history(self):
        """儲存歷史資料"""
        try:
            data = {}
            for asin, history_list in self.products_history.items():
                data[asin] = [item.dict() for item in history_list]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"儲存歷史資料失敗: {e}")
    
    def add_product_to_monitor(self, asin: str):
        """添加商品到監控清單
        
        Args:
            asin: 商品 ASIN
        """
        if asin not in self.products_history:
            self.products_history[asin] = []
            logger.info(f"已添加商品到監控清單: {asin}")
    
    def remove_product_from_monitor(self, asin: str):
        """從監控清單移除商品
        
        Args:
            asin: 商品 ASIN
        """
        if asin in self.products_history:
            del self.products_history[asin]
            logger.info(f"已從監控清單移除商品: {asin}")
    
    def get_monitored_products(self) -> List[str]:
        """獲取所有監控中的商品 ASIN
        
        Returns:
            商品 ASIN 列表
        """
        return list(self.products_history.keys())
    
    def check_product(self, asin: str) -> Optional[Product]:
        """檢查單個商品狀態
        
        Args:
            asin: 商品 ASIN
            
        Returns:
            商品資訊，失敗時返回 None
        """
        try:
            logger.info(f"檢查商品狀態: {asin}")
            
            # 獲取商品資訊
            product = self.scraper.get_product_info(asin)
            if not product:
                logger.warning(f"無法獲取商品資訊: {asin}")
                return None
            
            # 記錄歷史
            history_entry = ProductHistory(
                asin=asin,
                price=product.price,
                availability=product.availability
            )
            
            if asin not in self.products_history:
                self.products_history[asin] = []
            
            self.products_history[asin].append(history_entry)
            
            # 限制歷史記錄數量（保留最近 100 筆）
            if len(self.products_history[asin]) > 100:
                self.products_history[asin] = self.products_history[asin][-100:]
            
            # 檢查是否有重要變更
            if self._is_significant_change(asin, product):
                logger.info(f"商品狀態有重要變更: {asin}")
                for callback in self.callbacks:
                    try:
                        callback(product)
                    except Exception as e:
                        logger.error(f"回調函數執行失敗: {e}")
            
            return product
            
        except Exception as e:
            logger.error(f"檢查商品狀態失敗 {asin}: {e}")
            return None
    
    def _is_significant_change(self, asin: str, current_product: Product) -> bool:
        """檢查是否有重要變更
        
        Args:
            asin: 商品 ASIN
            current_product: 當前商品資訊
            
        Returns:
            是否有重要變更
        """
        history = self.products_history.get(asin, [])
        if len(history) < 2:
            return True  # 第一次檢查算重要變更
        
        previous = history[-2]  # 倒數第二個記錄
        
        # 檢查庫存變更
        if previous.availability != current_product.availability:
            logger.info(f"庫存狀態變更: {previous.availability} -> {current_product.availability}")
            return True
        
        # 檢查價格變更（超過 5% 或 $1）
        if previous.price and current_product.price:
            price_diff = abs(current_product.price - previous.price)
            price_change_percent = price_diff / previous.price * 100
            
            if price_diff >= 1.0 or price_change_percent >= 5.0:
                logger.info(f"價格有明顯變更: ${previous.price} -> ${current_product.price}")
                return True
        
        return False
    
    def check_all_products(self) -> Dict[str, Optional[Product]]:
        """檢查所有監控商品
        
        Returns:
            商品 ASIN 到商品資訊的映射
        """
        results = {}
        
        # 從配置獲取目標商品列表
        target_asins = self.config.target_products.copy()
        
        # 添加到監控清單
        for asin in target_asins:
            self.add_product_to_monitor(asin)
        
        # 檢查所有監控中的商品
        monitored_asins = self.get_monitored_products()
        
        for asin in monitored_asins:
            results[asin] = self.check_product(asin)
            
            # 添加隨機延遲避免被封
            self.scraper.random_delay(2, 5)
        
        # 儲存歷史資料
        self._save_history()
        
        return results
    
    def get_product_statistics(self, asin: str, days: int = 7) -> Dict[str, any]:
        """獲取商品統計資訊
        
        Args:
            asin: 商品 ASIN
            days: 統計天數
            
        Returns:
            統計資訊
        """
        if asin not in self.products_history:
            return {}
        
        # 獲取指定天數內的記錄
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_history = [
            h for h in self.products_history[asin]
            if h.timestamp >= cutoff_date
        ]
        
        if not recent_history:
            return {}
        
        # 計算統計資訊
        prices = [h.price for h in recent_history if h.price is not None]
        availabilities = [h.availability for h in recent_history]
        
        stats = {
            'asin': asin,
            'period_days': days,
            'total_checks': len(recent_history),
            'first_check': recent_history[0].timestamp.isoformat(),
            'last_check': recent_history[-1].timestamp.isoformat(),
        }
        
        if prices:
            stats.update({
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'current_price': recent_history[-1].price,
            })
        
        # 庫存可用性統計
        in_stock_count = sum(1 for a in availabilities if 'stock' in a.lower())
        stats['availability_rate'] = in_stock_count / len(availabilities) * 100
        
        return stats
    
    async def start_monitoring_async(self):
        """開始異步監控"""
        self.monitoring = True
        logger.info("開始商品監控（異步模式）")
        
        while self.monitoring:
            try:
                logger.info("執行商品檢查循環")
                results = self.check_all_products()
                
                # 記錄檢查結果
                available_count = sum(1 for p in results.values() 
                                    if p and p.is_available())
                logger.info(f"檢查完成，{available_count}/{len(results)} 個商品有庫存")
                
                # 等待下一次檢查
                await asyncio.sleep(self.config.monitor_interval)
                
            except Exception as e:
                logger.error(f"監控循環發生錯誤: {e}")
                await asyncio.sleep(30)  # 錯誤時短暫等待
    
    def start_monitoring(self):
        """開始同步監控"""
        self.monitoring = True
        logger.info("開始商品監控（同步模式）")
        
        while self.monitoring:
            try:
                logger.info("執行商品檢查循環")
                results = self.check_all_products()
                
                # 記錄檢查結果
                available_count = sum(1 for p in results.values() 
                                    if p and p.is_available())
                logger.info(f"檢查完成，{available_count}/{len(results)} 個商品有庫存")
                
                # 等待下一次檢查
                time.sleep(self.config.monitor_interval)
                
            except KeyboardInterrupt:
                logger.info("收到中斷信號，停止監控")
                break
            except Exception as e:
                logger.error(f"監控循環發生錯誤: {e}")
                time.sleep(30)  # 錯誤時短暫等待
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        logger.info("商品監控已停止")
    
    def generate_report(self, days: int = 7) -> str:
        """生成監控報告
        
        Args:
            days: 報告天數
            
        Returns:
            報告內容
        """
        report_lines = [
            f"# Amazon 商品監控報告",
            f"報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"統計期間: 最近 {days} 天",
            ""
        ]
        
        for asin in self.get_monitored_products():
            stats = self.get_product_statistics(asin, days)
            if stats:
                report_lines.extend([
                    f"## 商品: {asin}",
                    f"- 檢查次數: {stats['total_checks']}",
                    f"- 庫存可用率: {stats['availability_rate']:.1f}%",
                ])
                
                if 'current_price' in stats:
                    report_lines.extend([
                        f"- 當前價格: ${stats['current_price']:.2f}",
                        f"- 最低價格: ${stats['min_price']:.2f}",
                        f"- 最高價格: ${stats['max_price']:.2f}",
                        f"- 平均價格: ${stats['avg_price']:.2f}",
                    ])
                
                report_lines.append("")
        
        return "\n".join(report_lines)