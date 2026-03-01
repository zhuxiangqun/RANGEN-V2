# LangGraph可视化集成方案

## 📋 概述

本文档详细说明如何将"AI系统诊断与进化顾问"与现有的LangGraph工作流可视化系统深度集成，充分利用LangGraph的实时可视化能力。

## 🎯 集成目标

充分利用LangGraph框架的以下可视化特性：
1. **实时节点状态显示**：idle、running、completed、error
2. **工作流图可视化**：Mermaid图表，支持分层显示
3. **执行路径追踪**：记录实际执行的节点序列
4. **流式状态更新**：WebSocket实时推送节点状态

## 🔧 核心集成点

### 1. 诊断结果 → 工作流图标注

**功能**：将诊断结果直接标注在工作流图中

**实现方式**：
```python
# 在 SystemDiagnosticModule 中
async def diagnose_and_annotate_workflow(
    self,
    node_execution_data: Dict[str, Dict[str, Any]],
    workflow_graph: Any  # LangGraph的graph对象
) -> Dict[str, Any]:
    """诊断系统并在工作流图中标注"""
    # 1. 诊断节点
    diagnostics = await self.diagnose_from_execution(node_execution_data)
    
    # 2. 生成节点标注信息
    node_annotations = {}
    for node_name, diagnostic in diagnostics['node_diagnostics'].items():
        node_annotations[node_name] = {
            'status': diagnostic['status'],  # 'error', 'warning', 'bottleneck', 'normal'
            'execution_time': diagnostic['execution_time'],
            'diagnostic_info': diagnostic,
            'color': self._get_status_color(diagnostic['status'])
        }
    
    return {
        'diagnostics': diagnostics,
        'node_annotations': node_annotations  # 用于前端标注
    }
```

**前端集成**：
```javascript
// 在工作流图中标注诊断结果
function annotateWorkflowWithDiagnostics(nodeAnnotations) {
    Object.entries(nodeAnnotations).forEach(([nodeName, annotation]) => {
        // 更新节点颜色
        updateWorkflowGraphNode(nodeName, annotation.status);
        
        // 添加诊断信息提示
        addDiagnosticTooltip(nodeName, annotation.diagnostic_info);
    });
}
```

### 2. 建议生成 → 节点关联

**功能**：将建议与工作流节点关联，便于可视化

**实现方式**：
```python
# 在 RecommendationEngine 中
async def generate_recommendations_with_node_mapping(
    self,
    opportunities: List[Dict[str, Any]],
    workflow_graph: Any
) -> List[Dict[str, Any]]:
    """生成建议并映射到工作流节点"""
    recommendations = []
    
    for opportunity in opportunities:
        recommendation = await self._create_recommendation(opportunity)
        
        # 识别建议影响的节点
        affected_nodes = self._identify_affected_nodes(recommendation, workflow_graph)
        recommendation['affected_nodes'] = affected_nodes
        
        # 生成节点级别的执行计划
        node_execution_plan = self._generate_node_execution_plan(
            recommendation, affected_nodes
        )
        recommendation['node_execution_plan'] = node_execution_plan
        
        recommendations.append(recommendation)
    
    return recommendations
```

### 3. 建议预览 → 工作流图预览

**功能**：在工作流图中预览建议的执行效果

**实现方式**：
```python
# 在 BrowserServer 中
async def preview_recommendation_in_workflow(
    self,
    recommendation_id: str,
    workflow_graph: Any
) -> Dict[str, Any]:
    """在工作流图中预览建议效果"""
    recommendation = await self._get_recommendation(recommendation_id)
    
    # 生成预览工作流图
    preview_graph = workflow_graph.copy()
    
    # 应用建议的修改（仅预览，不实际修改）
    if recommendation['type'] == 'workflow_optimization':
        # 修改工作流结构（预览）
        preview_graph = self._apply_workflow_changes_preview(
            preview_graph, recommendation
        )
    elif recommendation['type'] == 'parameter_optimization':
        # 修改节点参数（预览）
        preview_graph = self._apply_parameter_changes_preview(
            preview_graph, recommendation
        )
    
    # 生成预览Mermaid图
    preview_mermaid = preview_graph.draw_mermaid()
    
    return {
        'recommendation': recommendation,
        'preview_mermaid': preview_mermaid,
        'affected_nodes': recommendation['affected_nodes'],
        'expected_changes': recommendation.get('expected_changes', {})
    }
```

### 4. 执行跟踪 → 实时状态更新

**功能**：实时显示建议执行对工作流的影响

**实现方式**：
```python
# 在 BrowserServer 中
async def track_recommendation_execution(
    self,
    recommendation_id: str,
    execution_status: str
):
    """跟踪建议执行状态"""
    recommendation = await self._get_recommendation(recommendation_id)
    
    # 更新建议状态
    recommendation['status'] = execution_status
    
    # 如果正在执行，实时更新影响的节点状态
    if execution_status == 'executing':
        for node_name in recommendation['affected_nodes']:
            await self.tracker.broadcast_update(execution_id, {
                "type": "node_update",
                "data": {
                    "name": node_name,
                    "status": "recommendation-executing",
                    "recommendation_id": recommendation_id
                }
            })
```

## 🖥️ 前端可视化增强

### 1. 诊断模式

**功能**：在工作流图中显示诊断结果

