# 🇯🇵 Amazon.jp 自動購買工具

> **專為 Amazon.jp 優化的 Playwright 爬蟲工具**

## ✨ 主要特色

- 🎯 **Amazon.jp 專用適配** - 完整支援日文介面和日圓價格
- ⚡ **Playwright 引擎** - 比 Selenium 更快、更穩定的現代爬蟲
- 🔄 **智能監控** - 自動價格追蹤和庫存監控
- 🛒 **自動購買** - 支援完整的購買流程自動化
- 📊 **數據分析** - 詳細的價格歷史和統計報告
- 🔔 **多重通知** - Email、Slack、Webhook 通知支援
- ⚙️ **雙引擎支援** - Playwright + Selenium 回退機制

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 Playwright（推薦）
playwright install chromium
```

### 2. 配置設定

```bash
# 複製配置範例
cp .env.example .env

# 編輯配置檔案
nano .env
```

基本配置：
```bash
# Amazon.jp 帳戶
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password

# 目標商品（日本 ASIN）
TARGET_PRODUCTS=B084J4WR8D,B08C1KN5J2

# 價格限制（日圓）
MAX_PRICE=10000
```

### 3. 開始使用

```bash
# 測試單個商品
python src/main/python/main.py --test B084J4WR8D

# 執行一次檢查
python src/main/python/main.py --once

# 持續監控
python src/main/python/main.py --monitor

# 高效異步監控
python src/main/python/main.py --monitor --async
```

## 📖 詳細文件

- 📚 [完整使用指南](docs/user/USAGE.md)
- 🇯🇵 [Amazon.jp 專用指南](docs/user/AMAZON_JP_GUIDE.md)
- 🎮 [互動式演示](examples/amazon_jp_demo.py)

## 🛠️ 核心功能

### 智能爬蟲
- **Playwright 引擎**：現代化、高效能
- **反檢測機制**：避免被 Amazon 封鎖
- **多瀏覽器支援**：Chromium、Firefox、WebKit
- **異步處理**：提升監控效率

### Amazon.jp 特化
- **日文介面解析**：完整支援日文元素
- **日圓價格處理**：自動格式化和轉換
- **庫存狀態識別**：準確判斷日文庫存信息
- **地區優化**：針對日本市場優化

### 監控功能
- **實時價格追蹤**：自動記錄價格變化
- **庫存監控**：即時通知補貨情況
- **歷史分析**：詳細的價格趨勢分析
- **多商品支援**：同時監控多個商品

### 自動購買
- **完整流程**：從加入購物車到下單
- **安全機制**：多重驗證和確認
- **測試模式**：乾式運行測試購買流程
- **智能判斷**：根據價格和庫存自動決策

## 🏗️ 專案架構

```
amazonbuyer/
├── src/main/python/          # 主要程式碼
│   ├── core/                 # 核心配置和日誌
│   ├── services/             # 爬蟲和業務服務
│   │   ├── playwright_scraper.py    # Playwright 爬蟲
│   │   ├── unified_scraper.py       # 統一爬蟲介面
│   │   ├── product_monitor.py       # 商品監控服務
│   │   └── auto_buyer.py           # 自動購買服務
│   ├── models/               # 資料模型
│   └── utils/                # 工具模組
├── src/test/                 # 測試程式碼
├── docs/user/                # 使用文件
├── examples/                 # 範例腳本
└── output/                   # 輸出資料
```

## 🎯 使用範例

### 監控 Echo 產品

```bash
# 設定環境變數
export TARGET_PRODUCTS="B084J4WR8D"
export MAX_PRICE="5000"

# 開始監控
python src/main/python/main.py --monitor
```

### 異步高效監控

```python
# 使用 Python 腳本
import asyncio
from core.config import Config
from services.unified_scraper import AsyncUnifiedAmazonScraper

async def monitor_products():
    config = Config()
    async with AsyncUnifiedAmazonScraper(config) as scraper:
        product = await scraper.get_product_info("B084J4WR8D")
        print(f"價格: {product.get_formatted_price()}")

asyncio.run(monitor_products())
```

### 價格分析報告

```bash
# 生成週報告
python src/main/python/main.py --report --days 7

# 匯出到 Excel
# 自動生成 monitoring_data_7days.xlsx
```

## 🔧 進階配置

### 瀏覽器選擇

```bash
# Playwright（推薦）
BROWSER_ENGINE=playwright
BROWSER_TYPE=chromium

# Selenium（回退）
BROWSER_ENGINE=selenium
```

### 監控頻率

```bash
# 一般商品
MONITOR_INTERVAL=300  # 5分鐘

# 熱門商品
MONITOR_INTERVAL=60   # 1分鐘

# 限量商品（謹慎）
MONITOR_INTERVAL=30   # 30秒
```

### 通知設定

```python
# 在程式中設定多重通知
app.setup_notifications(
    email_config={
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your_email@gmail.com',
        'password': 'your_password'
    },
    slack_webhook="https://hooks.slack.com/services/...",
    custom_webhook="https://your-webhook-url.com"
)
```

## 📊 數據分析

### 支援格式
- **JSON**：結構化數據儲存
- **CSV**：表格數據分析
- **Excel**：完整報告匯出
- **Markdown**：可讀性報告

### 統計功能
- 價格趨勢分析
- 庫存可用率統計
- 商品比較報告
- 歷史數據備份

## 🛡️ 安全特色

### 反檢測機制
- 隨機延遲模擬人類行為
- 動態 User-Agent 輪換
- 真實瀏覽器指紋
- 智能請求頻率控制

### 資料安全
- 本地資料儲存
- 自動備份機制
- 敏感資訊加密
- 完整操作日誌

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 授權條款

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## ⚠️ 免責聲明

本工具僅供學習和個人使用，請務必：
- 遵守 Amazon.jp 服務條款
- 合理使用，避免濫用
- 尊重其他用戶權益
- 承擔使用風險

---

**🌟 Star this project if you find it useful!**