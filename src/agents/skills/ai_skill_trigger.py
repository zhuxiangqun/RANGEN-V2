#!/usr/bin/env python3
"""
AI驱动的Skill触发器 - Claude Code风格

设计目标：
- 使用LLM理解用户输入，自主决定调用哪个skill
- 不依赖硬编码的关键词触发
- 读取SKILL.md理解skill能力，LLM决定最合适的skill

使用方式：
    from src.agents.skills.ai_skill_trigger import ai_auto_trigger_skills
    
    # AI自动触发skill
    skills = ai_auto_trigger_skills("帮我搜索最新的人工智能新闻")
    # 可能返回: ["web_search", "rag-retrieval"]
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class SkillInfo:
    """Skill信息"""
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    prompt_template: str = ""


class AISkillTrigger:
    """
    AI驱动的Skill触发器
    
    与传统关键词匹配的区别：
    - 传统：用户输入包含"搜索"→触发web_search
    - AI：LLM理解用户意图→自主决定最合适的skill
    
    优势：
    1. 更灵活 - 不依赖预定义关键词
    2. 更准确 - 理解语义而非字面匹配
    3. 可扩展 - 新skill无需添加触发词
    """
    
    def __init__(self):
        self._skills_cache: Optional[List[SkillInfo]] = None
        self._llm_client = None
    
    def _get_llm_client(self):
        """获取LLM客户端"""
        if self._llm_client is None:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                from src.core.llm_integration import LLMIntegration
                
                provider = os.getenv('LLM_PROVIDER', 'deepseek')
                api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
                base_url = os.getenv('DEEPSEEK_BASE_URL') or os.getenv('OPENAI_BASE_URL')
                model = os.getenv('DEEPSEEK_MODEL') or os.getenv('OPENAI_MODEL')
                
                if not api_key:
                    logger.warning("No API key found, falling back to keyword trigger")
                    return None
                
                llm_config = {
                    "provider": provider,
                    "model": model or "deepseek-reasoner",
                    "api_key": api_key,
                    "base_url": base_url,
                }
                self._llm_client = LLMIntegration(llm_config)
            except Exception as e:
                logger.warning(f"LLM client init failed: {e}")
                return None
        return self._llm_client
    
    def _load_skills_from_files(self) -> List[SkillInfo]:
        """从SKILL.md文件加载skills"""
        if self._skills_cache is not None:
            return self._skills_cache
        
        skills = []
        skill_dirs = [
            "src/agents/skills/bundled",
        ]
        
        import glob
        import yaml
        
        for skill_dir in skill_dirs:
            # 查找所有skill.yaml文件
            pattern = os.path.join(skill_dir, "*/skill.yaml")
            for yaml_file in glob.glob(pattern):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f) or {}
                    
                    skill_info = SkillInfo(
                        name=data.get('name', ''),
                        description=data.get('description', ''),
                        tags=data.get('tags', []),
                        prompt_template=data.get('prompt_template', '')
                    )
                    
                    if skill_info.name:
                        skills.append(skill_info)
                        logger.debug(f"Loaded skill: {skill_info.name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to load skill from {yaml_file}: {e}")
        
        self._skills_cache = skills
        logger.info(f"Loaded {len(skills)} skills from files")
        return skills
    
    def _build_trigger_prompt(self, user_input: str, skills: List[SkillInfo]) -> str:
        """构建触发决策的prompt"""
        
        skills_desc = []
        for s in skills:
            caps = s.capabilities if s.capabilities else [s.description]
            skills_desc.append(f"- {s.name}: {', '.join(caps[:3])}")
        
        skills_text = "\n".join(skills_desc)
        
        prompt = f"""你是一个智能助手选择器。根据用户输入，从以下可用技能中选择最合适的。

可用技能：
{skills_text}

用户输入: {user_input}

请分析用户意图，选择最合适的技能。你需要：
1. 理解用户真正想要什么
2. 选择最能满足用户需求的技能
3. 如果不确定，返回"通用助手"

