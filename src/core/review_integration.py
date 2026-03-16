#!/usr/bin/env python3
"""
Review Pipeline Agent Integration

将 Review Pipeline 与现有 Agent 集成：
- ValidationAgent 集成 L2 评审
- QualityController 集成 L0/L1 评审
- ChiefAgent 集成评审决策
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio


class ReviewIntegration:
    """
    Review Pipeline 集成器
    
    将分级评审集成到 Agent 工作流中
    """
    
    def __init__(self):
        self._pipeline_cache: Dict[str, Any] = {}
    
    async def review_artifact(
        self,
        artifact_name: str,
        artifact_content: Any,
        level: str,  # "l0", "l1", "l2", "l3"
        intent_statement: str = "",
        temp_implementation: str = "",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        评审产物
        
        Args:
            artifact_name: 产物名称
            artifact_content: 产物内容
            level: 评审级别 ("l0", "l1", "l2", "l3")
            intent_statement: 意图说明
            temp_implementation: 临时实现说明
            context: 上下文
        
        Returns:
            评审报告字典
        """
        from src.core.review_pipeline import (
            ReviewPipeline, ReviewLevel, ReviewResult
        )
        
        # 映射级别
        level_map = {
            "l0": ReviewLevel.L0_AUTO,
            "l1": ReviewLevel.L1_SELF,
            "l2": ReviewLevel.L2_PEER,
            "l3": ReviewLevel.L3_EXPERT
        }
        
        review_level = level_map.get(level.lower(), ReviewLevel.L0_AUTO)
        
        # 创建或获取 pipeline
        pipeline = self._get_pipeline(level)
        
        # 执行评审
        report = await pipeline.review(
            artifact_name=artifact_name,
            artifact_content=artifact_content,
            level=review_level,
            context=context or {},
            intent_statement=intent_statement,
            temp_implementation=temp_implementation
        )
        
        # 转换为字典
        return report.to_dict()
    
    def _get_pipeline(self, level: str):
        """获取或创建 Pipeline"""
        from src.core.review_pipeline import ReviewPipeline
        
        if level not in self._pipeline_cache:
            self._pipeline_cache[level] = ReviewPipeline(name=f"agent_{level}")
        
        return self._pipeline_cache[level]
    
    async def review_with_fallback(
        self,
        artifact_name: str,
        artifact_content: Any,
        max_level: str = "l2",
        intent_statement: str = ""
    ) -> Dict[str, Any]:
        """
        降级评审
        
        如果高级别评审失败，自动降级到低级别
        """
        levels = ["l3", "l2", "l1", "l0"]
        
        # 确定最大级别
        max_idx = levels.index(max_level) if max_level in levels else 1
        
        # 从低到高尝试
        for level in levels[max_idx:]:
            result = await self.review_artifact(
                artifact_name=artifact_name,
                artifact_content=artifact_content,
                level=level,
                intent_statement=intent_statement
            )
            
            # 如果通过或只有警告，返回结果
            if result["result"] in ["pass", "pass_with_warnings"]:
                result["review_level_used"] = level
                return result
        
        # 所有级别都失败
        return result


# === Agent 集成 Mixin ===

class ReviewableMixin:
    """
    可评审的 Agent Mixin
    
    让 Agent 支持评审功能
    """
    
    def __init__(self):
        self._review_integration = ReviewIntegration()
        self._review_enabled = True
    
    async def review_before_respond(self, response: Any) -> Dict[str, Any]:
        """
        响应前评审
        
        在 Agent 生成响应前进行评审
        """
        if not self._review_enabled:
            return {"enabled": False}
        
        return await self._review_integration.review_artifact(
            artifact_name=self.__class__.__name__,
            artifact_content=response,
            level="l0",  # 默认 L0
            intent_statement=getattr(self, '_intent_statement', ''),
            temp_implementation=getattr(self, '_temp_implementation', '')
        )
    
    def enable_review(self):
        """启用评审"""
        self._review_enabled = True
    
    def disable_review(self):
        """禁用评审"""
        self._review_enabled = False


# === ChiefAgent 评审决策集成 ===

class ReviewDecisionMaker:
    """
    评审决策器
    
    基于评审结果决定是否继续、修改或终止
    """
    
    # 决策阈值
    PASS_THRESHOLD = 80
    WARN_THRESHOLD = 50
    
    @staticmethod
    def decide(review_result: Dict[str, Any]) -> str:
        """
        基于评审结果做出决策
        
        Returns:
            "proceed": 可以继续
            "revise": 需要修改
            "block": 阻塞
            "escalate": 升级处理
        """
        score = review_result.get("score", 0)
        result = review_result.get("result", "")
        
        # 检查阻塞发现
        blocking_findings = [
            f for f in review_result.get("findings", [])
            if f.get("blocking", False)
        ]
        
        if blocking_findings:
            return "block"
        
        if score >= ReviewDecisionMaker.PASS_THRESHOLD:
            return "proceed"
        
        if score >= ReviewDecisionMaker.WARN_THRESHOLD:
            return "revise"
        
        return "escalate"
    
    @staticmethod
    def get_action_prompt(decision: str) -> str:
        """获取决策对应的行动提示"""
        prompts = {
            "proceed": "评审通过，继续执行下一阶段",
            "revise": "需要修改，根据评审意见调整后重试",
            "block": "被阻塞，需要人工介入",
            "escalate": "升级处理，需要专家评审"
        }
        return prompts.get(decision, "未知决策")


# === 便捷函数 ===

def get_review_integration() -> ReviewIntegration:
    """获取评审集成器"""
    return ReviewIntegration()


async def quick_review(
    artifact_name: str,
    artifact_content: Any,
    level: str = "l0"
) -> Dict[str, Any]:
    """快速评审"""
    integration = ReviewIntegration()
    return await integration.review_artifact(artifact_name, artifact_content, level)
