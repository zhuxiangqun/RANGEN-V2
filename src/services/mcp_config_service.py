#!/usr/bin/env python3
"""
MCP Configuration Service

Loads and manages MCP configuration from YAML files
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class MCPServerConfig:
    """MCP server configuration"""
    name: str
    description: str
    enabled: bool = True
    transport: str = "stdio"  # stdio or http
    
    # stdio configuration
    stdio_command: str = ""
    stdio_args: List[str] = field(default_factory=list)
    
    # http configuration
    http_enabled: bool = False
    http_host: str = "0.0.0.0"
    http_port: int = 8080
    http_endpoint: str = ""
    
    # Tools configuration
    include_all_tools: bool = True
    excluded_tools: List[str] = field(default_factory=list)
    included_tools_only: List[str] = field(default_factory=list)
    
    # Resources configuration
    resources_enabled: bool = False
    resource_paths: List[str] = field(default_factory=list)
    
    # Prompts configuration
    prompts_enabled: bool = False


@dataclass
class MCPClientConfig:
    """MCP client configuration"""
    name: str
    description: str
    transport: str = "stdio"
    server_url: str = ""
    auto_connect: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


@dataclass
class MCPIntegrationConfig:
    """MCP integration configuration"""
    auto_start_servers: bool = True
    auto_register_tools: bool = True
    enable_context_protocol: bool = True
    
    # PageIndex integration
    pageindex_enabled: bool = True
    pageindex_server_name: str = "pageindex"
    pageindex_transport: str = "stdio"


@dataclass
class MCPSecurityConfig:
    """MCP security configuration"""
    authentication_enabled: bool = False
    api_key: str = ""
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:*",
        "http://127.0.0.1:*"
    ])


@dataclass
class MCPMonitoringConfig:
    """MCP monitoring configuration"""
    enabled: bool = True
    log_requests: bool = True
    log_responses: bool = False
    metrics_collection: bool = True
    health_check_interval: int = 30  # seconds


@dataclass
class MCPPerformanceConfig:
    """MCP performance configuration"""
    max_concurrent_requests: int = 10
    request_timeout: int = 30  # seconds
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds


@dataclass
class MCPConfig:
    """Main MCP configuration"""
    enabled: bool = True
    log_level: str = "INFO"
    
    # Servers
    servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    
    # Clients
    clients: Dict[str, MCPClientConfig] = field(default_factory=dict)
    
    # Integration
    integration: MCPIntegrationConfig = field(default_factory=MCPIntegrationConfig)
    
    # Security
    security: MCPSecurityConfig = field(default_factory=MCPSecurityConfig)
    
    # Monitoring
    monitoring: MCPMonitoringConfig = field(default_factory=MCPMonitoringConfig)
    
    # Performance
    performance: MCPPerformanceConfig = field(default_factory=MCPPerformanceConfig)


class MCPConfigService:
    """MCP configuration service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config: Optional[MCPConfig] = None
        self._config_paths = [
            Path("config/mcp_config.yaml"),
            Path("config/environments/development.yaml"),
            Path("config/environments/production.yaml"),
            Path("config/environments/testing.yaml"),
        ]
        
        self._initialized = True
        logger.info("MCPConfigService initialized")
    
    def load_config(self, config_path: Optional[str] = None) -> MCPConfig:
        """Load MCP configuration from YAML file"""
        try:
            if config_path:
                config_file = Path(config_path)
            else:
                # Try to find config file
                config_file = None
                for path in self._config_paths:
                    if path.exists():
                        config_file = path
                        break
                
                if not config_file:
                    logger.warning("No MCP config file found, using defaults")
                    self.config = MCPConfig()
                    return self.config
            
            logger.info(f"Loading MCP config from: {config_file}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Extract MCP config from data
            mcp_data = config_data.get('mcp', {}) if isinstance(config_data, dict) else {}
            
            if not mcp_data and 'integrations' in config_data:
                # Try to get MCP config from integrations section
                integrations = config_data.get('integrations', {})
                mcp_data = integrations.get('mcp', {})
            
            self.config = self._parse_config(mcp_data)
            logger.info(f"MCP config loaded successfully")
            
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            self.config = MCPConfig()
            return self.config
    
    def _parse_config(self, data: Dict[str, Any]) -> MCPConfig:
        """Parse raw config data into MCPConfig object"""
        config = MCPConfig(
            enabled=data.get('enabled', True),
            log_level=data.get('log_level', 'INFO')
        )
        
        # Parse server configurations
        server_data = data.get('server', {})
        for server_name, server_config in server_data.items():
            if isinstance(server_config, dict) and server_config.get('enabled', True):
                config.servers[server_name] = self._parse_server_config(server_name, server_config)
        
        # Parse client configurations
        client_data = data.get('client', {})
        servers_list = client_data.get('servers', [])
        for server_config in servers_list:
            if isinstance(server_config, dict):
                name = server_config.get('name', '')
                if name:
                    config.clients[name] = self._parse_client_config(server_config)
        
        # Parse integration configuration
        integration_data = data.get('integration', {})
        config.integration = MCPIntegrationConfig(
            auto_start_servers=integration_data.get('auto_start_servers', True),
            auto_register_tools=integration_data.get('auto_register_tools', True),
            enable_context_protocol=integration_data.get('enable_context_protocol', True),
            pageindex_enabled=integration_data.get('pageindex', {}).get('enabled', True),
            pageindex_server_name=integration_data.get('pageindex', {}).get('server_name', 'pageindex'),
            pageindex_transport=integration_data.get('pageindex', {}).get('transport', 'stdio')
        )
        
        # Parse security configuration
        security_data = data.get('security', {})
        config.security = MCPSecurityConfig(
            authentication_enabled=security_data.get('authentication_enabled', False),
            api_key=security_data.get('api_key', ''),
            allowed_origins=security_data.get('allowed_origins', [
                "http://localhost:*",
                "http://127.0.0.1:*"
            ])
        )
        
        # Parse monitoring configuration
        monitoring_data = data.get('monitoring', {})
        config.monitoring = MCPMonitoringConfig(
            enabled=monitoring_data.get('enabled', True),
            log_requests=monitoring_data.get('log_requests', True),
            log_responses=monitoring_data.get('log_responses', False),
            metrics_collection=monitoring_data.get('metrics_collection', True),
            health_check_interval=monitoring_data.get('health_check_interval', 30)
        )
        
        # Parse performance configuration
        performance_data = data.get('performance', {})
        config.performance = MCPPerformanceConfig(
            max_concurrent_requests=performance_data.get('max_concurrent_requests', 10),
            request_timeout=performance_data.get('request_timeout', 30),
            cache_enabled=performance_data.get('cache_enabled', True),
            cache_ttl=performance_data.get('cache_ttl', 300)
        )
        
        return config
    
    def _parse_server_config(self, name: str, data: Dict[str, Any]) -> MCPServerConfig:
        """Parse server configuration"""
        stdio_data = data.get('stdio', {})
        http_data = data.get('http', {})
        tools_data = data.get('tools', {})
        resources_data = data.get('resources', {})
        prompts_data = data.get('prompts', {})
        
        # Build HTTP endpoint if not provided
        http_endpoint = http_data.get('endpoint', '')
        if not http_endpoint and http_data.get('enabled', False):
            host = http_data.get('host', '0.0.0.0')
            port = http_data.get('port', 8080)
            if host == '0.0.0.0':
                http_endpoint = f"http://localhost:{port}"
            else:
                http_endpoint = f"http://{host}:{port}"
        
        return MCPServerConfig(
            name=name,
            description=data.get('description', f"MCP Server: {name}"),
            enabled=data.get('enabled', True),
            transport=data.get('transport', 'stdio'),
            
            # stdio configuration
            stdio_command=stdio_data.get('command', ''),
            stdio_args=stdio_data.get('args', []),
            
            # http configuration
            http_enabled=http_data.get('enabled', False),
            http_host=http_data.get('host', '0.0.0.0'),
            http_port=http_data.get('port', 8080),
            http_endpoint=http_endpoint,
            
            # tools configuration
            include_all_tools=tools_data.get('include_all', True),
            excluded_tools=tools_data.get('exclude', []),
            included_tools_only=tools_data.get('include_only', []),
            
            # resources configuration
            resources_enabled=resources_data.get('enabled', False),
            resource_paths=resources_data.get('paths', []),
            
            # prompts configuration
            prompts_enabled=prompts_data.get('enabled', False)
        )
    
    def _parse_client_config(self, data: Dict[str, Any]) -> MCPClientConfig:
        """Parse client configuration"""
        http_data = data.get('http', {})
        
        return MCPClientConfig(
            name=data.get('name', ''),
            description=data.get('description', ''),
            transport=data.get('transport', 'stdio'),
            server_url=data.get('server_url', ''),
            auto_connect=data.get('auto_connect', False),
            timeout=data.get('timeout', 30),
            retry_attempts=data.get('retry_attempts', 3),
            retry_delay=data.get('retry_delay', 1)
        )
    
    def get_server_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name"""
        if not self.config:
            self.load_config()
        
        return self.config.servers.get(name)
    
    def get_client_config(self, name: str) -> Optional[MCPClientConfig]:
        """Get client configuration by name"""
        if not self.config:
            self.load_config()
        
        return self.config.clients.get(name)
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled server configurations"""
        if not self.config:
            self.load_config()
        
        return [
            server for server in self.config.servers.values()
            if server.enabled
        ]
    
    def get_auto_connect_clients(self) -> List[MCPClientConfig]:
        """Get list of client configurations with auto_connect enabled"""
        if not self.config:
            self.load_config()
        
        return [
            client for client in self.config.clients.values()
            if client.auto_connect
        ]
    
    def is_mcp_enabled(self) -> bool:
        """Check if MCP is enabled"""
        if not self.config:
            self.load_config()
        
        return self.config.enabled


# Singleton instance
_mcp_config_service: Optional[MCPConfigService] = None


def get_mcp_config_service() -> MCPConfigService:
    """Get the singleton MCPConfigService instance"""
    global _mcp_config_service
    if _mcp_config_service is None:
        _mcp_config_service = MCPConfigService()
    return _mcp_config_service


def get_mcp_config() -> MCPConfig:
    """Get MCP configuration"""
    service = get_mcp_config_service()
    return service.config or service.load_config()