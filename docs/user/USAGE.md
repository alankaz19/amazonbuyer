# Amazon 自動購買工具使用指南

## 🚀 快速開始

### 1. 環境設定

```bash
# 安裝依賴
pip install -r requirements.txt

# 複製環境變數範例檔案
cp .env.example .env

# 編輯配置檔案
nano .env
```

### 2. 配置設定

在 `.env` 檔案中設定必要的環境變數：

```bash
# Amazon 帳戶設定
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password

# 目標商品 (以逗號分隔的 ASIN)
TARGET_PRODUCTS=B08N5WRWNW,B0932HKQCT

# 購買設定
AUTO_BUY_ENABLED=false  # 設為 true 啟用自動購買
MAX_PRICE=100.0         # 最高價格限制

# 監控設定
MONITOR_INTERVAL=300    # 檢查間隔（秒）
```

### 3. 基本使用

```bash
# 執行一次檢查
python src/main/python/main.py --once

# 持續監控
python src/main/python/main.py --monitor

# 測試購買流程（不實際下單）
python src/main/python/main.py --test B08N5WRWNW

# 生成監控報告
python src/main/python/main.py --report --days 7
```

## 📖 詳細功能

### 監控模式

#### 單次檢查
```bash
python src/main/python/main.py --once
```
- 檢查所有配置的商品
- 儲存結果到 JSON 和 CSV 檔案
- 生成簡單報告

#### 持續監控
```bash
python src/main/python/main.py --monitor
```
- 按照設定間隔持續檢查商品
- 自動記錄價格和庫存變化
- 支援自動購買（需啟用）

#### 異步監控
```bash
python src/main/python/main.py --monitor --async
```
- 使用異步方式執行監控
- 更高效的資源使用
- 適合長時間運行

### 購買功能

#### 測試購買流程
```bash
python src/main/python/main.py --test B08N5WRWNW
```
- 模擬完整購買流程
- 不會實際下單
- 檢查每個步驟是否可行

#### 啟用自動購買
在 `.env` 檔案中設定：
```bash
AUTO_BUY_ENABLED=true
MAX_PRICE=150.0
BUY_QUANTITY=1
```

### 報告功能

#### 生成監控報告
```bash
python src/main/python/main.py --report --days 7
```
- 生成指定天數的監控報告
- 包含價格趨勢和庫存統計
- 匯出到 Markdown 和 Excel 格式

## ⚙️ 進階配置

### 瀏覽器設定

```bash
# 瀏覽器設定
BROWSER_HEADLESS=true   # 無頭模式
BROWSER_TIMEOUT=30      # 超時時間（秒）
```

### 通知設定

程式支援多種通知方式：

#### 電子郵件通知
```python
# 在程式中設定
email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your_email@gmail.com',
    'password': 'your_app_password'
}

app.setup_notifications(email_config=email_config)
```

#### Slack 通知
```python
slack_webhook = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
app.setup_notifications(slack_webhook=slack_webhook)
```

### 資料儲存

監控資料會自動儲存到 `output/` 目錄：

- `product_history.json` - 商品歷史記錄
- `purchase_history.json` - 購買歷史記錄
- `latest_check.json/csv` - 最新檢查結果
- `monitoring_report_*.md` - 監控報告
- `monitoring_data_*.xlsx` - Excel 資料匯出

## 🛡️ 安全注意事項

### 帳戶安全
- 使用強密碼
- 考慮使用應用程式專用密碼
- 定期檢查帳戶活動

### 反機器人機制
- 程式已內建隨機延遲
- 使用真實瀏覽器 User-Agent
- 避免過於頻繁的請求

### 購買安全
- 建議先使用測試模式
- 設定合理的價格上限
- 監控購買歷史記錄

## 🔧 疑難排解

### 常見問題

#### 1. 登入失敗
```
解決方法：
- 檢查帳號密碼是否正確
- 確認 Amazon 帳戶狀態正常
- 檢查是否需要雙重驗證
```

#### 2. 商品資訊獲取失敗
```
解決方法：
- 檢查 ASIN 是否正確
- 確認網路連線正常
- 嘗試手動開啟商品頁面
```

#### 3. 購買失敗
```
解決方法：
- 確認商品有庫存
- 檢查支付方式設定
- 驗證配送地址
```

#### 4. WebDriver 錯誤
```
解決方法：
- 安裝 Chrome 瀏覽器
- 更新 ChromeDriver
- 檢查 Selenium 版本
```

### 日誌分析

日誌檔案位置：`logs/amazonbuyer.log`

查看即時日誌：
```bash
tail -f logs/amazonbuyer.log
```

### 效能調優

#### 減少資源使用
```bash
# 使用無頭模式
BROWSER_HEADLESS=true

# 增加檢查間隔
MONITOR_INTERVAL=600  # 10分鐘
```

#### 提高檢查頻率
```bash
# 縮短檢查間隔（注意可能被封）
MONITOR_INTERVAL=60   # 1分鐘
```

## 📊 使用範例

### 場景 1：監控特定商品價格
```bash
# 設定目標商品和價格上限
echo "TARGET_PRODUCTS=B08N5WRWNW" >> .env
echo "MAX_PRICE=50.0" >> .env

# 開始監控
python src/main/python/main.py --monitor
```

### 場景 2：搶購限量商品
```bash
# 啟用自動購買，縮短檢查間隔
echo "AUTO_BUY_ENABLED=true" >> .env
echo "MONITOR_INTERVAL=30" >> .env

# 使用異步監控提高效率
python src/main/python/main.py --monitor --async
```

### 場景 3：價格趨勢分析
```bash
# 長期監控收集資料
python src/main/python/main.py --monitor

# 定期生成報告
python src/main/python/main.py --report --days 30
```

## 📝 最佳實踐

1. **負責任使用**
   - 遵守 Amazon 服務條款
   - 不要過度頻繁請求
   - 尊重其他使用者

2. **資料備份**
   - 定期備份監控資料
   - 匯出重要報告
   - 保存購買記錄

3. **監控優化**
   - 根據商品特性調整間隔
   - 設定合理價格上限
   - 定期檢查配置

4. **安全維護**
   - 定期更新依賴套件
   - 檢查日誌文件
   - 監控程式運行狀態