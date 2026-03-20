# 提示词使用优先级说明

生成时间: 2025-12-04

## 一、实际使用流程

### 1.1 主要路径（正常情况，99%的情况）

```
step_generator.execute_reasoning_steps_with_prompts()
  ↓
prompt_generator.generate_optimized_prompt("reasoning_steps_generation", ...)
  ↓
prompt_engineering.generate_prompt(template_name, **prompt_kwargs)
  ↓
从 templates/templates.json 加载模板 ✅ 这是主要使用的！
  ↓
替换占位符 {query}, {context}, {evidence}
  ↓
返回最终提示词
```

### 1.2 Fallback路径（异常情况，<1%的情况）

```
只有当 generate_optimized_prompt 返回 None 或抛出异常时
  ↓
使用 _get_fallback_reasoning_steps_prompt()
  ↓
这是硬编码的备用提示词 ⚠️ 只是备用方案
```

## 二、重点应该放在哪里？

**重点应该放在模板提示词（templates/templates.json）上！**

因为：
1. ✅ 这是正常情况下的主要使用路径
2. ✅ 99%的情况下都会使用这个模板
3. ✅ Fallback只是异常情况的备用方案

## 三、为什么两个都需要更新？

虽然重点在模板，但两个都需要更新是为了：
1. **保持一致性**：确保即使fallback被触发，也能使用改进后的提示词
2. **防御性编程**：防止模板加载失败时系统降级
3. **完整性**：确保所有路径都使用改进后的提示词

## 四、建议

1. **主要关注**：`templates/templates.json` 中的 `reasoning_steps_generation` 模板
2. **次要关注**：`step_generator.py` 中的 `_get_fallback_reasoning_steps_prompt()` 方法
3. **验证方式**：检查日志，确认系统实际使用的是哪个提示词

---

**报告生成时间**: 2025-12-04

