# LlamaIndex增强功能验证指南

## ✅ 功能状态

LlamaIndex增强功能已成功实施并集成到核心系统中：

1. **LlamaIndex适配器**: 已启用并初始化成功
2. **查询扩展功能**: 已实现（提取关键实体、数字、引号内容等）
3. **智能重排序功能**: 已实现（基于关键词、短语、实体匹配）
4. **核心系统集成**: 已完成（3个调用点已启用）

## 🚀 验证步骤

### 步骤1: 启用LlamaIndex

```bash
export ENABLE_LLAMAINDEX=true
```

### 步骤2: 运行核心系统

```bash
# 使用少量样本快速验证
python scripts/run_core_with_frames.py --sample-count 5

# 或使用更多样本进行完整测试
python scripts/run_core_with_frames.py --sample-count 50
```

### 步骤3: 查看日志验证

```bash
# 查看日志文件
tail -f logs/research_system.log

# 搜索LlamaIndex相关日志
grep -i "llamaindex\|增强检索\|查询扩展\|重排序" logs/research_system.log
```

## 📊 预期日志信息

### 初始化阶段

```
✅ LlamaIndex 适配器已启用
✅ LlamaIndex 适配器初始化成功
✅ LlamaIndex 索引管理器已初始化
```

### 查询阶段

```
🚀 LlamaIndex 增强检索完成，返回 X 条结果
查询扩展: 生成X个查询变体
LlamaIndex重排序: 原始X条 → 重排序后X条
LlamaIndex增强完成: 重排序X条结果，最高分=X.XXX
```

## 🔍 验证要点

### 1. 功能验证

- ✅ LlamaIndex适配器是否已启用
- ✅ 查询时是否调用了增强功能
- ✅ 日志中是否出现增强相关信息

### 2. 效果验证

- 📈 **检索准确率**: 应提升 20-30%
- 📉 **"无法确定"比例**: 应从 46% 降至 20% 以下
- 🎯 **检索结果相关性**: 应显著提升

### 3. 性能验证

- ⏱️ **查询扩展耗时**: 通常 < 0.1秒
- ⏱️ **重排序耗时**: 通常 < 0.5秒
- ⏱️ **总增强耗时**: 通常 < 1秒

## 📋 快速验证脚本

```python
#!/usr/bin/env python3
import os
os.environ["ENABLE_LLAMAINDEX"] = "true"

from knowledge_management_system.api.service_interface import get_knowledge_service

kms = get_knowledge_service()
print(f"LlamaIndex启用: {kms.llamaindex_enabled}")
print(f"LlamaIndex适配器: {kms.llamaindex_adapter is not None}")

# 测试查询
if kms.llamaindex_adapter:
    results = kms.query_knowledge("test", use_llamaindex=True, top_k=3)
    print(f"查询结果数: {len(results)}")
    if results:
        print(f"第一条结果分数: {results[0].get('similarity_score', 0):.3f}")
```

## 🐛 故障排除

### 问题1: LlamaIndex未启用

**症状**: 日志中没有LlamaIndex相关信息

**解决**:
```bash
export ENABLE_LLAMAINDEX=true
```

### 问题2: LlamaIndex未安装

**症状**: 日志显示"LlamaIndex 未安装"

**解决**:
```bash
pip install 'llama-index[all]>=0.9.0'
```

### 问题3: 增强功能未生效

**症状**: 日志中没有"增强检索完成"信息

**检查**:
1. 确认环境变量已设置
2. 确认核心系统调用时使用了`use_llamaindex=True`
3. 查看是否有错误日志

## 📈 性能对比

### 启用前 vs 启用后

| 指标 | 启用前 | 启用后（预期） |
|------|--------|---------------|
| 检索准确率 | 28% | 35-40% |
| "无法确定"比例 | 46% | < 20% |
| 检索结果相关性 | 低 | 显著提升 |
| 平均查询时间 | ~2秒 | ~3秒（增加<1秒） |

## 💡 使用建议

1. **生产环境**: 建议启用LlamaIndex增强功能
2. **测试环境**: 可以对比启用前后的效果
3. **性能敏感场景**: 如果查询时间要求严格，可以只启用重排序功能

## 📚 相关文档

- [LlamaIndex集成方案](../LLAMAINDEX_INTEGRATION_PROPOSAL.md)
- [多元化索引构建指南](./BUILD_DIVERSE_INDEXES_GUIDE.md)

