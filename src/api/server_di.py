#!/usr/bin/env python3
"""
RANGEN API Server - 依赖注入版本
使用统一的依赖注入系统，减少模块间耦合
"""

import time
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from contextlib import asynccontextmanager
from typing import Optional

# 依赖注入系统
from src.di.bootstrap import bootstrap_application_async, get_service, get_service_async
from src.di.unified_container import UnifiedDIContainer

# 服务接口
from src.core.interfaces import IConfigurationService, ILoggingService
from src.core.execution_coordinator import ExecutionCoordinator
from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter

# 工具和服务
from src.agents.tools.tool_registry import ToolRegistry
from src.agents.tools.retrieval_tool import RetrievalTool

# 模型和认证
from src.api.models import ChatRequest, ChatResponse
from src.api.auth import verify_api_key_auth, require_read, require_write, require_admin, register_api_key, AuthService
from src.middleware.validation import create_validation_middleware, create_security_headers_middleware, create_rate_limit_middleware
from src.utils.input_validator import ValidationLevel

# 全局容器和引导程序引用
_container: Optional[UnifiedDIContainer] = None
_bootstrap = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（使用依赖注入）"""
    global _container, _bootstrap
    
    logger = None
    try:
        # 1. 初始化依赖注入系统
        from src.di.bootstrap import bootstrap_application_async
        _bootstrap = await bootstrap_application_async()
        _container = _bootstrap.get_container()
        
        # 2. 获取日志服务
        logger = await get_service_async(ILoggingService)
        logger.info("初始化RANGEN系统（依赖注入版本）...")
        
        # 3. 初始化认证系统
        logger.info("初始化认证系统...")
        if os.getenv("RANGEN_API_KEY"):
            logger.info("默认API密钥已通过环境变量配置")
        else:
            logger.warning("未配置默认API密钥。请设置RANGEN_API_KEY环境变量。")
        
        # 4. 获取核心服务（通过依赖注入）
        context_manager = await get_service_async(ContextManager)
        router = await get_service_async(ConfigurableRouter)
        tool_registry = await get_service_async(ToolRegistry)
        
        # 5. 注册检索工具
        try:
            retrieval_tool = RetrievalTool()
            tool_registry.register_tool(retrieval_tool)
            logger.info("检索工具注册成功")
        except Exception as e:
            logger.error(f"检索工具初始化失败: {e}")
        
        # 6. 获取执行协调器
        coordinator = await get_service_async(ExecutionCoordinator)
        
        # 7. 存储协调器引用到应用状态
        app.state.coordinator = coordinator
        app.state.container = _container
        app.state.bootstrap = _bootstrap
        
        logger.info("RANGEN系统（依赖注入版本）初始化完成")
        
        yield
        
        # 8. 关闭逻辑
        logger.info("正在关闭系统...")
        
    except Exception as e:
        if logger:
            logger.error(f"系统初始化失败: {e}")
        raise
    finally:
        if logger:
            logger.info("系统关闭完成")


app = FastAPI(
    title="RANGEN API (DI)", 
    version="2.0.0", 
    lifespan=lifespan,
    description="RANGEN多智能体研究系统API（依赖注入版本）",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加中间件
app.add_middleware(create_validation_middleware, validation_level=ValidationLevel.MODERATE)
app.add_middleware(create_security_headers_middleware)
app.add_middleware(create_rate_limit_middleware, max_requests=200, window_seconds=60)


# 依赖函数
async def get_coordinator() -> ExecutionCoordinator:
    """获取执行协调器（依赖注入）"""
    if not hasattr(app.state, 'coordinator') or app.state.coordinator is None:
        try:
            coordinator = await get_service_async(ExecutionCoordinator)
            app.state.coordinator = coordinator
            return coordinator
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"系统未初始化: {str(e)}")
    return app.state.coordinator


async def get_auth_service() -> AuthService:
    """获取认证服务（依赖注入）"""
    try:
        return await get_service_async(AuthService)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"认证服务不可用: {str(e)}")


# API端点
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    auth_data: dict = Depends(require_write),
    coordinator: ExecutionCoordinator = Depends(get_coordinator)
):
    """聊天端点（使用依赖注入）"""
    http_request: Optional[Request] = None
    logger = await get_service_async(ILoggingService)
    
    # 使用中间件验证后的数据（如果可用）
    if http_request and hasattr(http_request.state, 'validated_body'):
        validated_data = http_request.state.validated_body
        query = validated_data.get("query", request.query)
        session_id = validated_data.get("session_id", request.session_id)
        context = validated_data.get("context", request.context)
    else:
        query = request.query
        session_id = request.session_id
        context = request.context
    
    logger.info(f"收到来自 {auth_data.get('name', '未知')} 的查询: {query}")
    
    try:
        result = await coordinator.run_task(
            task=query, 
            context=context,
            session_id=session_id
        )
        
        return ChatResponse(
            answer=result.get("final_answer", ""),
            steps=result.get("steps", []),
            status="completed" if not result.get("error") else "failed",
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查 - 无需认证"""
    return {
        "status": "ok", 
        "version": "2.0.0", 
        "timestamp": time.time(),
        "di_enabled": True,
        "container_initialized": _container is not None
    }


