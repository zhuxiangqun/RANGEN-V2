#!/usr/bin/env python3
"""
AI Agent选择器

根据用户输入，使用LLM自动选择合适的Agent

流程：
    用户输入 → Agent选择 → Agent决定使用哪些Skill → Skill调用工具

使用方式：
    from src.agents.agent_selector import AgentSelector, select_agent
    
    # AI选择Agent
    agent = await select_agent("帮我写一首诗")
    # 可能返回: {"agent": "creative-agent", "skills": ["summarization"]}
"""

import os
import yaml
import glob
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class AgentInfo:
    """Agent信息"""
    name: str
    description: str
    skills: List[str]
    capabilities: List[str]


class AgentSelector:
    """
    AI Agent选择器
    
    根据用户输入，使用LLM选择合适的Agent
    """
    
    def __init__(self):
        self._agents_cache: Optional[List[AgentInfo]] = None
        self._llm_client = None
    
    def _get_llm_client(self):
        """获取LLM客户端"""
        if self._llm_client is None:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                from src.core.llm_integration import LLMIntegration
                
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
                self._llm_client = LLMIntegration(llm_config)
            except Exception as e:
                logger.warning(f"LLM client init failed: {e}")
                return None
        return self._llm_client
    
    def _load_agents(self) -> List[AgentInfo]:
        """从配置加载Agents"""
        if self._agents_cache is not None:
            return self._agents_cache
        
        agents = []
        
        # 定义内置Agent
        builtin_agents = [
            {
                "name": "assistant-agent",
                "description": "通用助手，处理日常问答、计算、文件读取等基本任务",
                "skills": ["calculator-skill", "file-read-skill", "web_search"],
                "capabilities": ["问答", "计算", "文件处理", "搜索"]
            },
            {
                "name": "creative-agent",
                "description": "创意写作助手，擅长写诗、写文章、内容创作",
                "skills": ["summarization", "answer-generation"],
                "capabilities": ["写作", "创作", "总结"]
            },
            {
                "name": "research-agent",
                "description": "研究助手，擅长信息检索、文献分析、知识查询",
                "skills": ["web_search", "rag-retrieval", "knowledge-graph", "fact-check"],
                "capabilities": ["搜索", "检索", "分析", "研究"]
            },
            {
                "name": "analysis-agent",
                "description": "分析助手，擅长数据分析、机器学习预测",
                "skills": ["calculator-skill", "ml-prediction-expert", "data-analysis-workflow"],
                "capabilities": ["数据分析", "机器学习", "预测"]
            },
            {
                "name": "developer-agent",
                "description": "开发助手，擅长代码生成、调试、技术问题解答",
                "skills": ["reasoning-chain", "web_search", "tool-execution"],
                "capabilities": ["编程", "调试", "技术问答"]
            },
            {
                "name": "browser-agent",
                "description": "浏览器自动化助手，擅长网页操作、自动化测试",
                "skills": ["browser-skill", "web_search"],
                "capabilities": ["浏览器自动化", "网页操作", "测试"]
            },
            {
                "name": "multimodal-agent",
                "description": "多模态处理助手，擅长图像识别、视频分析、OCR",
                "skills": ["multimodal-skill"],
                "capabilities": ["图像识别", "视频分析", "OCR"]
            }
        ]
        
        for agent_data in builtin_agents:
            agents.append(AgentInfo(
                name=agent_data["name"],
                description=agent_data["description"],
                skills=agent_data["skills"],
                capabilities=agent_data["capabilities"]
            ))
        
        self._agents_cache = agents
        logger.info(f"Loaded {len(agents)} agents")
        return agents
    
    def _build_prompt(self, user_input: str, agents: List[AgentInfo]) -> str:
        """构建选择Agent的prompt"""
        
        agents_desc = []
        for agent in agents:
            agents_desc.append(
                f"- {agent.name}: {agent.description}\n"
                f"  能力: {', '.join(agent.capabilities)}\n"
                f"  技能: {', '.join(agent.skills)}"
            )
        
        prompt = f"""你是一个Agent选择器。根据用户输入，从以下Agent中选择最合适的。

可用Agent：
{chr(10).join(agents_desc)}

用户输入: {user_input}

请分析用户意图，选择最合适的Agent。

返回格式（JSON）：
{{
    "selected_agent": "agent名称",
    "reasoning": "为什么选择这个Agent",
    "confidence": 0.9
}}

只返回JSON，不要有其他内容。"""
        return prompt
    
    async def select(self, user_input: str) -> Dict[str, Any]:
        """
        选择合适的Agent
        
        Args:
            user_input: 用户输入
            
        Returns:
            {agent: str, skills: List[str], reasoning: str}
        """
        # 加载Agents
        agents = self._load_agents()
        
        # 获取LLM
        llm = self._get_llm_client()
        if not llm:
            # Fallback: 简单关键词匹配
            return self._fallback_select(user_input, agents)
        
        # 构建prompt并调用LLM
        prompt = self._build_prompt(user_input, agents)
        
        try:
            response = llm.call_llm(prompt)
            content = response if isinstance(response, str) else str(response)
            
            # 解析响应
            result = self._parse_response(content)
            
            if result:
                # 获取Agent的skills
                agent_name = result.get("selected_agent", "")
                for agent in agents:
                    if agent.name == agent_name:
                        result["skills"] = agent.skills
                        return result
                
                return result
            else:
                return self._fallback_select(user_input, agents)
                
        except Exception as e:
            logger.error(f"Agent selection failed: {e}")
            return self._fallback_select(user_input, agents)
    
    def _parse_response(self, content: str) -> Optional[Dict]:
        """解析LLM响应"""
        import re
        try:
            import json
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                if 'selected_agent' in data:
                    return data
        except Exception as e:
            logger.warning(f"Failed to parse response: {e}")
        return None
    
    def _fallback_select(self, user_input: str, agents: List[AgentInfo]) -> Dict[str, Any]:
        """后备选择：关键词匹配"""
        user_input_lower = user_input.lower()
        
        # 关键词到Agent的映射
        keyword_map = {
            "写诗": "creative-agent",
            "写作": "creative-agent",
            "创作": "creative-agent",
            "搜索": "research-agent",
            "研究": "research-agent",
            "分析": "analysis-agent",
            "数据": "analysis-agent",
            "代码": "developer-agent",
            "编程": "developer-agent",
            "开发": "developer-agent",
            "浏览器": "browser-agent",
            "网页": "browser-agent",
            "图像": "multimodal-agent",
            "图片": "multimodal-agent",
            "识别": "multimodal-agent",
            "计算": "assistant-agent",
            "文件": "assistant-agent",
        }
        
        for keyword, agent_name in keyword_map.items():
            if keyword in user_input_lower:
                for agent in agents:
                    if agent.name == agent_name:
                        return {
                            "selected_agent": agent_name,
                            "reasoning": f"关键词匹配: {keyword}",
                            "confidence": 0.7,
                            "skills": agent.skills
                        }
        
        # 默认返回通用助手
        for agent in agents:
            if agent.name == "assistant-agent":
                return {
                    "selected_agent": "assistant-agent",
                    "reasoning": "默认选择",
                    "confidence": 0.5,
                    "skills": agent.skills
                }
        
        return {"selected_agent": "assistant-agent", "reasoning": "fallback"}


