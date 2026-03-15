# 动态配置管理系统API文档

## 概述

动态配置管理系统提供了一套完整的REST API，用于配置管理和系统监控。本文档详细介绍了所有可用的API端点、参数和使用示例。

## 基础信息

- **基础URL**: `http://localhost:8080` (配置API), `http://localhost:8081` (Web界面)
- **认证**: Bearer Token (可选)
- **数据格式**: JSON
- **字符编码**: UTF-8

## API端点

### 配置管理

#### 1. 获取当前配置

**端点**: `GET /api/config`

**描述**: 获取当前系统的完整配置信息

**响应示例**:
```json
{
  "thresholds": {
    "simple_max_complexity": 0.05,
    "medium_max_complexity": 0.25,
    "complex_min_complexity": 0.25
  },
  "keywords": {
    "question_words": ["what", "why", "how"],
    "complexity_indicators": ["explain", "analyze"]
  },
  "routing_rules": []
}
```

#### 2. 更新阈值配置

**端点**: `POST /api/config/thresholds`

**描述**: 更新路由阈值配置

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "simple_max_complexity": 0.08,
  "medium_max_complexity": 0.3
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "阈值已更新"
}
```

#### 3. 更新关键词配置

**端点**: `POST /api/config/keywords`

**描述**: 添加或更新关键词配置

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "question_words": ["what", "why", "how", "when", "where"]
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "关键词已更新"
}
```

#### 4. 应用配置模板

**端点**: `POST /api/config/templates`

**描述**: 应用预定义的配置模板

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "template_name": "conservative"
}
```

**响应示例**:
```json
{
  "status": "success",
  "message": "模板 conservative 已应用"
}
```

### 系统监控

#### 5. 获取系统指标

**端点**: `GET /api/metrics`

**描述**: 获取配置系统的监控指标

**响应示例**:
```json
{
  "total_changes": 15,
  "recent_changes_7d": 3,
  "change_frequency_per_day": 2.1,
  "author_stats": {
    "admin": 10,
    "developer": 5
  },
  "type_distribution": {
    "manual": 12,
    "auto": 3
  },
  "health_score": 85.5
}
```

#### 6. 获取变更历史

**端点**: `GET /api/logs`

**查询参数**:
- `limit` (可选): 返回记录数量，默认10

**描述**: 获取配置变更历史记录

**响应示例**:
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "version": "a1b2c3d4",
      "author": "admin",
      "description": "更新阈值配置",
      "change_summary": {
        "thresholds_count": 5,
        "keywords_count": 2
      }
    }
  ]
}
```

#### 7. 获取模板列表

**端点**: `GET /api/templates`

**描述**: 获取所有可用的配置模板

**响应示例**:
```json
{
  "templates": [
    {
      "name": "conservative",
      "display_name": "保守配置",
      "description": "适用于生产环境的保守配置",
      "extends": "base",
      "environment": ["production", "staging"],
      "inheritance_chain": ["base", "conservative"]
    }
  ]
}
```

### 认证管理

#### 8. 用户登录

**端点**: `POST /api/auth/login`

**描述**: 用户认证登录

**请求体**:
```json
{
  "username": "admin",
  "password": "admin"
}
```

**响应示例**:
```json
{
  "status": "success",
  "session_id": "abc123def456",
  "user": "admin"
}
```

### 系统健康检查

#### 9. 健康检查

**端点**: `GET /health`

**描述**: 系统健康状态检查

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

## 错误响应

所有API在出错时都会返回相应的HTTP状态码和错误信息：

```json
{
  "error": "错误描述",
  "code": 400
}
```

### 常见错误码

- `400`: 请求参数错误
- `401`: 未认证
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器内部错误

## 使用示例

### Python客户端示例

```python
import requests

class ConfigAPIClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session_id = None

    def login(self, username, password):
        response = requests.post(f"{self.base_url}/api/auth/login", json={
            "username": username,
            "password": password
        })
        data = response.json()
        self.session_id = data.get("session_id")
        return data

    def get_config(self):
        headers = {}
        if self.session_id:
            headers["Authorization"] = f"Bearer {self.session_id}"

        response = requests.get(f"{self.base_url}/api/config", headers=headers)
        return response.json()

    def update_thresholds(self, thresholds):
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Authorization"] = f"Bearer {self.session_id}"

        response = requests.post(
            f"{self.base_url}/api/config/thresholds",
            json=thresholds,
            headers=headers
        )
        return response.json()

# 使用示例
client = ConfigAPIClient()
client.login("admin", "admin")

# 获取配置
config = client.get_config()
print("当前配置:", config)

# 更新阈值
result = client.update_thresholds({
    "simple_max_complexity": 0.08,
    "medium_max_complexity": 0.3
})
print("更新结果:", result)
```

### JavaScript客户端示例

```javascript
class ConfigAPIClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        this.sessionId = data.session_id;
        return data;
    }

    async getConfig() {
        const headers = {};
        if (this.sessionId) {
            headers['Authorization'] = `Bearer ${this.sessionId}`;
        }

        const response = await fetch(`${this.baseUrl}/api/config`, {
            headers
        });
        return response.json();
    }

    async updateThresholds(thresholds) {
        const headers = { 'Content-Type': 'application/json' };
        if (this.sessionId) {
            headers['Authorization'] = `Bearer ${this.sessionId}`;
        }

        const response = await fetch(`${this.baseUrl}/api/config/thresholds`, {
            method: 'POST',
            headers,
            body: JSON.stringify(thresholds)
        });
        return response.json();
    }
}

// 使用示例
const client = new ConfigAPIClient();
await client.login('admin', 'admin');

const config = await client.getConfig();
console.log('当前配置:', config);

const result = await client.updateThresholds({
    simple_max_complexity: 0.08,
    medium_max_complexity: 0.3
});
console.log('更新结果:', result);
```

### cURL命令示例

```bash
# 登录获取会话ID
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 获取配置
curl -X GET http://localhost:8080/api/config \
  -H "Authorization: Bearer <session_id>"

# 更新阈值
curl -X POST http://localhost:8080/api/config/thresholds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{
    "simple_max_complexity": 0.08,
    "medium_max_complexity": 0.3
  }'

# 获取监控指标
curl -X GET http://localhost:8080/api/metrics

# 应用配置模板
curl -X POST http://localhost:8080/api/config/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{"template_name": "conservative"}'
```

## 安全注意事项

1. **HTTPS**: 在生产环境中使用HTTPS协议
2. **认证**: 所有敏感操作都需要有效的认证令牌
3. **权限控制**: 根据用户角色限制操作权限
4. **输入验证**: 所有输入数据都会进行严格验证
5. **日志记录**: 所有操作都会记录审计日志

## 性能考虑

- API响应时间通常在100ms以内
- 支持并发请求处理
- 内置缓存机制优化性能
- 监控系统负载并自动调整

## 故障排除

### 常见问题

1. **连接超时**
   - 检查服务器是否正在运行
   - 确认端口配置正确
   - 检查网络连接

2. **认证失败**
   - 确认用户名和密码正确
   - 检查会话是否过期
   - 验证用户权限

3. **配置更新失败**
   - 检查输入数据的格式
   - 验证配置值的有效性
   - 查看详细的错误信息

### 调试模式

启用调试模式获取更多信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

这将提供详细的API调用日志和错误信息。
