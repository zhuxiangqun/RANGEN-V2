#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FactVerificationAgent → QualityController 迁移适配器

将 FactVerificationAgent 的调用适配到 QualityController，实现平滑迁移。
注意：FactVerificationAgent专注于事实验证，而QualityController专注于质量控制和验证。
适配器将事实验证任务转换为质量控制任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.quality_controller import QualityController
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class FactVerificationAgentAdapter(MigrationAdapter):
    """FactVerificationAgent → QualityController 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="FactVerificationAgent",
            target_agent_name="QualityController"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（QualityController）"""
        return QualityController()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        FactVerificationAgent 参数格式:
        {
            'answer': str,  # 要验证的答案
            'query': str,  # 查询
            'evidence': List,  # 证据
            'facts': List,  # 事实列表
            'context': Dict,  # 上下文
            ...
        }
        
        QualityController 参数格式:
        {
            'action': str,  # 'validate_content', 'assess_quality', 'verify_citations'
            'content': str,  # 要验证的内容
            'content_type': str,  # 'answer', 'citation', 'knowledge'
            'sources': List[str],  # 来源列表
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        answer = old_context.get("answer", "")
        query = old_context.get("query", "")
        evidence = old_context.get("evidence", [])
        facts = old_context.get("facts", [])
        context = old_context.get("context", {})
        
        # 确定操作类型（事实验证 -> 内容验证）
        action = old_context.get("action", "validate_content")
        
        # 提取sources（从evidence和facts中提取）
        sources = []
        if evidence:
            sources.extend([str(e) for e in evidence if e])
        if facts:
            sources.extend([str(f) for f in facts if f])
        
        # 转换参数格式
        adapted.update({
            "action": action,
            "content": answer or query,
            "content_type": "answer" if answer else "query",
            "sources": sources,
            # 保留原始参数供参考
            "query": query,
            "evidence": evidence,
            "facts": facts,
            "context": context,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action,
            "sources_count": len(sources)
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        QualityController 返回格式:
        {
            'success': bool,
            'data': {
                'assessment': QualityAssessment,
                'citations': List,
                'is_valid': bool,
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        
        FactVerificationAgent 期望格式:
        {
            'success': bool,
            'data': {
                'is_valid': bool,  # 是否有效
                'verified_facts': List,  # 已验证的事实
                'confidence': float,  # 置信度
                'verification_details': Dict,  # 验证详情
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
            
            # 提取事实验证相关数据
            verification_data = self._extract_verification_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": verification_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取事实验证相关数据
            verification_data = self._extract_verification_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": verification_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_verification": "is_valid" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_verification_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从QualityController的结果中提取事实验证数据"""
        verification_data = {}
        
        # 提取is_valid
        if "is_valid" in data:
            verification_data["is_valid"] = data["is_valid"]
        elif "assessment" in data:
            assessment = data["assessment"]
            if hasattr(assessment, 'overall_score'):
                # 如果分数大于0.7，认为有效
                verification_data["is_valid"] = assessment.overall_score > 0.7
            elif isinstance(assessment, dict):
                score = assessment.get("overall_score", 0.0)
                verification_data["is_valid"] = score > 0.7
        
        # 提取verified_facts（从citations或sources中提取）
        verified_facts = []
        if "citations" in data:
            verified_facts = [str(c) for c in data["citations"]]
        elif "sources" in data:
            verified_facts = [str(s) for s in data["sources"]]
        verification_data["verified_facts"] = verified_facts
        
        # 提取confidence
        if "confidence" in data:
            verification_data["confidence"] = data["confidence"]
        elif "assessment" in data:
            assessment = data["assessment"]
            if hasattr(assessment, 'overall_score'):
                verification_data["confidence"] = assessment.overall_score
            elif isinstance(assessment, dict):
                verification_data["confidence"] = assessment.get("overall_score", 0.7)
        
        # 提取verification_details
        verification_data["verification_details"] = {
            "assessment": data.get("assessment"),
            "citations": data.get("citations", []),
            "sources": data.get("sources", []),
        }
        
        # 如果没有找到验证数据，返回空结构
        if not verification_data or "is_valid" not in verification_data:
            verification_data = {
                "is_valid": False,
                "verified_facts": [],
                "confidence": 0.0,
                "verification_details": {}
            }
        
        return verification_data

