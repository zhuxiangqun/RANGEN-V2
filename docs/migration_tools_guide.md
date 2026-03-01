# Agent迁移工具指南

## 📋 概述

本文档详细介绍Agent迁移过程中使用的所有工具和脚本，包括使用方法、参数说明和最佳实践。

**适用范围**: RANGEN系统Agent架构统一迁移项目

---

## 🛠️ 核心迁移工具

### 1. 统一迁移管理器 (`scripts/manage_agent_migrations.py`)

#### 功能描述
统一管理所有Agent迁移任务，提供完整的迁移生命周期管理。

#### 使用方法
```bash
# 查看迁移状态
python scripts/manage_agent_migrations.py --status

# 执行特定Agent迁移
python scripts/manage_agent_migrations.py --migrate ReActAgent --target ReasoningExpert

# 批量迁移
python scripts/manage_agent_migrations.py --batch --config migration_batch_config.json

# 回滚迁移
python scripts/manage_agent_migrations.py --rollback ReActAgent
```

#### 参数说明
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--status` | flag | 否 | 显示所有Agent迁移状态 |
| `--migrate AGENT` | string | 否 | 指定要迁移的Agent名称 |
| `--target TARGET` | string | 否 | 指定目标Agent名称 |
| `--batch` | flag | 否 | 启用批量迁移模式 |
| `--config FILE` | string | 否 | 批量迁移配置文件路径 |
| `--rollback AGENT` | string | 否 | 回滚指定Agent的迁移 |

#### 输出示例
```
Agent迁移状态总览
==================

ReActAgent → ReasoningExpert
├── 状态: 进行中 (45%)
├── 开始时间: 2026-01-01 10:00:00
├── 预计完成: 2026-01-01 12:00:00
└── 健康状态: 良好

ChiefAgent → AgentCoordinator
├── 状态: 完成 (100%)
├── 开始时间: 2026-01-01 09:00:00
├── 完成时间: 2026-01-01 11:30:00
└── 性能提升: +35%
```

---

### 2. Agent使用情况分析器 (`scripts/analyze_agent_usage.py`)

#### 功能描述
分析项目中Agent的使用情况，为迁移优先级排序提供数据支持。

#### 使用方法
```bash
# 基础分析
python scripts/analyze_agent_usage.py --codebase-path src/

# 生成详细报告
python scripts/analyze_agent_usage.py --codebase-path src/ --output agent_analysis.json --detailed

# 包含测试文件
python scripts/analyze_agent_usage.py --codebase-path . --include-tests --output full_analysis.json
```

#### 参数说明
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--codebase-path PATH` | string | 是 | 代码库根目录路径 |
| `--output FILE` | string | 否 | 输出文件路径 (默认: agent_usage_analysis.json) |
| `--detailed` | flag | 否 | 生成详细分析报告 |
| `--include-tests` | flag | 否 | 包含测试文件分析 |
| `--exclude-pattern PATTERN` | string | 否 | 排除文件模式 (支持glob) |

#### 输出文件结构
```json
{
  "summary": {
    "total_files": 433,
    "total_agents": 21,
    "total_imports": 84
  },
  "agents": [
    {
      "name": "BaseAgent",
      "import_count": 16,
      "usage_locations": ["src/agents/base_agent.py", "src/core/agent_manager.py"],
      "migration_priority": "HIGH"
    }
  ],
  "migration_recommendations": [
    {
      "agent": "ReActAgent",
      "target": "ReasoningExpert",
      "priority": "HIGH",
      "complexity": "MEDIUM",
      "estimated_effort": "2 days"
    }
  ]
}
```

---

### 3. 迁移优先级计算器 (`scripts/calculate_migration_metrics.py`)

#### 功能描述
基于Agent使用情况计算迁移优先级和复杂度评估。

#### 使用方法
```bash
# 使用分析结果计算优先级
python scripts/calculate_migration_metrics.py --usage-data agent_usage_analysis.json

# 自定义权重配置
python scripts/calculate_migration_metrics.py --usage-data agent_usage_analysis.json --weights custom_weights.json

# 生成详细报告
python scripts/calculate_migration_metrics.py --usage-data agent_usage_analysis.json --output migration_priority.json --report migration_report.md
```

