#!/usr/bin/env python3
"""
统一Agent+Skill决策模块

一次LLM调用同时返回Agent和Skill选择，利用LangGraph的条件路由能力。

流程：
    用户输入 → single_agent_skill_decision_node → 条件路由 → 对应Workflow
"""
import os
import yaml
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Pydantic for structured output
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class AgentInfoSchema(BaseModel):
    """Agent信息Schema - 用于LLM理解"""
    name: str = Field(description="Agent名称，如 assistant-agent, research-agent, creative-agent")
    description: str = Field(description="Agent能力描述")
    capabilities: List[str] = Field(description="Agent擅长的工作类型")


class SkillInfoSchema(BaseModel):
    """Skill信息Schema - 用于LLM理解"""
    name: str = Field(description="Skill名称，如 calculator-skill, web-search, rag-retrieval")
    description: str = Field(description="Skill功能描述")
    triggers: List[str] = Field(description="触发该Skill的关键词或模式")


class AgentSkillDecision(BaseModel):
    """Agent+Skill决策结果 - LLM structured output"""
    selected_agent: str = Field(description="选择的Agent名称")
    selected_skills: List[str] = Field(description="选择的Skills列表")
    reasoning: str = Field(description="选择理由")
    confidence: float = Field(description="置信度 0-1", ge=0.0, le=1.0)


# ==================== Agent/Skill定义加载 ====================

def load_agents_from_selector() -> List[AgentInfoSchema]:
    """从AgentSelector加载Agent定义"""
    try:
        from src.agents.agent_selector import AgentSelector
        
        selector = AgentSelector()
        agents = selector._load_agents()
        
        return [
            AgentInfoSchema(
                name=a.name,
                description=a.description,
                capabilities=a.capabilities
            )
            for a in agents
        ]
    except Exception as e:
        logger.warning(f"从AgentSelector加载失败: {e}")
        # 返回默认定义
        return get_default_agents()


def load_skills_from_trigger() -> List[SkillInfoSchema]:
    """从AISkillTrigger加载Skill定义"""
    try:
        from src.agents.skills.ai_skill_trigger import AISkillTrigger
        
        trigger = AISkillTrigger()
        skills = trigger._load_skills()
        
        return [
            SkillInfoSchema(
                name=s.get("name", ""),
                description=s.get("description", ""),
                triggers=s.get("triggers", [])
            )
            for s in skills
        ]
    except Exception as e:
        logger.warning(f"从AISkillTrigger加载失败: {e}")
        return get_default_skills()


def get_default_agents() -> List[AgentInfoSchema]:
    """默认Agent定义"""
    return [
        AgentInfoSchema(
            name="assistant-agent",
            description="通用助手，处理日常问答、计算、文件读取等基本任务",
            capabilities=["问答", "计算", "文件处理", "搜索"]
        ),
        AgentInfoSchema(
            name="creative-agent",
            description="创意写作助手，擅长写诗、写文章、内容创作",
            capabilities=["写作", "创作", "总结"]
        ),
        AgentInfoSchema(
            name="research-agent",
            description="研究助手，擅长信息检索、文献分析、知识查询",
            capabilities=["搜索", "分析", "知识图谱", "RAG"]
        ),
        AgentInfoSchema(
            name="analysis-agent",
            description="分析助手，擅长数据分析、机器学习预测",
            capabilities=["数据分析", "机器学习", "预测"]
        ),
        AgentInfoSchema(
            name="developer-agent",
            description="开发助手，擅长代码生成、调试、技术问题解答",
            capabilities=["代码", "调试", "技术文档"]
        ),
        AgentInfoSchema(
            name="browser-agent",
            description="浏览器自动化助手，擅长网页操作、自动化测试",
            capabilities=["浏览器自动化", "网页操作"]
        ),
        AgentInfoSchema(
            name="multimodal-agent",
            description="多模态处理助手，擅长图像识别、视频分析、OCR",
            capabilities=["图像识别", "视频分析", "OCR"]
        ),
    ]


def get_default_skills() -> List[SkillInfoSchema]:
    """默认Skill定义"""
    return [
        SkillInfoSchema(
            name="calculator-skill",
            description="数学计算能力",
            triggers=["计算", "加", "减", "乘", "除", "等于"]
        ),
        SkillInfoSchema(
            name="file-read-skill",
            description="文件读取能力",
            triggers=["读取", "查看", "打开文件"]
        ),
        SkillInfoSchema(
            name="web-search",
            description="网络搜索能力",
            triggers=["搜索", "查找", "最新", "新闻"]
        ),
        SkillInfoSchema(
            name="rag-retrieval",
            description="知识库检索能力",
            triggers=["知识", "文档", "资料"]
        ),
        SkillInfoSchema(
            name="answer-generation",
            description="答案生成能力",
            triggers=["回答", "回答问题"]
        ),
        SkillInfoSchema(
            name="summarization",
            description="总结归纳能力",
            triggers=["总结", "概括", "摘要"]
        ),
        SkillInfoSchema(
            name="browser-skill",
            description="浏览器自动化能力",
            triggers=["浏览器", "网页", "点击"]
        ),
        SkillInfoSchema(
            name="multimodal-skill",
            description="多模态处理能力",
            triggers=["图片", "图像", "视频", "OCR"]
        ),
    ]


