#!/usr/bin/env python3
"""
Ralph Loop 持续迭代模块
对齐 Claude Code 的 Ralph Wiggum Loop 范式

核心功能:
- 持续迭代直到任务真正完成
- 外部状态感知 (代码、Git历史)
- Stop Hook 阻止过早退出
- 安全阀防止无限循环
"""
import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from src.core.stop_hook import StopHook, CompletionCriterion, CriterionType, create_stop_hook

logger = logging.getLogger(__name__)


class LoopState(str, Enum):
    """循环状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    MAX_ITERATIONS = "max_iterations"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class IterationResult:
    """单次迭代结果"""
    iteration: int
    state: LoopState
    agent_output: Any = None
    completion_status: Optional[bool] = None
    stop_hook_results: Optional[Dict[str, Any]] = None
    external_state: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class LoopConfig:
    """循环配置"""
    max_iterations: int = 50
    iteration_timeout: int = 300  # 单次迭代超时(秒)
    pause_between_iterations: float = 1.0  # 迭代间隔(秒)
    collect_external_state: bool = True  # 收集外部状态
    early_stop_on_error: bool = False  # 错误时提前停止
    log_level: str = "INFO"


class RalphLoop:
    """Ralph Loop - AI Agent 持续迭代
    
    核心思想:
    - 同一任务反复执行
    - 每次迭代收集外部状态 (代码变化、Git历史)
    - 使用StopHook验证完成条件
    - 直到满足所有条件才退出
    """
    
    def __init__(self, config: Optional[LoopConfig] = None):
        self.config = config or LoopConfig()
        self.stop_hook = StopHook()
        
        # 状态
        self.state = LoopState.IDLE
        self.current_iteration = 0
        self.iteration_results: List[IterationResult] = []
        
        # 回调
        self.on_iteration_start: Optional[Callable] = None
        self.on_iteration_end: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
        
        # 外部状态收集器
        self.external_state_collectors: List[Callable] = []
        
        logger.info(f"RalphLoop initialized (max_iterations={self.config.max_iterations})")
    
    def set_completion_criteria(self, criteria: List[str]):
        """设置完成条件
        
        Args:
            criteria: 条件列表
                - "pytest tests/ -v"
                - "coverage > 80"
                - "file_exists: tests/test_*.py"
        """
        self.stop_hook.add_criteria_from_list(criteria)
        logger.info(f"Set {len(criteria)} completion criteria")
    
    def add_external_state_collector(self, collector: Callable):
        """添加外部状态收集器"""
        self.external_state_collectors.append(collector)
    
    def collect_external_state(self) -> Dict[str, Any]:
        """收集外部状态
        
        让Agent看到自己的历史工作成果
        """
        state = {
            "timestamp": time.time(),
            "iteration": self.current_iteration
        }
        
        # Git状态
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            state["git_changes"] = result.stdout.strip()[:500] if result.stdout else ""
            
            # 最近commit
            result = subprocess.run(
                ["git", "log", "--oneline", "-3"],
                capture_output=True,
                text=True,
                timeout=5
            )
            state["git_recent_commits"] = result.stdout.strip()[:300] if result.stdout else ""
        except:
            pass
        
        # 文件状态
        try:
            project_files = list(Path(".").glob("src/**/*.py"))
            state["project_files_count"] = len(project_files)
        except:
            pass
        
        # 自定义收集器
        for collector in self.external_state_collectors:
            try:
                custom_state = collector()
                state.update(custom_state)
            except Exception as e:
                logger.warning(f"External state collector failed: {e}")
        
        return state
    
    async def run_until_complete(
        self, 
        task: str,
        agent_executor: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> IterationResult:
        """持续运行直到完成
        
        Args:
            task: 任务描述
            agent_executor: Agent执行函数 (async def execute(task, context) -> result)
            context: 初始上下文
            
        Returns:
            最终迭代结果
        """
        self.state = LoopState.RUNNING
        self.current_iteration = 0
        self.iteration_results = []
        
        ctx = context or {}
        
        logger.info(f"Starting RalphLoop: {task}")
        logger.info(f"Completion criteria: {len(self.stop_hook.criteria)} conditions")
        
        while self.current_iteration < self.config.max_iterations:
            self.current_iteration += 1
            iteration_start = time.time()
            
            logger.info(f"=== Iteration {self.current_iteration}/{self.config.max_iterations} ===")
            
            # 迭代开始回调
            if self.on_iteration_start:
                self.on_iteration_start(self.current_iteration, task, ctx)
            
            try:
                # 收集外部状态
                external_state = {}
                if self.config.collect_external_state:
                    external_state = self.collect_external_state()
                    logger.debug(f"External state: {list(external_state.keys())}")
                
                # 添加外部状态到上下文
                ctx["external_state"] = external_state
                ctx["iteration"] = self.current_iteration
                ctx["previous_results"] = [
                    r.agent_output for r in self.iteration_results
                ]
                
                # 执行Agent
                logger.debug(f"Executing agent with task: {task[:100]}...")
                agent_output = await asyncio.wait_for(
                    agent_executor(task, ctx),
                    timeout=self.config.iteration_timeout
                )
                
                # 检查完成条件
                current_state = {
                    "task": task,
                    "iteration": self.current_iteration,
                    "agent_output": agent_output,
                    "external_state": external_state
                }
                
                should_continue = self.stop_hook.should_continue(current_state)
                stop_hook_summary = self.stop_hook.get_summary()
                
                iteration_time = time.time() - iteration_start
                
                result = IterationResult(
                    iteration=self.current_iteration,
                    state=LoopState.RUNNING,
                    agent_output=agent_output,
                    completion_status=not should_continue,
                    stop_hook_results=stop_hook_summary,
                    external_state=external_state,
                    execution_time=iteration_time
                )
                
                self.iteration_results.append(result)
                
                # 迭代结束回调
                if self.on_iteration_end:
                    self.on_iteration_end(result)
                
                # 判断是否完成
                if not should_continue:
                    self.state = LoopState.COMPLETED
                    logger.info(
                        f"✅ Task completed at iteration {self.current_iteration} "
                        f"({stop_hook_summary['passed']}/{stop_hook_summary['total']} criteria met)"
                    )
                    return result
                
                # 迭代间隔
                if self.current_iteration < self.config.max_iterations:
                    await asyncio.sleep(self.config.pause_between_iterations)
                
                # 更新任务继续执行
                task = self._generate_continue_prompt(task, agent_output, stop_hook_summary)
                
            except asyncio.TimeoutError:
                error_msg = f"Iteration {self.current_iteration} timeout"
                logger.warning(error_msg)
                
                result = IterationResult(
                    iteration=self.current_iteration,
                    state=LoopState.RUNNING,
                    error=error_msg,
                    execution_time=time.time() - iteration_start
                )
                self.iteration_results.append(result)
                
                if self.config.early_stop_on_error:
                    self.state = LoopState.FAILED
                    return result
                    
            except Exception as e:
                error_msg = f"Iteration {self.current_iteration} failed: {e}"
                logger.error(error_msg)
                
                result = IterationResult(
                    iteration=self.current_iteration,
                    state=LoopState.FAILED,
                    error=error_msg,
                    execution_time=time.time() - iteration_start
                )
                self.iteration_results.append(result)
                
                if self.config.early_stop_on_error:
                    self.state = LoopState.FAILED
                    return result
        
        # 达到最大迭代次数
        self.state = LoopState.MAX_ITERATIONS
        logger.warning(
            f"⚠️ Max iterations ({self.config.max_iterations}) reached"
        )
        
        return self.iteration_results[-1] if self.iteration_results else None
    
    def _generate_continue_prompt(
        self, 
        original_task: str, 
        agent_output: Any,
        stop_hook_summary: Dict[str, Any]
    ) -> str:
        """生成继续执行的提示"""
        
        failed_criteria = []
        for result in stop_hook_summary.get("results", []):
            if not result["success"]:
                failed_criteria.append(result["criterion_id"])
        
        continue_prompt = f"""继续完成以下任务: {original_task}

