"""
分层状态管理系统 - P1阶段状态管理重构

将原有的单一ResearchSystemState拆分为三层状态结构：
1. BusinessState：业务核心状态 (查询、路由、结果)
2. CollaborationState：协作相关状态 (智能体、任务分配)
3. SystemState：系统配置状态 (配置、学习、监控)

提供向后兼容的迁移机制和高效的状态传递。
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class BusinessState:
    """业务核心状态 - 包含查询处理的核心业务逻辑"""

    # 基础查询信息
    query: str
    context: Dict[str, Any] = field(default_factory=dict)

    # 路由决策
    route_path: str = ""
    complexity_score: float = 0.0
    query_type: str = "simple"

    # 处理结果
    result: Dict[str, Any] = field(default_factory=dict)
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)

    # 执行状态
    current_step: str = ""
    step_index: int = 0
    total_steps: int = 0

    # 元数据
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 安全控制
    safety_check_passed: bool = True
    sensitive_topics: List[str] = field(default_factory=list)
    content_filter_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理datetime序列化
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessState':
        """从字典创建实例"""
        # 处理datetime反序列化
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


@dataclass
class AgentState:
    """单个智能体状态"""

    agent_id: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "idle"  # idle, active, paused, error
    current_task: Optional[str] = None
    task_progress: float = 0.0  # 0.0 - 1.0

    # 性能指标
    response_time: float = 0.0
    success_rate: float = 1.0
    task_completion_rate: float = 1.0

    # 状态跟踪
    last_active: datetime = field(default_factory=datetime.now)
    message_queue: List[Dict[str, Any]] = field(default_factory=list)
    contributions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['last_active'] = self.last_active.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """从字典创建实例"""
        if 'last_active' in data:
            data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)


@dataclass
class CollaborationState:
    """协作相关状态 - 管理多智能体协作"""

    # 会话信息
    session_id: str = field(default_factory=lambda: f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    participants: List[str] = field(default_factory=list)
    active_participants: List[str] = field(default_factory=list)

    # 智能体状态
    agent_states: Dict[str, AgentState] = field(default_factory=dict)

    # 任务分配
    task_assignments: Dict[str, List[str]] = field(default_factory=dict)  # task_id -> [agent_ids]
    task_dependencies: Dict[str, List[str]] = field(default_factory=dict)  # task_id -> [dependency_ids]

    # 协作上下文
    collaboration_context: Dict[str, Any] = field(default_factory=dict)
    shared_knowledge: Dict[str, Any] = field(default_factory=dict)
    collaboration_goals: List[str] = field(default_factory=list)

    # 冲突检测
    collaboration_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolved_conflicts: List[Dict[str, Any]] = field(default_factory=list)

    # 消息传递
    agent_messages: List[Dict[str, Any]] = field(default_factory=list)

    # 协作模式
    collaboration_mode: str = "single_agent"  # single_agent, multi_agent, hybrid
    coordination_strategy: str = "sequential"  # sequential, parallel, hybrid

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理AgentState序列化
        data['agent_states'] = {aid: astate.to_dict() for aid, astate in self.agent_states.items()}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationState':
        """从字典创建实例"""
        # 处理AgentState反序列化
        if 'agent_states' in data:
            data['agent_states'] = {aid: AgentState.from_dict(astate_data)
                                   for aid, astate_data in data['agent_states'].items()}
        return cls(**data)

    def add_agent(self, agent_state: AgentState):
        """添加智能体"""
        self.agent_states[agent_state.agent_id] = agent_state
        if agent_state.agent_id not in self.participants:
            self.participants.append(agent_state.agent_id)
        if agent_state.status == "active" and agent_state.agent_id not in self.active_participants:
            self.active_participants.append(agent_state.agent_id)

    def remove_agent(self, agent_id: str):
        """移除智能体"""
        if agent_id in self.agent_states:
            del self.agent_states[agent_id]
        if agent_id in self.participants:
            self.participants.remove(agent_id)
        if agent_id in self.active_participants:
            self.active_participants.remove(agent_id)

    def assign_task(self, task_id: str, agent_id: str):
        """分配任务给智能体"""
        if task_id not in self.task_assignments:
            self.task_assignments[task_id] = []

        if agent_id not in self.task_assignments[task_id]:
            self.task_assignments[task_id].append(agent_id)

        if agent_id in self.agent_states:
            self.agent_states[agent_id].current_task = task_id

    def get_agent_tasks(self, agent_id: str) -> List[str]:
        """获取智能体的任务列表"""
        return [task_id for task_id, agents in self.task_assignments.items()
                if agent_id in agents]

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """检测协作冲突"""
        conflicts = []

        # 检测任务分配冲突（重复分配）
        for task_id, agents in self.task_assignments.items():
            if len(agents) > 1:
                conflicts.append({
                    'conflict_type': 'duplicate_assignment',
                    'severity': 'high',
                    'description': f"任务 {task_id} 被重复分配给 {agents}",
                    'affected_tasks': [task_id],
                    'affected_agents': agents,
                    'suggested_resolution': 'reassign_to_most_suitable_agent'
                })

        # 检测能力不匹配冲突
        for task_id, agents in self.task_assignments.items():
            for agent_id in agents:
                if agent_id in self.agent_states:
                    agent_state = self.agent_states[agent_id]
                    # 简化的能力检查（可以扩展）
                    required_caps = self._infer_required_capabilities(task_id)
                    agent_caps = set(agent_state.capabilities)

                    if not required_caps.issubset(agent_caps):
                        conflicts.append({
                            'conflict_type': 'capability_mismatch',
                            'severity': 'medium',
                            'description': f"智能体 {agent_id} 缺少任务 {task_id} 所需能力",
                            'affected_tasks': [task_id],
                            'affected_agents': [agent_id],
                            'missing_capabilities': list(required_caps - agent_caps),
                            'suggested_resolution': 'reassign_to_capable_agent'
                        })

        self.collaboration_conflicts = conflicts
        return conflicts

    def _infer_required_capabilities(self, task_id: str) -> set:
        """推断任务所需能力"""
        if 'knowledge' in task_id.lower() or 'retrieve' in task_id.lower():
            return {'search', 'retrieve'}
        elif 'reasoning' in task_id.lower() or 'analyze' in task_id.lower():
            return {'analyze', 'reason'}
        elif 'answer' in task_id.lower() or 'generate' in task_id.lower():
            return {'generate', 'format'}
        elif 'citation' in task_id.lower() or 'cite' in task_id.lower():
            return {'cite', 'validate'}
        else:
            return {'process'}


@dataclass
class SystemState:
    """系统配置状态 - 管理配置、学习和监控"""

    # 配置优化
    config_optimization: Dict[str, Any] = field(default_factory=dict)
    current_config: Dict[str, Any] = field(default_factory=dict)
    config_history: List[Dict[str, Any]] = field(default_factory=list)

    # 反馈闭环
    feedback_loop: Dict[str, Any] = field(default_factory=dict)
    execution_feedback: List[Dict[str, Any]] = field(default_factory=list)
    performance_feedback: List[Dict[str, Any]] = field(default_factory=list)
    error_feedback: List[Dict[str, Any]] = field(default_factory=list)

    # 学习系统
    learning_system: Dict[str, Any] = field(default_factory=dict)
    learning_patterns: Dict[str, Any] = field(default_factory=dict)
    learning_strategies: Dict[str, Any] = field(default_factory=dict)
    learning_insights: List[Dict[str, Any]] = field(default_factory=list)

    # 监控指标
    monitoring_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_history: List[Dict[str, Any]] = field(default_factory=dict)
    system_health: Dict[str, Any] = field(default_factory=dict)

    # 缓存和优化
    cached_results: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemState':
        """从字典创建实例"""
        return cls(**data)

    def add_execution_feedback(self, feedback: Dict[str, Any]):
        """添加执行反馈"""
        self.execution_feedback.append({
            **feedback,
            'timestamp': datetime.now().isoformat()
        })
        # 保持最近的反馈记录
        if len(self.execution_feedback) > 100:
            self.execution_feedback = self.execution_feedback[-100:]

    def add_performance_feedback(self, feedback: Dict[str, Any]):
        """添加性能反馈"""
        self.performance_feedback.append({
            **feedback,
            'timestamp': datetime.now().isoformat()
        })
        # 保持最近的反馈记录
        if len(self.performance_feedback) > 100:
            self.performance_feedback = self.performance_feedback[-100:]

    def update_config(self, new_config: Dict[str, Any], reason: str = ""):
        """更新配置"""
        # 保存历史配置
        self.config_history.append({
            'previous_config': self.current_config.copy(),
            'new_config': new_config.copy(),
            'timestamp': datetime.now().isoformat(),
            'reason': reason
        })

        # 应用新配置
        self.current_config.update(new_config)

        # 保持配置历史
        if len(self.config_history) > 50:
            self.config_history = self.config_history[-50:]

    def add_learning_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """添加学习模式"""
        if pattern_type not in self.learning_patterns:
            self.learning_patterns[pattern_type] = []

        self.learning_patterns[pattern_type].append({
            **pattern_data,
            'discovered_at': datetime.now().isoformat()
        })

        # 限制每个类型的模式数量
        if len(self.learning_patterns[pattern_type]) > 20:
            self.learning_patterns[pattern_type] = self.learning_patterns[pattern_type][-20:]

    def add_learning_insight(self, insight: Dict[str, Any]):
        """添加学习洞察"""
        self.learning_insights.append({
            **insight,
            'generated_at': datetime.now().isoformat()
        })

        # 保持洞察记录
        if len(self.learning_insights) > 100:
            self.learning_insights = self.learning_insights[-100:]


@dataclass
class UnifiedState:
    """统一状态容器 - 整合三层状态"""

    business: BusinessState
    collaboration: Optional[CollaborationState] = None
    system: Optional[SystemState] = None

    # 版本控制
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = {
            'business': self.business.to_dict(),
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if self.collaboration:
            data['collaboration'] = self.collaboration.to_dict()
        if self.system:
            data['system'] = self.system.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedState':
        """从字典创建实例"""
        business_data = data.get('business', {})
        collaboration_data = data.get('collaboration')
        system_data = data.get('system')

        business = BusinessState.from_dict(business_data)
        collaboration = CollaborationState.from_dict(collaboration_data) if collaboration_data else None
        system = SystemState.from_dict(system_data) if system_data else None

        return cls(
            business=business,
            collaboration=collaboration,
            system=system,
            version=data.get('version', '1.0'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )

    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()

    def to_langgraph_state(self) -> Dict[str, Any]:
        """转换为LangGraph兼容的状态格式（向后兼容）"""
        state = self.business.to_dict()

        # 添加协作状态
        if self.collaboration:
            collab_dict = self.collaboration.to_dict()
            state.update({
                'agent_states': collab_dict['agent_states'],
                'collaboration_context': collab_dict['collaboration_context'],
                'agent_messages': collab_dict['agent_messages'],
                'task_assignments': collab_dict['task_assignments'],
                'collaboration_conflicts': collab_dict['collaboration_conflicts']
            })

        # 添加系统状态
        if self.system:
            system_dict = self.system.to_dict()
            state.update({
                'config_optimization': system_dict['config_optimization'],
                'feedback_loop': system_dict['feedback_loop'],
                'learning_system': system_dict['learning_system'],
                'learning_insights': system_dict.get('learning_insights', [])
            })

        return state

    @classmethod
    def from_langgraph_state(cls, langgraph_state: Dict[str, Any]) -> 'UnifiedState':
        """从LangGraph状态创建分层状态（迁移兼容）"""
        # 提取业务状态
        business_fields = {
            'query', 'context', 'route_path', 'complexity_score', 'query_type',
            'result', 'intermediate_steps', 'current_step', 'step_index',
            'total_steps', 'execution_time', 'safety_check_passed',
            'sensitive_topics', 'content_filter_applied'
        }

        business_data = {k: v for k, v in langgraph_state.items() if k in business_fields}
        business = BusinessState.from_dict(business_data)

        # 提取协作状态
        collaboration = None
        collab_fields = {
            'agent_states', 'collaboration_context', 'agent_messages',
            'task_assignments', 'collaboration_conflicts'
        }

        collab_data = {k: v for k, v in langgraph_state.items() if k in collab_fields}
        if collab_data:
            collaboration = CollaborationState.from_dict(collab_data)
            # 确保participants列表包含所有agent_states中的智能体
            if 'agent_states' in collab_data and collab_data['agent_states']:
                for agent_id in collab_data['agent_states'].keys():
                    if agent_id not in collaboration.participants:
                        collaboration.participants.append(agent_id)
                    # 如果智能体状态是active，也添加到active_participants
                    agent_state = collaboration.agent_states.get(agent_id)
                    if agent_state and agent_state.status == "active" and agent_id not in collaboration.active_participants:
                        collaboration.active_participants.append(agent_id)

        # 提取系统状态
        system = None
        system_data = {}

        # 处理配置优化 - 映射到current_config
        if 'config_optimization' in langgraph_state:
            system_data['current_config'] = langgraph_state['config_optimization']

        # 处理其他系统字段
        system_fields = {
            'feedback_loop', 'learning_system', 'learning_insights',
            'execution_feedback', 'performance_feedback', 'monitoring_metrics'
        }

        for field in system_fields:
            if field in langgraph_state:
                system_data[field] = langgraph_state[field]

        if system_data:
            system = SystemState.from_dict(system_data)

        return cls(
            business=business,
            collaboration=collaboration,
            system=system
        )


class StateMigrationManager:
    """状态迁移管理器 - 处理向后兼容迁移"""

    @staticmethod
    def migrate_legacy_state(legacy_state: Dict[str, Any]) -> UnifiedState:
        """迁移遗留状态到分层状态"""
        logger.info("开始状态迁移: 遗留状态 → 分层状态")

        try:
            unified_state = UnifiedState.from_langgraph_state(legacy_state)
            logger.info("✅ 状态迁移成功")
            return unified_state

        except Exception as e:
            logger.error(f"❌ 状态迁移失败: {e}")
            # 创建默认状态
            return UnifiedState(
                business=BusinessState(
                    query=legacy_state.get('query', ''),
                    context=legacy_state.get('context', {}),
                    result={'error': f'状态迁移失败: {e}'}
                )
            )

    @staticmethod
    def create_backward_compatible_state(unified_state: UnifiedState) -> Dict[str, Any]:
        """创建向后兼容的状态格式"""
        return unified_state.to_langgraph_state()

    @staticmethod
    def validate_state_integrity(state: Union[UnifiedState, Dict[str, Any]]) -> bool:
        """验证状态完整性"""
        try:
            if isinstance(state, UnifiedState):
                # 验证业务状态
                if not state.business.query:
                    return False
                # 验证协作状态一致性
                if state.collaboration:
                    for agent_id, agent_state in state.collaboration.agent_states.items():
                        if agent_id not in state.collaboration.participants:
                            return False
                return True
            else:
                # 验证字典格式状态
                return 'query' in state and 'result' in state

        except Exception:
            return False

    @staticmethod
    def optimize_state_size(state: UnifiedState) -> UnifiedState:
        """优化状态大小（清理过期数据）"""
        # 清理旧的学习洞察
        if state.system and len(state.system.learning_insights) > 50:
            state.system.learning_insights = state.system.learning_insights[-50:]

        # 清理旧的执行反馈
        if state.system and len(state.system.execution_feedback) > 50:
            state.system.execution_feedback = state.system.execution_feedback[-50:]

        # 清理旧的配置历史
        if state.system and len(state.system.config_history) > 20:
            state.system.config_history = state.system.config_history[-20:]

        return state


# 全局状态管理器实例
_state_manager_instance: Optional[StateMigrationManager] = None


def get_state_manager() -> StateMigrationManager:
    """获取状态管理器实例"""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateMigrationManager()
    return _state_manager_instance
