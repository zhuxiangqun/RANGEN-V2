# OpenTelemetry 可选安装指南

## 概述

OpenTelemetry 是一个**可选**的监控和追踪功能，用于收集工作流节点的执行指标和追踪信息。

## 当前状态

- ⚠️ **警告信息**: `⚠️ OpenTelemetry 未安装，监控功能将不可用`
- ✅ **系统状态**: 正常工作，有完善的回退机制
- ✅ **测试状态**: 所有测试可以正常运行

## 是否需要安装？

### 可以忽略的情况（推荐）

如果您：
- ✅ 只需要运行测试和基本功能
- ✅ 不需要详细的监控追踪数据
- ✅ 希望减少依赖项

**建议**: 可以忽略这个警告，系统会正常工作。

### 需要安装的情况

如果您：
- 📊 需要详细的性能监控数据
- 🔍 需要追踪工作流节点的执行情况
- 📈 需要集成到监控系统（Jaeger、Zipkin、OTLP等）

**建议**: 安装 OpenTelemetry 以启用监控功能。

## 安装方法

### 基础安装

```bash
pip install opentelemetry-api opentelemetry-sdk
```

### 完整安装（包含导出器）

```bash
# 基础包
pip install opentelemetry-api opentelemetry-sdk

# 控制台导出器（默认，已包含在sdk中）
# 无需额外安装

# Jaeger 导出器（可选）
pip install opentelemetry-exporter-jaeger-thrift

# Zipkin 导出器（可选）
pip install opentelemetry-exporter-zipkin-json

# OTLP 导出器（可选）
pip install opentelemetry-exporter-otlp-proto-grpc
```

## 启用方法

安装后，通过环境变量启用：

```bash
# 启用 OpenTelemetry（使用控制台导出器）
export ENABLE_OPENTELEMETRY=true

# 或使用其他导出器
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=jaeger  # 或 zipkin, otlp
export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces
```

## 功能说明

### 提供的监控功能

1. **节点执行追踪**: 追踪每个节点的执行时间和状态
2. **性能指标**: 收集节点执行次数、耗时等指标
3. **Token 使用统计**: 追踪 LLM 调用的 token 使用情况
4. **错误追踪**: 记录节点执行中的错误信息

### 导出器类型

- **console**: 控制台输出（默认，用于开发调试）
- **jaeger**: Jaeger 分布式追踪系统
- **zipkin**: Zipkin 分布式追踪系统
- **otlp**: OpenTelemetry Protocol（用于各种后端）

## 代码实现

系统已经实现了完善的回退机制：

```python
# 如果 OpenTelemetry 不可用
try:
    from src.core.langgraph_opentelemetry_integration import traced_node
except ImportError:
    # 无操作装饰器，不影响功能
    traced_node = lambda name: lambda func: func
```

装饰器会自动检查可用性：

```python
@traced_node("my_node")
async def my_node(state):
    # 如果 OpenTelemetry 不可用，直接执行
    if not OPENTELEMETRY_AVAILABLE:
        return await node_func(state)
    # 否则添加追踪
    ...
```

## 总结

- ✅ **不是必须的**: 可以忽略警告，系统正常工作
- ✅ **不影响测试**: 所有测试可以正常运行
- 📊 **可选功能**: 如果需要监控，可以安装
- 🔧 **易于启用**: 安装后通过环境变量启用

**建议**: 对于测试和开发，可以忽略这个警告。如果需要生产环境的监控，再安装 OpenTelemetry。

