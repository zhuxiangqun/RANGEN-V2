#!/usr/bin/env python3
"""
需求解析器 (Requirement Parser)
==============================

功能:
- 根据识别的能力类型，解析具体需求内容
- 为 Team: 提取角色、流程、所需Skills
- 为 Agent: 提取Agent用途、所需Skills
- 为 Skill: 提取Skill类型、所需Tools
- 为 Tool: 提取Tool名称

使用方式:
    from src.core.nlu_bridge.requirement_parser import RequirementParser
    
    parser = RequirementParser()
    result = await parser.parse("帮我建立一个软件研发团队", capability_type="team")
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from src.core.nlu_bridge.capability_type_detector import CapabilityType

logger = logging.getLogger(__name__)


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    # 基础信息
    original_input: str = ""
    capability_type: CapabilityType = CapabilityType.UNKNOWN
    
    # Team相关
    roles: List[str] = field(default_factory=list)
    workflow: List[str] = field(default_factory=list)
    team_name: str = ""
    
    # Agent相关
    agent_name: str = ""
    agent_purpose: str = ""
    
    # Skill相关
    skill_name: str = ""
    skill_description: str = ""
    
    # Tool相关
    tool_name: str = ""
    
    # 通用
    required_skills: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    complexity: str = "medium"


class RequirementParser:
    """
    需求解析器
    
    根据能力类型，解析具体需求内容
    """
    
    # Team角色模板
    ROLE_TEMPLATES = {
        "product_manager": {
            "name": "product_manager",
            "display_name": "产品经理",
            "skills": ["requirement_analysis", "priority_ranking", "user_story"],
            "tools": ["search", "file_manager"]
        },
        "architect": {
            "name": "architect", 
            "display_name": "系统架构师",
            "skills": ["technical_design", "architecture_review"],
            "tools": ["search", "file_manager"]
        },
        "developer": {
            "name": "developer",
            "display_name": "开发者",
            "skills": ["code_generation", "code_review", "refactoring"],
            "tools": ["code_executor", "file_manager", "search"]
        },
        "qa": {
            "name": "qa",
            "display_name": "测试工程师",
            "skills": ["test_generation", "test_execution", "bug_reporting"],
            "tools": ["code_executor", "file_manager"]
        },
        "devops": {
            "name": "devops",
            "display_name": "运维工程师",
            "skills": ["deployment", "ci_cd", "monitoring"],
            "tools": ["code_executor", "file_manager"]
        },
        "tech_writer": {
            "name": "tech_writer",
            "display_name": "技术文档工程师",
            "skills": ["api_documentation", "user_manual"],
            "tools": ["file_manager", "search"]
        }
    }
    
    # 工作流模板
    WORKFLOW_TEMPLATES = {
        "simple": ["开发", "测试"],
        "standard": ["需求分析", "开发", "测试", "交付"],
        "complete": ["需求分析", "技术设计", "开发", "测试", "文档", "交付"]
    }
    
    def __init__(self):
        self._llm_client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        if self._initialized:
            return
        
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            from src.core.llm_integration import LLMIntegration
            
            provider = os.getenv('LLM_PROVIDER', 'deepseek')
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
            base_url = os.getenv('DEEPSEEK_BASE_URL') or os.getenv('OPENAI_BASE_URL')
            model = os.getenv('DEEPSEEK_MODEL') or os.getenv('OPENAI_MODEL')
            
            if not api_key:
                self._initialized = True
                return
            
            llm_config = {
                "provider": provider,
                "model": model or "deepseek-chat",
                "api_key": api_key,
                "base_url": base_url,
            }
            self._llm_client = LLMIntegration(llm_config)
            self._initialized = True
            
        except Exception as e:
            logger.warning(f"LLM client init failed: {e}")
            self._initialized = True
    
    async def parse(self, user_input: str, capability_type: CapabilityType = None) -> RequirementAnalysis:
        """
        解析需求
        
        Args:
            user_input: 用户输入
            capability_type: 能力类型（可选，如果知道的话）
            
        Returns:
            RequirementAnalysis: 解析结果
        """
        self._ensure_initialized()
        
        # 如果没有指定类型，尝试使用LLM解析
        if capability_type is None and self._llm_client:
            try:
                from src.core.nlu_bridge.capability_type_detector import CapabilityTypeDetector
                detector = CapabilityTypeDetector()
                type_result = await detector.detect(user_input)
                capability_type = type_result.primary_type
            except:
                capability_type = CapabilityType.AGENT
        
        if capability_type is None:
            capability_type = CapabilityType.AGENT
        
        # 根据类型解析
        if capability_type == CapabilityType.TEAM:
            return await self._parse_team(user_input)
        elif capability_type == CapabilityType.AGENT:
            return await self._parse_agent(user_input)
        elif capability_type == CapabilityType.SKILL:
            return await self._parse_skill(user_input)
        elif capability_type == CapabilityType.TOOL:
            return await self._parse_tool(user_input)
        else:
            return await self._parse_general(user_input)
    
    async def _parse_team(self, user_input: str) -> RequirementAnalysis:
        """解析团队需求"""
        
        # 优先使用LLM
        if self._llm_client:
            try:
                prompt = self._build_team_prompt(user_input)
                response = self._llm_client.generate_response(prompt)
                return self._parse_team_response(user_input, response)
            except Exception as e:
                logger.warning(f"LLM team parsing failed: {e}")
        
        # 降级到规则匹配
        return self._parse_team_rules(user_input)
    
    def _build_team_prompt(self, user_input: str) -> str:
        return f"""分析以下团队需求，提取所需角色和工作流程。

