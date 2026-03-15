# 浏览器可视化使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_langgraph.txt
```

### 2. 启动可视化服务器

**方式1：使用启动脚本（推荐）**

```bash
python examples/start_visualization_server.py
```

**方式2：直接运行模块**

```bash
python -m src.visualization.browser_server --port 8080
```

**方式3：在代码中集成**

```python
from src.visualization.browser_server import BrowserVisualizationServer

# 创建服务器
server = BrowserVisualizationServer(port=8080)

# 启动服务器（同步方式）
server.run()

# 或异步方式
import asyncio
asyncio.run(server.start())
```

### 3. 访问可视化界面

在浏览器中打开：`http://localhost:8080`

## 功能特性

### 当前支持的功能

✅ **工作流图可视化**
- 自动加载 LangGraph 工作流图（如果已初始化）
- 支持传统流程的可视化（即使未使用 LangGraph）
- 使用 Mermaid.js 渲染流程图

✅ **实时状态追踪**
- WebSocket 实时推送节点执行状态
- 节点状态高亮（运行中/已完成/错误）
- 执行时间线显示

✅ **执行控制**
- 输入查询并执行工作流
- 查看执行状态
- 停止执行

### 后续增强功能（计划中）

- 历史执行记录查看
- 断点调试功能
- 状态回放
- 导出执行报告
- 性能图表（Chart.js）

## 集成到现有系统

### 在 UnifiedResearchSystem 中启用可视化

```python
import os
from src.unified_research_system import create_unified_research_system
from src.visualization.browser_server import start_visualization_server

async def main():
    # 创建系统实例
    system = await create_unified_research_system()
    
    # 启用可视化（开发模式默认启用）
    enable_viz = os.getenv('ENABLE_BROWSER_VISUALIZATION', 'true').lower() == 'true'
    if enable_viz:
        workflow = getattr(system, '_langgraph_workflow', None)
        await start_visualization_server(
            workflow=workflow,  # 可以为 None，系统会显示传统流程
            system=system,      # 传入系统实例，支持传统流程可视化
            port=8080
        )
    
    # 执行查询...
    result = await system.execute_research(request)
    
    return result
```

### 环境变量配置

在 `.env` 文件中添加：

```bash
# 启用浏览器可视化（默认：true）
ENABLE_BROWSER_VISUALIZATION=true

# 可视化服务器端口（默认：8080）
VISUALIZATION_PORT=8080

# 开发模式（自动启用可视化）
ENV=development
```

## API 接口

### GET /api/workflow/graph

获取工作流图结构（Mermaid 格式）

**响应示例**：
```json
{
  "mermaid": "graph TD\n    A[Entry] --> B[Route Query]...",
  "nodes": ["Entry", "Route Query", ...],
  "edges": [...],
  "has_workflow": true
}
```

### POST /api/workflow/execute

执行工作流

**请求体**：
```json
{
  "state": {
    "query": "What is the capital of France?"
  }
}
```

**响应**：
```json
{
  "execution_id": "uuid-string",
  "status": "started"
}
```

### GET /api/execution/{execution_id}

获取执行状态

**响应**：
```json
{
  "id": "execution-id",
  "status": "running",
  "nodes": [...],
  "start_time": 1234567890.0
}
```

### WebSocket /ws/{execution_id}

实时推送执行状态更新

**消息格式**：
```json
{
  "execution_id": "uuid-string",
  "type": "node_update",
  "data": {
    "name": "node_name",
    "timestamp": 1234567890.0,
    "status": "running"
  }
}
```

## 故障排除

### 问题1：无法访问可视化界面

**检查**：
1. 确认服务器已启动
2. 检查端口是否被占用
3. 确认防火墙设置

**解决**：
```bash
# 检查端口占用
lsof -i :8080

# 使用其他端口
python examples/start_visualization_server.py
# 然后设置环境变量 VISUALIZATION_PORT=8081
```

### 问题2：WebSocket 连接失败

**检查**：
1. 确认 WebSocket 支持
2. 检查浏览器控制台错误

**解决**：
- 使用现代浏览器（Chrome、Firefox、Safari）
- 检查网络代理设置

### 问题3：工作流图不显示

**检查**：
1. 确认 LangGraph 工作流已初始化
2. 检查 API 响应

**解决**：
- 即使没有 LangGraph 工作流，也会显示传统流程的可视化
- 查看浏览器控制台的错误信息

## 开发计划

### 阶段0-1：基础可视化系统 ✅ 已完成
- FastAPI 服务器
- 基础 API
- 前端页面（HTML + Mermaid.js）

### 阶段0-2：实时状态追踪（进行中）
- WebSocket 服务器
- 状态追踪器
- 前端实时更新

### 阶段0-3：集成到现有系统（进行中）
- 可视化钩子
- 启动脚本
- 文档完善

### 后续增强
- 历史执行记录
- 断点调试
- 状态回放
- 性能图表

## 贡献

欢迎提交问题和改进建议！

