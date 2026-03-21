# MCP (Model Context Protocol) 使用指南

## 概述

MCP (Model Context Protocol) 是标准化协议，用于连接AI模型与外部工具和数据源。RANGEN系统实现了MCP客户端和服务器功能。

## 架构设计

### MCP组件

| 组件 | 文件位置 | 用途 | 状态 |
|------|----------|------|------|
| **MCP协议** | `src/utils/mcp_protocol.py` | MCP协议实现 | 🟢 生产 |
| **MCP客户端** | `src/gateway/mcp/__init__.py` | MCP客户端 | 🟢 生产 |
| **MCP路由** | `src/access/api/mcp_routes.py` | MCP API路由 | 🟢 生产 |
| **MCP配置服务** | `src/services/mcp_config_service.py` | MCP配置管理 | 🟢 生产 |
| **MCP服务器管理** | `src/services/mcp_server_manager.py` | MCP服务器管理 | 🟢 生产 |
| **In-Process MCP** | `src/agents/execution_tools/agents/in_process_mcp.py` | 进程内MCP | 🟢 生产 |
| **4层桥接** | `src/agents/execution_tools/core/mcp_four_layer_bridge.py` | 四层桥接 | 🟡 实验 |

## 配置管理

### 配置文件

MCP配置位于 `config/mcp_config.yaml` 或环境变量配置：

```yaml
mcp:
  enabled: true
  log_level: "INFO"
  server_manager:
    enabled: true
```

## 使用示例

### 1. 使用MCP客户端

```python
from src.gateway.mcp import MCPClient

client = MCPClient(server_url="http://localhost:8080")
result = await client.call_tool("tool_name", {"param": "value"})
```

### 2. 使用MCP路由

```python
from src.access.api.mcp_routes import router

# MCP API路由已集成到主应用中
# 访问 /api/mcp/* 端点
```

## 目录结构

```
src/
├── gateway/
│   └── mcp/
│       └── __init__.py         # MCP客户端
├── services/
│   ├── mcp_config_service.py   # 配置服务
│   └── mcp_server_manager.py   # 服务器管理
├── utils/
│   └── mcp_protocol.py         # 协议实现
├── access/
│   └── api/
│       └── mcp_routes.py       # API路由
├── agents/
│   └── execution_tools/
│       ├── agents/
│       │   └── in_process_mcp.py  # 进程内MCP
│       └── core/
│           └── mcp_four_layer_bridge.py  # 4层桥接
└── kms/
    └── pageindex_mcp.py        # KMS MCP集成
```

---

*最后更新: 2026-03-22*
