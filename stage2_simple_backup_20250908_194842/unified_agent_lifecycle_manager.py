#!/usr/bin/env python3
"""
统一智能体生命周期管理器
整合所有重复的智能体管理功能，提供统一的智能体管理接口
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.smart_config_system import get_smart_config, create_query_context
from src.utils.unified_config_center import get_unified_config_center
from src.utils.unified_dependency_manager import get_dependency
from src.utils.unified_performance_center import get_unified_performance_center

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """智能体状态枚举"""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


class IntegrationPriority(Enum):
    """集成优先级枚举"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    agent_class: type
    priority: IntegrationPriority = IntegrationPriority.MEDIUM
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    timeout: float = 30.0
    state: AgentState = AgentState.UNREGISTERED


@dataclass
class AgentPerformance:
    """智能体性能记录"""
    total_calls: int = 0
    successful_calls: int = 0
    total_time: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    average_time: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    success_rate: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    last_execution_time: Optional[float] = None
    error_count: int = 0
    consecutive_failures: int = 0


@dataclass
class IntegrationResult:
    """集成结果"""
    success: bool
    agent_name: str
    result: Any = None
    error: str = None
    execution_time: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    agent_sequence: List[str]
    description: str = ""
    priority: IntegrationPriority = IntegrationPriority.MEDIUM
    max_execution_time: float = 300.0


