# Agent架构统一迁移实施指南

## 📋 概述

本文档提供Agent架构统一迁移的详细实施指南，包括工具使用、步骤说明和最佳实践。

## 🚀 快速开始

### 第一步：准备环境

```bash
# 创建必要的目录
mkdir -p logs backups analysis reports

# 安装依赖（如果需要）
pip install -r requirements.txt
```

### 第二步：运行分析

```bash
# 分析Agent使用情况
python scripts/analyze_agent_usage.py

# 计算迁移优先级
python scripts/calculate_migration_metrics.py
```

### 第三步：查看优先级报告

```bash
# 查看P0优先级Agent
cat migration_priority.json | jq '.priorities[] | select(.migration_priority == "P0-立即迁移")'

# 查看完整报告
cat migration_priority.json | jq '.'
```

### 第四步：开始第一个迁移

```bash
# 迁移ChiefAgent（最高优先级）
bash scripts/replace_chief_agent.sh
```

## 🛠️ 工具说明

### 分析工具

#### `scripts/analyze_agent_usage.py`

**功能**：分析代码库中Agent的使用情况

**用法**：
```bash
python scripts/analyze_agent_usage.py [选项]

选项:
  --codebase-path PATH  代码库路径（默认: src/）
  --output FILE         输出文件路径（默认: agent_usage_analysis.json）
```

**输出**：
- `agent_usage_analysis.json` - 使用情况数据
- 控制台输出Top 10使用频率最高的Agent

#### `scripts/calculate_migration_metrics.py`

**功能**：计算Agent迁移优先级分数

**用法**：
```bash
python scripts/calculate_migration_metrics.py [选项]

选项:
  --usage-data FILE     使用情况数据文件（默认: agent_usage_analysis.json）
  --output FILE         输出文件路径（默认: migration_priority.json）
```

**输出**：
- `migration_priority.json` - 优先级报告
- 控制台输出优先级摘要和Top 5优先级Agent

### 迁移工具

#### `src/adapters/base_adapter.py`

**功能**：迁移适配器基类

**使用示例**：
```python
from src.adapters.base_adapter import MigrationAdapter

class MyAgentAdapter(MigrationAdapter):
    def _initialize_target_agent(self):
        from src.agents.target_agent import TargetAgent
        return TargetAgent()
    
    def adapt_context(self, old_context):
        adapted = super().adapt_context(old_context)
        # 添加自定义转换逻辑
        return adapted
```

#### `src/strategies/gradual_replacement.py`

**功能**：逐步替换策略

**使用示例**：
```python
from src.strategies.gradual_replacement import GradualReplacementStrategy

strategy = GradualReplacementStrategy(
    old_agent=chief_agent,
    new_agent=coordinator,
    adapter=chief_adapter
)

# 执行逐步替换
result = await strategy.execute_with_gradual_replacement(context)

# 检查是否可以增加替换比例
if strategy.should_increase_rate():
    strategy.increase_replacement_rate(step=0.1)
```

#### `scripts/replace_chief_agent.sh`

**功能**：ChiefAgent迁移脚本

**用法**：
```bash
bash scripts/replace_chief_agent.sh
```

**执行步骤**：
1. 备份原文件
2. 分析使用情况
3. 应用适配器模式
4. 运行兼容性测试
5. 启动逐步替换监控

## 📊 监控和验证

### 查看迁移日志

```bash
# 查看ChiefAgent迁移日志
tail -f logs/migration_ChiefAgent.log

# 查看替换进度
tail -f logs/replacement_progress_ChiefAgent.log
```

### 检查迁移统计

```python
from src.adapters.base_adapter import MigrationAdapter

# 获取适配器统计
adapter = ChiefAgentAdapter()
stats = adapter.get_migration_stats()
print(f"成功率: {stats['success_rate']:.2%}")
```

### 检查替换统计

```python
from src.strategies.gradual_replacement import GradualReplacementStrategy

# 获取替换统计
stats = strategy.get_replacement_stats()
print(f"替换比例: {stats['replacement_rate']:.0%}")
print(f"新Agent成功率: {stats['new_agent_success_rate']:.2%}")
```

## 📈 进度跟踪

### 每周检查清单

**第1周**：
- [ ] 运行Agent使用情况分析
- [ ] 生成优先级报告
- [ ] 审查分析结果

**第2周**：
- [ ] 创建统一接口标准
- [ ] 建立适配器框架
- [ ] 创建测试框架

**第3周**：
- [ ] 创建ChiefAgent适配器
- [ ] 启动逐步替换（1%）
- [ ] 监控初始运行

**第4周**：
- [ ] 增加替换比例到10%
- [ ] 创建RAGAgent适配器
- [ ] 开始RAGAgent迁移

**后续周次**：
- [ ] 按计划逐步增加替换比例
- [ ] 迁移其他优先级Agent
- [ ] 持续监控和优化

## 🚨 故障排除

### 常见问题

#### 1. 适配器执行失败

**症状**：新Agent执行失败，回退到旧Agent

**排查步骤**：
1. 检查适配器的上下文转换逻辑
2. 验证目标Agent的初始化
3. 查看详细错误日志

**解决方案**：
```python
# 在适配器中添加详细日志
def adapt_context(self, old_context):
    logger.debug(f"原始上下文: {old_context}")
    adapted = super().adapt_context(old_context)
    logger.debug(f"转换后上下文: {adapted}")
    return adapted
```

#### 2. 替换比例无法增加

**症状**：成功率低于95%，无法增加替换比例

**排查步骤**：
1. 检查新Agent的成功率
2. 分析失败原因
3. 查看错误日志

**解决方案**：
- 修复新Agent的问题
- 改进适配器逻辑
- 降低替换比例增加步长

#### 3. 性能下降

**症状**：新Agent响应时间比旧Agent慢

**排查步骤**：
1. 运行性能基准测试
2. 对比新旧Agent性能
3. 分析性能瓶颈

**解决方案**：
- 优化新Agent实现
- 调整配置参数
- 考虑性能优化

## 📚 最佳实践

### 1. 渐进式迁移

- ✅ 从低替换比例开始（1%）
- ✅ 逐步增加（每次10%）
- ✅ 监控成功率和性能
- ✅ 达到95%成功率后再增加

### 2. 充分测试

- ✅ 每次迁移前运行完整测试
- ✅ 保持测试覆盖率≥90%
- ✅ 进行性能基准测试
- ✅ 验证API兼容性

### 3. 详细记录

- ✅ 记录所有迁移操作
- ✅ 保存备份文件
- ✅ 记录问题和解决方案
- ✅ 定期生成报告

### 4. 风险控制

- ✅ 保留回滚机制
- ✅ 设置监控告警
- ✅ 在低峰期进行迁移
- ✅ 准备应急预案

## 📖 相关文档

- **架构文档**：`SYSTEM_AGENTS_OVERVIEW.md`
- **迁移方案**：`SYSTEM_AGENTS_OVERVIEW.md` - "统一迁移方案实施步骤"
- **API文档**：`docs/api_reference.md`（待创建）
- **故障排除**：`docs/troubleshooting.md`（待创建）

## 🆘 获取帮助

如果遇到问题：

1. 查看本文档的故障排除部分
2. 检查日志文件（`logs/`目录）
3. 查看相关文档
4. 联系架构团队

---

*最后更新: 2026-01-01*

