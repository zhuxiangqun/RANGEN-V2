"""
Cost Alert API - Email/Webhook notifications for budget thresholds
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field
from src.services.cost_alert import get_alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class AlertConfigRequest(BaseModel):
    """告警配置请求"""
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None


class WebhookRequest(BaseModel):
    """Webhook请求"""
    url: str


class EmailRequest(BaseModel):
    """邮件请求"""
    email: str


class SMTPRequest(BaseModel):
    """SMTP配置请求"""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True


class AlertCheckRequest(BaseModel):
    """告警检查请求"""
    current_cost: float
    period: str = "daily"


@router.get("/config")
async def get_alert_config():
    """获取告警配置"""
    service = get_alert_service()
    return service.get_config()


@router.post("/config")
async def configure_alert(request: AlertConfigRequest):
    """配置告警阈值"""
    service = get_alert_service()
    
    service.configure(
        daily_limit=request.daily_limit,
        weekly_limit=request.weekly_limit,
        monthly_limit=request.monthly_limit,
        warning_threshold=request.warning_threshold,
        critical_threshold=request.critical_threshold
    )
    
    return {
        "message": "Alert configuration updated",
        "config": service.get_config()
    }


@router.post("/webhooks/add")
async def add_webhook(request: WebhookRequest):
    """添加Webhook URL"""
    service = get_alert_service()
    
    service.add_webhook(request.url)
    
    return {
        "message": "Webhook added",
        "url": request.url
    }


@router.delete("/webhooks")
async def remove_webhook(url: str):
    """移除Webhook URL"""
    service = get_alert_service()
    
    service.remove_webhook(url)
    
    return {"message": "Webhook removed"}


@router.post("/emails/add")
async def add_email_recipient(request: EmailRequest):
    """添加邮件接收者"""
    service = get_alert_service()
    
    service.add_email_recipient(request.email)
    
    return {
        "message": "Email recipient added",
        "email": request.email
    }


@router.delete("/emails")
async def remove_email_recipient(email: str):
    """移除邮件接收者"""
    service = get_alert_service()
    
    service.remove_email_recipient(email)
    
    return {"message": "Email recipient removed"}


@router.post("/smtp")
async def configure_smtp(request: SMTPRequest):
    """配置SMTP"""
    service = get_alert_service()
    
    service.configure_smtp(
        host=request.host,
        port=request.port,
        username=request.username,
        password=request.password,
        use_tls=request.use_tls
    )
    
    return {"message": "SMTP configured"}


@router.post("/check")
async def check_and_alert(request: AlertCheckRequest):
    """检查并触发告警"""
    service = get_alert_service()
    
    alerts = service.check_and_alert(
        current_cost=request.current_cost,
        period=request.period
    )
    
    if alerts:
        return {
            "alert_triggered": True,
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "level": "CRITICAL" if a.percentage >= 0.95 else "WARNING",
                    "message": a.message
                }
                for a in alerts
            ]
        }
    
    return {"alert_triggered": False}


@router.get("/history")
async def get_alert_history(limit: int = 10):
    """获取告警历史"""
    service = get_alert_service()
    
    alerts = service.get_alerts(limit)
    
    return {
        "alerts": [
            {
                "alert_id": a.alert_id,
                "type": a.alert_type.value,
                "message": a.message,
                "current": a.current,
                "threshold": a.threshold,
                "percentage": a.percentage,
                "sent": a.sent,
                "timestamp": a.timestamp.isoformat()
            }
            for a in alerts
        ]
    }
