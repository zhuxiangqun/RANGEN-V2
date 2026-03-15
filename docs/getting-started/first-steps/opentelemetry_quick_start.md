# OpenTelemetry 追踪快速启动指南

## 📋 概述

OpenTelemetry 监控功能**默认启用**（如果已安装），无需手动启动。本指南说明如何安装、配置和查看 OpenTelemetry 追踪数据。

## 🚀 快速启动（3步）

### 步骤1：安装 OpenTelemetry

**方法1：使用安装脚本（推荐）**
```bash
bash scripts/install_opentelemetry.sh
```

**方法2：手动安装**
```bash
pip install opentelemetry-api opentelemetry-sdk
```

**方法3：从依赖文件安装**
```bash
pip install -r requirements_langgraph.txt
```

### 步骤2：启动系统（OpenTelemetry 自动启用）

OpenTelemetry 会在系统启动时**自动初始化**，无需手动启动：

```bash
# 启动可视化服务器（OpenTelemetry 自动启用）
python examples/start_visualization_server.py
```

系统启动时，如果 OpenTelemetry 已安装，你会看到：
```
✅ OpenTelemetry 初始化成功
✅ OpenTelemetry 监控已启用
```

### 步骤3：查看追踪数据

根据你使用的导出器，查看方式不同：

## 📊 查看追踪数据的方法

### 方法1：控制台导出器（默认，最简单）

**特点**：
- ✅ 无需额外配置
- ✅ 开箱即用
- ✅ 数据输出到日志文件

**查看方法**：

```bash
# 查看实时日志
tail -f logs/research_system.log

# 或查看最近的追踪数据
grep -i "span\|trace\|opentelemetry" logs/research_system.log | tail -20
```

**输出示例**：
```
{
    "name": "node.route_query",
    "context": {...},
    "kind": "SpanKind.INTERNAL",
    "attributes": {
        "node.name": "route_query",
        "query": "What is AI?",
        "complexity_score": 3.5,
        "route_path": "complex"
    },
    "status": {"status_code": "OK"},
    "events": [...]
}
```

### 方法2：Jaeger UI（可视化界面，推荐用于生产环境）

**步骤1：安装 Jaeger 导出器**
```bash
pip install opentelemetry-exporter-jaeger-thrift
```

**步骤2：启动 Jaeger（使用 Docker）**
```bash
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest
```

**步骤3：配置环境变量**
```bash
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=jaeger
export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces
```

**步骤4：启动系统**
```bash
python examples/start_visualization_server.py
```

**步骤5：访问 Jaeger UI**
```
http://localhost:16686
```

在 Jaeger UI 中：
1. 选择服务：`langgraph-workflow`
2. 点击 "Find Traces"
3. 查看追踪数据

**查看内容**：
- 📊 完整的执行路径
- ⏱️ 每个节点的执行时间
- 🔍 节点执行的详细信息
- ❌ 错误和异常记录

### 方法3：Zipkin UI（另一个可视化界面）

**步骤1：安装 Zipkin 导出器**
```bash
pip install opentelemetry-exporter-zipkin-json
```

**步骤2：启动 Zipkin（使用 Docker）**
```bash
docker run -d \
  --name zipkin \
  -p 9411:9411 \
  openzipkin/zipkin
```

**步骤3：配置环境变量**
```bash
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=zipkin
export OPENTELEMETRY_ENDPOINT=http://localhost:9411/api/v2/spans
```

**步骤4：启动系统**
```bash
python examples/start_visualization_server.py
```

**步骤5：访问 Zipkin UI**
```
http://localhost:9411
```

### 方法4：OTLP 导出器（通用协议）

**步骤1：安装 OTLP 导出器**
```bash
pip install opentelemetry-exporter-otlp-proto-grpc
```

**步骤2：配置环境变量**
```bash
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=otlp
export OPENTELEMETRY_ENDPOINT=http://localhost:4317
```

**步骤3：启动系统**
```bash
python examples/start_visualization_server.py
```

OTLP 可以连接到多种后端：
- Jaeger
- Prometheus
- Grafana Tempo
- 其他支持 OTLP 的监控系统

