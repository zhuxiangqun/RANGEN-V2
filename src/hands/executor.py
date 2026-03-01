#!/usr/bin/env python3
"""
Hands能力包执行器
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

from .base import BaseHand, HandExecutionResult, HandSafetyLevel
from .registry import HandRegistry


class HandExecutor:
    """Hands能力包执行器"""
    
    def __init__(self, registry: Optional[HandRegistry] = None):
        self.logger = logging.getLogger(__name__)
        self.registry = registry or HandRegistry()
        self.execution_history: List[HandExecutionResult] = []
        self.max_history_size = 1000
        
        # 执行配置
        self.auto_safety_check = True
        self.require_validation_for_risky = True
        self.timeout_seconds = 300  # 5分钟
        
        self.logger.info("Hand执行器初始化完成")
    
    async def execute_hand(self, hand_name: str, **kwargs) -> HandExecutionResult:
        """执行指定的Hand"""
        hand = self.registry.get_hand(hand_name)
        
        if not hand:
            return HandExecutionResult(
                hand_name=hand_name,
                success=False,
                output=None,
                error=f"Hand '{hand_name}' 未找到"
            )
        
        self.logger.info(f"执行Hand: {hand_name} (参数: {kwargs})")
        
        try:
            # 1. 参数验证
            if not hand.validate_parameters(**kwargs):
                return HandExecutionResult(
                    hand_name=hand_name,
                    success=False,
                    output=None,
                    error="参数验证失败"
                )
            
            # 2. 安全检查
            safety_passed = True
            if self.auto_safety_check:
                safety_passed = await hand.safety_check(**kwargs)
                
                if not safety_passed:
                    safety_msg = f"安全检查未通过 (安全级别: {hand.safety_level.value})"
                    self.logger.warning(safety_msg)
                    
                    if hand.safety_level == HandSafetyLevel.DANGEROUS:
                        return HandExecutionResult(
                            hand_name=hand_name,
                            success=False,
                            output=None,
                            error=safety_msg,
                            safety_check_passed=False
                        )
                    elif self.require_validation_for_risky and hand.safety_level == HandSafetyLevel.RISKY:
                        return HandExecutionResult(
                            hand_name=hand_name,
                            success=False,
                            output=None,
                            error=safety_msg,
                            safety_check_passed=False
                        )
            
            # 3. 执行Hand
            start_time = datetime.now()
            
            try:
                # 设置超时
                if self.timeout_seconds > 0:
                    result = await asyncio.wait_for(
                        hand.execute(**kwargs),
                        timeout=self.timeout_seconds
                    )
                else:
                    result = await hand.execute(**kwargs)
                    
            except asyncio.TimeoutError:
                execution_time = (datetime.now() - start_time).total_seconds()
                error_msg = f"执行超时 ({execution_time:.1f}s > {self.timeout_seconds}s)"
                self.logger.error(error_msg)
                
                result = HandExecutionResult(
                    hand_name=hand_name,
                    success=False,
                    output=None,
                    error=error_msg,
                    execution_time=execution_time,
                    safety_check_passed=safety_passed
                )
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                error_msg = f"执行异常: {e}"
                self.logger.error(error_msg, exc_info=True)
                
                result = HandExecutionResult(
                    hand_name=hand_name,
                    success=False,
                    output=None,
                    error=error_msg,
                    execution_time=execution_time,
                    safety_check_passed=safety_passed
                )
            else:
                # 确保结果包含必要信息
                if not hasattr(result, 'hand_name'):
                    result.hand_name = hand_name
                if not hasattr(result, 'safety_check_passed'):
                    result.safety_check_passed = safety_passed
            
            # 4. 记录执行历史
            self._record_execution(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行流程异常: {e}", exc_info=True)
            return HandExecutionResult(
                hand_name=hand_name,
                success=False,
                output=None,
                error=f"执行流程异常: {e}"
            )
    
    async def execute_sequence(self, sequence: List[Dict[str, Any]]) -> List[HandExecutionResult]:
        """执行Hand序列"""
        results = []
        
        for i, hand_config in enumerate(sequence):
            hand_name = hand_config.get("hand")
            parameters = hand_config.get("parameters", {})
            condition = hand_config.get("condition")
            
            # 检查执行条件
            if condition is not None:
                if not self._evaluate_condition(condition, results):
                    self.logger.info(f"跳过步骤 {i+1}: {hand_name} (条件不满足)")
                    continue
            
            self.logger.info(f"执行序列步骤 {i+1}/{len(sequence)}: {hand_name}")
            
            # 执行Hand
            result = await self.execute_hand(hand_name, **parameters)
            results.append(result)
            
            # 检查是否需要中断序列
            if not result.success and hand_config.get("break_on_failure", True):
                self.logger.warning(f"序列在第 {i+1} 步中断: {hand_name} 执行失败")
                break
        
        return results
    
    def _evaluate_condition(self, condition: Any, previous_results: List[HandExecutionResult]) -> bool:
        """评估执行条件"""
        if condition is None:
            return True
        
        if isinstance(condition, bool):
            return condition
        
        if isinstance(condition, str):
            # 简单条件表达式
            if condition == "all_success":
                return all(r.success for r in previous_results)
            elif condition == "any_success":
                return any(r.success for r in previous_results)
            elif condition == "last_success":
                return previous_results[-1].success if previous_results else True
        
        return True
    
    def _record_execution(self, result: HandExecutionResult):
        """记录执行历史"""
        self.execution_history.append(result)
        
        # 限制历史记录大小
        if len(self.execution_history) > self.max_history_size:
            self.execution_history.pop(0)
    
    def get_execution_history(self, limit: int = 50) -> List[HandExecutionResult]:
        """获取执行历史"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def clear_history(self):
        """清空执行历史"""
        self.execution_history.clear()
        self.logger.info("执行历史已清空")
    
    async def validate_hand(self, hand_name: str, **kwargs) -> Dict[str, Any]:
        """验证Hand执行"""
        hand = self.registry.get_hand(hand_name)
        
        if not hand:
            return {
                "valid": False,
                "errors": [f"Hand '{hand_name}' 未找到"]
            }
        
        validation_results = {}
        
        # 1. 参数验证
        param_valid = hand.validate_parameters(**kwargs)
        validation_results["parameters_valid"] = param_valid
        
        # 2. 安全检查
        safety_passed = await hand.safety_check(**kwargs)
        validation_results["safety_check_passed"] = safety_passed
        
        # 3. 能力检查
        capability = hand.get_capability()
        validation_results["capability"] = {
            "name": capability.name,
            "category": capability.category.value,
            "safety_level": capability.safety_level.value,
            "version": capability.version
        }
        
        # 综合评估
        valid = param_valid and (safety_passed or hand.safety_level == HandSafetyLevel.SAFE)
        
        return {
            "valid": valid,
            "validation_results": validation_results,
            "recommendation": self._generate_recommendation(hand, param_valid, safety_passed)
        }
    
    def _generate_recommendation(self, hand: BaseHand, param_valid: bool, safety_passed: bool) -> str:
        """生成执行建议"""
        if not param_valid:
            return "参数验证失败，请检查参数"
        
        if not safety_passed:
            if hand.safety_level == HandSafetyLevel.DANGEROUS:
                return "危险操作，需要创业者确认"
            elif hand.safety_level == HandSafetyLevel.RISKY:
                return "高风险操作，建议进行详细审查"
            elif hand.safety_level == HandSafetyLevel.MODERATE:
                return "中等风险操作，建议简单确认"
        
        return "可以安全执行"
    
    async def batch_execute(self, hand_configs: List[Dict[str, Any]], parallel: bool = False) -> List[HandExecutionResult]:
        """批量执行Hands"""
        if parallel:
            return await self._parallel_execute(hand_configs)
        else:
            return await self._sequential_execute(hand_configs)
    
    async def _sequential_execute(self, hand_configs: List[Dict[str, Any]]) -> List[HandExecutionResult]:
        """顺序批量执行"""
        results = []
        
        for config in hand_configs:
            hand_name = config.get("hand")
            parameters = config.get("parameters", {})
            
            result = await self.execute_hand(hand_name, **parameters)
            results.append(result)
            
            # 可选的停止条件
            if config.get("stop_on_failure", False) and not result.success:
                break
        
        return results
    
    async def _parallel_execute(self, hand_configs: List[Dict[str, Any]]) -> List[HandExecutionResult]:
        """并行批量执行"""
        tasks = []
        
        for config in hand_configs:
            hand_name = config.get("hand")
            parameters = config.get("parameters", {})
            
            task = asyncio.create_task(self.execute_hand(hand_name, **parameters))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                hand_name = hand_configs[i].get("hand", "unknown")
                final_results.append(HandExecutionResult(
                    hand_name=hand_name,
                    success=False,
                    output=None,
                    error=f"并行执行异常: {result}"
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        if not self.execution_history:
            return {"total_executions": 0, "success_rate": 0.0}
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        success_rate = successful / total if total > 0 else 0.0
        
        # 按类别统计
        category_stats = {}
        for result in self.execution_history:
            hand = self.registry.get_hand(result.hand_name)
            if hand:
                category = hand.category.value
                if category not in category_stats:
                    category_stats[category] = {"total": 0, "success": 0}
                
                category_stats[category]["total"] += 1
                if result.success:
                    category_stats[category]["success"] += 1
        
        # 计算平均执行时间
        execution_times = [r.execution_time for r in self.execution_history if hasattr(r, 'execution_time')]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": success_rate,
            "average_execution_time": avg_time,
            "by_category": category_stats,
            "recent_executions": [
                {
                    "hand": r.hand_name,
                    "success": r.success,
                    "time": r.execution_time,
                    "timestamp": r.created_at
                }
                for r in self.execution_history[-10:]
            ]
        }
    
    def export_history(self, format: str = "json") -> Optional[str]:
        """导出执行历史"""
        if not self.execution_history:
            return None
        
        history_data = []
        for result in self.execution_history:
            history_data.append({
                "hand_name": result.hand_name,
                "success": result.success,
                "error": result.error,
                "execution_time": result.execution_time,
                "safety_check_passed": result.safety_check_passed,
                "created_at": result.created_at
            })
        
        if format == "json":
            return json.dumps(history_data, indent=2, ensure_ascii=False)
        else:
            self.logger.warning(f"不支持的导出格式: {format}")
            return None