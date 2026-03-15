# MCP (Model Context Protocol) 使用指南

## 概述

MCP (Model Context Protocol) 是Anthropic提出的标准化协议，用于连接AI模型与外部工具和数据源。RANGEN系统实现了完整的MCP服务器和客户端，允许将本地工具通过MCP协议暴露给系统使用。

## 架构设计

### MCP服务器类型

RANGEN系统实现了三种MCP服务器：

1. **主MCP服务器** (`src/agents/tools/mcp_server.py`)
   - 暴露RANGEN内部工具
   - 支持stdio和HTTP传输
   - 自动注册所有已注册的工具

2. **本地演示MCP服务器** (`src/agents/tools/mcp_local_server.py`)
   - 提供基本工具：计算器、回显、时间、随机数
   - 用于演示和测试

3. **独立MCP服务器** (`src/agents/tools/standalone_mcp_server.py`)
   - 不依赖RANGEN系统
   - 独立运行的工具集

### MCP客户端
- **MCP客户端** (`src/gateway/mcp/__init__.py`)
  - 连接到MCP服务器
  - 调用MCP工具和资源
  - 支持stdio和HTTP传输

### MCP协议实现
- **MCP协议** (`src/utils/mcp_protocol.py`)
  - 完整的MCP协议标准实现
  - 上下文管理和协议通信

## 配置管理

### 配置文件

MCP配置位于 `config/mcp_config.yaml`，主要包含以下部分：

```yaml
mcp:
  enabled: true
  log_level: "INFO"
  
  server:
    main:
      enabled: true
      name: "rangen-tools"
      transport: "stdio"
      stdio:
        command: "python -m src.agents.tools.mcp_server"
      http:
        enabled: true
        host: "0.0.0.0"
        port: 8080
        endpoint: "http://localhost:8080"
    
    local_demo:
      enabled: true
      name: "local-tools"
      transport: "stdio"
      stdio:
        command: "python -m src.agents.tools.mcp_local_server"
  
  client:
    servers:
      - name: "rangen-tools"
        description: "RANGEN Internal Tools"
        transport: "stdio"
        server_url: "python -m src.agents.tools.mcp_server"
        auto_connect: true
      
      - name: "local-demo"
        description: "Local Demo Tools"
        transport: "stdio"
        server_url: "python -m src.agents.tools.mcp_local_server"
        auto_connect: false
  
  integration:
    auto_start_servers: true
    auto_register_tools: true
    enable_context_protocol: true
```

### 环境配置

MCP配置也集成到环境配置文件中（`config/environments/development.yaml`）：

```yaml
integrations:
  mcp:
    enabled: true
    # ... 配置详情
```

## 快速开始

### 启动MCP服务器

#### 方法1：通过API服务器自动启动

当启动RANGEN API服务器时，MCP服务器会自动启动：

```bash
python src/api/server.py
```

在启动日志中查看MCP服务器状态：
```
2026-03-08 10:12:17 - src.services.mcp_server_manager - INFO - MCP server 'main' started successfully (PID: 23325)
2026-03-08 10:12:17 - src.services.mcp_server_manager - INFO - MCP server 'local_demo' started successfully (PID: 23326)
```

#### 方法2：手动启动MCP服务器

```bash
# 启动主MCP服务器
python -m src.agents.tools.mcp_server

# 启动本地演示MCP服务器
python -m src.agents.tools.mcp_local_server

# 启动独立MCP服务器
python -m src.agents.tools.standalone_mcp_server
```

#### 方法3：使用HTTP传输

```bash
# 启动HTTP MCP服务器
python -m src.agents.tools.mcp_server --http --host 0.0.0.0 --port 8080
```

### 使用MCP客户端

#### 连接到MCP服务器

```python
import asyncio
from src.gateway.mcp import MCPConnection, MCPClient, get_mcp_registry

async def example():
    # 创建连接
    connection = MCPConnection(
        name="local-tools",
        description="Local Demo Tools",
        transport="stdio",
        server_url="python -m src.agents.tools.mcp_local_server"
    )
    
    # 创建客户端
    client = MCPClient(connection)
    
    # 连接
    connected = await client.connect()
    if connected:
        print("Connected to MCP server")
        
        # 获取工具列表
        tools = await client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name} - {tool.description}")
        
        # 调用工具
        result = await client.call_tool("calculator", {"expression": "2+3*4"})
        print(f"Result: {result}")
        
        # 断开连接
        await client.disconnect()

asyncio.run(example())
```

