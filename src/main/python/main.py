#!/usr/bin/env python3
"""
Amazon 商品自動購買工具主程式
"""

import argparse
import asyncio
import signal
import sys
from typing import Optional

from core.config import Config
from core.logger import setup_logger
from services.unified_scraper import UnifiedAmazonScraper, AsyncUnifiedAmazonScraper
from services.product_monitor import ProductMonitor
from services.auto_buyer import AutoBuyer
from utils.data_storage import DataStorage, ReportGenerator
from utils.notification import NotificationManager


class AmazonBuyerApp:
    """Amazon 自動購買工具主應用程式"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger(config.log_level, config.log_file)
        self.running = True
        
        # 初始化服務
        self.scraper = UnifiedAmazonScraper(config)
        self.monitor = ProductMonitor(config, self.scraper)
        self.buyer = AutoBuyer(config, self.scraper)
        self.storage = DataStorage(config.output_dir)
        self.report_gen = ReportGenerator(self.storage)
        self.notifications = NotificationManager()
        
        # 設定信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 設定監控回調
        self.monitor.add_callback(self._on_product_change)
        
        self.logger.info("Amazon 自動購買工具初始化完成")
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        self.logger.info(f"收到信號 {signum}，正在停止程式...")
        self.running = False
        self.monitor.stop_monitoring()
    
    def _on_product_change(self, product):
        """商品狀態變更回調"""
        self.logger.info(f"商品狀態變更: {product.asin} - {product.title}")
        
        # 檢查是否符合購買條件
        if product.should_buy(self.config.max_price):
            self.logger.info(f"商品符合購買條件: {product.asin}")
            
            # 發送通知
            self.notifications.send_product_alert(
                product, 
                alert_type="available"
            )
            
            # 如果啟用自動購買，嘗試購買
            if self.config.auto_buy_enabled:
                success = self.buyer.attempt_purchase(product)
                if success:
                    self.logger.info(f"成功購買商品: {product.asin}")
                    self.notifications.send_product_alert(
                        product,
                        alert_type="purchased"
                    )
                else:
                    self.logger.error(f"購買失敗: {product.asin}")
    
    def setup_notifications(self, email_config: Optional[dict] = None,
                           slack_webhook: Optional[str] = None,
                           custom_webhook: Optional[str] = None):
        """設定通知系統"""
        if email_config:
            self.notifications.add_email_notifier(
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                username=email_config['username'],
                password=email_config['password'],
                use_tls=email_config.get('use_tls', True)
            )
        
        if slack_webhook:
            self.notifications.add_slack_notifier(slack_webhook)
        
        if custom_webhook:
            self.notifications.add_webhook_notifier(custom_webhook)
    
    def run_once(self):
        """執行一次檢查"""
        self.logger.info("執行單次商品檢查")
        
        try:
            # 檢查所有商品
            results = self.monitor.check_all_products()
            
            # 儲存結果
            products = [p for p in results.values() if p is not None]
            if products:
                self.storage.save_products_json(products, "latest_check.json")
                self.storage.save_products_csv(products, "latest_check.csv")
            
            # 生成報告
            if self.monitor.products_history:
                report = self.monitor.generate_report()
                report_file = f"{self.config.output_dir}/latest_report.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.logger.info(f"報告已儲存: {report_file}")
            
            self.logger.info(f"檢查完成，共 {len(products)} 個商品")
            return results
            
        except Exception as e:
            self.logger.error(f"執行檢查時發生錯誤: {e}")
            return {}
    
    def run_monitor(self):
        """執行持續監控"""
        self.logger.info("開始持續監控模式")
        
        try:
            # 使用同步監控
            self.monitor.start_monitoring()
            
        except KeyboardInterrupt:
            self.logger.info("監控被使用者中斷")
        except Exception as e:
            self.logger.error(f"監控過程發生錯誤: {e}")
        finally:
            self.cleanup()
    
    async def run_monitor_async(self):
        """執行異步監控"""
        self.logger.info("開始異步監控模式")
        
        try:
            # 使用異步爬蟲重新初始化監控
            async_scraper = AsyncUnifiedAmazonScraper(self.config)
            async with async_scraper:
                # 使用異步監控
                await self.monitor.start_monitoring_async()
            
        except Exception as e:
            self.logger.error(f"異步監控過程發生錯誤: {e}")
        finally:
            self.cleanup()
    
    def test_purchase(self, asin: str):
        """測試購買流程（不實際下單）"""
        self.logger.info(f"測試購買流程: {asin}")
        
        try:
            # 獲取商品資訊
            product = self.scraper.get_product_info(asin)
            if not product:
                self.logger.error(f"無法獲取商品資訊: {asin}")
                return None
            
            # 執行乾式運行
            result = self.buyer.dry_run_purchase(product)
            
            self.logger.info(f"測試結果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"測試購買流程失敗: {e}")
            return None
    
    def generate_report(self, days: int = 7):
        """生成監控報告"""
        self.logger.info(f"生成 {days} 天監控報告")
        
        try:
            # 獲取所有監控商品的最新資訊
            results = self.monitor.check_all_products()
            products = [p for p in results.values() if p is not None]
            
            # 生成報告
            report = self.report_gen.generate_daily_report(
                products, 
                self.monitor.products_history
            )
            
            # 儲存報告
            report_file = f"{self.config.output_dir}/monitoring_report_{days}days.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # 匯出到 Excel
            self.storage.export_to_excel(
                products,
                self.monitor.products_history,
                f"monitoring_data_{days}days.xlsx"
            )
            
            self.logger.info(f"報告已生成: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"生成報告失敗: {e}")
            return None
    
    def cleanup(self):
        """清理資源"""
        self.logger.info("正在清理資源...")
        
        try:
            # 停止監控
            self.monitor.stop_monitoring()
            
            # 關閉瀏覽器
            self.scraper.stop_driver()
            
            # 備份資料
            self.storage.backup_data()
            
            # 清理舊備份
            self.storage.cleanup_old_backups()
            
            self.logger.info("資源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理資源時發生錯誤: {e}")


def create_arg_parser():
    """建立命令列參數解析器"""
    parser = argparse.ArgumentParser(
        description="Amazon 商品自動購買工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py --once                    # 執行一次檢查
  python main.py --monitor                 # 持續監控
  python main.py --monitor --async         # 異步監控
  python main.py --test B08N5WRWNW         # 測試購買流程
  python main.py --report --days 7         # 生成 7 天報告
        """
    )
    
    parser.add_argument(
        '--once', 
        action='store_true',
        help='執行一次商品檢查後退出'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true', 
        help='執行持續監控'
    )
    
    parser.add_argument(
        '--async',
        action='store_true',
        help='使用異步監控模式'
    )
    
    parser.add_argument(
        '--test',
        metavar='ASIN',
        help='測試購買流程（指定商品 ASIN）'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='生成監控報告'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='報告天數（預設 7 天）'
    )
    
    return parser


def main():
    """主程式入口"""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    try:
        # 載入配置
        config = Config()
        
        # 建立應用程式實例
        app = AmazonBuyerApp(config)
        
        # 根據參數執行不同模式
        if args.once:
            app.run_once()
            
        elif args.monitor:
            if args.async:
                asyncio.run(app.run_monitor_async())
            else:
                app.run_monitor()
                
        elif args.test:
            result = app.test_purchase(args.test)
            if result:
                print(f"測試結果: {result}")
                
        elif args.report:
            report_file = app.generate_report(args.days)
            if report_file:
                print(f"報告已生成: {report_file}")
                
        else:
            # 預設行為：執行一次檢查
            print("未指定模式，執行一次檢查（使用 --help 查看所有選項）")
            app.run_once()
    
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
        sys.exit(0)
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()