# 三个问题分析报告

## 问题1：两次LLM查询可以合并

### 当前情况
- **查询类型分析**：`_analyze_query_type_with_ml` 在 `reason` 方法中调用（第2580行）
- **复杂度判断**：`_estimate_query_complexity_with_llm` 在 `_select_llm_for_task` 中调用（第11116行）
- **问题**：两次独立的LLM调用，增加了延迟和成本

### 优化方案
**合并为一次LLM调用**，同时返回查询类型和复杂度：

```python
def _analyze_query_and_complexity_with_llm(self, query: str, evidence_count: Optional[int] = None) -> Dict[str, Any]:
    """一次性分析查询类型和复杂度"""
    prompt = f"""Analyze the following query and return JSON format:
{{
    "query_type": "factual|numerical|temporal|causal|ranking|comparison|general",
    "complexity": "simple|medium|complex"
}}

Query: {query[:500]}
Evidence count: {evidence_count or 0}

Return ONLY the JSON, no other text."""
    
    response = self._call_deepseek(prompt, skip_complexity_estimation=True)
    # 解析JSON返回
    return {"query_type": "...", "complexity": "..."}
```

### 预期效果
- **减少延迟**：从2次LLM调用减少到1次，节省约3-10秒
- **降低成本**：减少50%的LLM调用次数
- **提高效率**：一次调用获取两个信息

---

## 问题2：查询和答案变成中文

### 当前情况
用户反馈：
- 查询：`美国首都华盛顿特区属于哪个州？土拨鼠日普苏塔尼菲尔的首次预测年份是什么时候？`
- 答案：`华盛顿特区不属于任何州；土拨鼠日普苏塔尼菲尔的首次预测年份是1887年`

这些应该是英文的，但显示为中文。

### 可能原因

#### 原因1：提示词模板使用中文
在 `_extract_with_llm` 方法中（第4124-4189行），提示词模板使用了中文：

```python
prompt_template = """从以下响应中提取答案（理解语义，不依赖格式）：

查询：{query}
查询类型：{query_type}
响应：{response}
...
"""
```

**问题**：虽然提示词是中文，但LLM应该返回英文答案。如果LLM返回中文，可能是：
1. LLM模型配置问题
2. 提示词中的语言暗示导致LLM返回中文
3. 输入查询本身就是中文

#### 原因2：日志输出使用中文标签
日志中使用了中文标签，如：
- `查询: {query}`
- `答案: {answer}`

但这只是日志格式，不应该影响实际查询和答案内容。

#### 原因3：输入数据本身是中文
如果输入的FRAMES数据集中的查询本身就是中文，那么答案也会是中文。

### 解决方案

#### 方案1：修改提示词为英文（推荐）
将所有提示词模板改为英文：

```python
prompt_template = """Extract the answer from the following response (understand semantics, not format-dependent):

Query: {query}
Query type: {query_type}
Response: {response}

Please extract the direct answer to the query, requirements:
1. Extract only the answer itself, do not include reasoning process or explanations
...
"""
```

#### 方案2：在提示词中明确要求英文
在提示词中添加语言要求：

```python
prompt_template = """...（中文提示词）...

**IMPORTANT**: The answer must be in English, even if the query is in Chinese.
Return the answer in English format.
"""
```

#### 方案3：检查输入数据
确认FRAMES数据集中的查询是否是英文的。

### 预期效果
- 确保答案始终是英文格式
- 保持与FRAMES数据集的一致性
- 提高国际化兼容性

---

## 问题3：活跃连接数为0

### 当前情况
评测报告显示：`活跃连接数: 0`

### 代码分析
在 `evaluation_system/comprehensive_evaluation.py` 中（第513-521行）：

```python
def _extract_connections(self, log_content: str) -> int:
    """提取活跃连接数"""
    # 🚀 修复：优先从系统健康指标中提取活跃连接数
    # 格式：系统健康指标: 活跃连接数 X
    health_pattern = r"系统健康指标:\s*活跃连接数\s*(\d+)"
    matches = re.findall(health_pattern, log_content)
    if matches:
        # 返回最后一个记录的活跃连接数
        return int(matches[-1])
    return 0
```

### 问题分析
1. **提取逻辑**：从日志中查找 `系统健康指标: 活跃连接数 X` 格式的文本
2. **如果没有找到**：返回0
3. **可能原因**：
   - 日志中没有记录系统健康指标
   - 系统没有输出活跃连接数信息
   - 连接数统计功能未启用

### 是否正常？
**可能是正常的**，因为：
1. 系统可能没有记录连接数信息
2. 如果使用的是同步调用，可能没有活跃连接的概念
3. 连接数统计可能不是核心功能

### 解决方案

#### 方案1：检查日志中是否有连接数信息
```bash
grep -i "活跃连接数\|active.*connection" research_system.log
```

#### 方案2：如果确实需要统计连接数
在系统健康检查中添加连接数统计：

```python
# 在系统健康检查中记录连接数
active_connections = get_active_connections()  # 需要实现
log_info(f"系统健康指标: 活跃连接数 {active_connections}")
```

#### 方案3：如果不需要连接数统计
可以忽略这个指标，或者从评测报告中移除。

### 建议
- **如果系统确实没有连接数统计**：这是正常的，可以忽略
- **如果需要连接数统计**：需要实现连接数监控功能
- **如果只是评测指标**：可以考虑移除或标记为"不适用"

---

## 总结

### 优先级排序

1. **高优先级** 🔴
   - **问题2：中文问题** - 影响答案格式和准确性
   - **问题1：两次LLM查询** - 影响性能和成本

2. **中优先级** 🟡
   - **问题3：活跃连接数为0** - 可能是正常的，需要确认

### 实施建议

1. **立即修复问题2**：将提示词模板改为英文，确保答案格式正确
2. **优化问题1**：合并查询类型分析和复杂度判断为一次LLM调用
3. **确认问题3**：检查日志，确认是否需要连接数统计

