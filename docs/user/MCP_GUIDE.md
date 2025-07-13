# MCP Playwright 使用指南

## 🎭 關於 MCP Playwright

MCP (Model Context Protocol) Playwright 是一個現代化的爬蟲解決方案，提供：

- 🚀 **更高效能** - 比直接 Playwright 更輕量
- 🔒 **更好隔離** - 每個腳本獨立執行
- 🛡️ **更強安全** - 沙盒環境執行
- 📦 **零依賴** - 不需要安裝 Playwright Python 套件

## 🚀 快速設定

### 1. 安裝 MCP Playwright Server

```bash
# 全域安裝
npm install -g @playwright/mcp@latest

# 或使用 npx（推薦）
npx @playwright/mcp@latest --version
```

### 2. 安裝 Node.js 和 Playwright

```bash
# 確保 Node.js 已安裝
node --version

# 安裝 Playwright（透過 npx）
npx playwright install chromium
```

### 3. 配置使用 MCP

編輯 `.env` 檔案：

```bash
# 使用 MCP Playwright 引擎
BROWSER_ENGINE=mcp

# 其他設定保持不變
AMAZON_BASE_URL=https://www.amazon.co.jp
AMAZON_REGION=jp
AMAZON_CURRENCY=JPY
```

## 🎯 使用方式

### 基本使用

```bash
# 測試 MCP 是否工作正常
python src/main/python/main.py --test B084J4WR8D

# 使用 MCP 進行監控
python src/main/python/main.py --monitor
```

### 驗證 MCP 設定

```bash
# 檢查 MCP Playwright 是否可用
npx @playwright/mcp@latest --version

# 測試 Node.js 環境
node -e "console.log('Node.js 正常運行')"

# 檢查 Playwright 安裝
npx playwright --version
```

## ⚡ MCP vs 其他引擎比較

| 特色 | MCP | Playwright | Selenium |
|------|-----|------------|----------|
| 安裝複雜度 | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 執行效率 | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 記憶體使用 | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 隔離性 | ⭐⭐⭐ | ⭐ | ⭐ |
| 維護性 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |

## 🔧 進階配置

### 自訂 MCP 腳本

MCP 爬蟲使用動態生成的 JavaScript 腳本，您可以在 `MCPPlaywrightScraper` 中自訂：

```python
# 在 mcp_playwright_scraper.py 中
def _create_mcp_script(self, asin: str) -> str:
    # 自訂您的爬蟲邏輯
    pass
```

### 錯誤處理

MCP 引擎具有完善的錯誤處理和回退機制：

```bash
# 如果 MCP 失敗，會自動回退到 Playwright
# 如果 Playwright 失敗，會回退到 Selenium
```

### 除錯模式

```bash
# 啟用詳細日誌
LOG_LEVEL=DEBUG

# 顯示瀏覽器視窗（除錯用）
BROWSER_HEADLESS=false
```

## 🐛 疑難排解

### 常見問題

#### 1. MCP 命令找不到
```bash
# 解決方案：檢查 Node.js 安裝
node --version
npm --version

# 重新安裝 MCP
npm uninstall -g @playwright/mcp
npm install -g @playwright/mcp@latest
```

#### 2. Playwright 未安裝
```bash
# 解決方案：安裝 Playwright 瀏覽器
npx playwright install chromium

# 或安裝所有瀏覽器
npx playwright install
```

#### 3. 腳本執行失敗
```bash
# 檢查日誌
tail -f logs/amazonbuyer.log

# 檢查 Node.js 權限
node -e "console.log(process.version)"
```

#### 4. Amazon.jp 訪問失敗
```bash
# 檢查網路連接
ping amazon.co.jp

# 檢查代理設定
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

### 效能調優

```bash
# 增加超時時間
BROWSER_TIMEOUT=60

# 使用更快的瀏覽器
BROWSER_TYPE=chromium  # 推薦

# 啟用無頭模式
BROWSER_HEADLESS=true
```

## 🔒 安全考量

### MCP 優勢

1. **沙盒執行** - 每個腳本在獨立進程中執行
2. **資源限制** - 自動記憶體和 CPU 限制
3. **臨時檔案** - 腳本檔案自動清理
4. **權限控制** - 最小權限原則

### 最佳實踐

```bash
# 定期更新 MCP
npm update -g @playwright/mcp

# 監控系統資源
# MCP 會自動管理資源，但建議監控

# 設定合理的超時
BROWSER_TIMEOUT=30  # 不要設定過長
```

## 📊 效能監控

### 監控指標

```bash
# 檢查 MCP 進程
ps aux | grep playwright

# 監控記憶體使用
top -p $(pgrep -f playwright)

# 檢查臨時檔案
ls -la /tmp/*.js 2>/dev/null | wc -l
```

### 最佳化建議

1. **定期重啟** - 長時間運行後重啟應用
2. **清理快取** - 定期清理瀏覽器快取
3. **資源監控** - 監控系統資源使用

## 📈 使用統計

啟用 MCP 後，您可以在日誌中看到：

```
INFO: 使用 MCP Playwright 爬蟲引擎
INFO: MCP Playwright Server 可用
INFO: 使用 MCP 獲取商品資訊: B084J4WR8D
```

## 🔄 回退機制

智能回退順序：

1. **MCP Playwright** (首選)
2. **直接 Playwright** (回退 1)
3. **Selenium** (回退 2)

```bash
# 強制使用特定引擎
BROWSER_ENGINE=mcp          # MCP 優先
BROWSER_ENGINE=playwright   # Playwright 優先  
BROWSER_ENGINE=selenium     # Selenium 優先
```

## 💡 提示和技巧

### 1. 快速切換引擎

```bash
# 創建多個配置檔案
cp .env .env.mcp
cp .env .env.playwright
cp .env .env.selenium

# 快速切換
ln -sf .env.mcp .env
```

### 2. 效能基準測試

```bash
# 測試不同引擎的效能
time python src/main/python/main.py --test B084J4WR8D
```

### 3. 批量測試

```python
# 使用 Python 腳本批量測試
for engine in ['mcp', 'playwright', 'selenium']:
    os.environ['BROWSER_ENGINE'] = engine
    # 執行測試
```

---

**注意：** MCP Playwright 是實驗性功能，建議在生產環境中進行充分測試。