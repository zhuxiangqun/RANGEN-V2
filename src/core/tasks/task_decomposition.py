#!/usr/bin/env python3
"""
Task Decomposition Engine - 任务分解引擎
自动将复杂任务分解为可执行的子任务
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


class TaskType(Enum):
    """任务类型"""
    SIMPLE = "simple"           # 简单任务 - 一步完成
    SEQUENTIAL = "sequential"  # 顺序任务 - 多步按序
    PARALLEL = "parallel"      # 并行任务 - 多步可同时
    CONDITIONAL = "conditional" # 条件任务 - 有分支
    ITERATIVE = "iterative"    # 迭代任务 - 循环执行


class TaskStatus(Enum):
    """子任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubTask:
    """子任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.SIMPLE
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)  # 依赖的子任务ID
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    execution_order: int = 0


@dataclass
class DecomposedTask:
    """分解后的任务"""
    original_task: str
    task_type: TaskType
    sub_tasks: List[SubTask]
    execution_plan: List[List[str]] = field(default_factory=list)  # 可并行执行的批次
    estimated_duration: float = 0.0


class TaskDecompositionEngine:
    """
    任务分解引擎
    
    功能：
    1. 分析任务复杂度
    2. 识别任务类型
    3. 分解为可执行的子任务
    4. 生成执行计划（考虑依赖和并行性）
    """
    
    def __init__(self):
        # 任务类型识别关键词
        self.task_type_keywords = {
            TaskType.SIMPLE: [
                "查询", "搜索", "获取", "找到", "什么是",
                "tell me", "find", "get", "what is"
            ],
            TaskType.SEQUENTIAL: [
                "首先", "然后", "接着", "最后", "步骤",
                "first", "then", "next", "finally", "steps"
            ],
            TaskType.PARALLEL: [
                "同时", "并行", "分别", "多个",
                "at the same time", "both", "all", "each"
            ],
            TaskType.CONDITIONAL: [
                "如果", "那么", "否则", "根据",
                "if", "then", "else", "depending on"
            ],
            TaskType.ITERATIVE: [
                "遍历", "每个", "全部", "重复",
                "each", "every", "all", "loop"
            ]
        }
    
    def decompose(self, task: str, context: Optional[Dict[str, Any]] = None) -> DecomposedTask:
        """
        分解任务
        
        Args:
            task: 原始任务描述
            context: 上下文信息
            
        Returns:
            DecomposedTask: 分解后的任务
        """
        context = context or {}
        
        # 1. 识别任务类型
        task_type = self._identify_task_type(task)
        
        # 2. 生成子任务
        sub_tasks = self._generate_sub_tasks(task, task_type, context)
        
        # 3. 生成执行计划
        execution_plan = self._create_execution_plan(sub_tasks)
        
        # 4. 估算执行时间
        estimated_duration = self._estimate_duration(sub_tasks)
        
        return DecomposedTask(
            original_task=task,
            task_type=task_type,
            sub_tasks=sub_tasks,
            execution_plan=execution_plan,
            estimated_duration=estimated_duration
        )
    
    def _identify_task_type(self, task: str) -> TaskType:
        """识别任务类型"""
        task_lower = task.lower()
        
        # 按优先级检查
        for task_type, keywords in self.task_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in task_lower:
                    return task_type
        
        # 默认顺序任务
        return TaskType.SEQUENTIAL
    
    def _generate_sub_tasks(
        self, 
        task: str, 
        task_type: TaskType,
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """生成子任务"""
        sub_tasks = []
        
        if task_type == TaskType.SIMPLE:
            # 简单任务 - 单个子任务
            sub_tasks.append(SubTask(
                name="执行任务",
                description=task,
                task_type=TaskType.SIMPLE,
                tool_name=self._suggest_tool(task),
                parameters={"query": task}
            ))
        
        elif task_type == TaskType.SEQUENTIAL:
            # 顺序任务 - 多个按序子任务
            sub_tasks = self._decompose_sequential(task, context)
        
        elif task_type == TaskType.PARALLEL:
            # 并行任务
            sub_tasks = self._decompose_parallel(task, context)
        
        elif task_type == TaskType.CONDITIONAL:
            # 条件任务
            sub_tasks = self._decompose_conditional(task, context)
        
        elif task_type == TaskType.ITERATIVE:
            # 迭代任务
            sub_tasks = self._decompose_iterative(task, context)
        
        return sub_tasks
    
    def _decompose_sequential(
        self, 
        task: str, 
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """分解顺序任务"""
        sub_tasks = []
        
        # 尝试识别步骤
        step_indicators = ["首先", "然后", "接着", "最后", "step 1", "step 2"]
        
        has_steps = any(indicator in task.lower() for indicator in step_indicators)
        
        if has_steps:
            # 从任务中提取步骤
            steps = self._extract_steps(task)
            for i, step in enumerate(steps):
                sub_tasks.append(SubTask(
                    name=f"步骤 {i+1}",
                    description=step,
                    task_type=TaskType.SEQUENTIAL,
                    tool_name=self._suggest_tool(step),
                    parameters={"query": step},
                    execution_order=i
                ))
        else:
            # 默认分解：理解 -> 检索 -> 处理 -> 回答
            sub_tasks = [
                SubTask(
                    name="理解任务",
                    description="理解用户意图和需求",
                    task_type=TaskType.SEQUENTIAL,
                    execution_order=0
                ),
                SubTask(
                    name="收集信息",
                    description="检索相关信息",
                    task_type=TaskType.SEQUENTIAL,
                    tool_name="knowledge_retrieval",
                    parameters={"query": task},
                    execution_order=1
                ),
                SubTask(
                    name="处理信息",
                    description="分析和处理收集的信息",
                    task_type=TaskType.SEQUENTIAL,
                    tool_name="reasoning",
                    parameters={"query": task},
                    execution_order=2
                ),
                SubTask(
                    name="生成答案",
                    description="生成最终答案",
                    task_type=TaskType.SEQUENTIAL,
                    tool_name="answer_generation",
                    parameters={"query": task},
                    execution_order=3
                )
            ]
        
        return sub_tasks
    
    def _decompose_parallel(
        self, 
        task: str, 
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """分解并行任务"""
        sub_tasks = []
        
        # 尝试识别多个目标
        targets = self._extract_parallel_targets(task)
        
        for i, target in enumerate(targets):
            sub_tasks.append(SubTask(
                name=f"任务 {i+1}",
                description=target,
                task_type=TaskType.PARALLEL,
                tool_name=self._suggest_tool(target),
                parameters={"query": target},
                execution_order=i
            ))
        
        return sub_tasks
    
    def _decompose_conditional(
        self, 
        task: str, 
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """分解条件任务"""
        sub_tasks = []
        
        # 识别条件分支
        branches = self._extract_branches(task)
        
        for i, branch in enumerate(branches):
            sub_tasks.append(SubTask(
                name=f"分支 {i+1}",
                description=branch,
                task_type=TaskType.CONDITIONAL,
                tool_name=self._suggest_tool(branch),
                parameters={"query": branch},
                execution_order=i
            ))
        
        return sub_tasks
    
    def _decompose_iterative(
        self, 
        task: str, 
        context: Dict[str, Any]
    ) -> List[SubTask]:
        """分解迭代任务"""
        sub_tasks = [
            SubTask(
                name="准备迭代",
                description="初始化迭代环境和数据",
                task_type=TaskType.ITERATIVE,
                execution_order=0
            ),
            SubTask(
                name="执行迭代",
                description="循环执行直到满足条件",
                task_type=TaskType.ITERATIVE,
                tool_name="reasoning",
                parameters={"query": task},
                execution_order=1
            ),
            SubTask(
                name="完成迭代",
                description="收集结果并结束",
                task_type=TaskType.ITERATIVE,
                execution_order=2
            )
        ]
        
        return sub_tasks
    
    def _extract_steps(self, task: str) -> List[str]:
        """提取步骤"""
        steps = []
        
        # 简单分割
        separators = ["首先", "然后", "接着", "最后", ";", "。" ]
        parts = [task]
        
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        steps = [p.strip() for p in parts if p.strip()]
        
        return steps if steps else [task]
    
    def _extract_parallel_targets(self, task: str) -> List[str]:
        """提取并行目标"""
        # 简化：返回任务本身
        return [task]
    
    def _extract_branches(self, task: str) -> List[str]:
        """提取条件分支"""
        # 简化：返回任务本身
        return [task]
    
    def _suggest_tool(self, task: str) -> Optional[str]:
        """建议工具"""
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["搜索", "查找", "search", "find"]):
            return "search"
        elif any(kw in task_lower for kw in ["分析", "reason", "think"]):
            return "reasoning"
        elif any(kw in task_lower for kw in ["浏览", "网页", "browser", "web"]):
            return "browser"
        elif any(kw in task_lower for kw in ["图片", "图像", "image"]):
            return "multimodal"
        elif any(kw in task_lower for kw in ["计算", "calculate"]):
            return "calculator"
        
        return "knowledge_retrieval"
    
    def _create_execution_plan(self, sub_tasks: List[SubTask]) -> List[List[str]]:
        """创建执行计划 - 识别可并行的任务"""
        if not sub_tasks:
            return []
        
        # 按执行顺序分组
        order_groups = {}
        for task in sub_tasks:
            order = task.execution_order
            if order not in order_groups:
                order_groups[order] = []
            order_groups[order].append(task.id)
        
        # 转换为列表
        execution_plan = list(order_groups.values())
        
        return execution_plan
    
    def _estimate_duration(self, sub_tasks: List[SubTask]) -> float:
        """估算执行时间（秒）"""
        # 每个子任务平均 5 秒
        return len(sub_tasks) * 5.0


# 便捷函数
def decompose_task(task: str, context: Optional[Dict[str, Any]] = None) -> DecomposedTask:
    """分解任务的便捷函数"""
    engine = TaskDecompositionEngine()
    return engine.decompose(task, context)
