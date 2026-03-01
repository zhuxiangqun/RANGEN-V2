# 推理链子查询问题分析

## 问题确认

从终端输出可以看到，**推理链各个节点的查询内容确实有问题**，这是导致证据检索失败的根本原因。

## 问题子查询示例

### 1. 步骤2 - 包含完整推理过程
```
原始: What is the 15th First Lady of the United States. The 15th president was James Buchanan (1857–1861). James Buchanan never married, so there was no official First Lady. Harriet Lane, his niece, served as White House hostess and is often considered the '15th First Lady' in some lists.?
```
**问题**：
- 包含多个句子和完整推理过程
- 包含历史事实（"James Buchanan never married"）
- 包含答案（"Harriet Lane"）

**应该清理为**：`Who was the 15th first lady of the United States?`

### 2. 步骤3 - 包含推理过程和答案
```
原始: What is Harriet Lane's mother's first name. Harriet Lane was the daughter of James Buchanan's sister, Jane Buchanan Lane. Jane Buchanan Lane's mother (Harriet's grandmother) was Elizabeth Speer Buchanan. However, the query asks for 'the 15th first lady's mother'—if we treat Harriet Lane as the 15th First Lady, her mother was Jane Buchanan Lane. Jane's first name is Jane.?
```
**问题**：
- 包含完整推理过程
- **直接包含了答案**（"Jane's first name is Jane"）
- 包含多个句子

**应该清理为**：`Who is Harriet Lane's mother?` 或 `What is Harriet Lane's mother's first name?`

### 3. 步骤5 - 包含推理过程
```
原始: What is the second assassinated U.S. president. The first assassinated president was Abraham Lincoln (1865). The second assassinated president was James A. Garfield (1881).?
```
**问题**：
- 包含推理过程（"The first assassinated president was..."）
- 包含答案（"James A. Garfield"）

**应该清理为**：`Who was the second assassinated president of the United States?`

### 4. 步骤6 - 直接包含答案
```
原始: What is James A. Garfield's mother's maiden name. Garfield's mother was Eliza Ballou Garfield. Her maiden name was Ballou.?
```
**问题**：
- **直接包含了答案**（"Her maiden name was Ballou"）
- 包含推理过程

**应该清理为**：`What is James A. Garfield's mother's maiden name?`

### 5. 步骤7 - 查询本身有问题
```
原始: What is the surname of the second assassinated president's mother's maiden name?
```
**问题**：
- 查询逻辑错误（"surname of ... maiden name"是重复的）
- 应该问"maiden name"而不是"surname of maiden name"

**应该清理为**：`What is the second assassinated president's mother's maiden name?`

## 根本原因

1. **LLM生成的推理步骤包含推理过程和答案**
   - LLM在生成推理步骤时，可能直接在描述中包含推理过程和答案
   - 这些内容被错误地作为`sub_query`使用

2. **子查询清理逻辑不够严格**
   - 当前的清理逻辑虽然尝试提取纯问题，但对于包含答案的情况处理不够
   - 需要更激进的清理策略

3. **缺少答案检测**
   - 没有检测子查询中是否直接包含了答案
   - 如果包含答案，应该重新生成查询

## 改进方案

### 1. 增强子查询清理逻辑（P0）

**策略**：
- 检测并移除包含答案的子查询
- 更严格地提取纯问题部分
- 如果无法清理，使用原始查询的关键部分重新生成

### 2. 答案检测和过滤（P0）

**策略**：
- 检测子查询中是否包含答案模式（如"is X", "was X", "name is X"）
- 如果检测到答案，重新生成查询

### 3. 改进推理步骤生成提示词（P1）

**策略**：
- 在生成推理步骤时，明确要求`sub_query`字段必须是纯问题格式
- 禁止在`sub_query`中包含推理过程或答案

### 4. 后处理验证（P1）

**策略**：
- 在子查询清理后，验证是否是纯问题格式
- 如果不是，使用更激进的清理策略或重新生成

