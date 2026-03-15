# 📡 API 数据格式参考

> RANGEN 系统 REST API 的完整请求响应格式、端点定义和数据模型

## 🎯 概述

RANGEN 系统提供基于 FastAPI 的 RESTful API 接口，支持智能体管理、模型管理、对话处理、系统监控等功能。本文档详细说明所有 API 端点的数据格式和使用方法。

### 1.1 文档目标
- 提供完整的 API 端点参考
- 详细说明请求和响应数据格式
- 解释认证和授权机制
- 提供使用示例和最佳实践

### 1.2 目标读者
- API 集成开发人员
- 系统管理员和运维工程师
- 第三方系统集成商
- 技术架构师和解决方案工程师

### 1.3 API 基础信息
- **基础 URL**: `http://localhost:8000` (开发环境)
- **API 版本**: `v1` (路径前缀: `/api/v1`)
- **数据格式**: JSON (UTF-8 编码)
- **认证方式**: API Key (Bearer Token) 或 JWT Token
- **文档地址**: `/docs` (Swagger UI), `/redoc` (ReDoc)

## 🔐 认证和授权

### 2.1 认证方式

#### 2.1.1 API Key 认证
大多数端点支持 API Key 认证，需要在请求头中提供：

```http
Authorization: Bearer rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

API Key 格式为 `rang_` 后跟 32 字符的随机字符串。

#### 2.1.2 JWT Token 认证
支持 JWT Token 认证的用户端点：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 2.1.3 权限级别
RANGEN 系统定义了三层权限级别：

| 权限级别 | 描述 | 适用端点 |
|----------|------|----------|
| **read** | 读取权限 | 查询类端点、健康检查 |
| **write** | 写入权限 | 创建、更新、执行类端点 |
| **admin** | 管理员权限 | 系统管理、诊断、配置修改 |

### 2.2 认证错误响应
认证失败时返回 HTTP 401 状态码：

```json
{
  "detail": "未提供认证信息或认证失败"
}
```

权限不足时返回 HTTP 403 状态码：

```json
{
  "detail": "权限不足"
}
```

### 2.3 获取 API Key

#### 2.3.1 环境变量配置
系统启动时可通过环境变量配置默认 API Key：

```bash
export RANGEN_API_KEY="rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

#### 2.3.2 动态创建 API Key
通过管理接口创建新的 API Key（需要管理员权限）：

```http
POST /api/v1/auth/keys
Authorization: Bearer <admin-key>

{
  "name": "production-key",
  "permissions": ["read", "write"],
  "expires_in_days": 30
}
```

响应：
```json
{
  "api_key": "rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "name": "production-key",
  "permissions": ["read", "write"],
  "expires_at": "2026-04-07T10:30:00Z",
  "created_at": "2026-03-07T10:30:00Z"
}
```

## 📡 核心 API 端点

### 3.1 系统状态端点

#### 3.1.1 健康检查
**端点**: `GET /health`

无需认证，返回系统基础状态。

**响应格式**:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "timestamp": 1741332600.123456
}
```

#### 3.1.2 认证健康检查
**端点**: `GET /health/auth`

需要 read 权限，返回详细系统状态。

**请求头**:
```http
Authorization: Bearer <api-key>
```

**响应格式**:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "timestamp": 1741332600.123456,
  "authenticated_as": "api-key-name",
  "coordinator_initialized": true,
  "chat_backend": "coordinator"
}
```

#### 3.1.3 系统诊断
**端点**: `GET /diag`

需要 admin 权限，返回详细系统诊断信息。

**请求头**:
```http
Authorization: Bearer <admin-api-key>
```

