"""自動購買服務"""

import time
from typing import Optional, List, Dict
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger

from core.config import Config
from models.product import Product
from services.amazon_scraper import AmazonScraper


class AutoBuyer:
    """自動購買服務"""
    
    def __init__(self, config: Config, scraper: AmazonScraper):
        self.config = config
        self.scraper = scraper
        self.purchase_history: List[Dict] = []
        self.is_logged_in = False
    
    def ensure_login(self) -> bool:
        """確保已登入 Amazon
        
        Returns:
            是否成功登入
        """
        if not self.is_logged_in:
            success = self.scraper.login()
            if success:
                self.is_logged_in = True
                logger.info("Amazon 登入確認成功")
            else:
                logger.error("Amazon 登入失敗")
            return success
        return True
    
    def attempt_purchase(self, product: Product) -> bool:
        """嘗試購買商品
        
        Args:
            product: 要購買的商品
            
        Returns:
            是否成功購買
        """
        if not self.config.auto_buy_enabled:
            logger.info("自動購買功能已停用")
            return False
        
        # 檢查商品是否符合購買條件
        if not product.should_buy(self.config.max_price):
            logger.info(f"商品 {product.asin} 不符合購買條件")
            return False
        
        try:
            logger.info(f"嘗試購買商品: {product.asin} - {product.title}")
            
            # 確保已登入
            if not self.ensure_login():
                return False
            
            # 前往商品頁面
            self.scraper.driver.get(product.url)
            
            # 檢查商品是否仍然可用
            if not self._verify_product_availability():
                logger.warning(f"商品 {product.asin} 已無庫存")
                return False
            
            # 加入購物車
            if not self._add_to_cart():
                logger.error(f"無法將商品 {product.asin} 加入購物車")
                return False
            
            # 前往結帳
            if not self._proceed_to_checkout():
                logger.error("無法前往結帳頁面")
                return False
            
            # 完成購買
            if not self._complete_purchase():
                logger.error("購買流程失敗")
                return False
            
            # 記錄購買歷史
            self._record_purchase(product)
            
            logger.info(f"成功購買商品: {product.asin}")
            return True
            
        except Exception as e:
            logger.error(f"購買商品失敗 {product.asin}: {e}")
            return False
    
    def _verify_product_availability(self) -> bool:
        """驗證商品可用性"""
        try:
            # 檢查是否有加入購物車按鈕
            add_to_cart_btn = WebDriverWait(self.scraper.driver, 10).until(
                EC.presence_of_element_located((By.ID, "add-to-cart-button"))
            )
            
            # 檢查按鈕是否可點擊
            return add_to_cart_btn.is_enabled()
            
        except TimeoutException:
            logger.warning("找不到加入購物車按鈕")
            return False
    
    def _add_to_cart(self) -> bool:
        """加入購物車"""
        try:
            # 設定數量
            if self.config.buy_quantity > 1:
                self._set_quantity(self.config.buy_quantity)
            
            # 點擊加入購物車
            add_to_cart_btn = WebDriverWait(self.scraper.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "add-to-cart-button"))
            )
            add_to_cart_btn.click()
            
            # 等待加入購物車完成
            WebDriverWait(self.scraper.driver, 10).until(
                lambda driver: "add-to-cart" not in driver.current_url.lower() or
                               "cart" in driver.current_url.lower()
            )
            
            logger.info("商品已加入購物車")
            return True
            
        except Exception as e:
            logger.error(f"加入購物車失敗: {e}")
            return False
    
    def _set_quantity(self, quantity: int) -> bool:
        """設定購買數量
        
        Args:
            quantity: 購買數量
            
        Returns:
            是否成功設定
        """
        try:
            # 尋找數量選擇器
            quantity_selector = self.scraper.driver.find_element(By.ID, "quantity")
            
            if quantity_selector.tag_name == "select":
                # 下拉選單
                select = Select(quantity_selector)
                select.select_by_value(str(quantity))
            else:
                # 輸入框
                quantity_selector.clear()
                quantity_selector.send_keys(str(quantity))
            
            logger.info(f"設定購買數量: {quantity}")
            return True
            
        except NoSuchElementException:
            logger.warning("找不到數量選擇器，使用預設數量")
            return True
        except Exception as e:
            logger.error(f"設定數量失敗: {e}")
            return False
    
    def _proceed_to_checkout(self) -> bool:
        """前往結帳"""
        try:
            # 尋找結帳按鈕
            checkout_selectors = [
                'input[name="proceedToRetailCheckout"]',
                'a[href*="checkout"]',
                'input[value*="Proceed"]',
                '#sc-buy-box-ptc-button',
            ]
            
            checkout_btn = None
            for selector in checkout_selectors:
                try:
                    checkout_btn = WebDriverWait(self.scraper.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not checkout_btn:
                # 嘗試前往購物車頁面
                self.scraper.driver.get(f"{self.config.amazon_base_url}/cart")
                
                # 再次尋找結帳按鈕
                checkout_btn = WebDriverWait(self.scraper.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="proceedToRetailCheckout"]'))
                )
            
            checkout_btn.click()
            
            # 等待結帳頁面載入
            WebDriverWait(self.scraper.driver, 15).until(
                lambda driver: "checkout" in driver.current_url.lower() or
                               "buy" in driver.current_url.lower()
            )
            
            logger.info("已前往結帳頁面")
            return True
            
        except Exception as e:
            logger.error(f"前往結帳失敗: {e}")
            return False
    
    def _complete_purchase(self) -> bool:
        """完成購買流程"""
        try:
            # 選擇配送地址（使用預設）
            if not self._select_shipping_address():
                logger.warning("選擇配送地址失敗，繼續嘗試")
            
            # 選擇配送方式（使用預設）
            if not self._select_shipping_method():
                logger.warning("選擇配送方式失敗，繼續嘗試")
            
            # 選擇付款方式（使用預設）
            if not self._select_payment_method():
                logger.warning("選擇付款方式失敗，繼續嘗試")
            
            # 檢查並下單
            return self._place_order()
            
        except Exception as e:
            logger.error(f"完成購買失敗: {e}")
            return False
    
    def _select_shipping_address(self) -> bool:
        """選擇配送地址"""
        try:
            # 尋找繼續按鈕或使用預設地址
            continue_selectors = [
                'input[name="continue"]',
                'button[name="continue"]',
                'input[value*="Continue"]',
                'input[value*="Use this address"]',
            ]
            
            for selector in continue_selectors:
                try:
                    btn = WebDriverWait(self.scraper.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    btn.click()
                    time.sleep(2)
                    return True
                except TimeoutException:
                    continue
            
            return True  # 可能已經選好地址
            
        except Exception as e:
            logger.error(f"選擇配送地址失敗: {e}")
            return False
    
    def _select_shipping_method(self) -> bool:
        """選擇配送方式"""
        try:
            # 尋找配送方式選項
            shipping_options = self.scraper.driver.find_elements(
                By.CSS_SELECTOR, 'input[name*="shipping"]'
            )
            
            if shipping_options:
                # 選擇第一個選項（通常是預設）
                shipping_options[0].click()
            
            # 尋找繼續按鈕
            continue_selectors = [
                'input[name="continue"]',
                'button[name="continue"]',
                'input[value*="Continue"]',
            ]
            
            for selector in continue_selectors:
                try:
                    btn = WebDriverWait(self.scraper.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    btn.click()
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"選擇配送方式失敗: {e}")
            return False
    
    def _select_payment_method(self) -> bool:
        """選擇付款方式"""
        try:
            # 尋找付款方式選項
            payment_options = self.scraper.driver.find_elements(
                By.CSS_SELECTOR, 'input[name*="payment"], input[name*="paymentMethod"]'
            )
            
            if payment_options:
                # 選擇第一個選項（通常是預設信用卡）
                payment_options[0].click()
            
            # 尋找繼續按鈕
            continue_selectors = [
                'input[name="continue"]',
                'button[name="continue"]',
                'input[value*="Continue"]',
                'input[value*="Use this payment method"]',
            ]
            
            for selector in continue_selectors:
                try:
                    btn = WebDriverWait(self.scraper.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    btn.click()
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"選擇付款方式失敗: {e}")
            return False
    
    def _place_order(self) -> bool:
        """下單"""
        try:
            # 尋找下單按鈕
            place_order_selectors = [
                'input[name="placeYourOrder1"]',
                'button[name="placeYourOrder1"]',
                'input[value*="Place your order"]',
                'button[id*="place-order"]',
                '#buy-now-button',
            ]
            
            place_order_btn = None
            for selector in place_order_selectors:
                try:
                    place_order_btn = WebDriverWait(self.scraper.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not place_order_btn:
                logger.error("找不到下單按鈕")
                return False
            
            # 最後確認 - 檢查價格和商品
            if not self._final_verification():
                logger.error("最終驗證失敗，取消下單")
                return False
            
            # 點擊下單
            logger.warning("即將下單 - 這將產生實際費用！")
            place_order_btn.click()
            
            # 等待訂單確認頁面
            WebDriverWait(self.scraper.driver, 30).until(
                lambda driver: "thank" in driver.current_url.lower() or
                               "order" in driver.current_url.lower() or
                               "confirmation" in driver.current_url.lower()
            )
            
            logger.info("訂單已成功提交")
            return True
            
        except Exception as e:
            logger.error(f"下單失敗: {e}")
            return False
    
    def _final_verification(self) -> bool:
        """最終購買確認"""
        try:
            # 檢查總價是否在預期範圍內
            price_elements = self.scraper.driver.find_elements(
                By.CSS_SELECTOR, 
                '.grand-total-price, .order-summary-total, #subtotals-marketplace-table .a-text-bold'
            )
            
            if price_elements and self.config.max_price:
                for elem in price_elements:
                    price_text = elem.text.strip()
                    # 提取價格數字
                    import re
                    price_match = re.search(r'\d+\.?\d*', price_text)
                    if price_match:
                        total_price = float(price_match.group())
                        if total_price > self.config.max_price:
                            logger.error(f"總價 ${total_price} 超過限制 ${self.config.max_price}")
                            return False
            
            return True
            
        except Exception as e:
            logger.warning(f"最終驗證時發生錯誤: {e}")
            return True  # 如果無法驗證，允許繼續
    
    def _record_purchase(self, product: Product):
        """記錄購買歷史
        
        Args:
            product: 購買的商品
        """
        purchase_record = {
            'timestamp': datetime.now().isoformat(),
            'asin': product.asin,
            'title': product.title,
            'price': product.price,
            'quantity': self.config.buy_quantity,
            'url': product.url,
        }
        
        self.purchase_history.append(purchase_record)
        
        # 儲存到檔案
        try:
            import json
            import os
            
            history_file = os.path.join(self.config.output_dir, "purchase_history.json")
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.purchase_history, f, ensure_ascii=False, indent=2)
                
            logger.info(f"購買記錄已儲存: {history_file}")
            
        except Exception as e:
            logger.error(f"儲存購買記錄失敗: {e}")
    
    def get_purchase_history(self) -> List[Dict]:
        """獲取購買歷史
        
        Returns:
            購買歷史列表
        """
        return self.purchase_history.copy()
    
    def dry_run_purchase(self, product: Product) -> Dict[str, any]:
        """模擬購買流程（不實際下單）
        
        Args:
            product: 要測試的商品
            
        Returns:
            測試結果
        """
        result = {
            'asin': product.asin,
            'can_purchase': False,
            'steps_completed': [],
            'errors': [],
            'total_time': 0,
        }
        
        start_time = time.time()
        
        try:
            # 檢查登入
            if self.ensure_login():
                result['steps_completed'].append('login')
            else:
                result['errors'].append('登入失敗')
                return result
            
            # 前往商品頁面
            self.scraper.driver.get(product.url)
            result['steps_completed'].append('navigate_to_product')
            
            # 檢查可用性
            if self._verify_product_availability():
                result['steps_completed'].append('verify_availability')
            else:
                result['errors'].append('商品無庫存')
                return result
            
            # 測試加入購物車
            if self._add_to_cart():
                result['steps_completed'].append('add_to_cart')
            else:
                result['errors'].append('無法加入購物車')
                return result
            
            # 測試前往結帳
            if self._proceed_to_checkout():
                result['steps_completed'].append('proceed_to_checkout')
                result['can_purchase'] = True
            else:
                result['errors'].append('無法前往結帳')
            
        except Exception as e:
            result['errors'].append(f'測試過程錯誤: {str(e)}')
        
        finally:
            result['total_time'] = time.time() - start_time
        
        return result