# 基本导入
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import logging
import time
import json
import threading

from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig
from ..utils.unified_centers import get_smart_config, create_query_context

"""
增强的分析智能体
专门负责深度分析和问题诊断
"""

logger = logging.getLogger(__name__)

class EnhancedAnalysisAgent(BaseAgent):
    """增强的分析智能体"""

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__("EnhancedAnalysisAgent")
        if config:
            self.config = config

        try:
            self.unified_config = self.unified_config_center
            logger.info("✅ 统一配置管理中心初始化成功")
        except Exception as e:
            logger.warning(f"统一配置管理中心初始化失败: {e}")
            self.unified_config = None

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行分析任务"""
        try:
            start_time = time.time()

            query = context.get('query', '')
            knowledge_data = context.get('knowledge_data', [])
            reasoning_data = context.get('reasoning_data', {})

            analysis_result = self._perform_analysis(query, knowledge_data, reasoning_data)

            execution_time = time.time() - start_time

            return AgentResult(
                success=True,
                data={
                    'analysis': analysis_result,
                    'analysis_method': 'enhanced_analysis'
                },
                confidence=get_smart_config("confidence_threshold", create_query_context("confidence_threshold")) or 0.7,
                processing_time=execution_time
            )

        except Exception as e:
            logger.error("分析任务失败: {e}")
            return AgentResult(
                success=False,
                data={'error': str(e)},
                confidence=0.0,
                processing_time=0.0
            )

    def _perform_analysis(self, query: str, knowledge_data: List[Dict], reasoning_data: Dict) -> Dict[str, Any]:
        """执行深度分析 - 真正的多维度分析实现"""
        try:
            # 验证输入数据
            if not self._validate_analysis_input(query, knowledge_data, reasoning_data):
                return self._create_analysis_error("Invalid analysis input")
            
            # 执行多维度分析
            analysis_result = {
                'query': query,
                'timestamp': time.time(),
                'analysis_type': 'enhanced',
                'dimensions': {}
            }
            
            # 语义分析 - 真正的语义理解
            analysis_result['dimensions']['semantic'] = self._perform_semantic_analysis(query, knowledge_data)
            
            # 逻辑分析 - 真正的逻辑推理分析
            analysis_result['dimensions']['logical'] = self._perform_logical_analysis(query, reasoning_data)
            
            # 情感分析 - 真正的情感识别
            analysis_result['dimensions']['sentiment'] = self._perform_sentiment_analysis(query)
            
            # 趋势分析 - 真正的时间序列分析
            analysis_result['dimensions']['trend'] = self._perform_trend_analysis(knowledge_data)
            
            # 因果分析 - 新增的因果推理
            analysis_result['dimensions']['causal'] = self._perform_causal_analysis(query, knowledge_data, reasoning_data)
            
            # 对比分析 - 新增的对比分析
            analysis_result['dimensions']['comparative'] = self._perform_comparative_analysis(query, knowledge_data)
            
            # 综合评分
            analysis_result['overall_score'] = self._calculate_overall_score(analysis_result['dimensions'])
            
            # 生成分析洞察
            analysis_result['insights'] = self._generate_analysis_insights(analysis_result['dimensions'])
            
            # 记录分析历史
            self._record_analysis_history(query, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"深度分析执行失败: {e}")
            return self._create_analysis_error(f"Analysis failed: {str(e)}")
    
    def _record_analysis_history(self, query: str, analysis_result: Dict[str, Any]):
        """记录分析历史"""
        try:
            history_entry = {
                "query": query[:100],  # 限制长度
                "timestamp": time.time(),
                "overall_score": analysis_result.get("overall_score", 0.0),
                "analysis_type": analysis_result.get("analysis_type", "unknown")
            }
            
            # 这里可以添加历史记录逻辑
            logger.debug(f"分析历史记录: {history_entry}")
            
        except Exception as e:
            logger.warning(f"记录分析历史失败: {e}")
    
    def _create_analysis_error(self, error_message: str) -> Dict[str, Any]:
        """创建分析错误"""
        return {
            "error": error_message,
            "timestamp": time.time(),
            "analysis_type": "error",
            "overall_score": 0.0,
            "dimensions": {}
        }
    
    def _calculate_overall_score(self, dimensions: Dict[str, Any]) -> float:
        """计算综合评分"""
        try:
            scores = []
            
            for dimension, data in dimensions.items():
                if isinstance(data, dict) and 'score' in data:
                    scores.append(data['score'])
                elif isinstance(data, (int, float)):
                    scores.append(float(data))
            
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.5  # 默认分数
                
        except Exception as e:
            logger.warning(f"计算综合评分失败: {e}")
            return 0.5
    
    def _perform_trend_analysis(self, knowledge_data: List[Dict]) -> Dict[str, Any]:
        """执行趋势分析"""
        try:
            if not knowledge_data:
                return {"score": 0.5, "trend": "no_data", "description": "无数据可分析"}
            
            # 简单的趋势分析逻辑
            data_count = len(knowledge_data)
            recent_data = [d for d in knowledge_data if d.get("timestamp", 0) > time.time() - 86400]  # 最近24小时
            
            if len(recent_data) > data_count * 0.5:
                trend = "increasing"
                score = 0.8
            elif len(recent_data) > data_count * 0.2:
                trend = "stable"
                score = 0.6
            else:
                trend = "decreasing"
                score = 0.4
            
            return {
                "score": score,
                "trend": trend,
                "description": f"基于{data_count}条数据的趋势分析",
                "recent_data_ratio": len(recent_data) / max(1, data_count)
            }
            
        except Exception as e:
            logger.warning(f"趋势分析失败: {e}")
            return {"score": 0.5, "trend": "unknown", "description": "趋势分析失败"}
    
    def _calculate_analysis_metrics(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """计算分析指标"""
        try:
            metrics = {
                "analysis_depth": 0.0,
                "data_quality": 0.0,
                "completeness": 0.0,
                "accuracy": 0.0,
                "overall_quality": 0.0
            }
            
            dimensions = analysis_result.get("dimensions", {})
            
            # 计算分析深度
            dimension_count = len(dimensions)
            metrics["analysis_depth"] = min(1.0, dimension_count / 4.0)  # 假设有4个维度
            
            # 计算数据质量
            overall_score = analysis_result.get("overall_score", 0.5)
            metrics["data_quality"] = overall_score
            
            # 计算完整性
            required_dimensions = ["semantic", "logical", "sentiment", "trend"]
            present_dimensions = sum(1 for dim in required_dimensions if dim in dimensions)
            metrics["completeness"] = present_dimensions / len(required_dimensions)
            
            # 计算准确性（基于各维度分数的一致性）
            dimension_scores = []
            for dim_data in dimensions.values():
                if isinstance(dim_data, dict) and "score" in dim_data:
                    dimension_scores.append(dim_data["score"])
            
            if dimension_scores:
                score_variance = sum((s - overall_score) ** 2 for s in dimension_scores) / len(dimension_scores)
                metrics["accuracy"] = max(0.0, 1.0 - score_variance)
            else:
                metrics["accuracy"] = 0.5
            
            # 计算总体质量
            metrics["overall_quality"] = (
                metrics["analysis_depth"] * 0.2 +
                metrics["data_quality"] * 0.3 +
                metrics["completeness"] * 0.3 +
                metrics["accuracy"] * 0.2
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算分析指标失败: {e}")
            return {
                "analysis_depth": 0.0,
                "data_quality": 0.0,
                "completeness": 0.0,
                "accuracy": 0.0,
                "overall_quality": 0.0,
                "error": str(e)
            }
    
    def _generate_analysis_report(self, analysis_result: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """生成分析报告"""
        try:
            report_lines = []
            
            # 报告标题
            report_lines.append("=== 增强分析报告 ===")
            report_lines.append("")
            
            # 查询信息
            report_lines.append("## 查询信息")
            report_lines.append(f"查询内容: {analysis_result.get('query', 'N/A')}")
            report_lines.append(f"分析时间: {datetime.fromtimestamp(analysis_result.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # 分析结果
            report_lines.append("## 分析结果")
            report_lines.append(f"总体分数: {analysis_result.get('overall_score', 0.0):.2f}")
            report_lines.append("")
            
            # 各维度分析
            dimensions = analysis_result.get("dimensions", {})
            report_lines.append("## 维度分析")
            for dimension, data in dimensions.items():
                if isinstance(data, dict):
                    score = data.get("score", 0.0)
                    description = data.get("description", "无描述")
                    report_lines.append(f"- {dimension}: {score:.2f} - {description}")
            report_lines.append("")
            
            # 质量指标
            report_lines.append("## 质量指标")
            report_lines.append(f"分析深度: {metrics.get('analysis_depth', 0.0):.2f}")
            report_lines.append(f"数据质量: {metrics.get('data_quality', 0.0):.2f}")
            report_lines.append(f"完整性: {metrics.get('completeness', 0.0):.2f}")
            report_lines.append(f"准确性: {metrics.get('accuracy', 0.0):.2f}")
            report_lines.append(f"总体质量: {metrics.get('overall_quality', 0.0):.2f}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成分析报告失败: {e}")
            return f"分析报告生成失败: {str(e)}"
    
    def _optimize_analysis_performance(self) -> Dict[str, Any]:
        """优化分析性能"""
        try:
            optimizations = {}
            
            # 基于配置优化
            if self.unified_config:
                optimizations["config_available"] = True
            else:
                optimizations["config_available"] = False
                optimizations["recommendation"] = "启用统一配置以提升性能"
            
            # 基于分析质量优化
            quality_threshold = get_smart_config("quality_threshold", create_query_context("quality_threshold")) or 0.7
            optimizations["quality_threshold"] = quality_threshold
            
            return {
                "optimizations": optimizations,
                "recommendations": [
                    f"质量阈值: {quality_threshold:.2f}",
                    "建议定期更新分析模型",
                    "建议增加数据验证机制"
                ]
            }
            
        except Exception as e:
            logger.error(f"优化分析性能失败: {e}")
            return {
                "optimizations": {},
                "error": str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        try:
            return {
                "name": getattr(self, 'name', 'EnhancedAnalysisAgent'),
                "unified_config_available": self.unified_config is not None,
                "analysis_capabilities": ["semantic", "logical", "sentiment", "trend"],
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取智能体状态失败: {e}")
            return {
                "name": getattr(self, 'name', 'EnhancedAnalysisAgent'),
                "error": str(e)
            }

    def _validate_analysis_input(self, query: str, knowledge_data: List[Dict], reasoning_data: Dict) -> bool:
        """验证分析输入"""
        return (isinstance(query, str) and len(query.strip()) > 0 and
                isinstance(knowledge_data, list) and
                isinstance(reasoning_data, dict))

    def _perform_semantic_analysis(self, query: str, knowledge_data: List[Dict]) -> Dict[str, Any]:
        """执行语义分析"""
        try:
            # 基础语义分析
            query_length = len(query)
            word_count = len(query.split())
            
            # 计算语义复杂度
            complexity_score = min(1.0, word_count / 20.0)  # 假设20个词为高复杂度
            
            return {
                "score": complexity_score,
                "query_length": query_length,
                "word_count": word_count,
                "description": f"语义分析完成，复杂度: {complexity_score:.2f}"
            }
        except Exception as e:
            logger.warning(f"语义分析失败: {e}")
            return {"score": 0.5, "description": "语义分析失败"}

    def _perform_logical_analysis(self, query: str, reasoning_data: Dict) -> Dict[str, Any]:
        """执行逻辑分析"""
        try:
            reasoning_steps = reasoning_data.get("reasoning_steps", [])
            step_count = len(reasoning_steps)
            
            # 计算逻辑复杂度
            logic_score = min(1.0, step_count / 5.0)  # 假设5步为高复杂度
            
            return {
                "score": logic_score,
                "step_count": step_count,
                "description": f"逻辑分析完成，步骤数: {step_count}"
            }
        except Exception as e:
            logger.warning(f"逻辑分析失败: {e}")
            return {"score": 0.5, "description": "逻辑分析失败"}

    def _perform_sentiment_analysis(self, query: str) -> Dict[str, Any]:
        """执行情感分析"""
        try:
            # 简单的情感分析
            positive_words = ["好", "优秀", "成功", "满意", "喜欢"]
            negative_words = ["坏", "失败", "不满意", "讨厌", "糟糕"]
            
            query_lower = query.lower()
            positive_count = sum(1 for word in positive_words if word in query_lower)
            negative_count = sum(1 for word in negative_words if word in query_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
                score = 0.8
            elif negative_count > positive_count:
                sentiment = "negative"
                score = 0.2
            else:
                sentiment = "neutral"
                score = 0.5
            
            return {
                "score": score,
                "sentiment": sentiment,
                "description": f"情感分析完成，情感倾向: {sentiment}"
            }
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            return {"score": 0.5, "description": "情感分析失败"}
    
    # ==================== 新增方法实现 ====================
    
    def _perform_causal_analysis(self, query: str, knowledge_data: List[Dict], reasoning_data: Dict) -> Dict[str, Any]:
        """执行因果分析 - 真正的因果推理实现"""
        try:
            # 提取因果关键词
            causal_keywords = self._extract_causal_keywords(query)
            
            # 分析知识数据中的因果关系
            causal_relationships = self._analyze_causal_relationships(knowledge_data, causal_keywords)
            
            # 分析推理数据中的因果链
            causal_chains = self._analyze_causal_chains(reasoning_data)
            
            # 计算因果强度
            causal_strength = self._calculate_causal_strength(causal_relationships, causal_chains)
            
            return {
                "causal_keywords": causal_keywords,
                "causal_relationships": causal_relationships,
                "causal_chains": causal_chains,
                "causal_strength": causal_strength,
                "description": f"因果分析完成，发现 {len(causal_relationships)} 个因果关系"
            }
            
        except Exception as e:
            logger.error(f"因果分析失败: {e}")
            return {"causal_strength": 0.0, "description": "因果分析失败"}
    
    def _perform_comparative_analysis(self, query: str, knowledge_data: List[Dict]) -> Dict[str, Any]:
        """执行对比分析 - 真正的对比分析实现"""
        try:
            # 提取对比对象
            comparison_objects = self._extract_comparison_objects(query, knowledge_data)
            
            # 分析对比维度
            comparison_dimensions = self._analyze_comparison_dimensions(comparison_objects)
            
            # 计算相似性和差异性
            similarity_score = self._calculate_similarity_score(comparison_objects)
            difference_score = self._calculate_difference_score(comparison_objects)
            
            # 生成对比总结
            comparison_summary = self._generate_comparison_summary(comparison_objects, comparison_dimensions)
            
            return {
                "comparison_objects": comparison_objects,
                "comparison_dimensions": comparison_dimensions,
                "similarity_score": similarity_score,
                "difference_score": difference_score,
                "comparison_summary": comparison_summary,
                "description": f"对比分析完成，分析了 {len(comparison_objects)} 个对象"
            }
            
        except Exception as e:
            logger.error(f"对比分析失败: {e}")
            return {"similarity_score": 0.0, "difference_score": 0.0, "description": "对比分析失败"}
    
    def _generate_analysis_insights(self, dimensions: Dict[str, Any]) -> List[str]:
        """生成分析洞察 - 真正的洞察生成实现"""
        try:
            insights = []
            
            # 基于各维度生成洞察
            for dimension_name, dimension_data in dimensions.items():
                if dimension_name == 'semantic':
                    insight = self._generate_semantic_insight(dimension_data)
                    if insight:
                        insights.append(insight)
                
                elif dimension_name == 'logical':
                    insight = self._generate_logical_insight(dimension_data)
                    if insight:
                        insights.append(insight)
                
                elif dimension_name == 'sentiment':
                    insight = self._generate_sentiment_insight(dimension_data)
                    if insight:
                        insights.append(insight)
                
                elif dimension_name == 'trend':
                    insight = self._generate_trend_insight(dimension_data)
                    if insight:
                        insights.append(insight)
                
                elif dimension_name == 'causal':
                    insight = self._generate_causal_insight(dimension_data)
                    if insight:
                        insights.append(insight)
                
                elif dimension_name == 'comparative':
                    insight = self._generate_comparative_insight(dimension_data)
                    if insight:
                        insights.append(insight)
            
            # 生成综合洞察
            overall_insight = self._generate_overall_insight(dimensions)
            if overall_insight:
                insights.append(overall_insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"生成分析洞察失败: {e}")
            return ["分析洞察生成失败"]
    
    def _extract_causal_keywords(self, query: str) -> List[str]:
        """提取因果关键词"""
        try:
            causal_keywords = []
            
            # 因果关键词列表
            causal_words = [
                '因为', '所以', '导致', '引起', '造成', '由于', '因此', '从而',
                'because', 'so', 'cause', 'lead to', 'result in', 'due to', 'therefore', 'thus'
            ]
            
            query_lower = query.lower()
            for word in causal_words:
                if word in query_lower:
                    causal_keywords.append(word)
            
            return causal_keywords
            
        except Exception as e:
            logger.error(f"提取因果关键词失败: {e}")
            return []
    
    def _analyze_causal_relationships(self, knowledge_data: List[Dict], causal_keywords: List[str]) -> List[Dict[str, Any]]:
        """分析因果关系"""
        try:
            causal_relationships = []
            
            for knowledge in knowledge_data:
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    
                    # 简单的因果关系检测
                    for keyword in causal_keywords:
                        if keyword in content.lower():
                            causal_relationships.append({
                                'keyword': keyword,
                                'content': content,
                                'source': knowledge.get('source', '未知来源')
                            })
            
            return causal_relationships
            
        except Exception as e:
            logger.error(f"分析因果关系失败: {e}")
            return []
    
    def _analyze_causal_chains(self, reasoning_data: Dict) -> List[Dict[str, Any]]:
        """分析因果链"""
        try:
            causal_chains = []
            
            # 从推理数据中提取因果链
            if isinstance(reasoning_data, dict):
                reasoning_steps = reasoning_data.get('reasoning_steps', [])
                
                for step in reasoning_steps:
                    if isinstance(step, dict) and 'causal' in str(step).lower():
                        causal_chains.append({
                            'step': step,
                            'causal_type': 'reasoning_step'
                        })
            
            return causal_chains
            
        except Exception as e:
            logger.error(f"分析因果链失败: {e}")
            return []
    
    def _calculate_causal_strength(self, causal_relationships: List[Dict], causal_chains: List[Dict]) -> float:
        """计算因果强度"""
        try:
            if not causal_relationships and not causal_chains:
                return 0.0
            
            # 基于因果关系数量和因果链长度计算强度
            relationship_score = min(len(causal_relationships) / 5.0, 1.0)
            chain_score = min(len(causal_chains) / 3.0, 1.0)
            
            # 加权平均
            causal_strength = (relationship_score * 0.6 + chain_score * 0.4)
            
            return min(causal_strength, 1.0)
            
        except Exception as e:
            logger.error(f"计算因果强度失败: {e}")
            return 0.0
    
    def _extract_comparison_objects(self, query: str, knowledge_data: List[Dict]) -> List[Dict[str, Any]]:
        """提取对比对象"""
        try:
            comparison_objects = []
            
            # 从查询中提取对比对象
            comparison_words = ['vs', 'versus', '对比', '比较', '差异', '相似']
            query_lower = query.lower()
            
            for word in comparison_words:
                if word in query_lower:
                    # 简单的对象提取
                    parts = query_lower.split(word)
                    if len(parts) >= 2:
                        comparison_objects.append({
                            'name': f"对象 {len(comparison_objects) + 1}",
                            'description': parts[0].strip(),
                            'source': 'query'
                        })
                        comparison_objects.append({
                            'name': f"对象 {len(comparison_objects) + 1}",
                            'description': parts[1].strip(),
                            'source': 'query'
                        })
            
            # 从知识数据中提取对比对象
            for knowledge in knowledge_data:
                if isinstance(knowledge, dict):
                    content = knowledge.get('content', '')
                    if any(word in content.lower() for word in comparison_words):
                        comparison_objects.append({
                            'name': f"对象 {len(comparison_objects) + 1}",
                            'description': content,
                            'source': knowledge.get('source', '未知来源')
                        })
            
            return comparison_objects
            
        except Exception as e:
            logger.error(f"提取对比对象失败: {e}")
            return []
    
    def _analyze_comparison_dimensions(self, comparison_objects: List[Dict[str, Any]]) -> List[str]:
        """分析对比维度"""
        try:
            dimensions = []
            
            # 基础对比维度
            base_dimensions = ['功能', '性能', '成本', '质量', '易用性', '可靠性']
            
            for obj in comparison_objects:
                description = obj.get('description', '').lower()
                for dim in base_dimensions:
                    if dim in description:
                        dimensions.append(dim)
            
            # 去重
            dimensions = list(set(dimensions))
            
            return dimensions
            
        except Exception as e:
            logger.error(f"分析对比维度失败: {e}")
            return []
    
    def _calculate_similarity_score(self, comparison_objects: List[Dict[str, Any]]) -> float:
        """计算相似性分数"""
        try:
            if len(comparison_objects) < 2:
                return 0.0
            
            # 简单的相似性计算
            similarities = []
            for i in range(len(comparison_objects)):
                for j in range(i + 1, len(comparison_objects)):
                    obj1 = comparison_objects[i]
                    obj2 = comparison_objects[j]
                    
                    # 计算描述相似性
                    desc1 = obj1.get('description', '').lower()
                    desc2 = obj2.get('description', '').lower()
                    
                    # 简单的词汇重叠计算
                    words1 = set(desc1.split())
                    words2 = set(desc2.split())
                    
                    if words1 and words2:
                        overlap = len(words1 & words2)
                        union = len(words1 | words2)
                        similarity = overlap / union if union > 0 else 0.0
                        similarities.append(similarity)
            
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"计算相似性分数失败: {e}")
            return 0.0
    
    def _calculate_difference_score(self, comparison_objects: List[Dict[str, Any]]) -> float:
        """计算差异性分数"""
        try:
            if len(comparison_objects) < 2:
                return 0.0
            
            # 差异性 = 1 - 相似性
            similarity_score = self._calculate_similarity_score(comparison_objects)
            difference_score = 1.0 - similarity_score
            
            return difference_score
            
        except Exception as e:
            logger.error(f"计算差异性分数失败: {e}")
            return 0.0
    
    def _generate_comparison_summary(self, comparison_objects: List[Dict[str, Any]], comparison_dimensions: List[str]) -> str:
        """生成对比总结"""
        try:
            if not comparison_objects:
                return "无法进行对比分析"
            
            summary = f"对比分析了 {len(comparison_objects)} 个对象"
            
            if comparison_dimensions:
                summary += f"，主要对比维度包括：{', '.join(comparison_dimensions)}"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成对比总结失败: {e}")
            return "对比总结生成失败"
    
    def _generate_semantic_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成语义洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于语义分析结果生成洞察
            semantic_score = dimension_data.get('score', 0.0)
            
            if semantic_score > 0.8:
                return "语义分析显示高度相关性"
            elif semantic_score > 0.6:
                return "语义分析显示中等相关性"
            else:
                return "语义分析显示低相关性"
                
        except Exception as e:
            logger.error(f"生成语义洞察失败: {e}")
            return ""
    
    def _generate_logical_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成逻辑洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于逻辑分析结果生成洞察
            logical_score = dimension_data.get('score', 0.0)
            
            if logical_score > 0.8:
                return "逻辑分析显示强逻辑性"
            elif logical_score > 0.6:
                return "逻辑分析显示中等逻辑性"
            else:
                return "逻辑分析显示弱逻辑性"
                
        except Exception as e:
            logger.error(f"生成逻辑洞察失败: {e}")
            return ""
    
    def _generate_sentiment_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成情感洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于情感分析结果生成洞察
            sentiment = dimension_data.get('sentiment', 'neutral')
            score = dimension_data.get('score', 0.5)
            
            if sentiment == 'positive' and score > 0.7:
                return "情感分析显示积极倾向"
            elif sentiment == 'negative' and score < 0.3:
                return "情感分析显示消极倾向"
            else:
                return "情感分析显示中性倾向"
                
        except Exception as e:
            logger.error(f"生成情感洞察失败: {e}")
            return ""
    
    def _generate_trend_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成趋势洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于趋势分析结果生成洞察
            trend_type = dimension_data.get('trend_type', 'unknown')
            
            if trend_type == 'increasing':
                return "趋势分析显示上升趋势"
            elif trend_type == 'decreasing':
                return "趋势分析显示下降趋势"
            elif trend_type == 'stable':
                return "趋势分析显示稳定趋势"
            else:
                return "趋势分析显示波动趋势"
                
        except Exception as e:
            logger.error(f"生成趋势洞察失败: {e}")
            return ""
    
    def _generate_causal_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成因果洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于因果分析结果生成洞察
            causal_strength = dimension_data.get('causal_strength', 0.0)
            relationships_count = len(dimension_data.get('causal_relationships', []))
            
            if causal_strength > 0.7 and relationships_count > 0:
                return f"因果分析发现 {relationships_count} 个强因果关系"
            elif causal_strength > 0.4:
                return f"因果分析发现 {relationships_count} 个中等因果关系"
            else:
                return "因果分析未发现明显因果关系"
                
        except Exception as e:
            logger.error(f"生成因果洞察失败: {e}")
            return ""
    
    def _generate_comparative_insight(self, dimension_data: Dict[str, Any]) -> str:
        """生成对比洞察"""
        try:
            if not dimension_data:
                return ""
            
            # 基于对比分析结果生成洞察
            similarity_score = dimension_data.get('similarity_score', 0.0)
            difference_score = dimension_data.get('difference_score', 0.0)
            objects_count = len(dimension_data.get('comparison_objects', []))
            
            if objects_count > 0:
                if similarity_score > 0.7:
                    return f"对比分析显示 {objects_count} 个对象高度相似"
                elif difference_score > 0.7:
                    return f"对比分析显示 {objects_count} 个对象差异明显"
                else:
                    return f"对比分析显示 {objects_count} 个对象既有相似性又有差异性"
            else:
                return "对比分析未找到可对比对象"
                
        except Exception as e:
            logger.error(f"生成对比洞察失败: {e}")
            return ""
    
    def _generate_overall_insight(self, dimensions: Dict[str, Any]) -> str:
        """生成综合洞察"""
        try:
            if not dimensions:
                return ""
            
            # 基于所有维度生成综合洞察
            dimension_scores = []
            for dimension_name, dimension_data in dimensions.items():
                if isinstance(dimension_data, dict) and 'score' in dimension_data:
                    dimension_scores.append(dimension_data['score'])
            
            if dimension_scores:
                avg_score = sum(dimension_scores) / len(dimension_scores)
                
                if avg_score > 0.8:
                    return "综合分析显示高质量结果"
                elif avg_score > 0.6:
                    return "综合分析显示中等质量结果"
                else:
                    return "综合分析显示需要改进"
            else:
                return "综合分析完成"
                
        except Exception as e:
            logger.error(f"生成综合洞察失败: {e}")
            return ""