#### 使用MCP注册表

```python
import asyncio
from src.gateway.mcp import get_mcp_registry

async def example():
    registry = get_mcp_registry()
    
    # 添加服务器
    conn_id = await registry.add_server(
        name="local-tools",
        server_url="python -m src.agents.tools.mcp_local_server",
        transport="stdio"
    )
    
    # 获取工具列表
    tools = registry.get_tools(conn_id)
    
    # 调用工具
    result = await registry.call_tool(conn_id, "calculator", {"expression": "100/5+20"})
    print(f"Result: {result}")

asyncio.run(example())
```

## API管理接口

RANGEN提供了完整的MCP管理API：

### 获取MCP状态
```
GET /mcp/status
```
返回MCP系统状态、服务器数量、运行状态等。

### 列出MCP服务器
```
GET /mcp/servers
```
返回所有MCP服务器的详细状态。

### 管理MCP服务器
```
POST /mcp/servers/{server_name}/{action}
```
支持的操作：`start`, `stop`, `restart`

### 获取MCP配置
```
GET /mcp/config
```
返回完整的MCP配置信息。

### 健康检查
```
GET /mcp/health
```
返回MCP系统健康状态。

## 集成示例

### 将工具暴露为MCP服务

#### 示例：创建自定义MCP工具

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

# 创建MCP服务器
server = Server("my-tools")

