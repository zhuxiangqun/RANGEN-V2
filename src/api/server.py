"""
RANGEN API Server

Chat 后端可选:
- 默认: ExecutionCoordinator (轻量，仅 RetrievalTool + ReasoningAgent)
- 启用统一研究系统: 设置 RANGEN_USE_UNIFIED_RESEARCH=1 使用 UnifiedResearchSystem（多智能体+完整工具链）
"""
import time
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from contextlib import asynccontextmanager
from typing import Optional, Any

from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter
from src.core.execution_coordinator import ExecutionCoordinator

from src.agents.tools.tool_registry import ToolRegistry
from src.agents.tools.retrieval_tool import RetrievalTool
from src.services.logging_service import get_logger
from src.api.models import ChatRequest, ChatResponse
from src.api.sop_routes import router as sop_router
from src.api.auth import verify_api_key_auth, require_read, require_write, require_admin, register_api_key, AuthService
from src.middleware.validation import create_validation_middleware, create_security_headers_middleware, create_rate_limit_middleware
from src.utils.input_validator import ValidationLevel

logger = get_logger("api_server")

# Global instances
coordinator: ExecutionCoordinator = None  # type: ignore
research_system: Any = None  # UnifiedResearchSystem when RANGEN_USE_UNIFIED_RESEARCH=1


def _use_unified_research() -> bool:
    """是否使用统一研究系统作为 /chat 后端"""
    return os.getenv("RANGEN_USE_UNIFIED_RESEARCH", "").strip().lower() in ("1", "true", "yes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global coordinator, research_system
    logger.info("Initializing RANGEN System...")

    # 0. Initialize Authentication
    logger.info("Initializing authentication system...")
    if os.getenv("RANGEN_API_KEY"):
        logger.info("Default API key configured via environment")
    else:
        logger.warning("No default API key configured. Set RANGEN_API_KEY environment variable.")

    # 1. Core Services
    context_manager = ContextManager()
    router = ConfigurableRouter()

    # 2. Tool Registry
    registry = ToolRegistry()

    # Register Retrieval Tool (try to connect to KMS, else fallback or error)
    try:
        retrieval_tool = RetrievalTool()
        registry.register_tool(retrieval_tool)
    except Exception as e:
        logger.error(f"Failed to initialize RetrievalTool: {e}")

    # 3. Coordinator (always created for fallback and diag)
    coordinator = ExecutionCoordinator()

    # 4. Optional: Unified Research System as primary chat backend
    if _use_unified_research():
        try:
            from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
            research_system = UnifiedResearchSystem(max_concurrent_queries=2, enable_visualization_server=False)
            logger.info("UnifiedResearchSystem created (lazy init on first /chat). Set RANGEN_USE_UNIFIED_RESEARCH=1 to use.")
        except Exception as e:
            logger.warning(f"UnifiedResearchSystem not available, /chat will use ExecutionCoordinator: {e}")
            research_system = None
    else:
        research_system = None
        logger.info("Chat backend: ExecutionCoordinator. Set RANGEN_USE_UNIFIED_RESEARCH=1 for full multi-agent pipeline.")

    logger.info("RANGEN System Initialized.")
    yield
    # Shutdown logic
    logger.info("Shutting down...")


app = FastAPI(
    title="RANGEN API", 
    version="2.0.0", 
    lifespan=lifespan,
    description="RANGEN Multi-Agent Research System API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加输入验证中间件
app.add_middleware(create_validation_middleware, validation_level=ValidationLevel.MODERATE)

# 添加安全头中间件
app.add_middleware(create_security_headers_middleware)

# 添加速率限制中间件（可选，防止滥用）
app.add_middleware(create_rate_limit_middleware, max_requests=200, window_seconds=60)

# 添加SOP管理路由
app.include_router(sop_router)
app.add_middleware(create_rate_limit_middleware, max_requests=200, window_seconds=60)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    auth_data: dict = Depends(require_write)
):
    http_request: Optional[Request] = None
    if not coordinator and not research_system:
        raise HTTPException(status_code=503, detail="System not initialized")

    if http_request and hasattr(http_request.state, "validated_body"):
        validated_data = http_request.state.validated_body
        query = validated_data.get("query", request.query)
        session_id = validated_data.get("session_id", request.session_id)
        context = validated_data.get("context", request.context)
    else:
        query = request.query
        session_id = request.session_id
        context = request.context

    logger.info(f"Received query from {auth_data.get('name', 'unknown')}: {query}")

    try:
        if research_system is not None:
            from src.unified_research_system import ResearchRequest
            req = ResearchRequest(query=query, context=context or {})
            res = await research_system.execute_research(req)
            steps = (res.metadata or {}).get("steps", [])
            if isinstance(steps, list) and steps and not isinstance(steps[0], dict):
                steps = [{"step": s} for s in steps]
            return ChatResponse(
                answer=res.answer or "",
                steps=steps,
                status="completed" if res.success else "failed",
                error=res.error
            )
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
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Public health check - no authentication required"""
    return {"status": "ok", "version": "2.0.0", "timestamp": time.time()}


@app.get("/health/auth")
async def health_check_auth(auth_data: dict = Depends(require_read)):
    """Authenticated health check with additional system info"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": time.time(),
        "authenticated_as": auth_data.get("name", "unknown"),
        "coordinator_initialized": coordinator is not None,
        "chat_backend": "unified_research" if research_system is not None else "coordinator"
    }


@app.get("/diag")
async def diagnostic_check(auth_data: dict = Depends(require_admin)):
    """Secure diagnostic endpoint for troubleshooting - requires admin permissions"""
    
    # Check environment variables (SECURE: no sensitive data exposure)
    diag_info = {
        "timestamp": time.time(),
        "environment": {
            "LLM_PROVIDER": os.getenv('LLM_PROVIDER', 'Not Set'),
            "PYTHONPATH": os.getenv('PYTHONPATH', 'Not Set'),
            "DEEPSEEK_API_KEY": "configured" if os.getenv('DEEPSEEK_API_KEY') else "not_set"
        },
        "server_status": {
            "coordinator_initialized": coordinator is not None,
            "chat_backend_unified_research": research_system is not None,
            "pid": os.getpid(),
            "authenticated_as": auth_data.get("name", "unknown")
        }
    }
    
    # Test LLM connection if coordinator exists
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
    
    # Check neural models
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
    """Create a new API key (admin only)"""
    try:
        # 使用中间件验证后的参数（如果可用）
        if request and hasattr(request.state, 'validated_query_params'):
            validated_params = request.state.validated_query_params
            if 'name' in validated_params:
                name = validated_params['name']
            if 'permissions' in validated_params:
                permissions = validated_params['permissions']
        
        permission_list = [p.strip() for p in permissions.split(",")]
        new_key = AuthService.generate_api_key()
        
        success = register_api_key(new_key, name, permission_list)
        if success:
            return {
                "api_key": new_key,
                "name": name,
                "permissions": permission_list,
                "message": "API key created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create API key")
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/info")
async def get_auth_info(auth_data: dict = Depends(verify_api_key_auth)):
    """Get current authentication information"""
    return {
        "authenticated_as": auth_data.get("name", "unknown"),
        "auth_type": auth_data.get("type", "unknown"),
        "permissions": auth_data.get("permissions", [])
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
