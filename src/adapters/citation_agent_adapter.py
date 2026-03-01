#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CitationAgent → QualityController 迁移适配器

将 CitationAgent 的调用适配到 QualityController，实现平滑迁移。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.quality_controller import QualityController
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class CitationAgentAdapter(MigrationAdapter):
    """CitationAgent → QualityController 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="CitationAgent",
            target_agent_name="QualityController"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（QualityController）"""
        return QualityController()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        CitationAgent 参数格式:
        {
            'query': str,
            'answer': str,
            'knowledge': List[Dict],
            'evidence': List,
            ...
        }
        
        QualityController 参数格式:
        {
            'action': str,  # 'validate_content', 'assess_quality', 'verify_citations'
            'content': str,
            'content_type': str,  # 'answer', 'citation', 'knowledge'
            'sources': List[str],
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        answer = old_context.get("answer", "") or old_context.get("content", "")
        knowledge = old_context.get("knowledge", []) or old_context.get("sources", [])
        evidence = old_context.get("evidence", [])
        
        # 确定操作类型
        # 如果主要是生成引用，使用 'verify_citations'
        # 如果主要是验证质量，使用 'validate_content'
        action = old_context.get("action", "verify_citations")
        if action not in ["validate_content", "assess_quality", "verify_citations"]:
            # 根据上下文推断操作类型
            if answer and knowledge:
                action = "verify_citations"  # 有答案和知识，主要是验证引用
            elif answer:
                action = "validate_content"  # 只有答案，验证内容质量
            else:
                action = "assess_quality"  # 默认质量评估
        
        # 转换参数格式
        adapted.update({
            "action": action,
            "content": answer or query,
            "content_type": "answer" if answer else "query",
            "sources": self._extract_sources(knowledge),
            "knowledge": knowledge,  # 保留原始knowledge供参考
            "evidence": evidence,  # 保留原始evidence供参考
            "query": query,  # 保留原始query供参考
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action
        })
        
        return adapted
    
    def _extract_sources(self, knowledge: list) -> list:
        """从knowledge列表中提取source信息"""
        sources = []
        for item in knowledge:
            if isinstance(item, dict):
                # 尝试多种可能的source字段名
                source = (
                    item.get("source") or
                    item.get("url") or
                    item.get("reference") or
                    item.get("citation") or
                    str(item.get("id", ""))
                )
                if source:
                    sources.append(source)
            elif isinstance(item, str):
                sources.append(item)
        return sources
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        QualityController 返回格式:
        {
            'success': bool,
            'data': {
                'assessment': QualityAssessment,
                'citations': List,
                ...
            },
            'confidence': float,
            ...
        }
        
        CitationAgent 期望格式:
        {
            'success': bool,
            'data': {
                'citations': List,
                'sources': List,
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            adapted.update({
                "success": new_result.success,
                "data": self._extract_citation_data(new_result.data if hasattr(new_result, 'data') else {}),
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取引用相关数据
            citation_data = self._extract_citation_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": citation_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_citations": "citations" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_citation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从QualityController的结果中提取引用数据"""
        citation_data = {}
        
        # 如果data中有assessment对象
        if "assessment" in data:
            assessment = data["assessment"]
            # 尝试从assessment中提取引用信息
            if hasattr(assessment, 'detected_issues'):
                # 提取引用相关的问题
                citation_issues = [
                    issue for issue in assessment.detected_issues
                    if "citation" in str(issue).lower() or "source" in str(issue).lower()
                ]
                if citation_issues:
                    citation_data["citation_issues"] = citation_issues
        
        # 如果data中有citations字段
        if "citations" in data:
            citation_data["citations"] = data["citations"]
        
        # 如果data中有sources字段
        if "sources" in data:
            citation_data["sources"] = data["sources"]
        
        # 如果data中有quality_assessment，提取相关信息
        if "quality_assessment" in data:
            qa = data["quality_assessment"]
            citation_data["quality_score"] = (
                qa.overall_score if hasattr(qa, 'overall_score') else
                qa.get("overall_score", 0.0) if isinstance(qa, dict) else 0.0
            )
        
        # 如果没有找到引用数据，返回空结构
        if not citation_data:
            citation_data = {
                "citations": [],
                "sources": [],
                "quality_score": 0.0
            }
        
        return citation_data

