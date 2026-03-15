#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习能力分析器
分析系统的学习能力、自适应能力和知识积累能力
"""

import os
import ast
import re
import logging
from typing import Dict, List, Any, Optional
from base_analyzer import BaseAnalyzer


class LearningCapabilityAnalyzer(BaseAnalyzer):
    """学习能力分析器"""
    
    def __init__(self, python_files: List[str]):
        super().__init__(python_files)
        self.analyzer_name = "学习能力分析器"
        
    def analyze(self) -> Dict[str, Any]:
        """分析学习能力"""
        try:
            learning_metrics = {
                "adaptive_learning": self._analyze_adaptive_learning(),
                "knowledge_accumulation": self._analyze_knowledge_accumulation(),
                "pattern_recognition": self._analyze_pattern_recognition(),
                "feedback_learning": self._analyze_feedback_learning(),
                "continuous_improvement": self._analyze_continuous_improvement(),
                "experience_integration": self._analyze_experience_integration(),
                "learning_algorithms": self._analyze_learning_algorithms(),
                "knowledge_base": self._analyze_knowledge_base(),
                "learning_metrics": self._analyze_learning_metrics(),
                "adaptive_strategies": self._analyze_adaptive_strategies()
            }
            
            # 计算综合学习能力分数
            total_score = sum(learning_metrics.values()) / len(learning_metrics)
            
            return {
                "learning_capability_score": total_score,
                "learning_metrics": learning_metrics,
                "analysis_details": self._get_analysis_details(),
                "recommendations": self._get_recommendations(learning_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"学习能力分析失败: {e}")
            return {"learning_capability_score": 0.0, "error": str(e)}
    
    def _analyze_adaptive_learning(self) -> float:
        """分析自适应学习能力"""
        score = 0.0
        adaptive_patterns = [
            r"adaptive.*learning",
            r"self.*adjust",
            r"dynamic.*update",
            r"automatic.*adapt",
            r"learning.*rate",
            r"adaptive.*strategy"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in adaptive_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_knowledge_accumulation(self) -> float:
        """分析知识积累能力"""
        score = 0.0
        knowledge_patterns = [
            r"knowledge.*base",
            r"knowledge.*store",
            r"knowledge.*accumulate",
            r"experience.*store",
            r"learning.*history",
            r"knowledge.*update"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in knowledge_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_pattern_recognition(self) -> float:
        """分析模式识别能力"""
        score = 0.0
        pattern_recognition_patterns = [
            r"pattern.*recognition",
            r"pattern.*detect",
            r"pattern.*learn",
            r"pattern.*match",
            r"similarity.*detect",
            r"clustering",
            r"classification"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in pattern_recognition_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_feedback_learning(self) -> float:
        """分析反馈学习能力"""
        score = 0.0
        feedback_patterns = [
            r"feedback.*learning",
            r"reinforcement.*learning",
            r"reward.*learning",
            r"feedback.*loop",
            r"performance.*feedback",
            r"learning.*feedback"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in feedback_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_continuous_improvement(self) -> float:
        """分析持续改进能力"""
        score = 0.0
        improvement_patterns = [
            r"continuous.*improvement",
            r"iterative.*improvement",
            r"performance.*optimization",
            r"model.*update",
            r"algorithm.*improve",
            r"learning.*optimization"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in improvement_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_experience_integration(self) -> float:
        """分析经验整合能力"""
        score = 0.0
        experience_patterns = [
            r"experience.*integration",
            r"experience.*learn",
            r"historical.*data",
            r"past.*experience",
            r"experience.*base",
            r"learning.*from.*experience"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in experience_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_learning_algorithms(self) -> float:
        """分析学习算法"""
        score = 0.0
        learning_algorithms = [
            r"machine.*learning",
            r"deep.*learning",
            r"neural.*network",
            r"gradient.*descent",
            r"backpropagation",
            r"reinforcement.*learning",
            r"supervised.*learning",
            r"unsupervised.*learning"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for algorithm in learning_algorithms:
                    if re.search(algorithm, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_knowledge_base(self) -> float:
        """分析知识库"""
        score = 0.0
        knowledge_base_patterns = [
            r"knowledge.*base",
            r"knowledge.*graph",
            r"knowledge.*store",
            r"knowledge.*management",
            r"knowledge.*retrieval",
            r"knowledge.*update"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in knowledge_base_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_learning_metrics(self) -> float:
        """分析学习指标"""
        score = 0.0
        learning_metrics_patterns = [
            r"learning.*metrics",
            r"learning.*performance",
            r"learning.*accuracy",
            r"learning.*efficiency",
            r"learning.*progress",
            r"learning.*rate"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in learning_metrics_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _analyze_adaptive_strategies(self) -> float:
        """分析自适应策略"""
        score = 0.0
        adaptive_strategy_patterns = [
            r"adaptive.*strategy",
            r"dynamic.*strategy",
            r"learning.*strategy",
            r"strategy.*adaptation",
            r"adaptive.*behavior",
            r"strategy.*learning"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in adaptive_strategy_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 0.1
                        
            except Exception:
                continue
        
        return min(score, 1.0)
    
    def _get_analysis_details(self) -> Dict[str, Any]:
        """获取分析详情"""
        return {
            "total_files_analyzed": len(self.python_files),
            "learning_components_found": self._count_learning_components(),
            "adaptive_features": self._count_adaptive_features(),
            "knowledge_management": self._count_knowledge_management()
        }
    
    def _count_learning_components(self) -> int:
        """统计学习组件数量"""
        count = 0
        learning_components = [
            "LearningEngine", "AdaptiveLearning", "KnowledgeBase",
            "PatternLearner", "FeedbackLearner", "ExperienceManager"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for component in learning_components:
                    if component in content:
                        count += 1
                        
            except Exception:
                continue
        
        return count
    
    def _count_adaptive_features(self) -> int:
        """统计自适应功能数量"""
        count = 0
        adaptive_features = [
            "adaptive", "dynamic", "self-adjust", "automatic",
            "learning_rate", "adaptive_strategy"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for feature in adaptive_features:
                    if re.search(feature, content, re.IGNORECASE):
                        count += 1
                        
            except Exception:
                continue
        
        return count
    
    def _count_knowledge_management(self) -> int:
        """统计知识管理功能数量"""
        count = 0
        knowledge_features = [
            "knowledge", "experience", "learning", "pattern",
            "feedback", "improvement"
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for feature in knowledge_features:
                    if re.search(feature, content, re.IGNORECASE):
                        count += 1
                        
            except Exception:
                continue
        
        return count
    
    def _get_recommendations(self, learning_metrics: Dict[str, float]) -> List[str]:
        """获取改进建议"""
        recommendations = []
        
        if learning_metrics["adaptive_learning"] < 0.5:
            recommendations.append("增强自适应学习能力，实现动态参数调整")
        
        if learning_metrics["knowledge_accumulation"] < 0.5:
            recommendations.append("完善知识积累机制，建立知识库系统")
        
        if learning_metrics["pattern_recognition"] < 0.5:
            recommendations.append("加强模式识别能力，实现智能模式匹配")
        
        if learning_metrics["feedback_learning"] < 0.5:
            recommendations.append("建立反馈学习机制，实现强化学习")
        
        if learning_metrics["continuous_improvement"] < 0.5:
            recommendations.append("实现持续改进机制，优化学习效果")
        
        if learning_metrics["learning_algorithms"] < 0.5:
            recommendations.append("集成更多学习算法，提升学习能力")
        
        if not recommendations:
            recommendations.append("学习能力表现优秀，继续保持")
        
        return recommendations
