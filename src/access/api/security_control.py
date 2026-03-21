"""
Security Control API - Outbound confirmation, whitelist, account protection
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field
from src.services.security_control import (
    get_security_controller,
    SecurityLevel,
    ConfirmationStatus
)

router = APIRouter(prefix="/api/v1/security", tags=["security"])


class OutboundCheckRequest(BaseModel):
    """外发检查请求"""
    destination: str = Field(..., description="目标地址")
    destination_type: str = Field(default="api", description="目标类型")
    content: str = Field(..., description="外发内容")


class OutboundConfirmRequest(BaseModel):
    """外发确认请求"""
    request_id: str
    approved: bool
    confirmed_by: str = Field(default="admin")


class WhitelistAddRequest(BaseModel):
    """添加白名单请求"""
    pattern: str
    pattern_type: str = Field(default="domain")
    description: str


class SecurityStatusResponse(BaseModel):
    """安全状态响应"""
    security_level: str
    pending_requests: int
    whitelist_entries: int
    api_key_protected: bool


@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status():
    """获取安全状态"""
    controller = get_security_controller()
    
    return controller.get_security_status()


@router.post("/level")
async def set_security_level(level: str):
    """设置安全级别"""
    controller = get_security_controller()
    controller.set_security_level(level)
    
    return {
        "security_level": level,
        "message": "Security level updated"
    }


@router.post("/outbound/check")
async def check_outbound(request: OutboundCheckRequest):
    """检查外发请求"""
    controller = get_security_controller()
    
    # 快速检查
    can_proceed, reason = controller.can_proceed(request.destination, request.content)
    
    # 创建正式请求
    outbound_request = controller.create_outbound_request(
        destination=request.destination,
        destination_type=request.destination_type,
        content=request.content
    )
    
    return {
        "request_id": outbound_request.request_id,
        "can_proceed": can_proceed,
        "reason": reason,
        "requires_confirmation": outbound_request.status == ConfirmationStatus.PENDING,
        "contains_sensitive": outbound_request.contains_sensitive,
        "sensitive_keywords": outbound_request.sensitive_keywords_found
    }


@router.post("/outbound/confirm")
async def confirm_outbound(request: OutboundConfirmRequest):
    """确认外发请求"""
    controller = get_security_controller()
    
    success = controller.confirm_outbound(
        request_id=request.request_id,
        approved=request.approved,
        confirmed_by=request.confirmed_by
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot confirm: request not found or expired"
        )
    
    status_info = controller.get_outbound_status(request.request_id)
    
    return {
        "request_id": request.request_id,
        "status": status_info.status.value,
        "confirmed_by": status_info.confirmed_by
    }


@router.get("/outbound/status/{request_id}")
async def get_outbound_status(request_id: str):
    """获取外发请求状态"""
    controller = get_security_controller()
    
    request = controller.get_outbound_status(request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request not found: {request_id}"
        )
    
    return {
        "request_id": request.request_id,
        "destination": request.destination,
        "destination_type": request.destination_type,
        "contains_sensitive": request.contains_sensitive,
        "status": request.status.value,
        "created_at": request.created_at.isoformat(),
        "expires_at": request.expires_at.isoformat() if request.expires_at else None
    }


@router.get("/whitelist")
async def get_whitelist():
    """获取白名单"""
    controller = get_security_controller()
    
    entries = controller.get_whitelist()
    
    return {
        "entries": [
            {
                "id": e.id,
                "pattern": e.pattern,
                "pattern_type": e.pattern_type,
                "description": e.description,
                "enabled": e.enabled
            }
            for e in entries
        ]
    }


@router.post("/whitelist/add")
async def add_whitelist(request: WhitelistAddRequest):
    """添加白名单"""
    controller = get_security_controller()
    
    entry = controller.add_whitelist(
        pattern=request.pattern,
        pattern_type=request.pattern_type,
        description=request.description
    )
    
    return {
        "id": entry.id,
        "pattern": entry.pattern,
        "message": "Whitelist entry added"
    }


@router.delete("/whitelist/{entry_id}")
async def remove_whitelist(entry_id: str):
    """移除白名单"""
    controller = get_security_controller()
    
    success = controller.remove_whitelist(entry_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whitelist entry not found: {entry_id}"
        )
    
    return {"message": "Whitelist entry removed"}


@router.post("/api-key/protect")
async def protect_api_key(api_key: str):
    """保护API密钥"""
    controller = get_security_controller()
    
    masked = controller.protect_api_key(api_key)
    
    return {
        "message": "API key protected",
        "masked": masked
    }


@router.post("/api-key/verify")
async def verify_api_key(api_key: str):
    """验证API密钥"""
    controller = get_security_controller()
    
    valid = controller.verify_api_key(api_key)
    
    return {
        "valid": valid
    }
