"""
推理分析器
分析系统推理能力，包括逻辑推理、因果推理、类比推理等
"""

import re
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer

class ReasoningAnalyzer(BaseAnalyzer):
    """推理分析器"""
    
    def __init__(self):
        super().__init__("ReasoningAnalyzer")
    
    def analyze(self, log_content: str) -> Dict[str, Any]:
        """分析推理能力指标"""
        return {
            "logical_reasoning": self._analyze_logical_reasoning(log_content),
            "causal_reasoning": self._analyze_causal_reasoning(log_content),
            "analogical_reasoning": self._analyze_analogical_reasoning(log_content),
            "abductive_reasoning": self._analyze_abductive_reasoning(log_content),
            "spatial_reasoning": self._analyze_spatial_reasoning(log_content),
            "temporal_reasoning": self._analyze_temporal_reasoning(log_content),
            "overall_reasoning": self._calculate_overall_reasoning(log_content)
        }
    
    def _analyze_logical_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析逻辑推理能力"""
        # 逻辑推理关键词
        logical_keywords = [
            "逻辑推理", "logical reasoning", "逻辑", "logic",
            "演绎", "deduction", "演绎推理", "deductive reasoning",
            "归纳", "induction", "归纳推理", "inductive reasoning",
            "前提", "premise", "结论", "conclusion",
            "推理规则", "reasoning rule", "逻辑规则", "logical rule",
            "真值", "truth value", "有效性", "validity"
        ]
        
        logical_indicators = self._extract_pattern_matches(log_content, logical_keywords, case_sensitive=False)
        
        # 分析推理步骤
        step_patterns = [
            r"推理步骤数: (\d+)",
            r"reasoning steps: (\d+)",
            r"逻辑步骤: (\d+)"
        ]
        
        reasoning_steps = self._extract_numeric_values(log_content, step_patterns)
        step_stats = self._calculate_statistics(reasoning_steps)
        
        # 分析推理复杂度
        complexity_indicators = [
            "复杂推理", "complex reasoning", "多步推理", "multi-step reasoning",
            "嵌套推理", "nested reasoning", "递归推理", "recursive reasoning"
        ]
        
        complexity_count = len(self._extract_pattern_matches(log_content, complexity_indicators, case_sensitive=False))
        
        return {
            "logical_indicators": len(logical_indicators),
            "reasoning_steps": step_stats,
            "complexity_indicators": complexity_count,
            "logical_reasoning_score": min(1.0, len(logical_indicators) / 50.0)
        }
    
    def _analyze_causal_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析因果推理能力"""
        # 因果推理关键词
        causal_keywords = [
            "因果推理", "causal reasoning", "因果关系", "causality",
            "原因", "cause", "结果", "effect", "因果链", "causal chain",
            "因果分析", "causal analysis", "因果模型", "causal model",
            "反事实", "counterfactual", "反事实推理", "counterfactual reasoning",
            "因果推断", "causal inference", "因果发现", "causal discovery"
        ]
        
        causal_indicators = self._extract_pattern_matches(log_content, causal_keywords, case_sensitive=False)
        
        # 分析因果链长度
        chain_patterns = [
            r"因果链长度: (\d+)",
            r"causal chain length: (\d+)",
            r"因果步骤: (\d+)"
        ]
        
        chain_lengths = self._extract_numeric_values(log_content, chain_patterns)
        chain_stats = self._calculate_statistics(chain_lengths)
        
        # 分析因果强度
        strength_patterns = [
            r"因果强度: (\d+\.?\d*)",
            r"causal strength: (\d+\.?\d*)",
            r"关联度: (\d+\.?\d*)"
        ]
        
        strength_scores = self._extract_numeric_values(log_content, strength_patterns)
        strength_stats = self._calculate_statistics(strength_scores)
        
        return {
            "causal_indicators": len(causal_indicators),
            "chain_lengths": chain_stats,
            "strength_scores": strength_stats,
            "causal_reasoning_score": min(1.0, len(causal_indicators) / 30.0)
        }
    
    def _analyze_analogical_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析类比推理能力"""
        # 类比推理关键词
        analogical_keywords = [
            "类比推理", "analogical reasoning", "类比", "analogy",
            "相似性", "similarity", "相似", "similar",
            "映射", "mapping", "对应", "correspondence",
            "类比映射", "analogical mapping", "结构映射", "structure mapping",
            "类比检索", "analogical retrieval", "类比匹配", "analogical matching"
        ]
        
        analogical_indicators = self._extract_pattern_matches(log_content, analogical_keywords, case_sensitive=False)
        
        # 分析类比相似度
        similarity_patterns = [
            r"相似度: (\d+\.?\d*)",
            r"similarity: (\d+\.?\d*)",
            r"类比度: (\d+\.?\d*)"
        ]
        
        similarity_scores = self._extract_numeric_values(log_content, similarity_patterns)
        similarity_stats = self._calculate_statistics(similarity_scores)
        
        # 分析类比数量
        analogy_patterns = [
            r"类比数量: (\d+)",
            r"analogy count: (\d+)",
            r"找到类比: (\d+)"
        ]
        
        analogy_counts = self._extract_numeric_values(log_content, analogy_patterns)
        count_stats = self._calculate_statistics(analogy_counts)
        
        return {
            "analogical_indicators": len(analogical_indicators),
            "similarity_scores": similarity_stats,
            "analogy_counts": count_stats,
            "analogical_reasoning_score": min(1.0, len(analogical_indicators) / 25.0)
        }
    
    def _analyze_abductive_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析溯因推理能力"""
        # 溯因推理关键词
        abductive_keywords = [
            "溯因推理", "abductive reasoning", "溯因", "abduction",
            "假设", "hypothesis", "假设生成", "hypothesis generation",
            "最佳解释", "best explanation", "解释推理", "explanatory reasoning",
            "溯因推断", "abductive inference", "溯因发现", "abductive discovery",
            "解释力", "explanatory power", "解释质量", "explanation quality"
        ]
        
        abductive_indicators = self._extract_pattern_matches(log_content, abductive_keywords, case_sensitive=False)
        
        # 分析假设质量
        hypothesis_patterns = [
            r"假设质量: (\d+\.?\d*)",
            r"hypothesis quality: (\d+\.?\d*)",
            r"解释力: (\d+\.?\d*)"
        ]
        
        hypothesis_scores = self._extract_numeric_values(log_content, hypothesis_patterns)
        hypothesis_stats = self._calculate_statistics(hypothesis_scores)
        
        # 分析假设数量
        hypothesis_count_patterns = [
            r"假设数量: (\d+)",
            r"hypothesis count: (\d+)",
            r"生成假设: (\d+)"
        ]
        
        hypothesis_counts = self._extract_numeric_values(log_content, hypothesis_count_patterns)
        count_stats = self._calculate_statistics(hypothesis_counts)
        
        return {
            "abductive_indicators": len(abductive_indicators),
            "hypothesis_scores": hypothesis_stats,
            "hypothesis_counts": count_stats,
            "abductive_reasoning_score": min(1.0, len(abductive_indicators) / 20.0)
        }
    
    def _analyze_spatial_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析空间推理能力"""
        # 空间推理关键词
        spatial_keywords = [
            "空间推理", "spatial reasoning", "空间", "spatial",
            "位置", "position", "方向", "direction", "距离", "distance",
            "空间关系", "spatial relation", "空间布局", "spatial layout",
            "空间变换", "spatial transformation", "空间映射", "spatial mapping",
            "几何推理", "geometric reasoning", "空间认知", "spatial cognition"
        ]
        
        spatial_indicators = self._extract_pattern_matches(log_content, spatial_keywords, case_sensitive=False)
        
        # 分析空间复杂度
        complexity_patterns = [
            r"空间复杂度: (\d+\.?\d*)",
            r"spatial complexity: (\d+\.?\d*)",
            r"几何复杂度: (\d+\.?\d*)"
        ]
        
        complexity_scores = self._extract_numeric_values(log_content, complexity_patterns)
        complexity_stats = self._calculate_statistics(complexity_scores)
        
        # 分析空间操作
        operation_patterns = [
            r"空间操作: (\d+)",
            r"spatial operations: (\d+)",
            r"几何操作: (\d+)"
        ]
        
        operation_counts = self._extract_numeric_values(log_content, operation_patterns)
        operation_stats = self._calculate_statistics(operation_counts)
        
        return {
            "spatial_indicators": len(spatial_indicators),
            "complexity_scores": complexity_stats,
            "operation_counts": operation_stats,
            "spatial_reasoning_score": min(1.0, len(spatial_indicators) / 20.0)
        }
    
    def _analyze_temporal_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析时间推理能力"""
        # 时间推理关键词
        temporal_keywords = [
            "时间推理", "temporal reasoning", "时间", "temporal",
            "时序", "sequence", "时间序列", "time series",
            "时间关系", "temporal relation", "时间顺序", "temporal order",
            "时间因果", "temporal causality", "时间模式", "temporal pattern",
            "时间预测", "temporal prediction", "时间推断", "temporal inference"
        ]
        
        temporal_indicators = self._extract_pattern_matches(log_content, temporal_keywords, case_sensitive=False)
        
        # 分析时间序列长度
        sequence_patterns = [
            r"时间序列长度: (\d+)",
            r"sequence length: (\d+)",
            r"时序长度: (\d+)"
        ]
        
        sequence_lengths = self._extract_numeric_values(log_content, sequence_patterns)
        sequence_stats = self._calculate_statistics(sequence_lengths)
        
        # 分析时间预测准确率
        prediction_patterns = [
            r"时间预测准确率: (\d+\.?\d*)",
            r"temporal prediction accuracy: (\d+\.?\d*)",
            r"时序预测: (\d+\.?\d*)"
        ]
        
        prediction_scores = self._extract_numeric_values(log_content, prediction_patterns)
        prediction_stats = self._calculate_statistics(prediction_scores)
        
        return {
            "temporal_indicators": len(temporal_indicators),
            "sequence_lengths": sequence_stats,
            "prediction_scores": prediction_stats,
            "temporal_reasoning_score": min(1.0, len(temporal_indicators) / 20.0)
        }
    
    def _calculate_overall_reasoning(self, log_content: str) -> Dict[str, Any]:
        """计算整体推理能力"""
        # 获取各维度推理分析结果
        logical = self._analyze_logical_reasoning(log_content)
        causal = self._analyze_causal_reasoning(log_content)
        analogical = self._analyze_analogical_reasoning(log_content)
        abductive = self._analyze_abductive_reasoning(log_content)
        spatial = self._analyze_spatial_reasoning(log_content)
        temporal = self._analyze_temporal_reasoning(log_content)
        
        # 计算各维度推理分数
        reasoning_scores = {
            "logical": logical["logical_reasoning_score"],
            "causal": causal["causal_reasoning_score"],
            "analogical": analogical["analogical_reasoning_score"],
            "abductive": abductive["abductive_reasoning_score"],
            "spatial": spatial["spatial_reasoning_score"],
            "temporal": temporal["temporal_reasoning_score"]
        }
        
        # 计算整体推理分数
        overall_score = sum(reasoning_scores.values()) / len(reasoning_scores)
        
        # 分析推理类型分布
        reasoning_distribution = self._analyze_reasoning_distribution(log_content)
        
        return {
            "overall_reasoning_score": overall_score,
            "reasoning_scores": reasoning_scores,
            "reasoning_distribution": reasoning_distribution,
            "reasoning_level": self._classify_reasoning_level(overall_score),
            "strongest_reasoning_type": max(reasoning_scores, key=reasoning_scores.get),
            "weakest_reasoning_type": min(reasoning_scores, key=reasoning_scores.get)
        }
    
    def _analyze_reasoning_distribution(self, log_content: str) -> Dict[str, int]:
        """分析推理类型分布"""
        reasoning_types = {
            "logical": ["逻辑推理", "logical reasoning", "演绎", "归纳"],
            "causal": ["因果推理", "causal reasoning", "因果关系", "因果分析"],
            "analogical": ["类比推理", "analogical reasoning", "类比", "相似性"],
            "abductive": ["溯因推理", "abductive reasoning", "假设", "最佳解释"],
            "spatial": ["空间推理", "spatial reasoning", "空间", "几何"],
            "temporal": ["时间推理", "temporal reasoning", "时间", "时序"]
        }
        
        distribution = {}
        for reasoning_type, keywords in reasoning_types.items():
            count = 0
            for keyword in keywords:
                pattern = f"\\b{re.escape(keyword)}\\b"
                matches = self._extract_pattern_matches(log_content, [pattern], case_sensitive=False)
                count += len(matches)
            distribution[reasoning_type] = count
        
        return distribution
    
    def _classify_reasoning_level(self, score: float) -> str:
        """分类推理水平"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "average"
        elif score >= 0.2:
            return "below_average"
        else:
            return "poor"
