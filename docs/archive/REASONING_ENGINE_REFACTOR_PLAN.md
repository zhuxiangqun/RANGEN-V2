# 推理引擎重构方案：从“流程烟雾”到“动态智能” (v3.0)

> **基于用户深度反馈的最终定稿版本**
> 
> **核心愿景**：将系统从一个“僵化的流程表演者”转变为一个“动态的实质思考者”，打造一个**聪明、高效、透明、可进化**的下一代推理引擎。

## 1. 核心问题诊断

当前 `RealReasoningEngine` 存在根本性的设计哲学错误，将“拥有推理过程”误认为“进行推理”：

1.  **僵化流水线 (Rigid Pipeline)**: 无论问题复杂度，强制执行固定的 4-7 步流程。
2.  **步骤空转 (Step Idling)**: “逻辑演绎”等步骤仅是 LLM 的复述，无**信息增益 (Information Gain)**。
3.  **虚假量化 (Fake Quantification)**: 置信度机械衰减（0.8 -> 0.5），缺乏真实评估。
4.  **无效耗时 (Inefficient Latency)**: 简单问题响应慢，且输出常被截断。

---

## 2. 新架构设计：双系统与动态图

### 2.1 双通道认知架构 (System 1 & System 2)

引入卡尼曼“快慢思考”架构，实现资源的最优分配：

*   **Fast Path (System 1 - 直觉/检索)**
    *   **适用场景**: 简单事实查询、已有高置信度知识。
    *   **流程**: Query -> **Safety Check** -> Retrieval/Generation -> **Light Verification** -> Output。
    *   **特点**: 毫秒级响应，低成本。
    *   **安全网 (Safety Net)**: 即使走快速通道，如果 `Light Verification` 发现答案含糊或证据单一，自动升级到 System 2。

*   **Slow Path (System 2 - 深度推理)**
    *   **适用场景**: 多跳推理、矛盾消解、复杂分析、需要使用工具的场景。
    *   **流程**: Query -> **Dynamic Planner** -> **Reasoning Loop** -> **Deep Verification** -> Output。
    *   **特点**: 动态迭代，算力换智能。

### 2.2 动态推理循环 (The Reasoning Loop)

废弃线性列表，构建基于状态机的 **While Loop**：

```python
state = ReasoningState(query, evidence)
while not state.is_solved() and not state.budget_exhausted():
    # 1. 规划 (Plan): 决定下一步操作 (Retrieve / Deduce / Verify / ToolUse)
    next_op = planner.decide_next_step(state)
    
    # 2. 执行 (Act): 调用实质性算子，产生信息增益
    result = executor.execute(next_op)
    
    # 3. 更新 (Update): 更新状态图谱 (Knowledge Graph / Fact List)
    state.update(result)
    
    # 4. 反思 (Reflect): 检查是否偏离目标，必要时触发 Re-planning
    if state.is_stuck():
        planner.replan()
```

### 2.3 实质性推理算子 (Substantive Operators)

将“步骤”替换为具有明确**输入/输出契约**的功能算子，并引入**元算子**概念以避免算子爆炸：

| 算子类型 | 功能描述 | 典型应用 |
| :--- | :--- | :--- |
| **Extraction** | 从非结构化文本提取实体/关系 | 文本 -> 结构化事实 |
| **Comparison** | 识别多源证据的异同 | 独立事实 -> 矛盾点/共识点 |
| **Synthesis** | 拼凑碎片信息 | 碎片 -> 完整链条 |
| **Verification** | 验证假设或答案 | 假设 -> 真/假/不确定 |
| **ToolUse** | **[New]** 调用外部工具或计算能力 | 计算增长率、搜索实时信息 |
| **Meta-Op** | **[New]** 基础算子 + 动态 Prompt | 针对特定矛盾点的专项分析 |

---

## 3. 关键子系统设计

### 3.1 动态规划器与反思机制 (Planner & Reflection)

为解决 **Planner 可靠性** 与 **反思成本** 的矛盾：

1.  **安全网机制**: 简单的规则引擎作为 Planner 的前置守门员。
2.  **务实的反思 (Pragmatic Reflection)**:
    *   **规则驱动**: 连续 3 步无信息增益 / 置信度连续下降 -> 触发反思。
    *   **轻量询问**: 使用 Fast LLM 快速评估“我们是否在接近答案？”，低成本判断方向。
