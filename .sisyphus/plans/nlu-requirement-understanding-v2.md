# RANGEN AI中台 - 智能需求理解与自动能力构建方案

> **版本**: v2.1 (能力类型识别优先)  
> **目标**: 将RANGEN打造为纯AI能力中台  
> **核心理念**: 识别类型 → 匹配能力 → 补充缺失

---

## 一、核心流程（能力类型识别优先）

```
用户输入: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"

    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段0: 能力类型识别 (Capability Type Detection) - 第一优先级        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  使用LLM判断用户需求需要什么层次的能力:                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Tool  (工具层)                                             │   │
│  │  ─────────────                                              │   │
│  │  单一操作: 搜索、计算、读写文件、执行代码                    │   │
│  │  示例: "搜索今天天气"、"计算1+1"                            │   │
│  │  判断: 用户只想做一件具体的事                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Skill (技能层) - 多个Tool的组合                           │   │
│  │  ─────────────────────                                     │   │
│  │  复合能力: RAG检索、代码分析、测试执行                      │   │
│  │  示例: "帮我查一下RAG的原理"、"分析这段代码"                │   │
│  │  判断: 用户需要完成一个技能任务                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Agent (智能体层) - Skill + 推理                           │   │
│  │  ─────────────────────                                     │   │
│  │  完整智能体: 带思考能力的角色                               │   │
│  │  示例: "帮我写一个排序算法"、"当我的技术顾问"              │   │
│  │  判断: 用户需要一个能自主推理的助手                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Team (团队层) - 多个Agent协作                             │   │
│  │  ─────────────────────                                     │   │
│  │  多角色协作: PM + Dev + QA + Architect                     │   │
│  │  示例: "帮我建立一个研发团队"、"做一个完整项目"            │   │
│  │  判断: 用户需要多个角色协作完成复杂任务                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 识别结果: "Team" (需要多个Agent协作)
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段1: 基于类型的需求理解                                          │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  阶段2: 能力匹配与构建                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、能力层次定义

### 2.1 RANGEN现有能力层次

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RANGEN 能力层次                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Team (团队)                                                       │
│  ─────────                                                         │
│  • 多个Agent协作                                                   │
│  • 协作流程编排                                                     │
│  • 示例: 软件研发团队 = PM + Dev + QA + Architect                  │
│  • 复用: AgentCoordinator                                          │
│                                                                     │
│  Agent (智能体)                                                     │
│  ───────────                                                       │
│  • Skill + 推理能力 + Prompt                                        │
│  • 能自主思考和决策                                                │
│  • 示例: ReasoningAgent, RAGAgent                                   │
│  • 复用: AgentBuilder                                             │
│                                                                     │
│  Skill (技能)                                                      │
│  ────────                                                         │
│  • 多个Tool的组合                                                  │
│  • 有明确的目标和能力描述                                          │
│  • 示例: rag-retrieval, code_analysis                             │
│  • 复用: SkillRegistry, SkillFactory                              │
│                                                                     │
│  Tool (工具)                                                       │
│  ───────                                                          │
│  • 单一功能执行                                                    │
│  • 最小执行单元                                                    │
│  • 示例: web_search, file_reader, calculator                      │
│  • 复用: ToolRegistry                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 需求类型识别规则

| 用户输入特征 | 识别类型 | 示例 |
|-------------|---------|------|
| 单一操作动词 | **Tool** | "搜索今天天气"、"计算总和" |
| 技能任务描述 | **Skill** | "查一下RAG原理"、"分析这段代码" |
| 需要"助手"/"顾问"/"帮我" | **Agent** | "当我技术顾问"、"帮我写个算法" |
| "建立团队"/"多角色"/"完整流程" | **Team** | "建立研发团队"、"做完整项目" |

---

## 三、详细实现方案

### 3.1 新增模块

```
src/core/nlu_bridge/
├── __init__.py
├── capability_type_detector.py   # 新增: 能力类型识别器
├── requirement_parser.py          # 新增: 需求解析器
└── team_builder.py               # 新增: 团队构建器
```

### 3.2 能力类型识别器

```python
# src/core/nlu_bridge/capability_type_detector.py
"""
能力类型识别器 - 第一步：判断需求需要什么层次的能力

这是整个流程的第一优先级！
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CapabilityType(Enum):
    """能力类型枚举"""
    TOOL = "tool"           # 单一工具
    SKILL = "skill"         # 技能组合
    AGENT = "agent"         # 智能体
    TEAM = "team"           # 多Agent团队
    UNKNOWN = "unknown"     # 未知

@dataclass
class TypeDetectionResult:
    """类型识别结果"""
    primary_type: CapabilityType      # 主要类型
    confidence: float                # 置信度
    reasoning: str                   # 识别理由
    suggested_actions: list          # 建议操作
    secondary_types: list            # 可能的次要类型

class CapabilityTypeDetector:
    """
    能力类型识别器
    
    使用LLM分析用户输入，判断需要什么层次的能力
    """
    
    # 能力类型描述 (用于LLM理解)
    TYPE_DESCRIPTIONS = {
        CapabilityType.TOOL: """
            TOOL (工具层): 用户只需要完成一个单一的操作动作
            - 特征: 搜索、计算、查询、执行一个具体命令
            - 示例: "搜索今天天气"、"1+1等于多少"、"打开文件"
            - 关键词: 搜索、计算、查询、打开、执行
        """,
        CapabilityType.SKILL: """
            SKILL (技能层): 用户需要完成一个完整的能力任务
            - 特征: 需要多个工具组合才能完成的任务
            - 示例: "查一下RAG的原理"、"分析这段代码"、"帮我测试"
            - 关键词: 分析、测试、检索、查询知识、解释
        """,
        CapabilityType.AGENT: """
            AGENT (智能体层): 用户需要一个能自主推理的助手
            - 特征: 需要AI进行思考、推理、决策的任务
            - 示例: "当我技术顾问"、"帮我写一个排序算法"、"帮我规划"
            - 关键词: 顾问、帮助、规划、建议、帮我(做)
        """,
        CapabilityType.TEAM: """
            TEAM (团队层): 用户需要多个角色协作完成复杂任务
            - 特征: 需要建立团队、多角色协作、完整流程
            - 示例: "建立研发团队"、"做完整项目"、"创建协作流程"
            - 关键词: 团队、协作、建立(团队/流程)、多角色
        """
    }
    
    def __init__(self):
        self.llm_client = None  # 复用现有LLM
    
    async def detect(self, user_input: str) -> TypeDetectionResult:
        """
        识别用户需求需要的能力类型
        
        这是整个流程的【第一步】！
        """
        
        # 构建识别提示词
        prompt = self._build_detection_prompt(user_input)
        
        # 调用LLM识别
        response = await self._call_llm(prompt)
        
        # 解析结果
        result = self._parse_response(response)
        
        return result
    
    def _build_detection_prompt(self, user_input: str) -> str:
        """构建类型识别提示词"""
        return f"""
