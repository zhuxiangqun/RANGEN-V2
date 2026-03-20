"""
RANGEN API Server

Chat 后端选项 (按优先级):
1. ProductionWorkflow (默认): 基于 langgraph_unified_workflow 简化版，含 RAG/CE/PE
2. UnifiedResearchSystem: 完整多智能体系统
3. ExecutionCoordinator: 轻量版
"""

import re
import time
import os
import uvicorn
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path, override=False)
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Depends, Request
from contextlib import asynccontextmanager
from typing import Optional, Any

from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter

# 默认使用 ProductionWorkflow (基于 langgraph_unified_workflow 简化)
from src.core.production_workflow import ProductionWorkflow, get_production_workflow

from src.agents.tools.tool_registry import ToolRegistry
from src.agents.tools.retrieval_tool import RetrievalTool
from src.services.logging_service import get_logger
from src.api.models import ChatRequest, ChatResponse
from src.api.sop_routes import router as sop_router
from src.api.unified_create_routes import router as unified_create_router
from src.api.workflows import router as workflows_router
from src.api.auto_create_routes import router as auto_create_router
from src.api.team_routes import router as team_router
from src.api.agents import router as agents_router
from src.api.skills import router as skills_router
from src.api.tools import router as tools_router
from src.api.teams import router as teams_router

# 新增路由
from src.api.cost_control import router as cost_router
from src.api.security_control import router as security_router
from src.api.sandbox import router as sandbox_router
from src.api.mcp_routes import router as mcp_router
from src.api.external_integration import router as external_router
from src.api.model_routes import router as model_router
from src.api.test_execution import router as test_router
from src.api.routing_monitor_routes import router as routing_monitor_router
from src.api.cost_alert import router as cost_alert_router
from src.api.execution_control import router as execution_control_router
from src.api.ops_diagnosis_routes import router as ops_diagnosis_router
from src.api.smart_handler_routes import router as smart_handler_router
from src.api.conversation_routes import router as conversation_router
from src.api.hub_routes import router as hub_router

from src.api.auth import verify_api_key_auth, require_read, require_write, require_admin, register_api_key, AuthService
from src.middleware.validation import create_validation_middleware, create_security_headers_middleware, create_rate_limit_middleware
from src.utils.input_validator import ValidationLevel

logger = get_logger("api_server")

# Global instances
production_workflow: Optional[ProductionWorkflow] = None
coordinator: Any = None  # ExecutionCoordinator (备用)
research_system: Any = None  # UnifiedResearchSystem


def _use_production_workflow() -> bool:
    """是否使用生产工作流 (默认)"""
    return os.getenv("RANGEN_USE_PRODUCTION_WORKFLOW", "true").strip().lower() in ("1", "true", "yes")