## 🔍 追踪数据内容

OpenTelemetry 追踪包含以下信息：

### 1. 工作流构建追踪
- `workflow.build` span - 工作流构建过程
- 包含构建时间、节点数量等信息

### 2. 节点执行追踪
每个节点都有独立的 span，包含：
- **节点名称**：`node.route_query`, `node.simple_query` 等
- **查询内容**：查询的前100个字符
- **复杂度评分**：查询的复杂度评分
- **路由路径**：simple/complex/multi_agent
- **执行时间**：节点执行耗时
- **重试次数**：如果节点重试
- **状态**：成功/失败
- **错误信息**：如果执行失败

### 3. 指标数据
- `node_execution_total` - 节点执行总次数
- `node_execution_duration_seconds` - 节点执行耗时
- `token_usage_total` - Token 使用总数

## 🎯 实际使用示例

### 示例1：使用控制台导出器（开发环境）

```bash
# 1. 安装 OpenTelemetry
pip install opentelemetry-api opentelemetry-sdk

# 2. 启动系统（OpenTelemetry 自动启用）
python examples/start_visualization_server.py

# 3. 在另一个终端查看日志
tail -f logs/research_system.log | grep -i "span\|trace"
```

### 示例2：使用 Jaeger UI（生产环境）

```bash
# 1. 安装 OpenTelemetry 和 Jaeger 导出器
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger-thrift

# 2. 启动 Jaeger
docker run -d --name jaeger -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest

# 3. 配置环境变量
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=jaeger
export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces

# 4. 启动系统
python examples/start_visualization_server.py

# 5. 访问 Jaeger UI
# 打开浏览器访问: http://localhost:16686
```

### 示例3：在代码中查看追踪状态

```python
from src.core.langgraph_opentelemetry_integration import (
    OPENTELEMETRY_AVAILABLE,
    tracer
)

# 检查 OpenTelemetry 是否可用
if OPENTELEMETRY_AVAILABLE:
    print("✅ OpenTelemetry 已启用")
    print(f"追踪器: {tracer}")
else:
    print("❌ OpenTelemetry 未安装")
```

## 🔧 配置选项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_OPENTELEMETRY` | `true` | 是否启用 OpenTelemetry |
| `OPENTELEMETRY_EXPORTER` | `console` | 导出器类型（console/jaeger/zipkin/otlp） |
| `OPENTELEMETRY_ENDPOINT` | - | 导出器端点（仅 jaeger/zipkin/otlp 需要） |

### 在 `.env` 文件中配置

创建或编辑 `.env` 文件：

```env
# OpenTelemetry 配置
ENABLE_OPENTELEMETRY=true
OPENTELEMETRY_EXPORTER=console  # 或 jaeger, zipkin, otlp
OPENTELEMETRY_ENDPOINT=  # 可选，仅在使用 jaeger/zipkin/otlp 时需要
```

## 📝 验证 OpenTelemetry 是否正常工作

### 方法1：检查日志

启动系统后，查看日志中是否有：
```
✅ OpenTelemetry 初始化成功
✅ OpenTelemetry 监控已启用
```

### 方法2：检查健康状态

访问健康检查端点：
```bash
curl http://localhost:8080/api/workflow/health
```

检查返回的 JSON 中的 `langgraph_available` 状态。

### 方法3：执行查询并查看追踪

1. 执行一个查询
2. 查看日志或 Jaeger UI 中是否有追踪数据

## 🎉 总结

OpenTelemetry 追踪功能：

- ✅ **自动启动**：系统启动时自动初始化，无需手动启动
- ✅ **默认启用**：如果已安装，默认启用（除非明确禁用）
- ✅ **多种导出器**：支持控制台、Jaeger、Zipkin、OTLP
- ✅ **详细追踪**：追踪工作流构建和节点执行
- ✅ **易于查看**：通过日志或可视化界面查看

**最简单的使用方式**：
1. 安装 OpenTelemetry：`pip install opentelemetry-api opentelemetry-sdk`
2. 启动系统：`python examples/start_visualization_server.py`
3. 查看日志：`tail -f logs/research_system.log`

就这么简单！

