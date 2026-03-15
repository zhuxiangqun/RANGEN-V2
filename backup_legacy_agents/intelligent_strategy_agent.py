#!/usr/bin/env python3
"""
智能策略智能体 - 整合策略分析、决策制定和执行功能
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re
import numpy as np

# 基础导入
from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig, AgentCapability, StrategyDecision, PerformanceMetrics, LearningResult

# 工具导入
from ..utils.unified_centers import get_unified_center

logger = logging.getLogger(__name__)

@dataclass
class StrategyAnalysis:
    """策略分析"""
    analysis_id: str
    query_type: str
    complexity: float
    key_factors: List[str]
    recommendations: List[str]
    confidence: float

class IntelligentStrategyAgent(BaseAgent):
    """智能策略智能体 - 整合策略分析、决策制定和执行功能"""

    def __init__(self, agent_name: str = "IntelligentStrategyAgent", use_intelligent_config: bool = True):
        super().__init__(agent_name, capabilities=None, config=None)

        self.is_executing = False
        self._execution_lock = threading.Lock()
        self.agent_name = agent_name

        # 初始化策略配置
        self.strategy_config = self._get_default_strategy_config()
        self.decision_threshold = 0.7
        self.analysis_threshold = 0.6
        
        # 策略统计
        self.strategy_stats = {
            "total_queries": 0,
            "successful_strategies": 0,
            "failed_strategies": 0,
            "average_confidence": 0.0,
            "strategy_types": {},
            "decision_count": 0
        }

        logger.info("✅ 智能策略智能体初始化完成")

    def _get_default_strategy_config(self) -> Dict[str, Any]:
        """获取默认策略配置"""
        return {
            "max_analysis_depth": 5,
            "decision_threshold": 0.7,
            "analysis_threshold": 0.6,
            "strategy_types": ["competitive", "collaborative", "adaptive", "innovative"],
            "risk_tolerance": 0.5,
            "time_horizon": "medium",
            "resource_constraints": [],
            "stakeholder_considerations": True
        }

    async def process_query(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> AgentResult:
        """处理查询"""
        start_time = time.time()
        
        try:
            with self._execution_lock:
                self.is_executing = True
                
                # 更新统计
                self.strategy_stats["total_queries"] += 1
                
                # 分析查询类型
                query_analysis = self._analyze_query(query)
                
                # 执行策略分析
                strategy_analysis = await self._execute_strategy_analysis(query, query_analysis, context)
                
                # 制定策略决策
                strategy_decision = await self._make_strategy_decision(strategy_analysis, query_analysis)
                
                # 生成策略建议
                strategy_recommendations = self._generate_strategy_recommendations(strategy_decision, strategy_analysis)
                
                # 计算置信度
                confidence = self._calculate_strategy_confidence(strategy_analysis, strategy_decision)
                
                processing_time = time.time() - start_time
                
                # 更新统计
                if confidence >= self.decision_threshold:
                    self.strategy_stats["successful_strategies"] += 1
                    self.strategy_stats["decision_count"] += 1
                else:
                    self.strategy_stats["failed_strategies"] += 1
                
                self._update_average_confidence(confidence)
                self._update_strategy_type_stats(strategy_analysis.query_type)
                
                return AgentResult(
                    success=True,
                    data=strategy_recommendations,
                    confidence=confidence,
                    processing_time=processing_time,
                    metadata={
                        "strategy_type": strategy_analysis.query_type,
                        "analysis_id": strategy_analysis.analysis_id,
                        "processing_time": processing_time,
                        "query": query
                    }
                )
                
        except Exception as e:
            logger.error(f"处理策略查询失败: {e}")
            self.strategy_stats["failed_strategies"] += 1
            
            return AgentResult(
                success=False,
                data=f"策略分析失败: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e), "query": query},
                error=str(e)
            )
        finally:
            self.is_executing = False

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询类型和复杂度"""
        query_lower = query.lower()
        
        # 基础查询类型分析
        query_type = "general"
        complexity = 0.5
        
        if any(word in query_lower for word in ["策略", "战略", "计划", "方案"]):
            query_type = "strategic"
            complexity = 0.8
        elif any(word in query_lower for word in ["决策", "选择", "决定", "判断"]):
            query_type = "decision"
            complexity = 0.7
        elif any(word in query_lower for word in ["分析", "评估", "评价", "比较"]):
            query_type = "analytical"
            complexity = 0.6
        elif any(word in query_lower for word in ["创新", "改进", "优化", "提升"]):
            query_type = "innovative"
            complexity = 0.9
        
        # 基于长度调整复杂度
        word_count = len(query.split())
        if word_count > 25:
            complexity = min(1.0, complexity + 0.2)
        elif word_count < 5:
            complexity = max(0.2, complexity - 0.2)
        
        return {
            "type": query_type,
            "complexity": complexity,
            "word_count": word_count,
            "keywords": self._extract_keywords(query),
            "urgency": self._assess_urgency(query),
            "stakeholders": self._identify_stakeholders(query)
        }

    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        words = query.split()
        keywords = []
        
        for word in words:
            if len(word) > 2 and word.isalpha():
                keywords.append(word.lower())
        
        return keywords[:15]  # 限制关键词数量

    def _assess_urgency(self, query: str) -> str:
        """评估紧急程度"""
        urgent_words = ["紧急", "立即", "马上", "尽快", "急迫"]
        query_lower = query.lower()
        
        if any(word in query_lower for word in urgent_words):
            return "high"
        elif "重要" in query_lower or "关键" in query_lower:
            return "medium"
        else:
            return "low"

    def _identify_stakeholders(self, query: str) -> List[str]:
        """识别利益相关者"""
        stakeholders = []
        query_lower = query.lower()
        
        stakeholder_keywords = {
            "客户": ["客户", "用户", "消费者"],
            "员工": ["员工", "团队", "人员"],
            "股东": ["股东", "投资者", "投资人"],
            "供应商": ["供应商", "合作伙伴", "合作方"],
            "政府": ["政府", "监管", "政策"]
        }
        
        for stakeholder, keywords in stakeholder_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                stakeholders.append(stakeholder)
        
        return stakeholders

    async def _execute_strategy_analysis(self, query: str, query_analysis: Dict[str, Any], 
                                       context: Optional[List[Dict[str, Any]]]) -> StrategyAnalysis:
        """执行策略分析"""
        analysis_id = f"analysis_{int(time.time() * 1000)}"
        query_type = query_analysis.get("type", "general")
        
        # 根据查询类型选择分析策略
        if query_type == "strategic":
            analysis = await self._strategic_analysis(query, context)
        elif query_type == "decision":
            analysis = await self._decision_analysis(query, context)
        elif query_type == "analytical":
            analysis = await self._analytical_analysis(query, context)
        elif query_type == "innovative":
            analysis = await self._innovative_analysis(query, context)
        else:
            analysis = await self._general_analysis(query, context)
        
        return StrategyAnalysis(
            analysis_id=analysis_id,
            query_type=query_type,
            complexity=query_analysis.get("complexity", 0.5),
            key_factors=analysis.get("key_factors", []),
            recommendations=analysis.get("recommendations", []),
            confidence=analysis.get("confidence", 0.6)
        )

    async def _strategic_analysis(self, query: str, context: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """战略分析"""
        return {
            "key_factors": ["市场环境", "竞争态势", "资源能力", "时间窗口"],
            "recommendations": ["制定长期战略", "建立竞争优势", "优化资源配置"],
            "confidence": 0.8
        }

    async def _decision_analysis(self, query: str, context: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """决策分析"""
        return {
            "key_factors": ["决策标准", "可选方案", "风险评估", "预期结果"],
            "recommendations": ["明确决策标准", "评估各方案", "制定实施计划"],
            "confidence": 0.7
        }

    async def _analytical_analysis(self, query: str, context: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """分析性分析"""
        return {
            "key_factors": ["数据质量", "分析方法", "假设条件", "结论可靠性"],
            "recommendations": ["收集更多数据", "验证分析方法", "检查假设条件"],
            "confidence": 0.6
        }

    async def _innovative_analysis(self, query: str, context: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """创新分析"""
        return {
            "key_factors": ["创新机会", "技术可行性", "市场需求", "实施难度"],
            "recommendations": ["探索创新机会", "评估技术可行性", "验证市场需求"],
            "confidence": 0.9
        }

    async def _general_analysis(self, query: str, context: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """通用分析"""
        return {
            "key_factors": ["问题定义", "影响因素", "解决方案", "实施计划"],
            "recommendations": ["明确问题定义", "分析影响因素", "制定解决方案"],
            "confidence": 0.5
        }

    async def _make_strategy_decision(self, strategy_analysis: StrategyAnalysis, 
                                   query_analysis: Dict[str, Any]) -> StrategyDecision:
        """制定策略决策"""
        decision_id = f"decision_{int(time.time() * 1000)}"
        
        # 基于分析结果制定决策
        strategy_type = self._select_strategy_type(strategy_analysis)
        reasoning = self._generate_reasoning(strategy_analysis)
        alternatives = self._generate_alternatives(strategy_analysis)
        risk_assessment = self._assess_risk(strategy_analysis, query_analysis)
        
        # 计算决策置信度
        confidence = self._calculate_decision_confidence(strategy_analysis, risk_assessment)
        
        return StrategyDecision(
            strategy_name=strategy_type,
            strategy_type=strategy_type,
            confidence=confidence,
            reasoning="; ".join(reasoning),
            parameters={"decision_id": decision_id, "risk_assessment": risk_assessment},
            expected_outcome="策略执行成功",
            fallback_strategies=alternatives
        )

    def _select_strategy_type(self, analysis: StrategyAnalysis) -> str:
        """选择策略类型"""
        strategy_types = self.strategy_config.get("strategy_types", ["competitive", "collaborative", "adaptive", "innovative"])
        
        # 基于分析复杂度选择策略类型
        if analysis.complexity > 0.8:
            return "innovative"
        elif analysis.complexity > 0.6:
            return "competitive"
        elif analysis.complexity > 0.4:
            return "collaborative"
        else:
            return "adaptive"

    def _generate_reasoning(self, analysis: StrategyAnalysis) -> List[str]:
        """生成推理过程"""
        reasoning = []
        
        reasoning.append(f"基于{analysis.query_type}分析")
        reasoning.append(f"识别了{len(analysis.key_factors)}个关键因素")
        reasoning.append(f"提出了{len(analysis.recommendations)}项建议")
        
        return reasoning

    def _generate_alternatives(self, analysis: StrategyAnalysis) -> List[str]:
        """生成备选方案"""
        alternatives = []
        
        for i, recommendation in enumerate(analysis.recommendations):
            alternatives.append(f"方案{i+1}: {recommendation}")
        
        return alternatives

    def _assess_risk(self, analysis: StrategyAnalysis, query_analysis: Dict[str, Any]) -> float:
        """评估风险"""
        base_risk = 0.3
        
        # 基于复杂度调整风险
        complexity_risk = analysis.complexity * 0.4
        
        # 基于紧急程度调整风险
        urgency = query_analysis.get("urgency", "low")
        urgency_risk = {"high": 0.3, "medium": 0.2, "low": 0.1}[urgency]
        
        total_risk = base_risk + complexity_risk + urgency_risk
        return min(1.0, total_risk)

    def _calculate_decision_confidence(self, analysis: StrategyAnalysis, risk_assessment: float) -> float:
        """计算决策置信度"""
        base_confidence = analysis.confidence
        
        # 基于风险调整置信度
        risk_factor = 1.0 - (risk_assessment * 0.3)
        
        final_confidence = base_confidence * risk_factor
        return min(1.0, max(0.0, final_confidence))

    def _generate_strategy_recommendations(self, decision: StrategyDecision, 
                                        analysis: StrategyAnalysis) -> str:
        """生成策略建议"""
        recommendations = []
        
        # 添加主要建议
        recommendations.append(f"推荐策略类型: {decision.strategy_type}")
        recommendations.append(f"决策置信度: {decision.confidence:.2f}")
        recommendations.append(f"风险评估: {decision.parameters.get('risk_assessment', 0.5):.2f}")
        
        # 添加具体建议
        for recommendation in analysis.recommendations:
            recommendations.append(f"• {recommendation}")
        
        # 添加备选方案
        if decision.fallback_strategies:
            recommendations.append("备选方案:")
            for alternative in decision.fallback_strategies[:3]:  # 限制备选方案数量
                recommendations.append(f"  - {alternative}")
        
        return "\n".join(recommendations)

    def _calculate_strategy_confidence(self, analysis: StrategyAnalysis, 
                                     decision: StrategyDecision) -> float:
        """计算策略置信度"""
        analysis_confidence = analysis.confidence
        decision_confidence = decision.confidence
        
        # 综合置信度计算
        combined_confidence = (analysis_confidence * 0.6 + decision_confidence * 0.4)
        
        # 基于复杂度调整
        complexity_factor = 1.0 - (analysis.complexity * 0.2)
        
        final_confidence = combined_confidence * complexity_factor
        return min(1.0, max(0.0, final_confidence))

    def _update_average_confidence(self, confidence: float):
        """更新平均置信度"""
        total_queries = self.strategy_stats["total_queries"]
        current_avg = self.strategy_stats["average_confidence"]
        
        # 计算新的平均值
        new_avg = (current_avg * (total_queries - 1) + confidence) / total_queries
        self.strategy_stats["average_confidence"] = new_avg

    def _update_strategy_type_stats(self, strategy_type: str):
        """更新策略类型统计"""
        if strategy_type not in self.strategy_stats["strategy_types"]:
            self.strategy_stats["strategy_types"][strategy_type] = 0
        self.strategy_stats["strategy_types"][strategy_type] += 1

    def get_strategy_stats(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return self.strategy_stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.strategy_stats = {
            "total_queries": 0,
            "successful_strategies": 0,
            "failed_strategies": 0,
            "average_confidence": 0.0,
            "strategy_types": {},
            "decision_count": 0
        }

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.strategy_config.copy()

    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.strategy_config.update(config)
        
        # 更新阈值
        if "decision_threshold" in config:
            self.decision_threshold = config["decision_threshold"]
        if "analysis_threshold" in config:
            self.analysis_threshold = config["analysis_threshold"]

    async def _execute_core_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行核心任务"""
        return {"result": "策略任务执行完成", "status": "success"}
    
    def _validate_strategy_input(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """验证策略输入"""
        try:
            if not query or not query.strip():
                return False
            
            if len(query) > 1000:  # 限制查询长度
                return False
            
            if context and not isinstance(context, dict):
                return False
            
            return True
        except Exception:
            return False
    
    def _calculate_strategy_metrics(self, analysis: StrategyAnalysis, decision: StrategyDecision) -> Dict[str, Any]:
        """计算策略指标"""
        try:
            metrics = {
                "analysis_confidence": analysis.confidence,
                "decision_confidence": decision.confidence,
                "overall_confidence": (analysis.confidence + decision.confidence) / 2,
                "complexity_score": analysis.complexity,
                "key_factors_count": len(analysis.key_factors),
                "recommendations_count": len(analysis.recommendations),
                "strategy_type": decision.strategy_type,
                "risk_level": decision.parameters.get('risk_assessment', 0.5)
            }
            
            # 计算质量分数
            quality_score = (
                metrics["analysis_confidence"] * 0.3 +
                metrics["decision_confidence"] * 0.3 +
                (1.0 - metrics["risk_level"]) * 0.2 +
                min(1.0, metrics["key_factors_count"] / 5) * 0.1 +
                min(1.0, metrics["recommendations_count"] / 3) * 0.1
            )
            metrics["quality_score"] = quality_score
            
            return metrics
        except Exception as e:
            logger.error(f"计算策略指标失败: {e}")
            return {
                "analysis_confidence": 0.0,
                "decision_confidence": 0.0,
                "overall_confidence": 0.0,
                "quality_score": 0.0,
                "error": str(e)
            }
    
    def _generate_strategy_report(self, analysis: StrategyAnalysis, decision: StrategyDecision, 
                                metrics: Dict[str, Any]) -> str:
        """生成策略报告"""
        try:
            report_lines = []
            
            # 报告标题
            report_lines.append("=== 智能策略分析报告 ===")
            report_lines.append("")
            
            # 分析信息
            report_lines.append("## 分析信息")
            report_lines.append(f"分析ID: {analysis.analysis_id}")
            report_lines.append(f"查询类型: {analysis.query_type}")
            report_lines.append(f"复杂度: {analysis.complexity:.2f}")
            report_lines.append(f"分析置信度: {analysis.confidence:.2f}")
            report_lines.append("")
            
            # 关键因素
            report_lines.append("## 关键因素")
            for i, factor in enumerate(analysis.key_factors, 1):
                report_lines.append(f"{i}. {factor}")
            report_lines.append("")
            
            # 建议
            report_lines.append("## 策略建议")
            for i, recommendation in enumerate(analysis.recommendations, 1):
                report_lines.append(f"{i}. {recommendation}")
            report_lines.append("")
            
            # 决策信息
            report_lines.append("## 决策信息")
            report_lines.append(f"策略类型: {decision.strategy_type}")
            report_lines.append(f"决策置信度: {decision.confidence:.2f}")
            report_lines.append(f"风险评估: {decision.parameters.get('risk_assessment', 0.5):.2f}")
            report_lines.append("")
            
            # 指标
            report_lines.append("## 质量指标")
            report_lines.append(f"整体置信度: {metrics.get('overall_confidence', 0.0):.2f}")
            report_lines.append(f"质量分数: {metrics.get('quality_score', 0.0):.2f}")
            report_lines.append(f"关键因素数量: {metrics.get('key_factors_count', 0)}")
            report_lines.append(f"建议数量: {metrics.get('recommendations_count', 0)}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成策略报告失败: {e}")
            return f"策略报告生成失败: {str(e)}"
    
    def _optimize_strategy_performance(self) -> Dict[str, Any]:
        """优化策略性能"""
        try:
            stats = self.get_strategy_stats()
            config = self.get_config()
            
            optimizations = {}
            
            # 基于成功率优化决策阈值
            success_rate = stats["successful_strategies"] / max(1, stats["total_queries"])
            if success_rate < 0.6:
                optimizations["decision_threshold"] = max(0.5, config["decision_threshold"] - 0.1)
            elif success_rate > 0.9:
                optimizations["decision_threshold"] = min(0.9, config["decision_threshold"] + 0.05)
            
            # 基于平均置信度优化分析阈值
            avg_confidence = stats["average_confidence"]
            if avg_confidence < 0.5:
                optimizations["analysis_threshold"] = max(0.4, config["analysis_threshold"] - 0.1)
            elif avg_confidence > 0.8:
                optimizations["analysis_threshold"] = min(0.8, config["analysis_threshold"] + 0.05)
            
            # 基于策略类型分布优化策略类型权重
            strategy_types = stats["strategy_types"]
            if strategy_types:
                most_used = max(strategy_types, key=strategy_types.get)
                optimizations["preferred_strategy_type"] = most_used
            
            return {
                "optimizations": optimizations,
                "current_stats": stats,
                "recommendations": [
                    f"当前成功率: {success_rate:.2f}",
                    f"平均置信度: {avg_confidence:.2f}",
                    f"最常用策略: {max(strategy_types, key=strategy_types.get) if strategy_types else 'N/A'}"
                ]
            }
            
        except Exception as e:
            logger.error(f"优化策略性能失败: {e}")
            return {
                "optimizations": {},
                "error": str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        try:
            return {
                "name": self.agent_name,
                "is_executing": self.is_executing,
                "strategy_config_loaded": bool(self.strategy_config),
                "total_queries": self.strategy_stats["total_queries"],
                "success_rate": self.strategy_stats["successful_strategies"] / max(1, self.strategy_stats["total_queries"]),
                "average_confidence": self.strategy_stats["average_confidence"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取智能体状态失败: {e}")
            return {
                "name": self.agent_name,
                "is_executing": False,
                "error": str(e)
            }

# 全局实例
_intelligent_strategy_agent = None

def get_intelligent_strategy_agent() -> IntelligentStrategyAgent:
    """获取智能策略智能体实例"""
    global _intelligent_strategy_agent
    if _intelligent_strategy_agent is None:
        _intelligent_strategy_agent = IntelligentStrategyAgent()
    return _intelligent_strategy_agent

# 定义缺失的函数
def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """获取智能配置"""
    try:
        center = get_unified_center('get_unified_config_center')
        if center:
            return center.get_smart_config(key, context or {})
    except Exception:
        # 回退到默认配置
        return _get_default_config(key, context or {})
    
def _get_default_config(key: str, context: Dict[str, Any]) -> Any:
    """获取默认配置"""
    try:
        # 默认配置映射
        default_configs = {
            'strategy_type': 'adaptive',
            'learning_rate': 0.01,
            'max_iterations': 1000,
            'convergence_threshold': 0.001,
            'exploration_rate': 0.1,
            'exploitation_rate': 0.9,
            'memory_size': 10000,
            'batch_size': 32,
            'update_frequency': 100,
            'evaluation_interval': 50
        }
        
        # 根据上下文调整配置
        if context.get('high_performance', False):
            default_configs['learning_rate'] = 0.005
            default_configs['max_iterations'] = 2000
        
        if context.get('fast_convergence', False):
            default_configs['convergence_threshold'] = 0.01
            default_configs['update_frequency'] = 50
        
        return default_configs.get(key, None)
        
    except Exception:
        return None
    return None

def create_query_context(query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """创建查询上下文"""
    return {
        "query": query,
        "user_id": user_id,
        "timestamp": time.time(),
        "session_id": f"session_{int(time.time())}",
        "metadata": {}
    }

def get_intelligent_strategy_config() -> Dict[str, Any]:
    """获取智能策略配置"""
    try:
        center = get_unified_center('get_unified_config_center')
        if center:
            return center.get_strategy_config()
    except Exception:
        pass
    
    # 回退到默认配置
    return {
        "strategy_types": ["competitive", "collaborative", "adaptive", "innovative"],
        "decision_threshold": 0.7,
        "analysis_threshold": 0.6,
        "risk_tolerance": 0.5,
        "time_horizon": "medium",
        "max_analysis_depth": 5,
        "resource_constraints": [],
        "stakeholder_considerations": True
    }

def validate_strategy_input(query: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """验证策略输入"""
    try:
        if not query or not query.strip():
            return False
        
        if len(query) > 1000:  # 限制查询长度
            return False
        
        if context and not isinstance(context, dict):
            return False
        
        return True
    except Exception:
        return False

def calculate_strategy_metrics(analysis: StrategyAnalysis, decision: StrategyDecision) -> Dict[str, Any]:
    """计算策略指标"""
    try:
        metrics = {
            "analysis_confidence": analysis.confidence,
            "decision_confidence": decision.confidence,
            "overall_confidence": (analysis.confidence + decision.confidence) / 2,
            "complexity_score": analysis.complexity,
            "key_factors_count": len(analysis.key_factors),
            "recommendations_count": len(analysis.recommendations),
            "strategy_type": decision.strategy_type,
            "risk_level": decision.parameters.get('risk_assessment', 0.5)
        }
        
        # 计算质量分数
        quality_score = (
            metrics["analysis_confidence"] * 0.3 +
            metrics["decision_confidence"] * 0.3 +
            (1.0 - metrics["risk_level"]) * 0.2 +
            min(1.0, metrics["key_factors_count"] / 5) * 0.1 +
            min(1.0, metrics["recommendations_count"] / 3) * 0.1
        )
        metrics["quality_score"] = quality_score
        
        return metrics
    except Exception as e:
        logger.error(f"计算策略指标失败: {e}")
        return {
            "analysis_confidence": 0.0,
            "decision_confidence": 0.0,
            "overall_confidence": 0.0,
            "quality_score": 0.0,
            "error": str(e)
        }

def generate_strategy_report(analysis: StrategyAnalysis, decision: StrategyDecision, 
                           metrics: Dict[str, Any]) -> str:
    """生成策略报告"""
    try:
        report_lines = []
        
        # 报告标题
        report_lines.append("=== 智能策略分析报告 ===")
        report_lines.append("")
        
        # 分析信息
        report_lines.append("## 分析信息")
        report_lines.append(f"分析ID: {analysis.analysis_id}")
        report_lines.append(f"查询类型: {analysis.query_type}")
        report_lines.append(f"复杂度: {analysis.complexity:.2f}")
        report_lines.append(f"分析置信度: {analysis.confidence:.2f}")
        report_lines.append("")
        
        # 关键因素
        report_lines.append("## 关键因素")
        for i, factor in enumerate(analysis.key_factors, 1):
            report_lines.append(f"{i}. {factor}")
        report_lines.append("")
        
        # 建议
        report_lines.append("## 策略建议")
        for i, recommendation in enumerate(analysis.recommendations, 1):
            report_lines.append(f"{i}. {recommendation}")
        report_lines.append("")
        
        # 决策信息
        report_lines.append("## 决策信息")
        report_lines.append(f"策略类型: {decision.strategy_type}")
        report_lines.append(f"决策置信度: {decision.confidence:.2f}")
        report_lines.append(f"风险评估: {decision.parameters.get('risk_assessment', 0.5):.2f}")
        report_lines.append("")
        
        # 指标
        report_lines.append("## 质量指标")
        report_lines.append(f"整体置信度: {metrics.get('overall_confidence', 0.0):.2f}")
        report_lines.append(f"质量分数: {metrics.get('quality_score', 0.0):.2f}")
        report_lines.append(f"关键因素数量: {metrics.get('key_factors_count', 0)}")
        report_lines.append(f"建议数量: {metrics.get('recommendations_count', 0)}")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"生成策略报告失败: {e}")
        return f"策略报告生成失败: {str(e)}"

def optimize_strategy_performance(agent: IntelligentStrategyAgent) -> Dict[str, Any]:
    """优化策略性能"""
    try:
        stats = agent.get_strategy_stats()
        config = agent.get_config()
        
        optimizations = {}
        
        # 基于成功率优化决策阈值
        success_rate = stats["successful_strategies"] / max(1, stats["total_queries"])
        if success_rate < 0.6:
            optimizations["decision_threshold"] = max(0.5, config["decision_threshold"] - 0.1)
        elif success_rate > 0.9:
            optimizations["decision_threshold"] = min(0.9, config["decision_threshold"] + 0.05)
        
        # 基于平均置信度优化分析阈值
        avg_confidence = stats["average_confidence"]
        if avg_confidence < 0.5:
            optimizations["analysis_threshold"] = max(0.4, config["analysis_threshold"] - 0.1)
        elif avg_confidence > 0.8:
            optimizations["analysis_threshold"] = min(0.8, config["analysis_threshold"] + 0.05)
        
        # 基于策略类型分布优化策略类型权重
        strategy_types = stats["strategy_types"]
        if strategy_types:
            most_used = max(strategy_types, key=strategy_types.get)
            optimizations["preferred_strategy_type"] = most_used
        
        return {
            "optimizations": optimizations,
            "current_stats": stats,
            "recommendations": [
                f"当前成功率: {success_rate:.2f}",
                f"平均置信度: {avg_confidence:.2f}",
                f"最常用策略: {max(strategy_types, key=strategy_types.get) if strategy_types else 'N/A'}"
            ]
        }
        
    except Exception as e:
        logger.error(f"优化策略性能失败: {e}")
        return {
            "optimizations": {},
            "error": str(e)
        }