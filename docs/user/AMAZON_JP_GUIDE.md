# Amazon.jp 使用指南

## 🇯🇵 Amazon.jp 專用功能

本工具已針對 Amazon.jp（日本亞馬遜）進行完整適配，支援：

- 日文介面元素識別
- 日圓價格解析
- 日文庫存狀態判斷
- Playwright 高效能爬蟲
- 反機器人偵測機制

## 🚀 快速設定

### 1. 安裝 Playwright

```bash
# 安裝 Playwright
pip install playwright

# 安裝瀏覽器
playwright install chromium
```

### 2. 配置 Amazon.jp

```bash
# 複製並編輯環境變數
cp .env.example .env
```

編輯 `.env` 檔案：

```bash
# Amazon.jp 設定
AMAZON_EMAIL=your_email@example.com
AMAZON_PASSWORD=your_password
AMAZON_BASE_URL=https://www.amazon.co.jp
AMAZON_REGION=jp
AMAZON_CURRENCY=JPY

# Playwright 設定
BROWSER_ENGINE=playwright
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_LOCALE=ja-JP

# 目標商品（日本 ASIN）
TARGET_PRODUCTS=B084J4WR8D,B08C1KN5J2

# 價格設定（日圓）
MAX_PRICE=10000
```

## 🛠️ 使用方式

### 基本操作

```bash
# 檢查單個商品
python src/main/python/main.py --test B084J4WR8D

# 執行一次檢查
python src/main/python/main.py --once

# 持續監控
python src/main/python/main.py --monitor

# 異步高效監控
python src/main/python/main.py --monitor --async
```

### 演示腳本

```bash
# 運行互動式演示
python examples/amazon_jp_demo.py
```

## 🎯 日本商品特色

### 常見商品類別 ASIN 示例

```bash
# 電子產品
B084J4WR8D  # Amazon Echo Dot (第4世代)
B08C1KN5J2  # Fire TV Stick
B07HZLHPKP  # Echo Show 5

# 遊戲
B08L8JZBSM  # PlayStation 5
B08P2PDV1Z  # Nintendo Switch Lite

# 書籍
B08XXXXX    # 日文書籍示例
```

### 價格格式

程式自動處理多種日文價格格式：

- `￥1,234` → ¥1,234
- `1,234円` → ¥1,234  
- `5,678 円` → ¥5,678
- `12,345JPY` → ¥12,345

### 庫存狀態識別

自動識別日文庫存狀態：

**有庫存：**
- 在庫あり
- すぐに発送
- 通常配送無料
- あと○個の在庫

**缺貨：**
- 在庫切れ
- 一時的に在庫切れ
- 入荷時期未定
- 現在在庫切れ

## ⚡ Playwright 優勢

相比 Selenium，Playwright 提供：

### 效能提升
- 更快的頁面載入
- 更低的記憶體使用
- 原生異步支援

### 更好的反檢測
- 內建反機器人機制
- 真實瀏覽器指紋
- 動態 User-Agent

### 多瀏覽器支援
```bash
# 可選擇不同瀏覽器
BROWSER_TYPE=chromium  # 預設，推薦
BROWSER_TYPE=firefox   # 替代選項
BROWSER_TYPE=webkit    # Safari 核心
```

## 🔧 進階配置

### 語言和地區設定

```bash
# 日本地區設定
BROWSER_LOCALE=ja-JP
AMAZON_REGION=jp
AMAZON_CURRENCY=JPY

# 時區設定（程式自動處理）
# 日本時區：Asia/Tokyo
```

### 監控頻率建議

```bash
# 一般商品（不急）
MONITOR_INTERVAL=600  # 10分鐘

# 熱門商品
MONITOR_INTERVAL=300  # 5分鐘

# 限量商品（謹慎使用）
MONITOR_INTERVAL=60   # 1分鐘
```

### 價格設定參考

```bash
# 日用品
MAX_PRICE=5000     # ¥5,000

# 電子產品
MAX_PRICE=50000    # ¥50,000

# 奢侈品
MAX_PRICE=100000   # ¥100,000
```

## 📊 監控報告

### 日圓格式化

報告中價格自動格式化為日圓：

```
商品: B084J4WR8D
當前價格: ¥5,980
最低價格: ¥4,980  
最高價格: ¥6,980
平均價格: ¥5,647
```

### Excel 匯出

支援日文字符的 Excel 匯出：

```bash
python src/main/python/main.py --report --days 7
```

## 🛡️ 安全注意事項

### Amazon.jp 特殊規則

1. **購買限制**
   - 某些商品限日本地址
   - 需要日本信用卡
   - 可能需要身分驗證

2. **配送限制**
   - 確認配送地址設定
   - 注意國際配送政策
   - 檢查關稅和稅費

3. **帳戶安全**
   - 使用日本 Amazon 帳戶
   - 避免過度頻繁操作
   - 定期檢查帳戶狀態

### 合規使用

1. **遵守服務條款**
   - 遵循 Amazon.jp 使用條款
   - 不進行商業轉售
   - 尊重其他用戶權益

2. **技術限制**
   - 適當的請求間隔
   - 合理的重試機制
   - 避免過載伺服器

## 🔍 疑難排解

### 常見問題

#### 1. 無法訪問 Amazon.jp
```bash
# 檢查網路連接
ping amazon.co.jp

# 確認 URL 設定
echo $AMAZON_BASE_URL
```

#### 2. 日文字符顯示問題
```bash
# 確認終端支援 UTF-8
export LANG=ja_JP.UTF-8

# 或使用英文環境
export LANG=en_US.UTF-8
```

#### 3. Playwright 安裝問題
```bash
# 重新安裝
pip uninstall playwright
pip install playwright
playwright install chromium
```

#### 4. 登入失敗
- 檢查是否需要雙重驗證
- 確認帳戶在日本地區
- 嘗試手動登入確認

### 效能優化

```bash
# 使用異步模式
python src/main/python/main.py --monitor --async

# 調整並發數
# 在監控服務中，可以同時處理多個商品

# 使用無頭模式
BROWSER_HEADLESS=true
```

## 📈 最佳實踐

### 1. 商品選擇
- 選擇有明確 ASIN 的商品
- 避免變體商品（顏色、尺寸）
- 確認商品在日本有售

### 2. 價格策略
- 研究商品歷史價格
- 設定合理的價格上限
- 考慮匯率波動

### 3. 監控策略
- 錯開監控時間
- 使用不同的 User-Agent
- 定期清理監控列表

### 4. 購買策略
- 先使用測試模式
- 確認支付方式
- 準備備用帳戶

## 🎉 成功案例

### 範例 1：監控 Echo 產品
```bash
# 設定目標
TARGET_PRODUCTS=B084J4WR8D
MAX_PRICE=5000

# 開始監控
python src/main/python/main.py --monitor

# 結果：成功在特價時購買
```

### 範例 2：遊戲機搶購
```bash
# 高頻監控（謹慎使用）
MONITOR_INTERVAL=30
AUTO_BUY_ENABLED=true

# 異步模式提高效率
python src/main/python/main.py --monitor --async
```

## 📞 支援

如有問題，請：

1. 檢查日誌檔案：`logs/amazonbuyer.log`
2. 運行測試腳本：`python examples/amazon_jp_demo.py`
3. 查看專案文件：`docs/user/USAGE.md`

---

**注意：** 本工具僅供學習和個人使用，請務必遵守相關法律法規和服務條款。