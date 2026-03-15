import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.agents.skills.enhanced_registry import get_enhanced_skill_registry

# 新增：触发优化器
try:
    from src.services.skill_trigger_optimizer import SkillTriggerOptimizer, TriggerAnalysis, OptimizedTriggerConfig
    from src.services.skill_trigger_optimizer import TriggerTestCase, TriggerTestResult
except ImportError:
    SkillTriggerOptimizer = None
    TriggerAnalysis = None
    OptimizedTriggerConfig = None
    TriggerTestCase = None
    TriggerTestResult = None

"""
Skill 触发器 - 根据用户输入自动触发对应 Skill

功能：
1. 分析用户输入
2. 识别触发关键词
3. 自动选择对应的 Skills
4. 动态配置 Agent
5. 触发词优化与分析
"""


@dataclass
class SkillTriggerResult:
    """触发结果"""
    triggered_skills: List[str]
    confidence: float
    reasoning: str


class SkillTrigger:
    """
    Skill 触发器
    
    根据用户输入的关键词自动触发对应的 Skills。
    与增强版注册表配合使用。
    支持触发词优化和分析功能。
    """
    
    def __init__(self, registry=None):
        self.registry = registry or get_enhanced_skill_registry()
        self._build_trigger_index()
        
        # 初始化优化器（如果可用）
        self._optimizer = None
        if SkillTriggerOptimizer:
            try:
                self._optimizer = SkillTriggerOptimizer()
            except Exception:
                pass
    
    def _build_trigger_index(self):
        """构建触发词索引"""
        self._trigger_to_skills: Dict[str, List[str]] = {}
        
        for metadata in self.registry.list_skills():
            for trigger in metadata.triggers:
                trigger_lower = trigger.lower()
                if trigger_lower not in self._trigger_to_skills:
                    self._trigger_to_skills[trigger_lower] = []
                self._trigger_to_skills[trigger_lower].append(metadata.name)
    
    def trigger(self, user_input: str) -> SkillTriggerResult:
        """
        分析用户输入，触发对应的 Skills
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            SkillTriggerResult: 触发结果
        """
        user_input_lower = user_input.lower()
        
        # 1. 检测是否为技能创建请求
        create_keywords = [
            "创建技能", "新建技能", "添加技能", "开发技能", "制作技能", "设计技能", "编写技能", "实现技能", "构建技能",
            "创建一个技能", "新建一个技能", "添加一个技能", "开发一个技能", "制作一个技能", "设计一个技能", "编写一个技能",
            "技能创建", "技能开发", "技能制作", "技能设计", "技能编写", "技能实现", "技能构建",
            "做个技能", "弄个技能", "搞个技能", "做个新技能", "弄个新技能", "搞个新技能",
            "create skill", "new skill", "add skill", "develop skill", "make skill", "build skill", "design skill", "implement skill",
            "skill factory", "技能工厂", "工厂创建", "factory create", "skill creation", "skill development"
        ]
        
        # 更灵活的检测：检查是否同时包含"创建"和"技能"或"create"和"skill"
        create_chinese_words = ["创建", "新建", "添加", "开发", "制作", "设计", "编写", "实现", "构建", "做个", "弄个", "搞个"]
        skill_chinese_words = ["技能", "功能", "能力", "工具", "工作流", "模型", "系统", "程序", "代码", "应用", "服务", "模块"]
        
        has_create_chinese = any(word in user_input_lower for word in create_chinese_words)
        has_skill_chinese = any(word in user_input_lower for word in skill_chinese_words)
        has_create_english = any(word in user_input_lower for word in ["create", "new", "add", "develop", "make", "build", "design", "implement"])
        has_skill_english = "skill" in user_input_lower
        
        # 特殊短语检测
        special_phrases = [
            "想创建一个", "要创建一个", "需要创建一个", "希望创建一个",
            "想做个", "要做个", "需要做个", "希望做个",
            "开发一个", "设计一个", "实现一个", "构建一个"
        ]
        
        has_special_phrase = any(phrase in user_input_lower for phrase in special_phrases)
        
        is_creation_request = (
            any(keyword in user_input_lower for keyword in create_keywords) or
            (has_create_chinese and has_skill_chinese) or
            (has_create_english and has_skill_english) or
            (has_special_phrase and has_skill_chinese)
        )
        
        if is_creation_request:
            # 检查 Skill Factory 是否可用
            try:
                from .skill_factory_integration import is_skill_factory_available
                if is_skill_factory_available():
                    # 返回特殊结果，建议使用 Skill Factory
                    return SkillTriggerResult(
                        triggered_skills=["skill_factory_suggestion"],
                        confidence=0.9,
                        reasoning="检测到技能创建请求。建议使用 Skill Factory 快速创建新技能。"
                    )
            except ImportError:
                pass  # 继续正常匹配
        
        # 2. 正常触发词匹配
        matched_skills: Dict[str, int] = {}  # skill -> match_count
        
        for trigger, skills in self._trigger_to_skills.items():
            # 精确匹配
            if trigger in user_input_lower:
                for skill in skills:
                    matched_skills[skill] = matched_skills.get(skill, 0) + 3
            
            # 模糊匹配
            else:
                trigger_words = trigger.split()
                for word in trigger_words:
                    if len(word) >= 2 and word in user_input_lower:
                        for skill in skills:
                            matched_skills[skill] = matched_skills.get(skill, 0) + 1
        
        if not matched_skills:
            return SkillTriggerResult(
                triggered_skills=[],
                confidence=0.0,
                reasoning="No triggers matched"
            )
        
        # 排序并返回结果
        sorted_skills = sorted(
            matched_skills.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 选择前 N 个 Skills
        top_skills = [s[0] for s in sorted_skills[:5]]
        
        # 计算置信度
        max_score = sorted_skills[0][1] if sorted_skills else 1
        confidence = min(max_score / 10, 1.0)
        
        return SkillTriggerResult(
            triggered_skills=top_skills,
            confidence=confidence,
            reasoning=f"Matched {len(matched_skills)} skills: {', '.join(top_skills)}"
        )
    
    def get_skill_config(self, user_input: str) -> Dict[str, Any]:
        """
        获取 Skill 配置（用于 Agent 初始化）
        
        Args:
            user_input: 用户输入
            
        Returns:
            配置字典，可直接传给 Agent
        """
        result = self.trigger(user_input)
        
        # 检查是否为 Skill Factory 建议
        if result.triggered_skills and result.triggered_skills[0] == "skill_factory_suggestion":
            # 返回 Skill Factory 建议配置
            return {
                "triggered_skills": ["skill_factory_suggestion"],
                "confidence": result.confidence,
                "skill_configs": [{
                    "name": "skill_factory_suggestion",
                    "description": "检测到技能创建请求。建议使用 Skill Factory 快速创建新技能。",
                    "tools": [],
                    "prompt_template": ""
                }],
                "reasoning": result.reasoning,
                "factory_suggestion": True,
                "factory_available": True
            }
        
        # 获取 Skills 元数据
        skill_configs = []
        for skill_name in result.triggered_skills:
            metadata = self.registry.get_metadata(skill_name)
            if metadata:
                skill_configs.append({
                    "name": metadata.name,
                    "description": metadata.description,
                    "tools": [t.name for t in metadata.tools],
                    "prompt_template": metadata.prompt_template
                })
        
        return {
            "triggered_skills": result.triggered_skills,
            "confidence": result.confidence,
            "skill_configs": skill_configs,
            "reasoning": result.reasoning
        }
    
    # ========== 触发优化相关方法 ==========
    
    def analyze_trigger_effectiveness(
        self,
        skill_name: str,
        skill_description: str,
        triggers: List[str],
        positive_samples: List[str],
        negative_samples: List[str],
        test_cases: Optional[List[TriggerTestCase]] = None
    ) -> Optional[TriggerAnalysis]:
        """
        分析触发词效果
        
        Args:
            skill_name: 技能名称
            skill_description: 技能描述
            triggers: 触发词列表
            positive_samples: 正样本（应该触发）
            negative_samples: 负样本（不该触发）
            test_cases: 可选的额外测试用例
            
        Returns:
            TriggerAnalysis: 分析结果，如果优化器不可用返回 None
        """
        if not self._optimizer:
            return None
        
        return self._optimizer.analyze_trigger_effectiveness(
            skill_name=skill_name,
            skill_description=skill_description,
            triggers=triggers,
            positive_samples=positive_samples,
            negative_samples=negative_samples,
            test_cases=test_cases
        )
    
    def optimize_triggers(
        self,
        skill_name: str,
        skill_description: str,
        current_triggers: List[str],
        positive_samples: List[str],
        negative_samples: List[str],
        target_precision: float = 0.9,
        target_recall: float = 0.85
    ) -> Optional[OptimizedTriggerConfig]:
        """
        优化触发词
        
        Args:
            skill_name: 技能名称
            skill_description: 技能描述
            current_triggers: 当前触发词列表
            positive_samples: 正样本
            negative_samples: 负样本
            target_precision: 目标精确率
            target_recall: 目标召回率
            
        Returns:
            OptimizedTriggerConfig: 优化后的配置，如果优化器不可用返回 None
        """
        if not self._optimizer:
            return None
        
        return self._optimizer.optimize_triggers(
            skill_name=skill_name,
            skill_description=skill_description,
            current_triggers=current_triggers,
            positive_samples=positive_samples,
            negative_samples=negative_samples,
            target_precision=target_precision,
    )

    def get_trigger_stats(self) -> Dict[str, Any]:
        """获取触发器统计信息"""
        stats = {
            "total_triggers": len(self._trigger_to_skills),
            "total_skills": len(set(
                skill for skills in self._trigger_to_skills.values() 
                for skill in skills
            )),
            "optimizer_available": self._optimizer is not None,
            "trigger_mapping": {
                trigger: skills 
                for trigger, skills in list(self._trigger_to_skills.items())[:10]
            }
        }
        return stats


# 全局单例
_skill_trigger: Optional[SkillTrigger] = None


def get_skill_trigger() -> SkillTrigger:
    """获取 Skill 触发器单例"""
    global _skill_trigger
    if _skill_trigger is None:
        _skill_trigger = SkillTrigger()
    return _skill_trigger


# 便捷函数
def auto_trigger_skills(user_input: str) -> List[str]:
    """自动触发 Skills - 返回技能名称列表"""
    trigger = get_skill_trigger()
    result = trigger.trigger(user_input)
    return result.triggered_skills


def get_skill_config_for_input(user_input: str) -> Dict[str, Any]:
    """获取用户输入对应的 Skill 配置"""
    trigger = get_skill_trigger()
    return trigger.get_skill_config(user_input)


def analyze_skill_triggers(test_cases: List[TriggerTestCase]) -> Optional[TriggerAnalysis]:
    """分析技能触发效果"""
    trigger = get_skill_trigger()
    return trigger.analyze_trigger_effectiveness(test_cases)


def optimize_skill_triggers(skill_name: str, test_cases: List[TriggerTestCase]) -> Optional[OptimizedTriggerConfig]:
    """优化技能触发词"""
    trigger = get_skill_trigger()
    return trigger.optimize_triggers(skill_name, test_cases)