**实现**：
```javascript
// 诊断模式切换
function switchToDiagnosticMode() {
    // 获取诊断结果
    fetch('/api/diagnostic-results?execution_id=' + currentExecutionId)
        .then(response => response.json())
        .then(data => {
            // 在工作流图中标注问题节点
            annotateWorkflowWithDiagnostics(data.node_annotations);
            
            // 显示诊断信息面板
            showDiagnosticPanel(data.diagnostic_result);
        });
}

// 标注节点
function annotateWorkflowWithDiagnostics(nodeAnnotations) {
    Object.entries(nodeAnnotations).forEach(([nodeName, annotation]) => {
        const nodeElement = findNodeInWorkflow(nodeName);
        if (nodeElement) {
            // 添加诊断状态类
            nodeElement.classList.add(`diagnostic-${annotation.status}`);
            
            // 添加诊断信息提示
            addTooltip(nodeElement, {
                title: `诊断: ${annotation.status}`,
                content: `执行时间: ${annotation.execution_time}s`,
                diagnostic: annotation.diagnostic_info
            });
        }
    });
}
```

### 2. 建议预览模式

**功能**：在工作流图中预览建议的执行效果

**实现**：
```javascript
// 建议预览
function previewRecommendation(recommendationId) {
    // 获取建议预览
    fetch(`/api/recommendations/${recommendationId}/preview`)
        .then(response => response.json())
        .then(data => {
            // 高亮影响的节点
            highlightNodes(data.affected_nodes);
            
            // 显示预览工作流图
            showPreviewWorkflow(data.preview_mermaid);
            
            // 显示预期变化
            showExpectedChanges(data.expected_changes);
        });
}

// 高亮节点
function highlightNodes(nodeNames) {
    nodeNames.forEach(nodeName => {
        const nodeElement = findNodeInWorkflow(nodeName);
        if (nodeElement) {
            nodeElement.classList.add('recommendation-highlight');
        }
    });
}
```

### 3. 执行跟踪模式

**功能**：实时显示建议执行对工作流的影响

**实现**：
```javascript
// 执行跟踪
function trackRecommendationExecution(recommendationId) {
    // 建立WebSocket连接
    const ws = new WebSocket(`ws://localhost:8000/ws/execution/${executionId}`);
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'recommendation_execution_update') {
            // 更新节点状态
            message.data.affected_nodes.forEach(nodeName => {
                updateWorkflowGraphNode(nodeName, message.data.status);
            });
        }
    };
}
```

## 📊 数据流设计

### 诊断数据流

```
节点执行 → 收集执行数据 → 诊断分析 → 生成节点标注 → 前端可视化
```

### 建议数据流

```
诊断结果 → 生成建议 → 映射到节点 → 生成预览 → 前端可视化 → 人类审批
```

### 执行跟踪数据流

```
人类执行 → 更新执行状态 → 实时推送 → 前端更新工作流图 → 验证效果
```

## 🔄 API端点设计

### 1. 诊断相关API

```python
# 获取诊断结果（包含节点标注信息）
GET /api/diagnostic-results?execution_id={execution_id}
Response: {
    "diagnostic_result": {...},
    "node_annotations": {
        "node_name": {
            "status": "error|warning|bottleneck|normal",
            "execution_time": 1.23,
            "diagnostic_info": {...}
        }
    }
}

# 在工作流图中高亮诊断节点
GET /api/diagnostic-highlight?execution_id={execution_id}
Response: {
    "error_nodes": ["node1", "node2"],
    "bottleneck_nodes": ["node3"],
    "warning_nodes": ["node4"]
}
```

### 2. 建议相关API

```python
# 获取建议（包含节点映射）
GET /api/recommendations?execution_id={execution_id}
Response: {
    "recommendations": [
        {
            "recommendation_id": "rec_123",
            "affected_nodes": ["node1", "node2"],
            "node_execution_plan": {...}
        }
    ]
}

# 预览建议效果
GET /api/recommendations/{recommendation_id}/preview
Response: {
    "recommendation": {...},
    "preview_mermaid": "...",
    "affected_nodes": ["node1", "node2"],
    "expected_changes": {...}
}
```

### 3. 执行跟踪API

```python
# 跟踪建议执行
POST /api/recommendations/{recommendation_id}/execute
Request: {
    "execution_plan": {...}
}
Response: {
    "execution_id": "exec_123",
    "status": "executing"
}

# 获取执行状态
GET /api/recommendations/{recommendation_id}/execution-status
Response: {
    "status": "executing|completed|failed",
    "affected_nodes_status": {
        "node1": "updated",
        "node2": "pending"
    }
}
```

## 🎨 可视化样式设计

### 节点状态颜色

```css
/* 诊断状态 */
.diagnostic-error { background-color: #f44336; }      /* 红色：错误 */
.diagnostic-warning { background-color: #ff9800; }    /* 橙色：警告 */
.diagnostic-bottleneck { background-color: #ffc107; } /* 黄色：瓶颈 */
.diagnostic-normal { background-color: #4caf50; }    /* 绿色：正常 */

/* 建议高亮 */
.recommendation-highlight {
    border: 2px solid #2196f3;
    box-shadow: 0 0 10px rgba(33, 150, 243, 0.5);
}

/* 建议执行中 */
.recommendation-executing {
    animation: pulse 1s infinite;
}
```

## 📝 实施建议

### 阶段1：基础集成（1周）
- 实现诊断结果在工作流图中的标注
- 实现建议与节点的关联
- 实现基本的可视化展示

### 阶段2：预览功能（1周）
- 实现建议预览功能
- 实现工作流图预览
- 实现预期效果展示

### 阶段3：执行跟踪（1周）
- 实现执行状态实时更新
- 实现执行前后对比
- 实现效果验证可视化

### 阶段4：优化增强（1周）
- 优化可视化性能
- 增强交互体验
- 完善文档

## 🔗 相关文档

- [AI系统诊断与进化顾问设计方案](./ai_self_evolution_system_design.md)
- [LangGraph工作流可视化文档](../implementation/query_processing_workflow.md)
- [工作流图构建器文档](../../src/visualization/workflow_graph_builder.py)