用户需求: {user_input}

请以JSON格式输出:
{{
    "team_name": "团队名称",
    "roles": ["product_manager", "architect", "developer", "qa", "devops", "tech_writer"],
    "workflow": ["需求分析", "技术设计", "开发", "测试", "文档", "交付"],
    "required_skills": ["需要的技能列表"],
    "complexity": "low/medium/high"
}}

只输出JSON。"""
    
    def _parse_team_response(self, user_input: str, response: str) -> RequirementAnalysis:
        try:
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group(0))
                
                return RequirementAnalysis(
                    original_input=user_input,
                    capability_type=CapabilityType.TEAM,
                    team_name=data.get("team_name", "软件研发团队"),
                    roles=data.get("roles", ["developer"]),
                    workflow=data.get("workflow", ["需求分析", "开发", "测试"]),
                    required_skills=data.get("required_skills", []),
                    complexity=data.get("complexity", "medium")
                )
        except Exception as e:
            logger.warning(f"Failed to parse team response: {e}")
        
        return self._parse_team_rules(user_input)
    
    def _parse_team_rules(self, user_input: str) -> RequirementAnalysis:
        """规则匹配解析团队需求"""
        text = user_input.lower()
        
        # 检测角色
        roles = []
        
        # 中文关键词映射
        role_keywords = {
            "product_manager": ["产品经理", "需求", "PM", "项目管理"],
            "architect": ["架构师", "技术设计", "架构"],
            "developer": ["开发", "程序", "工程师", "代码"],
            "qa": ["测试", "QA", "质检"],
            "devops": ["运维", "部署", "DevOps"],
            "tech_writer": ["文档", "技术文档", "手册"]
        }
        
        for role, keywords in role_keywords.items():
            if any(kw in text for kw in keywords):
                roles.append(role)
        
        # 默认角色
        if not roles:
            roles = ["developer", "qa"]
        
        # 检测工作流
        workflow = []
        workflow_keywords = {
            "需求分析": ["需求", "分析"],
            "技术设计": ["设计", "架构", "技术方案"],
            "开发": ["开发", "代码", "写代码"],
            "测试": ["测试", "验证"],
            "文档": ["文档", "手册"],
            "交付": ["交付", "上线", "发布"]
        }
        
        for step, keywords in workflow_keywords.items():
            if any(kw in text for kw in keywords):
                workflow.append(step)
        
        # 默认工作流
        if not workflow:
            workflow = ["需求分析", "开发", "测试"]
        
        # 检测团队名称
        team_name = "软件研发团队"
        if "软件" in text:
            team_name = "软件研发团队"
        elif "数据" in text:
            team_name = "数据团队"
        elif "营销" in text:
            team_name = "营销团队"
        
        return RequirementAnalysis(
            original_input=user_input,
            capability_type=CapabilityType.TEAM,
            team_name=team_name,
            roles=roles,
            workflow=workflow,
            required_skills=self._get_role_skills(roles),
            complexity="high" if len(roles) > 2 else "medium"
        )
    
    def _get_role_skills(self, roles: List[str]) -> List[str]:
        """获取角色所需的Skills"""
        skills = set()
        for role in roles:
            if role in self.ROLE_TEMPLATES:
                skills.update(self.ROLE_TEMPLATES[role].get("skills", []))
        return list(skills)
    
    async def _parse_agent(self, user_input: str) -> RequirementAnalysis:
        """解析Agent需求"""
        
        if self._llm_client:
            try:
                prompt = self._build_agent_prompt(user_input)
                response = self._llm_client.generate_response(prompt)
                return self._parse_agent_response(user_input, response)
            except Exception as e:
                logger.warning(f"LLM agent parsing failed: {e}")
        
        return self._parse_agent_rules(user_input)
    
    def _build_agent_prompt(self, user_input: str) -> str:
        return f"""分析以下Agent需求，提取Agent信息。

