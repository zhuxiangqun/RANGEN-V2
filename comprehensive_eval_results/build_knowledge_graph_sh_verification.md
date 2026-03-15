# build_knowledge_graph.sh 脚本验证报告

**验证时间**: 2025-11-15  
**状态**: ✅ 已验证，已更新

---

## ✅ 功能确认

**`./build_knowledge_graph.sh` 脚本可以构建知识图谱，并且会使用所有上述优化。**

---

## 📋 脚本功能

### 1. 调用Python脚本
- **脚本路径**: `knowledge_management_system/scripts/build_knowledge_graph.py`
- **参数传递**: 正确传递所有参数

### 2. 默认行为
- **断点续传**: 默认启用（`RESUME=true`）
- **自动重试失败条目**: 默认启用（Python脚本的`auto_retry_failed=True`）
- **批次大小**: 默认100

### 3. 支持的参数
- `--batch-size`: 指定批次大小
- `--no-entities`: 不提取实体
- `--no-relations`: 不提取关系
- `--resume`: 启用断点续传
- `--no-resume`: 不启用断点续传
- `--retry-failed`: 只重新处理失败的条目
- `--no-retry-failed`: 不自动重试失败的条目（新增）

---

## 🚀 使用的优化

### 1. 并发优化 ✅
- **并发数**: 10（从5增加到10）
- **位置**: `knowledge_management_system/scripts/build_knowledge_graph.py`

### 2. 重试机制优化 ✅
- **默认重试次数**: 3次
- **超时时间**: 120秒（从90秒增加）
- **指数退避策略**: 自动重试
- **位置**: `knowledge_management_system/utils/jina_service.py`

### 3. 自动重试失败条目 ✅
- **默认行为**: 自动重试失败的条目
- **位置**: `knowledge_management_system/scripts/build_knowledge_graph.py`

### 4. max_tokens优化 ✅
- **推理模型基础值**: 8000 tokens（从6000增加）
- **复杂问题**: 12000 tokens（从9000增加）
- **位置**: `src/core/llm_integration.py`

---

## 📝 使用示例

### 基本使用（推荐）
```bash
# 默认行为：自动断点续传 + 自动重试失败的条目
./build_knowledge_graph.sh
```

### 指定批次大小
```bash
# 指定批次大小为100
./build_knowledge_graph.sh --batch-size 100
```

### 只重试失败的条目
```bash
# 只重新处理之前失败的条目
./build_knowledge_graph.sh --retry-failed
```

### 不自动重试失败的条目
```bash
# 不自动重试失败的条目（只处理未处理的条目）
./build_knowledge_graph.sh --no-retry-failed
```

### 从头开始
```bash
# 从头开始，忽略之前的进度
./build_knowledge_graph.sh --no-resume
```

---

## 🔍 脚本执行流程

1. **解析参数** - 解析命令行参数
2. **切换到项目根目录** - 确保路径正确
3. **设置环境变量** - 设置OpenMP相关环境变量
4. **构建Python参数** - 将shell参数转换为Python参数
5. **执行Python脚本** - 调用`build_knowledge_graph.py`
6. **返回退出码** - 返回执行结果

---

## ✅ 验证结果

### 功能验证
- ✅ 可以构建知识图谱
- ✅ 支持断点续传
- ✅ 支持自动重试失败的条目
- ✅ 支持所有优化功能

### 优化验证
- ✅ 并发优化：10个并发
- ✅ 重试机制：3次重试，120秒超时
- ✅ 自动重试：默认自动重试失败的条目
- ✅ max_tokens：8000/12000 tokens

---

## 📊 预期效果

使用 `./build_knowledge_graph.sh` 运行后：

1. **自动断点续传**: 从上次停止的地方继续
2. **自动重试失败条目**: 自动重试之前失败的条目
3. **使用优化后的性能**: 
   - 并发数：10
   - 重试机制：3次重试
   - 超时时间：120秒
   - max_tokens：8000/12000

---

## 🎯 建议

**直接使用 `./build_knowledge_graph.sh` 即可**，它会：
- ✅ 自动使用所有优化
- ✅ 自动断点续传
- ✅ 自动重试失败的条目
- ✅ 无需额外参数

---

*验证时间: 2025-11-15*