# ==================== Prompt模板 ====================

DECISION_PROMPT_TEMPLATE = """你是一个智能任务路由器。根据用户输入，从以下Agent和Skill中选择最合适的组合。

## 可用Agents:
{agents_schema}

## 可用Skills:
{skills_schema}

## 用户输入:
{user_query}

## 要求:
1. 选择最合适的Agent（只能选一个）
2. 选择需要使用的Skills（可以多个，按优先级排序）
3. 给出选择理由和置信度

请以JSON格式返回决策结果:
{{
    "selected_agent": "agent名称",
    "selected_skills": ["skill1", "skill2"],
    "reasoning": "选择理由",
    "confidence": 0.95
}}
"""


def build_decision_prompt(user_query: str) -> str:
    """构建决策Prompt"""
    agents = load_agents_from_selector()
    skills = load_skills_from_trigger()
    
    agents_json = json.dumps([a.model_dump() for a in agents], ensure_ascii=False, indent=2)
    skills_json = json.dumps([s.model_dump() for s in skills], ensure_ascii=False, indent=2)
    
    return DECISION_PROMPT_TEMPLATE.format(
        agents_schema=agents_json,
        skills_schema=skills_json,
        user_query=user_query
    )


# ==================== LLM调用 ====================

async def get_llm_decision(user_query: str, timeout: float = 30.0) -> Optional[AgentSkillDecision]:
    """
    获取LLM的Agent+Skill决策
    
    Args:
        user_query: 用户输入
        timeout: 超时时间（秒）
    
    Returns:
        AgentSkillDecision或None
    """
    try:
        from src.core.llm_integration import LLMIntegration
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('DEEPSEEK_BASE_URL') or os.getenv('OPENAI_BASE_URL')
        model = os.getenv('DEEPSEEK_MODEL') or os.getenv('OPENAI_MODEL')
        
        if not api_key:
            logger.warning("No API key found")
            return None
        
        llm_config = {
            "provider": "deepseek",
            "model": model or "deepseek-reasoner",
            "api_key": api_key,
            "base_url": base_url,
        }
        
        llm = LLMIntegration(llm_config)
        
        # 使用structured output
        prompt = build_decision_prompt(user_query)
        
        # 调用LLM
        import asyncio
        try:
            response = await asyncio.wait_for(
                llm.agenerate([prompt]),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"LLM调用超时: {timeout}秒")
            return None
        
        if not response or not response.generations:
            return None
        
        text = response.generations[0][0].text
        
        # 解析JSON
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return AgentSkillDecision(**data)
        
        return None
        
    except Exception as e:
        logger.error(f"LLM决策失败: {e}")
        return None


async def get_llm_decision_with_fallback(user_query: str) -> AgentSkillDecision:
    """
    获取LLM决策，带fallback
    
    如果LLM调用失败，使用关键词匹配作为fallback
    """
    # 尝试LLM决策
    decision = await get_llm_decision(user_query)
    
    if decision:
        return decision
    
    # Fallback: 关键词匹配
    logger.info("使用fallback关键词匹配")
    return fallback_decision(user_query)


