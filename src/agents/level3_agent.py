#!/usr/bin/env python3
"""
Level 3 Autonomous Agent - 自主执行Agent

整合任务分解、执行追踪、验证循环的完整自动化Agent。

使用场景:
- 复杂多步骤任务自动化
- 需要任务验证的研究流程
- 自主决策循环

与 ExecutionCoordinator 的区别:
- ExecutionCoordinator: 轻量级路由 + 单次推理
- Level3Agent: 完整任务分解 + 执行追踪 + 多轮验证
"""

from typing import Dict, Any, Optional, List
"""
Level 3 Autonomous Agent - 自主执行Agent

⚠️ DEPRECATED: 此模块已不再维护。
请使用 core/ExecutionCoordinator 代替。

整合任务分解、执行追踪、验证循环的完整自动化Agent
"""

import warnings
warnings.warn(
    "Level3Agent is deprecated. Use src.core.ExecutionCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)

from typing import Dict, Any, Optional, List
"""
Level 3 Autonomous Agent - 自主执行Agent
整合任务分解、执行追踪、验证循环的完整自动化Agent
"""

from typing import Dict, Any, Optional, List
import asyncio

from src.agents.enhanced_react_agent import EnhancedReActAgentConfig
from src, EnhancedReAct.core.task_decomposition import TaskDecompositionEngine, DecomposedTask, SubTask
from src.core.task_execution_tracker import TaskExecutionTracker, ExecutionStatus
from src.core.verification_loop import VerificationLoop, GAIAStyleVerifier, VerificationResult


class Level3AgentConfig:
    """Level 3 Agent配置"""
    def __init__(
        self,
        enable_task_decomposition: bool = True,
        enable_progress_tracking: bool = True,
        enable_verification: bool = True,
        max_task_retries: int = 3,
        confidence_threshold: float = 0.8
    ):
        self.enable_task_decomposition = enable_task_decomposition
        self.enable_progress_tracking = enable_progress_tracking
        self.enable_verification = enable_verification
        self.max_task_retries = max_task_retries
        self.confidence_threshold = confidence_threshold


class Level3Agent:
    """
    Level 3 自主执行Agent
    
    特性：
    1. 任务自动分解 - 将复杂任务拆分为可执行子任务
    2. 执行进度追踪 - 实时监控任务执行进度
    3. 验证循环 - 自动验证结果质量
    4. 错误恢复 - 支持检查点和重试
    """
    
    def __init__(
        self,
        agent_name: str = "Level3Agent",
        config: Optional[Level3AgentConfig] = None
    ):
        # 初始化配置
        self.config = config or Level3AgentConfig()
        
        # 初始化底层Agent (使用EnhancedReAct)
        enhanced_config = EnhancedReActConfig(
            enable_autonomous_decision=True,
            enable_self_reflection=True,
            confidence_threshold=self.config.confidence_threshold
        )
        self.agent = EnhancedReActAgent(
            agent_name=agent_name,
            enhanced_config=enhanced_config
        )
        
        # 初始化组件
        self.decomposition_engine = TaskDecompositionEngine()
        self.tracker = TaskExecutionTracker()
        self.verifier = GAIAStyleVerifier()
        
        print(f"✅ Level3Agent 初始化完成: {agent_name}")
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 用户任务
            context: 上下文
            
        Returns:
            执行结果
        """
        context = context or {}
        
        print(f"\n🚀 开始执行任务: {task[:50]}...")
        
        # 1. 任务分解
        if self.config.enable_task_decomposition:
            decomposed = self.decomposition_engine.decompose(task, context)
            print(f"📋 任务已分解为 {len(decomposed.sub_tasks)} 个子任务")
            
            # 注册所有子任务到追踪器
            self.tracker.start_execution()
            for sub_task in decomposed.sub_tasks:
                self.tracker.register_task(sub_task.id, sub_task.name)
            
            # 执行子任务
            results = await self._execute_sub_tasks(decomposed.sub_tasks, context)
            
            # 验证结果
            final_result = self._combine_results(results)
            verification = self.verifier.verify_task_completion(task, final_result)
            
            if verification.status == "failed" or verification.status == "needs_improvement":
                print(f"⚠️ 验证失败: {verification.message}")
                if verification.retry_needed:
                    # 重试
                    final_result = await self._retry_task(task, context, verification)
            
            # 更新追踪器
            self.tracker.complete_execution()
            
            return {
                "task": task,
                "result": final_result,
                "verification": {
                    "status": verification.status.value,
                    "message": verification.message,
                    "suggestions": verification.suggestions
                },
                "statistics": self.tracker.get_statistics()
            }
        else:
            # 简单模式：直接使用底层Agent
            result = await self.agent.execute({"query": task, **context})
            return {
                "task": task,
                "result": result,
                "verification": None,
                "statistics": None
            }
    
    async def _execute_sub_tasks(
        self, 
        sub_tasks: List[SubTask], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行子任务"""
        results = {}
        
        # 按执行计划分组执行
        for batch in self._get_execution_batches(sub_tasks):
            # 获取该批次的所有子任务
            batch_tasks = [t for t in sub_tasks if t.id in batch]
            
            # 并行执行（如果有多个）
            if len(batch_tasks) > 1:
                task_coroutines = [
                    self._execute_single_task(sub_task, context)
                    for sub_task in batch_tasks
                ]
                batch_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
                
                for sub_task, result in zip(batch_tasks, batch_results):
                    results[sub_task.id] = result
                    if isinstance(result, Exception):
                        self.tracker.fail_task(sub_task.id, str(result))
                    else:
                        self.tracker.complete_task(sub_task.id, result)
            else:
                # 顺序执行
                for sub_task in batch_tasks:
                    result = await self._execute_single_task(sub_task, context)
                    results[sub_task.id] = result
                    
                    if isinstance(result, Exception):
                        self.tracker.fail_task(sub_task.id, str(result))
                    else:
                        self.tracker.complete_task(sub_task.id, result)
        
        return results
    
    async def _execute_single_task(
        self, 
        sub_task: SubTask, 
        context: Dict[str, Any]
    ) -> Any:
        """执行单个子任务"""
        self.tracker.update_progress(sub_task.id, 50, f"执行中: {sub_task.name}")
        
        try:
            # 使用底层Agent执行
            result = await self.agent.execute({
                "query": sub_task.description or sub_task.name,
                **context
            })
            
            # 如果有指定工具，直接调用
            if sub_task.tool_name:
                tool = self.agent.tool_registry.get_tool(sub_task.tool_name)
                if tool:
                    tool_result = await tool.execute(sub_task.parameters)
                    return tool_result.data if hasattr(tool_result, 'data') else tool_result
            
            return result
        except Exception as e:
            print(f"❌ 子任务执行失败: {sub_task.name}, 错误: {e}")
            return e
    
    def _get_execution_batches(self, sub_tasks: List[SubTask]) -> List[List[str]]:
        """获取执行批次"""
        # 简单实现：按顺序分组
        batches = []
        current_batch = []
        
        for task in sub_tasks:
            # 检查依赖
            deps = task.dependencies
            if deps and any(d in current_batch for d in deps):
                # 有未完成的依赖，推迟到下一批
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                current_batch.append(task.id)
            else:
                current_batch.append(task.id)
        
        if current_batch:
            batches.append(current_batch)
        
        return batches if batches else [[t.id for t in sub_tasks]]
    
    def _combine_results(self, results: Dict[str, Any]) -> str:
        """合并子任务结果"""
        if not results:
            return "没有执行结果"
        
        combined = []
        for task_id, result in results.items():
            if isinstance(result, Exception):
                combined.append(f"错误: {str(result)}")
            else:
                combined.append(str(result))
        
        return "\n\n".join(combined)
    
    async def _retry_task(
        self, 
        task: str, 
        context: Dict[str, Any],
        last_verification: VerificationResult
    ) -> Any:
        """重试任务"""
        print(f"🔄 开始重试 (剩余: {self.config.max_task_retries} 次)")
        
        for retry in range(self.config.max_task_retries):
            # 根据建议改进任务
            improved_context = {**context}
            if last_verification.suggestions:
                improved_context["improvement_hint"] = "; ".join(last_verification.suggestions)
            
            # 重新执行
            result = await self.execute(task, improved_context)
            
            # 验证
            verification = self.verifier.verify_task_completion(
                task, 
                result.get("result", ""),
                context.get("expected_elements")
            )
            
            if verification.status == "passed":
                return result.get("result", "")
            
            last_verification = verification
        
        return "任务执行多次后仍未能通过验证"


# 便捷函数
def create_level3_agent(
    agent_name: str = "Level3Agent",
    enable_task_decomposition: bool = True,
    enable_verification: bool = True
) -> Level3Agent:
    """创建Level 3 Agent"""
    config = Level3AgentConfig(
        enable_task_decomposition=enable_task_decomposition,
        enable_verification=enable_verification
    )
    return Level3Agent(agent_name=agent_name, config=config)
