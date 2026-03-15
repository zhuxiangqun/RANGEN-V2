"""
Cost Alert Service - Email/Webhook notifications for budget thresholds
"""
import os
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Thread

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class AlertType(str, Enum):
    """告警类型"""
    DAILY_LIMIT = "daily_limit"      # 每日限额
    WEEKLY_LIMIT = "weekly_limit"    # 每周限额
    MONTHLY_LIMIT = "monthly_limit"  # 每月限额
    SINGLE_REQUEST = "single_request" # 单次请求
    ANOMALY = "anomaly"              # 异常使用


class NotificationChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class AlertConfig:
    """告警配置"""
    enabled: bool = True
    daily_limit: float = 100.0        # 每日限额(美元)
    weekly_limit: float = 500.0      # 每周限额
    monthly_limit: float = 2000.0    # 每月限额
    warning_threshold: float = 0.8    # 警告阈值(80%)
    critical_threshold: float = 0.95 # 严重阈值(95%)


@dataclass
class AlertRecord:
    """告警记录"""
    alert_id: str
    alert_type: AlertType
    channel: NotificationChannel
    threshold: float
    current: float
    percentage: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    sent: bool = False


class CostAlertService:
    """成本告警服务"""
    
    def __init__(self):
        self._config = AlertConfig()
        self._alerts: List[AlertRecord] = []
        self._webhook_urls: List[str] = []
        self._email_recipients: List[str] = []
        self._smtp_config: Optional[Dict[str, str]] = None
    
    def configure(
        self,
        daily_limit: Optional[float] = None,
        weekly_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None
    ):
        """配置告警阈值"""
        if daily_limit is not None:
            self._config.daily_limit = daily_limit
        if weekly_limit is not None:
            self._config.weekly_limit = weekly_limit
        if monthly_limit is not None:
            self._config.monthly_limit = monthly_limit
        if warning_threshold is not None:
            self._config.warning_threshold = warning_threshold
        if critical_threshold is not None:
            self._config.critical_threshold = critical_threshold
        
        logger.info(f"Alert config updated: daily=${daily_limit}, weekly=${weekly_limit}, monthly=${monthly_limit}")
    
    def add_webhook(self, url: str):
        """添加Webhook URL"""
        if url not in self._webhook_urls:
            self._webhook_urls.append(url)
            logger.info(f"Webhook added: {url}")
    
    def remove_webhook(self, url: str):
        """移除Webhook URL"""
        if url in self._webhook_urls:
            self._webhook_urls.remove(url)
    
    def add_email_recipient(self, email: str):
        """添加邮件接收者"""
        if email not in self._email_recipients:
            self._email_recipients.append(email)
            logger.info(f"Email recipient added: {email}")
    
    def remove_email_recipient(self, email: str):
        """移除邮件接收者"""
        if email in self._email_recipients:
            self._email_recipients.remove(email)
    
    def configure_smtp(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True
    ):
        """配置SMTP"""
        self._smtp_config = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "use_tls": use_tls
        }
        logger.info("SMTP configured")
    
    def check_and_alert(
        self,
        current_cost: float,
        period: str = "daily"
    ) -> List[AlertRecord]:
        """检查并发送告警"""
        alerts = []
        
        # 确定阈值
        if period == "daily":
            threshold = self._config.daily_limit
            alert_type = AlertType.DAILY_LIMIT
        elif period == "weekly":
            threshold = self._config.weekly_limit
            alert_type = AlertType.WEEKLY_LIMIT
        else:
            threshold = self._config.monthly_limit
            alert_type = AlertType.MONTHLY_LIMIT
        
        # 计算百分比
        percentage = current_cost / threshold if threshold > 0 else 0
        
        # 检查是否需要告警
        if percentage >= self._config.critical_threshold:
            level = "CRITICAL"
            message = f"🚨 成本告警: {period}费用 ${current_cost:.2f} 已超过 {threshold:.2f} 的 {percentage*100:.1f}%"
        elif percentage >= self._config.warning_threshold:
            level = "WARNING"
            message = f"⚠️ 成本提醒: {period}费用 ${current_cost:.2f} 已达到 {threshold:.2f} 的 {percentage*100:.1f}%"
        else:
            return alerts  # 不需要告警
        
        # 创建告警记录
        alert_id = f"alert_{int(time.time())}"
        alert = AlertRecord(
            alert_id=alert_id,
            alert_type=alert_type,
            channel=NotificationChannel.EMAIL,  # 默认
            threshold=threshold,
            current=current_cost,
            percentage=percentage,
            message=message
        )
        
        self._alerts.append(alert)
        
        # 异步发送通知
        Thread(target=self._send_notifications, args=(alert, level)).start()
        
        return [alert]
    
    def _send_notifications(self, alert: AlertRecord, level: str):
        """发送通知"""
        # 发送Webhook
        for url in self._webhook_urls:
            self._send_webhook(url, alert, level)
        
        # 发送邮件
        for email in self._email_recipients:
            self._send_email(email, alert, level)
        
        alert.sent = True
        logger.info(f"Alert sent: {alert.alert_id}, level: {level}")
    
    def _send_webhook(self, url: str, alert: AlertRecord, level: str):
        """发送Webhook通知"""
        try:
            import urllib.request
            import urllib.parse
            
            payload = {
                "alert_id": alert.alert_id,
                "level": level,
                "type": alert.alert_type.value,
                "message": alert.message,
                "current_cost": alert.current,
                "threshold": alert.threshold,
                "percentage": alert.percentage,
                "timestamp": alert.timestamp.isoformat()
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                logger.info(f"Webhook sent successfully: {url}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    def _send_email(self, recipient: str, alert: AlertRecord, level: str):
        """发送邮件通知"""
        if not self._smtp_config:
            logger.warning("SMTP not configured, skipping email")
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{level}] AI中台成本告警"
            msg['From'] = self._smtp_config['username']
            msg['To'] = recipient
            
            html_content = f"""
            <html>
            <body>
                <h2>{level} - 成本告警</h2>
                <p>{alert.message}</p>
                <table>
                    <tr><td>当前费用:</td><td>${alert.current:.2f}</td></tr>
                    <tr><td>阈值:</td><td>${alert.threshold:.2f}</td></tr>
                    <tr><td>使用率:</td><td>{alert.percentage*100:.1f}%</td></tr>
                    <tr><td>时间:</td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                </table>
            </body>
            </html>
            """
            
            part = MIMEText(html_content, 'html')
            msg.attach(part)
            
            # 发送邮件
            with smtplib.SMTP(
                self._smtp_config['host'],
                self._smtp_config['port']
            ) as server:
                if self._smtp_config.get('use_tls'):
                    server.starttls()
                server.login(
                    self._smtp_config['username'],
                    self._smtp_config['password']
                )
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def get_alerts(self, limit: int = 10) -> List[AlertRecord]:
        """获取告警记录"""
        return sorted(self._alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_config(self) -> Dict[str, Any]:
        """获取告警配置"""
        return {
            "enabled": self._config.enabled,
            "daily_limit": self._config.daily_limit,
            "weekly_limit": self._config.weekly_limit,
            "monthly_limit": self._config.monthly_limit,
            "warning_threshold": self._config.warning_threshold,
            "critical_threshold": self._config.critical_threshold,
            "webhook_count": len(self._webhook_urls),
            "email_recipients": len(self._email_recipients)
        }


# Global instance
_alert_service: Optional[CostAlertService] = None


def get_alert_service() -> CostAlertService:
    """获取告警服务实例"""
    global _alert_service
    if _alert_service is None:
        _alert_service = CostAlertService()
    return _alert_service
