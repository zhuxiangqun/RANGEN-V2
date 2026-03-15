# API配置指南

## 问题描述

新Agent (ReasoningExpert, RAGExpert等) 在调用DeepSeek API时失败，报错：
```
HTTPSConnectionPool(host='api.deepseek.com', port=443): Max retries exceeded
```

这是因为API密钥未正确配置导致的。

## 快速解决步骤

### 1. 获取DeepSeek API密钥

1. 访问 [DeepSeek平台](https://platform.deepseek.com/)
2. 注册账户（如果还没有）
3. 在控制台创建API密钥
4. 复制生成的API密钥（格式类似：`sk-xxxxxxxxxxxxxxxxxx`）

### 2. 配置环境变量

**推荐方法：设置环境变量**

```bash
# 临时设置（当前会话有效）
export DEEPSEEK_API_KEY="你的API密钥"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export DEEPSEEK_MODEL="deepseek-reasoner"

# 验证设置
echo $DEEPSEEK_API_KEY
```

**永久设置方法：**

```bash
# 添加到shell配置文件 (~/.bashrc 或 ~/.zshrc)
echo 'export DEEPSEEK_API_KEY="你的API密钥"' >> ~/.bashrc
echo 'export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"' >> ~/.bashrc
echo 'export DEEPSEEK_MODEL="deepseek-reasoner"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

### 3. 验证配置

运行测试脚本验证API连接：

```bash
python3 test_api_connection.py
```

成功输出示例：
```
🧪 测试API连接
============================================================
📋 配置信息:
   API Key: 设置 (32 字符)
   Base URL: https://api.deepseek.com/v1
   Model: deepseek-reasoner

🔄 初始化LLM客户端...
📤 发送测试请求...
✅ API连接成功!
   响应: Hello, API test successful!...
```

## 提供的工具脚本

### `setup_api_config.py`
- 检查当前API配置状态
- 提供详细的配置指导
- 测试API连接

```bash
python3 setup_api_config.py
```

### `test_api_connection.py`
- 快速测试API连接
- 验证配置是否正确

```bash
python3 test_api_connection.py
```

### `set_env_vars.sh`
- 临时设置环境变量的脚本
- 用于快速测试

```bash
source set_env_vars.sh
# 然后编辑脚本中的API密钥
```

## 配置说明

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DEEPSEEK_API_KEY` | (必须设置) | DeepSeek API密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | API端点地址 |
| `DEEPSEEK_MODEL` | `deepseek-reasoner` | 使用的模型 |

## 常见问题

### 1. API密钥格式错误
- 确保API密钥以 `sk-` 开头
- 检查密钥长度是否正确（通常30+字符）

### 2. 网络连接问题
- 检查防火墙设置
- 确认网络可以访问 `api.deepseek.com`
- 检查是否有代理设置干扰

### 3. API额度不足
- 登录DeepSeek控制台检查账户余额
- 确认API密钥有效且未过期

### 4. 模型不存在
- 确认模型名称正确：
  - `deepseek-reasoner` (推理模型，支持thinking)
  - `deepseek-chat` (快速模型)

## 迁移测试

配置完成后，可以继续进行Agent迁移：

```bash
# 测试ReActAgent迁移
python3 temp_migration_test.py

# 或继续批量迁移
python3 scripts/batch_apply_p2_replacements.py
```

## Step-3.5-Flash 配置

RANGEN 系统现已支持 Step-3.5-Flash 模型，这是一个由 StepFun 开发的开源稀疏 MoE 大语言模型（196B 总参数，11B 活跃参数）。

### 部署方式

Step-3.5-Flash 支持三种部署方式：

1. **OpenRouter API** (推荐) - 通过 OpenRouter 平台调用
2. **NVIDIA NIM API** - 通过 NVIDIA NIM 服务调用
3. **vLLM 本地部署** - 本地部署 vLLM 服务器

### 配置步骤

#### 1. 获取 API 密钥

- **OpenRouter**: 访问 [OpenRouter](https://openrouter.ai/) 注册账户并获取 API 密钥
- **NVIDIA NIM**: 访问 [NVIDIA API Catalog](https://build.nvidia.com/explore/discover) 获取访问权限

#### 2. 配置环境变量

```bash
# 使用 Step-3.5-Flash (OpenRouter)
export LLM_PROVIDER="stepflash"
export STEPSFLASH_API_KEY="你的_OpenRouter_API_密钥"

# 或使用 NVIDIA NIM
export LLM_PROVIDER="stepflash"
export STEPSFLASH_API_KEY="你的_NVIDIA_NIM_API_密钥"
export STEPFLASH_DEPLOYMENT_TYPE="nim"
export STEPFLASH_BASE_URL="https://api.nvidia.com/nim/v1"

# 或使用 vLLM 本地部署
export LLM_PROVIDER="stepflash"
export STEPFLASH_DEPLOYMENT_TYPE="vllm_local"
export STEPFLASH_BASE_URL="http://localhost:8000/v1"
```

#### 3. 验证配置

运行集成测试验证 Step-3.5-Flash 配置：

```bash
# 运行 Step-3.5-Flash 集成测试
python3 tests/test_stepflash_integration.py

# 运行生产环境端到端测试
python3 tests/test_stepflash_production.py
```

### 配置说明

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `LLM_PROVIDER` | `deepseek` | LLM 提供者，设置为 `stepflash` 使用 Step-3.5-Flash |
| `STEPSFLASH_API_KEY` | (必须设置) | Step-3.5-Flash API 密钥 |
| `STEPFLASH_DEPLOYMENT_TYPE` | `openrouter` | 部署类型：`openrouter`, `nim`, `vllm_local` |
| `STEPFLASH_BASE_URL` | 自动设置 | 自定义基础 URL (主要用于 vLLM 本地部署) |
| `STEPFLASH_MODEL` | 自动设置 | 模型名称，根据部署类型自动选择 |

### 性能参数

StepFlashAdapter 提供以下可调性能参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `timeout` | 30秒 | 请求超时时间 |
| `max_tokens` | 8192 | 最大生成 token 数 |
| `temperature` | 0.7 | 温度参数 |
| `max_retries` | 3 | 最大重试次数 |
| `retry_delay` | 1.0秒 | 重试延迟时间 |

这些参数可通过适配器构造函数或环境变量进行配置。

### 示例代码

```python
from src.services.stepflash_adapter import StepFlashAdapter

# 使用 OpenRouter
adapter = StepFlashAdapter(
    deployment_type="openrouter",
    api_key="your-api-key",
    timeout=30,
    max_tokens=8192
)

# 使用 vLLM 本地部署
adapter = StepFlashAdapter(
    deployment_type="vllm_local",
    base_url="http://localhost:8000",
    timeout=60,
    max_retries=5
)

# 调用模型
messages = [{"role": "user", "content": "你好，Step-3.5-Flash！"}]
response = adapter.chat_completion(messages)
```

### 故障排除

#### 1. API 密钥错误
- 确认 API 密钥有效且未过期
- 检查部署类型与 API 密钥匹配

#### 2. 网络连接问题
- 确认可以访问相应的 API 端点
- 检查防火墙和代理设置

#### 3. 模型不可用
- 确认所选部署方式支持 Step-3.5-Flash 模型
- 检查模型名称是否正确

#### 4. 性能问题
- 调整 `timeout` 参数以适应网络延迟
- 调整 `max_retries` 和 `retry_delay` 优化重试策略

## 技术支持

如果配置后仍有问题：
1. 运行 `python3 setup_api_config.py` 查看详细诊断信息
2. 检查网络连接和防火墙设置
3. 确认DeepSeek账户状态正常
4. 查看项目日志中的错误详情
