#!/usr/bin/env python3
"""
应急回滚系统
提供Agent迁移失败时的安全回滚机制
"""

import asyncio
import time
import logging
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class RollbackStrategy(Enum):
    """回滚策略"""
    IMMEDIATE = "immediate"        # 立即回滚 - 直接恢复到100%旧Agent
    GRADUAL = "gradual"           # 渐进回滚 - 逐步减少新Agent比例
    SELECTIVE = "selective"       # 选择性回滚 - 只回滚问题Agent
    PHASED = "phased"            # 分阶段回滚 - 按优先级分批回滚


class RollbackTrigger(Enum):
    """回滚触发条件"""
    MANUAL = "manual"                    # 手动触发
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    ERROR_RATE_SPIKE = "error_rate_spike"               # 错误率激增
    SYSTEM_CRASH = "system_crash"                       # 系统崩溃
    BUSINESS_IMPACT = "business_impact"                 # 业务影响


@dataclass
class RollbackPlan:
    """回滚计划"""
    plan_id: str
    strategy: RollbackStrategy
    trigger: RollbackTrigger
    affected_agents: List[str]
    target_rates: Dict[str, float]  # Agent -> 目标替换率
    estimated_duration: timedelta
    risk_level: str
    rollback_steps: List[Dict[str, Any]]
    verification_steps: List[str]
    created_at: datetime


@dataclass
class RollbackExecution:
    """回滚执行记录"""
    execution_id: str
    plan: RollbackPlan
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    steps_executed: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: Dict[str, Any] = field(default_factory=dict)
    issues_encountered: List[str] = field(default_factory=list)