#### 参数说明
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `--usage-data FILE` | string | 是 | Agent使用情况分析结果文件 |
| `--weights FILE` | string | 否 | 自定义权重配置文件 |
| `--output FILE` | string | 否 | 输出优先级计算结果 |
| `--report FILE` | string | 否 | 生成详细报告文件 |

#### 优先级计算公式
```
优先级分数 = (使用频率 × 0.4) + (复杂度 × 0.3) + (依赖度 × 0.2) + (业务重要性 × 0.1)

其中：
- 使用频率: 基于导入次数和调用频率
- 复杂度: 基于代码行数和依赖关系
- 依赖度: 基于被其他组件依赖的数量
- 业务重要性: 基于业务逻辑复杂度
```

---

### 4. 逐步替换管理器 (`src/strategies/gradual_replacement.py`)

#### 功能描述
实现Agent的逐步替换策略，支持平滑迁移和回滚。

#### 使用方法
```python
from src.strategies.gradual_replacement import GradualReplacementManager

# 创建替换管理器
manager = GradualReplacementManager(
    source_agent="ReActAgent",
    target_agent="ReasoningExpert",
    replacement_rate=0.1  # 10%替换率
)

# 启动逐步替换
manager.start_replacement()

# 调整替换率
manager.adjust_replacement_rate(0.25)  # 25%

# 监控替换状态
status = manager.get_replacement_status()
print(f"当前替换率: {status['current_rate']}%")
print(f"目标替换率: {status['target_rate']}%")

# 回滚替换
if status['has_issues']:
    manager.rollback_to_rate(0.05)  # 回滚到5%
```

#### 配置参数
```json
{
  "source_agent": "ReActAgent",
  "target_agent": "ReasoningExpert",
  "initial_rate": 0.01,
  "target_rate": 1.0,
  "increment_step": 0.05,
  "monitoring_interval": 300,
  "rollback_threshold": 0.8,
  "success_criteria": {
    "performance_degradation_max": 0.1,
    "error_rate_max": 0.05,
    "response_time_max": 2.0
  }
}
```

---

## 🔧 验证和测试工具

### 5. 性能验证脚本 (`scripts/verify_performance_metrics.py`)

#### 功能描述
验证Agent迁移后的性能指标是否达到预期。

#### 使用方法
```bash
# 运行性能验证
python scripts/verify_performance_metrics.py

# 指定Agent进行验证
python scripts/verify_performance_metrics.py --agents ReActAgent ReasoningExpert

# 生成详细报告
python scripts/verify_performance_metrics.py --report performance_report.md

# 比较新旧版本性能
python scripts/verify_performance_metrics.py --compare --baseline baseline_metrics.json
```

#### 性能指标
| 指标 | 目标值 | 验证方法 |
|------|--------|----------|
| 响应时间 | <8-15秒 | 多轮测试取平均值 |
| 准确率 | >85-95% | 基于测试用例的准确性评估 |
| 系统稳定性 | >99.5% | 连续运行稳定性测试 |
| 内存使用 | <500MB | 内存泄漏和峰值使用检测 |
| CPU使用率 | <80% | 高负载下的CPU使用监控 |

---

### 6. 系统集成测试器 (`test_system_integration_multi_agent.py`)

#### 功能描述
测试多个Agent间的协作和集成是否正常。

#### 使用方法
```bash
# 运行集成测试
python test_system_integration_multi_agent.py

# 指定测试场景
python test_system_integration_multi_agent.py --scenario complex_query

# 详细输出模式
python test_system_integration_multi_agent.py --verbose --log-level DEBUG

# 性能测试模式
python test_system_integration_multi_agent.py --performance --duration 3600
```

#### 测试场景
- **基础协作**: Agent间的简单调用和数据传递
- **复杂查询**: 多Agent协作处理复杂任务
- **错误恢复**: Agent失败时的降级和恢复机制
- **负载测试**: 高并发下的系统稳定性
- **边界情况**: 异常输入和极端条件的处理