用户需求: {user_input}

请以JSON格式输出:
{{
    "agent_name": "Agent名称(英文)",
    "agent_purpose": "Agent用途描述",
    "required_skills": ["需要的技能"],
    "complexity": "low/medium/high"
}}

只输出JSON。"""
    
    def _parse_agent_response(self, user_input: str, response: str) -> RequirementAnalysis:
        try:
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group(0))
                
                return RequirementAnalysis(
                    original_input=user_input,
                    capability_type=CapabilityType.AGENT,
                    agent_name=data.get("agent_name", "assistant"),
                    agent_purpose=data.get("agent_purpose", user_input),
                    required_skills=data.get("required_skills", []),
                    complexity=data.get("complexity", "medium")
                )
        except:
            pass
        
        return self._parse_agent_rules(user_input)
    
    def _parse_agent_rules(self, user_input: str) -> RequirementAnalysis:
        """规则匹配解析Agent需求"""
        
        # 尝试从输入中提取Agent名称
        agent_name = "assistant"
        if "顾问" in user_input:
            agent_name = "consultant"
        elif "助手" in user_input:
            agent_name = "assistant"
        elif "写" in user_input and "代码" in user_input:
            agent_name = "coder"
        
        return RequirementAnalysis(
            original_input=user_input,
            capability_type=CapabilityType.AGENT,
            agent_name=agent_name,
            agent_purpose=user_input,
            required_skills=["general_assist"],
            complexity="medium"
        )
    
    async def _parse_skill(self, user_input: str) -> RequirementAnalysis:
        """解析Skill需求"""
        
        # 检测需要的Skill类型
        skill_name = "general_skill"
        required_tools = []
        
        text = user_input.lower()
        
        if "分析" in text:
            skill_name = "code_analysis"
            required_tools = ["code_executor", "file_manager"]
        elif "测试" in text:
            skill_name = "testing"
            required_tools = ["code_executor"]
        elif "检索" in text or "搜索" in text:
            skill_name = "retrieval"
            required_tools = ["search", "rag"]
        elif "审查" in text:
            skill_name = "code_review"
            required_tools = ["code_executor", "file_manager"]
        
        return RequirementAnalysis(
            original_input=user_input,
            capability_type=CapabilityType.SKILL,
            skill_name=skill_name,
            skill_description=user_input,
            required_tools=required_tools,
            complexity="low"
        )
    
    async def _parse_tool(self, user_input: str) -> RequirementAnalysis:
        """解析Tool需求"""
        
        tool_name = "unknown"
        text = user_input.lower()
        
        tool_keywords = {
            "web_search": ["搜索", "天气", "查"],
            "calculator": ["计算", "等于", "加", "减"],
            "file_reader": ["读", "查看", "打开"],
            "code_executor": ["执行", "运行", "跑"]
        }
        
        for tool, keywords in tool_keywords.items():
            if any(kw in text for kw in keywords):
                tool_name = tool
                break
        
        return RequirementAnalysis(
            original_input=user_input,
            capability_type=CapabilityType.TOOL,
            tool_name=tool_name,
            complexity="low"
        )
    
    async def _parse_general(self, user_input: str) -> RequirementAnalysis:
        """通用解析"""
        return RequirementAnalysis(
            original_input=user_input,
            capability_type=CapabilityType.AGENT,
            agent_name="assistant",
            agent_purpose=user_input,
            complexity="medium"
        )


async def parse_requirement(user_input: str, capability_type: CapabilityType = None) -> RequirementAnalysis:
    """便捷函数: 解析需求"""
    parser = RequirementParser()
    return await parser.parse(user_input, capability_type)
