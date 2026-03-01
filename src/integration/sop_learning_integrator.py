#!/usr/bin/env python3
"""
SOP学习集成器 - 连接HandExecutor和SOP学习系统

负责监听Hand执行、提取执行信息、调用SOP学习系统进行学习，
并提供SOP查询和执行建议功能。
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime

from src.hands.executor import HandExecutor, HandExecutionResult
from src.hands.base import BaseHand
from src.core.sop_learning import (
    SOPLearningSystem, get_sop_learning_system,
    StandardOperatingProcedure, SOPStep, SOPLevel, SOPCategory
)


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    task_name: str
    execution_time: float
    success: bool
    hand_results: List[Dict[str, Any]]
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SOPLearningIntegrator:
    """SOP学习集成器"""
    
    def __init__(self, hand_executor: Optional[HandExecutor] = None, 
                 sop_system: Optional[SOPLearningSystem] = None,
                 auto_learn: bool = True):
        """
        初始化SOP学习集成器
        
        Args:
            hand_executor: Hand执行器实例
            sop_system: SOP学习系统实例
            auto_learn: 是否自动学习
        """
        self.logger = logging.getLogger(__name__)
        
        # 依赖注入
        self.hand_executor = hand_executor
        self.sop_system = sop_system or get_sop_learning_system()
        
        # 配置
        self.auto_learn = auto_learn
        self.min_steps_for_learning = 2  # 最少步骤数才学习
        self.execution_history: List[ExecutionRecord] = []
        self.max_history_size = 100
        
        # 回调函数
        self.on_learn_callbacks: List[Callable] = []
        self.on_recall_callbacks: List[Callable] = []
        
        self.logger.info("SOP学习集成器初始化完成")
    
    def set_hand_executor(self, hand_executor: HandExecutor) -> None:
        """设置Hand执行器"""
        self.hand_executor = hand_executor
        self.logger.info(f"已设置Hand执行器: {hand_executor}")
    
    def register_hand_executor(self, hand_executor: HandExecutor) -> None:
        """注册Hand执行器（兼容性方法）"""
        self.set_hand_executor(hand_executor)
    
    def add_learn_callback(self, callback: Callable) -> None:
        """添加学习回调"""
        self.on_learn_callbacks.append(callback)
    
    def add_recall_callback(self, callback: Callable) -> None:
        """添加回忆回调"""
        self.on_recall_callbacks.append(callback)
    
    async def record_execution(self, task_name: str, hand_results: List[HandExecutionResult],
                             context: Optional[Dict[str, Any]] = None, 
                             tags: Optional[List[str]] = None) -> str:
        """
        记录执行结果
        
        Args:
            task_name: 任务名称
            hand_results: Hand执行结果列表
            context: 执行上下文
            tags: 标签
            
        Returns:
            执行记录ID
        """
        if not hand_results:
            self.logger.warning("没有执行结果可记录")
            return ""
        
        # 创建执行记录
        record_id = f"exec_{int(time.time())}_{hash(task_name) % 10000:04d}"
        success = all(result.success for result in hand_results)
        
        # 提取Hand结果信息
        hand_info = []
        for result in hand_results:
            hand_info.append({
                "hand_name": result.hand_name,
                "success": result.success,
                "parameters": self._extract_parameters(result),
                "output_summary": self._summarize_output(result.output),
                "execution_time": result.execution_time,
                "error": result.error
            })
        
        record = ExecutionRecord(
            record_id=record_id,
            task_name=task_name,
            execution_time=time.time(),
            success=success,
            hand_results=hand_info,
            context=context or {},
            tags=tags or [],
            metadata={"recorded_by": "sop_learning_integrator"}
        )
        
        # 保存记录
        self.execution_history.append(record)
        if len(self.execution_history) > self.max_history_size:
            self.execution_history.pop(0)
        
        self.logger.info(f"记录执行: {task_name} (ID: {record_id}), 成功: {success}, 步骤数: {len(hand_results)}")
        
        # 自动学习
        if self.auto_learn and success and len(hand_results) >= self.min_steps_for_learning:
            await self.learn_from_execution(record)
        
        # 触发回调
        for callback in self.on_learn_callbacks:
            try:
                callback(record)
            except Exception as e:
                self.logger.error(f"学习回调执行失败: {e}")
        
        return record_id
    
    def _extract_parameters(self, result: HandExecutionResult) -> Dict[str, Any]:
        """从执行结果提取参数"""
        # 这是一个简化版本，实际实现需要根据具体Hand类型提取参数
        # 这里假设result.output包含执行参数信息
        if isinstance(result.output, dict):
            # 尝试从output中提取参数
            params = {}
            for key in ["url", "method", "data", "params", "headers", "file_path", "command"]:
                if key in result.output:
                    params[key] = result.output[key]
            return params
        
        # 默认返回空字典
        return {}
    
    def _summarize_output(self, output: Any) -> Any:
        """摘要化输出，避免存储过大数据"""
        if output is None:
            return None
        
        if isinstance(output, dict):
            # 只保留关键信息
            summary = {}
            for key, value in output.items():
                if key in ["status_code", "success", "error", "result", "size", "count"]:
                    summary[key] = value
                elif isinstance(value, (str, int, float, bool)):
                    # 简单类型直接保留
                    summary[key] = value
                elif isinstance(value, (list, dict)):
                    # 复杂类型只记录大小
                    if isinstance(value, list):
                        summary[f"{key}_count"] = len(value)
                    elif isinstance(value, dict):
                        summary[f"{key}_keys"] = list(value.keys())[:5]  # 只记录前5个键
            return summary
        
        # 对于非字典类型，尝试转换为字符串
        try:
            str_output = str(output)
            # 截断过长的输出
            if len(str_output) > 200:
                return str_output[:200] + "..."
            return str_output
        except:
            return "[无法摘要的输出]"
    
    async def learn_from_execution(self, record: ExecutionRecord) -> Optional[str]:
        """
        从执行记录学习SOP
        
        Args:
            record: 执行记录
            
        Returns:
            创建的SOP ID，如果未创建则返回None
        """
        if not record.success:
            self.logger.debug("执行失败，跳过学习")
            return None
        
        # 提取执行步骤
        execution_steps = []
        for hand_info in record.hand_results:
            step = {
                "hand_name": hand_info["hand_name"],
                "parameters": hand_info["parameters"],
                "description": f"执行 {hand_info['hand_name']}",
                "metadata": {
                    "execution_time": hand_info["execution_time"],
                    "success": hand_info["success"]
                }
            }
            execution_steps.append(step)
        
        # 调用SOP学习系统
        try:
            sop_id = self.sop_system.learn_from_execution(
                task_name=record.task_name,
                execution_steps=execution_steps,
                success=record.success,
                execution_id=record.record_id,
                importance=1.0  # 默认重要性
            )
            
            if sop_id:
                self.logger.info(f"从执行记录学习到SOP: {sop_id}")
                
                # 添加标签
                if record.tags:
                    sop = self.sop_system.get_sop(sop_id)
                    if sop:
                        for tag in record.tags:
                            if tag not in sop.tags:
                                sop.tags.append(tag)
                
                return sop_id
            
        except Exception as e:
            self.logger.error(f"SOP学习失败: {e}")
        
        return None
    
    async def recall_sops(self, task_description: str, context: Optional[Dict[str, Any]] = None,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        回忆相关SOP
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            limit: 返回数量限制
            
        Returns:
            相关SOP列表
        """
        try:
            # 调用SOP学习系统回忆功能
            relevant_sops = self.sop_system.recall_sop(task_description, context)
            
            # 触发回调
            for callback in self.on_recall_callbacks:
                try:
                    callback(task_description, relevant_sops)
                except Exception as e:
                    self.logger.error(f"回忆回调执行失败: {e}")
            
            return relevant_sops[:limit]
        
        except Exception as e:
            self.logger.error(f"SOP回忆失败: {e}")
            return []
    
    async def execute_with_sop_guidance(self, task_description: str, 
                                       context: Optional[Dict[str, Any]] = None) -> List[HandExecutionResult]:
        """
        使用SOP指导执行任务
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            Hand执行结果列表
        """
        if not self.hand_executor:
            raise ValueError("Hand执行器未设置")
        
        # 1. 回忆相关SOP
        relevant_sops = await self.recall_sops(task_description, context)
        
        if not relevant_sops:
            self.logger.info(f"未找到相关SOP，将手动执行任务: {task_description}")
            # 这里可以添加默认执行逻辑
            return []
        
        # 2. 选择最佳SOP（目前选择相关性最高的）
        best_sop_info = relevant_sops[0]
        best_sop = best_sop_info["sop"]
        
        self.logger.info(f"使用SOP执行任务: {best_sop.name} (相关性: {best_sop_info['relevance']:.2f})")
        
        # 3. 按SOP步骤执行
        results = []
        for i, step in enumerate(best_sop.steps):
            self.logger.info(f"执行SOP步骤 {i+1}/{len(best_sop.steps)}: {step.hand_name}")
            
            try:
                # 执行Hand
                result = await self.hand_executor.execute_hand(
                    step.hand_name, 
                    **step.parameters
                )
                results.append(result)
                
                # 检查步骤执行是否成功
                if not result.success:
                    self.logger.warning(f"SOP步骤执行失败: {step.hand_name}")
                    # 可以添加重试或备选方案逻辑
                    
            except Exception as e:
                self.logger.error(f"执行SOP步骤异常: {e}")
                # 创建失败结果
                results.append(HandExecutionResult(
                    hand_name=step.hand_name,
                    success=False,
                    output=None,
                    error=f"执行异常: {e}"
                ))
        
        # 4. 记录执行结果用于学习
        await self.record_execution(
            task_name=task_description,
            hand_results=results,
            context=context,
            tags=["sop_guided", best_sop.sop_id]
        )
        
        # 5. 更新SOP执行统计
        self._update_sop_execution_stats(best_sop.sop_id, results)
        
        return results
    
    def _update_sop_execution_stats(self, sop_id: str, results: List[HandExecutionResult]) -> None:
        """更新SOP执行统计"""
        try:
            sop = self.sop_system.get_sop(sop_id)
            if not sop:
                return
            
            # 更新执行次数
            sop.execution_count += 1
            
            # 计算本次执行成功率
            success_count = sum(1 for r in results if r.success)
            step_success_rate = success_count / len(results) if results else 0.0
            
            # 更新总体成功率
            if sop.execution_count > 0:
                total_success = (sop.success_rate * (sop.execution_count - 1)) + step_success_rate
                sop.success_rate = total_success / sop.execution_count
            
            # 更新最后执行时间
            sop.last_executed = time.time()
            
            self.logger.debug(f"更新SOP统计: {sop.name}, 执行次数: {sop.execution_count}, 成功率: {sop.success_rate:.2f}")
            
        except Exception as e:
            self.logger.error(f"更新SOP统计失败: {e}")
    
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
        analysis_result = {
            "task_description": task_description,
            "analysis_time": datetime.now().isoformat(),
            "has_related_sops": False,
            "suggestions": [],
            "execution_plan": None
        }
        
        # 1. 回忆相关SOP
        relevant_sops = await self.recall_sops(task_description, context)
        
        if relevant_sops:
            analysis_result["has_related_sops"] = True
            analysis_result["sop_count"] = len(relevant_sops)
            analysis_result["top_sops"] = []
            
            for sop_info in relevant_sops[:3]:  # 只取前3个
                sop = sop_info["sop"]
                analysis_result["top_sops"].append({
                    "sop_id": sop.sop_id,
                    "name": sop.name,
                    "description": sop.description,
                    "relevance": sop_info["relevance"],
                    "success_rate": sop.success_rate,
                    "execution_count": sop.execution_count,
                    "step_count": len(sop.steps),
                    "quality_analysis": self.sop_system.analyze_sop_quality(sop.sop_id)
                })
            
            # 生成建议
            best_sop = relevant_sops[0]["sop"]
            analysis_result["suggestions"].append({
                "type": "use_existing_sop",
                "description": f"建议使用现有SOP: {best_sop.name} (成功率: {best_sop.success_rate*100:.1f}%)",
                "confidence": relevant_sops[0]["relevance"],
                "priority": "high"
            })
            
            # 生成执行计划
            analysis_result["execution_plan"] = {
                "strategy": "sop_guided",
                "recommended_sop": best_sop.sop_id,
                "steps": [
                    {
                        "step": i+1,
                        "hand_name": step.hand_name,
                        "description": step.description,
                        "parameters_summary": list(step.parameters.keys())
                    }
                    for i, step in enumerate(best_sop.steps[:5])  # 只显示前5步
                ],
                "estimated_steps": len(best_sop.steps)
            }
        
        else:
            # 没有相关SOP的建议
            analysis_result["suggestions"].append({
                "type": "manual_execution",
                "description": "未找到相关SOP，建议手动执行并学习",
                "confidence": 0.3,
                "priority": "medium"
            })
            
            # 尝试基于关键词生成简单执行计划
            analysis_result["execution_plan"] = {
                "strategy": "manual_exploration",
                "suggested_hands": self._suggest_hands_by_keywords(task_description),
                "recommendation": "建议从简单的Hand开始尝试，系统会自动学习成功执行"
            }
        
        # 添加系统建议
        analysis_result["suggestions"].extend(self._generate_system_suggestions(analysis_result))
        
        return analysis_result
    
    def _suggest_hands_by_keywords(self, task_description: str) -> List[Dict[str, Any]]:
        """根据关键词建议Hand"""
        if not self.hand_executor:
            return []
        
        # 简单关键词匹配
        keywords = task_description.lower().split()
        suggested_hands = []
        
        # 检查registry中可用的Hand
        registry = self.hand_executor.registry
        if hasattr(registry, 'get_all_hands'):
            all_hands = registry.get_all_hands()
            
            for hand in all_hands:
                hand_name = hand.name.lower()
                hand_desc = (hand.description or "").lower()
                
                # 计算匹配分数
                score = 0
                for keyword in keywords:
                    if keyword in hand_name:
                        score += 2
                    if keyword in hand_desc:
                        score += 1
                
                if score > 0:
                    suggested_hands.append({
                        "hand_name": hand.name,
                        "description": hand.description,
                        "match_score": score,
                        "category": hand.category.value if hasattr(hand, 'category') else "unknown"
                    })
        
        # 按匹配分数排序
        suggested_hands.sort(key=lambda x: x["match_score"], reverse=True)
        
        return suggested_hands[:5]  # 返回前5个
    
    def _generate_system_suggestions(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成系统建议"""
        suggestions = []
        
        if analysis_result.get("has_related_sops"):
            top_sop = analysis_result.get("top_sops", [{}])[0]
            quality = top_sop.get("quality_analysis", {})
            
            if quality.get("quality_score", 0) < 0.7:
                suggestions.append({
                    "type": "improve_sop_quality",
                    "description": f"SOP质量较低 ({quality.get('quality_score', 0)*100:.1f}%)，建议从更多成功执行中学习",
                    "priority": "medium"
                })
            
            if top_sop.get("execution_count", 0) < 3:
                suggestions.append({
                    "type": "need_more_executions",
                    "description": "SOP执行次数较少，建议增加验证执行",
                    "priority": "low"
                })
        
        else:
            suggestions.append({
                "type": "enable_learning",
                "description": "启用自动学习功能，系统将从成功执行中学习新的SOP",
                "priority": "high"
            })
        
        return suggestions
    
    def get_integrator_stats(self) -> Dict[str, Any]:
        """获取集成器统计信息"""
        # 获取SOP系统统计
        sop_stats = self.sop_system.get_statistics() if self.sop_system else {}
        
        return {
            "execution_records_count": len(self.execution_history),
            "auto_learn_enabled": self.auto_learn,
            "min_steps_for_learning": self.min_steps_for_learning,
            "hand_executor_set": self.hand_executor is not None,
            "sop_system_available": self.sop_system is not None,
            "learn_callbacks_count": len(self.on_learn_callbacks),
            "recall_callbacks_count": len(self.on_recall_callbacks),
            "recent_executions": [
                {
                    "task_name": record.task_name,
                    "success": record.success,
                    "time": datetime.fromtimestamp(record.execution_time).isoformat(),
                    "step_count": len(record.hand_results),
                    "tags": record.tags
                }
                for record in self.execution_history[-5:]  # 最近5条记录
            ],
            "sop_system_stats": sop_stats
        }
    
    def get_execution_record(self, record_id: str) -> Optional[ExecutionRecord]:
        """获取执行记录"""
        for record in self.execution_history:
            if record.record_id == record_id:
                return record
        return None
    
    def search_execution_records(self, task_name_filter: Optional[str] = None,
                               success_filter: Optional[bool] = None,
                               tag_filter: Optional[str] = None,
                               limit: int = 20) -> List[ExecutionRecord]:
        """搜索执行记录"""
        filtered = self.execution_history
        
        if task_name_filter:
            filtered = [r for r in filtered if task_name_filter.lower() in r.task_name.lower()]
        
        if success_filter is not None:
            filtered = [r for r in filtered if r.success == success_filter]
        
        if tag_filter:
            filtered = [r for r in filtered if tag_filter in r.tags]
        
        # 按时间倒序排序
        filtered.sort(key=lambda r: r.execution_time, reverse=True)
        
        return filtered[:limit]
    
    def clear_history(self) -> None:
        """清空执行历史"""
        self.execution_history.clear()
        self.logger.info("执行历史已清空")


# 全局SOP学习集成器实例
_sop_learning_integrator_instance: Optional[SOPLearningIntegrator] = None


def get_sop_learning_integrator(hand_executor: Optional[HandExecutor] = None,
                               auto_learn: bool = True) -> SOPLearningIntegrator:
    """获取SOP学习集成器实例（单例模式）"""
    global _sop_learning_integrator_instance
    
    if _sop_learning_integrator_instance is None:
        _sop_learning_integrator_instance = SOPLearningIntegrator(
            hand_executor=hand_executor,
            auto_learn=auto_learn
        )
    
    # 如果提供了新的hand_executor，则更新
    if hand_executor and _sop_learning_integrator_instance.hand_executor != hand_executor:
        _sop_learning_integrator_instance.set_hand_executor(hand_executor)
    
    return _sop_learning_integrator_instance


def register_hand_executor_for_sop_learning(hand_executor: HandExecutor) -> None:
    """注册Hand执行器到SOP学习系统（便捷函数）"""
    integrator = get_sop_learning_integrator()
    integrator.set_hand_executor(hand_executor)