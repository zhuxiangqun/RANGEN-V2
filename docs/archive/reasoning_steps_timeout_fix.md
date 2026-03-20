# 推理步骤生成超时问题分析与修复

## 问题现象

从终端输出看到以下警告：

1. **中文查询警告**：
   ```
   ⚠️ 检测到查询包含中文字符，但系统应使用英文查询
   当前查询: 推理分析：整合检索到的信息，确定第15任第一夫人的母亲的名字...
   ```

2. **推理步骤生成超时**：
   ```
   ⚠️ 推理步骤生成超时（30秒），使用回退方法
   ```

3. **没有推理步骤**：
   ```
   ⚠️ 没有推理步骤，使用原始查询检索证据
   ```

## 问题分析

### 1. 中文查询警告（非关键问题）

**原因**：
- 这是来自ChiefAgent的任务分解结果
- LLM将原始英文查询分解成了中文的子任务描述
- 这是正常的，只是提醒，不影响功能

**位置**：`src/core/real_reasoning_engine.py:2552-2557`

### 2. 推理步骤生成超时（关键问题）

**原因**：
- `_execute_reasoning_steps_with_prompts` 方法调用LLM生成推理步骤
- 当前超时设置为30秒（第2866行）
- LLM响应可能较慢，导致超时

**影响**：
- 推理步骤生成失败
- 系统回退到使用原始查询检索证据
- 可能影响推理质量

**位置**：`src/core/real_reasoning_engine.py:2866`

### 3. 没有推理步骤（结果）

**原因**：
- 推理步骤生成超时后，`reasoning_steps` 被设置为空列表
- 系统检测到没有推理步骤，使用原始查询检索证据

**位置**：`src/core/real_reasoning_engine.py:2949-2951`

## 解决方案

### 方案1：增加超时时间（推荐）

将推理步骤生成的超时时间从30秒增加到60秒或更长：

```python
# 修改前
reasoning_steps = await asyncio.wait_for(reasoning_steps_task, timeout=30.0)

# 修改后
reasoning_steps = await asyncio.wait_for(reasoning_steps_task, timeout=60.0)  # 增加到60秒
```

### 方案2：改进错误处理和日志

添加更详细的日志，帮助诊断问题：

```python
try:
    reasoning_steps = await asyncio.wait_for(reasoning_steps_task, timeout=60.0)
except asyncio.TimeoutError:
    elapsed_time = time.time() - step_start
    self.logger.error(
        f"⚠️ 推理步骤生成超时（60秒），已耗时{elapsed_time:.2f}秒，使用回退方法"
    )
    self.logger.debug(f"查询: {query[:100]}...")
    reasoning_steps = []
except Exception as e:
    self.logger.error(f"⚠️ 推理步骤生成异常: {e}", exc_info=True)
    reasoning_steps = []
```

### 方案3：优化LLM调用

检查 `_execute_reasoning_steps_with_prompts` 方法中的LLM调用，确保：
- 使用正确的LLM客户端
- 提示词不会太长
- 有适当的重试机制

## 建议的修复

1. **立即修复**：增加超时时间到60秒
2. **短期优化**：改进错误处理和日志
3. **长期优化**：优化LLM调用性能

