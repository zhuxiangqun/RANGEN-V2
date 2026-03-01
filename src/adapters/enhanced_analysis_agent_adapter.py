#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EnhancedAnalysisAgent → ReasoningExpert 迁移适配器

将 EnhancedAnalysisAgent 的调用适配到 ReasoningExpert，实现平滑迁移。
注意：EnhancedAnalysisAgent专注于分析，而ReasoningExpert专注于推理。
适配器将分析任务转换为推理任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.reasoning_expert import ReasoningExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class EnhancedAnalysisAgentAdapter(MigrationAdapter):
    """EnhancedAnalysisAgent → ReasoningExpert 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="EnhancedAnalysisAgent",
            target_agent_name="ReasoningExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（ReasoningExpert）"""
        return ReasoningExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        EnhancedAnalysisAgent 参数格式:
        {
            'query': str,  # 必需，分析查询
            'analysis_type': str,  # 可选，分析类型
            'data': Any,  # 可选，要分析的数据
            'context': Dict,  # 可选，上下文信息
            ...
        }
        
        ReasoningExpert 参数格式:
        {
            'query': str,  # 必需
            'reasoning_type': str,  # 可选，默认自动分析
            'complexity': str,  # 可选，默认自动分析
            'max_parallel_paths': int,  # 可选，默认3
            'use_cache': bool,  # 可选，默认True
            'use_graph': bool,  # 可选，默认False
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        analysis_type = old_context.get("analysis_type", "")
        data = old_context.get("data")
        context = old_context.get("context", {})
        
        # 将analysis_type映射到reasoning_type
        reasoning_type_mapping = {
            "deep": "chain_of_thought",
            "shallow": "direct",
            "comparative": "comparative",
            "causal": "causal",
        }
        reasoning_type = reasoning_type_mapping.get(analysis_type, None)
        
        # 转换参数格式
        adapted.update({
            "query": query,
            # ReasoningExpert的参数
            "reasoning_type": reasoning_type,  # 可选，让ReasoningExpert自动分析
            "complexity": old_context.get("complexity"),  # 可选，让ReasoningExpert自动分析
            "max_parallel_paths": old_context.get("max_parallel_paths", 3),
            "use_cache": old_context.get("use_cache", True),
            "use_graph": old_context.get("use_graph", False),
            # 保留原始参数供参考
            "analysis_type": analysis_type,
            "data": data,
            "context": context,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "query_length": len(query),
            "analysis_type": analysis_type
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        ReasoningExpert 返回格式:
        {
            'success': bool,
            'data': {
                'answer': str,
                'reasoning_paths': List,
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        
        EnhancedAnalysisAgent 期望格式:
        {
            'success': bool,
            'data': {
                'analysis_result': str,  # 分析结果
                'insights': List,  # 洞察
                'conclusions': List,  # 结论
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            data = new_result.data if hasattr(new_result, 'data') else {}
            
            # 提取分析相关数据
            analysis_data = self._extract_analysis_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": analysis_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取分析相关数据
            analysis_data = self._extract_analysis_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": analysis_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_analysis": "analysis_result" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从ReasoningExpert的结果中提取分析数据"""
        analysis_data = {}
        
        # 提取answer（转换为analysis_result）
        if "answer" in data:
            analysis_data["analysis_result"] = data["answer"]
        elif "result" in data:
            if isinstance(data["result"], str):
                analysis_data["analysis_result"] = data["result"]
            elif isinstance(data["result"], dict):
                analysis_data["analysis_result"] = data["result"].get("answer", "")
        
        # 提取reasoning_paths（转换为insights和conclusions）
        if "reasoning_paths" in data:
            reasoning_paths = data["reasoning_paths"]
            insights = []
            conclusions = []
            
            for path in reasoning_paths:
                if isinstance(path, dict):
                    # 提取洞察
                    if "insight" in path:
                        insights.append(path["insight"])
                    elif "step" in path:
                        insights.append(path["step"])
                    # 提取结论
                    if "conclusion" in path:
                        conclusions.append(path["conclusion"])
                    elif "final_answer" in path:
                        conclusions.append(path["final_answer"])
            
            if insights:
                analysis_data["insights"] = insights
            if conclusions:
                analysis_data["conclusions"] = conclusions
        
        # 提取confidence
        if "confidence" in data:
            analysis_data["confidence"] = data["confidence"]
        
        # 如果没有找到分析数据，返回空结构
        if not analysis_data or "analysis_result" not in analysis_data:
            analysis_data = {
                "analysis_result": "",
                "insights": [],
                "conclusions": [],
                "confidence": 0.0
            }
        
        return analysis_data