@app.get("/health/auth")
async def health_check_auth(auth_data: dict = Depends(require_read)):
    """认证健康检查 - 包含系统信息"""
    coordinator = await get_coordinator()
    
    return {
        "status": "ok", 
        "version": "2.0.0", 
        "timestamp": time.time(),
        "authenticated_as": auth_data.get("name", "unknown"),
        "coordinator_initialized": coordinator is not None,
        "di_container": {
            "initialized": _container is not None,
            "services_count": len(_container.get_registered_services()) if _container else 0
        }
    }


@app.get("/diag")
async def diagnostic_check(auth_data: dict = Depends(require_admin)):
    """诊断端点 - 需要管理员权限"""
    
    diag_info = {
        "timestamp": time.time(),
        "environment": {
            "LLM_PROVIDER": os.getenv('LLM_PROVIDER', '未设置'),
            "PYTHONPATH": os.getenv('PYTHONPATH', '未设置'),
            "DEEPSEEK_API_KEY": "已配置" if os.getenv('DEEPSEEK_API_KEY') else "未设置"
        },
        "server_status": {
            "coordinator_initialized": hasattr(app.state, 'coordinator') and app.state.coordinator is not None,
            "container_initialized": _container is not None,
            "pid": os.getpid(),
            "authenticated_as": auth_data.get("name", "unknown")
        },
        "dependency_injection": {
            "container_type": _container.__class__.__name__ if _container else "未初始化",
            "services_registered": len(_container.get_registered_services()) if _container else 0,
            "bootstrap_initialized": _bootstrap is not None
        }
    }
    
    # 测试协调器
    try:
        coordinator = await get_coordinator()
        if coordinator and hasattr(coordinator, 'llm_service'):
            try:
                llm_test = coordinator.llm_service._call_llm("test", max_tokens=5)
                diag_info["llm_test"] = {
                    "status": "success",
                    "response": llm_test[:50] if llm_test else "empty"
                }
            except Exception as e:
                diag_info["llm_test"] = {
                    "status": "failed", 
                    "error": str(e)
                }
        else:
            diag_info["llm_test"] = {"status": "not_available"}
    except Exception as e:
        diag_info["llm_test"] = {"status": "coordinator_error", "error": str(e)}
    
    # 检查神经网络模型
    try:
        from src.core.neural.factory import NeuralServiceFactory
        intent_classifier = NeuralServiceFactory.get_intent_classifier()
        diag_info["neural_models"] = {
            "intent_classifier": "available" if intent_classifier else "failed_to_load"
        }
    except Exception as e:
        diag_info["neural_models"] = {"intent_classifier": f"error: {str(e)}"}
    
    return diag_info


@app.post("/auth/api-key", response_model=dict)
async def create_api_key(
    request: Request,
    name: str,
    permissions: str = "read,write",
    auth_data: dict = Depends(require_admin)
):
    """创建API密钥（仅管理员）"""
    logger = await get_service_async(ILoggingService)
    
    try:
        # 使用中间件验证后的参数（如果可用）
        if request and hasattr(request.state, 'validated_query_params'):
            validated_params = request.state.validated_query_params
            if 'name' in validated_params:
                name = validated_params['name']
            if 'permissions' in validated_params:
                permissions = validated_params['permissions']
        
        permission_list = [p.strip() for p in permissions.split(",")]
        
        # 使用依赖注入获取认证服务
        auth_service = await get_auth_service()
        new_key = auth_service.generate_api_key()
        
        success = register_api_key(new_key, name, permission_list)
        if success:
            logger.info(f"API密钥已创建: {name}")
            return {
                "api_key": new_key,
                "name": name,
                "permissions": permission_list,
                "message": "API密钥创建成功"
            }
        else:
            raise HTTPException(status_code=500, detail="创建API密钥失败")
    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/info")
async def get_auth_info(auth_data: dict = Depends(verify_api_key_auth)):
    """获取当前认证信息"""
    return {
        "authenticated_as": auth_data.get("name", "unknown"),
        "auth_type": auth_data.get("type", "unknown"),
        "permissions": auth_data.get("permissions", [])
    }


@app.get("/di/services")
async def list_services(auth_data: dict = Depends(require_admin)):
    """列出所有已注册的服务（仅管理员）"""
    if not _container:
        raise HTTPException(status_code=503, detail="依赖注入容器未初始化")
    
    services = _container.get_registered_services()
    service_list = []
    
    for service_type, descriptor in services.items():
        service_list.append({
            "name": service_type.__name__,
            "lifetime": descriptor.lifetime.value,
            "has_factory": descriptor.factory is not None,
            "is_async": descriptor.is_async,
            "dependencies": [d.__name__ for d in descriptor.dependencies] if descriptor.dependencies else []
        })
    
    return {
        "count": len(service_list),
        "services": service_list
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动服务器"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()