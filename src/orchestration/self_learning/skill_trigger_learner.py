#!/usr/bin/env python3
"""
技能触发学习器 (Skill Trigger Learner)
=======================================

学习什么条件下触发哪个技能效果最好

功能:
- 记录技能触发与成功率的映射
- 分析触发条件与最佳技能的关系
- 预测新场景应该触发什么技能
- 自动优化触发条件
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


@dataclass
class TriggerCondition:
    """触发条件"""
    keywords: List[str] = field(default_factory=list)
    query_patterns: List[str] = field(default_factory=list)
    context_required: List[str] = field(default_factory=list)
    min_confidence: float = 0.5
    
    def matches(self, query: str, context: Dict = None) -> float:
        """检查是否匹配，返回置信度"""
        query_lower = query.lower()
        context = context or {}
        
        # 关键词匹配
        keyword_matches = sum(
            1 for kw in self.keywords
            if kw.lower() in query_lower
        )
        keyword_score = keyword_matches / len(self.keywords) if self.keywords else 0
        
        # 上下文匹配
        context_matches = sum(
            1 for ctx in self.context_required
            if context.get(ctx)
        )
        context_score = context_matches / len(self.context_required) if self.context_required else 1.0
        
        # 综合分数
        confidence = (keyword_score * 0.7 + context_score * 0.3)
        
        return confidence if confidence >= self.min_confidence else 0.0


@dataclass
class SkillTriggerRecord:
    """技能触发记录"""
    skill_name: str
    trigger_condition: TriggerCondition
    query: str
    context: Dict
    success: bool
    quality_score: float
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class SkillTriggerLearner:
    """
    技能触发学习器
    
    从历史触发记录中学习，优化技能触发策略
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 学习参数
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_samples = self.config.get("min_samples", 5)
        
        # 技能表现记录
        # {skill_name: [records]}
        self._skill_records: Dict[str, List[SkillTriggerRecord]] = defaultdict(list)
        
        # 技能性能缓存
        # {skill_name: performance_score}
        self._skill_performance: Dict[str, float] = {}
        
        # 关键词到技能的映射
        # {keyword: {skill_name: count}}
        self._keyword_skill_map: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 技能协同记录
        # {skill_name: {co_skill: count}}
        self._skill_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 触发条件优化
        # {skill_name: optimized_condition}
        self._optimized_conditions: Dict[str, TriggerCondition] = {}
        
        # 锁
        self._lock = threading.RLock()
        
        # 统计
        self._total_triggers = 0
        self._successful_triggers = 0
        
        logger.info("SkillTriggerLearner initialized")
    
    def register_skill(
        self,
        skill_name: str,
        trigger_keywords: List[str] = None,
        trigger_patterns: List[str] = None
    ):
        """注册技能及其触发条件"""
        with self._lock:
            # 初始化性能缓存
            if skill_name not in self._skill_performance:
                self._skill_performance[skill_name] = 0.5
            
            # 初始化关键词映射
            if trigger_keywords:
                for keyword in trigger_keywords:
                    self._keyword_skill_map[keyword][skill_name] = 0
            
            # 初始化优化条件
            if skill_name not in self._optimized_conditions:
                self._optimized_conditions[skill_name] = TriggerCondition(
                    keywords=trigger_keywords or [],
                    query_patterns=trigger_patterns or []
                )
            
            logger.debug(f"Registered skill: {skill_name}")
    
    def record_trigger(
        self,
        skill_name: str,
        trigger_condition: TriggerCondition,
        query: str,
        context: Dict,
        success: bool,
        quality_score: float = 0.5,
        execution_time: float = 0.0
    ):
        """记录技能触发"""
        with self._lock:
            record = SkillTriggerRecord(
                skill_name=skill_name,
                trigger_condition=trigger_condition,
                query=query,
                context=context,
                success=success,
                quality_score=quality_score,
                execution_time=execution_time
            )
            
            self._skill_records[skill_name].append(record)
            self._total_triggers += 1
            
            if success:
                self._successful_triggers += 1
            
            # 更新关键词映射
            query_lower = query.lower()
            for keyword in trigger_condition.keywords:
                if keyword.lower() in query_lower:
                    self._keyword_skill_map[keyword][skill_name] += 1
            
            # 更新性能缓存
            self._update_performance_cache(skill_name)
            
            # 限制记录数量
            max_records = self.config.get("max_records_per_skill", 500)
            if len(self._skill_records[skill_name]) > max_records:
                self._skill_records[skill_name] = self._skill_records[skill_name][-max_records:]
            
            logger.debug(f"Recorded trigger: {skill_name}, success={success}")
    
    def _update_performance_cache(self, skill_name: str):
        """更新技能性能缓存"""
        records = self._skill_records.get(skill_name, [])
        
        if not records:
            return
        
        # 计算成功率
        success_count = sum(1 for r in records if r.success)
        success_rate = success_count / len(records)
        
        # 计算平均质量分数
        avg_quality = sum(r.quality_score for r in records) / len(records)
        
        # 计算平均执行时间分数 (越快越好)
        if records:
            avg_time = sum(r.execution_time for r in records) / len(records)
            time_score = max(0, 1.0 - (avg_time / 30.0))  # 30秒为满分
        else:
            time_score = 0.5
        
        # 综合分数
        performance = success_rate * 0.5 + avg_quality * 0.35 + time_score * 0.15
        
        self._skill_performance[skill_name] = performance
    
    def predict_best_skill(
        self,
        query: str,
        context: Dict = None,
        available_skills: List[str] = None
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """
        预测最佳触发的技能
        
        Args:
            query: 用户查询
            context: 上下文
            available_skills: 可用技能列表
            
        Returns:
            (最佳技能, 所有技能评分)
        """
        with self._lock:
            context = context or {}
            
            # 如果没有可用技能列表，使用已注册的
            if available_skills is None:
                available_skills = list(self._skill_performance.keys())
            
            if not available_skills:
                return None, {}
            
            # 如果没有足够样本，返回默认
            if self._total_triggers < self.min_samples:
                return available_skills[0] if available_skills else None, \
                       {s: 0.5 for s in available_skills}
            
            # 计算每个技能的匹配分数
            scores = {}
            
            for skill_name in available_skills:
                # 基础性能分数
                base_score = self._skill_performance.get(skill_name, 0.5)
                
                # 关键词匹配分数
                keyword_score = self._calculate_keyword_score(
                    query, skill_name
                )
                
                # 上下文匹配分数
                context_score = self._calculate_context_score(
                    skill_name, context
                )
                
                # 综合分数
                score = (
                    base_score * 0.5 +
                    keyword_score * 0.3 +
                    context_score * 0.2
                )
                
                scores[skill_name] = score
            
            # 选择最佳技能
            if not scores:
                return None, {}
            
            best_skill = max(scores.items(), key=lambda x: x[1])[0]
            
            logger.debug(f"Predicted best skill: {best_skill} for query: {query[:30]}...")
            
            return best_skill, scores
    
    def _calculate_keyword_score(self, query: str, skill_name: str) -> float:
        """计算关键词匹配分数"""
        query_lower = query.lower()
        
        # 获取该技能关联的关键词
        skill_keywords = {}
        for keyword, skill_counts in self._keyword_skill_map.items():
            if skill_name in skill_counts:
                skill_keywords[keyword] = skill_counts[skill_name]
        
        if not skill_keywords:
            return 0.3  # 默认分数
        
        # 计算匹配
        matches = sum(
            count for kw, count in skill_keywords.items()
            if kw.lower() in query_lower
        )
        
        max_count = max(skill_keywords.values()) if skill_keywords else 1
        
        return min(1.0, matches / max_count)
    
    def _calculate_context_score(self, skill_name: str, context: Dict) -> float:
        """计算上下文匹配分数"""
        # 简单实现：检查上下文是否匹配技能的预期
        # 实际可以根据历史数据学习
        
        if not context:
            return 0.5
        
        # 可以根据历史成功案例计算
        records = self._skill_records.get(skill_name, [])
        
        if not records:
            return 0.5
        
        # 计算相似上下文的成功率
        context_keys = set(context.keys())
        
        relevant_records = [
            r for r in records
            if set(r.context.keys()) & context_keys
        ]
        
        if not relevant_records:
            return 0.5
        
        success_count = sum(1 for r in relevant_records if r.success)
        return success_count / len(relevant_records)
    
    def learn_from_feedback(
        self,
        predicted_skill: str,
        actual_skill: str,
        success: bool,
        quality_score: float
    ):
        """从反馈中学习"""
        # 这个方法主要用于记录，让系统自动学习
        # 实际触发时会自动调用 record_trigger
        logger.debug(f"Learned: predicted={predicted_skill}, actual={actual_skill}")
    
    def get_skill_recommendations(
        self,
        query: str,
        context: Dict = None,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """获取技能推荐"""
        _, scores = self.predict_best_skill(query, context)
        
        if not scores:
            return []
        
        sorted_skills = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_skills[:top_k]
    
    def optimize_trigger_condition(self, skill_name: str) -> TriggerCondition:
        """优化触发条件"""
        with self._lock:
            records = self._skill_records.get(skill_name, [])
            
            if not records:
                return self._optimized_conditions.get(
                    skill_name,
                    TriggerCondition()
                )
            
            # 分析成功的触发条件
            successful_keywords = defaultdict(int)
            total_successful = 0
            
            for record in records:
                if record.success:
                    total_successful += 1
                    for kw in record.trigger_condition.keywords:
                        successful_keywords[kw] += 1
            
            if not successful_keywords:
                return self._optimized_conditions.get(skill_name, TriggerCondition())
            
            # 找出最有效的关键词
            sorted_keywords = sorted(
                successful_keywords.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # 取成功率高的关键词
            top_keywords = [
                kw for kw, count in sorted_keywords[:10]
                if count >= total_successful * 0.3
            ]
            
            # 更新优化条件
            optimized = TriggerCondition(
                keywords=top_keywords,
                min_confidence=0.4
            )
            
            self._optimized_conditions[skill_name] = optimized
            
            logger.info(f"Optimized trigger condition for {skill_name}: {top_keywords}")
            
            return optimized
    
    def get_cooccurrence_skills(self, skill_name: str) -> List[Tuple[str, float]]:
        """获取经常一起使用的技能"""
        co_skills = self._skill_cooccurrence.get(skill_name, {})
        
        if not co_skills:
            return []
        
        total = sum(co_skills.values())
        
        return [
            (s, count / total)
            for s, count in sorted(co_skills.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def record_skill_cooccurrence(self, skill1: str, skill2: str):
        """记录技能共现"""
        with self._lock:
            self._skill_cooccurrence[skill1][skill2] += 1
            self._skill_cooccurrence[skill2][skill1] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        with self._lock:
            return {
                "total_triggers": self._total_triggers,
                "successful_triggers": self._successful_triggers,
                "success_rate": (
                    self._successful_triggers / self._total_triggers
                    if self._total_triggers > 0 else 0
                ),
                "registered_skills": len(self._skill_performance),
                "skill_performance": self._skill_performance,
                "keyword_map_size": len(self._keyword_skill_map)
            }
    
    def export_knowledge(self, path: str):
        """导出学习到的知识"""
        with self._lock:
            data = {
                "skill_performance": self._skill_performance,
                "optimized_conditions": {
                    k: {"keywords": v.keywords, "min_confidence": v.min_confidence}
                    for k, v in self._optimized_conditions.items()
                },
                "keyword_map": dict(self._keyword_skill_map),
                "statistics": self.get_statistics()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported skill trigger knowledge to {path}")
    
    def import_knowledge(self, path: str):
        """导入知识"""
        with self._lock:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._skill_performance = data.get("skill_performance", {})
                
                # 恢复优化条件
                for skill, cond_data in data.get("optimized_conditions", {}).items():
                    self._optimized_conditions[skill] = TriggerCondition(
                        keywords=cond_data.get("keywords", []),
                        min_confidence=cond_data.get("min_confidence", 0.5)
                    )
                
                self._keyword_skill_map = defaultdict(
                    lambda: defaultdict(int),
                    data.get("keyword_map", {})
                )
                
                logger.info(f"Imported skill trigger knowledge from {path}")
            except Exception as e:
                logger.error(f"Failed to import knowledge: {e}")


# 全局实例
_skill_trigger_learner: Optional[SkillTriggerLearner] = None


def get_skill_trigger_learner(config: Optional[Dict] = None) -> SkillTriggerLearner:
    """获取技能触发学习器实例"""
    global _skill_trigger_learner
    if _skill_trigger_learner is None:
        _skill_trigger_learner = SkillTriggerLearner(config)
    return _skill_trigger_learner