---

## 📊 监控和运维工具

### 7. 统一架构监控系统 (`scripts/start_unified_architecture_monitoring.py`)

#### 功能描述
实时监控8个核心Agent的运行状态和性能指标。

#### 使用方法
```bash
# 启动监控（持续运行）
python scripts/start_unified_architecture_monitoring.py

# 单次检查模式
python scripts/start_unified_architecture_monitoring.py --once

# 自定义监控间隔
python scripts/start_unified_architecture_monitoring.py --interval 60

# 导出监控报告
python scripts/start_unified_architecture_monitoring.py --export monitoring_report.json --duration 1800
```

#### 监控指标
- **Agent健康状态**: 响应时间、错误计数、状态检查
- **系统资源**: CPU使用率、内存使用率、磁盘空间
- **性能指标**: 请求数、响应时间、错误率、吞吐量
- **告警系统**: 自动检测异常并生成告警

#### 监控输出示例
```
🎯 统一架构监控系统
启动时间: 2026-01-04 11:50:58

📊 当前状态摘要
Agent总数: 8
健康Agent: 8
健康率: 100.0%
活跃告警: 0个

🤖 Agent健康详情
🟢 AgentCoordinator: healthy | 响应时间: N/A
🟢 ReasoningExpert: healthy | 响应时间: N/A
🟢 RAGExpert: healthy | 响应时间: N/A
...
```

---

### 8. 迁移状态同步器 (`scripts/sync_migration_status.py`)

#### 功能描述
同步迁移状态到相关文档和配置中。

#### 使用方法
```bash
# 同步所有状态
python scripts/sync_migration_status.py

# 只同步特定Agent
python scripts/sync_migration_status.py --agent ReActAgent

# 验证同步结果
python scripts/sync_migration_status.py --verify

# 强制重新同步
python scripts/sync_migration_status.py --force
```

---

## 🔄 适配器和迁移脚本

### 9. 适配器生成器 (`scripts/generate_agent_adapter.py`)

#### 功能描述
自动生成Agent适配器代码，减少手动编写的工作量。

#### 使用方法
```bash
# 生成基础适配器
python scripts/generate_agent_adapter.py --source ReActAgent --target ReasoningExpert

# 生成完整适配器（包含测试）
python scripts/generate_agent_adapter.py --source ReActAgent --target ReasoningExpert --with-tests

# 自定义模板
python scripts/generate_agent_adapter.py --source ReActAgent --target ReasoningExpert --template custom_template.py
```

#### 生成的文件结构
```
src/adapters/
├── react_agent_adapter.py          # 适配器实现
├── test_react_agent_adapter.py     # 单元测试
└── react_agent_migration_config.json  # 配置信息
```

---

## 📋 最佳实践

### 工具使用原则
1. **先分析后迁移**: 使用分析工具了解现状，再制定迁移计划
2. **小步快跑**: 分阶段迁移，每个阶段都有验证和回滚机制
3. **监控先行**: 迁移过程中保持监控，及时发现问题
4. **自动化优先**: 尽量使用自动化工具，减少手动操作

### 故障排除
1. **迁移失败**: 检查适配器配置和目标Agent初始化
2. **性能下降**: 使用性能验证工具定位瓶颈
3. **集成问题**: 运行系统集成测试检查Agent协作
4. **监控异常**: 检查监控配置和系统资源

### 维护建议
1. **定期更新**: 保持工具和脚本的最新版本
2. **文档同步**: 工具更新时同步更新文档
3. **培训分享**: 定期培训团队成员使用方法
4. **反馈收集**: 建立反馈机制持续改进工具

---

## 📚 相关文档

- [迁移实施指南](migration_implementation_guide.md)
- [迁移最佳实践](migration_best_practices.md)
- [常见问题解答](migration_faq.md)
- [系统Agent概览](../SYSTEM_AGENTS_OVERVIEW.md)

---

*本文档最后更新时间: 2026年1月4日*
*维护者: 系统架构团队*
