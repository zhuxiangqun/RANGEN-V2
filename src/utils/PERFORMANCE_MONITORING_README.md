# 增强性能监控系统使用指南

## 概述

增强性能监控系统提供了模块级别的详细性能跟踪和评测报告功能。

## 核心功能

### 1. 模块执行跟踪
- 记录每个模块的执行时间
- 跟踪执行路径类型（main, fallback, exception, simple）
- 监控子模块性能
- 记录异常和回退原因

### 2. 评测报告
- 完整的评测生命周期管理
- 自动瓶颈识别
- 智能优化建议
- 详细的性能分析

## 使用方法

### 装饰器方式（推荐）
```python
@monitor_module_performance("knowledge_retrieval", "main")
def knowledge_retrieval_module(query: str):
    pass
```

### 上下文管理器
```python
with ModulePerformanceContext("complex_function", "main") as ctx:
    pass
```

## 执行路径类型

- **main**: 正常主流程
- **fallback**: 回退处理
- **exception**: 异常处理
- **simple**: 简化处理

## 评测流程

```python
start_evaluation("evaluation_001")
# 执行评测任务
report = end_evaluation()
```

## 报告内容

- 模块执行时间
- 执行路径统计
- 性能瓶颈分析
- 优化建议
