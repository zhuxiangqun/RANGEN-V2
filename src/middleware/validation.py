"""
输入验证中间件
为FastAPI提供统一的输入验证中间件
"""
import json
from typing import Dict, Any, Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from src.utils.input_validator import InputValidator, ValidationLevel, ValidationResult, get_validator
from src.utils.output_encoder import get_output_encoder, ContextType
from src.services.logging_service import get_logger
from src.services.audit_log_service import (
    AuditEventType, AuditSeverity, AuditSource, 
    log_security_alert
)

logger = get_logger("validation_middleware")

class InputValidationMiddleware(BaseHTTPMiddleware):
    """输入验证中间件"""
    
    def __init__(self, app, validation_level: ValidationLevel = ValidationLevel.MODERATE, enable_output_encoding: bool = True):
        super().__init__(app)
        self.validator = get_validator(validation_level)
        self.enable_output_encoding = enable_output_encoding
        self.output_encoder = get_output_encoder() if enable_output_encoding else None
        self._setup_endpoint_configs()
        logger.info(f"Input validation middleware initialized with level: {validation_level.value}, output encoding: {enable_output_encoding}")
    
    def _setup_endpoint_configs(self):
        """设置各端点的验证配置"""
        self.endpoint_configs = {
            # POST请求需要验证请求体
            "/chat": {
                "methods": ["POST"],
                "validate_body": True,
                "validate_query": True,
                "validation_level": ValidationLevel.MODERATE
            },
            "/auth/api-key": {
                "methods": ["POST"],
                "validate_query": True,  # 验证路径参数和查询参数
                "validation_level": ValidationLevel.MODERATE
            },
            
            # GET请求需要验证查询参数
            "/health": {
                "methods": ["GET"],
                "validate_query": True,
                "validation_level": ValidationLevel.LENIENT
            },
            "/health/auth": {
                "methods": ["GET"],
                "validate_query": True,
                "validation_level": ValidationLevel.LENIENT
            },
            "/diag": {
                "methods": ["GET"],
                "validate_query": True,
                "validation_level": ValidationLevel.MODERATE
            },
            "/auth/info": {
                "methods": ["GET"],
                "validate_query": True,
                "validation_level": ValidationLevel.LENIENT
            },
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """中间件主处理函数"""
        path = request.url.path
        method = request.method
        
        # 获取端点配置
        endpoint_config = self.endpoint_configs.get(path, {})
        
        # 检查是否需要验证此端点
        if method not in endpoint_config.get("methods", []):
            # 不需要验证，直接通过
            return await call_next(request)
        
        try:
            # 验证查询参数
            if endpoint_config.get("validate_query", False):
                await self._validate_query_params(request)
            
            # 验证请求体（仅对POST/PUT请求）
            if endpoint_config.get("validate_body", False) and method in ["POST", "PUT"]:
                request = await self._validate_request_body(request, path)
            
            # 继续处理请求
            response = await call_next(request)
            
            # 输出编码
            if self.enable_output_encoding:
                encoded_response = self._encode_response(response)
                if encoded_response:
                    response = encoded_response
            
            return response
            
        except HTTPException as e:
            # 返回HTTP异常
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "validation_error",
                    "message": e.detail,
                    "type": "input_validation_failed"
                }
            )
        except Exception as e:
            # 记录未预期的错误
            logger.error(f"验证中间件发生错误: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error", 
                    "message": "服务器内部错误",
                    "type": "validation_middleware_error"
                }
            )
    
    async def _validate_query_params(self, request: Request):
        """验证查询参数"""
        # 获取查询参数
        query_params = dict(request.query_params)
        
        # 验证参数
        validator = get_validator(self.endpoint_configs.get(request.url.path, {}).get("validation_level", ValidationLevel.MODERATE))
        result = validator.validate_query_params(query_params, request.url.path)
        
        if not result.is_valid:
            logger.warning(f"查询参数验证失败: {result.error_message}")
            
            # 记录安全事件
            ip_address = request.client.host if request.client else None
            log_security_alert(
                message=f"恶意查询参数检测: {result.error_message}",
                severity=AuditSeverity.WARNING,
                ip_address=ip_address,
                context={
                    "path": request.url.path,
                    "method": request.method,
                    "error_message": result.error_message,
                    "threat_type": result.threat_type.value if result.threat_type else "unknown",
                    "query_params": dict(request.query_params)
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"查询参数验证失败: {result.error_message}"
            )
        
        # 将验证后的参数重新设置到请求中
        # 注意：这里我们无法直接修改request.query_params，
        # 但可以在请求属性中存储验证后的参数
        request.state.validated_query_params = result.sanitized_value
    
    async def _validate_request_body(self, request: Request, path: str) -> Request:
        """验证请求体"""
        try:
            # 读取请求体
            body_bytes = await request.body()
            
            # 如果请求体为空且不需要，直接返回
            if not body_bytes:
                return request
            
            # 解析JSON
            try:
                body_data = json.loads(body_bytes.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"请求体JSON格式错误: {str(e)}"
                )
            
            # 验证请求体
            validator = get_validator(self.endpoint_configs.get(path, {}).get("validation_level", ValidationLevel.MODERATE))
            result = validator.validate_request_body(body_data, path)
            
            if not result.is_valid:
                logger.warning(f"请求体验证失败: {result.error_message}")
                
                # 记录安全事件
                ip_address = request.client.host if request.client else None
                log_security_alert(
                    message=f"恶意请求体检测: {result.error_message}",
                    severity=AuditSeverity.WARNING,
                    ip_address=ip_address,
                    context={
                        "path": request.url.path,
                        "method": request.method,
                        "error_message": result.error_message,
                        "threat_type": result.threat_type.value if result.threat_type else "unknown",
                        "body_preview": str(body_data)[:500]  # 限制预览长度
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"请求体验证失败: {result.error_message}"
                )
            
            # 将验证后的请求体存储在请求状态中
            request.state.validated_body = result.sanitized_value
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"请求体验证过程中发生错误: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"请求体验证错误: {str(e)}"
            )
    
    def _encode_response(self, response: Response) -> Optional[Response]:
        """编码响应内容"""
        if not self.enable_output_encoding or not self.output_encoder:
            return None
        
        # Skip StreamingResponse (it does not have body attribute)
        if not hasattr(response, 'body'):
            return None
        
        try:
            # 只处理JSON响应
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return None
            
            # 获取响应体
            body = response.body
            if not body:
                return None
            
            # 解码JSON
            try:
                body_str = body.decode("utf-8")
                data = json.loads(body_str)
            except (UnicodeDecodeError, json.JSONDecodeError):
                # 如果不是有效的JSON，跳过编码
                return None
            
            # 对响应数据进行编码
            encoded_data = self.output_encoder.encode_json(data)
            
            # 创建新的响应
            encoded_response = Response(
                content=encoded_data,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            logger.debug(f"响应已编码，原始大小: {len(body_str)}, 编码后大小: {len(encoded_data)}")
            return encoded_response
            
        except Exception as e:
            logger.error(f"响应编码失败: {e}")
            return None

class RateLimitValidationMiddleware(BaseHTTPMiddleware):
    """速率限制验证中间件（可选）"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # 简单的内存存储，生产环境应使用Redis等
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """速率限制检查"""
        # 获取客户端标识（IP地址或API密钥）
        client_id = await self._get_client_id(request)
        
        # 检查速率限制
        if not await self._check_rate_limit(client_id):
            logger.warning(f"客户端 {client_id} 超过速率限制")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"请求过于频繁，请在{self.window_seconds}秒后重试",
                    "type": "rate_limit_error"
                }
            )
        
        # 继续处理请求
        return await call_next(request)
    
    async def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 尝试从Authorization头获取API密钥
        auth_header = request.headers.get("authorization")
        if auth_header:
            # 提取API密钥或令牌
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if token.startswith("rang_"):
                    return f"api_key:{token[:20]}"  # 使用API密钥前缀
                else:
                    return f"jwt:{token[:20]}"  # 使用JWT令牌前缀
        
        # 回退到IP地址
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """检查速率限制"""
        import time
        
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 获取或创建客户端记录
        if client_id not in self.request_counts:
            self.request_counts[client_id] = []
        
        client_requests = self.request_counts[client_id]
        
        # 移除超出时间窗口的请求
        window_start = current_time - self.window_seconds
        client_requests = [req_time for req_time in client_requests if req_time > window_start]
        
        # 检查是否超过限制
        if len(client_requests) >= self.max_requests:
            return False
        
        # 记录当前请求
        client_requests.append(current_time)
        self.request_counts[client_id] = client_requests
        
        return True
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期的速率限制记录"""
        cutoff_time = current_time - self.window_seconds
        
        # 清理每个客户端的过期记录
        for client_id in list(self.request_counts.keys()):
            client_requests = self.request_counts[client_id]
            valid_requests = [req_time for req_time in client_requests if req_time > cutoff_time]
            
            if not valid_requests:
                # 如果没有有效请求，删除客户端记录
                del self.request_counts[client_id]
            else:
                # 更新有效请求列表
                self.request_counts[client_id] = valid_requests

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """添加安全头"""
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP: 对 /docs 和 /redoc 允许外部资源
        path = request.url.path
        if path in ["/docs", "/redoc", "/openapi.json"]:
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://fastapi.tiangolo.com data:"
        else:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

def create_validation_middleware(app, validation_level: ValidationLevel = ValidationLevel.MODERATE):
    """创建验证中间件的便捷函数"""
    return InputValidationMiddleware(app, validation_level)

def create_rate_limit_middleware(app, max_requests: int = 100, window_seconds: int = 60):
    """创建速率限制中间件的便捷函数"""
    return RateLimitValidationMiddleware(app, max_requests, window_seconds)

def create_security_headers_middleware(app):
    """创建安全头中间件的便捷函数"""
    return SecurityHeadersMiddleware(app)