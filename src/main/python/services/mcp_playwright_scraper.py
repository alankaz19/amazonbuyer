"""MCP Playwright 爬蟲服務 - 使用 Playwright MCP Server"""

import json
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
from loguru import logger

from core.config import Config
from models.product import Product


class MCPPlaywrightScraper:
    """使用 MCP Playwright Server 的爬蟲"""
    
    def __init__(self, config: Config):
        self.config = config
        self.mcp_server_running = False
        self._check_mcp_availability()
        
        # Amazon.jp 特定設定
        self.jp_selectors = self._get_jp_selectors()
        self.jp_text_patterns = self._get_jp_text_patterns()
    
    def _check_mcp_availability(self):
        """檢查 MCP Playwright Server 是否可用"""
        try:
            result = subprocess.run(
                ["npx", "@playwright/mcp@latest", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("MCP Playwright Server 可用")
                self.mcp_server_running = True
            else:
                logger.warning("MCP Playwright Server 不可用")
        except Exception as e:
            logger.warning(f"無法檢查 MCP Playwright Server: {e}")
    
    def _get_jp_selectors(self) -> Dict[str, list]:
        """獲取 amazon.jp 特定的選擇器"""
        return {
            'title': [
                '#productTitle',
                'h1.a-size-large',
                'h1#title',
            ],
            'price': [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#price_inside_buybox',
                '.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen',
                '.a-price.a-text-price.a-size-base .a-offscreen',
                '#corePrice_feature_div .a-offscreen',
            ],
            'availability': [
                '#availability span',
                '#merchant-info',
                '#buybox-availability-message',
                '.a-alert-content',
            ],
            'image': [
                '#landingImage',
                '#imgTagWrapperId img',
                '.a-image.a-image-main img',
            ],
        }
    
    def _get_jp_text_patterns(self) -> Dict[str, list]:
        """獲取日文文字模式"""
        return {
            'in_stock': ['在庫あり', 'すぐに発送', '即日発送', '通常配送無料', 'あと', '個の在庫'],
            'out_of_stock': ['在庫切れ', '一時的に在庫切れ', '入荷時期未定', '現在在庫切れ'],
            'price_symbols': ['￥', '円', 'JPY'],
        }
    
    def _create_mcp_script(self, asin: str) -> str:
        """創建 MCP 腳本來抓取商品資訊"""
        url = f"{self.config.amazon_base_url}/dp/{asin}"
        
        script = f"""
        // MCP Playwright 腳本 - Amazon.jp 商品抓取
        const {{ chromium }} = require('playwright');
        
        (async () => {{
            const browser = await chromium.launch({{
                headless: {str(self.config.browser_headless).lower()},
                args: [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            }});
            
            const context = await browser.newContext({{
                locale: '{self.config.browser_locale}',
                timezoneId: 'Asia/Tokyo',
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }});
            
            // 反檢測腳本
            await context.addInitScript(() => {{
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                }});
            }});
            
            const page = await context.newPage();
            page.setDefaultTimeout({self.config.browser_timeout * 1000});
            
            try {{
                await page.goto('{url}', {{ waitUntil: 'domcontentloaded' }});
                await page.waitForSelector('#productTitle', {{ timeout: 10000 }});
                
                // 提取商品資訊
                const productInfo = await page.evaluate(() => {{
                    const selectors = {{
                        title: {json.dumps(self.jp_selectors['title'])},
                        price: {json.dumps(self.jp_selectors['price'])},
                        availability: {json.dumps(self.jp_selectors['availability'])},
                        image: {json.dumps(self.jp_selectors['image'])}
                    }};
                    
                    function getTextBySelectors(selectorList) {{
                        for (const selector of selectorList) {{
                            const element = document.querySelector(selector);
                            if (element) {{
                                return element.textContent?.trim() || element.innerText?.trim() || '';
                            }}
                        }}
                        return null;
                    }}
                    
                    function getAttributeBySelectors(selectorList, attribute) {{
                        for (const selector of selectorList) {{
                            const element = document.querySelector(selector);
                            if (element) {{
                                return element.getAttribute(attribute);
                            }}
                        }}
                        return null;
                    }}
                    
                    return {{
                        title: getTextBySelectors(selectors.title) || 'Unknown',
                        price: getTextBySelectors(selectors.price),
                        availability: getTextBySelectors(selectors.availability) || 'Unknown',
                        image: getAttributeBySelectors(selectors.image, 'src')
                    }};
                }});
                
                console.log(JSON.stringify(productInfo));
                
            }} catch (error) {{
                console.error('Error:', error.message);
                console.log(JSON.stringify({{ error: error.message }}));
            }} finally {{
                await browser.close();
            }}
        }})();
        """
        
        return script
    
    def _parse_jp_price(self, price_text: str) -> Optional[float]:
        """解析日文價格文字"""
        if not price_text:
            return None
            
        try:
            import re
            
            # 移除日文價格符號和格式
            price_text = price_text.replace('￥', '').replace('円', '').replace('JPY', '')
            price_text = price_text.replace(',', '').replace(' ', '')
            
            # 提取數字
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                price_str = price_match.group().replace(',', '')
                return float(price_str)
                
        except Exception as e:
            logger.warning(f"價格解析失敗: {price_text}, 錯誤: {e}")
        
        return None
    
    def _parse_jp_availability(self, availability_text: str) -> str:
        """解析日文庫存狀態"""
        if not availability_text:
            return "Unknown"
            
        text_lower = availability_text.lower()
        
        # 檢查有庫存的模式
        for pattern in self.jp_text_patterns['in_stock']:
            if pattern in availability_text:
                return "In Stock"
        
        # 檢查缺貨的模式
        for pattern in self.jp_text_patterns['out_of_stock']:
            if pattern in availability_text:
                return "Out of Stock"
        
        # 英文回退檢查
        if any(keyword in text_lower for keyword in ['in stock', 'available']):
            return "In Stock"
        elif any(keyword in text_lower for keyword in ['out of stock', 'unavailable']):
            return "Out of Stock"
        
        return "Unknown"
    
    def get_product_info(self, asin: str) -> Optional[Product]:
        """使用 MCP 獲取商品資訊"""
        if not self.mcp_server_running:
            logger.error("MCP Playwright Server 不可用")
            return None
        
        try:
            logger.info(f"使用 MCP 獲取商品資訊: {asin}")
            
            # 創建臨時腳本檔案
            script_content = self._create_mcp_script(asin)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # 執行 MCP Playwright 腳本
                result = subprocess.run(
                    ["node", script_path],
                    capture_output=True,
                    text=True,
                    timeout=self.config.browser_timeout + 10
                )
                
                if result.returncode == 0:
                    # 解析結果
                    output_lines = result.stdout.strip().split('\n')
                    json_line = output_lines[-1]  # 最後一行應該是 JSON
                    
                    product_data = json.loads(json_line)
                    
                    if 'error' in product_data:
                        logger.error(f"MCP 腳本錯誤: {product_data['error']}")
                        return None
                    
                    # 解析價格和庫存
                    price = self._parse_jp_price(product_data.get('price'))
                    availability = self._parse_jp_availability(product_data.get('availability'))
                    
                    return Product(
                        asin=asin,
                        title=product_data.get('title', 'Unknown'),
                        price=price,
                        currency=self.config.amazon_currency,
                        availability=availability,
                        image_url=product_data.get('image'),
                        url=f"{self.config.amazon_base_url}/dp/{asin}"
                    )
                else:
                    logger.error(f"MCP 腳本執行失敗: {result.stderr}")
                    return None
                    
            finally:
                # 清理臨時檔案
                try:
                    os.unlink(script_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"MCP 獲取商品資訊失敗 {asin}: {e}")
            return None
    
    def login(self) -> bool:
        """登入功能（MCP 版本暫不支援）"""
        logger.warning("MCP 版本暫不支援自動登入功能")
        return False
    
    def add_to_cart(self, asin: str) -> bool:
        """加入購物車功能（MCP 版本暫不支援）"""
        logger.warning("MCP 版本暫不支援自動加入購物車功能")
        return False
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """隨機延遲"""
        import time
        import random
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def start_driver(self):
        """啟動驅動（MCP 版本不需要）"""
        pass
    
    def stop_driver(self):
        """停止驅動（MCP 版本不需要）"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass