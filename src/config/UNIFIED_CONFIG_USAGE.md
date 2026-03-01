# 统一配置使用指南

## 📋 重构后的配置架构

经过重构，环境变量配置现在统一由 `UnifiedConfigCenter` 管理，解决了之前配置分散和不一致的问题。

## 🔄 **学习率持久化机制**

### **问题解决**
学习率是动态调整的，但调整后的值需要持久化保存，避免重启后丢失学习成果。

### **持久化机制**
```python
from src.config.learning_state_manager import (
    get_current_learning_rate,
    update_learning_rate
)

# 获取当前学习率（优先使用持久化的动态调整值）
current_rate = get_current_learning_rate()  # 默认: 0.001

# 动态调整学习率并自动保存
update_learning_rate(0.05, "performance_improvement", {"accuracy": 0.85})
```

### **状态文件**
- **文件位置**: `learning_state.json`
- **内容**: 学习率、批次大小、探索率等参数的当前值和调整历史
- **自动管理**: 系统自动创建、更新和维护

### **配置优先级（更新后）**
```
持久化的动态调整值 (最高优先级)
    ↓
环境变量 (初始值/种子值)
    ↓
默认值 (fallback)
```

## 🚀 使用方法

### **1. 使用便捷函数（推荐）**

```python
from src.utils.unified_centers import (
    get_max_evaluation_items,
    get_batch_size,
    get_learning_rate,
    get_max_concurrent_queries,
    get_request_timeout,
    get_max_cache_size
)

# 获取配置值
max_items = get_max_evaluation_items()  # 默认: 1000
batch_size = get_batch_size()          # 默认: 32
learning_rate = get_learning_rate()    # 优先使用持久化的动态调整值
```

### **2. 使用统一配置中心**

```python
from src.utils.unified_centers import get_unified_config_center

config_center = get_unified_config_center()

# 获取系统配置
max_items = config_center.get_env_config('system', 'MAX_EVALUATION_ITEMS', 1000)
timeout = config_center.get_env_config('system', 'REQUEST_TIMEOUT', 30)

# 获取AI/ML配置
batch_size = config_center.get_env_config('ai_ml', 'BATCH_SIZE', 32)
learning_rate = config_center.get_env_config('ai_ml', 'LEARNING_RATE', 0.001)
```

### **3. 环境变量设置**

```bash
# 设置样本数量
export MAX_EVALUATION_ITEMS=50

# 设置批次大小
export BATCH_SIZE=16

# 设置学习率
export LEARNING_RATE=0.01

# 运行核心系统
python scripts/run_core_with_frames.py --sample-count 10
```

## 📊 配置分类

### **系统配置 (system)**
- `MAX_EVALUATION_ITEMS`: 最大评估项目数 (默认: 1000)
- `MAX_CONCURRENT_QUERIES`: 最大并发查询数 (默认: 3)
- `REQUEST_TIMEOUT`: 请求超时时间 (默认: 30)
- `MAX_CACHE_SIZE`: 最大缓存大小 (默认: 100)
- `SESSION_TIMEOUT`: 会话超时时间 (默认: 3600)
- `MAX_THREADS`: 最大线程数 (默认: 4)
- `MAX_CONNECTIONS`: 最大连接数 (默认: 100)

### **AI/ML配置 (ai_ml)**
- `BATCH_SIZE`: 批次大小 (默认: 32)
- `LEARNING_RATE`: 学习率初始值 (默认: 0.001) - **注意：实际使用时会动态调整并持久化**
- `EPOCHS`: 训练轮数 (默认: 100)
- `MODEL_MAX_LENGTH`: 模型最大长度 (默认: 256)
- `VECTOR_DIMENSION`: 向量维度 (默认: 384)
- `SIMILARITY_THRESHOLD`: 相似度阈值 (默认: 0.6)

### **路径配置 (paths)**
- `FAISS_INDEX_PATH`: FAISS索引路径
- `DATA_DIRECTORY`: 数据目录
- `LOG_DIRECTORY`: 日志目录
- `CONFIG_DIRECTORY`: 配置目录
- `CACHE_DIRECTORY`: 缓存目录

### **URL配置 (urls)**
- `API_BASE_URL`: API基础URL
- `LLM_API_URL`: LLM API URL
- `LLM_API_KEY`: LLM API密钥
- `VECTOR_DB_URL`: 向量数据库URL

## 🔧 迁移指南

### **旧方式（已废弃）**
```python
# ❌ 不要这样做
import os
max_items = int(os.getenv('MAX_EVALUATION_ITEMS', '1000'))
batch_size = int(os.getenv('BATCH_SIZE', '32'))
```

### **新方式（推荐）**
```python
# ✅ 推荐做法
from src.utils.unified_centers import get_max_evaluation_items, get_batch_size
max_items = get_max_evaluation_items()
batch_size = get_batch_size()
```

## 🎯 优势

1. **统一管理**: 所有环境变量配置集中在一个地方
2. **一致性**: 消除了不同文件中的默认值不一致问题
3. **易维护**: 修改配置只需要在一个地方进行
4. **类型安全**: 自动处理类型转换
5. **缓存优化**: 内置缓存机制，提高性能

## 📝 注意事项

- `SystemConstants` 现在只包含真正的常量，不包含环境变量配置
- 所有环境变量配置都通过 `UnifiedConfigCenter` 获取
- **学习率特殊处理**：环境变量提供初始值，实际使用时会动态调整并持久化保存
- 配置优先级：持久化的动态调整值 > 环境变量 > 用户配置 > 默认配置
- 建议使用便捷函数而不是直接调用 `os.getenv()`
- 学习状态文件 `learning_state.json` 会自动创建和管理，无需手动干预
