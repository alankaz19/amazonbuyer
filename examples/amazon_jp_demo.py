#!/usr/bin/env python3
"""
Amazon.jp Playwright 演示腳本
展示如何使用新的 Playwright 爬蟲獲取日本 Amazon 商品資訊
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from core.config import Config
from core.logger import setup_logger
from services.unified_scraper import UnifiedAmazonScraper, AsyncUnifiedAmazonScraper


def demo_sync_scraper():
    """演示同步爬蟲使用"""
    print("🤖 Amazon.jp Playwright 同步爬蟲演示")
    print("=" * 50)
    
    # 設定環境變數（演示用）
    demo_env = {
        'AMAZON_EMAIL': 'demo@example.com',
        'AMAZON_PASSWORD': 'demo_password',
        'AMAZON_BASE_URL': 'https://www.amazon.co.jp',
        'AMAZON_REGION': 'jp',
        'AMAZON_CURRENCY': 'JPY',
        'BROWSER_ENGINE': 'playwright',
        'BROWSER_HEADLESS': 'true',
        'BROWSER_LOCALE': 'ja-JP',
        'LOG_LEVEL': 'INFO'
    }
    
    # 臨時設定環境變數
    for key, value in demo_env.items():
        os.environ[key] = value
    
    try:
        # 初始化配置和爬蟲
        config = Config()
        logger = setup_logger(config.log_level)
        
        logger.info("初始化 Amazon.jp 爬蟲...")
        
        # 使用統一爬蟲介面
        scraper = UnifiedAmazonScraper(config)
        
        # 示例日本商品 ASIN (Amazon Echo Dot)
        demo_asins = [
            "B084J4WR8D",  # Echo Dot (4th Gen)
            "B08C1KN5J2",  # Fire TV Stick
            "B07HZLHPKP",  # Echo Show 5
        ]
        
        print(f"\n📱 使用 {config.browser_engine} 引擎")
        print(f"🌐 目標網站: {config.amazon_base_url}")
        print(f"💰 貨幣: {config.amazon_currency}")
        print(f"🗣️ 語言: {config.browser_locale}")
        
        with scraper:
            for asin in demo_asins:
                print(f"\n🔍 檢查商品: {asin}")
                
                try:
                    product = scraper.get_product_info(asin)
                    
                    if product:
                        print(f"  ✅ 商品名稱: {product.title[:60]}...")
                        print(f"  💰 價格: {product.get_formatted_price()}")
                        print(f"  📦 庫存: {product.availability}")
                        print(f"  🔗 連結: {product.url}")
                        
                        if product.should_buy(max_price=10000):  # 10,000 日圓
                            print("  🛒 符合購買條件！")
                        else:
                            print("  ❌ 不符合購買條件")
                    else:
                        print("  ❌ 無法獲取商品資訊")
                
                except Exception as e:
                    print(f"  ❌ 錯誤: {e}")
                
                # 延遲避免請求過快
                scraper.random_delay(2, 4)
        
        print("\n✅ 演示完成！")
        
    except Exception as e:
        print(f"❌ 演示失敗: {e}")
        print("\n💡 提示:")
        print("1. 請確保已安裝 playwright: pip install playwright")
        print("2. 安裝瀏覽器: playwright install chromium")
        print("3. 檢查網路連接是否正常")


async def demo_async_scraper():
    """演示異步爬蟲使用"""
    print("\n🚀 Amazon.jp Playwright 異步爬蟲演示")
    print("=" * 50)
    
    # 設定環境變數（演示用）
    demo_env = {
        'AMAZON_EMAIL': 'demo@example.com',
        'AMAZON_PASSWORD': 'demo_password',
        'AMAZON_BASE_URL': 'https://www.amazon.co.jp',
        'AMAZON_REGION': 'jp',
        'AMAZON_CURRENCY': 'JPY',
        'BROWSER_ENGINE': 'playwright',
        'BROWSER_HEADLESS': 'true',
        'BROWSER_LOCALE': 'ja-JP',
        'LOG_LEVEL': 'INFO'
    }
    
    # 臨時設定環境變數
    for key, value in demo_env.items():
        os.environ[key] = value
    
    try:
        # 初始化配置
        config = Config()
        logger = setup_logger(config.log_level)
        
        logger.info("初始化異步 Amazon.jp 爬蟲...")
        
        # 示例商品
        demo_asins = [
            "B084J4WR8D",  # Echo Dot (4th Gen)
            "B08C1KN5J2",  # Fire TV Stick
        ]
        
        # 使用異步爬蟲
        async with AsyncUnifiedAmazonScraper(config) as async_scraper:
            
            print(f"\n🔄 異步處理 {len(demo_asins)} 個商品")
            
            # 併發獲取商品資訊
            tasks = []
            for asin in demo_asins:
                task = async_scraper.get_product_info(asin)
                tasks.append(task)
            
            # 等待所有任務完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 顯示結果
            for asin, result in zip(demo_asins, results):
                print(f"\n🔍 商品 {asin}:")
                
                if isinstance(result, Exception):
                    print(f"  ❌ 錯誤: {result}")
                elif result:
                    print(f"  ✅ 名稱: {result.title[:60]}...")
                    print(f"  💰 價格: {result.get_formatted_price()}")
                    print(f"  📦 庫存: {result.availability}")
                else:
                    print("  ❌ 無法獲取商品資訊")
        
        print("\n🎉 異步演示完成！")
        
    except Exception as e:
        print(f"❌ 異步演示失敗: {e}")


def demo_price_monitoring():
    """演示價格監控功能"""
    print("\n📊 Amazon.jp 價格監控演示")
    print("=" * 50)
    
    from models.product import Product
    
    # 模擬商品資料
    products = [
        Product(
            asin="B084J4WR8D",
            title="Amazon Echo Dot (第4世代) - スマートスピーカー with Alexa",
            price=5980.0,
            currency="JPY",
            availability="在庫あり",
            url="https://www.amazon.co.jp/dp/B084J4WR8D"
        ),
        Product(
            asin="B08C1KN5J2",
            title="Fire TV Stick - Alexa対応音声認識リモコン付属",
            price=4980.0,
            currency="JPY",
            availability="一時的に在庫切れ",
            url="https://www.amazon.co.jp/dp/B08C1KN5J2"
        ),
    ]
    
    print("\n📦 監控商品列表:")
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.title}")
        print(f"   💰 價格: {product.get_formatted_price()}")
        print(f"   📦 庫存: {product.availability}")
        print(f"   ✅ 有庫存: {'是' if product.is_available() else '否'}")
        print(f"   🛒 建議購買: {'是' if product.should_buy(max_price=6000) else '否'}")
    
    print("\n💡 監控建議:")
    available_products = [p for p in products if p.is_available()]
    print(f"• 目前有 {len(available_products)} 個商品有庫存")
    
    affordable_products = [p for p in products if p.meets_price_criteria(max_price=6000)]
    print(f"• 目前有 {len(affordable_products)} 個商品價格在預算內（¥6,000以下）")


def main():
    """主函數"""
    print("🇯🇵 Amazon.jp Playwright 爬蟲演示")
    print("=" * 60)
    
    try:
        # 檢查 Playwright 是否已安裝
        try:
            import playwright
            print("✅ Playwright 已安裝")
        except ImportError:
            print("❌ Playwright 未安裝")
            print("請運行: pip install playwright")
            print("然後運行: playwright install chromium")
            return
        
        print("\n選擇演示模式:")
        print("1. 同步爬蟲演示")
        print("2. 異步爬蟲演示")  
        print("3. 價格監控演示")
        print("4. 全部演示")
        
        choice = input("\n請輸入選擇 (1-4): ").strip()
        
        if choice == "1":
            demo_sync_scraper()
        elif choice == "2":
            asyncio.run(demo_async_scraper())
        elif choice == "3":
            demo_price_monitoring()
        elif choice == "4":
            demo_sync_scraper()
            asyncio.run(demo_async_scraper())
            demo_price_monitoring()
        else:
            print("❌ 無效選擇")
    
    except KeyboardInterrupt:
        print("\n\n👋 演示已中斷")
    except Exception as e:
        print(f"\n❌ 演示錯誤: {e}")


if __name__ == "__main__":
    main()