上次执行结果:
{agent_output}

尚未满足的条件:
{', '.join(failed_criteria)}

请继续执行，直到所有条件都满足。"""
        
        return continue_prompt
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取运行统计"""
        if not self.iteration_results:
            return {"state": self.state.value, "iterations": 0}
        
        total_time = sum(r.execution_time for r in self.iteration_results)
        successful = sum(1 for r in self.iteration_results if r.completion_status)
        
        return {
            "state": self.state.value,
            "total_iterations": len(self.iteration_results),
            "current_iteration": self.current_iteration,
            "total_time": total_time,
            "avg_iteration_time": total_time / len(self.iteration_results),
            "completion_rate": successful / len(self.iteration_results),
            "final_status": self.iteration_results[-1].completion_status if self.iteration_results else None
        }
    
    def cancel(self):
        """取消循环"""
        self.state = LoopState.CANCELLED
        logger.info("RalphLoop cancelled")
    
    def reset(self):
        """重置循环"""
        self.state = LoopState.IDLE
        self.current_iteration = 0
        self.iteration_results.clear()
        self.stop_hook.clear()
        logger.info("RalphLoop reset")


class RalphLoopBuilder:
    """RalphLoop 建造者"""
    
    def __init__(self):
        self.config = LoopConfig()
        self.criteria: List[str] = []
        self.external_collectors: List[Callable] = []
    
    def max_iterations(self, n: int) -> "RalphLoopBuilder":
        self.config.max_iterations = n
        return self
    
    def timeout(self, seconds: int) -> "RalphLoopBuilder":
        self.config.iteration_timeout = seconds
        return self
    
    def completion_criteria(self, *criteria: str) -> "RalphLoopBuilder":
        self.criteria.extend(criteria)
        return self
    
    def collect_external_state(self, enabled: bool = True) -> "RalphLoopBuilder":
        self.config.collect_external_state = enabled
        return self
    
    def early_stop_on_error(self, enabled: bool = True) -> "RalphLoopBuilder":
        self.config.early_stop_on_error = enabled
        return self
    
    def on_iteration_start(self, callback: Callable) -> "RalphLoopBuilder":
        return self
    
    def on_iteration_end(self, callback: Callable) -> "RalphLoopBuilder":
        return self
    
    def build(self) -> RalphLoop:
        loop = RalphLoop(self.config)
        
        if self.criteria:
            loop.set_completion_criteria(self.criteria)
        
        for collector in self.external_collectors:
            loop.add_external_state_collector(collector)
        
        return loop


# 便捷函数
def create_ralph_loop(
    max_iterations: int = 50,
    criteria: List[str] = None
) -> RalphLoop:
    """创建RalphLoop实例"""
    config = LoopConfig(max_iterations=max_iterations)
    loop = RalphLoop(config)
    
    if criteria:
        loop.set_completion_criteria(criteria)
    
    return loop


async def run_task_with_ralph_loop(
    task: str,
    agent_executor: Callable,
    completion_criteria: List[str],
    max_iterations: int = 50
) -> IterationResult:
    """快速运行任务"""
    loop = create_ralph_loop(max_iterations, completion_criteria)
    return await loop.run_until_complete(task, agent_executor)
