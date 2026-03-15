#!/usr/bin/env python3
"""
能力类型识别器 (Capability Type Detector)
==========================================

这是整个需求理解流程的【第一优先级】！

功能:
- 识别用户需求需要什么层次的能力: Tool / Skill / Agent / Team
- 使用LLM进行语义理解（复用AISkillTrigger的能力）
- 不依赖硬编码关键词

使用方式:
    from src.core.nlu_bridge.capability_type_detector import CapabilityTypeDetector
    
    detector = CapabilityTypeDetector()
    result = await detector.detect("帮我建立一个软件研发团队")
    print(result.primary_type)  # -> CapabilityType.TEAM
"""

import os
import json
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


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
    primary_type: CapabilityType = CapabilityType.UNKNOWN
    confidence: float = 0.0
    reasoning: str = ""
    suggested_actions: List[str] = field(default_factory=list)
    secondary_types: List[CapabilityType] = field(default_factory=list)


class CapabilityTypeDetector:
    """
    能力类型识别器
    
    使用LLM分析用户输入，判断需要什么层次的能力。
    复用AISkillTrigger的LLM理解能力。
    
    与传统关键词匹配的区别:
    - 传统: 用户输入包含"团队"→触发Team
    - AI: LLM理解语义→自主判断需要Team
    """
    
    # 能力类型描述 (用于LLM理解)
    TYPE_DESCRIPTIONS = {
        CapabilityType.TOOL: """
TOOL (工具层): 用户只需要完成一个单一的操作动作
- 特征: 搜索、计算、查询、执行一个具体命令
- 示例: "搜索今天天气"、"1+1等于多少"、"打开文件"、"告诉我时间"
- 关键词: 搜索、计算、查询、打开、执行、告诉、看看
""",
        CapabilityType.SKILL: """
SKILL (技能层): 用户需要完成一个完整的能力任务
- 特征: 需要多个工具组合才能完成的任务
- 示例: "查一下RAG的原理"、"分析这段代码"、"帮我测试这个函数"
- 关键词: 分析、测试、检索、查询知识、解释、查看原理
""",
        CapabilityType.AGENT: """
AGENT (智能体层): 用户需要一个能自主推理的助手
- 特征: 需要AI进行思考、推理、决策的任务
- 示例: "当我技术顾问"、"帮我写一个排序算法"、"帮我规划项目"
- 关键词: 顾问、帮助、帮我(做)、规划、设计、建议
""",
        CapabilityType.TEAM: """
TEAM (团队层): 用户需要多个角色协作完成复杂任务
- 特征: 需要建立团队、多角色协作、完整流程
- 示例: "建立研发团队"、"做完整项目"、"创建协作流程"
- 关键词: 团队、协作、建立(团队/流程)、多角色、完整项目
"""
    }
    
    def __init__(self):
        self._llm_client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保初始化"""
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
                logger.warning("No API key found, type detection will use fallback")
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
            logger.warning(f"LLM client init failed, using fallback: {e}")
            self._initialized = True
    
    async def detect(self, user_input: str) -> TypeDetectionResult:
        """
        识别用户需求需要的能力类型
        
        这是整个流程的【第一步】！
        
        Args:
            user_input: 用户输入的自然语言
            
        Returns:
            TypeDetectionResult: 识别结果
        """
        self._ensure_initialized()
        
        # 优先尝试LLM识别
        if self._llm_client:
            try:
                return await self._detect_with_llm(user_input)
            except Exception as e:
                logger.warning(f"LLM detection failed, using fallback: {e}")
        
        # 降级使用规则匹配
        return self._detect_with_rules(user_input)
    
    async def _detect_with_llm(self, user_input: str) -> TypeDetectionResult:
        """使用LLM进行类型识别"""
        
        # 构建识别提示词
        prompt = self._build_detection_prompt(user_input)
        
        # 调用LLM (同步方法)
        response = self._llm_client.generate_response(prompt)
        
        # 解析结果
        result = self._parse_llm_response(response, user_input)
        
        logger.info(f"Type detection for '{user_input}': {result.primary_type.value} (confidence: {result.confidence})")
        
        return result
    
    def _build_detection_prompt(self, user_input: str) -> str:
        """构建类型识别提示词"""
        return f"""你是一个能力类型识别器。请分析用户输入，判断用户需要什么层次的能力。

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

