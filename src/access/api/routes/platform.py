"""
平台管理 API Routes

功能:
- 应用注册与管理
- 配额管理
- 命名空间管理

启用条件:
- RANGEN_PLATFORM_ENABLED=true
- 模块可正常导入

注意: 此文件为纯新增，不修改现有 API
"""

import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from datetime import datetime

# 尝试导入平台组件
try:
    from src.platform.app.registry import get_app_registry, AppStatus, App
    from src.platform.app.registry import AppRegistry
    from src.platform.quota.manager import get_quota_manager, QuotaLimit, QuotaManager
    from src.platform.namespace.manager import get_namespace_manager, Namespace
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False

router = APIRouter(prefix="/platform", tags=["platform"])


# ========== 请求/响应模型 ==========

class QuotaConfig(BaseModel):
    """配额配置"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    tokens_per_month: int = 1000000
    cost_per_month: float = 100.0


class CreateAppRequest(BaseModel):
    """创建应用请求"""
    name: str
    description: str = ""
    quota_config: Optional[QuotaConfig] = None


class AppResponse(BaseModel):
    """应用响应"""
    app_id: str
    name: str
    description: str
    status: str
    namespace_id: Optional[str] = None
    created_at: Optional[str] = None


class CreateNamespaceRequest(BaseModel):
    """创建命名空间请求"""
    name: str
    description: str = ""
    vector_dim: int = 1536
    max_documents: int = 10000
    max_graph_nodes: int = 50000


class NamespaceResponse(BaseModel):
    """命名空间响应"""
    namespace_id: str
    name: str
    description: str
    document_count: int = 0
    max_documents: int = 10000


# ========== 依赖项 ==========

def check_platform_available():
    """检查平台功能是否可用"""
    if not PLATFORM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="平台模块不可用，请检查安装"
        )

def check_platform_enabled():
    """检查平台功能是否启用"""
    if not PLATFORM_AVAILABLE:
        raise HTTPException(503, "平台模块不可用")
    
    enabled = os.getenv("RANGEN_PLATFORM_ENABLED", "false").lower()
    if enabled != "true":
        raise HTTPException(
            status_code=503,
            detail="平台功能未启用，请设置 RANGEN_PLATFORM_ENABLED=true"
        )


def get_current_app_id(request: Request) -> Optional[str]:
    """获取当前请求的 app_id"""
    return getattr(request.state, 'app_id', None)


# ========== 应用管理 ==========

@router.post("/apps", response_model=AppResponse, dependencies=[Depends(check_platform_enabled)])
async def create_app(req: CreateAppRequest):
    """
    注册新应用
    
    创建应用并生成 API Key，每个应用有独立的命名空间和配额
    """
    registry = get_app_registry()
    
    # 检查名称是否已存在
    existing = registry.get_by_name(req.name)
    if existing:
        raise HTTPException(400, f"应用名称已存在: {req.name}")
    
    # 创建应用
    quota_config = req.quota_config.model_dump() if req.quota_config else None
    app = registry.register(
        name=req.name,
        description=req.description,
        owner_id="system",  # TODO: 从认证获取
        quota_config=quota_config
    )
    
    # 设置配额
    if req.quota_config:
        quota_mgr = get_quota_manager()
        quota_mgr.set_quota(app.app_id, QuotaLimit(**req.quota_config.model_dump()))
    
    # 创建默认命名空间
    ns_mgr = get_namespace_manager()
    namespace = ns_mgr.create_default(app.app_id)
    app.namespace_id = namespace.namespace_id
    
    return AppResponse(
        app_id=app.app_id,
        name=app.name,
        description=app.description,
        status=app.status.value,
        namespace_id=app.namespace_id,
        created_at=app.created_at.isoformat() if hasattr(app.created_at, 'isoformat') else str(app.created_at)
    )


@router.get("/apps", dependencies=[Depends(check_platform_enabled)])
async def list_apps(
    owner_id: Optional[str] = None,
    status: Optional[str] = None
):
    """
    列出应用
    
    - owner_id: 按所有者过滤
    - status: 按状态过滤 (active/suspended/deleted)
    """
    registry = get_app_registry()
    
    # 解析状态
    app_status = None
    if status:
        try:
            app_status = AppStatus(status)
        except ValueError:
            raise HTTPException(400, f"无效状态: {status}")
    
    apps = registry.list_apps(owner_id=owner_id, status=app_status)
    
    return {
        "apps": [
            {
                "app_id": a.app_id,
                "name": a.name,
                "description": a.description,
                "status": a.status.value,
                "namespace_id": a.namespace_id
            }
            for a in apps
        ],
        "total": len(apps)
    }


@router.get("/apps/{app_id}", dependencies=[Depends(check_platform_enabled)])
async def get_app(app_id: str):
    """获取应用详情"""
    registry = get_app_registry()
    app = registry.get_by_id(app_id)
    
    if not app:
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    return {
        "app_id": app.app_id,
        "name": app.name,
        "description": app.description,
        "status": app.status.value,
        "namespace_id": app.namespace_id,
        "owner_id": app.owner_id,
        "created_at": app.created_at.isoformat() if hasattr(app.created_at, 'isoformat') else str(app.created_at),
        "updated_at": app.updated_at.isoformat() if hasattr(app.updated_at, 'isoformat') else str(app.updated_at)
    }


@router.delete("/apps/{app_id}", dependencies=[Depends(check_platform_enabled)])
async def delete_app(app_id: str):
    """删除应用 (软删除)"""
    registry = get_app_registry()
    
    if not registry.delete(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    return {"message": f"应用已删除: {app_id}"}


# ========== 配额管理 ==========

@router.get("/apps/{app_id}/quota", dependencies=[Depends(check_platform_enabled)])
async def get_app_quota(app_id: str):
    """获取应用配额"""
    registry = get_app_registry()
    if not registry.get_by_id(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    quota_mgr = get_quota_manager()
    quota = quota_mgr.get_quota(app_id)
    
    if not quota:
        return {"message": "应用未设置配额"}
    
    return {
        "requests_per_minute": quota.requests_per_minute,
        "requests_per_hour": quota.requests_per_hour,
        "requests_per_day": quota.requests_per_day,
        "tokens_per_month": quota.tokens_per_month,
        "cost_per_month": quota.cost_per_month
    }


@router.put("/apps/{app_id}/quota", dependencies=[Depends(check_platform_enabled)])
async def set_app_quota(app_id: str, quota_config: QuotaConfig):
    """设置应用配额"""
    registry = get_app_registry()
    if not registry.get_by_id(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    quota_mgr = get_quota_manager()
    quota = QuotaLimit(**quota_config.model_dump())
    quota_mgr.set_quota(app_id, quota)
    
    return {"message": "配额已更新", "app_id": app_id}


@router.get("/apps/{app_id}/usage", dependencies=[Depends(check_platform_enabled)])
async def get_app_usage(app_id: str):
    """获取应用使用情况"""
    registry = get_app_registry()
    if not registry.get_by_id(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    quota_mgr = get_quota_manager()
    usage = quota_mgr.get_usage(app_id)
    
    if not usage:
        return {
            "app_id": app_id,
            "message": "暂无使用数据"
        }
    
    return usage


# ========== 命名空间管理 ==========

@router.post("/namespaces", dependencies=[Depends(check_platform_enabled)])
async def create_namespace(
    app_id: str,
    req: CreateNamespaceRequest
):
    """为应用创建命名空间"""
    registry = get_app_registry()
    if not registry.get_by_id(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    ns_mgr = get_namespace_manager()
    
    # 检查命名空间名称是否已存在
    existing = ns_mgr.get_by_name(app_id, req.name)
    if existing:
        raise HTTPException(400, f"命名空间已存在: {req.name}")
    
    namespace = ns_mgr.create(
        app_id=app_id,
        name=req.name,
        description=req.description,
        vector_dim=req.vector_dim,
        max_documents=req.max_documents,
        max_graph_nodes=req.max_graph_nodes
    )
    
    return NamespaceResponse(
        namespace_id=namespace.namespace_id,
        name=namespace.name,
        description=namespace.description,
        document_count=namespace.document_count,
        max_documents=namespace.max_documents
    )


@router.get("/namespaces", dependencies=[Depends(check_platform_enabled)])
async def list_namespaces(app_id: str):
    """列出应用的所有命名空间"""
    registry = get_app_registry()
    if not registry.get_by_id(app_id):
        raise HTTPException(404, f"应用不存在: {app_id}")
    
    ns_mgr = get_namespace_manager()
    namespaces = ns_mgr.get_by_app(app_id)
    
    return {
        "namespaces": [
            {
                "namespace_id": ns.namespace_id,
                "name": ns.name,
                "description": ns.description,
                "document_count": ns.document_count,
                "max_documents": ns.max_documents
            }
            for ns in namespaces
        ],
        "total": len(namespaces)
    }


@router.get("/namespaces/{namespace_id}", dependencies=[Depends(check_platform_enabled)])
async def get_namespace(namespace_id: str):
    """获取命名空间详情"""
    ns_mgr = get_namespace_manager()
    namespace = ns_mgr.get_by_id(namespace_id)
    
    if not namespace:
        raise HTTPException(404, f"命名空间不存在: {namespace_id}")
    
    return {
        "namespace_id": namespace.namespace_id,
        "app_id": namespace.app_id,
        "name": namespace.name,
        "description": namespace.description,
        "vector_dim": namespace.vector_dim,
        "document_count": namespace.document_count,
        "max_documents": namespace.max_documents,
        "graph_node_count": namespace.graph_node_count,
        "max_graph_nodes": namespace.max_graph_nodes
    }


@router.delete("/namespaces/{namespace_id}", dependencies=[Depends(check_platform_enabled)])
async def delete_namespace(namespace_id: str):
    """删除命名空间"""
    ns_mgr = get_namespace_manager()
    
    if not ns_mgr.delete(namespace_id):
        raise HTTPException(404, f"命名空间不存在: {namespace_id}")
    
    return {"message": f"命名空间已删除: {namespace_id}"}


# ========== 系统信息 ==========

@router.get("/status", dependencies=[Depends(check_platform_available)])
async def get_platform_status():
    """获取平台状态"""
    enabled = os.getenv("RANGEN_PLATFORM_ENABLED", "false").lower() == "true"
    
    status = {
        "available": PLATFORM_AVAILABLE,
        "enabled": enabled,
        "message": "平台功能已启用" if enabled else "平台功能已禁用 (RANGEN_PLATFORM_ENABLED=false)"
    }
    
    if enabled:
        registry = get_app_registry()
        ns_mgr = get_namespace_manager()
        quota_mgr = get_quota_manager()
        
        status["stats"] = {
            "total_apps": len(registry),
            "total_namespaces": len(ns_mgr),
            "apps_with_quota": len(quota_mgr)
        }
    
    return status
