# 知识检索失败问题修复

## 问题描述

知识检索服务在初始化失败或FAISS/KMS不可用时，会直接返回错误，导致Simple查询无法获取知识，进而回退到推理链模式。

## 问题根源

### 1. 初始化失败导致服务不可用

**位置**：`src/services/knowledge_retrieval_service.py` 的 `execute` 方法

```python
if self.kms_service is None and self.faiss_service is None:
    # 初始化服务
    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, self._initialize_services),
            timeout=180.0
        )
    except asyncio.TimeoutError:
        # ❌ 问题：直接返回错误，没有使用fallback机制
        return AgentResult(success=False, error="服务初始化超时")
    except Exception as e:
        # ❌ 问题：直接返回错误，没有使用fallback机制
        return AgentResult(success=False, error=f"服务初始化失败: {e}")
```

**问题**：
- 初始化超时或失败时，直接返回错误
- 没有尝试使用Wiki检索等fallback机制
- 导致知识检索完全失败

### 2. FAISS/KMS不可用时没有fallback

**位置**：`src/services/knowledge_retrieval_service.py` 的 `_get_faiss_knowledge` 方法

```python
if not self.faiss_service:
    logger.warning("FAISS服务不可用")
    return None  # ❌ 问题：直接返回None，没有尝试其他检索方式
```

**问题**：
- FAISS服务不可用时，直接返回None
- 没有尝试Wiki检索等fallback方式
- 导致知识检索失败

### 3. 知识源检索逻辑不够健壮

**位置**：`src/services/knowledge_retrieval_service.py` 的 `_perform_knowledge_retrieval` 方法

```python
knowledge_sources = [
    self._retrieve_from_wiki,
    self._retrieve_from_faiss,
    self._retrieve_from_fallback
]

for source_func in knowledge_sources:
    result = await source_func(query, query_analysis, context)
    if result and result.confidence >= self.config.confidence_threshold:
        return result  # ❌ 问题：只检查confidence，不检查是否有有效的sources
```

**问题**：
- 只检查confidence阈值，不检查是否有有效的sources
- 如果sources为空，仍然返回结果，导致后续处理失败

## 修复方案

### 修复1：初始化失败时继续执行，使用fallback机制

**修改**：`src/services/knowledge_retrieval_service.py` 的 `execute` 方法

```python
# 修改前：初始化失败时直接返回错误
except asyncio.TimeoutError:
    return AgentResult(success=False, error="服务初始化超时")

# 修改后：初始化失败时继续执行，使用fallback机制
except asyncio.TimeoutError:
    logger.warning("⚠️ 知识检索服务初始化超时（180秒），将使用fallback机制")
    logger.info("🔄 继续执行知识检索，将尝试Wiki检索等fallback方式")
    # 不返回错误，继续执行
```

**效果**：
- 即使初始化失败，也能继续执行知识检索
- 使用Wiki检索等fallback机制，确保知识检索能够成功

### 修复2：优化知识源检索逻辑

**修改**：`src/services/knowledge_retrieval_service.py` 的 `_perform_knowledge_retrieval` 方法

```python
# 修改前：只检查confidence阈值
if result and result.confidence >= self.config.confidence_threshold:
    return result

# 修改后：检查是否有有效的sources
if result and result.success and result.data:
    sources = []
    if isinstance(result.data, dict):
        sources = result.data.get('sources', [])
    elif isinstance(result.data, list):
        sources = result.data
    
    if sources and len(sources) > 0:
        logger.info(f"✅ 成功从{source_name}获取知识: {len(sources)}条")
        return result
    else:
        logger.debug(f"⚠️ {source_name}返回空结果，尝试下一个知识源")
```

**效果**：
- 确保返回的结果包含有效的sources
- 如果sources为空，尝试下一个知识源
- 提高知识检索的成功率

### 修复3：优化知识源优先级

**修改**：`src/services/knowledge_retrieval_service.py` 的 `_perform_knowledge_retrieval` 方法

```python
# 修改前：知识源列表没有名称，难以调试
knowledge_sources = [
    self._retrieve_from_wiki,
    self._retrieve_from_faiss,
    self._retrieve_from_fallback
]

# 修改后：添加名称，便于调试和日志记录
knowledge_sources = [
    ("Wiki检索", self._retrieve_from_wiki),  # 优先级最高，不依赖KMS/FAISS
    ("FAISS检索", self._retrieve_from_faiss),
    ("Fallback检索", self._retrieve_from_fallback)
]
```

**效果**：
- Wiki检索优先级最高，不依赖KMS/FAISS
- 即使KMS/FAISS不可用，也能使用Wiki检索
- 日志更清晰，便于调试

## 修复效果

### 预期改进

1. **初始化失败时也能检索**：
   - 即使初始化超时或失败，也能继续执行知识检索
   - 使用Wiki检索等fallback机制，确保知识检索能够成功

2. **FAISS/KMS不可用时也能检索**：
   - 即使FAISS/KMS服务不可用，也能使用Wiki检索
   - 提高知识检索的成功率

3. **更健壮的知识源检索**：
   - 确保返回的结果包含有效的sources
   - 如果sources为空，尝试下一个知识源
   - 提高知识检索的可靠性

### 关键改进

- ✅ 初始化失败时继续执行，使用fallback机制
- ✅ 优化知识源检索逻辑，确保返回有效结果
- ✅ Wiki检索优先级最高，不依赖KMS/FAISS
- ✅ 更清晰的日志，便于调试

## 当前状态

- ✅ 已识别问题根源
- ✅ 已实施修复方案
- ⏳ 待验证修复效果

## 下一步

1. ✅ 已修复初始化失败时的处理逻辑
2. ✅ 已优化知识源检索逻辑
3. ⏳ 待测试验证：验证知识检索在初始化失败时也能成功
4. ⏳ 待测试验证：验证FAISS/KMS不可用时也能使用Wiki检索