3.  **多视角投票**: (可选) 高价值问题使用 Ensemble Planning。

### 3.2 分层置信度体系 (Layered Confidence)

为解决 **评估真实性与成本** 的矛盾，建立分层评估模型：

*   **Level 1 (基础 - 低成本)**: 基于证据元数据、答案完整性。 *适用于 Fast Path。*
*   **Level 2 (逻辑 - 中成本)**: 基于内部一致性、约束覆盖度。 *适用于 Slow Path 中间态。*
*   **Level 3 (深度 - 高成本)**: **Self-Consistency** (多次生成一致性) + **NLI** (蕴含分数)。 *仅在最终答案置信度处于“灰色地带”时触发。*

**输出**: 不仅输出分数，还输出**不确定性来源**（如“证据冲突”、“推理跳跃”）。

### 3.3 状态管理 (Context Management)

明确定义 `ReasoningState`，构建动态知识图谱骨架：

```python
class ReasoningState:
    def __init__(self, query):
        self.query = query
        self.facts = []          # 已验证的事实 (Facts)
        self.hypotheses = []     # 待验证的假设 (Hypotheses)
        self.information_gaps = [] # 缺失的信息点 (Information Gaps)
        self.history = []        # 操作历史 (轨迹)
        self.contradictions = [] # 发现的矛盾点
        self.tools = []          # 可用工具列表 [New]
```

---

## 4. 数据飞轮与持续进化 (Data Flywheel)

为系统建立长期的**进化机制**：

1.  **轨迹记录 (Trajectory Recording)**: 结构化存储每一次推理的完整快照（State变化、决策点、算子输出）。
2.  **强化学习数据集 (RLHF Dataset)**: 基于用户反馈（点赞/点踩）对轨迹进行打分，构建 DPO/PPO 训练数据。
3.  **自我优化**: 定期分析失败案例（Low Confidence + Bad Feedback），自动优化 Planner 的 Prompt 或微调模型。

---

## 5. 实施路线图 (Roadmap)

### Phase 1: 熔断与清理 (The Breaker) - *Immediate Action*
*   **目标**: 立即停止无效空转，恢复系统诚实度。
*   **行动**:
    1.  **入口熔断**: `reason` 方法增加严格校验，无有效 Evidence 且非简单寒暄 -> 立即返回“无法回答”。
    2.  **清理空转**: 移除 `_perform_reasoning_steps` 中的表演性代码。
    3.  **修复截断**: 彻底检查并修复所有可能的字符串截断点。

### Phase 2: 基础双通道与可视化 (The Dual-System & Viz)
*   **目标**: 解决简单问题耗时过长，让过程可见。
*   **行动**:
    1.  实现 `FastPath` 逻辑。
    2.  实现基础的 `Planner`。
    3.  **[New] 可视化原型**: 实现推理过程的动态有向图 (GraphViz/Mermaid) 输出，辅助调试。

### Phase 3: 深度推理算子与工具 (The Deep Reasoner & Tools)
*   **目标**: 解决复杂问题推理能力弱，增强动手能力。
*   **行动**:
    1.  实现 `Extraction`, `Comparison`, `Synthesis` 等核心算子。
    2.  实现 `ToolUse` 算子框架。
    3.  构建 `Reasoning Loop` 状态机。

### Phase 4: 高级优化与进化 (The Evolution)
*   **目标**: 提升鲁棒性，建立数据飞轮。
*   **行动**:
    1.  引入 Level 3 (Self-Consistency) 评估。
    2.  完善 `Reflection` 机制。
    3.  部署轨迹记录与回放系统。

---

## 6. 总结

本方案（v3.0）是一个**可执行的、防御性设计的、具备进化潜力的系统工程方案**。它不仅解决了当前的痛点，更为未来的具身智能和持续学习奠定了坚实的架构基础。

*   **输入**: 问题 + 原始数据
*   **过程**: 动态规划 -> 实质加工 (含工具调用) -> 真实评估 -> 持续进化
*   **输出**: 经得起推敲的答案 + 清晰的置信度来源
