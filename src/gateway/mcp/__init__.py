"""
MCP (Model Context Protocol) Support

MCP是Anthropic提出的标准化协议，用于连接AI模型与外部工具和数据源
参考: https://modelcontextprotocol.io/
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class MCPMessageType(Enum):
    """MCP消息类型"""
    JSONRPC = "jsonrpc"
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResource:
    """MCP资源"""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    
    def to_dict(self) -> Dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


@dataclass
class MCPPrompt:
    """MCP提示模板"""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


@dataclass
class MCPConnection:
    """MCP连接"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    server_url: str = ""
    transport: str = "stdio"  # stdio, http, websocket
    
    # 能力
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)
    prompts: List[MCPPrompt] = field(default_factory=list)
    
    # 状态
    connected: bool = False
    initialized: bool = False
    last_error: str = ""
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)


class MCPClient:
    """
    MCP客户端
    
    连接到MCP服务器并调用其工具/资源
    """
    
    def __init__(self, connection: MCPConnection):
        self.connection = connection
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stdin: Optional[asyncio.StreamWriter] = None
        self._stdout: Optional[asyncio.StreamReader] = None
        self._request_id = 0
        self._pending_requests: Dict[str, asyncio.Future] = {}
    
    async def connect(self) -> bool:
        """连接到MCP服务器"""
        try:
            if self.connection.transport == "stdio":
                return await self._connect_stdio()
            elif self.connection.transport == "http":
                return await self._connect_http()
            else:
                logger.error(f"Unsupported transport: {self.connection.transport}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connection.last_error = str(e)
            return False
    
    async def _connect_stdio(self) -> bool:
        """通过stdio连接"""
        # 检查服务器命令
        if not self.connection.server_url:
            logger.error("MCP server command not specified")
            return False
        
        # 启动进程
        try:
            self._process = await asyncio.create_subprocess_shell(
                self.connection.server_url,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self._stdin = self._process.stdin
            self._stdout = self._process.stdout
            
            # 初始化
            success = await self.initialize()
            
            if success:
                self.connection.connected = True
                logger.info(f"Connected to MCP server: {self.connection.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def _connect_http(self) -> bool:
        """通过HTTP连接"""
        # 🚀 Gateway 能力扩展：实现 HTTP transport
        if not self.connection.server_url:
            logger.error("MCP server URL not specified")
            return False
        
        try:
            import aiohttp
            
            # 创建 HTTP 会话
            self._http_session = aiohttp.ClientSession()
            
            # 尝试初始化连接
            # HTTP transport 需要服务器支持 SSE (Server-Sent Events)
            # 或者标准的 JSON-RPC over HTTP
            
            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "clientInfo": {
                        "name": "rangen-gateway",
                        "version": "1.0.0"
                    }
                }
            }
            
            # 发送请求
            async with self._http_session.post(
                self.connection.server_url,
                json=init_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        self.connection.connected = True
                        logger.info(f"Connected to MCP server via HTTP: {self.connection.name}")
                        return True
                
            logger.warning(f"HTTP connection failed with status: {response.status}")
            return False
            
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
            return False
        except Exception as e:
            logger.error(f"Failed to connect via HTTP: {e}")
            self.connection.last_error = str(e)
            return False
        """通过HTTP连接"""
        # TODO: 实现HTTP transport
        logger.error("HTTP transport not implemented yet")
        return False
    
    async def initialize(self) -> bool:
        """初始化MCP连接"""
        if not self._stdin or not self._stdout:
            return False
        
        # 发送initialize请求
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "rangen-gateway",
                    "version": "1.0.0"
                }
            }
        }
        
        # 发送请求
        await self._send(request)
        
        # 等待响应
        try:
            response = await self._receive()
            
            if "result" in response:
                self.connection.initialized = True
                
                # 获取能力
                capabilities = response.get("result", {}).get("capabilities", {})
                
                # 获取工具列表
                if capabilities.get("tools"):
                    await self.list_tools()
                
                return True
            
        except Exception as e:
            logger.error(f"Initialize failed: {e}")
        
        return False
    
    async def list_tools(self) -> List[MCPTool]:
        """获取工具列表"""
        if not self.connection.connected:
            return []
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list"
        }
        
        await self._send(request)
        
        try:
            response = await self._receive()
            tools_data = response.get("result", {}).get("tools", [])
            
            self.connection.tools = [
                MCPTool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {})
                )
                for t in tools_data
            ]
            
            logger.info(f"Loaded {len(self.connection.tools)} tools from MCP server")
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
        
        return self.connection.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self.connection.connected:
            raise RuntimeError("Not connected to MCP server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        await self._send(request)
        
        try:
            response = await self._receive()
            result = response.get("result", {})
            
            # 处理工具响应
            if "content" in result:
                return result["content"]
            
            return result
            
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise
    
    async def read_resource(self, uri: str) -> str:
        """读取资源"""
        if not self.connection.connected:
            raise RuntimeError("Not connected to MCP server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        await self._send(request)
        
        try:
            response = await self._receive()
            result = response.get("result", {})
            
            if "contents" in result:
                contents = result["contents"]
                if contents and "text" in contents[0]:
                    return contents[0]["text"]
            
            return ""
            
        except Exception as e:
            logger.error(f"Resource read failed: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        if self._process:
            self._process.terminate()
            await self._process.wait()
        
        self.connection.connected = False
        self.connection.initialized = False
        logger.info(f"Disconnected from MCP server: {self.connection.name}")
    
    def _next_id(self) -> str:
        """生成请求ID"""
        self._request_id += 1
        return str(self._request_id)
    
    async def _send(self, request: Dict):
        """发送请求"""
        if not self._stdin:
            return
        
        message = json.dumps(request) + "\n"
        self._stdin.write(message.encode())
        await self._stdin.drain()
    
    async def _receive(self) -> Dict:
        """接收响应"""
        if not self._stdout:
            return {}
        
        line = await self._stdout.readline()
        
        if not line:
            return {}
        
        return json.loads(line.decode())


class MCPRegistry:
    """
    MCP注册表
    
    管理所有MCP连接
    """
    
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self.clients: Dict[str, MCPClient] = {}
    
    async def add_server(
        self,
        name: str,
        server_url: str,
        transport: str = "stdio"
    ) -> str:
        """添加MCP服务器"""
        connection = MCPConnection(
            name=name,
            server_url=server_url,
            transport=transport
        )
        
        self.connections[connection.id] = connection
        
        # 创建客户端并连接
        client = MCPClient(connection)
        success = await client.connect()
        
        if success:
            self.clients[connection.id] = client
            logger.info(f"Added MCP server: {name}")
            return connection.id
        else:
            del self.connections[connection.id]
            raise RuntimeError(f"Failed to connect to MCP server: {name}")
    
    async def remove_server(self, connection_id: str):
        """移除MCP服务器"""
        if connection_id in self.clients:
            await self.clients[connection_id].disconnect()
            del self.clients[connection_id]
        
        if connection_id in self.connections:
            del self.connections[connection_id]
        
        logger.info(f"Removed MCP server: {connection_id}")
    
    def get_tools(self, connection_id: str) -> List[MCPTool]:
        """获取服务器工具列表"""
        connection = self.connections.get(connection_id)
        if connection:
            return connection.tools
        return []
    
    def get_all_tools(self) -> Dict[str, List[MCPTool]]:
        """获取所有工具"""
        result = {}
        for conn_id, conn in self.connections.items():
            if conn.tools:
                result[conn.name] = conn.tools
        return result
    
    async def call_tool(
        self,
        connection_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """调用工具"""
        client = self.clients.get(connection_id)
        if not client:
            raise ValueError(f"Connection not found: {connection_id}")
        
        return await client.call_tool(tool_name, arguments)
    
    def list_connections(self) -> List[Dict]:
        """列出所有连接"""
        return [
            {
                "id": conn.id,
                "name": conn.name,
                "connected": conn.connected,
                "tools_count": len(conn.tools),
                "resources_count": len(conn.resources)
            }
            for conn in self.connections.values()
        ]


# ==================== 便捷函数 ====================

_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """获取MCP注册表"""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry


async def add_mcp_server(
    name: str,
    server_url: str,
    transport: str = "stdio"
) -> str:
    """添加MCP服务器"""
    registry = get_mcp_registry()
    return await registry.add_server(name, server_url, transport)
