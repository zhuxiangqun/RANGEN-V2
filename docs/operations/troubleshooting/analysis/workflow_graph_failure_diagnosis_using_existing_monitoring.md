# 利用现有监控能力诊断工作流图获取失败

## 概述

系统已经具备丰富的监控能力，我们应该**利用现有监控**来诊断工作流图获取失败的问题，而不是创建新的诊断工具。

## 现有监控能力

### 1. **日志系统** (`logging`)
- ✅ 详细的错误日志记录
- ✅ 堆栈跟踪信息
- ✅ 多级别日志（DEBUG, INFO, WARNING, ERROR）

### 2. **OpenTelemetry 监控** (`src/core/langgraph_opentelemetry_integration.py`)
- ✅ 分布式追踪
- ✅ 性能指标收集
- ✅ 节点执行追踪
- ✅ 错误记录和异常追踪

### 3. **编排追踪器** (`src/visualization/orchestration_tracker.py`)
- ✅ Agent 执行追踪
- ✅ 工具调用追踪
- ✅ 提示词工程追踪
- ✅ 上下文工程追踪

### 4. **工作流追踪器** (`src/visualization/browser_server.py::WorkflowTracker`)
- ✅ 执行状态追踪
- ✅ 节点执行记录
- ✅ WebSocket 实时更新

### 5. **性能监控** (`src/core/langgraph_performance_monitor.py`)
- ✅ 节点执行时间
- ✅ Token 使用统计
- ✅ API 调用统计

### 6. **健康检查端点** (`/api/workflow/health`)
- ✅ 工作流状态检查
- ✅ 系统初始化状态
- ✅ 环境变量检查
- ✅ LangGraph 可用性检查

## 利用现有监控诊断问题

### 方法1：使用健康检查端点（推荐）

访问 `/api/workflow/health` 端点获取详细的工作流健康状态：

```bash
curl http://localhost:8080/api/workflow/health
```

返回的 JSON 包含：
- `status`: 整体健康状态（healthy/degraded/unhealthy）
- `checks`: 各项检查的详细结果
  - `system_exists`: 系统是否存在
  - `system_initialized`: 系统是否已初始化
  - `workflow_instance`: 工作流实例状态
  - `workflow_property`: workflow 属性状态
  - `workflow_graph`: 工作流图获取能力
  - `environment_variables`: 环境变量配置
  - `langgraph_available`: LangGraph 可用性
- `error_checks`: 失败的检查列表
- `warning_checks`: 警告的检查列表

### 方法2：查看系统初始化日志

系统初始化时会记录详细的工作流初始化过程：

```bash
# 查看日志文件
tail -f logs/research_system.log | grep -i "工作流\|workflow"

# 或查看最近的错误
grep -i "工作流.*失败\|workflow.*fail" logs/research_system.log
```

关键日志信息：
- `✅ [初始化] 统一工作流（MVP）初始化完成` - 初始化成功
- `❌ [初始化] 统一工作流初始化失败` - 初始化失败
- `⚠️ 系统有 _unified_workflow 属性，但值为 None` - 工作流为 None

### 方法3：使用 OpenTelemetry 追踪（如果已启用）

**OpenTelemetry 默认自动启动**（如果已安装），无需手动启动。

#### 启动 OpenTelemetry

**步骤1：安装 OpenTelemetry**
```bash
# 方法1：使用安装脚本（推荐）
bash scripts/install_opentelemetry.sh

# 方法2：手动安装
pip install opentelemetry-api opentelemetry-sdk
```

**步骤2：启动系统（OpenTelemetry 自动启用）**
```bash
python examples/start_visualization_server.py
```

系统启动时，如果 OpenTelemetry 已安装，会自动初始化并启用。

#### 查看追踪数据

**方法A：控制台导出器（默认）**

```bash
# 查看实时日志
tail -f logs/research_system.log

# 或查看追踪相关的日志
grep -i "span\|trace\|opentelemetry" logs/research_system.log | tail -20
```

**方法B：Jaeger UI（可视化界面，推荐）**

1. **安装 Jaeger 导出器**：
   ```bash
   pip install opentelemetry-exporter-jaeger-thrift
   ```

2. **启动 Jaeger**：
   ```bash
   docker run -d --name jaeger -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest
   ```

3. **配置环境变量**：
   ```bash
   export ENABLE_OPENTELEMETRY=true
   export OPENTELEMETRY_EXPORTER=jaeger
   export OPENTELEMETRY_ENDPOINT=http://localhost:14268/api/traces
   ```

4. **启动系统**：
   ```bash
   python examples/start_visualization_server.py
   ```

