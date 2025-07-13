"""資料儲存工具"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from loguru import logger

from models.product import Product, ProductHistory


class DataStorage:
    """資料儲存管理器"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """確保輸出目錄存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"建立輸出目錄: {self.output_dir}")
    
    def save_products_json(self, products: List[Product], filename: str = "products.json"):
        """儲存商品資料為 JSON 格式
        
        Args:
            products: 商品列表
            filename: 檔案名稱
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            data = [product.dict() for product in products]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"已儲存 {len(products)} 個商品資料到 {filepath}")
            
        except Exception as e:
            logger.error(f"儲存 JSON 檔案失敗: {e}")
    
    def load_products_json(self, filename: str = "products.json") -> List[Product]:
        """從 JSON 檔案載入商品資料
        
        Args:
            filename: 檔案名稱
            
        Returns:
            商品列表
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"檔案不存在: {filepath}")
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = [Product(**item) for item in data]
            logger.info(f"已載入 {len(products)} 個商品資料從 {filepath}")
            
            return products
            
        except Exception as e:
            logger.error(f"載入 JSON 檔案失敗: {e}")
            return []
    
    def save_products_csv(self, products: List[Product], filename: str = "products.csv"):
        """儲存商品資料為 CSV 格式
        
        Args:
            products: 商品列表
            filename: 檔案名稱
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not products:
                    return
                
                fieldnames = products[0].dict().keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in products:
                    writer.writerow(product.dict())
            
            logger.info(f"已儲存 {len(products)} 個商品資料到 {filepath}")
            
        except Exception as e:
            logger.error(f"儲存 CSV 檔案失敗: {e}")
    
    def save_history_csv(self, history_data: Dict[str, List[ProductHistory]], 
                        filename: str = "product_history.csv"):
        """儲存商品歷史資料為 CSV 格式
        
        Args:
            history_data: 歷史資料字典 {asin: [ProductHistory]}
            filename: 檔案名稱
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            # 展平歷史資料
            rows = []
            for asin, history_list in history_data.items():
                for history in history_list:
                    row = history.dict()
                    row['asin'] = asin
                    rows.append(row)
            
            if not rows:
                logger.warning("沒有歷史資料可儲存")
                return
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['asin', 'timestamp', 'price', 'availability']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"已儲存 {len(rows)} 筆歷史資料到 {filepath}")
            
        except Exception as e:
            logger.error(f"儲存歷史 CSV 檔案失敗: {e}")
    
    def export_to_excel(self, products: List[Product], 
                       history_data: Optional[Dict[str, List[ProductHistory]]] = None,
                       filename: str = "amazon_data.xlsx"):
        """匯出資料到 Excel 檔案
        
        Args:
            products: 商品列表
            history_data: 歷史資料
            filename: 檔案名稱
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 商品資料表
                if products:
                    products_df = pd.DataFrame([product.dict() for product in products])
                    products_df.to_excel(writer, sheet_name='Products', index=False)
                
                # 歷史資料表
                if history_data:
                    history_rows = []
                    for asin, history_list in history_data.items():
                        for history in history_list:
                            row = history.dict()
                            row['asin'] = asin
                            history_rows.append(row)
                    
                    if history_rows:
                        history_df = pd.DataFrame(history_rows)
                        history_df.to_excel(writer, sheet_name='History', index=False)
                
                # 統計資料表
                if products:
                    stats_data = self._generate_statistics(products, history_data)
                    if stats_data:
                        stats_df = pd.DataFrame(stats_data)
                        stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            logger.info(f"已匯出資料到 Excel: {filepath}")
            
        except Exception as e:
            logger.error(f"匯出 Excel 檔案失敗: {e}")
    
    def _generate_statistics(self, products: List[Product], 
                           history_data: Optional[Dict[str, List[ProductHistory]]]) -> List[Dict]:
        """生成統計資料
        
        Args:
            products: 商品列表
            history_data: 歷史資料
            
        Returns:
            統計資料列表
        """
        stats = []
        
        for product in products:
            stat = {
                'ASIN': product.asin,
                'Title': product.title,
                'Current_Price': product.price,
                'Availability': product.availability,
                'Last_Updated': product.last_updated,
            }
            
            # 添加歷史統計
            if history_data and product.asin in history_data:
                history = history_data[product.asin]
                prices = [h.price for h in history if h.price is not None]
                
                if prices:
                    stat.update({
                        'Min_Price': min(prices),
                        'Max_Price': max(prices),
                        'Avg_Price': sum(prices) / len(prices),
                        'Price_Checks': len(prices),
                    })
                
                # 庫存可用率
                in_stock_count = sum(1 for h in history if 'stock' in h.availability.lower())
                stat['Availability_Rate'] = (in_stock_count / len(history) * 100) if history else 0
            
            stats.append(stat)
        
        return stats
    
    def backup_data(self, backup_suffix: Optional[str] = None):
        """備份所有資料檔案
        
        Args:
            backup_suffix: 備份檔案後綴，預設使用時間戳
        """
        try:
            if backup_suffix is None:
                backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            backup_dir = os.path.join(self.output_dir, f"backup_{backup_suffix}")
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 複製所有檔案到備份目錄
            import shutil
            
            backed_up_count = 0
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                
                if os.path.isfile(filepath) and not filename.startswith('backup_'):
                    backup_filepath = os.path.join(backup_dir, filename)
                    shutil.copy2(filepath, backup_filepath)
                    backed_up_count += 1
            
            logger.info(f"已備份 {backed_up_count} 個檔案到 {backup_dir}")
            
        except Exception as e:
            logger.error(f"備份資料失敗: {e}")
    
    def cleanup_old_backups(self, keep_days: int = 7):
        """清理舊的備份檔案
        
        Args:
            keep_days: 保留天數
        """
        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            removed_count = 0
            for item in os.listdir(self.output_dir):
                item_path = os.path.join(self.output_dir, item)
                
                if (os.path.isdir(item_path) and 
                    item.startswith('backup_') and 
                    os.path.getctime(item_path) < cutoff_date):
                    
                    import shutil
                    shutil.rmtree(item_path)
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"已清理 {removed_count} 個舊備份")
            
        except Exception as e:
            logger.error(f"清理備份失敗: {e}")


class ReportGenerator:
    """報告生成器"""
    
    def __init__(self, storage: DataStorage):
        self.storage = storage
    
    def generate_daily_report(self, products: List[Product], 
                            history_data: Dict[str, List[ProductHistory]]) -> str:
        """生成每日報告
        
        Args:
            products: 商品列表
            history_data: 歷史資料
            
        Returns:
            報告內容
        """
        report_lines = [
            "# Amazon 商品監控每日報告",
            f"報告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"監控商品數量: {len(products)}",
            "",
        ]
        
        # 有庫存的商品
        available_products = [p for p in products if p.is_available()]
        report_lines.extend([
            f"## 庫存狀況",
            f"- 有庫存: {len(available_products)} 個",
            f"- 無庫存: {len(products) - len(available_products)} 個",
            "",
        ])
        
        # 價格變動
        if history_data:
            price_changes = self._analyze_price_changes(history_data)
            if price_changes:
                report_lines.extend([
                    "## 價格變動",
                ])
                for change in price_changes[:5]:  # 顯示前5個
                    report_lines.append(f"- {change}")
                report_lines.append("")
        
        # 推薦購買
        recommendations = self._get_purchase_recommendations(products)
        if recommendations:
            report_lines.extend([
                "## 推薦購買",
            ])
            for rec in recommendations:
                report_lines.append(f"- {rec}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _analyze_price_changes(self, history_data: Dict[str, List[ProductHistory]]) -> List[str]:
        """分析價格變動"""
        changes = []
        
        for asin, history in history_data.items():
            if len(history) >= 2:
                recent = history[-2:]
                if recent[0].price and recent[1].price:
                    change = recent[1].price - recent[0].price
                    if abs(change) >= 1.0:  # 價格變動超過 $1
                        direction = "上漲" if change > 0 else "下跌"
                        changes.append(f"{asin}: 價格{direction} ${abs(change):.2f}")
        
        return changes
    
    def _get_purchase_recommendations(self, products: List[Product]) -> List[str]:
        """獲取購買推薦"""
        recommendations = []
        
        for product in products:
            if product.is_available() and product.is_price_valid():
                recommendations.append(
                    f"{product.asin}: {product.title[:50]}... - ${product.price:.2f}"
                )
        
        return recommendations[:5]  # 最多5個推薦