# 注册工具
@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="custom_tool",
            description="自定义工具示例",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "输入文本"}
                },
                "required": ["input"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "custom_tool":
        input_text = arguments.get("input", "")
        result = f"处理结果: {input_text.upper()}"
        return [TextContent(type="text", text=result)]

# 运行服务器
async def main():
    async with server.stdio_server() as session:
        await session.run()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 集成现有RANGEN工具

RANGEN主MCP服务器会自动暴露所有已注册的工具。要查看已注册的工具：

```python
from src.agents.tools.tool_registry import get_tool_registry

registry = get_tool_registry()
tools = registry.list_tools()
for tool in tools:
    print(f"Tool: {tool.name} - {tool.description}")
```

## 高级功能

### HTTP传输支持

MCP支持HTTP传输，允许远程访问MCP工具：

```python
# 客户端连接HTTP MCP服务器
connection = MCPConnection(
    name="remote-tools",
    description="远程MCP工具",
    transport="http",
    server_url="http://localhost:8080"
)

client = MCPClient(connection)
await client.connect()
```

### 资源(Resources)和提示(Prompts)支持

MCP协议支持资源和提示的暴露：

```python
# 读取资源
resource_content = await client.read_resource("resource://example/document.txt")

# 获取提示列表
# (提示功能将在后续版本中实现)
```

### 上下文协议集成

MCP协议与RANGEN上下文管理系统集成：

```python
from src.utils.mcp_protocol import MCPProtocolHandler

mcp_handler = MCPProtocolHandler()

# 导出上下文到MCP
context_id = mcp_handler.export_context(session_id="test-session")

# 从MCP导入上下文
context = mcp_handler.import_context(context_id)
```

## 监控和管理

### 查看MCP服务器状态

```bash
# 通过API查看
curl http://localhost:8000/mcp/servers

# 通过日志查看
tail -f logs/mcp.log
```

### 性能监控

MCP系统提供以下监控指标：
- 请求计数
- 错误计数
- 响应时间
- 连接状态

### 故障排除

#### 常见问题

1. **MCP服务器启动失败**
   - 检查依赖项是否安装：`pip install transformers torch mcp`
   - 检查端口是否被占用
   - 查看日志获取详细错误信息

2. **连接失败**
   - 检查服务器URL是否正确
   - 验证传输协议（stdio/http）
   - 检查防火墙设置（HTTP传输）

3. **工具调用失败**
   - 检查工具名称是否正确
   - 验证输入参数格式
   - 查看服务器日志

#### 日志配置

MCP日志级别可在配置中调整：
```yaml
mcp:
  log_level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

## 安全考虑

### 认证和授权

HTTP MCP服务器支持API密钥认证（需要配置）：
```yaml
mcp:
  security:
    authentication_enabled: true
    api_key: "your-secret-api-key"
```

### 网络隔离

建议将MCP服务器部署在受信任的网络环境中：
- 使用内网IP地址
- 配置防火墙规则
- 启用HTTPS（未来版本）

## 扩展开发

### 添加新的MCP服务器

1. 创建新的MCP服务器文件
2. 实现工具列表和调用处理
3. 添加到配置文件中
4. 集成到系统启动流程

### 自定义工具暴露

通过继承`BaseTool`类并注册到工具注册表，工具会自动暴露给MCP服务器：

```python
from src.agents.tools.base_tool import BaseTool
from src.agents.tools.tool_registry import get_tool_registry

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "自定义工具"
    
    async def execute(self, **kwargs):
        # 工具逻辑
        return "结果"

# 注册工具
registry = get_tool_registry()
registry.register_tool(CustomTool())
```

## 可视化界面管理

RANGEN系统提供了完整的前端监控界面，用于可视化管理和监控MCP服务器和工具。

### 前端监控系统

前端监控系统是一个独立的Vue.js 3应用程序，集成了以下功能：

1. **MCP服务器管理** - 查看和管理所有MCP服务器的状态
2. **工具管理** - 查看系统内部工具和数据库工具
3. **实时监控** - 监控系统运行状态和性能指标

### 访问前端监控系统

#### 启动前端监控系统

```bash
# 进入前端监控目录
cd frontend_monitor

# 使用启动脚本（推荐）
./start.sh

# 或者手动启动
# 启动后端服务（端口5000或5001）
cd backend
python app.py

# 启动前端服务（端口3000）
npm run dev
```

#### 访问界面

启动后，在浏览器中访问：
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:5000 (或5001)

### MCP管理界面功能

在前端监控系统中，点击"MCP管理"标签页，可以：

1. **查看MCP系统状态**
   - 总体状态：启用/禁用
   - 服务器数量：运行中/已停止
   - 健康状态

2. **管理MCP服务器**
   - 启动/停止/重启MCP服务器
   - 查看服务器详情
   - 监控服务器日志

3. **查看MCP配置**
   - 完整的MCP配置信息
   - 传输协议设置
   - 服务器参数

4. **健康检查**
   - 实时健康状态监控
   - 错误和警告信息

### 工具管理界面功能

在前端监控系统中，点击"工具管理"标签页，可以：

1. **查看内部工具**
   - 12个预注册的内部工具列表
   - 工具分类：检索类、推理类、生成类、实用类
   - 工具描述和技能映射

2. **查看数据库工具**
   - 数据库中存储的工具记录
   - 工具状态（活跃/禁用）
   - 创建时间和类型信息

3. **搜索和筛选**
   - 按名称、描述、分类搜索工具
   - 按状态筛选数据库工具

4. **工具详情**
   - 查看工具详细信息
   - 技能映射关系
   - 测试工具功能（待实现）

### 使用示例

#### 示例1：监控MCP服务器状态

1. 启动RANGEN主API服务器（端口8000）
2. 启动前端监控系统（端口3000）
3. 在浏览器中访问 http://localhost:3000
4. 点击"MCP管理"标签页
5. 查看所有MCP服务器的运行状态

#### 示例2：管理MCP服务器

1. 在"MCP管理"界面中，找到要管理的服务器
2. 点击"启动"、"停止"或"重启"按钮
3. 查看操作结果和服务器状态变化

#### 示例3：查看系统工具

1. 在"工具管理"界面中，默认显示内部工具
2. 使用搜索框查找特定工具
3. 点击"详情"按钮查看工具详细信息
4. 切换到"数据库工具"视图查看数据库中的工具记录

### 技术架构

前端监控系统采用以下技术栈：

- **前端框架**: Vue.js 3 + Composition API
- **UI组件库**: Element Plus
- **构建工具**: Vite
- **后端框架**: Flask (Python)
- **API代理**: 通过Flask后端代理到RANGEN主API

### 故障排除

#### 前端无法加载MCP数据

1. 检查RANGEN主API是否运行（端口8000）
2. 检查前端后端服务是否正常（端口5000/5001）
3. 查看浏览器开发者工具的控制台日志
4. 检查网络请求是否被代理正确转发

#### 工具列表为空

1. 确认RANGEN系统已正确初始化
2. 检查工具注册表是否已加载工具
3. 查看后端日志是否有错误信息

#### 界面显示异常

1. 清除浏览器缓存
2. 重新启动前端服务
3. 检查Node.js和npm版本兼容性

## 参考链接

- [MCP官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [RANGEN文档](../README.md)

---

**注意**: MCP功能仍在积极开发中，API可能会有变化。建议定期查看更新日志。