# 检索质量评估框架

## 概述

检索质量评估框架用于验证检索性能优化后质量是否下降。该框架提供完整的评估体系，包括离线评估、在线A/B测试、基线对比等。

## 核心特性

### 1. 全面的质量指标
- **精确率 (Precision)**: 检索结果中的相关文档比例
- **召回率 (Recall)**: 相关文档被检索到的比例
- **F1分数**: 精确率和召回率的调和平均值
- **MRR (平均倒数排名)**: 第一个相关文档的排位指标
- **响应时间**: 查询响应时间
- **成功率**: 查询成功执行的比例

### 2. 多层次评估方法

#### 离线评估
- 使用预定义的测试查询集
- 基于标注的ground truth数据
- 计算各项质量指标
- 与基线版本对比

#### 在线A/B测试
- 在生产环境中进行对比测试
- 流量自动分配到不同版本
- 统计显著性检验
- 用户行为指标收集

#### 持续监控
- 实时质量指标监控
- 自动预警机制
- 质量趋势分析
- 性能回归检测

## 使用方法

### 1. 准备测试数据

创建测试查询集和对应的ground truth：

```python
# 测试查询示例
test_queries = [
    "什么是人工智能？",
    "机器学习和深度学习的区别",
    "Python编程语言的特点"
]

# Ground truth数据 (query -> relevant_doc_ids)
ground_truth = {
    "什么是人工智能？": {"doc_ai_001", "doc_ai_002"},
    "机器学习和深度学习的区别": {"doc_ml_003", "doc_dl_001"},
    "Python编程语言的特点": {"doc_python_001"}
}
```

### 2. 运行评估脚本

```bash
# 运行完整的质量评估
python src/scripts/assess_retrieval_quality.py

# 或者使用自定义配置
python -c "
import asyncio
from src.scripts.assess_retrieval_quality import main
asyncio.run(main())
"
```

### 3. 集成到优化流程

```python
from src.core.retrieval_quality_assessment import run_comprehensive_quality_assessment

# 定义检索函数
async def baseline_retrieval(query):
    # 原始检索实现
    return RetrievalResult(...)

async def optimized_retrieval(query):
    # 优化后检索实现
    return RetrievalResult(...)

# 运行评估
report = await run_comprehensive_quality_assessment(
    baseline_retrieval=baseline_retrieval,
    test_retrieval=optimized_retrieval,
    test_queries=test_queries,
    ground_truth=ground_truth,
    assessment_name="my_optimization"
)

# 检查结果
if report.passed_thresholds:
    print("✅ 优化成功，可以部署")
else:
    print("❌ 质量下降，需要重新优化")
```

## 评估流程

### 阶段1: 基线建立
1. 选择代表性的测试查询集
2. 准备高质量的ground truth标注
3. 运行基线版本，建立质量基准

### 阶段2: 离线评估
1. 使用相同的测试查询
2. 运行优化版本
3. 计算各项指标并与基线对比
4. 检查是否满足质量阈值

### 阶段3: 在线验证 (可选)
1. 在生产环境进行小流量A/B测试
2. 监控真实用户指标
3. 验证统计显著性
4. 确认没有性能回归

### 阶段4: 持续监控
1. 部署质量监控系统
2. 设置自动预警阈值
3. 定期生成质量报告
4. 及时发现质量下降

## 质量阈值设置

### 推荐的质量阈值

```python
QUALITY_THRESHOLDS = {
    "precision": 0.75,      # 精确率不低于75%
    "recall": 0.70,         # 召回率不低于70%
    "f1_score": 0.72,       # F1分数不低于72%
    "response_time": 5.0,   # 响应时间不超过5秒
    "success_rate": 0.95    # 成功率不低于95%
}
```

### 质量下降判定标准
- **精确率/召回率**: 下降超过5%需要关注
- **响应时间**: 增加超过1秒需要关注
- **成功率**: 下降超过2%需要立即处理