5. **访问 Jaeger UI**：
   ```
   http://localhost:16686
   ```
   
   在 Jaeger UI 中：
   - 选择服务：`langgraph-workflow`
   - 点击 "Find Traces"
   - 查看追踪数据

**方法C：Zipkin UI**

1. **安装 Zipkin 导出器**：
   ```bash
   pip install opentelemetry-exporter-zipkin-json
   ```

2. **启动 Zipkin**：
   ```bash
   docker run -d --name zipkin -p 9411:9411 openzipkin/zipkin
   ```

3. **配置环境变量**：
   ```bash
   export ENABLE_OPENTELEMETRY=true
   export OPENTELEMETRY_EXPORTER=zipkin
   export OPENTELEMETRY_ENDPOINT=http://localhost:9411/api/v2/spans
   ```

4. **启动系统并访问 Zipkin UI**：
   ```
   http://localhost:9411
   ```

追踪信息包括：
- `workflow.build` span - 工作流构建过程
- 节点执行追踪（每个节点都有独立的 span）
- 错误和异常记录
- 性能指标（执行时间、Token 使用等）

**详细说明**：请查看 [OpenTelemetry 快速启动指南](../../getting-started/first-steps/opentelemetry_quick_start.md)

### 方法4：使用编排追踪器

编排追踪器会记录工作流初始化事件：

```python
# 在代码中访问编排追踪器
if system._orchestration_tracker:
    events = system._orchestration_tracker.events
    for event in events:
        if event.component_name == "UnifiedResearchWorkflow":
            print(f"事件: {event.event_type}, 错误: {event.data.get('error')}")
```

### 方法5：检查可视化服务器日志

可视化服务器会记录工作流图获取的详细过程：

```bash
# 查看工作流图获取日志
tail -f logs/research_system.log | grep -i "工作流图\|workflow.*graph"
```

关键日志信息：
- `🔍 [工作流图] 开始获取工作流图...` - 开始获取
- `✅ [工作流图] 从系统获取统一工作流` - 获取成功
- `❌ [工作流图] 统一工作流实例存在，但 workflow 图为 None` - 工作流构建失败
- `❌ [工作流图] 系统有 _unified_workflow 属性，但值为 None` - 工作流初始化失败

## 常见问题诊断流程

### 问题1：工作流图一直显示"正在加载"

**诊断步骤**：
1. 访问 `/api/workflow/health` 端点
2. 检查 `workflow_instance` 和 `workflow_property` 的状态
3. 查看可视化服务器日志中的错误信息

**可能原因**：
- 系统未初始化 → 检查 `system_initialized` 状态
- 工作流初始化失败 → 检查系统初始化日志
- 工作流被禁用 → 检查 `environment_variables.ENABLE_UNIFIED_WORKFLOW`

### 问题2：工作流实例为 None

**诊断步骤**：
1. 查看系统初始化日志，查找 "统一工作流初始化失败" 的错误
2. 检查 `langgraph_available` 状态
3. 检查环境变量 `ENABLE_UNIFIED_WORKFLOW`

**可能原因**：
- LangGraph 未安装 → 安装 LangGraph
- 工作流被禁用 → 设置 `ENABLE_UNIFIED_WORKFLOW=true`
- 初始化异常 → 查看详细错误堆栈

### 问题3：workflow 属性为 None

**诊断步骤**：
1. 查看系统初始化日志，查找 "工作流构建失败" 的错误
2. 检查 OpenTelemetry 追踪中的 `workflow.build` span
3. 查看编排追踪器中的工作流初始化事件

**可能原因**：
- `_build_workflow()` 抛出异常 → 查看详细错误堆栈
- 工作流编译失败 → 检查节点和边的定义
- 依赖模块导入失败 → 检查模块导入错误

## 最佳实践

1. **优先使用健康检查端点**：
   - 快速获取工作流状态
   - 包含详细的诊断信息和建议

2. **查看日志文件**：
   - 系统初始化日志包含详细的错误信息
   - 可视化服务器日志包含工作流图获取过程

3. **利用 OpenTelemetry**：
   - 如果已启用，查看追踪数据获取更详细的执行信息

4. **利用编排追踪器**：
   - 查看工作流初始化事件
   - 追踪初始化过程中的错误

## 相关端点

- `/api/workflow/health` - 工作流健康检查（新增）
- `/api/workflow/graph` - 获取工作流图
- `/api/status` - 系统状态
- `/api/metrics` - 性能指标

## 相关文件

- `src/visualization/browser_server.py` - 可视化服务器和健康检查端点
- `src/core/langgraph_unified_workflow.py` - 工作流定义和初始化
- `src/unified_research_system.py` - 系统初始化
- `src/core/langgraph_opentelemetry_integration.py` - OpenTelemetry 集成
- `src/visualization/orchestration_tracker.py` - 编排追踪器