class UnifiedAgentLifecycleManager:
    """统一智能体生命周期管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 智能体管理
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.agent_instances: Dict[str, Any] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.agent_performance: Dict[str, AgentPerformance] = {}

        # 工作流管理
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}

        # 集成历史
        self.integration_history: List[IntegrationResult] = []

        # 核心系统
        self.config_center = None
        self.performance_center = None
        self.prompt_engine = None
        self.intelligent_scorer = None

        # 初始化核心系统
        self._init_core_systems()

        # 注册默认智能体
        self._register_default_agents()

        logger.info("统一智能体生命周期管理器初始化完成")

    def _init_core_systems(self):
        """初始化核心系统"""
        try:
            # 配置中心
            self.config_center = get_unified_config_center()

            # 性能中心
            self.performance_center = get_unified_performance_center()

            # 提示词引擎
            try:
                from src.utils.prompt_engine import get_prompt_engine
                self.prompt_engine = get_prompt_engine()
            except Exception as e:
                self.logger.warning(f"提示词引擎初始化失败: {e}")

            # 智能评分器
            try:
                from src.utils.unified_scoring_center import get_unified_intelligent_scorer
                self.intelligent_scorer = get_unified_intelligent_scorer()
            except Exception as e:
                self.logger.warning(f"智能评分器初始化失败: {e}")

            self.logger.info("核心系统初始化成功")

        except Exception as e:
            self.logger.error(f"核心系统初始化失败: {e}")

    def _register_default_agents(self):
        """注册默认智能体配置"""
        default_agents = [
            {
                "name": "EnhancedReasoningAgent",
                "class_path": "src.agents.enhanced_reasoning_agent.EnhancedReasoningAgent",
                "priority": IntegrationPriority.CRITICAL,
                "dependencies": []
            },
            {
                "name": "EnhancedKnowledgeRetrievalAgent",
                "class_path": "src.agents.enhanced_knowledge_retrieval_agent.EnhancedKnowledgeRetrievalAgent",
                "priority": IntegrationPriority.HIGH,
                "dependencies": []
            },
            {
                "name": "EnhancedAnswerGenerationAgent",
                "class_path": "src.agents.enhanced_answer_generation_agent.EnhancedAnswerGenerationAgent",
                "priority": IntegrationPriority.HIGH,
                "dependencies": []
            },
            {
                "name": "EnhancedAnalysisAgent",
                "class_path": "src.agents.enhanced_analysis_agent.EnhancedAnalysisAgent",
                "priority": IntegrationPriority.MEDIUM,
                "dependencies": []
            },
            {
                "name": "EnhancedCitationAgent",
                "class_path": "src.agents.enhanced_citation_agent.EnhancedCitationAgent",
                "priority": IntegrationPriority.MEDIUM,
                "dependencies": []
            },
            {
                "name": "IntelligentCoordinatorAgent",
                "class_path": "src.agents.intelligent_coordinator_agent.IntelligentCoordinatorAgent",
                "priority": IntegrationPriority.HIGH,
                "dependencies": []
            },
            {
                "name": "FactVerificationAgent",
                "class_path": "src.agents.fact_verification_agent.FactVerificationAgent",
                "priority": IntegrationPriority.MEDIUM,
                "dependencies": []
            },
            {
                "name": "IntelligentStrategyAgent",
                "class_path": "src.agents.intelligent_strategy_agent.IntelligentStrategyAgent",
                "priority": IntegrationPriority.MEDIUM,
                "dependencies": []
            }
        ]

        for agent_info in default_agents:
            try:
                self.register_agent_from_config(agent_info)
            except Exception as e:
                self.logger.warning(f"注册默认智能体失败 {agent_info['name']}: {e}")

    # ===== 智能体注册和管理 =====

    def register_agent(self, config: AgentConfig) -> bool:
        """注册智能体"""
        try:
            if config.name in self.agent_configs:
                self.logger.warning(f"智能体 {config.name} 已存在，正在更新配置")
                self.agent_configs[config.name] = config
            else:
                self.agent_configs[config.name] = config

            self.agent_states[config.name] = AgentState.REGISTERED
            self.logger.info(f"✅ 智能体 {config.name} 注册成功")
            return True

        except Exception as e:
            self.logger.error(f"❌ 智能体 {config.name} 注册失败: {e}")
            return False

    def register_agent_from_config(self, config_dict: Dict[str, Any]) -> bool:
        """从配置字典注册智能体"""
        try:
            # 动态导入智能体类
            class_path = config_dict.get("class_path", "")
            if not class_path:
                self.logger.error("智能体配置缺少class_path")
                return False

            # 解析类路径
            module_path, class_name = class_path.rsplit(".", 1)

            try:
                import importlib
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
            except Exception as e:
                self.logger.error(f"导入智能体类失败 {class_path}: {e}")
                return False

            # 创建配置对象
            config = AgentConfig(
                name=config_dict["name"],
                agent_class=agent_class,
                priority=config_dict.get("priority", IntegrationPriority.MEDIUM),
                enabled=config_dict.get("enabled", True),
                dependencies=config_dict.get("dependencies", []),
                config=config_dict.get("config", {})
            )

            return self.register_agent(config)

        except Exception as e:
            self.logger.error(f"从配置注册智能体失败 {config_dict.get('name', 'unknown')}: {e}")
            return False

    def unregister_agent(self, agent_name: str) -> bool:
        """注销智能体"""
        try:
            if agent_name in self.agent_instances:
                # 停止智能体实例
                self.stop_agent(agent_name)

            if agent_name in self.agent_configs:
                del self.agent_configs[agent_name]

            if agent_name in self.agent_states:
                del self.agent_states[agent_name]

            if agent_name in self.agent_performance:
                del self.agent_performance[agent_name]

            self.logger.info(f"✅ 智能体 {agent_name} 注销成功")
            return True

        except Exception as e:
            self.logger.error(f"❌ 智能体 {agent_name} 注销失败: {e}")
            return False

    # ===== 智能体生命周期管理 =====

    def create_agent(self, agent_name: str, **kwargs) -> Optional[Any]:
        """创建智能体实例"""
        try:
            if agent_name not in self.agent_configs:
                self.logger.error(f"❌ 智能体 {agent_name} 未注册")
                return None

            config = self.agent_configs[agent_name]
            if not config.enabled:
                self.logger.warning(f"⚠️ 智能体 {agent_name} 已禁用")
                return None

            # 检查依赖
            if not self._check_dependencies(config.dependencies):
                self.logger.error(f"❌ 智能体 {agent_name} 的依赖未满足")
                return None

            # 更新状态
            self.agent_states[agent_name] = AgentState.INITIALIZING

            # 创建智能体实例
            agent_kwargs = config.config.copy()
            agent_kwargs.update(kwargs)

            agent = config.agent_class(**agent_kwargs)
            self.agent_instances[agent_name] = agent

            # 更新状态
            self.agent_states[agent_name] = AgentState.ACTIVE

            # 初始化性能记录
            if agent_name not in self.agent_performance:
                self.agent_performance[agent_name] = AgentPerformance()

            self.logger.info(f"✅ 智能体 {agent_name} 创建成功")
            return agent

        except Exception as e:
            self.logger.error(f"❌ 智能体 {agent_name} 创建失败: {e}")
            self.agent_states[agent_name] = AgentState.ERROR
            return None

    def stop_agent(self, agent_name: str) -> bool:
        """停止智能体"""
        try:
            if agent_name in self.agent_instances:
                agent = self.agent_instances[agent_name]

                # 如果智能体有stop方法，调用它
                if hasattr(agent, 'stop') and callable(getattr(agent, 'stop')):
                    try:
                        if asyncio.iscoroutinefunction(agent.stop):
                            asyncio.create_task(agent.stop())
                        else:
                            agent.stop()
                    except Exception as e:
                        self.logger.warning(f"停止智能体 {agent_name} 时出现异常: {e}")

                del self.agent_instances[agent_name]

            self.agent_states[agent_name] = AgentState.INACTIVE
            self.logger.info(f"✅ 智能体 {agent_name} 已停止")
            return True

        except Exception as e:
            self.logger.error(f"❌ 停止智能体 {agent_name} 失败: {e}")
            return False

    def restart_agent(self, agent_name: str) -> bool:
        """重启智能体"""
        try:
            # 停止现有实例
            self.stop_agent(agent_name)

            # 重新创建
            return self.create_agent(agent_name) is not None

        except Exception as e:
            self.logger.error(f"❌ 重启智能体 {agent_name} 失败: {e}")
            return False

    # ===== 智能体执行和管理 =====

    async def execute_agent(self, agent_name: str, task: Dict[str, Any], **kwargs) -> IntegrationResult:
        """执行智能体任务"""
        start_time = time.time()
        result = IntegrationResult(success=False, agent_name=agent_name)

        try:
            # 获取智能体实例
            agent = self.get_agent(agent_name)
            if agent is None:
                result.error = f"智能体 {agent_name} 不可用"
                return result

            # 执行任务
            if hasattr(agent, 'execute') and callable(getattr(agent, 'execute')):
                if asyncio.iscoroutinefunction(agent.execute):
                    task_result = await agent.execute(task, **kwargs)
                else:
                    task_result = agent.execute(task, **kwargs)
            else:
                result.error = f"智能体 {agent_name} 没有execute方法"
                return result

            # 记录执行结果
            execution_time = time.time() - start_time
            result.success = True
            result.result = task_result
            result.execution_time = execution_time

            # 更新性能统计
            self._record_performance(agent_name, execution_time, True)

            self.logger.info(f"✅ 智能体 {agent_name} 执行成功，耗时 {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            result.error = str(e)
            result.execution_time = execution_time

            # 更新性能统计
            self._record_performance(agent_name, execution_time, False)

            self.logger.error(f"❌ 智能体 {agent_name} 执行失败: {e}")
            return result

        finally:
            # 记录到历史
            self.integration_history.append(result)

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """获取智能体实例"""
        if agent_name in self.agent_instances:
            return self.agent_instances[agent_name]

        # 如果实例不存在，尝试创建
        if agent_name in self.agent_configs:
            return self.create_agent(agent_name)

        return None

    # ===== 性能监控和管理 =====

    def _record_performance(self, agent_name: str, execution_time: float, success: bool):
        """记录智能体性能"""
        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = AgentPerformance()

        perf = self.agent_performance[agent_name]
        perf.total_calls += 1
        perf.total_time += execution_time
        perf.average_time = perf.total_time / perf.total_calls
        perf.last_execution_time = execution_time

        if success:
            perf.successful_calls += 1
            perf.consecutive_failures = 0
        else:
            perf.error_count += 1
            perf.consecutive_failures += 1

        perf.success_rate = perf.successful_calls / perf.total_calls

    def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformance]:
        """获取智能体性能"""
        return self.agent_performance.get(agent_name)

    def get_all_agent_performance(self) -> Dict[str, AgentPerformance]:
        """获取所有智能体性能"""
        return self.agent_performance.copy()

    def reset_agent_performance(self, agent_name: Optional[str] = None):
        """重置智能体性能"""
        try:
            if agent_name:
                if agent_name in self.agent_performance:
                    del self.agent_performance[agent_name]
            else:
                self.agent_performance.clear()

            self.logger.info(f"✅ 智能体性能重置成功 {'(' + agent_name + ')' if agent_name else '(全部)'}")

        except Exception as e:
            self.logger.error(f"❌ 重置智能体性能失败: {e}")

    # ===== 工作流管理 =====

    def create_workflow(self, workflow: WorkflowDefinition) -> bool:
        """创建工作流"""
        try:
            if workflow.name in self.workflows:
                self.logger.warning(f"工作流 {workflow.name} 已存在，正在更新")

            self.workflows[workflow.name] = workflow
            self.logger.info(f"✅ 工作流 {workflow.name} 创建成功")
            return True

        except Exception as e:
            self.logger.error(f"❌ 创建工作流失败 {workflow.name}: {e}")
            return False

    async def execute_workflow(self, workflow_name: str, initial_task: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            if workflow_name not in self.workflows:
                raise ValueError(f"工作流 {workflow_name} 不存在")

            workflow = self.workflows[workflow_name]
            current_task = initial_task
            workflow_results = {}

            # 按顺序执行智能体
            for agent_name in workflow.agent_sequence:
                self.logger.info(f"执行工作流 {workflow_name} - 智能体 {agent_name}")

                result = await self.execute_agent(agent_name, current_task)

                if not result.success:
                    raise Exception(f"工作流 {workflow_name} 在智能体 {agent_name} 失败: {result.error}")

                # 将结果传递给下一个智能体
                workflow_results[agent_name] = result.result
                current_task = {
                    "input": result.result,
                    "workflow_context": workflow_results,
                    "current_agent": agent_name
                }

            return {
                "success": True,
                "workflow": workflow_name,
                "results": workflow_results,
                "total_agents": len(workflow.agent_sequence)
            }

        except Exception as e:
            self.logger.error(f"❌ 工作流 {workflow_name} 执行失败: {e}")
            return {
                "success": False,
                "workflow": workflow_name,
                "error": str(e)
            }

    # ===== 依赖检查和状态管理 =====

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖是否满足"""
        for dep in dependencies:
            if dep not in self.agent_instances:
                # 尝试创建依赖的智能体
                if dep in self.agent_configs and self.create_agent(dep) is None:
                    return False

        return True

    def get_agent_state(self, agent_name: str) -> AgentState:
        """获取智能体状态"""
        return self.agent_states.get(agent_name, AgentState.UNREGISTERED)

    def get_all_agent_states(self) -> Dict[str, AgentState]:
        """获取所有智能体状态"""
        return self.agent_states.copy()

    def enable_agent(self, agent_name: str) -> bool:
        """启用智能体"""
        if agent_name in self.agent_configs:
            self.agent_configs[agent_name].enabled = True
            self.logger.info(f"✅ 智能体 {agent_name} 已启用")
            return True
        return False

    def disable_agent(self, agent_name: str) -> bool:
        """禁用智能体"""
        if agent_name in self.agent_configs:
            self.agent_configs[agent_name].enabled = False
            self.stop_agent(agent_name)
            self.logger.info(f"✅ 智能体 {agent_name} 已禁用")
            return True
        return False

    # ===== 系统状态和监控 =====

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        total_agents = len(self.agent_configs)
        active_agents = len([name for name, state in self.agent_states.items()
                           if state == AgentState.ACTIVE])
        error_agents = len([name for name, state in self.agent_states.items()
                          if state == AgentState.ERROR])

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "error_agents": error_agents,
            "inactive_agents": total_agents - active_agents - error_agents,
            "total_workflows": len(self.workflows),
            "active_workflows": len(self.active_workflows),
            "total_integration_calls": len(self.integration_history),
            "successful_calls": len([r for r in self.integration_history if r.success]),
            "system_health": "healthy" if error_agents == 0 else "warning" if error_agents < total_agents * 0.1 else "critical"
        }

    def get_integration_history(self, limit: int = get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))) -> List[IntegrationResult]:
        """获取集成历史"""
        return self.integration_history[-limit:] if limit > 0 else self.integration_history

    def clear_integration_history(self):
        """清空集成历史"""
        self.integration_history.clear()
        self.logger.info("✅ 集成历史已清空")

    def cleanup(self):
        """清理资源"""
        try:
            # 停止所有智能体
            for agent_name in list(self.agent_instances.keys()):
                self.stop_agent(agent_name)

            # 清空状态
            self.agent_instances.clear()
            self.agent_states.clear()
            self.active_workflows.clear()

            self.logger.info("✅ 统一智能体生命周期管理器已清理")

        except Exception as e:
            self.logger.error(f"❌ 清理失败: {e}")


