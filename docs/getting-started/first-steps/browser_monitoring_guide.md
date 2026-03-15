# 浏览器监控功能使用指南

## 📋 概述

现在可以通过浏览器界面直接查看系统监控信息，包括：
- **系统健康状态**：工作流状态、组件可用性
- **性能指标**：节点执行次数、Token 使用、平均执行时间
- **OpenTelemetry 追踪**：节点执行追踪数据

## 🚀 快速开始

### 步骤1：启动可视化服务器

```bash
python examples/start_visualization_server.py
```

### 步骤2：打开浏览器

访问：`http://localhost:8080`

### 步骤3：切换到 Monitoring Tab

在浏览器界面顶部，点击 **"Monitoring"** 标签页。

## 📊 监控面板说明

### 1. System Health（系统健康状态）

显示系统的整体健康状态和各项检查结果：

- **Overall Status**：整体状态（healthy/degraded/unhealthy/error）
- **各项检查**：
  - `system_initialized` - 系统是否已初始化
  - `workflow_instance` - 工作流实例是否存在
  - `workflow_property` - 工作流属性是否可用
  - `langgraph_available` - LangGraph 是否可用
  - 等等

**颜色说明**：
- 🟢 **绿色**：正常（OK）
- 🟠 **橙色**：警告（Warning）
- 🔴 **红色**：错误（Error）

### 2. Performance Metrics（性能指标）

显示系统的性能统计数据：

- **节点执行**：总执行次数
- **Token 使用**：总 Token 数
- **平均执行时间**：平均执行时间（秒）

**注意**：执行查询后，这些指标会实时更新。

### 3. OpenTelemetry Traces（OpenTelemetry 追踪）

显示 OpenTelemetry 追踪数据：

- **追踪列表**：最近的节点执行追踪
- **状态**：每个追踪的状态（OK/ERROR）
- **持续时间**：执行时间（如果可用）

**如果显示 "OpenTelemetry 未启用"**：
1. 安装 OpenTelemetry：`pip install opentelemetry-api opentelemetry-sdk`
2. 重启系统
3. 查看 [OpenTelemetry 快速启动指南](./opentelemetry_quick_start.md)

## 🔄 自动刷新

当切换到 **Monitoring** 标签页时，监控信息会：
- **立即加载**：切换到该标签页时立即加载
- **自动刷新**：每 5 秒自动刷新一次
- **手动刷新**：点击 "Refresh" 按钮手动刷新

离开 **Monitoring** 标签页时，自动刷新会停止。

## 📝 使用示例

### 示例1：查看系统健康状态

1. 启动系统：`python examples/start_visualization_server.py`
2. 打开浏览器：`http://localhost:8080`
3. 点击 **"Monitoring"** 标签页
4. 查看 **System Health** 面板

如果看到：
- ✅ **Overall Status: HEALTHY** - 系统正常
- ⚠️ **Overall Status: DEGRADED** - 系统降级（部分功能不可用）
- ❌ **Overall Status: UNHEALTHY** - 系统不健康

### 示例2：查看性能指标

1. 执行一个查询（在 "Workflow Graph" 或 "Execution Details" 标签页）
2. 切换到 **"Monitoring"** 标签页
3. 查看 **Performance Metrics** 面板

你会看到：
- 节点执行次数
- Token 使用量
- 平均执行时间

### 示例3：查看 OpenTelemetry 追踪

**前提条件**：OpenTelemetry 已安装并启用

1. 确保 OpenTelemetry 已安装：`pip install opentelemetry-api opentelemetry-sdk`
2. 启动系统（OpenTelemetry 会自动启用）
3. 执行一个查询
4. 切换到 **"Monitoring"** 标签页
5. 查看 **OpenTelemetry Traces** 面板

你会看到最近的节点执行追踪数据。

## 🔧 故障排查

### 问题1：监控面板显示 "Loading..." 或 "加载失败"

**可能原因**：
- 后端服务未启动
- API 端点不可用

**解决方案**：
1. 检查后端服务是否正在运行
2. 查看浏览器控制台（F12）的错误信息
3. 检查后端日志

### 问题2：性能指标显示 "暂无数据"

**可能原因**：
- 还没有执行过查询
- 执行记录为空

**解决方案**：
1. 执行一个查询
2. 等待查询完成
3. 刷新监控面板

### 问题3：OpenTelemetry Traces 显示 "未启用"

**可能原因**：
- OpenTelemetry 未安装
- OpenTelemetry 未启用

**解决方案**：
1. 安装 OpenTelemetry：`pip install opentelemetry-api opentelemetry-sdk`
2. 重启系统
3. 查看系统启动日志，确认看到 "✅ OpenTelemetry 监控已启用"

## 📚 相关文档

- [OpenTelemetry 快速启动指南](./opentelemetry_quick_start.md)
- [快速启动指南](./quick-start-guide.md)
- [工作流诊断指南](../analysis/workflow_graph_failure_diagnosis_using_existing_monitoring.md)

## 🎉 总结

浏览器监控功能提供了：
- ✅ **实时监控**：自动刷新，实时查看系统状态
- ✅ **易于使用**：通过浏览器界面直接查看，无需命令行
- ✅ **全面信息**：系统健康、性能指标、追踪数据一应俱全
- ✅ **可视化展示**：清晰的颜色标识和格式化显示

只需打开浏览器，切换到 **Monitoring** 标签页，即可查看所有监控信息！

