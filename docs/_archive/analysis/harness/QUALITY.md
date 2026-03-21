# RANGEN 质量标准

> 详细说明代码质量和验证标准

---

## 验证层次

### 1. 自动化验证

| 类型 | 工具 | 频率 |
|------|------|------|
| Lint | Ruff, Pylint | 每次保存 |
| Type | mypy | 每次提交 |
| Test | pytest | 每次 PR |

### 2. 质量指标

- **测试覆盖率**: > 70%
- **Lint 通过率**: 100%
- **Type 检查**: 0 错误

---

## 任务契约

使用 `TaskContract` 定义完成标准：

```python
contract = create_contract(
    "task_id",
    "任务描述",
    verifications=[
        {"id": "test", "type": "test", "criteria": "pytest passes"},
        {"id": "lint", "type": "assertion", "criteria": "ruff passes"}
    ]
)
```

### 验证类型

- `test`: 运行测试
- `screenshot`: UI 截图验证
- `manual`: 人工验证
- `assertion`: 断言验证
- `file_exists`: 文件存在验证

---

## 评审流程

```
代码 → Agent Review → Human Review → 合并
         ↓
    质量评分 < 阈值 → 拒绝
```

---

## 禁止绕过

- ❌ 修改测试来通过验证
- ❌ 跳过 lint 检查
- ❌ 忽略 type 错误

---

## Agent Linter (P3)

Agent 友好的 Linter，错误消息包含修复建议。

### 使用方式

```python
from src.core.agent_linter import lint_file, auto_fix_file

# lint 单个文件
result = lint_file("src/core/main.py")
print(result["issues"][0]["fix"])  # "未使用的导入，可以删除..."

# 自动修复
auto_fix_file("src/core/main.py")
```

### 特点

- 错误消息包含 `fix_suggestion` 字段
- 支持自动修复 (`--fix`)
- 结构化 JSON 输出

---

## Agent 自动化评审 (P4)

Agent ↔ Agent 评审循环，人类只在关键节点介入。

### 使用方式

```python
from src.core.agent_reviewer import review_code, CodeChange

change = CodeChange(
    file_path="src/core/main.py",
    diff="+ new line\n- old line"
)
result = review_code("src/core/main.py", "+ new line")
print(result["decision"])  # "approve" / "request_changes"
```

### 评审流程

```
Agent A 写代码 → Agent Reviewer 评审 → 需要修改? → Agent A 修复 → 再次评审
                                                    ↓
                                              通过 → 标记待人类审批
```

### 质量分数

- **>= 85**: 自动批准
- **70-84**: 需要人类审批
- **< 70**: 拒绝，要求修改

---

## Agent 可观测性 (P5)

Agent 可查询运行时日志/指标，进行自我验证。

### 使用方式

```python
import asyncio
from src.core.agent_observability_client import query_logs, query_metric

# 查询日志
logs = asyncio.run(query_logs("error", time_range="1h"))

# 查询指标
metrics = asyncio.run(query_metric("latency", time_range="1h"))
```

### 功能

- 查询应用/系统/Agent 日志
- 查询延迟/错误/Token/质量指标
- 任务执行自我验证
