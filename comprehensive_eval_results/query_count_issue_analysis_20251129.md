# 查询数量统计问题分析

**问题时间**: 2025-11-29  
**问题描述**: 用户只运行了1个样本，但评测报告显示"查询数量: 2"和"基于43个查询"

---

## 🔍 问题分析

### 1. "查询数量: 2" 的原因

**统计逻辑**:
```python
def _extract_query_count(self, log_content: str) -> int:
    query_patterns = [
        r"FRAMES sample=\d+/\d+",  # FRAMES样本格式
        r"处理查询|Processing query|Query processed",
        r"开始分析|Starting analysis|Analysis started",
        r"查询请求|Query request|Request received"
    ]
```

**实际情况**:
- 日志中 "FRAMES sample=1/1" 出现了2次：
  1. `FRAMES sample=1/1 started query=...`
  2. `FRAMES sample=1/1 success=True took=118.98s answer=...`
- 统计逻辑匹配了所有 "FRAMES sample=\d+/\d+" 的出现，所以统计为2

**问题**: 同一个样本的started和success都被统计为查询，导致数量翻倍

---

### 2. "基于43个查询" 的原因

**统计逻辑**:
```python
query_success_patterns = [
    r"查询成功|Query successful|Success",
    r"分析完成|Analysis completed|Completed",
    r"结果生成|Result generated|Generated"
]
```

**实际情况**:
- "Success" 模式匹配了43次
- 这些匹配主要来自日志中的诊断信息：
  - `success=True` (在多个地方出现)
  - `success: True` (ReAct Agent诊断信息)
  - `success=False` (ReAct Agent诊断信息)
  - `FRAMES sample=1/1 success=True` (这是真正的成功)

**问题**: "Success" 模式太宽泛，匹配到了所有包含"success"的日志行，包括：
- ReAct Agent内部的诊断信息
- 工具调用的成功/失败状态
- 其他非查询相关的成功标记

---

## 📊 实际统计结果

### 日志文件分析

- **FRAMES样本记录**: 2次（1个样本的started + success）
- **包含"Success"的日志行**: 43次（主要是诊断信息）
- **实际样本数量**: 1个
- **实际查询数量**: 1个

---

## 🔧 修复方案

### 方案1: 修复查询数量统计（推荐）

**问题**: 同一个样本的started和success都被统计

**修复**: 只统计唯一的样本ID

```python
def _extract_query_count(self, log_content: str) -> int:
    """提取查询数量 - 修复：只统计唯一样本"""
    # 方法1: 从FRAMES样本格式提取唯一样本ID
    frames_sample_pattern = r"FRAMES sample=(\d+)/\d+"
    sample_ids = set(re.findall(frames_sample_pattern, log_content, re.IGNORECASE))
    
    if sample_ids:
        return len(sample_ids)
    
    # 方法2: 回退到原有逻辑（如果没有FRAMES格式）
    query_patterns = [
        r"处理查询|Processing query|Query processed",
        r"开始分析|Starting analysis|Analysis started",
        r"查询请求|Query request|Request received"
    ]
    
    total_queries = 0
    for pattern in query_patterns:
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        total_queries += len(matches)
    
    return total_queries
```

---

### 方案2: 修复查询成功率统计（推荐）

**问题**: "Success" 模式太宽泛，匹配到了诊断信息

**修复**: 使用更精确的模式，排除诊断信息

```python
def _calculate_success_rate(self, log_content: str) -> Dict[str, Any]:
    """计算查询成功率和样本成功率 - 修复：使用更精确的模式"""
    # 1. 查询成功率（基于FRAMES样本格式）
    # 优先使用FRAMES样本格式，更准确
    frames_success_pattern = r"FRAMES sample=\d+/\d+\s+success=True"
    frames_success_matches = re.findall(frames_success_pattern, log_content, re.IGNORECASE)
    query_success_count = len(frames_success_matches)
    
    # 如果没有FRAMES格式，回退到原有逻辑（但排除诊断信息）
    if query_success_count == 0:
        query_success_patterns = [
            r"查询成功(?!.*success=True)",  # 排除包含success=True的行
            r"Query successful(?!.*success=True)",
            r"分析完成|Analysis completed",
            r"结果生成|Result generated"
        ]
        
        query_success_count = 0
        for pattern in query_success_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            query_success_count += len(matches)
    
    # 查询错误数量（同样使用精确模式）
    frames_error_pattern = r"FRAMES sample=\d+/\d+\s+success=False"
    frames_error_matches = re.findall(frames_error_pattern, log_content, re.IGNORECASE)
    query_error_count = len(frames_error_matches)
    
    # 如果没有FRAMES格式，回退到原有逻辑
    if query_error_count == 0:
        query_error_patterns = [
            r"查询失败|Query failed",
            r"分析错误|Analysis error",
            r"异常|Exception occurred"
        ]
        
        query_error_count = 0
        for pattern in query_error_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            query_error_count += len(matches)
    
    query_total = query_success_count + query_error_count
    query_success_rate = query_success_count / query_total if query_total > 0 else 0.0
    
    # 2. 样本成功率（保持不变）
    # ... 现有逻辑 ...
```

---

## ✅ 修复效果预期

修复后，对于1个样本的运行：
- **查询数量**: 1（而不是2）
- **基于X个查询**: 1（而不是43）
- **查询成功率**: 100% (基于1个查询)（而不是100% (基于43个查询)）

---

## 📝 实施建议

1. **立即修复**: 修复查询数量统计，使用唯一样本ID
2. **立即修复**: 修复查询成功率统计，使用更精确的模式（优先FRAMES格式）
3. **测试验证**: 重新运行评测，验证修复效果

---

**报告生成时间**: 2025-11-29

