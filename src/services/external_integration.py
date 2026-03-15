"""
External Integration Service - MCP Server, OpenAI/GitHub, Custom API import
"""
import os
import json
import yaml
import importlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ExternalSourceType(str, Enum):
    """外部来源类型"""
    MCP_SERVER = "mcp_server"      # MCP Server
    OPENAI = "openai"              # OpenAI GPTs
    GITHUB = "github"              # GitHub Copilot
    CUSTOM_API = "custom_api"      # 自定义API
    YAML_CONFIG = "yaml_config"    # YAML配置导入
    JSON_CONFIG = "json_config"    # JSON配置导入


@dataclass
class ExternalCapability:
    """外部能力"""
    id: str
    name: str
    source_type: ExternalSourceType
    source: str  # URL, path, or identifier
    description: str
    capabilities: List[str] = field(default_factory=list)  # tools, skills, agents
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, connected, error
    imported_at: Optional[datetime] = None


@dataclass
class MCPEndpoint:
    """MCP服务端点配置"""
    name: str
    url: str
    transport: str = "stdio"  # stdio, http
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    server_type: str = "external"  # local, external


class ExternalIntegrationService:
    """外部集成服务 - 导入外部能力"""
    
    def __init__(self):
        self._integrations: Dict[str, ExternalCapability] = {}
        self._mcp_endpoints: Dict[str, MCPEndpoint] = {}
    
    # ========== MCP Server Integration ==========
    
    def add_mcp_endpoint(
        self,
        name: str,
        url: str,
        transport: str = "stdio",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        server_type: str = "external"
    ) -> MCPEndpoint:
        """添加MCP服务端点"""
        endpoint = MCPEndpoint(
            name=name,
            url=url,
            transport=transport,
            command=command,
            args=args or [],
            server_type=server_type
        )
        
        self._mcp_endpoints[name] = endpoint
        
        # 创建集成记录
        capability = ExternalCapability(
            id=f"mcp_{name}",
            name=f"MCP: {name}",
            source_type=ExternalSourceType.MCP_SERVER,
            source=url,
            description=f"MCP Server: {name}",
            status="pending"
        )
        self._integrations[capability.id] = capability
        
        logger.info(f"MCP endpoint added: {name}")
        return endpoint
    
    def connect_mcp_endpoint(self, name: str) -> bool:
        """连接MCP服务端点"""
        if name not in self._mcp_endpoints:
            logger.warning(f"MCP endpoint not found: {name}")
            return False
        
        endpoint = self._mcp_endpoints[name]
        
        # 模拟连接（实际需要MCP SDK）
        capability_id = f"mcp_{name}"
        if capability_id in self._integrations:
            self._integrations[capability_id].status = "connected"
            self._integrations[capability_id].imported_at = datetime.now()
            logger.info(f"MCP endpoint connected: {name}")
            return True
        
        return False
    
    def list_mcp_tools(self, endpoint_name: str) -> List[Dict[str, Any]]:
        """列出MCP Server提供的工具"""
        # 模拟返回工具列表
        # 实际需要调用MCP协议的list_tools方法
        return [
            {
                "name": f"{endpoint_name}_tool_1",
                "description": "Example tool from MCP server",
                "inputSchema": {"type": "object"}
            },
            {
                "name": f"{endpoint_name}_tool_2", 
                "description": "Another tool from MCP server",
                "inputSchema": {"type": "object"}
            }
        ]
    
    # ========== OpenAI/GitHub Integration ==========
    
    def import_openai_agent(
        self,
        agent_id: str,
        name: str,
        description: str = ""
    ) -> ExternalCapability:
        """导入OpenAI GPTs Agent"""
        capability = ExternalCapability(
            id=f"openai_{agent_id}",
            name=name,
            source_type=ExternalSourceType.OPENAI,
            source=f"https://openai.com/gpts/{agent_id}",
            description=description or f"OpenAI GPT: {name}",
            capabilities=["agent"],
            metadata={"agent_id": agent_id},
            status="pending"
        )
        
        self._integrations[capability.id] = capability
        logger.info(f"OpenAI agent added: {name}")
        
        return capability
    
    def import_github_copilot(
        self,
        agent_id: str,
        name: str,
        description: str = ""
    ) -> ExternalCapability:
        """导入GitHub Copilot Agent"""
        capability = ExternalCapability(
            id=f"github_{agent_id}",
            name=name,
            source_type=ExternalSourceType.GITHUB,
            source=f"https://github.com/features/copilot",
            description=description or f"GitHub Copilot: {name}",
            capabilities=["agent", "code_completion"],
            metadata={"agent_id": agent_id},
            status="pending"
        )
        
        self._integrations[capability.id] = capability
        logger.info(f"GitHub Copilot agent added: {name}")
        
        return capability
    
    # ========== Custom API Integration ==========
    
    def add_custom_api(
        self,
        name: str,
        base_url: str,
        auth_type: str = "none",  # none, api_key, bearer, basic
        headers: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> ExternalCapability:
        """添加自定义API作为Tool来源"""
        capability = ExternalCapability(
            id=f"api_{name}",
            name=name,
            source_type=ExternalSourceType.CUSTOM_API,
            source=base_url,
            description=description or f"Custom API: {name}",
            capabilities=["tool"],
            metadata={
                "auth_type": auth_type,
                "headers": headers or {}
            },
            status="pending"
        )
        
        self._integrations[capability.id] = capability
        logger.info(f"Custom API added: {name}")
        
        return capability
    
    # ========== Config Import ==========
    
    def import_from_yaml(self, yaml_path: str) -> List[ExternalCapability]:
        """从YAML文件导入配置"""
        capabilities = []
        
        if not os.path.exists(yaml_path):
            logger.error(f"YAML file not found: {yaml_path}")
            return capabilities
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return capabilities
            
            # 解析agents配置
            for agent_config in config.get('agents', []):
                capability = ExternalCapability(
                    id=f"yaml_{agent_config.get('name', 'unknown')}",
                    name=agent_config.get('name', 'Unknown'),
                    source_type=ExternalSourceType.YAML_CONFIG,
                    source=yaml_path,
                    description=agent_config.get('description', ''),
                    capabilities=agent_config.get('capabilities', ['agent']),
                    metadata=agent_config,
                    status="connected",
                    imported_at=datetime.now()
                )
                self._integrations[capability.id] = capability
                capabilities.append(capability)
            
            # 解析skills配置
            for skill_config in config.get('skills', []):
                capability = ExternalCapability(
                    id=f"yaml_{skill_config.get('name', 'unknown')}",
                    name=skill_config.get('name', 'Unknown'),
                    source_type=ExternalSourceType.YAML_CONFIG,
                    source=yaml_path,
                    description=skill_config.get('description', ''),
                    capabilities=skill_config.get('capabilities', ['skill']),
                    metadata=skill_config,
                    status="connected",
                    imported_at=datetime.now()
                )
                self._integrations[capability.id] = capability
                capabilities.append(capability)
            
            logger.info(f"Imported {len(capabilities)} capabilities from YAML")
            
        except Exception as e:
            logger.error(f"Error importing YAML: {e}")
        
        return capabilities
    
    def import_from_json(self, json_path: str) -> List[ExternalCapability]:
        """从JSON文件导入配置"""
        capabilities = []
        
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return capabilities
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not config:
                return capabilities
            
            # 通用解析
            for item in config.get('agents', []) + config.get('skills', []) + config.get('tools', []):
                item_type = item.get('type', 'unknown')
                capability = ExternalCapability(
                    id=f"json_{item.get('name', 'unknown')}",
                    name=item.get('name', 'Unknown'),
                    source_type=ExternalSourceType.JSON_CONFIG,
                    source=json_path,
                    description=item.get('description', ''),
                    capabilities=[item_type],
                    metadata=item,
                    status="connected",
                    imported_at=datetime.now()
                )
                self._integrations[capability.id] = capability
                capabilities.append(capability)
            
            logger.info(f"Imported {len(capabilities)} capabilities from JSON")
            
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
        
        return capabilities
    
    # ========== Listing ==========
    
    def get_all_integrations(self) -> List[ExternalCapability]:
        """获取所有外部集成"""
        return list(self._integrations.values())
    
    def get_integration(self, integration_id: str) -> Optional[ExternalCapability]:
        """获取单个集成"""
        return self._integrations.get(integration_id)
    
    def remove_integration(self, integration_id: str) -> bool:
        """移除集成"""
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            logger.info(f"Integration removed: {integration_id}")
            return True
        return False


# Global instance
_external_service: Optional[ExternalIntegrationService] = None


def get_external_service() -> ExternalIntegrationService:
    """获取外部集成服务实例"""
    global _external_service
    if _external_service is None:
        _external_service = ExternalIntegrationService()
    return _external_service