**响应格式**:
```json
{
  "timestamp": 1741332600.123456,
  "environment": {
    "LLM_PROVIDER": "deepseek",
    "PYTHONPATH": "/path/to/project",
    "RANGEN_USE_UNIFIED_RESEARCH": "false"
  },
  "system": {
    "coordinator_status": "running",
    "tool_registry_count": 5,
    "active_sessions": 3
  },
  "resources": {
    "cpu_percent": 12.5,
    "memory_percent": 45.3,
    "disk_usage_percent": 28.7
  }
}
```

### 3.2 对话处理端点

#### 3.2.1 对话请求
**端点**: `POST /chat`

处理用户查询，返回智能体回答和推理步骤。

**请求头**:
```http
Authorization: Bearer <api-key>
Content-Type: application/json
```

**请求格式**:
```json
{
  "query": "什么是机器学习？",
  "session_id": "session_123456",
  "context": {
    "user_id": "user_001",
    "language": "zh-CN",
    "preferences": {
      "detailed_explanations": true
    }
  }
}
```

**字段说明**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `query` | string | 是 | 用户查询文本 |
| `session_id` | string | 否 | 会话 ID，用于上下文保持 |
| `context` | object | 否 | 额外上下文信息 |

**响应格式**:
```json
{
  "answer": "机器学习是人工智能的一个分支，它使计算机系统能够从数据中学习并改进性能，而无需显式编程。",
  "steps": [
    "分析查询：识别用户询问的是机器学习的定义",
    "检索知识：从知识库中查找机器学习相关概念",
    "组织答案：整理机器学习的核心定义和特点",
    "生成回答：用通俗易懂的语言解释机器学习"
  ],
  "status": "completed",
  "error": null
}
```

**字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| `answer` | string | 最终回答文本 |
| `steps` | array | 推理步骤列表 |
| `status` | string | 执行状态：`completed`, `failed` |
| `error` | string/null | 错误信息（如果执行失败） |

#### 3.2.2 流式对话响应
**端点**: `POST /chat/stream`

支持 Server-Sent Events (SSE) 的流式响应。

**请求格式**: 同 `/chat` 端点

**响应格式** (流式):
```text
event: chunk
data: {"type": "thinking", "content": "正在分析问题..."}

event: chunk
data: {"type": "answer", "content": "机器学习是"}

event: chunk
data: {"type": "answer", "content": "人工智能的一个分支"}

event: done
data: {"status": "completed", "steps": [...], "full_answer": "..."}
```

### 3.3 智能体管理端点

#### 3.3.1 创建智能体
**端点**: `POST /api/v1/agents`

创建新的智能体。

**请求头**:
```http
Authorization: Bearer <write-api-key>
Content-Type: application/json
```

**请求格式**:
```json
{
  "name": "数据分析专家",
  "description": "专门处理数据分析和可视化任务的智能体",
  "type": "data_analysis",
  "skills": ["skill_data_analysis", "skill_visualization"],
  "tools": ["tool_pandas", "tool_matplotlib"],
  "config": {
    "max_iterations": 5,
    "temperature": 0.7,
    "enable_retry": true
  }
}
```

**响应格式**:
```json
{
  "id": "agent_123456",
  "name": "数据分析专家",
  "type": "data_analysis",
  "description": "专门处理数据分析和可视化任务的智能体",
  "skills": ["skill_data_analysis", "skill_visualization"],
  "tools": ["tool_pandas", "tool_matplotlib"],
  "status": "active",
  "created_at": "2026-03-07T10:30:00Z",
  "updated_at": "2026-03-07T10:30:00Z",
  "reference_count": 0
}
```

#### 3.3.2 获取智能体列表
**端点**: `GET /api/v1/agents`

获取智能体列表，支持状态过滤。

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| `status` | string | 过滤状态：`active`, `inactive`, `all` |

**响应格式**:
```json
{
  "agents": [
    {
      "id": "agent_123456",
      "name": "数据分析专家",
      "type": "data_analysis",
      "description": "专门处理数据分析和可视化任务的智能体",
      "skills": ["skill_data_analysis", "skill_visualization"],
      "tools": ["tool_pandas", "tool_matplotlib"],
      "status": "active",
      "created_at": "2026-03-07T10:30:00Z",
      "updated_at": "2026-03-07T10:30:00Z",
      "reference_count": 5
    }
  ],
  "total": 1
}
```