## 评估报告解读

### 报告结构

```json
{
  "experiment_name": "retrieval_optimization_test",
  "baseline_version": "v1.0",
  "test_version": "v1.1_optimized",
  "overall_quality_score": 85.6,
  "passed_thresholds": true,
  "metrics": {
    "precision": {
      "value": 0.78,
      "baseline_value": 0.76,
      "improvement": 0.02,
      "statistical_significance": true
    },
    "response_time": {
      "value": 2.3,
      "baseline_value": 4.1,
      "improvement": 1.8,
      "statistical_significance": true
    }
  },
  "recommendations": [
    "✅ 所有质量指标均符合要求，可以安全部署",
    "🚀 响应时间提升1.8秒，性能优化成功"
  ],
  "warnings": []
}
```

### 关键指标说明

#### 总体质量分数
- **90-100**: 优秀，质量显著提升
- **80-89**: 良好，可以安全部署
- **70-79**: 可接受，但建议进一步优化
- **<70**: 质量下降，需要重新评估

#### 改进指标解读
- **正值**: 优化版本优于基线
- **负值**: 优化版本劣于基线
- **统计显著性**: 确保改进不是偶然现象

## 最佳实践

### 1. 测试数据准备
- 选择多样化的查询类型
- 确保ground truth标注准确
- 测试数据量足够大（至少100个查询）

### 2. 评估频率
- 每次重大优化后进行完整评估
- 定期进行监控评估（每周）
- 新功能上线前进行回归测试

### 3. 质量保障
- 设置自动化的CI/CD集成
- 质量下降时自动阻断部署
- 维护历史质量趋势数据

### 4. 参数调优策略
```python
# 渐进式优化策略
optimization_steps = [
    {"top_k": 10, "similarity_threshold": 0.5},  # 基线
    {"top_k": 8, "similarity_threshold": 0.5},   # 减少top_k
    {"top_k": 8, "similarity_threshold": 0.6},   # 提高阈值
    {"top_k": 5, "similarity_threshold": 0.7},   # 进一步优化
]

for params in optimization_steps:
    # 评估当前参数组合
    report = await assess_parameters(params)
    if report.passed_thresholds:
        print(f"✅ 参数组合有效: {params}")
        break
    else:
        print(f"❌ 参数组合质量下降: {params}")
```

## 故障排除

### 常见问题

#### 1. 评估结果不稳定
**原因**: 测试数据不足或ground truth质量差
**解决**: 增加测试查询数量，提高标注质量

#### 2. 在线A/B测试流量不均
**原因**: 流量分配算法问题
**解决**: 检查随机种子设置，使用更均衡的分配策略

#### 3. 质量监控误报
**原因**: 阈值设置过严或数据波动
**解决**: 调整阈值，增加观察周期

#### 4. 性能评估与质量评估冲突
**原因**: 性能优化影响了质量指标
**解决**: 寻找性能和质量的最佳平衡点

## 扩展功能

### 自定义指标
```python
from src.core.retrieval_quality_assessment import QualityMetric

# 添加自定义指标
custom_metric = QualityMetric(
    name="user_satisfaction",
    calculation_function=my_satisfaction_calculation,
    threshold=0.8
)
```

### 集成监控系统
```python
# 与现有监控系统集成
from src.core.monitoring_system import get_monitoring_system

monitoring = get_monitoring_system()
monitoring.register_quality_metrics(quality_assessor.metrics)
```

### 自动化优化
```python
# 基于评估结果自动调整参数
optimizer = RetrievalParameterOptimizer(quality_assessor)
optimal_params = await optimizer.find_optimal_parameters()
```

## 结论

检索质量评估框架提供了从离线评估到在线验证的完整解决方案，确保检索性能优化不会以牺牲质量为代价。通过科学的评估方法和严格的质量控制，可以安全地进行检索系统的优化和改进。
