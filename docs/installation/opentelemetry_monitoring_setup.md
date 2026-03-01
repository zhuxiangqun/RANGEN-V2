# OpenTelemetry 监控功能设置指南

## 📋 概述

OpenTelemetry 监控功能现在**默认启用**（如果已安装），为系统提供分布式追踪和性能监控能力。

## 🚀 快速安装

### 方法1：使用安装脚本（推荐）

```bash
bash scripts/install_opentelemetry.sh
```

这个脚本会：
- 安装 OpenTelemetry 核心包（`opentelemetry-api` 和 `opentelemetry-sdk`）
- 可选安装导出器（Jaeger、Zipkin、OTLP）
- 提供使用说明

### 方法2：手动安装

```bash
# 安装核心包
pip install opentelemetry-api>=1.20.0 opentelemetry-sdk>=1.20.0

# 可选：安装导出器（根据需要选择）
pip install opentelemetry-exporter-jaeger-thrift      # Jaeger 导出器
pip install opentelemetry-exporter-zipkin-json        # Zipkin 导出器
pip install opentelemetry-exporter-otlp-proto-grpc    # OTLP 导出器
```

### 方法3：从依赖文件安装

```bash
pip install -r requirements_langgraph.txt
```

`requirements_langgraph.txt` 已包含 OpenTelemetry 依赖。

## ✅ 默认行为

**OpenTelemetry 现在默认启用**（如果已安装）：

- ✅ 如果 OpenTelemetry 已安装，监控功能**自动启用**
- ✅ 无需设置环境变量即可使用
- ✅ 默认使用控制台导出器（输出到日志）

## ⚙️ 配置选项

### 禁用 OpenTelemetry

如果不想使用 OpenTelemetry 监控，可以设置环境变量：

```bash
export ENABLE_OPENTELEMETRY=false
```

或在 `.env` 文件中：

```env
ENABLE_OPENTELEMETRY=false
```

### 使用其他导出器

默认使用控制台导出器。如需使用其他导出器（如 Jaeger、Zipkin），设置环境变量：

```bash
# 使用 Jaeger 导出器
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=jaeger
export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces

# 使用 Zipkin 导出器
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=zipkin
export OPENTELEMETRY_ENDPOINT=http://localhost:9411/api/v2/spans

# 使用 OTLP 导出器
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=otlp
export OPENTELEMETRY_ENDPOINT=http://localhost:4317
```

### 在 `.env` 文件中配置

创建或编辑 `.env` 文件：

```env
# OpenTelemetry 配置（默认启用）
ENABLE_OPENTELEMETRY=true
OPENTELEMETRY_EXPORTER=console  # console, jaeger, zipkin, otlp
OPENTELEMETRY_ENDPOINT=  # 可选，仅在使用 jaeger/zipkin/otlp 时需要
```

## 📊 监控功能

OpenTelemetry 提供以下监控能力：

### 1. 分布式追踪

- **节点执行追踪**：追踪每个工作流节点的执行
- **执行路径**：记录完整的执行路径
- **性能分析**：分析每个节点的执行时间

### 2. 指标收集

- **节点执行次数**：`node_execution_total`
- **节点执行耗时**：`node_execution_duration_seconds`
- **Token 使用量**：`token_usage_total`

### 3. 追踪信息

每个节点追踪包含：
- 节点名称
- 查询内容（前100字符）
- 复杂度评分
- 路由路径
- 重试次数
- 执行时间

## 🔍 查看监控数据

### 控制台导出器（默认）

监控数据会输出到日志中，查看日志文件即可：

```bash
tail -f logs/research_system.log
```

### Jaeger UI

如果使用 Jaeger 导出器：

1. 启动 Jaeger（使用 Docker）：
   ```bash
   docker run -d -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest
   ```

2. 访问 Jaeger UI：http://localhost:16686

3. 查看追踪数据

### Zipkin UI

如果使用 Zipkin 导出器：

1. 启动 Zipkin（使用 Docker）：
   ```bash
   docker run -d -p 9411:9411 openzipkin/zipkin
   ```

2. 访问 Zipkin UI：http://localhost:9411

3. 查看追踪数据

## 📝 验证安装

运行以下命令验证 OpenTelemetry 是否已安装：

```bash
python3 -c "from opentelemetry import trace; print('✅ OpenTelemetry 已安装')"
```

如果看到 "✅ OpenTelemetry 已安装"，说明安装成功。

## 🎯 使用示例

### 示例1：使用默认配置（控制台导出器）

无需任何配置，直接运行系统即可：

```bash
python examples/start_visualization_server.py
```

监控数据会自动输出到日志。

### 示例2：使用 Jaeger 导出器

```bash
# 设置环境变量
export ENABLE_OPENTELEMETRY=true
export OPENTELEMETRY_EXPORTER=jaeger
export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces

# 启动系统
python examples/start_visualization_server.py
```

## 🔧 故障排查

### 问题1：仍然看到 "OpenTelemetry 未安装" 信息

**解决方案**：
1. 确认已安装：`pip list | grep opentelemetry`
2. 如果未安装，运行：`bash scripts/install_opentelemetry.sh`
3. 重启系统

### 问题2：监控数据没有输出

**检查清单**：
1. 确认 OpenTelemetry 已安装
2. 确认 `ENABLE_OPENTELEMETRY` 未设置为 `false`
3. 检查日志文件是否有错误信息
4. 确认导出器配置正确（如果使用 Jaeger/Zipkin）

### 问题3：Jaeger/Zipkin 连接失败

**解决方案**：
1. 确认 Jaeger/Zipkin 服务正在运行
2. 检查 `OPENTELEMETRY_ENDPOINT` 是否正确
3. 检查网络连接和防火墙设置

## 📚 相关文档

- [OpenTelemetry 集成指南](../implementation/opentelemetry_integration_guide.md)
- [系统使用指南](../usage/system_usage_guide.md)
- [性能监控文档](../implementation/phase2_completion_summary.md)

## 🎉 总结

现在 OpenTelemetry 监控功能：
- ✅ **默认启用**（如果已安装）
- ✅ **自动初始化**（无需手动配置）
- ✅ **易于使用**（控制台导出器开箱即用）
- ✅ **可扩展**（支持 Jaeger、Zipkin、OTLP）

只需安装 OpenTelemetry，监控功能就会自动工作！

