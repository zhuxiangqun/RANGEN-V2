#!/usr/bin/env python3
"""
增强版Hand执行器 - 集成SOP学习功能

基于GenericAgent理念，在标准HandExecutor基础上增加：
1. 执行记录和SOP学习
2. SOP指导的任务执行
3. 任务分析和建议生成
4. 执行统计和质量评估
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

from .executor import HandExecutor, HandExecutionResult
from .base import BaseHand
from ..integration.sop_learning_integrator import (
    SOPLearningIntegrator, get_sop_learning_integrator,
    ExecutionRecord, register_hand_executor_for_sop_learning
)


class EnhancedHandExecutor(HandExecutor):
    """增强版Hand执行器 - 集成SOP学习"""
    
    def __init__(self, registry=None, enable_sop_learning: bool = True,
                 auto_record_executions: bool = True, **kwargs):
        """
        初始化增强版Hand执行器
        
        Args:
            registry: Hand注册表
            enable_sop_learning: 是否启用SOP学习
            auto_record_executions: 是否自动记录执行
            **kwargs: 传递给父类的参数
        """
        super().__init__(registry=registry, **kwargs)
        self.logger = logging.getLogger(__name__)
        
        # SOP学习配置
        self.enable_sop_learning = enable_sop_learning
        self.auto_record_executions = auto_record_executions
        
        # SOP学习集成器
        self.sop_integrator: Optional[SOPLearningIntegrator] = None
        if enable_sop_learning:
            self.sop_integrator = get_sop_learning_integrator(self, auto_learn=True)
            self.logger.info("SOP学习功能已启用")
        
        # 增强功能配置
        self.task_context_provider: Optional[Callable] = None
        self.execution_analyzers: List[Callable] = []
        self.sop_guidance_enabled = True
        
        self.logger.info("增强版Hand执行器初始化完成")
    
    def set_task_context_provider(self, provider: Callable) -> None:
        """设置任务上下文提供器"""
        self.task_context_provider = provider
        self.logger.info(f"已设置任务上下文提供器: {provider}")
    
    def add_execution_analyzer(self, analyzer: Callable) -> None:
        """添加执行分析器"""
        self.execution_analyzers.append(analyzer)
        self.logger.info(f"已添加执行分析器: {analyzer}")
    
    async def execute_hand(self, hand_name: str, **kwargs) -> HandExecutionResult:
        """执行指定的Hand（增强版）"""
        # 获取任务上下文（如果有）
        task_context = None
        if self.task_context_provider:
            try:
                task_context = self.task_context_provider()
            except Exception as e:
                self.logger.warning(f"获取任务上下文失败: {e}")
        
        # 调用父类执行
        start_time = time.time()
        result = await super().execute_hand(hand_name, **kwargs)
        execution_time = time.time() - start_time
        
        # 记录执行（如果需要）
        if self.auto_record_executions and self.sop_integrator:
            task_name = kwargs.get("task_name", f"执行 {hand_name}")
            
            # 提取任务标签
            tags = kwargs.get("tags", [])
            if "sop_guided" not in tags and kwargs.get("sop_id"):
                tags.append("sop_guided")
            
            # 记录执行
            await self.sop_integrator.record_execution(
                task_name=task_name,
                hand_results=[result],
                context=task_context,
                tags=tags
            )
        
        # 执行分析
        for analyzer in self.execution_analyzers:
            try:
                analyzer(result, execution_time, kwargs)
            except Exception as e:
                self.logger.error(f"执行分析器失败: {e}")
        
        return result
    
    async def execute_sequence(self, sequence: List[Dict[str, Any]], 
                              task_name: Optional[str] = None,
                              context: Optional[Dict[str, Any]] = None,
                              tags: Optional[List[str]] = None) -> List[HandExecutionResult]:
        """执行Hand序列（增强版）"""
        # 调用父类执行序列
        results = await super().execute_sequence(sequence)
        
        # 记录执行（如果需要）
        if self.auto_record_executions and self.sop_integrator and results:
            # 确定任务名称
            actual_task_name = task_name or f"序列执行 ({len(sequence)} 个步骤)"
            
            # 记录执行
            await self.sop_integrator.record_execution(
                task_name=actual_task_name,
                hand_results=results,
                context=context,
                tags=tags or []
            )
        
        return results
    
    async def execute_with_sop_guidance(self, task_description: str,
                                       context: Optional[Dict[str, Any]] = None,
                                       sop_id: Optional[str] = None) -> List[HandExecutionResult]:
        """
        使用SOP指导执行任务
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            sop_id: 指定SOP ID（如果为None则自动选择）
            
        Returns:
            Hand执行结果列表
        """
        if not self.enable_sop_learning or not self.sop_integrator:
            self.logger.warning("SOP学习未启用，将使用标准执行")
            # 回退到标准执行
            return []
        
        # 获取任务上下文
        task_context = context
        if not task_context and self.task_context_provider:
            try:
                task_context = self.task_context_provider()
            except Exception as e:
                self.logger.warning(f"获取任务上下文失败: {e}")
        
        # 使用SOP指导执行
        results = await self.sop_integrator.execute_with_sop_guidance(
            task_description=task_description,
            context=task_context
        )
        
        return results
    
    async def analyze_task(self, task_description: str,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析任务并生成执行建议
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            分析结果
        """
        if not self.enable_sop_learning or not self.sop_integrator:
            return {
                "task_description": task_description,
                "analysis_time": datetime.now().isoformat(),
                "has_related_sops": False,
                "suggestions": [{
                    "type": "sop_learning_disabled",
                    "description": "SOP学习功能未启用，无法提供智能建议",
                    "priority": "medium"
                }],
                "execution_plan": None
            }
        
        # 获取任务上下文
        task_context = context
        if not task_context and self.task_context_provider:
            try:
                task_context = self.task_context_provider()
            except Exception as e:
                self.logger.warning(f"获取任务上下文失败: {e}")
        
        # 分析任务
        analysis_result = await self.sop_integrator.analyze_task(
            task_description=task_description,
            context=task_context
        )
        
        return analysis_result
    
    async def get_sop_recommendations(self, task_description: str,
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """获取SOP推荐"""
        if not self.enable_sop_learning or not self.sop_integrator:
            return []
        
        return await self.sop_integrator.recall_sops(
            task_description=task_description,
            limit=limit
        )
    
    async def learn_from_execution_record(self, record_id: str) -> Optional[str]:
        """从执行记录学习SOP"""
        if not self.enable_sop_learning or not self.sop_integrator:
            return None
        
        # 获取执行记录
        record = self.sop_integrator.get_execution_record(record_id)
        if not record:
            self.logger.warning(f"执行记录未找到: {record_id}")
            return None
        
        # 学习SOP
        return await self.sop_integrator.learn_from_execution(record)
    
    def get_sop_learning_stats(self) -> Dict[str, Any]:
        """获取SOP学习统计信息"""
        if not self.enable_sop_learning or not self.sop_integrator:
            return {"sop_learning_enabled": False}
        
        return self.sop_integrator.get_integrator_stats()
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强版统计信息"""
        # 获取基础统计
        base_stats = super().get_statistics()
        
        # 获取SOP学习统计
        sop_stats = self.get_sop_learning_stats()
        
        # 合并统计
        enhanced_stats = {
            **base_stats,
            "enhanced_features": {
                "sop_learning_enabled": self.enable_sop_learning,
                "auto_record_executions": self.auto_record_executions,
                "sop_guidance_enabled": self.sop_guidance_enabled,
                "execution_analyzers_count": len(self.execution_analyzers),
                "task_context_provider_set": self.task_context_provider is not None
            },
            "sop_learning": sop_stats
        }
        
        return enhanced_stats
    
    def search_execution_records(self, task_name_filter: Optional[str] = None,
                               success_filter: Optional[bool] = None,
                               tag_filter: Optional[str] = None,
                               limit: int = 20) -> List[ExecutionRecord]:
        """搜索执行记录"""
        if not self.enable_sop_learning or not self.sop_integrator:
            return []
        
        return self.sop_integrator.search_execution_records(
            task_name_filter=task_name_filter,
            success_filter=success_filter,
            tag_filter=tag_filter,
            limit=limit
        )
    
    async def optimize_sop(self, sop_id: str) -> Dict[str, Any]:
        """优化SOP"""
        if not self.enable_sop_learning or not self.sop_integrator:
            return {"success": False, "error": "SOP学习未启用"}
        
        try:
            # 获取SOP系统
            sop_system = self.sop_integrator.sop_system
            if not sop_system:
                return {"success": False, "error": "SOP系统不可用"}
            
            # 分析SOP质量
            quality_analysis = sop_system.analyze_sop_quality(sop_id)
            
            # 获取优化建议
            suggestions = quality_analysis.get("suggestions", [])
            
            # 这里可以添加自动优化逻辑，比如：
            # 1. 基于建议自动调整SOP
            # 2. 从更多执行记录中学习
            # 3. 合并相似SOP
            
            return {
                "success": True,
                "sop_id": sop_id,
                "quality_analysis": quality_analysis,
                "optimization_suggestions": suggestions,
                "optimization_applied": False,  # 当前版本仅提供建议，不自动应用
                "recommendation": "根据质量分析建议手动优化SOP"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def enable_sop_learning_features(self, enable: bool = True) -> None:
        """启用或禁用SOP学习功能"""
        if enable and not self.sop_integrator:
            self.sop_integrator = get_sop_learning_integrator(self, auto_learn=True)
            self.enable_sop_learning = True
            self.logger.info("SOP学习功能已启用")
        elif not enable:
            self.enable_sop_learning = False
            self.logger.info("SOP学习功能已禁用")
    
    def configure_sop_learning(self, auto_learn: Optional[bool] = None,
                             min_steps_for_learning: Optional[int] = None) -> None:
        """配置SOP学习参数"""
        if not self.sop_integrator:
            self.logger.warning("SOP集成器未初始化，无法配置")
            return
        
        if auto_learn is not None:
            self.sop_integrator.auto_learn = auto_learn
            self.logger.info(f"自动学习设置为: {auto_learn}")
        
        if min_steps_for_learning is not None:
            self.sop_integrator.min_steps_for_learning = min_steps_for_learning
            self.logger.info(f"最小学习步骤数设置为: {min_steps_for_learning}")


# 便捷函数
def create_enhanced_executor(registry=None, enable_sop_learning: bool = True, **kwargs) -> EnhancedHandExecutor:
    """创建增强版Hand执行器"""
    return EnhancedHandExecutor(registry=registry, enable_sop_learning=enable_sop_learning, **kwargs)


def enable_sop_learning_for_executor(executor: HandExecutor) -> EnhancedHandExecutor:
    """
    为现有Hand执行器启用SOP学习功能
    
    注意：这会创建一个新的EnhancedHandExecutor实例，包装原有执行器
    """
    # 创建增强版执行器
    enhanced = EnhancedHandExecutor(
        registry=executor.registry,
        enable_sop_learning=True,
        auto_record_executions=True
    )
    
    # 复制配置
    enhanced.auto_safety_check = executor.auto_safety_check
    enhanced.require_validation_for_risky = executor.require_validation_for_risky
    enhanced.timeout_seconds = executor.timeout_seconds
    
    # 复制执行历史（如果存在）
    if hasattr(executor, 'execution_history'):
        enhanced.execution_history = executor.execution_history.copy()
    
    return enhanced