# FRAMES基准增强评测报告

> 本报告包含FRAMES基准准确率、推理效率创新性、详细性能分析和优化建议

## 📊 评测概览

- **评测类型**: frames_benchmark_async_enhanced
- **数据集**: FRAMES Benchmark
- **开始时间**: 2025-08-25T12:01:25.683219
- **结束时间**: 2025-08-25T12:01:54.276221
- **总查询数**: 5
- **成功数**: 5
- **失败数**: 0
- **总体成功率**: 100.00%

## 🎯 FRAMES基准准确率分析（主要指标）

- **平均FRAMES准确率**: 0.800
- **高准确率答案**: 4 个 (≥80%)
- **中等准确率答案**: 0 个 (50%-80%)
- **低准确率答案**: 1 个 (<50%)

## 🧠 推理效率和方法创新性分析

- **平均创新性分数**: 0.000

### 创新推理能力统计
- **多跳推理**: 0 次
- **约束满足推理**: 0 次
- **时间推理**: 0 次
- **数值计算推理**: 0 次
- **知识整合推理**: 0 次

### 推理效率指标
- **多跳推理效率**: 0.0%
- **约束满足效率**: 0.0%
- **时间推理效率**: 0.0%
- **数值计算效率**: 0.0%
- **知识整合效率**: 0.0%

## ⚙️ 模块性能分析（定位性能瓶颈）

### 各模块执行时长统计
| 模块 | 平均时长(s) | 总时长(s) | 最大时长(s) | 执行次数 | 标准差 |
|------|-------------|-----------|-------------|----------|--------|
| knowledge_retrieval | 0.000 | 0.000 | 0.000 | 0 | 0.000 |
| reasoning | 0.000 | 0.000 | 0.000 | 0 | 0.000 |
| answer_generation | 0.000 | 0.000 | 0.000 | 0 | 0.000 |
| citation | 0.000 | 0.000 | 0.000 | 0 | 0.000 |
| total_pipeline | 6.798 | 33.991 | 6.807 | 5 | 0.007 |

### 各模块执行路径分析（主流程 vs 异常处理 vs 简单处理）
| 模块 | 主流程执行 | 异常处理 | 简单处理 | 主流程占比 |
|------|------------|----------|----------|------------|
| knowledge_retrieval | 5 | 0 | 0 | 100.0% |
| reasoning | 5 | 0 | 0 | 100.0% |
| answer_generation | 5 | 0 | 0 | 100.0% |
| citation | 5 | 0 | 0 | 100.0% |

### 🔍 性能瓶颈识别
1. **total_pipeline模块**
   - 瓶颈类型: highest_total_time
   - 时长: 33.991秒
   - 占总时长: 100.0%

2. **total_pipeline模块**
   - 瓶颈类型: highest_average_time
   - 时长: 6.798秒
   - 影响级别: high

### 💡 性能优化建议
1. total_pipeline模块平均执行时间过长(6.80s)，建议优化算法或增加缓存

## 🎯 答案质量分析

- **高质量答案**: 0 个
- **中等质量答案**: 1 个
- **低质量答案**: 4 个
- **平均质量分数**: 0.348
- **质量分数范围**: 0.180 - 0.450
- **质量分布类型**: normal

## ⚡ 流水线性能分析

- **快速查询**: 3 个 (<0.1s)
- **正常查询**: 0 个 (0.1-1.0s)
- **慢速查询**: 2 个 (>1.0s)
- **平均执行时间**: 2.722 秒
- **总执行时间**: 13.608 秒

### 流水线时间详细分析
- **平均流水线时间**: 6.798秒
- **中位数流水线时间**: 6.802秒
- **最快流水线时间**: 6.791秒
- **最慢流水线时间**: 6.807秒
- **流水线效率**: 0.0% (1秒内完成)
- **慢速流水线数量**: 5 (>5秒)

## 🔧 系统配置信息

- **异步架构**: unified
- **最大并发任务**: 2
- **查询超时时间**: 90.0 秒
- **内存使用率**: 79.2%
- **可用内存**: 3.33 GB
- **已用内存**: 5.81 GB

## 📝 详细查询结果示例

### 查询示例 1
- **查询内容**: If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated p...
- **期望答案**: Jane Ballou
- **实际答案**: Jane Ballou...
- **FRAMES准确率**: 1.000
- **质量分数**: 0.450
- **创新性分数**: 0.000
- **执行时间**: 6.790 秒
- **流水线时间**: 6.791 秒
- **知识数量**: 1
- **引用数量**: 0
- **模块执行时间**:
  - knowledge_retrieval: 0.000s
  - reasoning: 0.000s
  - answer_generation: 0.000s
  - citation: 0.000s
- **模块执行类型**:
  - knowledge_retrieval: main_flow
  - reasoning: main_flow
  - answer_generation: main_flow
  - citation: main_flow

### 查询示例 2
- **查询内容**: Imagine there is a building called Bronte tower whose height in feet is the same number as the dewey decimal classification for the Charlotte Bronte b...
- **期望答案**: 37th
- **实际答案**: 37th...
- **FRAMES准确率**: 1.000
- **质量分数**: 0.370
- **创新性分数**: 0.000
- **执行时间**: 6.790 秒
- **流水线时间**: 6.791 秒
- **知识数量**: 1
- **引用数量**: 0
- **模块执行时间**:
  - knowledge_retrieval: 0.000s
  - reasoning: 0.000s
  - answer_generation: 0.000s
  - citation: 0.000s
- **模块执行类型**:
  - knowledge_retrieval: main_flow
  - reasoning: main_flow
  - answer_generation: main_flow
  - citation: main_flow

### 查询示例 3
- **查询内容**: How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capito...
- **期望答案**: 87
- **实际答案**: 87...
- **FRAMES准确率**: 1.000
- **质量分数**: 0.370
- **创新性分数**: 0.000
- **执行时间**: 0.011 秒
- **流水线时间**: 6.802 秒
- **知识数量**: 1
- **引用数量**: 0
- **模块执行时间**:
  - knowledge_retrieval: 0.000s
  - reasoning: 0.000s
  - answer_generation: 0.000s
  - citation: 0.000s
- **模块执行类型**:
  - knowledge_retrieval: main_flow
  - reasoning: main_flow
  - answer_generation: main_flow
  - citation: main_flow

... 还有 2 个成功结果

## 📈 评测总结

### 主要成果
1. **FRAMES基准准确率**: 80.0%
2. **系统成功率**: 100.0%
3. **推理创新性**: 0.00/1.0
4. **平均响应时间**: 2.72秒

### 关键发现
- 系统存在以下优化空间:
  - total_pipeline模块平均执行时间过长(6.80s)，建议优化算法或增加缓存

---
*详细评测报告生成时间: 2025-08-25T12:01:54.284523*
*本报告包含FRAMES基准测试的全面分析，为系统优化提供数据支持*