# 全局单例
_agent_selector: Optional[AgentSelector] = None


def get_agent_selector() -> AgentSelector:
    """获取Agent选择器单例"""
    global _agent_selector
    if _agent_selector is None:
        _agent_selector = AgentSelector()
    return _agent_selector


async def select_agent(user_input: str) -> Dict[str, Any]:
    """
    选择合适的Agent - 主入口函数
    
    Args:
        user_input: 用户输入
        
    Returns:
        {
            "selected_agent": "agent名称",
            "reasoning": "选择原因",
            "confidence": 0.9,
            "skills": ["skill1", "skill2"]
        }
    """
    selector = get_agent_selector()
    return await selector.select(user_input)


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("Agent选择器测试")
        print("=" * 60)
        
        test_cases = [
            "帮我计算100加200",
            "帮我写一首关于春天的诗",
            "搜索最新的AI新闻",
            "分析这个数据集",
            "帮我写段Python代码",
            "打开浏览器访问google",
            "识别这张图片里的内容",
        ]
        
        for test_input in test_cases:
            print(f"\n用户输入: {test_input}")
            result = await select_agent(test_input)
            print(f"选择的Agent: {result.get('selected_agent')}")
            print(f"使用的Skills: {result.get('skills', [])}")
            print(f"原因: {result.get('reasoning')}")
        
        print("\n" + "=" * 60)
    
    asyncio.run(test())
