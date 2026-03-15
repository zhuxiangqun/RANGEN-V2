# AI Interviewer System Solution (Powered by RANGEN V2)

本文档描述了如何利用 RANGEN V2 的**双脑智能**与**动态难度加载 (DDL)** 能力，快速构建一个专业的 AI 面试官系统。

## 1. 核心价值主张

利用 RANGEN V2 的特性，该面试系统将具备以下独特优势：

*   **动态追问 (DDL)**: 根据候选人回答的深度（复杂度 Beta），自动调整下一个问题的难度。回答太简单则追问细节，回答深入则探讨架构。
*   **低成本初筛 (Phi-3)**: 简单的寒暄、背景确认由本地模型完成，零成本。
*   **深度技术评估 (DeepSeek)**: 复杂的架构设计题、代码评审由云端大模型进行深度分析。
*   **简历与知识库 (KMS)**: 将职位描述 (JD) 和候选人简历导入 KMS，实现基于事实的精准提问。

## 2. 系统架构

该系统作为 RANGEN V2 的上层应用 (`Application Layer`) 存在。

```mermaid
graph TD
    User[Candidate] --> Frontend[Web UI (Streamlit/React)]
    Frontend --> InterviewerAgent[AI Interviewer Agent]
    
    subgraph "RANGEN V2 Core"
        InterviewerAgent --> Engine[RealReasoningEngine]
        InterviewerAgent --> KMS[Knowledge Management]
    end
    
    subgraph "Data Sources"
        Resume[Resume PDF] --> KMS
        JD[Job Description] --> KMS
        QuestionBank[Question Bank] --> KMS
    end
```

## 3. 核心流程设计

### 3.1 准备阶段 (Knowledge Injection)
面试开始前，需要将上下文注入 KMS。

*   **动作**: 使用 `TransactionalKnowledgeManager` 导入数据。
*   **内容**:
    1.  **职位描述 (JD)**: "高级 Python 工程师，熟悉 RAG，了解 asyncio..."
    2.  **候选人简历**: "张三，5年经验，曾主导 KMS 重构..."
    3.  **面试题库**: 预设的一些标准问题（可选）。

### 3.2 面试阶段 (The Interview Loop)

面试过程是一个基于状态机的循环，由 `InterviewerAgent` 控制。

#### 阶段 A: 破冰与核实 (Phase: Ice-breaking)
*   **策略**: **Fast Path (Phi-3)**
*   **逻辑**: "请简单介绍一下你自己。" -> Phi-3 快速生成回应，确认基本信息。
*   **目的**: 低延迟，营造轻松氛围。

#### 阶段 B: 技术考察 (Phase: Technical Deep Dive)
*   **策略**: **DDL Adaptive (Direct -> CoT)**
*   **逻辑**:
    1.  **提问**: "你提到熟悉 RAG，请讲讲你是如何解决检索幻觉的？"
    2.  **收听回答**: 候选人输入回答。
    3.  **评估 (关键)**: 调用 `RealReasoningEngine` 分析回答的**复杂度 (Beta)** 和 **质量**。
        *   如果 Beta < 0.5 (回答肤浅): **追问细节** ("具体是用什么指标衡量的？")
        *   如果 Beta > 1.0 (回答深入): **升级难度** ("如果数据量达到 10亿级，你的方案还需要怎么调整？")
*   **技术点**: 利用 RANGEN 的 `context['ddl_beta_hint']` 来感知候选人的水平。

#### 阶段 C: 架构设计 (Phase: System Design)
*   **策略**: **CoT Strategy (DeepSeek R1)**
*   **逻辑**: 给出一个开放性问题 ("设计一个高并发的秒杀系统")，让 DeepSeek 进行思维链评估，检查候选人的思考过程是否严谨。

### 3.3 评估阶段 (Evaluation)
面试结束后，生成面试报告。
*   **动作**: 将整个对话记录作为 Context，让 DeepSeek 生成总结。
*   **输出**: 技术深度评分、沟通能力评分、匹配度建议。

## 4. 核心代码实现示例

### 4.1 知识导入脚本 (`scripts/interview_prep.py`)

```python
from knowledge_management_system.core.transactional_knowledge_manager import TransactionalKnowledgeManager

def prepare_interview(candidate_name, resume_text, jd_text):
    kms = TransactionalKnowledgeManager()
    
    # 导入简历
    kms.add_knowledge(
        content=resume_text, 
        metadata={"type": "resume", "candidate": candidate_name}
    )
    
    # 导入 JD
    kms.add_knowledge(
        content=jd_text, 
        metadata={"type": "jd", "role": "Senior Engineer"}
    )
    print("✅ Interview context loaded.")
```

### 4.2 面试官代理 (`src/apps/interviewer.py`)

```python
from src.core.real_reasoning_engine import RealReasoningEngine

class AIInterviewer:
    def __init__(self):
        self.engine = RealReasoningEngine()
        self.history = []
        
    async def ask(self, candidate_input: str):
        # 1. 构建 Prompt，包含面试官的人设
        system_prompt = """
        你是一个专业的各种技术面试官。
        根据候选人的回答深度，动态调整下一个问题的难度。
        如果回答太简单，请追问细节；如果回答很好，请转入更深的话题。
        """
        
        # 2. 组合上下文
        context = {
            "history": self.history,
            "role_instruction": system_prompt,
            # 💡 关键：告诉 RANGEN 这是一个面试场景，需要评估复杂度
            "complexity_sensitivity": "high" 
        }
        
        # 3. 调用核心引擎
        # RANGEN 会自动路由：
        # - 简单的寒暄 -> Phi-3
        # - 复杂的技术评估 -> DeepSeek
        result = await self.engine.reason(candidate_input, context)
        
        # 4. 记录历史
        self.history.append(f"Candidate: {candidate_input}")
        self.history.append(f"Interviewer: {result.final_answer}")
        
        return result.final_answer
```

## 5. 实施路线图

1.  **Day 1: 数据准备**: 编写脚本，支持解析 PDF 简历并导入 KMS。
2.  **Day 2: 代理逻辑**: 实现 `AIInterviewer` 类，通过 Prompt Engineering 定义面试官的人格。
3.  **Day 3: 前端集成**: 使用 Streamlit 快速搭建一个聊天界面。
4.  **Day 4: 评估报告**: 增加面试后的总结生成功能。

## 6. 优势总结

这个方案不仅仅是一个 "Chatbot"，它是一个**有策略的面试官**：
*   它**记得**简历细节（KMS）。
*   它**感知**回答深度（Phi-3 Beta Analysis）。
*   它**具备**专家级判断力（DeepSeek R1）。
*   它**极其省钱**（大部分寒暄和简单追问都在本地完成）。