def _use_unified_research() -> bool:
    """是否使用统一研究系统"""
    return os.getenv("RANGEN_USE_UNIFIED_RESEARCH", "").strip().lower() in ("1", "true", "yes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global production_workflow, coordinator, research_system
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
    try:
        retrieval_tool = RetrievalTool()
        registry.register_tool(retrieval_tool)
    except Exception as e:
        logger.error(f"Failed to initialize RetrievalTool: {e}")

    # 3. Production Workflow (默认)
    if _use_production_workflow():
        try:
            production_workflow = get_production_workflow()
            logger.info("ProductionWorkflow initialized (RAG/CE/PE enabled)!")
        except Exception as e:
            logger.warning(f"ProductionWorkflow init failed: {e}")
            production_workflow = None

    # 4. Unified Research System (可选)
    if _use_unified_research():
        try:
            from src.unified_research_system import UnifiedResearchSystem, ResearchRequest
            research_system = UnifiedResearchSystem(max_concurrent_queries=2, enable_visualization_server=False)
            logger.info("UnifiedResearchSystem created (optional).")
        except Exception as e:
            logger.warning(f"UnifiedResearchSystem not available: {e}")
            research_system = None
    
    # 5. ExecutionCoordinator (备用)
    try:
        from src.core.execution_coordinator import ExecutionCoordinator
        coordinator = ExecutionCoordinator()
    except Exception as e:
        logger.warning(f"ExecutionCoordinator not available: {e}")
        coordinator = None

    logger.info("RANGEN System Initialized.")
    yield
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

# 添加统一创建路由
app.include_router(unified_create_router)

# 添加Workflow路由
app.include_router(workflows_router)

# 添加自动创建工作流路由
app.include_router(auto_create_router)

# 添加 Team 执行路由
try:
    from src.api.team_routes import router as team_router
    app.include_router(team_router)
except Exception:
    pass

# 添加 Agent 路由
try:
    app.include_router(agents_router)
except Exception:
    pass

# 添加 Skill 路由
try:
    app.include_router(skills_router)
except Exception:
    pass

# 添加 Tool 路由
try:
    app.include_router(tools_router)
except Exception:
    pass

# 添加 Teams 路由
try:
    app.include_router(teams_router)
except Exception:
    pass

# 新增路由 - 质量控制 (路由器已有前缀，不要重复添加)
try:
    app.include_router(cost_router, tags=["cost"])
except Exception as e:
    logger.warning(f"Cost router not loaded: {e}")

try:
    app.include_router(security_router, tags=["security"])
except Exception as e:
    logger.warning(f"Security router not loaded: {e}")

try:
    app.include_router(sandbox_router, tags=["sandbox"])
except Exception as e:
    logger.warning(f"Sandbox router not loaded: {e}")

try:
    app.include_router(cost_alert_router, tags=["cost-alert"])
except Exception as e:
    logger.warning(f"Cost alert router not loaded: {e}")

try:
    app.include_router(execution_control_router, tags=["execution"])
except Exception as e:
    logger.warning(f"Execution control router not loaded: {e}")

try:
    app.include_router(ops_diagnosis_router, tags=["ops-diagnosis"])
except Exception as e:
    logger.warning(f"Ops diagnosis router not loaded: {e}")

try:
    app.include_router(smart_handler_router, tags=["smart-handler"])
except Exception as e:
    logger.warning(f"Smart handler router not loaded: {e}")

try:
    app.include_router(conversation_router, tags=["conversation"])
except Exception as e:
    logger.warning(f"Conversation router not loaded: {e}")

# 新增路由 - 集成
try:
    app.include_router(mcp_router, tags=["mcp"])
except Exception as e:
    logger.warning(f"MCP router not loaded: {e}")

try:
    app.include_router(external_router, tags=["external"])
except Exception as e:
    logger.warning(f"External router not loaded: {e}")

try:
    app.include_router(model_router, tags=["model"])
except Exception as e:
    logger.warning(f"Model router not loaded: {e}")

# 新增路由 - 测试与监控
try:
    app.include_router(test_router, tags=["test"])
except Exception as e:
    logger.warning(f"Test router not loaded: {e}")

try:
    app.include_router(routing_monitor_router, tags=["routing"])
except Exception as e:
    logger.warning(f"Routing monitor router not loaded: {e}")

# Central Hub 路由 - Hands 智能助手基盘
try:
    app.include_router(hub_router, tags=["hub"])
    logger.info("Central Hub router loaded - Hands intelligent assistant platform ready!")
except Exception as e:
    logger.warning(f"Hub router not loaded: {e}")

app.add_middleware(create_rate_limit_middleware, max_requests=200, window_seconds=60)


@app.get("/", response_model=dict)
async def root():
    return {
        "message": "RANGEN API Server",
        "version": "2.0",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }


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

    # Check if this is an entity creation request
    creation_patterns = [
        r"创建.*", r"做一个", r"帮我建", r"新建.*",
        r"create.*", r"make.*", r"build.*",
        r"添加.*skill", r"添加.*agent", r"添加.*tool",
        r"创建一个.*team", r"创建一个.*agent", r"创建一个.*skill"
    ]
    
    is_creation_request = any(re.match(pattern, query.lower()) for pattern in creation_patterns)
    
    if is_creation_request:
        try:
            from src.api.unified_create_routes import EntityCreateRequest
            from src.services.unified_creator import get_unified_creator
            
            creator = get_unified_creator()
            result = await creator.create_from_natural_language(query)
            
            if result.success:
                return ChatResponse(
                    answer=result.message,
                    steps=[f"Entity creation: Created {result.entity_type}: {result.entity_name}"],
                    status="completed"
                )
            else:
                # Fall through to normal chat if creation failed
                logger.info(f"Entity creation failed, falling back to normal chat: {result.error}")
        except Exception as e:
            logger.warning(f"Entity creation detection failed: {e}")
    
    try:
        # ===== Intelligent Tool Selection =====
        # 在 workflow 执行之前先尝试智能工具选择
        try:
            from src.core.unified_tool_executor import get_unified_tool_executor
            unified_executor = get_unified_tool_executor()
            if unified_executor:
                tool_result = await unified_executor.execute_with_intelligent_selection(query)
                if tool_result and tool_result.get("success"):
                    logger.info(f"Intelligent tool execution successful: {tool_result.get('tool_name')}")
                    return ChatResponse(
                        answer=tool_result.get("answer", "操作完成"),
                        steps=["intelligent_tool_selection"],
                        status="completed",
                        error=None
                    )
        except Exception as e:
            logger.warning(f"Intelligent tool selection failed: {e}")
        # ===== End Intelligent Tool Selection =====
    
        # 优先使用 ProductionWorkflow (基于 langgraph_unified_workflow 简化)
        if production_workflow is not None:
            result = await production_workflow.execute(
                query=query,
                context=context
            )
            return ChatResponse(
                answer=result.get("final_answer", ""),
                steps=result.get("steps", []),
                status="completed" if not result.get("error") else "failed",
                error=result.get("error")
            )
        
        # 其次使用统一研究系统
        if research_system is not None:
            from src.core.research_request import ResearchRequest
            req = ResearchRequest(
                request_id=f"api_{int(time.time())}",
                query=query,
                user_id=session_id or "anonymous",
                context=context or {}
            )
            res = await research_system.execute_research(req)
            steps = (res.metadata or {}).get("steps", [])
            if isinstance(steps, list) and steps:
                if isinstance(steps[0], dict):
                    steps = [s.get("step", str(s)) for s in steps]
            else:
                steps = []
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


@app.get("/health/resource")
async def resource_health_check():
    """Resource health check - CPU, Memory, Disk usage"""
    try:
        from src.utils.resource_monitor import ResourceMonitor
        monitor = ResourceMonitor()
        status = monitor.get_resource_status()
        return {
            "status": "ok",
            "timestamp": time.time(),
            "resources": status
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/health/auth")
async def health_check_auth(auth_data: dict = Depends(require_read)):
    """Authenticated health check with additional system info"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": time.time(),
        "authenticated_as": auth_data.get("name", "unknown"),
        "coordinator_initialized": coordinator is not None,
        "chat_backend": "production_workflow" if production_workflow else "unified_research" if research_system else "coordinator"
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
