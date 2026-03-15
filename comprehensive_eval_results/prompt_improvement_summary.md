# 提示词改进总结

生成时间: 2025-11-03
改进目标: 解决LLM过度依赖不相关证据的问题

## 🔍 问题诊断

### 用户观察
用户指出两个关键问题：
1. **提示词问题** - LLM没有给出正确答案
2. **知识库检索** - 是否找到了相应的内容

### 分析发现

#### 1. 知识检索执行情况 ✅
- ✅ 知识检索在执行（每个样本都检索到了知识）
- ✅ 每个样本检索到15条结果
- ⚠️ 但检索到的知识质量有问题

#### 2. 具体案例
- **样本1**: 检索到"James Buchanan"（15th president），但问题是关于first lady的母亲
- **样本2**: 检索到"Charlotte Brontë"（作家），但问题是关于建筑高度
- **样本4**: 检索到"London"（城市），但问题是关于FIFA World Cup持有者（国家）

#### 3. 提示词问题 ⚠️⚠️⚠️
- **当前问题**: 
  - 强调"PRIORITIZE EVIDENCE"和"TRUST and USE it"
  - 没有明确指导如何处理不相关的证据
  - 没有强调当证据不准确时应该使用自己的知识库

- **影响**:
  - LLM可能过度依赖检索到的知识（即使不准确）
  - 当证据不相关时，LLM可能仍然尝试使用它
  - 没有足够使用LLM自己的知识库进行推理

## 🔧 已完成的改进

### 改进1: 提示词增强 - 证据质量评估和智能使用 ✅

**文件**: `templates/templates.json` (reasoning_with_evidence模板)

**改进内容**:
1. **证据质量评估优先** (STEP 1):
   - 在使用证据前，必须评估其相关性
   - 检查证据是否与问题主题匹配（如：人物问题→人物证据？）
   - 确定相关性级别：HIGH/MEDIUM/LOW/IRRELEVANT

2. **智能证据使用** (STEP 2):
   - 如果证据高度相关 → 直接使用
   - 如果证据部分相关 → 结合自己的知识
   - **如果证据不相关或误导 → 完全忽略，使用自己的知识库**

3. **明确规则**:
   - 如果证据与问题主题不匹配（如人物 vs 地点），**不要使用它**
   - 当证据不相关时，主动使用自己的知识库

4. **推理步骤增强**:
   - Step 1现在要求评估证据的相关性
   - 明确记录决策：使用证据 / 忽略证据（使用自己的知识）/ 结合两者

**代码位置**: `templates/templates.json` lines 37-38

## 📋 改进前后对比

### 改进前
```
2. Evidence Processing (CRITICAL):
   ✅ **PRIORITIZE EVIDENCE**: Always use the provided evidence FIRST
   ✅ If evidence is provided, it is highly relevant - TRUST and USE it
   ⚠️ Only use your own knowledge when evidence is completely insufficient
```

**问题**: 
- 强制优先使用证据，即使不相关
- 假设证据总是相关的
- 只有当证据完全不足时才使用自己的知识

### 改进后
```
2. Evidence Processing (CRITICAL - SMART USAGE):
   ✅ **STEP 1: EVIDENCE QUALITY ASSESSMENT** (MANDATORY FIRST STEP):
      - Evaluate RELEVANCE before using
      - Check topic match
      - Determine: HIGH/MEDIUM/LOW/IRRELEVANT
   
   ✅ **STEP 2: INTELLIGENT EVIDENCE USAGE**:
      - If IRRELEVANT: IGNORE IT and use your knowledge base
      - If doesn't match topic: DO NOT use it
   
   ⚠️ **CRITICAL RULE**: If evidence unrelated, use your knowledge base
```

**改进**:
- 必须先评估证据质量
- 明确指导忽略不相关证据
- 强调使用自己的知识库

## 🎯 预期改进效果

### 直接效果
1. **LLM能够识别不相关证据**:
   - 评估证据与问题的相关性
   - 识别主题不匹配的情况

2. **LLM能够主动使用自己的知识库**:
   - 当证据不相关时，忽略它
   - 使用自己的知识库回答问题

3. **改善的样本**:
   - **样本1**: LLM应该识别"James Buchanan"（president）与"first lady的母亲"不相关，使用自己的知识库
   - **样本2**: LLM应该识别"Charlotte Brontë"（作家）与"建筑高度"不相关，使用自己的知识库
   - **样本4**: LLM应该识别"London"（城市）与"FIFA World Cup持有者"（国家）不相关，使用自己的知识库

### 准确率预期
- **改进前**: 10% (1/10)
- **预期改进后**: 40-50% (4-5/10)
  - 样本1：应该能够正确回答（使用自己的知识库）
  - 样本2：应该能够正确回答或至少更接近
  - 样本4：应该能够正确回答（France）

## 📝 后续改进建议

### P0 - 知识检索质量改进
1. **提高相似度阈值**: 从0.30提高到0.40-0.50
2. **改进查询重写**: 生成更精确的检索查询
3. **增强验证逻辑**: 更严格地验证检索结果的相关性

### P1 - 验证改进效果
1. **重新运行测试**: 验证提示词改进是否生效
2. **检查推理过程**: 确认LLM是否正确评估和使用证据
3. **分析准确率变化**: 检查是否有改善

## ✅ 已完成的工作

- [x] 改进提示词模板（证据质量评估和智能使用）
- [x] 分析知识检索问题
- [x] 生成改进总结文档

## 📊 总结

**核心改进**:
- ✅ 提示词现在要求先评估证据相关性
- ✅ 明确指导忽略不相关证据
- ✅ 强调使用自己的知识库当证据不相关时

**关键洞察**:
- 用户观察非常准确：确实是提示词和知识检索的问题
- 知识检索找到了内容，但质量不足
- 提示词强制使用证据，即使不相关

**下一步**:
1. 验证提示词改进效果
2. 改进知识检索质量（相似度阈值、查询重写）
3. 根据结果进一步优化

