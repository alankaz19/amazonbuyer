"""通知系統"""

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger

from models.product import Product


class EmailNotifier:
    """電子郵件通知器"""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 username: str, password: str, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_notification(self, to_emails: List[str], subject: str, 
                         message: str, attachments: Optional[List[str]] = None):
        """發送通知郵件
        
        Args:
            to_emails: 收件人列表
            subject: 郵件主題
            message: 郵件內容
            attachments: 附件檔案路徑列表
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # 添加郵件內容
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        
                        import os
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        
                        msg.attach(part)
                        
                    except Exception as e:
                        logger.error(f"添加附件失敗 {file_path}: {e}")
            
            # 發送郵件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"郵件通知已發送給 {', '.join(to_emails)}")
            
        except Exception as e:
            logger.error(f"發送郵件失敗: {e}")
    
    def send_product_alert(self, product: Product, to_emails: List[str], 
                          alert_type: str = "available"):
        """發送商品警報
        
        Args:
            product: 商品資訊
            to_emails: 收件人列表
            alert_type: 警報類型 (available, price_drop, back_in_stock)
        """
        alert_messages = {
            'available': f"商品 {product.title} 現在有庫存！",
            'price_drop': f"商品 {product.title} 價格下降了！",
            'back_in_stock': f"商品 {product.title} 重新有庫存！",
        }
        
        subject = f"Amazon 商品警報 - {alert_messages.get(alert_type, '狀態更新')}"
        
        message = f"""
商品警報通知

商品名稱: {product.title}
商品 ASIN: {product.asin}
當前價格: ${product.price:.2f} {product.currency}
庫存狀態: {product.availability}
商品連結: {product.url}

警報類型: {alert_type}
通知時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

這是自動生成的通知郵件，請勿直接回覆。
        """
        
        self.send_notification(to_emails, subject, message)


class WebhookNotifier:
    """Webhook 通知器"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    def send_notification(self, data: Dict):
        """發送 Webhook 通知
        
        Args:
            data: 要發送的資料
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Webhook 通知發送成功")
            else:
                logger.error(f"Webhook 通知失敗，狀態碼: {response.status_code}")
                
        except Exception as e:
            logger.error(f"發送 Webhook 通知失敗: {e}")
    
    def send_product_alert(self, product: Product, alert_type: str = "available"):
        """發送商品警報
        
        Args:
            product: 商品資訊
            alert_type: 警報類型
        """
        data = {
            'type': 'product_alert',
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'product': {
                'asin': product.asin,
                'title': product.title,
                'price': product.price,
                'currency': product.currency,
                'availability': product.availability,
                'url': product.url,
            }
        }
        
        self.send_notification(data)


class SlackNotifier:
    """Slack 通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_notification(self, message: str, channel: Optional[str] = None,
                         username: Optional[str] = None):
        """發送 Slack 通知
        
        Args:
            message: 訊息內容
            channel: 頻道名稱
            username: 發送者名稱
        """
        try:
            payload = {
                'text': message,
            }
            
            if channel:
                payload['channel'] = channel
            
            if username:
                payload['username'] = username
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack 通知發送成功")
            else:
                logger.error(f"Slack 通知失敗，狀態碼: {response.status_code}")
                
        except Exception as e:
            logger.error(f"發送 Slack 通知失敗: {e}")
    
    def send_product_alert(self, product: Product, alert_type: str = "available"):
        """發送商品警報到 Slack
        
        Args:
            product: 商品資訊
            alert_type: 警報類型
        """
        emoji_map = {
            'available': '🛒',
            'price_drop': '💰',
            'back_in_stock': '📦',
        }
        
        emoji = emoji_map.get(alert_type, '📢')
        
        message = f"""{emoji} *Amazon 商品警報*

*商品名稱:* {product.title}
*ASIN:* `{product.asin}`
*價格:* ${product.price:.2f} {product.currency}
*庫存:* {product.availability}
*連結:* <{product.url}|查看商品>

*警報類型:* {alert_type}
*時間:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_notification(message, username="Amazon Bot")


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifiers = []
    
    def add_email_notifier(self, smtp_server: str, smtp_port: int,
                          username: str, password: str, use_tls: bool = True):
        """添加電子郵件通知器"""
        notifier = EmailNotifier(smtp_server, smtp_port, username, password, use_tls)
        self.notifiers.append(('email', notifier))
        logger.info("已添加電子郵件通知器")
    
    def add_webhook_notifier(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        """添加 Webhook 通知器"""
        notifier = WebhookNotifier(webhook_url, headers)
        self.notifiers.append(('webhook', notifier))
        logger.info("已添加 Webhook 通知器")
    
    def add_slack_notifier(self, webhook_url: str):
        """添加 Slack 通知器"""
        notifier = SlackNotifier(webhook_url)
        self.notifiers.append(('slack', notifier))
        logger.info("已添加 Slack 通知器")
    
    def send_product_alert(self, product: Product, alert_type: str = "available",
                          email_recipients: Optional[List[str]] = None):
        """發送商品警報到所有通知器
        
        Args:
            product: 商品資訊
            alert_type: 警報類型
            email_recipients: 電子郵件收件人（僅用於電子郵件通知器）
        """
        for notifier_type, notifier in self.notifiers:
            try:
                if notifier_type == 'email' and email_recipients:
                    notifier.send_product_alert(product, email_recipients, alert_type)
                else:
                    notifier.send_product_alert(product, alert_type)
                    
            except Exception as e:
                logger.error(f"{notifier_type} 通知發送失敗: {e}")
    
    def send_daily_summary(self, products: List[Product], 
                          email_recipients: Optional[List[str]] = None):
        """發送每日摘要
        
        Args:
            products: 商品列表
            email_recipients: 電子郵件收件人
        """
        available_count = sum(1 for p in products if p.is_available())
        
        summary = f"""📊 Amazon 監控每日摘要

監控商品總數: {len(products)}
有庫存商品: {available_count}
無庫存商品: {len(products) - available_count}

報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        for notifier_type, notifier in self.notifiers:
            try:
                if notifier_type == 'email' and email_recipients:
                    notifier.send_notification(
                        email_recipients,
                        "Amazon 監控每日摘要",
                        summary
                    )
                elif notifier_type == 'slack':
                    notifier.send_notification(summary)
                elif notifier_type == 'webhook':
                    data = {
                        'type': 'daily_summary',
                        'timestamp': datetime.now().isoformat(),
                        'summary': {
                            'total_products': len(products),
                            'available_products': available_count,
                            'unavailable_products': len(products) - available_count,
                        }
                    }
                    notifier.send_notification(data)
                    
            except Exception as e:
                logger.error(f"{notifier_type} 每日摘要發送失敗: {e}")