只输出JSON，不要其他内容。"""
    
    def _parse_llm_response(self, response: str, user_input: str) -> TypeDetectionResult:
        """解析LLM响应"""
        try:
            # 提取JSON
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            # 映射类型
            type_map = {
                "tool": CapabilityType.TOOL,
                "skill": CapabilityType.SKILL,
                "agent": CapabilityType.AGENT,
                "team": CapabilityType.TEAM,
            }
            
            primary_type = type_map.get(
                data.get("primary_type", "").lower(),
                CapabilityType.UNKNOWN
            )
            
            # 映射次要类型
            secondary = []
            for t in data.get("secondary_types", []):
                if t.lower() in type_map:
                    secondary.append(type_map[t.lower()])
            
            return TypeDetectionResult(
                primary_type=primary_type,
                confidence=float(data.get("confidence", 0.0)),
                reasoning=data.get("reasoning", ""),
                suggested_actions=data.get("suggested_actions", []),
                secondary_types=secondary
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            # 降级到规则匹配
            return self._detect_with_rules(user_input)
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 尝试找到JSON块
        import re
        
        # 尝试 ```json ... ```
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if match:
            return match.group(1)
        
        # 尝试 { ... }
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group(0)
        
        return text
    
    def _detect_with_rules(self, user_input: str) -> TypeDetectionResult:
        """
        降级方案: 使用规则匹配
        
        虽然不如LLM准确，但在没有API Key时可以工作
        """
        text = user_input.lower()
        
        # Team 关键词 (最高优先级)
        team_keywords = ["团队", "协作", "建立团队", "多角色", "完整项目", 
                       "研发团队", "项目团队", "创建团队"]
        if any(kw in text for kw in team_keywords):
            return TypeDetectionResult(
                primary_type=CapabilityType.TEAM,
                confidence=0.85,
                reasoning="检测到团队相关关键词",
                suggested_actions=["解析团队需求", "创建所需角色", "定义协作流程"]
            )
        
        # Agent 关键词
        agent_keywords = ["顾问", "助手", "帮我做", "帮我写", "帮我规划",
                         "当我的", "技术顾问", "编程助手"]
        if any(kw in text for kw in agent_keywords):
            return TypeDetectionResult(
                primary_type=CapabilityType.AGENT,
                confidence=0.80,
                reasoning="检测到助手/顾问相关关键词",
                suggested_actions=["创建Agent", "激活任务执行"]
            )
        
        # Skill 关键词
        skill_keywords = ["分析", "测试", "检索", "查询", "解释", "原理",
                        "检查", "审查", "优化"]
        if any(kw in text for kw in skill_keywords):
            return TypeDetectionResult(
                primary_type=CapabilityType.SKILL,
                confidence=0.75,
                reasoning="检测到技能任务相关关键词",
                suggested_actions=["匹配Skill", "执行任务"]
            )
        
        # Tool 关键词 (最低优先级)
        tool_keywords = ["搜索", "计算", "查询", "打开", "执行", "告诉",
                        "看看", "时间", "天气", "等于"]
        if any(kw in text for kw in tool_keywords):
            return TypeDetectionResult(
                primary_type=CapabilityType.TOOL,
                confidence=0.70,
                reasoning="检测到单一操作相关关键词",
                suggested_actions=["调用Tool", "执行操作"]
            )
        
        # 默认: 假设是Agent (最常见的情况)
        return TypeDetectionResult(
            primary_type=CapabilityType.AGENT,
            confidence=0.50,
            reasoning="无法明确识别，使用默认Agent类型",
            suggested_actions=["创建Agent", "执行任务"]
        )


# ============================================================
# 便捷函数
# ============================================================

async def detect_capability_type(user_input: str) -> TypeDetectionResult:
    """
    便捷函数: 快速识别能力类型
    
    Example:
        result = await detect_capability_type("帮我建立一个研发团队")
        print(result.primary_type)  # -> CapabilityType.TEAM
    """
    detector = CapabilityTypeDetector()
    return await detector.detect(user_input)


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        detector = CapabilityTypeDetector()
        
        test_cases = [
            "搜索今天天气",
            "查一下RAG的原理",
            "当我技术顾问",
            "帮我建立一个软件研发团队",
            "1+1等于多少",
            "帮我写一个排序算法",
            "分析这段代码有什么问题",
            "做一个完整项目"
        ]
        
        print("=" * 60)
        print("能力类型识别测试")
        print("=" * 60)
        
        for query in test_cases:
            result = await detector.detect(query)
            print(f"\n输入: {query}")
            print(f"类型: {result.primary_type.value} (置信度: {result.confidence})")
            print(f"理由: {result.reasoning}")
    
    asyncio.run(test())