返回格式（JSON）：
{{
    "selected_skills": ["skill1", "skill2"],
    "reasoning": "为什么选择这些技能",
    "confidence": 0.9
}}

只返回JSON，不要有其他内容。"""
        return prompt
    
    async def trigger(self, user_input: str) -> List[str]:
        """
        AI触发skill
        
        Args:
            user_input: 用户输入
            
        Returns:
            触发的skill名称列表
        """
        # 1. 加载skills
        skills = self._load_skills_from_files()
        if not skills:
            logger.warning("No skills loaded, returning empty list")
            return []
        
        # 2. 获取LLM客户端
        llm = self._get_llm_client()
        if not llm:
            logger.warning("LLM not available, falling back")
            return self._fallback_trigger(user_input, skills)
        
        # 3. 构建prompt并调用LLM
        prompt = self._build_trigger_prompt(user_input, skills)
        
        try:
            response = llm.call_llm(prompt)
            content = response if isinstance(response, str) else str(response)
            
            # 4. 解析响应
            result = self._parse_llm_response(content)
            
            if result:
                logger.info(f"AI triggered skills: {result['selected_skills']}")
                return result['selected_skills']
            else:
                return self._fallback_trigger(user_input, skills)
                
        except Exception as e:
            logger.error(f"AI trigger failed: {e}")
            return self._fallback_trigger(user_input, skills)
    
    def _parse_llm_response(self, content: str) -> Optional[Dict]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                if 'selected_skills' in data:
                    return data
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        return None
    
    def _fallback_trigger(self, user_input: str, skills: List[SkillInfo]) -> List[str]:
        """后备触发：使用关键词匹配"""
        user_input_lower = user_input.lower()
        
        # 简单关键词匹配
        matched = []
        for skill in skills:
            skill_name_lower = skill.name.lower()
            
            # 检查名称是否在输入中
            if skill_name_lower.replace('-', ' ') in user_input_lower:
                matched.append(skill.name)
            
            # 检查标签
            for tag in skill.tags:
                if tag.lower() in user_input_lower:
                    matched.append(skill.name)
                    break
        
        if matched:
            return matched[:3]  # 最多返回3个
        
        # 默认返回通用助手
        return ["通用助手"]


# 全局单例
_ai_skill_trigger: Optional[AISkillTrigger] = None


def get_ai_skill_trigger() -> AISkillTrigger:
    """获取AI skill触发器单例"""
    global _ai_skill_trigger
    if _ai_skill_trigger is None:
        _ai_skill_trigger = AISkillTrigger()
    return _ai_skill_trigger


async def ai_auto_trigger_skills(user_input: str) -> List[str]:
    """
    AI自动触发skills - 主要入口函数
    
    这个函数是Claude Code风格的核心：
    - 不依赖关键词
    - LLM理解意图
    - 自主决定调用哪个skill
    
    Args:
        user_input: 用户输入
        
    Returns:
        触发的skill名称列表
    """
    trigger = get_ai_skill_trigger()
    return await trigger.trigger(user_input)


# 便捷函数 - 同步版本
def ai_trigger_skills_sync(user_input: str) -> List[str]:
    """同步版本 - 兼容现有代码"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 在async环境中，创建新loop
            return asyncio.run(ai_auto_trigger_skills(user_input))
        else:
            return loop.run_until_complete(ai_auto_trigger_skills(user_input))
    except RuntimeError:
        return asyncio.run(ai_auto_trigger_skills(user_input))


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("测试: AI驱动的Skill触发器")
        print("=" * 60)
        
        # 测试用例
        test_cases = [
            "帮我搜索最新的人工智能新闻",
            "总结这篇文档的主要内容",
            "查找关于Python编程的资料",
            "帮我写一首诗",
            "分析这段代码的性能",
        ]
        
        for test_input in test_cases:
            print(f"\n用户输入: {test_input}")
            skills = await ai_auto_trigger_skills(test_input)
            print(f"触发的skills: {skills}")
        
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
    
    asyncio.run(test())