def fallback_decision(user_query: str) -> AgentSkillDecision:
    """基于关键词的fallback决策"""
    query_lower = user_query.lower()
    
    # 关键词到Agent的映射
    agent_keywords = {
        "research-agent": ["搜索", "查找", "研究", "分析", "知识", "文献"],
        "creative-agent": ["写", "创作", "诗", "文章", "故事", "创意"],
        "analysis-agent": ["分析", "预测", "数据", "统计", "机器学习"],
        "developer-agent": ["代码", "编程", "开发", "调试", "技术"],
        "browser-agent": ["浏览器", "网页", "点击", "自动化"],
        "multimodal-agent": ["图片", "图像", "视频", "OCR", "识别"],
        "assistant-agent": ["计算", "问答", "帮助"],
    }
    
    # 关键词到Skill的映射
    skill_keywords = {
        "calculator-skill": ["计算", "加", "减", "乘", "除", "等于", "结果"],
        "file-read-skill": ["读取", "查看", "打开文件", "文件内容"],
        "web-search": ["搜索", "查找", "最新", "新闻", "网上"],
        "rag-retrieval": ["知识", "文档", "资料", "知识库"],
        "answer-generation": ["回答", "回答问题"],
        "summarization": ["总结", "概括", "摘要"],
        "browser-skill": ["浏览器", "网页", "点击"],
        "multimodal-skill": ["图片", "图像", "视频", "OCR"],
    }
    
    # 匹配Agent
    best_agent = "assistant-agent"
    best_agent_score = 0
    
    for agent, keywords in agent_keywords.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > best_agent_score:
            best_agent_score = score
            best_agent = agent
    
    # 匹配Skills
    selected_skills = []
    for skill, keywords in skill_keywords.items():
        if any(kw in query_lower for kw in keywords):
            selected_skills.append(skill)
    
    if not selected_skills:
        selected_skills = ["calculator-skill"]  # 默认
    
    return AgentSkillDecision(
        selected_agent=best_agent,
        selected_skills=selected_skills,
        reasoning=f"Fallback: 关键词匹配 (agent: {best_agent}, skills: {selected_skills})",
        confidence=0.5
    )


# ==================== 条件路由 ====================

def get_workflow_name(agent_name: str) -> str:
    """根据Agent名称获取对应的workflow名称"""
    workflow_map = {
        "assistant-agent": "assistant_workflow",
        "creative-agent": "creative_workflow",
        "research-agent": "research_workflow",
        "analysis-agent": "analysis_workflow",
        "developer-agent": "developer_workflow",
        "browser-agent": "browser_workflow",
        "multimodal-agent": "multimodal_workflow",
    }
    return workflow_map.get(agent_name, "assistant_workflow")


def route_by_agent(state: Dict[str, Any]) -> str:
    """
    LangGraph条件路由函数
    
    根据state中的selected_agent选择下一个节点
    """
    agent = state.get("selected_agent", "assistant-agent")
    return get_workflow_name(agent)


# ==================== LangGraph Node ====================

def single_agent_skill_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一Agent+Skill决策节点
    
    一次LLM调用同时返回Agent和Skill选择，用于LangGraph工作流。
    
    Args:
        state: 工作流状态，必须包含 'query' 字段
    
    Returns:
        更新后的状态，包含 selected_agent, selected_skills, decision_reasoning
    """
    import asyncio
    
    query = state.get("query", "")
    if not query:
        logger.warning("No query in state, using fallback decision")
        decision = fallback_decision("")
    else:
        # 同步调用异步函数
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步环境中，创建新任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, get_llm_decision_with_fallback(query))
                    decision = future.result(timeout=30)
            else:
                decision = loop.run_until_complete(get_llm_decision_with_fallback(query))
        except RuntimeError:
            # 没有事件循环，直接创建新的
            decision = asyncio.run(get_llm_decision_with_fallback(query))
    
    # 更新状态
    state["selected_agent"] = decision.selected_agent
    state["selected_skills"] = decision.selected_skills
    state["decision_reasoning"] = decision.reasoning
    state["decision_confidence"] = decision.confidence
    
    # 同时更新 agent_states 中的信息（用于协作）
    if "agent_states" not in state:
        state["agent_states"] = {}
    state["agent_states"]["agent_skill_decision"] = {
        "agent": decision.selected_agent,
        "skills": decision.selected_skills,
        "confidence": decision.confidence,
        "reasoning": decision.reasoning
    }
    
    logger.info(f"Agent+Skill决策: {decision.selected_agent} + {decision.selected_skills}")
    
    return state


def create_agent_skill_decision_edge():
    """
    创建条件路由边
    
    Returns:
        条件路由函数，用于LangGraph的add_conditional_edges
    """
    def route_to_agent_workflow(state: Dict[str, Any]) -> str:
        """
        根据selected_agent路由到对应的工作流
        
        Returns:
            工作流节点名称
        """
        agent = state.get("selected_agent", "assistant-agent")
        return get_workflow_name(agent)
    
    return route_to_agent_workflow


# ==================== 测试 ====================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("测试: 统一Agent+Skill决策")
        print("=" * 60)
        
        test_cases = [
            "帮我计算100加200",
            "帮我写一首关于春天的诗",
            "搜索最新的AI新闻",
            "分析这个数据并预测趋势",
        ]
        
        for query in test_cases:
            print(f"\n用户输入: {query}")
            decision = await get_llm_decision_with_fallback(query)
            print(f"  Agent: {decision.selected_agent}")
            print(f"  Skills: {decision.selected_skills}")
            print(f"  原因: {decision.reasoning}")
            print(f"  置信度: {decision.confidence}")
            print(f"  路由到: {get_workflow_name(decision.selected_agent)}")
        
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
    
    asyncio.run(test())