#### 3.3.3 获取智能体详情
**端点**: `GET /api/v1/agents/{agent_id}`

获取指定智能体的详细信息。

**响应格式**: 同创建智能体响应格式

#### 3.3.4 更新智能体
**端点**: `PUT /api/v1/agents/{agent_id}`

更新智能体信息。

**请求格式**:
```json
{
  "name": "高级数据分析专家",
  "description": "升级版数据分析智能体，支持更复杂的数据处理",
  "status": "active"
}
```

#### 3.3.5 删除智能体
**端点**: `DELETE /api/v1/agents/{agent_id}`

删除智能体（软删除，标记为 inactive）。

### 3.4 技能管理端点

#### 3.4.1 创建技能
**端点**: `POST /api/v1/skills`

创建新的技能。

**请求格式**:
```json
{
  "name": "数据可视化",
  "description": "将数据转换为图表和可视化报告",
  "tools": ["tool_matplotlib", "tool_seaborn", "tool_plotly"],
  "config_path": "config/skills/visualization.yaml"
}
```

**响应格式**:
```json
{
  "id": "skill_123456",
  "name": "数据可视化",
  "description": "将数据转换为图表和可视化报告",
  "tools": ["tool_matplotlib", "tool_seaborn", "tool_plotly"],
  "status": "active",
  "created_at": "2026-03-07T10:30:00Z",
  "reference_count": 3
}
```

#### 3.4.2 获取技能列表
**端点**: `GET /api/v1/skills`

获取技能列表。

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| `status` | string | 过滤状态：`active`, `inactive`, `all` |

**响应格式**:
```json
{
  "skills": [
    {
      "id": "skill_123456",
      "name": "数据可视化",
      "description": "将数据转换为图表和可视化报告",
      "tools": ["tool_matplotlib", "tool_seaborn", "tool_plotly"],
      "status": "active",
      "created_at": "2026-03-07T10:30:00Z",
      "reference_count": 3
    }
  ],
  "total": 1
}
```

### 3.5 工具管理端点

#### 3.5.1 获取工具列表
**端点**: `GET /api/v1/tools`

获取可用工具列表。

**响应格式**:
```json
{
  "tools": [
    {
      "id": "tool_matplotlib",
      "name": "Matplotlib",
      "description": "Python 2D绘图库",
      "type": "visualization",
      "status": "active",
      "created_at": "2026-03-07T10:30:00Z"
    },
    {
      "id": "tool_pandas",
      "name": "Pandas",
      "description": "Python数据分析库",
      "type": "data_processing",
      "status": "active",
      "created_at": "2026-03-07T10:30:00Z"
    }
  ],
  "total": 2
}
```

### 3.6 模型管理端点

#### 3.6.1 创建模型提供商
**端点**: `POST /api/v1/models/providers`

创建新的模型提供商。

**请求格式**:
```json
{
  "name": "custom-openai",
  "display_name": "自定义 OpenAI 接口",
  "description": "自定义部署的 OpenAI 兼容接口",
  "website": "https://api.example.com",
  "api_type": "openai_compatible"
}
```

**响应格式**:
```json
{
  "id": "provider_123456",
  "name": "custom-openai",
  "display_name": "自定义 OpenAI 接口",
  "description": "自定义部署的 OpenAI 兼容接口",
  "website": "https://api.example.com",
  "api_type": "openai_compatible",
  "status": "active",
  "created_at": "2026-03-07T10:30:00Z"
}
```

#### 3.6.2 获取模型列表
**端点**: `GET /api/v1/models`

获取可用模型列表。

