# OpenTelemetry 监控集成指南 - 阶段2.5

## 概述

OpenTelemetry 集成提供了分布式追踪和指标收集功能，可以帮助监控和分析工作流的执行情况。

## 功能特性

- ✅ 节点执行追踪（Span）
- ✅ 自定义指标（Counter、Histogram）
- ✅ Token 使用追踪
- ✅ API 调用追踪
- ✅ 错误追踪
- ✅ 支持多种导出器（Console、Jaeger、Zipkin、OTLP）

## 安装依赖

### 基础依赖（必需）

```bash
pip install opentelemetry-api opentelemetry-sdk
```

### 导出器依赖（可选）

**Jaeger 导出器**：
```bash
pip install opentelemetry-exporter-jaeger-thrift
```

**Zipkin 导出器**：
```bash
pip install opentelemetry-exporter-zipkin-json
```

**OTLP 导出器**（通用）：
```bash
pip install opentelemetry-exporter-otlp-proto-grpc
```

## 配置

### 环境变量

```bash
# 启用 OpenTelemetry
ENABLE_OPENTELEMETRY=true

# 导出器类型（console, jaeger, zipkin, otlp）
OPENTELEMETRY_EXPORTER=jaeger

# 导出器端点（可选）
OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces
```

### 代码配置

```python
from src.core.langgraph_opentelemetry_integration import (
    initialize_opentelemetry,
    configure_opentelemetry_exporter
)

# 初始化 OpenTelemetry
initialize_opentelemetry(
    exporter_type="jaeger",
    endpoint="http://localhost:14268/api/traces",
    enabled=True
)
```

## 使用方式

### 1. 自动集成（推荐）

如果设置了环境变量 `ENABLE_OPENTELEMETRY=true`，系统会自动为所有节点添加追踪。

### 2. 手动装饰节点

```python
from src.core.langgraph_opentelemetry_integration import traced_node

@traced_node("my_node")
async def my_node(state: ResearchSystemState) -> ResearchSystemState:
    # 节点逻辑
    return state
```

## 导出器设置

### Console 导出器（默认）

追踪数据会输出到控制台，适合开发和调试。

### Jaeger 导出器

1. **启动 Jaeger**（使用 Docker）：
```bash
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest
```

2. **配置环境变量**：
```bash
ENABLE_OPENTELEMETRY=true
OPENTELEMETRY_EXPORTER=jaeger
OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces
```

3. **访问 Jaeger UI**：
打开浏览器访问：`http://localhost:16686`

### Zipkin 导出器

1. **启动 Zipkin**（使用 Docker）：
```bash
docker run -d -p 9411:9411 openzipkin/zipkin
```

2. **配置环境变量**：
```bash
ENABLE_OPENTELEMETRY=true
OPENTELEMETRY_EXPORTER=zipkin
OPENTELEMETRY_ENDPOINT=http://localhost:9411/api/v2/spans
```

3. **访问 Zipkin UI**：
打开浏览器访问：`http://localhost:9411`

## 追踪数据

### Span 属性

每个节点执行会创建以下 Span 属性：
- `node.name`: 节点名称
- `query`: 查询文本（前100字符）
- `complexity_score`: 复杂度分数
- `route_path`: 路由路径
- `retry_count`: 重试次数
- `duration_seconds`: 执行时间
- `success`: 是否成功

### 指标

系统会收集以下指标：
- `node_execution_total`: 节点执行总次数（带 status 标签）
- `node_execution_duration_seconds`: 节点执行耗时（Histogram）
- `token_usage_total`: Token 使用总数（带 node 和 type 标签）

## 可视化

### Jaeger UI

在 Jaeger UI 中可以：
- 查看工作流执行轨迹
- 可视化节点执行时间和依赖关系
- 查看详细的追踪信息
- 分析性能瓶颈

### Zipkin UI

在 Zipkin UI 中可以：
- 查看服务追踪
- 分析延迟
- 查看依赖关系

## 注意事项

1. **可选依赖**：OpenTelemetry 是可选依赖，如果未安装，系统会正常 work，只是没有追踪功能
2. **性能影响**：追踪会带来少量性能开销，生产环境建议使用采样
3. **数据量**：追踪数据可能很大，建议配置适当的保留策略

## 故障排除

### 问题：追踪数据没有显示

1. 检查 OpenTelemetry 是否安装：`pip list | grep opentelemetry`
2. 检查环境变量是否正确设置
3. 检查导出器端点是否可访问
4. 查看日志中的错误信息

### 问题：Jaeger/Zipkin 连接失败

1. 确认服务已启动：`docker ps | grep jaeger` 或 `docker ps | grep zipkin`
2. 检查端口是否正确映射
3. 检查防火墙设置

## 相关文档

- [OpenTelemetry Python 文档](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger 文档](https://www.jaegertracing.io/docs/)
- [Zipkin 文档](https://zipkin.io/)

