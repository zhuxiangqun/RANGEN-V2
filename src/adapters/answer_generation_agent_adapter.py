#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnswerGenerationAgent → RAGExpert 迁移适配器

将 AnswerGenerationAgent 的调用适配到 RAGExpert，实现平滑迁移。
注意：RAGExpert包含知识检索和答案生成，而AnswerGenerationAgent只做答案生成。
适配器将只使用RAGExpert的答案生成部分。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.rag_agent import RAGExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class AnswerGenerationAgentAdapter(MigrationAdapter):
    """AnswerGenerationAgent → RAGExpert 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="AnswerGenerationAgent",
            target_agent_name="RAGExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（RAGExpert）"""
        return RAGExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        AnswerGenerationAgent 参数格式:
        {
            'query': str,  # 必需
            'knowledge': List[Dict],  # 可选，知识数据
            'evidence': List,  # 可选，证据
            'dependencies': Dict,  # 可选，依赖信息（如推理结果）
            'knowledge_data': List[Dict],  # 可选，知识数据（别名）
            'reasoning_data': Dict,  # 可选，推理数据
            ...
        }
        
        RAGExpert 参数格式:
        {
            'query': str,  # 必需
            'type': str,  # 可选，默认为"rag"
            'use_cache': bool,  # 可选，默认为True
            'use_parallel': bool,  # 可选，默认为True
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        knowledge = old_context.get("knowledge", []) or old_context.get("knowledge_data", [])
        evidence = old_context.get("evidence", [])
        dependencies = old_context.get("dependencies", {})
        reasoning_data = old_context.get("reasoning_data", {})
        
        # 转换参数格式
        adapted.update({
            "query": query,
            # RAGExpert的参数
            "type": old_context.get("type", "rag"),
            "use_cache": old_context.get("use_cache", True),
            "use_parallel": old_context.get("use_parallel", True),
            # 保留原始参数供参考
            "knowledge": knowledge,
            "evidence": evidence,
            "dependencies": dependencies,
            "reasoning_data": reasoning_data,
            # 标记只做答案生成（可以使用已有的知识）
            "_answer_generation_only": True,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "query_length": len(query),
            "has_knowledge": len(knowledge) > 0,
            "has_dependencies": len(dependencies) > 0
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        RAGExpert 返回格式:
        {
            'success': bool,
            'data': {
                'answer': str,  # 答案
                'sources': List,  # 知识源
                'evidence': List,  # 证据
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        
        AnswerGenerationAgent 期望格式:
        {
            'success': bool,
            'data': {
                'answer': str,  # 答案（主要关注这个）
                'final_answer': str,  # 最终答案（别名）
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            data = new_result.data if hasattr(new_result, 'data') and new_result.data is not None else {}

            # 提取答案生成相关数据
            answer_data = self._extract_answer_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": answer_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取答案生成相关数据
            answer_data = self._extract_answer_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": answer_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_answer": "answer" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_answer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从RAGExpert的结果中提取答案数据"""
        answer_data = {}

        # 提取answer（答案）
        if "answer" in data:
            answer_data["answer"] = data["answer"]
            answer_data["final_answer"] = data["answer"]  # 也设置final_answer
        elif "final_answer" in data:
            answer_data["answer"] = data["final_answer"]
            answer_data["final_answer"] = data["final_answer"]
        elif "result" in data and data["result"] is not None:
            result = data["result"]
            if isinstance(result, str):
                answer_data["answer"] = result
                answer_data["final_answer"] = result
            elif isinstance(result, dict):
                answer_data["answer"] = result.get("answer", "")
                answer_data["final_answer"] = answer_data["answer"]

        # 保留其他可能需要的字段
        if "confidence" in data:
            answer_data["confidence"] = data["confidence"]
        if "sources" in data:
            answer_data["sources"] = data["sources"]
        if "evidence" in data:
            answer_data["evidence"] = data["evidence"]

        # 如果没有找到答案，返回空结构
        if not answer_data or "answer" not in answer_data:
            answer_data = {
                "answer": "",
                "final_answer": ""
            }

        return answer_data

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行方法（兼容迁移脚本）

        Args:
            context: 输入上下文

        Returns:
            执行结果
        """
        return await self.execute_adapted(context)