你是一个能力类型识别器。请分析用户输入，判断用户需要什么层次的能力。

用户输入: {user_input}

能力类型定义:
{self.TYPE_DESCRIPTIONS[CapabilityType.TOOL]}
{self.TYPE_DESCRIPTIONS[CapabilityType.SKILL]}
{self.TYPE_DESCRIPTIONS[CapabilityType.AGENT]}
{self.TYPE_DESCRIPTIONS[CapabilityType.TEAM]}

请输出JSON格式:
{{
    "primary_type": "tool/skill/agent/team",
    "confidence": 0.0-1.0,
    "reasoning": "为什么这么判断",
    "suggested_actions": ["建议的下一步操作"],
    "secondary_types": ["可能的次要类型"]
}}

只输出JSON，不要其他内容。
"""
```

### 3.3 完整流程处理

```python
# src/core/nlu_bridge/requirement_handler.py
"""
需求处理器 - 完整流程
"""

from capability_type_detector import CapabilityTypeDetector, CapabilityType
from requirement_parser import RequirementParser
from team_builder import TeamBuilder
from skill_builder import SkillBuilder
from tool_builder import ToolBuilder
from src.services.capability_checker import CapabilityChecker

class RequirementHandler:
    """
    需求处理器 - 完整流程
    
    流程:
    1. 识别能力类型 (第一优先级)
    2. 解析具体需求
    3. 匹配/构建能力
    4. 执行
    """
    
    def __init__(self):
        self.type_detector = CapabilityTypeDetector()
        self.requirement_parser = RequirementParser()
        self.capability_checker = CapabilityChecker()
        self.team_builder = TeamBuilder()
        self.skill_builder = SkillBuilder()
        self.tool_builder = ToolBuilder()
    
    async def handle(self, user_input: str) -> dict:
        """
        处理用户需求
        
        【第一步】: 识别能力类型
        """
        
        # 1. 识别能力类型 (第一优先级！)
        type_result = await self.type_detector.detect(user_input)
        
        # 2. 根据类型处理
        if type_result.primary_type == CapabilityType.TOOL:
            return await self._handle_tool(user_input, type_result)
        elif type_result.primary_type == CapabilityType.SKILL:
            return await self._handle_skill(user_input, type_result)
        elif type_result.primary_type == CapabilityType.AGENT:
            return await self._handle_agent(user_input, type_result)
        elif type_result.primary_type == CapabilityType.TEAM:
            return await self._handle_team(user_input, type_result)
        else:
            return await self._handle_unknown(user_input, type_result)
    
    async def _handle_team(self, user_input: str, type_result) -> dict:
        """处理团队需求"""
        
        # 1. 解析团队需求 (复用现有NLU)
        analysis = await self.requirement_parser.parse(user_input)
        
        # 2. 检查能力缺失
        capability_check = self.capability_checker.check_skills(analysis.required_skills)
        
        # 3. 自动构建缺失能力 (复用SkillFactory)
        if capability_check.missing:
            await self.skill_builder.auto_create(capability_check.missing)
        
        # 4. 构建团队 (复用AgentBuilder)
        team = await self.team_builder.build(analysis)
        
        return {
            "type": "team",
            "team": team,
            "message": f"✅ 已创建{team.name}，包含{len(team.members)}个角色"
        }
    
    # ... 其他处理方法类似
```

---

## 四、API设计

### 4.1 核心API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/detect-type` | POST | 识别能力类型（第一优先级） |
| `/api/v1/understand` | POST | 完整需求理解（包含类型识别） |
| `/api/v1/team/create` | POST | 创建团队 |
| `/api/v1/skill/create` | POST | 创建技能 |
| `/api/v1/agent/create` | POST | 创建智能体 |

### 4.2 请求示例

**POST /api/v1/detect-type**

```json
// Request
{
    "query": "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"
}

// Response
{
    "success": true,
    "detection": {
        "primary_type": "team",
        "confidence": 0.95,
        "reasoning": "用户提到'建立团队'，需要PM、开发者、QA等多个角色协作完成复杂任务",
        "suggested_actions": [
            "解析团队需求",
            "创建所需角色",
            "定义协作流程"
        ],
        "secondary_types": []
    }
}
```

---

## 五、复用映射

| 功能 | 复用现有 | 说明 |
|------|---------|------|
| 类型识别LLM | `AISkillTrigger` | 使用其LLM客户端 |
| 需求解析 | 新增 | 理解具体需求内容 |
| Skill检查 | `CapabilityChecker.check_skills()` | 检查现有能力 |
| Skill创建 | `SkillFactoryIntegration` | 自动创建Skill |
| Agent创建 | `AgentBuilder` | 创建Agent |
| Team协作 | `AgentCoordinator` | 协调多Agent |

---

## 六、实施计划

| 阶段 | 时间 | 任务 |
|------|------|------|
| Phase 1 | 第1天 | 能力类型识别器 (`capability_type_detector.py`) |
| Phase 2 | 第2天 | 需求解析器 (`requirement_parser.py`) |
| Phase 3 | 第3天 | 团队/技能/Agent构建器 |
| Phase 4 | 第4天 | API集成 |
| Phase 5 | 第5天 | 测试验证 |

---

## 七、示例演示

### 示例1: Tool类型

```
输入: "搜索今天天气"

识别结果:
- primary_type: "tool"
- confidence: 0.98
- reasoning: "用户只需要执行'搜索'这个单一操作"

处理: 直接调用 web_search tool
```

### 示例2: Skill类型

```
输入: "帮我分析一下这段代码有什么问题"

识别结果:
- primary_type: "skill"  
- confidence: 0.92
- reasoning: "用户需要'代码分析'这个复合技能"

处理: 
1. 检查 code_analysis skill 是否存在
2. 如不存在，自动创建
3. 执行skill
```

### 示例3: Agent类型

```
输入: "当我技术顾问，帮我解答技术问题"

识别结果:
- primary_type: "agent"
- confidence: 0.89
- reasoning: "用户需要一个能自主推理的技术顾问角色"

处理:
1. 检查 technical_consultant agent 是否存在
2. 如不存在，自动创建
3. 激活agent
```

### 示例4: Team类型

```
输入: "帮我建立一个软件研发团队，能够完成客户的需求并完成交付"

识别结果:
- primary_type: "team"
- confidence: 0.95
- reasoning: "用户需要PM+开发+QA+架构师等多个角色协作"

处理:
1. 解析团队需求
2. 检查/创建缺失的Skills
3. 创建多个Agent
4. 定义协作流程
5. 激活团队
```

---

## 八、下一步

1. **确认方案** - 能力类型识别作为第一优先级是否符合预期？
2. **开始实施** - 从 `capability_type_detector.py` 开始
3. **持续迭代**

---

*方案版本: v2.1*
*更新时间: 2026-03-15*
