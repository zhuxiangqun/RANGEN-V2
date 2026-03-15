# RANGEN V2 功能集成计划

## 当前状态

### ✅ 已集成 (生产使用)
- ExecutionCoordinator (轻量模式)
- ContextManager (含Smart Forgetting)
- ReasoningAgent
- ToolRegistry
- QualityEvaluator
- Hook系统 (刚改进)
- 事件流系统 (刚改进)
- 自学习系统 (刚改进)

### ❌ 未集成但需要集成

#### P0 - 必须集成
| 功能 | 文件 | 说明 |
|------|------|------|
| ForgettingMechanism | core/forgetting_mechanism.py | 4层记忆管理 |
| ML优化组件 | core/reasoning/ml_framework/* | 19个组件 |
| 审计日志 | services/audit_log_service.py | 合规必需 |
| A/B测试 | services/ab_testing_service.py | 优化决策 |

#### P1 - 应该集成
| 功能 | 文件 | 说明 |
|------|------|------|
| 知识图谱 | services/knowledge_graph_service.py | 关系推理 |
| 安全沙箱 | services/sandbox_service.py | 安全保障 |
| 缓存服务 | services/explicit_cache_service.py | 性能优化 |

#### P2 - 可以集成
| 功能 | 文件 | 说明 |
|------|------|------|
| 监控面板 | services/monitoring_dashboard_service.py | 可观测性 |
| 容错服务 | services/fault_tolerance_service.py | 稳定性 |
| 自动扩缩容 | services/autoscaling_service.py | 资源管理 |

---

## 集成策略

### 1. ExecutionCoordinator 扩展
将以下功能集成到主协调器:
- ForgettingMechanism
- 审计日志
- ML优化组件(可选)

### 2. ContextManager 增强
- 集成ForgettingMechanism
- 改进压缩策略

### 3. 新增配置选项
```python
ExecutionCoordinator(
    enable_hooks=True,
    enable_event_stream=True,
    enable_self_learning=True,
    enable_forgetting=True,      # 新增: 遗忘机制
    enable_ml_optimization=True, # 新增: ML优化
    enable_audit=True,          # 新增: 审计日志
)
```

---

## 实施顺序

1. ForgettingMechanism → ContextManager
2. ML优化组件 → ExecutionCoordinator  
3. 审计日志 → ExecutionCoordinator
4. A/B测试服务 → 可选
