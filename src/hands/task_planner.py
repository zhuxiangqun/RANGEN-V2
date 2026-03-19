#!/usr/bin/env python3
"""
Task Planner - 任务规划器

将用户查询分解为可执行的 Hand 调用序列。

功能：
1. 任务分解 - 使用 TaskDecompositionEngine
2. Hand 映射 - 将子任务映射到 Hands
3. 执行规划 - 生成并行/顺序执行计划
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base import BaseHand
from .registry import HandRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: int
    hand_name: str
    hand: BaseHand
    action: str
    parameters: Dict[str, Any]
    dependencies: List[int]  # 依赖的步骤ID
    parallel_group: int  # 并行组号，-1表示不并行


@dataclass
class ExecutionPlan:
    """执行计划"""
    steps: List[ExecutionStep]
    parallel_groups: List[List[int]]  # 可并行执行的步骤组
    estimated_time: float
    complexity: str  # simple, moderate, complex


class TaskPlanner:
    """
    任务规划器 - 连接任务分解和 Hand 执行
    """
    
    def __init__(self, registry: Optional[HandRegistry] = None):
        self.logger = logger
        self.registry = registry or HandRegistry()
        self._decomposition_engine = None
        
        # 操作关键词映射
        self._action_keywords = {
            "fetch": ["获取", "收", "读取", "拉取", "fetch", "get", "read"],
            "send": ["发送", "发", "send", "post"],
            "search": ["搜索", "查找", "查询", "search", "find", "query"],
            "create": ["创建", "新建", "添加", "create", "new", "add"],
            "update": ["更新", "修改", "edit", "update", "modify"],
            "delete": ["删除", "移除", "delete", "remove"],
            "list": ["列表", "列出", "list", "show"],
        }
    
    def _get_decomposition_engine(self):
        """懒加载任务分解引擎"""
        if self._decomposition_engine is None:
            try:
                from src.core.task_decomposition import TaskDecompositionEngine
                self._decomposition_engine = TaskDecompositionEngine()
                self.logger.info("任务分解引擎初始化成功")
            except Exception as e:
                self.logger.warning(f"任务分解引擎初始化失败: {e}")
                self._decomposition_engine = None
        return self._decomposition_engine
    
    def plan(
        self, 
        query: str, 
        recommended_hands: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成执行计划
        
        Args:
            query: 用户查询
            recommended_hands: 推荐的 Hands 列表
            
        Returns:
            执行计划
        """
        # 1. 任务分解
        decomposed = self._decompose_task(query)
        
        # 2. 映射到 Hands
        steps = self._map_to_hands(decomposed, recommended_hands, query)
        
        # 3. 生成并行计划
        parallel_groups = self._create_parallel_groups(steps)
        
        # 4. 估算时间
        estimated_time = self._estimate_time(steps)
        
        return {
            "steps": [
                {
                    "step_id": s.step_id,
                    "hand_name": s.hand_name,
                    "action": s.action,
                    "parameters": s.parameters,
                    "dependencies": s.dependencies,
                    "parallel_group": s.parallel_group
                }
                for s in steps
            ],
            "parallel_groups": parallel_groups,
            "estimated_time": estimated_time,
            "complexity": decomposed.get("complexity", "simple"),
            "can_parallel": len(parallel_groups) > 1
        }
    
    def _decompose_task(self, task: str) -> Dict[str, Any]:
        """分解任务"""
        engine = self._get_decomposition_engine()
        
        if engine:
            try:
                result = engine.decompose(task)
                return {
                    "task_type": result.task_type.value,
                    "sub_tasks": [
                        {
                            "id": st.id,
                            "name": st.name,
                            "description": st.description,
                            "dependencies": st.dependencies
                        }
                        for st in result.sub_tasks
                    ],
                    "execution_plan": result.execution_plan,
                    "complexity": self._assess_complexity(result),
                    "estimated_duration": result.estimated_duration
                }
            except Exception as e:
                self.logger.warning(f"任务分解失败: {e}")
        
        # 回退到简单分解
        return self._simple_decompose(task)
    
    def _simple_decompose(self, task: str) -> Dict[str, Any]:
        """简单的任务分解"""
        # 检测操作类型
        actions = []
        for action, keywords in self._action_keywords.items():
            for keyword in keywords:
                if keyword in task.lower():
                    actions.append(action)
                    break
        
        if not actions:
            actions = ["execute"]  # 默认执行
        
        return {
            "task_type": "simple",
            "sub_tasks": [
                {
                    "id": "1",
                    "name": "执行任务",
                    "description": task,
                    "dependencies": []
                }
            ],
            "actions": actions,
            "complexity": "simple",
            "estimated_duration": 1.0
        }
    
    def _assess_complexity(self, decomposed_task) -> str:
        """评估任务复杂度"""
        num_tasks = len(decomposed_task.sub_tasks)
        
        if num_tasks <= 1:
            return "simple"
        elif num_tasks <= 3:
            return "moderate"
        else:
            return "complex"
    
    def _map_to_hands(
        self, 
        decomposed: Dict[str, Any], 
        recommended_hands: List[Dict[str, Any]],
        query: str
    ) -> List[ExecutionStep]:
        """将子任务映射到 Hands"""
        steps = []
        step_id = 1
        
        # 获取主 Hand
        primary_hand = recommended_hands[0] if recommended_hands else None
        
        if not primary_hand:
            return steps
        
        hand = primary_hand["hand"]
        
        # 提取操作
        action = self._extract_action(query)
        
        # 提取参数
        parameters = self._extract_parameters(query, action)
        
        # 创建执行步骤
        for sub_task in decomposed.get("sub_tasks", []):
            step = ExecutionStep(
                step_id=step_id,
                hand_name=hand.name,
                hand=hand,
                action=action,
                parameters=parameters,
                dependencies=[int(d) for d in sub_task.get("dependencies", [])],
                parallel_group=0
            )
            steps.append(step)
            step_id += 1
        
        # 如果没有子任务，创建一个默认步骤
        if not steps:
            step = ExecutionStep(
                step_id=1,
                hand_name=hand.name,
                hand=hand,
                action=action,
                parameters=parameters,
                dependencies=[],
                parallel_group=0
            )
            steps.append(step)
        
        return steps
    
    def _extract_action(self, query: str) -> str:
        """从查询中提取操作"""
        query_lower = query.lower()
        
        for action, keywords in self._action_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return action
        
        return "execute"
    
    def _extract_parameters(self, query: str, action: str) -> Dict[str, Any]:
        """从查询中提取参数"""
        params = {"operation": action}
        
        # 根据操作类型添加默认参数
        if action == "fetch":
            if "邮件" in query or "email" in query.lower():
                params["operation"] = "fetch_unread"
        
        elif action == "send":
            if "邮件" in query or "email" in query.lower():
                params["operation"] = "send"
        
        elif action == "search":
            if "邮件" in query or "email" in query.lower():
                params["operation"] = "search"
            # 提取搜索词
            search_term = query.replace("搜索", "").replace("查找", "").replace("搜索", "").strip()
            if search_term:
                params["query"] = search_term
        
        # 提取邮箱地址
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        if emails:
            params["email"] = emails[0]
        
        return params
    
    def _create_parallel_groups(self, steps: List[ExecutionStep]) -> List[List[int]]:
        """创建并行执行组"""
        if not steps:
            return []
        
        # 简单策略：无依赖的步骤可以并行
        groups = []
        processed = set()
        
        for step in steps:
            if step.step_id in processed:
                continue
            
            # 检查依赖
            deps = set(step.dependencies)
            if not deps:
                # 无依赖，加入当前组
                current_group = [step.step_id]
                processed.add(step.step_id)
                
                # 查找其他无依赖的步骤
                for other_step in steps:
                    if other_step.step_id not in processed and not other_step.dependencies:
                        current_group.append(other_step.step_id)
                        processed.add(other_step.step_id)
                
                groups.append(current_group)
            else:
                # 有依赖，单独执行
                groups.append([step.step_id])
                processed.add(step.step_id)
        
        return groups
    
    def _estimate_time(self, steps: List[ExecutionStep]) -> float:
        """估算执行时间（秒）"""
        if not steps:
            return 0.0
        
        # 简单估算：每个步骤约 1 秒
        base_time = len(steps) * 1.0
        
        # 并行优化
        parallel_groups = self._create_parallel_groups(steps)
        if len(parallel_groups) > 1:
            # 并行可以减少时间
            base_time *= 0.6
        
        return base_time
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行计划"""
        results = []
        errors = []
        
        for step_data in plan.get("steps", []):
            hand_name = step_data["hand_name"]
            parameters = step_data.get("parameters", {})
            
            hand = self.registry.get_hand(hand_name)
            if not hand:
                errors.append(f"Hand 不存在: {hand_name}")
                continue
            
            try:
                result = await hand.execute(**parameters)
                results.append({
                    "step_id": step_data["step_id"],
                    "hand_name": hand_name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                })
            except Exception as e:
                errors.append(f"执行失败 {hand_name}: {e}")
                results.append({
                    "step_id": step_data["step_id"],
                    "hand_name": hand_name,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "total_steps": len(plan.get("steps", [])),
            "completed_steps": len([r for r in results if r.get("success")])
        }
