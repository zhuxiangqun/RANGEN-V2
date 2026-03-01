#!/usr/bin/env python3
"""
Self-Evolving Mixin 自进化混入类

为现有 Agent 赋予自进化能力的混入类

使用方法:
    class MyAgent(BaseAgent, SelfEvolvingMixin):
        def __init__(self, ...):
            super().__init__(...)
            self.init_self_evolving(config)
            
功能:
- 任务执行时自动收集反馈
- 失败时自动反思和改进
- 多轨迹探索(可选)
- 模式学习与存储
- 与 Knowledge Management System 集成
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.core.self_evolving_agent import EvolutionConfig, EvolutionStrategy, AgentState
    from src.core.self_evolving_agent import SelfEvolvingAgent, EvolutionResult

from src.core.self_evolving_agent import (
    SelfEvolvingAgent, EvolutionConfig, EvolutionStrategy,
    EvolutionStage, AgentState, EvolutionResult
)
from src.core.reflection import ReflexionAgent, ReflectionResult
from src.core.multi_trajectory import MultiTrajectoryExplorer, ExplorerConfig

logger = logging.getLogger(__name__)


@dataclass
class SelfEvolvingConfig:
    """自进化配置"""
    enabled: bool = True                      # 是否启用
    enable_reflection: bool = True            # 启用反思
    enable_multi_trajectory: bool = False     # 启用多轨迹(计算密集)
    enable_pattern_learning: bool = True      # 启用模式学习
    min_success_rate_threshold: float = 0.7    # 最低成功率阈值
    max_consecutive_failures: int = 3         # 最大连续失败次数
    auto_reflect_on_failure: bool = True      # 失败时自动反思
    pattern_storage_enabled: bool = True      # 存储模式到KMS
    reflection_threshold: float = 0.6          # 反思置信度阈值


class SelfEvolvingMixin:
    """自进化混入类
    
    可被混入到任何 Agent 类中，赋予自进化能力
    """
    
    def init_self_evolving(
        self,
        config: Optional[SelfEvolvingConfig] = None,
        llm_provider=None
    ) -> None:
        """初始化自进化能力
        
        Args:
            config: 自进化配置
            llm_provider: LLM提供者
        """
        self.self_evolving_config = config or SelfEvolvingConfig()
        self.llm_provider = llm_provider
        
        # 安全获取 agent_id
        self._se_agent_id = getattr(self, 'agent_id', 'self_evolving_agent')
        
        if not self.self_evolving_config.enabled:
            logger.info(f"{self._se_agent_id}: Self-evolving disabled")
            return
        self.llm_provider = llm_provider
        
        if not self.self_evolving_config.enabled:
            logger.info(f"{self._se_agent_id}: Self-evolving disabled")
            return
            
        # 初始化组件
        self._init_self_evolving_components()
        
        # 状态跟踪
        self._evolution_state = AgentState()
        self._consecutive_failures = 0
        self._total_tasks = 0
        self._successful_tasks = 0
        
        logger.info(f"{self._se_agent_id}: Self-evolving initialized")
    
    def _init_self_evolving_components(self) -> None:
        """初始化自进化组件"""
        config = self.self_evolving_config
        
        # 反思组件
        if config.enable_reflection:
            self._reflection_agent = ReflexionAgent(self.llm_provider)
        else:
            self._reflection_agent = None
        
        # 多轨迹探索器(可选，计算密集)
        if config.enable_multi_trajectory:
            explorer_config = ExplorerConfig(
                max_trajectories=3,  # 限制轨迹数
                enable_cross_pollination=True
            )
            self._multi_trajectory_explorer = MultiTrajectoryExplorer(explorer_config)
        else:
            self._multi_trajectory_explorer = None
        
        # Knowledge Management System 连接
        self._kms_patterns: Dict[str, Any] = {}
        if config.pattern_storage_enabled:
            self._init_kms_connection()
    
    def _init_kms_connection(self) -> None:
        """初始化 KMS 连接"""
        agent_id = getattr(self, 'agent_id', 'unknown')
        try:
            from knowledge_management_system.api.service_interface import get_knowledge_service
            self._kms_service = get_knowledge_service()
            logger.info(f"{agent_id}: Connected to KMS for pattern storage")
        except Exception as e:
            logger.warning(f"{agent_id}: KMS not available: {e}")
            self._kms_service = None
        """初始化 KMS 连接"""
        try:
            from knowledge_management_system.api.service_interface import get_knowledge_service
            self._kms_service = get_knowledge_service()
            logger.info(f"{self._se_agent_id}: Connected to KMS for pattern storage")
        except Exception as e:
            logger.warning(f"{self._se_agent_id}: KMS not available: {e}")
            self._kms_service = None
    
    # ==================== 核心执行钩子 ====================
    
    async def execute_with_self_evolving(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        execute_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """带自进化的执行
        
        在原有执行流程基础上添加自进化能力
        
        Args:
            task: 任务描述
            context: 执行上下文
            execute_func: 执行函数 (task, context) -> result
            
        Returns:
            执行结果 + 自进化元数据
        """
        if not self.self_evolving_config.enabled:
            # 不启用自进化，直接执行
            if execute_func:
                return await execute_func(task, context)
            return {"success": True, "task": task}
        
        context = context or {}
        self._total_tasks += 1
        
        result = None
        success = False
        reflection_result = None
        
        try:
            # 1. 检查是否有多轨迹探索
            if self._multi_trajectory_explorer and self.self_evolving_config.enable_multi_trajectory:
                result = await self._execute_with_trajectory(task, context)
            elif execute_func:
                result = await execute_func(task, context)
            else:
                result = await self._default_execute(task, context)
            
            # 2. 判断成功/失败
            success = self._check_success(result)
            
            if success:
                self._successful_tasks += 1
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
            
            # 3. 反思(失败时或定期)
            if self._reflection_agent and (
                not success and self.self_evolving_config.auto_reflect_on_failure
            ):
                reflection_result = await self._reflection_agent.reflect(
                    task, result, context
                )
                
                # 深度反思
                if reflection_result and reflection_result.confidence < self.self_evolving_config.reflection_threshold:
                    deep_reflection = await self._reflection_agent.reflect_deeply(
                        task, result, context
                    )
                    if deep_reflection:
                        reflection_result = deep_reflection
            
            # 4. 模式学习
            if self.self_evolving_config.enable_pattern_learning:
                await self._learn_from_result(task, result, success, reflection_result)
            
            # 5. 检查是否需要恢复
            if self._consecutive_failures >= self.self_evolving_config.max_consecutive_failures:
                await self._recover()
            
            # 6. 更新状态
            self._update_evolution_state(success, reflection_result)
            
        except Exception as e:
            logger.error(f"{self._se_agent_id}: Self-evolving execution error: {e}")
            self._consecutive_failures += 1
            success = False
            result = {"error": str(e)}
        
        # 返回结果 + 元数据
        return {
            **result,
            "_self_evolving_meta": {
                "success": success,
                "reflection": reflection_result.to_dict() if reflection_result else None,
                "consecutive_failures": self._consecutive_failures,
                "success_rate": self._successful_tasks / max(self._total_tasks, 1),
                "evolution_stage": self._evolution_state.stage.value if self._evolution_state else "idle"
            }
        }
    
    async def _execute_with_trajectory(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用多轨迹执行"""
        if not self._multi_trajectory_explorer:
            return await self._default_execute(task, context)
        
        # 设置执行器
        async def trajectory_executor(action: str, trajectory, ctx):
            # 这里调用实际的执行逻辑
            result = await self._default_execute(action, ctx)
            return result.get("success", False), result, None
        
        self._multi_trajectory_explorer.set_executor(trajectory_executor)
        
        # 执行多轨迹探索
        trajectory_result = await self._multi_trajectory_explorer.explore(task, context)
        
        if trajectory_result.best_trajectory:
            return {
                "success": True,
                "result": trajectory_result.best_trajectory.to_dict(),
                "exploration_summary": trajectory_result.exploration_summary
            }
        
        return {"success": False, "error": "No valid trajectory found"}
    
    async def _default_execute(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """默认执行(子类可覆盖)"""
        # 模拟执行 - 实际由子类实现
        await asyncio.sleep(0.01)
        return {"success": True, "output": f"Executed: {task[:50]}..."}
    
    def _check_success(self, result: Any) -> bool:
        """检查执行是否成功"""
        if isinstance(result, dict):
            return result.get("success", False)
        return result is not None
    
    # ==================== 反思与学习 ====================
    
    async def _learn_from_result(
        self,
        task: str,
        result: Dict[str, Any],
        success: bool,
        reflection: Optional[ReflectionResult]
    ) -> None:
        """从执行结果学习"""
        # 提取模式
        pattern = {
            "task_signature": self._get_task_signature(task),
            "task": task,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self._se_agent_id,
            "reflection_issues": reflection.issues if reflection else [],
            "reflection_suggestions": reflection.suggestions if reflection else []
        }
        
        # 本地存储
        task_sig = pattern["task_signature"]
        if task_sig not in self._kms_patterns:
            self._kms_patterns[task_sig] = []
        self._kms_patterns[task_sig].append(pattern)
        
        # 存储到 KMS(可选)
        if self._kms_service and self.self_evolving_config.pattern_storage_enabled:
            await self._store_pattern_to_kms(pattern)
    
    def _get_task_signature(self, task: str) -> str:
        """获取任务签名(用于模式匹配)"""
        # 简化: 使用前50字符 + 任务类型
        return task[:50].lower().strip()
    
    async def _store_pattern_to_kms(self, pattern: Dict[str, Any]) -> None:
        """存储模式到 Knowledge Management System"""
        if not self._kms_service:
            return
            
        try:
            # 作为知识条目存储
            await self._kms_service.import_knowledge(
                data={
                    "type": "agent_pattern",
                    "content": str(pattern),
                    "agent_id": self._se_agent_id,
                    "task_signature": pattern["task_signature"]
                },
                modality="text"
            )
            logger.debug(f"{self._se_agent_id}: Pattern stored to KMS")
        except Exception as e:
            logger.warning(f"{self._se_agent_id}: Failed to store pattern to KMS: {e}")
    
    async def _recover(self) -> None:
        """恢复机制: 连续失败后尝试修复"""
        logger.info(f"{self._se_agent_id}: Attempting recovery after {self._consecutive_failures} failures")
        
        # 清除最近的低质量模式
        if self._kms_patterns:
            for sig, patterns in self._kms_patterns.items():
                # 保留成功的
                self._kms_patterns[sig] = [p for p in patterns if p.get("success", False)]
        
        # 重置失败计数
        self._consecutive_failures = 0
        
        logger.info(f"{self._se_agent_id}: Recovery complete")
    
    def _update_evolution_state(
        self,
        success: bool,
        reflection: Optional[ReflectionResult]
    ) -> None:
        """更新进化状态"""
        if not self._evolution_state:
            return
            
        self._evolution_state.total_tasks = self._total_tasks
        self._evolution_state.successful_tasks = self._successful_tasks
        self._evolution_state.failed_tasks = self._total_tasks - self._successful_tasks
        
        # 更新阶段
        if self._consecutive_failures >= self.self_evolving_config.max_consecutive_failures:
            self._evolution_state.stage = EvolutionStage.RECOVERING
        elif success:
            self._evolution_state.stage = EvolutionStage.STABLE
        else:
            self._evolution_state.stage = EvolutionStage.REFLECTING
        
        # 更新置信度
        if reflection:
            self._evolution_state.avg_confidence = (
                (self._evolution_state.avg_confidence + reflection.confidence) / 2
            )
        
        self._evolution_state.last_update = datetime.now()
    
    # ==================== 公共接口 ====================
    
    def get_evolution_state(self) -> Optional[AgentState]:
        """获取当前进化状态"""
        return self._evolution_state
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        return self._successful_tasks / max(self._total_tasks, 1)
    
    def get_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取学习到的模式"""
        return self._kms_patterns
    
    def get_reflection_history(self) -> List[Dict[str, Any]]:
        """获取反思历史"""
        if self._reflection_agent and hasattr(self._reflection_agent, 'reflection_history'):
            return [r.to_dict() for r in self._reflection_agent.reflection_history[-10:]]
        return []
    
    async def force_reflect(self, task: str, result: Any, context: Dict[str, Any]) -> Optional[ReflectionResult]:
        """强制反思(手动调用)"""
        if not self._reflection_agent:
            return None
        return await self._reflection_agent.reflect(task, result, context)
    
    def enable_self_evolving(self) -> None:
        """启用自进化"""
        self.self_evolving_config.enabled = True
    
    def disable_self_evolving(self) -> None:
        """禁用自进化"""
        self.self_evolving_config.enabled = False
    
    def is_self_evolving_enabled(self) -> bool:
        """检查是否启用自进化"""
        return self.self_evolving_config.enabled


class AdaptiveSelfEvolvingMixin(SelfEvolvingMixin):
    """自适应自进化混入类
    
    在 SelfEvolvingMixin 基础上增加:
    - 根据成功率自动调整策略
    - 动态启用/禁用多轨迹探索
    - 资源感知的进化
    """
    
    def __init__(self):
        super().__init__()
        self._resource_budget = 1.0  # 0-1, 资源预算
        self._last_strategy_adjustment = datetime.now()
    
    async def execute_with_self_evolving(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        execute_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """自适应执行"""
        # 1. 动态调整策略
        await self._adaptive_strategy_adjustment()
        
        # 2. 根据资源预算决定是否启用多轨迹
        if self._resource_budget < 0.3:
            # 资源不足，禁用多轨迹
            self.self_evolving_config.enable_multi_trajectory = False
        elif self._resource_budget > 0.7 and self.get_success_rate() < 0.8:
            # 资源充足且成功率低，启用多轨迹
            self.self_evolving_config.enable_multi_trajectory = True
        
        # 3. 执行
        return await super().execute_with_self_evolving(task, context, execute_func)
    
    async def _adaptive_strategy_adjustment(self) -> None:
        """自适应策略调整"""
        now = datetime.now()
        
        # 每分钟调整一次
        if (now - self._last_strategy_adjustment).seconds < 60:
            return
            
        self._last_strategy_adjustment = now
        success_rate = self.get_success_rate()
        
        # 成功率低时增加反思频率
        if success_rate < 0.5:
            self.self_evolving_config.auto_reflect_on_failure = True
            self.self_evolving_config.reflection_threshold = 0.8
        elif success_rate > 0.9:
            # 成功率高，减少开销
            self.self_evolving_config.auto_reflect_on_failure = False
        
        logger.debug(f"{self._se_agent_id}: Strategy adjusted, success_rate={success_rate:.2f}")
