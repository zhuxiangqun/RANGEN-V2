"""
应用上下文中间件 - 可选启用，不影响现有系统

功能:
- 从请求中提取 App Key
- 认证应用
- 检查配额
- 注入应用上下文到 request.state

启用条件:
- PLATFORM_AVAILABLE = True (模块可导入)
- RANGEN_PLATFORM_ENABLED = "true" (环境变量)

默认状态: 禁用，不影响现有系统
"""

import os
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# 尝试导入平台组件
try:
    from src.platform.app.registry import get_app_registry
    from src.platform.quota.manager import get_quota_manager
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False


class AppContextMiddleware(BaseHTTPMiddleware):
    """
    应用上下文中间件 - 可选启用
    
    功能:
    1. 从请求中提取 API Key
    2. 认证应用
    3. 检查配额限制
    4. 注入应用上下文到 request.state
    
    使用方式:
    - 默认不启用 (RANGEN_PLATFORM_ENABLED != "true")
    - 启用后自动处理所有请求
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        如果平台功能未启用或无法导入，直接跳过
        """
        # 如果平台功能不可用或未启用，直接通过
        if not self._is_platform_enabled():
            return await call_next(request)
        
        # 1. 获取 App Key
        app_key = self._extract_app_key(request)
        
        if app_key:
            # 2. 认证应用
            app_registry = get_app_registry()
            app = app_registry.authenticate(app_key)
            
            if app:
                # 3. 检查配额
                quota_manager = get_quota_manager()
                allowed, reason = quota_manager.check_quota(app.app_id)
                
                if not allowed:
                    raise HTTPException(403, reason)
                
                # 4. 注入应用上下文
                request.state.app = app
                request.state.app_id = app.app_id
                request.state.namespace_id = app.namespace_id
                
                # 记录使用量 (延迟到响应后更好，这里简化处理)
                # 注意: 实际记录应该在响应后执行，避免阻塞
        
        response = await call_next(request)
        return response
    
    def _extract_app_key(self, request: Request) -> Optional[str]:
        """
        从请求中提取 App Key
        
        优先级:
        1. X-App-Key header
        2. Bearer token (如果以 sk_ 开头)
        3. X-API-Key header
        """
        # 方式1: X-App-Key header
        app_key = request.headers.get('X-App-Key')
        if app_key:
            return app_key
        
        # 方式2: Bearer token (sk_ 开头)
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            if token.startswith('sk_'):
                return token
        
        # 方式3: X-API-Key header
        return request.headers.get('X-API-Key')
    
    def _is_platform_enabled(self) -> bool:
        """检查平台功能是否启用"""
        return PLATFORM_AVAILABLE and os.getenv(
            "RANGEN_PLATFORM_ENABLED", "false"
        ).lower() == "true"


def is_platform_enabled() -> bool:
    """检查平台功能是否已启用"""
    return PLATFORM_AVAILABLE and os.getenv(
        "RANGEN_PLATFORM_ENABLED", "false"
    ).lower() == "true"