class EmergencyRollbackSystem:
    """应急回滚系统"""

    def __init__(self):
        self.is_active = False
        self.monitor_thread: Optional[threading.Thread] = None

        # 回滚配置
        self.rollback_plans: Dict[str, RollbackPlan] = {}
        self.active_executions: Dict[str, RollbackExecution] = {}

        # 自动触发条件
        self.auto_triggers = self._initialize_auto_triggers()

        # 数据存储
        self.data_dir = Path("data/rollback")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("应急回滚系统初始化完成")

    def _initialize_auto_triggers(self) -> Dict[str, Dict[str, Any]]:
        """初始化自动触发条件"""
        return {
            'performance_degradation': {
                'enabled': True,
                'threshold': 1.5,  # 性能下降50%
                'window_minutes': 30,
                'cooldown_minutes': 60
            },
            'error_rate_spike': {
                'enabled': True,
                'threshold': 0.20,  # 错误率超过20%
                'window_minutes': 15,
                'cooldown_minutes': 30
            },
            'system_crash': {
                'enabled': True,
                'restart_attempts': 3,
                'backoff_seconds': 300
            }
        }

    def create_rollback_plan(self, strategy: RollbackStrategy,
                           trigger: RollbackTrigger,
                           affected_agents: List[str],
                           custom_rates: Optional[Dict[str, float]] = None) -> RollbackPlan:
        """
        创建回滚计划

        Args:
            strategy: 回滚策略
            trigger: 触发条件
            affected_agents: 受影响的Agent列表
            custom_rates: 自定义目标替换率 (可选)

        Returns:
            回滚计划
        """
        plan_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 根据策略设置默认目标替换率
        if custom_rates:
            target_rates = custom_rates
        else:
            if strategy == RollbackStrategy.IMMEDIATE:
                target_rates = {agent: 0.0 for agent in affected_agents}  # 100%回滚到旧Agent
            elif strategy == RollbackStrategy.GRADUAL:
                target_rates = {agent: 0.1 for agent in affected_agents}  # 逐步降到10%
            elif strategy == RollbackStrategy.SELECTIVE:
                target_rates = {agent: 0.0 for agent in affected_agents}  # 只对指定Agent回滚
            else:  # PHASED
                target_rates = {agent: 0.0 for agent in affected_agents}  # 分阶段回滚

        # 估算持续时间
        if strategy == RollbackStrategy.IMMEDIATE:
            estimated_duration = timedelta(minutes=5)
        elif strategy == RollbackStrategy.GRADUAL:
            estimated_duration = timedelta(hours=1)
        else:
            estimated_duration = timedelta(minutes=30)

        # 评估风险等级
        if len(affected_agents) >= 5 or strategy == RollbackStrategy.IMMEDIATE:
            risk_level = "high"
        elif len(affected_agents) >= 3:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 生成回滚步骤
        rollback_steps = self._generate_rollback_steps(strategy, affected_agents, target_rates)

        # 生成验证步骤
        verification_steps = self._generate_verification_steps(affected_agents)

        plan = RollbackPlan(
            plan_id=plan_id,
            strategy=strategy,
            trigger=trigger,
            affected_agents=affected_agents,
            target_rates=target_rates,
            estimated_duration=estimated_duration,
            risk_level=risk_level,
            rollback_steps=rollback_steps,
            verification_steps=verification_steps,
            created_at=datetime.now()
        )

        self.rollback_plans[plan_id] = plan
        self._save_rollback_plan(plan)

        logger.info(f"回滚计划已创建: {plan_id} (策略: {strategy.value}, 风险: {risk_level})")
        return plan

    def _generate_rollback_steps(self, strategy: RollbackStrategy,
                               affected_agents: List[str],
                               target_rates: Dict[str, float]) -> List[Dict[str, Any]]:
        """生成回滚步骤"""
        steps = []

        if strategy == RollbackStrategy.IMMEDIATE:
            # 立即回滚所有Agent
            for agent in affected_agents:
                steps.append({
                    'step_id': f"rollback_{agent}",
                    'description': f"将{agent}替换率立即设置为{target_rates[agent]:.1%}",
                    'action': 'set_replacement_rate',
                    'agent': agent,
                    'target_rate': target_rates[agent],
                    'immediate': True
                })

        elif strategy == RollbackStrategy.GRADUAL:
            # 渐进式回滚
            steps_per_agent = []
            for agent in affected_agents:
                current_rate = 0.5  # 假设当前50%，实际情况应该从监控系统获取
                step_size = (current_rate - target_rates[agent]) / 5  # 5步完成

                for i in range(5):
                    rate = current_rate - (i + 1) * step_size
                    steps_per_agent.append({
                        'step_id': f"rollback_{agent}_step_{i+1}",
                        'description': f"将{agent}替换率降至{rate:.1%} (第{i+1}步)",
                        'action': 'set_replacement_rate',
                        'agent': agent,
                        'target_rate': max(0, rate),
                        'delay_seconds': 60  # 每步间隔1分钟
                    })

            steps.extend(steps_per_agent)

        elif strategy == RollbackStrategy.SELECTIVE:
            # 选择性回滚
            for agent in affected_agents:
                steps.append({
                    'step_id': f"selective_rollback_{agent}",
                    'description': f"选择性回滚{agent}到{target_rates[agent]:.1%}",
                    'action': 'set_replacement_rate',
                    'agent': agent,
                    'target_rate': target_rates[agent],
                    'selective': True
                })

        else:  # PHASED
            # 分阶段回滚 - 按优先级
            priority_order = self._get_rollback_priority(affected_agents)

            for phase, agents_in_phase in enumerate(priority_order, 1):
                for agent in agents_in_phase:
                    steps.append({
                        'step_id': f"phase_{phase}_rollback_{agent}",
                        'description': f"第{phase}阶段: 将{agent}回滚到{target_rates[agent]:.1%}",
                        'action': 'set_replacement_rate',
                        'agent': agent,
                        'target_rate': target_rates[agent],
                        'phase': phase,
                        'delay_seconds': 300  # 阶段间间隔5分钟
                    })

        return steps

    def _get_rollback_priority(self, agents: List[str]) -> List[List[str]]:
        """获取回滚优先级"""
        # 定义优先级顺序 (核心Agent优先回滚)
        priority_groups = [
            ['ChiefAgentWrapper', 'AgentCoordinator'],  # 核心协调Agent
            ['RAGExpert', 'KnowledgeRetrievalAgentWrapper'],  # 知识检索Agent
            ['ReasoningExpert', 'ReActAgent'],  # 推理Agent
            ['QualityController', 'CitationAgent']  # 质量控制Agent
        ]

        result = []
        remaining_agents = set(agents)

        for group in priority_groups:
            phase_agents = [agent for agent in group if agent in remaining_agents]
            if phase_agents:
                result.append(phase_agents)
                remaining_agents -= set(phase_agents)

        # 剩余Agent作为最后一阶段
        if remaining_agents:
            result.append(list(remaining_agents))

        return result

    def _generate_verification_steps(self, affected_agents: List[str]) -> List[str]:
        """生成验证步骤"""
        return [
            "检查系统日志，确认无异常错误",
            "运行基础功能测试，确保核心功能正常",
            f"验证{affected_agents}的替换率已正确调整",
            "监控系统性能指标，确认恢复正常水平",
            "检查业务指标，确保用户体验不受影响",
            "运行集成测试，确认Agent间协作正常"
        ]

    async def execute_rollback(self, plan: RollbackPlan) -> RollbackExecution:
        """
        执行回滚计划

        Args:
            plan: 回滚计划

        Returns:
            执行记录
        """
        execution_id = f"exec_{plan.plan_id}_{datetime.now().strftime('%H%M%S')}"

        execution = RollbackExecution(
            execution_id=execution_id,
            plan=plan,
            started_at=datetime.now()
        )

        self.active_executions[execution_id] = execution

        try:
            logger.info(f"开始执行回滚计划: {plan.plan_id}")

            # 执行回滚步骤
            for step in plan.rollback_steps:
                success = await self._execute_rollback_step(step, execution)
                if not success:
                    execution.status = "failed"
                    execution.issues_encountered.append(f"步骤执行失败: {step['step_id']}")
                    break

                execution.steps_executed.append({
                    'step': step,
                    'executed_at': datetime.now(),
                    'success': True
                })

                # 步骤间延迟
                if 'delay_seconds' in step:
                    await asyncio.sleep(step['delay_seconds'])

            # 执行验证步骤
            if execution.status != "failed":
                verification_results = await self._execute_verification(plan.verification_steps)
                execution.verification_results = verification_results

                # 基于验证结果判断最终状态
                if verification_results.get('overall_success', False):
                    execution.status = "completed"
                else:
                    execution.status = "failed"
                    execution.issues_encountered.extend(verification_results.get('issues', []))

            execution.completed_at = datetime.now()

        except Exception as e:
            execution.status = "failed"
            execution.issues_encountered.append(f"执行异常: {str(e)}")
            logger.error(f"回滚执行异常: {e}", exc_info=True)

        finally:
            self._save_rollback_execution(execution)

        logger.info(f"回滚执行完成: {execution_id} (状态: {execution.status})")
        return execution

    async def _execute_rollback_step(self, step: Dict[str, Any], execution: RollbackExecution) -> bool:
        """执行单个回滚步骤"""
        try:
            step_id = step['step_id']
            action = step['action']

            logger.info(f"执行回滚步骤: {step_id}")

            if action == 'set_replacement_rate':
                agent = step['agent']
                target_rate = step['target_rate']

                # 这里应该调用实际的Agent包装器来设置替换率
                # 由于无法直接访问，这里模拟设置
                success = await self._set_agent_replacement_rate(agent, target_rate)

                if success:
                    logger.info(f"✅ {agent}替换率已设置为{target_rate:.1%}")
                    return True
                else:
                    logger.error(f"❌ 设置{agent}替换率失败")
                    return False

            else:
                logger.warning(f"未知的回滚动作: {action}")
                return False

        except Exception as e:
            logger.error(f"执行回滚步骤异常: {e}")
            return False

    async def _set_agent_replacement_rate(self, agent_name: str, rate: float) -> bool:
        """设置Agent替换率"""
        # 这里是模拟实现
        # 实际应该通过包装器的API或配置系统来设置

        try:
            # 模拟网络延迟
            await asyncio.sleep(0.1)

            # 记录到配置或状态管理系统
            logger.info(f"模拟设置{agent_name}替换率为{rate:.1%}")

            # 假设总是成功
            return True

        except Exception as e:
            logger.error(f"设置替换率异常: {e}")
            return False

    async def _execute_verification(self, verification_steps: List[str]) -> Dict[str, Any]:
        """执行验证步骤"""
        results = {
            'overall_success': True,
            'step_results': [],
            'issues': []
        }

        for step in verification_steps:
            try:
                logger.info(f"执行验证: {step}")

                # 这里应该执行实际的验证逻辑
                # 现在模拟验证
                success = await self._simulate_verification(step)

                results['step_results'].append({
                    'step': step,
                    'success': success,
                    'timestamp': datetime.now()
                })

                if not success:
                    results['overall_success'] = False
                    results['issues'].append(f"验证失败: {step}")

            except Exception as e:
                results['overall_success'] = False
                results['issues'].append(f"验证异常: {step} - {str(e)}")

        return results

    async def _simulate_verification(self, step: str) -> bool:
        """模拟验证步骤"""
        # 模拟验证耗时
        await asyncio.sleep(1)

        # 简单的模拟逻辑 - 实际应该执行真实的验证
        if "日志" in step or "功能测试" in step:
            return True  # 假设日志检查和功能测试通过
        elif "性能" in step:
            return True  # 假设性能指标正常
        elif "集成测试" in step:
            return True  # 假设集成测试通过
        else:
            return True  # 默认通过

    def _save_rollback_plan(self, plan: RollbackPlan):
        """保存回滚计划"""
        try:
            filename = f"rollback_plan_{plan.plan_id}.json"
            filepath = self.data_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'plan_id': plan.plan_id,
                    'strategy': plan.strategy.value,
                    'trigger': plan.trigger.value,
                    'affected_agents': plan.affected_agents,
                    'target_rates': plan.target_rates,
                    'estimated_duration_seconds': plan.estimated_duration.total_seconds(),
                    'risk_level': plan.risk_level,
                    'rollback_steps': plan.rollback_steps,
                    'verification_steps': plan.verification_steps,
                    'created_at': plan.created_at.isoformat()
                }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存回滚计划异常: {e}")

    def _save_rollback_execution(self, execution: RollbackExecution):
        """保存回滚执行记录"""
        try:
            filename = f"rollback_execution_{execution.execution_id}.json"
            filepath = self.data_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'execution_id': execution.execution_id,
                    'plan_id': execution.plan.execution_id if hasattr(execution.plan, 'execution_id') else execution.plan.plan_id,
                    'started_at': execution.started_at.isoformat(),
                    'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                    'status': execution.status,
                    'steps_executed': [
                        {
                            'step_id': step['step'].get('step_id', ''),
                            'executed_at': step['executed_at'].isoformat(),
                            'success': step['success']
                        }
                        for step in execution.steps_executed
                    ],
                    'verification_results': execution.verification_results,
                    'issues_encountered': execution.issues_encountered
                }, f, ensure_ascii=False, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存回滚执行记录异常: {e}")

    def get_available_rollback_plans(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的回滚计划"""
        return {
            plan_id: {
                'strategy': plan.strategy.value,
                'trigger': plan.trigger.value,
                'affected_agents': plan.affected_agents,
                'risk_level': plan.risk_level,
                'estimated_duration': plan.estimated_duration.total_seconds()
            }
            for plan_id, plan in self.rollback_plans.items()
        }

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        history = []
        for execution in self.active_executions.values():
            history.append({
                'execution_id': execution.execution_id,
                'plan_id': execution.plan.plan_id,
                'status': execution.status,
                'started_at': execution.started_at,
                'completed_at': execution.completed_at,
                'issues': execution.issues_encountered
            })

        # 按时间排序
        history.sort(key=lambda x: x['started_at'], reverse=True)
        return history

    async def create_emergency_rollback_plan(self, trigger: RollbackTrigger,
                                           problematic_agents: Optional[List[str]] = None) -> RollbackPlan:
        """
        创建应急回滚计划

        Args:
            trigger: 触发原因
            problematic_agents: 有问题的Agent列表 (可选)

        Returns:
            应急回滚计划
        """
        if problematic_agents is None:
            # 默认回滚所有逐步替换的Agent
            problematic_agents = [
                'ChiefAgentWrapper', 'AnswerGenerationAgentWrapper',
                'LearningSystemWrapper', 'StrategicChiefAgentWrapper',
                'PromptEngineeringAgentWrapper', 'ContextEngineeringAgentWrapper',
                'OptimizedKnowledgeRetrievalAgentWrapper'
            ]

        # 根据触发原因选择策略
        if trigger in [RollbackTrigger.SYSTEM_CRASH, RollbackTrigger.BUSINESS_IMPACT]:
            strategy = RollbackStrategy.IMMEDIATE
        elif trigger == RollbackTrigger.PERFORMANCE_DEGRADATION:
            strategy = RollbackStrategy.GRADUAL
        else:
            strategy = RollbackStrategy.SELECTIVE

        return self.create_rollback_plan(strategy, trigger, problematic_agents)

    async def execute_emergency_rollback(self, trigger: RollbackTrigger,
                                       problematic_agents: Optional[List[str]] = None) -> RollbackExecution:
        """
        执行应急回滚

        Args:
            trigger: 触发原因
            problematic_agents: 有问题的Agent列表

        Returns:
            执行记录
        """
        plan = await self.create_emergency_rollback_plan(trigger, problematic_agents)
        return await self.execute_rollback(plan)


# 全局回滚系统实例
_rollback_system = None


def get_rollback_system() -> EmergencyRollbackSystem:
    """获取全局回滚系统实例"""
    global _rollback_system
    if _rollback_system is None:
        _rollback_system = EmergencyRollbackSystem()
    return _rollback_system


async def create_rollback_plan(strategy: str, trigger: str, agents: List[str]) -> Optional[RollbackPlan]:
    """创建回滚计划 (便捷函数)"""
    system = get_rollback_system()

    try:
        strategy_enum = RollbackStrategy(strategy)
        trigger_enum = RollbackTrigger(trigger)

        return system.create_rollback_plan(strategy_enum, trigger_enum, agents)
    except ValueError as e:
        logger.error(f"无效的参数: {e}")
        return None


async def execute_emergency_rollback(trigger: str, agents: Optional[List[str]] = None) -> Optional[RollbackExecution]:
    """执行应急回滚 (便捷函数)"""
    system = get_rollback_system()

    try:
        trigger_enum = RollbackTrigger(trigger)
        return await system.execute_emergency_rollback(trigger_enum, agents)
    except ValueError as e:
        logger.error(f"无效的触发条件: {e}")
        return None