**响应格式**:
```json
{
  "models": [
    {
      "id": "model_123456",
      "name": "deepseek-chat",
      "display_name": "DeepSeek Chat",
      "provider": "deepseek",
      "description": "DeepSeek 对话模型",
      "capabilities": ["chat", "reasoning", "code"],
      "max_tokens": 8192,
      "status": "active",
      "cost_per_token": 0.000001
    },
    {
      "id": "model_123457",
      "name": "step-3.5-flash",
      "display_name": "Step-3.5-Flash",
      "provider": "stepsflash",
      "description": "高性能低成本模型",
      "capabilities": ["chat", "fast_response"],
      "max_tokens": 4096,
      "status": "active",
      "cost_per_token": 0.0000005
    }
  ],
  "total": 2
}
```

### 3.7 标准作业程序 (SOP) 管理端点

#### 3.7.1 创建 SOP
**端点**: `POST /api/v1/sop`

创建新的标准作业程序。

**请求格式**:
```json
{
  "name": "客户支持工单处理",
  "description": "处理客户支持工单的标准流程",
  "steps": [
    {
      "step": 1,
      "action": "确认工单信息",
      "description": "确认工单的完整信息和客户需求"
    },
    {
      "step": 2,
      "action": "分析问题类型",
      "description": "根据工单内容分析问题类型和优先级"
    },
    {
      "step": 3,
      "action": "执行解决方案",
      "description": "根据问题类型执行相应的解决方案"
    }
  ],
  "triggers": ["customer_support_ticket"],
  "agents": ["agent_support_specialist"]
}
```

#### 3.7.2 执行 SOP
**端点**: `POST /api/v1/sop/{sop_id}/execute`

执行指定的 SOP。

**请求格式**:
```json
{
  "context": {
    "ticket_id": "ticket_123456",
    "customer_id": "customer_789",
    "issue_description": "无法登录系统",
    "priority": "high"
  },
  "parameters": {
    "max_steps": 10,
    "timeout": 300
  }
}
```

### 3.8 自然语言智能体端点

#### 3.8.1 创建自然语言智能体
**端点**: `POST /api/v1/natural-language-agents`

通过自然语言描述创建智能体。

**请求格式**:
```json
{
  "description": "创建一个专门处理财务报表分析的智能体，需要能够读取Excel文件、进行财务比率计算、生成可视化图表。",
  "name": "财务分析助手",
  "constraints": [
    "必须使用安全的数据处理方式",
    "不能修改原始数据文件",
    "所有计算必须可追溯"
  ]
}
```

**响应格式**:
```json
{
  "agent_id": "agent_nl_123456",
  "name": "财务分析助手",
  "description": "专门处理财务报表分析的智能体",
  "generated_skills": ["skill_excel_processing", "skill_financial_analysis", "skill_data_visualization"],
  "generated_tools": ["tool_pandas", "tool_openpyxl", "tool_matplotlib"],
  "status": "created",
  "created_at": "2026-03-07T10:30:00Z"
}
```

## 📊 数据模型定义

### 4.1 通用响应模型

#### 4.1.1 分页响应模型
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

