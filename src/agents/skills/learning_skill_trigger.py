#!/usr/bin/env python3
"""
Learning-Enabled Skill Trigger
==============================

将自我学习能力集成到Skill触发系统中

功能:
- 基于学习自动预测最佳Skill
- 优化触发条件
- 记录触发效果并学习
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from ..agents.skills.skill_trigger import SkillTrigger, SkillTriggerResult
from ..agents.skills.enhanced_registry import get_enhanced_skill_registry
from src.core.self_learning import (
    get_skill_trigger_learner,
    TriggerCondition
)

logger = logging.getLogger(__name__)


class LearningSkillTrigger(SkillTrigger):
    """
    带学习能力的Skill触发器
    
    继承SkillTrigger的所有功能，并增加:
    - 基于学习的Skill预测
    - 触发条件优化
    - 触发效果学习
    """
    
    def __init__(self, registry=None, enable_learning: bool = True):
        """初始化带学习的Skill触发器"""
        super().__init__(registry)
        
        # 学习功能
        self.enable_learning = enable_learning
        
        if enable_learning:
            self.skill_learner = get_skill_trigger_learner()
            
            # 将已注册的Skill注册到学习器
            self._register_existing_skills()
        
        # 学习统计
        self._learning_stats = {
            "predictions_made": 0,
            "trigger_records": 0,
            "conditions_optimized": 0
        }
        
        logger.info("✅ LearningSkillTrigger initialized")
    
    def _register_existing_skills(self):
        """注册已有的Skill到学习器"""
        if not self.enable_learning:
            return
        
        try:
            for skill_meta in self.registry.list_skills():
                skill_name = skill_meta.name
                triggers = getattr(skill_meta, 'triggers', [])
                
                if triggers:
                    self.skill_learner.register_skill(
                        skill_name=skill_name,
                        trigger_keywords=triggers
                    )
                
                logger.debug(f"Registered skill for learning: {skill_name}")
                
        except Exception as e:
            logger.warning(f"Failed to register existing skills: {e}")
    
    def trigger_with_learning(
        self,
        user_input: str,
        context: Dict = None,
        record_result: bool = True
    ) -> SkillTriggerResult:
        """
        触发Skill（带学习功能）
        
        Args:
            user_input: 用户输入
            context: 上下文
            record_result: 是否记录结果用于学习
            
        Returns:
            SkillTriggerResult: 触发结果
        """
        context = context or {}
        
        # 如果没有启用学习，使用原始触发
        if not self.enable_learning:
            return self.trigger(user_input)
        
        # 获取可用Skills
        available_skills = [s.name for s in self.registry.list_skills()]
        
        # 预测最佳Skill
        predicted_skill, scores = self.skill_learner.predict_best_skill(
            query=user_input,
            context=context,
            available_skills=available_skills
        )
        
        self._learning_stats["predictions_made"] += 1
        
        # 如果预测置信度低，使用原始触发作为补充
        if not predicted_skill or scores.get(predicted_skill, 0) < 0.5:
            fallback_result = self.trigger(user_input)
            
            # 合并结果
            triggered_skills = list(set(
                fallback_result.triggered_skills + 
                ([predicted_skill] if predicted_skill else [])
            ))
            
            confidence = max(fallback_result.confidence, scores.get(predicted_skill, 0))
            reasoning = f"预测: {predicted_skill}, 原始: {fallback_result.triggered_skills}"
            
            result = SkillTriggerResult(
                triggered_skills=triggered_skills,
                confidence=confidence,
                reasoning=reasoning
            )
        else:
            result = SkillTriggerResult(
                triggered_skills=[predicted_skill],
                confidence=scores.get(predicted_skill, 0.5),
                reasoning=f"Learned prediction: {predicted_skill}"
            )
        
        # 记录触发结果用于学习
        if record_result:
            # 注意：实际执行结果需要在外部调用后反馈
            pass
        
        return result
    
    def record_trigger_result(
        self,
        skill_name: str,
        query: str,
        context: Dict,
        success: bool,
        quality_score: float = 0.5,
        execution_time: float = 0.0
    ):
        """
        记录触发结果，用于学习
        
        在Skill执行完成后调用
        """
        if not self.enable_learning:
            return
        
        # 获取触发条件
        skill_meta = self.registry.get_skill(skill_name)
        triggers = getattr(skill_meta, 'triggers', []) if skill_meta else []
        
        # 注册Skill（如果不存在）
        if skill_name not in self.skill_learner._skill_performance:
            self.skill_learner.register_skill(
                skill_name=skill_name,
                trigger_keywords=triggers
            )
        
        # 记录触发
        self.skill_learner.record_trigger(
            skill_name=skill_name,
            trigger_condition=TriggerCondition(
                keywords=self._extract_keywords(query)
            ),
            query=query,
            context=context,
            success=success,
            quality_score=quality_score,
            execution_time=execution_time
        )
        
        self._learning_stats["trigger_records"] += 1
        
        logger.debug(f"Recorded trigger result: {skill_name}, success={success}")
    
    def optimize_trigger_conditions(self) -> Dict[str, List[str]]:
        """
        优化触发条件
        
        基于学习结果自动优化每个Skill的触发关键词
        
        Returns:
            Dict[skill_name, optimized_keywords]
        """
        if not self.enable_learning:
            return {}
        
        optimized = {}
        
        for skill_name in self.skill_learner._skill_performance.keys():
            condition = self.skill_learner.optimize_trigger_condition(skill_name)
            optimized[skill_name] = condition.keywords
            
            self._learning_stats["conditions_optimized"] += 1
        
        logger.info(f"Optimized {len(optimized)} trigger conditions")
        
        return optimized
    
    def get_skill_recommendations(
        self,
        query: str,
        context: Dict = None,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        获取Skill推荐
        
        Returns:
            List[(skill_name, score)]
        """
        if not self.enable_learning:
            return []
        
        return self.skill_learner.get_skill_recommendations(
            query=query,
            context=context,
            top_k=top_k
        )
    
    def get_cooccurrence_skills(self, skill_name: str) -> List[Tuple[str, float]]:
        """获取经常一起使用的Skills"""
        if not self.enable_learning:
            return []
        
        return self.skill_learner.get_cooccurrence_skills(skill_name)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', text)
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        keywords = list(set(chinese_words + english_words))
        keywords = [k for k in keywords if len(k) >= 2]
        
        return keywords[:10]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        if not self.enable_learning:
            return {"learning_enabled": False}
        
        return {
            "learning_enabled": True,
            "learning_stats": self._learning_stats,
            "skill_learner_stats": self.skill_learner.get_statistics()
        }
    
    def export_learning_knowledge(self, path: str):
        """导出学习知识"""
        if self.enable_learning:
            self.skill_learner.export_knowledge(path)
    
    def import_learning_knowledge(self, path: str):
        """导入学习知识"""
        if self.enable_learning:
            self.skill_learner.import_knowledge(path)


def create_learning_skill_trigger() -> LearningSkillTrigger:
    """创建带学习的Skill触发器"""
    registry = get_enhanced_skill_registry()
    return LearningSkillTrigger(registry=registry)