# ===== 全局实例管理 =====

_unified_agent_manager = None

def get_unified_agent_lifecycle_manager() -> UnifiedAgentLifecycleManager:
    """获取统一智能体生命周期管理器实例"""
    global _unified_agent_manager
    if _unified_agent_manager is None:
        _unified_agent_manager = UnifiedAgentLifecycleManager()
    return _unified_agent_manager

def create_agent(agent_name: str, **kwargs) -> Optional[Any]:
    """便捷函数：创建智能体"""
    manager = get_unified_agent_lifecycle_manager()
    return manager.create_agent(agent_name, **kwargs)

def get_agent(agent_name: str) -> Optional[Any]:
    """便捷函数：获取智能体"""
    manager = get_unified_agent_lifecycle_manager()
    return manager.get_agent(agent_name)

async def execute_agent(agent_name: str, task: Dict[str, Any], **kwargs) -> IntegrationResult:
    """便捷函数：执行智能体"""
    manager = get_unified_agent_lifecycle_manager()
    return await manager.execute_agent(agent_name, task, **kwargs)

def get_agent_performance(agent_name: str) -> Optional[AgentPerformance]:
    """便捷函数：获取智能体性能"""
    manager = get_unified_agent_lifecycle_manager()
    return manager.get_agent_performance(agent_name)

def get_system_status() -> Dict[str, Any]:
    """便捷函数：获取系统状态"""
    manager = get_unified_agent_lifecycle_manager()
    return manager.get_system_status()

# ===== 向后兼容性 =====

# 为旧的intelligent_agent_manager提供别名
IntelligentAgentManager = UnifiedAgentLifecycleManager

# 为旧的agent_integration_manager提供别名
AgentIntegrationManager = UnifiedAgentLifecycleManager

# 为旧的intelligent_agent_integrator提供别名
IntelligentAgentIntegrator = UnifiedAgentLifecycleManager

logger.info("统一智能体生命周期管理器加载完成，提供向后兼容性")