#### 4.1.2 错误响应模型
```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-03-07T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 4.2 核心数据模型

#### 4.2.1 会话模型 (Session)
```json
{
  "session_id": "session_123456",
  "user_id": "user_001",
  "created_at": "2026-03-07T10:30:00Z",
  "last_activity_at": "2026-03-07T10:35:00Z",
  "metadata": {
    "language": "zh-CN",
    "device": "web",
    "ip_address": "192.168.1.100"
  },
  "context": {
    "conversation_history": [],
    "user_preferences": {}
  }
}
```

#### 4.2.2 执行追踪模型 (Execution Trace)
```json
{
  "trace_id": "trace_123456",
  "session_id": "session_123456",
  "query": "什么是机器学习？",
  "start_time": "2026-03-07T10:30:00Z",
  "end_time": "2026-03-07T10:30:05Z",
  "duration_ms": 5000,
  "status": "completed",
  "steps": [
    {
      "step_id": "step_1",
      "type": "reasoning",
      "description": "分析查询意图",
      "start_time": "2026-03-07T10:30:00Z",
      "end_time": "2026-03-07T10:30:01Z",
      "duration_ms": 1000,
      "input": "什么是机器学习？",
      "output": "用户询问机器学习的定义",
      "metadata": {
        "confidence": 0.95
      }
    }
  ],
  "result": {
    "answer": "机器学习是人工智能的一个分支...",
    "confidence": 0.92,
    "sources": ["知识库条目 #123", "知识库条目 #456"]
  }
}
```

### 4.3 配置模型

#### 4.3.1 智能体配置模型
```json
{
  "max_iterations": 5,
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 2000,
  "enable_retry": true,
  "retry_count": 3,
  "enable_fallback": true,
  "fallback_model": "step-3.5-flash",
  "timeout_seconds": 30,
  "enable_logging": true,
  "log_level": "info"
}
```

#### 4.3.2 模型路由配置
```json
{
  "strategy": "auto",
  "enable_reflection": true,
  "reflection_threshold": 0.7,
  "fallback_enabled": true,
  "cost_optimization": true,
  "providers": [
    {
      "name": "deepseek",
      "priority": 1,
      "models": ["deepseek-chat", "deepseek-reasoner"],
      "capabilities": ["reasoning", "complex_queries"]
    },
    {
      "name": "stepsflash",
      "priority": 2,
      "models": ["step-3.5-flash"],
      "capabilities": ["simple_queries", "fast_response"]
    }
  ]
}
```

## 🚀 API 使用示例

### 5.1 Python 客户端示例

#### 5.1.1 基础客户端
```python
import requests
import json

class RANGENClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })
    
    def chat(self, query, session_id=None, context=None):
        """发送对话请求"""
        url = f"{self.base_url}/chat"
        data = {"query": query}
        
        if session_id:
            data["session_id"] = session_id
        if context:
            data["context"] = context
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_agent(self, name, description, skills=None, tools=None):
        """创建智能体"""
        url = f"{self.base_url}/api/v1/agents"
        data = {
            "name": name,
            "description": description,
            "skills": skills or [],
            "tools": tools or []
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def health_check(self):
        """健康检查"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

# 使用示例
client = RANGENClient(
    base_url="http://localhost:8000",
    api_key="rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
)

# 发送对话请求
response = client.chat("什么是人工智能？")
print(f"回答: {response['answer']}")

# 创建智能体
agent = client.create_agent(
    name="研究助手",
    description="协助进行学术研究的智能体",
    skills=["skill_research", "skill_writing"],
    tools=["tool_web_search", "tool_citation"]
)
print(f"创建的智能体 ID: {agent['id']}")
```

#### 5.1.2 异步客户端
```python
import aiohttp
import asyncio

class AsyncRANGENClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    async def chat(self, query, session_id=None, context=None):
        """异步发送对话请求"""
        url = f"{self.base_url}/chat"
        data = {"query": query}
        
        if session_id:
            data["session_id"] = session_id
        if context:
            data["context"] = context
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def stream_chat(self, query, session_id=None, context=None):
        """流式对话"""
        url = f"{self.base_url}/chat/stream"
        data = {"query": query}
        
        if session_id:
            data["session_id"] = session_id
        if context:
            data["context"] = context
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self.headers) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if line.startswith(b"data: "):
                        yield json.loads(line[6:].decode())

# 使用示例
async def main():
    client = AsyncRANGENClient(
        base_url="http://localhost:8000",
        api_key="rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    )
    
    # 普通对话
    response = await client.chat("解释一下区块链技术")
    print(response["answer"])
    
    # 流式对话
    async for chunk in client.stream_chat("讲一个关于AI的故事"):
        if chunk["type"] == "thinking":
            print(f"思考: {chunk['content']}")
        elif chunk["type"] == "answer":
            print(chunk["content"], end="", flush=True)

# asyncio.run(main())
```

### 5.2 cURL 示例

#### 5.2.1 基础对话请求
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是深度学习？",
    "session_id": "session_123456"
  }'
```

#### 5.2.2 创建智能体
```bash
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "代码审查助手",
    "description": "帮助审查和优化代码的智能体",
    "skills": ["skill_code_review", "skill_optimization"],
    "tools": ["tool_pylint", "tool_black"]
  }'
```

#### 5.2.3 获取健康状态
```bash
curl -X GET "http://localhost:8000/health/auth" \
  -H "Authorization: Bearer rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 5.3 JavaScript/TypeScript 示例

#### 5.3.1 浏览器客户端
```javascript
class RANGENBrowserClient {
  constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.headers = {
      'Content-Type': 'application/json',
    };
    
    if (apiKey) {
      this.headers['Authorization'] = `Bearer ${apiKey}`;
    }
  }
  
  async chat(query, sessionId = null, context = null) {
    const url = `${this.baseUrl}/chat`;
    const body = { query };
    
    if (sessionId) body.session_id = sessionId;
    if (context) body.context = context;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async streamChat(query, sessionId = null, context = null) {
    const url = `${this.baseUrl}/chat/stream`;
    const body = { query };
    
    if (sessionId) body.session_id = sessionId;
    if (context) body.context = context;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    return {
      async *[Symbol.asyncIterator]() {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.substring(6);
                if (data.trim()) {
                  yield JSON.parse(data);
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      }
    };
  }
}

// 使用示例
const client = new RANGENBrowserClient(
  'http://localhost:8000',
  'rang_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
);

// 普通对话
client.chat('什么是机器学习？')
  .then(response => {
    console.log('回答:', response.answer);
    console.log('步骤:', response.steps);
  })
  .catch(error => console.error('错误:', error));

// 流式对话
async function streamExample() {
  const stream = await client.streamChat('讲一个技术故事');
  
  for await (const chunk of stream) {
    switch (chunk.type) {
      case 'thinking':
        console.log('思考中:', chunk.content);
        break;
      case 'answer':
        process.stdout.write(chunk.content);
        break;
      case 'done':
        console.log('\n完整回答:', chunk.full_answer);
        break;
    }
  }
}
```

## ⚠️ 错误处理

### 6.1 常见错误码

| HTTP 状态码 | 错误码 | 描述 | 解决方案 |
|-------------|--------|------|----------|
| 400 | `INVALID_REQUEST` | 请求格式错误 | 检查请求体格式和字段类型 |
| 401 | `UNAUTHORIZED` | 未提供认证或认证失败 | 提供有效的 API Key |
| 403 | `FORBIDDEN` | 权限不足 | 使用具有相应权限的 API Key |
| 404 | `NOT_FOUND` | 资源不存在 | 检查资源 ID 是否正确 |
| 429 | `RATE_LIMITED` | 请求频率过高 | 降低请求频率或联系管理员 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 | 查看服务器日志或联系技术支持 |
| 503 | `SERVICE_UNAVAILABLE` | 服务不可用 | 等待服务恢复或检查系统状态 |

### 6.2 错误响应示例

#### 6.2.1 认证错误
```json
{
  "detail": "认证失败: 无效的 API Key",
  "error_code": "UNAUTHORIZED",
  "timestamp": "2026-03-07T10:30:00Z",
  "request_id": "req_123456789"
}
```

#### 6.2.2 验证错误
```json
{
  "detail": "请求验证失败",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-03-07T10:30:00Z",
  "request_id": "req_123456789",
  "errors": [
    {
      "field": "query",
      "message": "query 字段不能为空"
    },
    {
      "field": "context.user_id",
      "message": "user_id 必须是字符串"
    }
  ]
}
```

#### 6.2.3 资源不存在
```json
{
  "detail": "智能体 'agent_999999' 不存在",
  "error_code": "NOT_FOUND",
  "timestamp": "2026-03-07T10:30:00Z",
  "request_id": "req_123456789",
  "resource_type": "agent",
  "resource_id": "agent_999999"
}
```

### 6.3 重试策略

#### 6.3.1 指数退避重试
```python
import time
import requests
from requests.exceptions import RequestException

def request_with_retry(url, headers, data, max_retries=3):
    """带指数退避的重试机制"""
    retry_delays = [1, 2, 4, 8, 16]  # 退避延迟（秒）
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # 4xx 错误不重试（除 429）
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                raise
            
            # 429 速率限制错误
            if e.response.status_code == 429:
                retry_after = e.response.headers.get('Retry-After', retry_delays[attempt])
                time.sleep(int(retry_after))
                continue
                
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            # 网络错误，进行重试
            pass
            
        except RequestException as e:
            # 其他请求异常
            raise
            
        # 执行退避
        if attempt < len(retry_delays):
            time.sleep(retry_delays[attempt])
        else:
            break
    
    raise Exception(f"请求失败，重试 {max_retries} 次后仍失败")
```

#### 6.3.2 异步重试
```python
import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30)
)
async def make_request_with_retry(session, url, headers, data):
    """异步重试请求"""
    async with session.post(url, headers=headers, json=data) as response:
        if response.status in [429, 500, 502, 503, 504]:
            raise Exception(f"HTTP {response.status}")
        
        response.raise_for_status()
        return await response.json()
```

## 🔧 高级配置

### 7.1 自定义请求头

#### 7.1.1 跟踪头
```http
X-Request-ID: req_123456789
X-Client-Version: 1.2.0
X-User-ID: user_001
X-Session-ID: session_123456
```

#### 7.1.2 语言和区域头
```http
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Content-Language: zh-CN
```

### 7.2 超时配置

#### 7.2.1 客户端超时设置
```python
# Python requests
response = requests.post(url, timeout=(10, 30))  # 连接10秒，读取30秒

# aiohttp
timeout = aiohttp.ClientTimeout(total=60)  # 总超时60秒
```

#### 7.2.2 服务器端超时
通过环境变量配置：
```bash
export RANGEN_REQUEST_TIMEOUT=30  # 请求处理超时（秒）
export RANGEN_STREAM_TIMEOUT=300  # 流式响应超时（秒）
```

### 7.3 压缩和性能优化

#### 7.3.1 启用响应压缩
```http
Accept-Encoding: gzip, deflate, br
```

#### 7.3.2 分块传输
流式端点自动使用分块传输编码。

## 📈 监控和日志

### 8.1 请求追踪

#### 8.1.1 追踪头
每个响应包含追踪头：
```http
X-Request-ID: req_123456789
X-Response-Time: 1.234
X-Trace-ID: trace_123456789
```

#### 8.1.2 性能指标
```json
{
  "request_id": "req_123456789",
  "endpoint": "/chat",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 1234.5,
  "timestamp": "2026-03-07T10:30:00Z",
  "user_agent": "Python-Requests/2.28.1",
  "ip_address": "192.168.1.100"
}
```

### 8.2 日志格式

#### 8.2.1 访问日志
```
2026-03-07 10:30:00 INFO [api_server] POST /chat 200 1234ms req_123456789
```

#### 8.2.2 错误日志
```
2026-03-07 10:30:00 ERROR [api_server] Request failed: 认证失败
Trace ID: trace_123456789
Request ID: req_123456789
Endpoint: /chat
Client IP: 192.168.1.100
```

## 📖 版本管理

### 9.1 API 版本策略

#### 9.1.1 版本标识
- 路径版本：`/api/v1/agents`
- 头信息版本：`Accept: application/vnd.rangen.v1+json`

#### 9.1.2 版本兼容性
| 版本 | 状态 | 维护截止 | 迁移指南 |
|------|------|----------|----------|
| v1 | 当前稳定版 | 2027-03-07 | - |
| v0 | 已弃用 | 2026-06-07 | [迁移指南](migration-v0-to-v1.md) |

### 9.2 弃用策略

#### 9.2.1 弃用通知
弃用的端点返回警告头：
```http
Deprecation: Sat, 07 Mar 2026 10:30:00 GMT
Sunset: Mon, 07 Jun 2026 10:30:00 GMT
Link: </api/v2/agents>; rel="successor-version"
```

#### 9.2.2 迁移时间线
1. **公告期** (30天)：添加弃用警告
2. **迁移期** (60天)：保持功能，鼓励迁移
3. **弃用期** (30天)：功能降级，仅返回基础响应
4. **移除期**：完全移除功能

## 🔗 相关资源

### 10.1 官方资源
- [API 文档 (Swagger UI)](http://localhost:8000/docs)
- [API 文档 (ReDoc)](http://localhost:8000/redoc)
- [GitHub 仓库](https://github.com/your-repo/RANGEN)
- [问题追踪](https://github.com/your-repo/RANGEN/issues)

### 10.2 客户端库
- **Python**: `pip install rangen-client` (开发中)
- **JavaScript**: `npm install rangen-client` (开发中)
- **Go**: `go get github.com/your-repo/rangen-go` (规划中)

### 10.3 示例项目
- [Python 集成示例](https://github.com/your-repo/RANGEN-examples/tree/main/python)
- [JavaScript 网页应用](https://github.com/your-repo/RANGEN-examples/tree/main/javascript)
- [移动应用集成](https://github.com/your-repo/RANGEN-examples/tree/main/mobile)

## 📝 更新日志

### 11.1 版本历史

| 版本 | 日期 | 变更描述 |
|------|------|----------|
| v1.0.0 | 2026-03-07 | 初始 API 版本发布 |
| v1.1.0 | 2026-03-14 | 新增流式对话端点 |
| v1.2.0 | 2026-03-21 | 增强错误处理，添加请求追踪 |
| v1.3.0 | 2026-03-28 | 新增自然语言智能体创建端点 |

### 11.2 近期更新
- **2026-03-07**: 发布初始 API 文档
- **2026-03-08**: 添加 Python 客户端示例
- **2026-03-09**: 完善错误处理章节
- **2026-03-10**: 添加版本管理和弃用策略

## 📞 支持与反馈

### 12.1 技术支持
- **技术问题**: [提交 Issue](https://github.com/your-repo/RANGEN/issues)
- **API 疑问**: [API 讨论区](https://github.com/your-repo/RANGEN/discussions/categories/api)
- **集成帮助**: [集成支持](https://github.com/your-repo/RANGEN/discussions/categories/integration)

### 12.2 反馈渠道
- **功能建议**: [功能请求](https://github.com/your-repo/RANGEN/discussions/categories/ideas)
- **文档反馈**: [文档改进](https://github.com/your-repo/RANGEN/discussions/categories/documentation)
- **错误报告**: [错误报告](https://github.com/your-repo/RANGEN/issues/new?template=bug_report.md)

### 12.3 紧急联系
- **生产事故**: 联系运维团队或查看 [紧急处理指南](../operations/emergency-response.md)
- **安全漏洞**: [安全报告](https://github.com/your-repo/RANGEN/security/advisories)
- **服务中断**: 查看 [状态页面](https://status.rangen.ai) (规划中)

---

*最后更新: 2026-03-07*  
*文档版本: 1.0.0*  
*API 版本: v1*  
*维护团队: RANGEN API 工程组*

> **重要提示**: 本文档适用于 RANGEN API v1 版本。API 会持续演进，建议定期查看最新文档。