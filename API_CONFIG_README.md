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

## 技术支持

如果配置后仍有问题：
1. 运行 `python3 setup_api_config.py` 查看详细诊断信息
2. 检查网络连接和防火墙设置
3. 确认DeepSeek账户状态正常
4. 查看项目日志中的错误详情
