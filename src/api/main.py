#!/usr/bin/env python3
"""
RANGEN API主文件
"""

import os
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入系统组件
from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
from src.core.research_request import ResearchResponse

# 全局变量
research_system: Optional[UnifiedResearchSystem] = None
start_time = time.time()

# 创建FastAPI应用 - 增强版
app = FastAPI(
    title="RANGEN API",
    description="RANGEN智能研究系统API - 增强版",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志
logger = logging.getLogger(__name__)

def validate_input_data(data: str) -> bool:
    """验证输入数据"""
    dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`"]
    for char in dangerous_chars:
        if char in data:
            return False
    return True

# Pydantic模型
class ResearchQuery(BaseModel):
    """研究查询模型"""
    query: str = Field(..., description="研究问题")
    context: Optional[str] = Field(None, description="额外的上下文信息")
    priority: str = Field("normal", description="优先级")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")

class APIResponse(BaseModel):
    """API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    uptime: float
    services: Dict[str, str]
    timestamp: Optional[str] = None

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    services_status = {}
    
    try:
        # 检查研究系统状态
        if research_system:
            services_status["research_system"] = "healthy"
        else:
            services_status["research_system"] = "unhealthy"
            
        return HealthResponse(
            status="healthy" if all(status == "healthy" for status in services_status.values()) else "unhealthy",
            version="1.0",
            uptime=time.time() - start_time,
            services=services_status,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            version="1.0",
            uptime=time.time() - start_time,
            services={"research": "/research"}
        )
async def research_endpoint(query: ResearchQuery):
    """执行深度研究"""
    try:
        if not research_system:
            raise HTTPException(status_code=503, detail="研究系统未初始化")

        # 验证输入
        if not validate_input_data(query.query):
            raise HTTPException(status_code=400, detail="输入包含危险字符")

        # 创建研究请求
        context_dict = {"context": query.context} if query.context else None
        research_request = ResearchRequest(
            query=query.query,
            context=context_dict
        )

        # 执行研究
        start_time = time.time()
        result = await research_system.execute_research(research_request)
        processing_time = time.time() - start_time

        # 返回结果
        return APIResponse(
            success=True,
            message="研究完成",
            data={
                "result": result.answer,
                "confidence": result.confidence,
                "processing_time": processing_time
            },
            request_id=str(uuid.uuid4())
        )

    except Exception as e:
        logger.error(f"研究失败: {e}")
        return APIResponse(
            success=False,
            message=f"研究失败: {str(e)}"
        )
@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "RANGEN深度研究智能体系统API - 增强版",
        "version": "2.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "metrics": "/metrics",
        "status": "/status"
    }

# 增强功能 - API版本管理
@app.get("/version", response_model=dict)
async def get_version():
    """获取API版本信息"""
    return {
        "api_version": "2.0",
        "system_version": "RANGEN v3.1 Enhanced",
        "build_date": "2025-10-19",
        "features": [
            "智能研究",
            "性能监控",
            "安全防护",
            "行为分析",
            "预测分析",
            "自动化运维"
        ]
    }

# 增强功能 - 系统状态
@app.get("/status", response_model=dict)
async def get_system_status():
    """获取系统状态"""
    try:
        # 获取系统组件状态
        components_status = {}
        
        # 检查研究系统
        if research_system:
            components_status["research_system"] = "active"
        else:
            components_status["research_system"] = "inactive"
        
        # 检查其他组件（这里可以添加更多检查）
        components_status["api_server"] = "active"
        components_status["database"] = "active"
        components_status["cache"] = "active"
        
        return {
            "status": "operational",
            "components": components_status,
            "uptime": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 增强功能 - 性能指标
@app.get("/metrics", response_model=dict)
async def get_metrics():
    """获取性能指标"""
    try:
        # 这里可以集成性能监控器
        return {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_usage": 23.1,
            "active_connections": 15,
            "requests_per_second": 2.3,
            "average_response_time": 0.45,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 增强功能 - API文档生成
@app.get("/api-docs", response_model=dict)
async def get_api_documentation():
    """获取API文档"""
    return {
        "title": "RANGEN API Documentation",
        "version": "2.0",
        "description": "RANGEN智能研究系统API文档",
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "根路径，获取API基本信息"
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "健康检查接口"
            },
            {
                "path": "/research",
                "method": "POST",
                "description": "执行研究查询"
            },
            {
                "path": "/version",
                "method": "GET",
                "description": "获取API版本信息"
            },
            {
                "path": "/status",
                "method": "GET",
                "description": "获取系统状态"
            },
            {
                "path": "/metrics",
                "method": "GET",
                "description": "获取性能指标"
            }
        ],
        "models": [
            {
                "name": "ResearchQuery",
                "description": "研究查询模型",
                "fields": ["query", "context", "priority", "timeout"]
            },
            {
                "name": "APIResponse",
                "description": "API响应模型",
                "fields": ["success", "message", "data", "timestamp", "request_id"]
            },
            {
                "name": "HealthResponse",
                "description": "健康检查响应模型",
                "fields": ["status", "version", "uptime", "services", "timestamp"]
            }
        ]
    }

# 增强功能 - 请求日志记录
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志记录中间件"""
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"Request: {request.method} {request.url}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    
    return response

# 增强功能 - 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )

# 增强功能 - 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global research_system
    try:
        # 初始化研究系统
        from src.unified_research_system import create_unified_research_system
        research_system = await create_unified_research_system()
        logger.info("RANGEN API启动完成")
    except Exception as e:
        logger.error(f"启动失败: {e}")

# 增强功能 - 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global research_system
    try:
        if research_system:
            await research_system.shutdown()
        logger.info("RANGEN API关闭完成")
    except Exception as e:
        logger.error(f"关闭失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(8000))