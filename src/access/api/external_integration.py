"""
External Integration API - MCP Server, OpenAI/GitHub, Custom API import
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel, Field
from src.services.external_integration import (
    get_external_service,
    ExternalSourceType
)

router = APIRouter(prefix="/external", tags=["external"])


class MCPEndpointRequest(BaseModel):
    """MCP服务端点请求"""
    name: str
    url: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    server_type: str = "external"


class OpenAIImportRequest(BaseModel):
    """OpenAI导入请求"""
    agent_id: str
    name: str
    description: Optional[str] = None


class GitHubImportRequest(BaseModel):
    """GitHub导入请求"""
    agent_id: str
    name: str
    description: Optional[str] = None


class CustomAPIRequest(BaseModel):
    """自定义API请求"""
    name: str
    base_url: str
    auth_type: str = "none"
    headers: Optional[dict] = None
    description: Optional[str] = None


class IntegrationResponse(BaseModel):
    """集成响应"""
    id: str
    name: str
    source_type: str
    source: str
    description: str
    capabilities: List[str]
    status: str
    imported_at: Optional[str] = None


@router.get("/integrations", response_model=List[IntegrationResponse])
async def get_integrations():
    """获取所有外部集成"""
    service = get_external_service()
    
    integrations = service.get_all_integrations()
    
    return [
        IntegrationResponse(
            id=i.id,
            name=i.name,
            source_type=i.source_type.value,
            source=i.source,
            description=i.description,
            capabilities=i.capabilities,
            status=i.status,
            imported_at=i.imported_at.isoformat() if i.imported_at else None
        )
        for i in integrations
    ]


@router.post("/mcp/add")
async def add_mcp_endpoint(request: MCPEndpointRequest):
    """添加MCP服务端点"""
    service = get_external_service()
    
    endpoint = service.add_mcp_endpoint(
        name=request.name,
        url=request.url,
        transport=request.transport,
        command=request.command,
        args=request.args,
        server_type=request.server_type
    )
    
    return {
        "message": "MCP endpoint added",
        "endpoint": {
            "name": endpoint.name,
            "url": endpoint.url,
            "transport": endpoint.transport
        }
    }


@router.post("/mcp/connect/{name}")
async def connect_mcp(name: str):
    """连接MCP服务端点"""
    service = get_external_service()
    
    success = service.connect_mcp_endpoint(name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP endpoint not found: {name}"
        )
    
    return {
        "message": f"MCP endpoint '{name}' connected",
        "tools": service.list_mcp_tools(name)
    }


@router.get("/mcp/tools/{endpoint_name}")
async def list_mcp_tools(endpoint_name: str):
    """列出MCP Server工具"""
    service = get_external_service()
    
    tools = service.list_mcp_tools(endpoint_name)
    
    return {"endpoint": endpoint_name, "tools": tools}


@router.post("/openai/import")
async def import_openai_agent(request: OpenAIImportRequest):
    """导入OpenAI GPTs Agent"""
    service = get_external_service()
    
    capability = service.import_openai_agent(
        agent_id=request.agent_id,
        name=request.name,
        description=request.description
    )
    
    return {
        "message": "OpenAI agent imported",
        "integration": {
            "id": capability.id,
            "name": capability.name,
            "status": capability.status
        }
    }


@router.post("/github/import")
async def import_github_copilot(request: GitHubImportRequest):
    """导入GitHub Copilot Agent"""
    service = get_external_service()
    
    capability = service.import_github_copilot(
        agent_id=request.agent_id,
        name=request.name,
        description=request.description
    )
    
    return {
        "message": "GitHub Copilot agent imported",
        "integration": {
            "id": capability.id,
            "name": capability.name,
            "status": capability.status
        }
    }


@router.post("/custom-api/add")
async def add_custom_api(request: CustomAPIRequest):
    """添加自定义API"""
    service = get_external_service()
    
    capability = service.add_custom_api(
        name=request.name,
        base_url=request.base_url,
        auth_type=request.auth_type,
        headers=request.headers,
        description=request.description
    )
    
    return {
        "message": "Custom API added",
        "integration": {
            "id": capability.id,
            "name": capability.name,
            "status": capability.status
        }
    }


@router.post("/import/yaml")
async def import_yaml(file: UploadFile = File(...)):
    """从YAML文件导入配置"""
    import tempfile
    import os
    
    service = get_external_service()
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        content = await file.read()
        tmp.write(content.decode('utf-8'))
        tmp_path = tmp.name
    
    try:
        capabilities = service.import_from_yaml(tmp_path)
        
        return {
            "message": f"Imported {len(capabilities)} capabilities from YAML",
            "capabilities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "capabilities": c.capabilities
                }
                for c in capabilities
            ]
        }
    finally:
        os.unlink(tmp_path)


@router.post("/import/json")
async def import_json(file: UploadFile = File(...)):
    """从JSON文件导入配置"""
    import tempfile
    import os
    
    service = get_external_service()
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        content = await file.read()
        tmp.write(content.decode('utf-8'))
        tmp_path = tmp.name
    
    try:
        capabilities = service.import_from_json(tmp_path)
        
        return {
            "message": f"Imported {len(capabilities)} capabilities from JSON",
            "capabilities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "capabilities": c.capabilities
                }
                for c in capabilities
            ]
        }
    finally:
        os.unlink(tmp_path)


@router.delete("/integrations/{integration_id}")
async def remove_integration(integration_id: str):
    """移除集成"""
    service = get_external_service()
    
    success = service.remove_integration(integration_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration not found: {integration_id}"
        )
    
    return {"message": "Integration removed"}
