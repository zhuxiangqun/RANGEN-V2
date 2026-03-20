"""
协作状态同步机制 (Collaboration State Synchronizer)

实现多智能体间的实时状态同步和协作上下文管理：
- 状态广播和订阅机制
- 协作上下文共享
- 状态一致性保证
- 冲突检测和解决
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import weakref

logger = logging.getLogger(__name__)


class StateSyncMode(Enum):
    """状态同步模式"""
    REAL_TIME = "real_time"          # 实时同步
    BATCH = "batch"                 # 批量同步
    LAZY = "lazy"                   # 懒同步
    PERIODIC = "periodic"           # 定期同步


class StateScope(Enum):
    """状态作用域"""
    GLOBAL = "global"               # 全局状态
    SESSION = "session"             # 会话状态
    AGENT = "agent"                 # 智能体状态
    TASK = "task"                   # 任务状态


@dataclass
class StateSnapshot:
    """状态快照"""
    state_id: str
    scope: StateScope
    owner_id: str
    data: Dict[str, Any]
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'state_id': self.state_id,
            'scope': self.scope.value,
            'owner_id': self.owner_id,
            'data': self.data,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'checksum': self.checksum,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """从字典创建"""
        data_copy = data.copy()
        data_copy['scope'] = StateScope(data_copy['scope'])
        data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        return cls(**data_copy)


@dataclass
class CollaborationContext:
    """协作上下文"""
    context_id: str
    session_id: str
    participants: Set[str]
    shared_state: Dict[str, StateSnapshot] = field(default_factory=dict)
    state_versions: Dict[str, int] = field(default_factory=dict)  # state_id -> version
    subscribers: Dict[str, Set[str]] = field(default_factory=dict)  # state_id -> agent_ids
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_participant(self, agent_id: str):
        """添加参与者"""
        self.participants.add(agent_id)
        self.last_updated = datetime.now()

    def remove_participant(self, agent_id: str):
        """移除参与者"""
        self.participants.discard(agent_id)
        # 清理该智能体的订阅
        for state_subscribers in self.subscribers.values():
            state_subscribers.discard(agent_id)
        self.last_updated = datetime.now()

    def update_shared_state(self, state_snapshot: StateSnapshot):
        """更新共享状态"""
        state_id = state_snapshot.state_id
        current_version = self.state_versions.get(state_id, 0)

        if state_snapshot.version > current_version:
            self.shared_state[state_id] = state_snapshot
            self.state_versions[state_id] = state_snapshot.version
            self.last_updated = datetime.now()

            # 通知订阅者
            self._notify_subscribers(state_id, state_snapshot)

    def subscribe_to_state(self, agent_id: str, state_id: str):
        """订阅状态"""
        if state_id not in self.subscribers:
            self.subscribers[state_id] = set()
        self.subscribers[state_id].add(agent_id)

    def unsubscribe_from_state(self, agent_id: str, state_id: str):
        """取消订阅状态"""
        if state_id in self.subscribers:
            self.subscribers[state_id].discard(agent_id)

    def _notify_subscribers(self, state_id: str, state_snapshot: StateSnapshot):
        """通知订阅者"""
        # 这里会通过通信中间件发送通知
        pass

    def get_state_snapshot(self, state_id: str) -> Optional[StateSnapshot]:
        """获取状态快照"""
        return self.shared_state.get(state_id)

    def get_all_states(self) -> Dict[str, StateSnapshot]:
        """获取所有共享状态"""
        return self.shared_state.copy()


class StateChangeHandler(Protocol):
    """状态变更处理器协议"""
    async def on_state_changed(self, state_snapshot: StateSnapshot,
                             context: CollaborationContext) -> None:
        """状态变更回调"""
        ...


@dataclass
class SyncOperation:
    """同步操作"""
    operation_id: str
    operation_type: str  # create, update, delete, sync
    state_snapshot: Optional[StateSnapshot] = None
    target_agents: List[str] = field(default_factory=list)
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)


class StateConflictResolver:
    """状态冲突解决器"""

    def __init__(self):
        self.conflict_handlers: Dict[str, Callable] = {
            'last_write_wins': self._resolve_last_write_wins,
            'merge_strategy': self._resolve_merge_strategy,
            'version_based': self._resolve_version_based,
            'manual_override': self._resolve_manual_override
        }

    async def resolve_conflict(self, conflicting_states: List[StateSnapshot],
                             strategy: str = 'last_write_wins') -> StateSnapshot:
        """解决状态冲突"""
        handler = self.conflict_handlers.get(strategy, self._resolve_last_write_wins)
        return await handler(conflicting_states)

    async def _resolve_last_write_wins(self, states: List[StateSnapshot]) -> StateSnapshot:
        """最后写入胜出策略"""
        return max(states, key=lambda s: s.timestamp)

    async def _resolve_version_based(self, states: List[StateSnapshot]) -> StateSnapshot:
        """基于版本的解决策略"""
        return max(states, key=lambda s: s.version)

    async def _resolve_merge_strategy(self, states: List[StateSnapshot]) -> StateSnapshot:
        """合并策略"""
        # 取最新版本作为基础
        base_state = max(states, key=lambda s: s.version)

        # 合并数据（简单实现，实际可能需要更复杂的合并逻辑）
        merged_data = base_state.data.copy()

        for state in states:
            if state != base_state:
                # 合并非冲突字段
                for key, value in state.data.items():
                    if key not in merged_data or merged_data[key] == value:
                        merged_data[key] = value
                    # 对于冲突字段，可以添加冲突标记
                    elif merged_data[key] != value:
                        merged_data[f"{key}_conflict_{state.owner_id}"] = value

        return StateSnapshot(
            state_id=base_state.state_id,
            scope=base_state.scope,
            owner_id="merged",
            data=merged_data,
            version=base_state.version + 1,
            metadata={'merge_strategy': 'simple_merge', 'conflicts_resolved': len(states) - 1}
        )

    async def _resolve_manual_override(self, states: List[StateSnapshot]) -> StateSnapshot:
        """手动覆盖策略（返回最新状态，需要人工确认）"""
        latest_state = max(states, key=lambda s: s.timestamp)
        latest_state.metadata['requires_manual_review'] = True
        return latest_state


class CollaborationStateSynchronizer:
    """
    协作状态同步器

    提供多智能体间的状态同步服务：
    - 实时状态广播和订阅
    - 协作上下文管理
    - 状态一致性保证
    - 冲突检测和解决
    """

    def __init__(self):
        self.contexts: Dict[str, CollaborationContext] = {}
        self.state_handlers: Dict[str, List[StateChangeHandler]] = {}
        self.conflict_resolver = StateConflictResolver()

        # 同步队列
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.pending_operations: Dict[str, SyncOperation] = {}

        # 运行状态
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None

        # 配置
        self.sync_mode = StateSyncMode.REAL_TIME
        self.batch_size = 10
        self.sync_interval = 5  # 秒

    async def start(self):
        """启动状态同步器"""
        if self._running:
            return

        self._running = True
        self._sync_task = asyncio.create_task(self._sync_worker())
        logger.info("协作状态同步器已启动")

    async def stop(self):
        """停止状态同步器"""
        if not self._running:
            return

        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        logger.info("协作状态同步器已停止")

    async def create_collaboration_context(self, context_id: str,
                                         session_id: str,
                                         initial_participants: List[str]) -> CollaborationContext:
        """创建协作上下文"""
        if context_id in self.contexts:
            raise ValueError(f"协作上下文 {context_id} 已存在")

        context = CollaborationContext(
            context_id=context_id,
            session_id=session_id,
            participants=set(initial_participants)
        )

        self.contexts[context_id] = context
        logger.info(f"创建协作上下文: {context_id}, 参与者: {initial_participants}")
        return context

    async def join_collaboration_context(self, context_id: str, agent_id: str) -> bool:
        """加入协作上下文"""
        if context_id not in self.contexts:
            return False

        context = self.contexts[context_id]
        context.add_participant(agent_id)

        # 同步当前状态给新参与者
        await self._sync_state_to_agent(context, agent_id)

        logger.info(f"智能体 {agent_id} 加入协作上下文 {context_id}")
        return True

    async def leave_collaboration_context(self, context_id: str, agent_id: str):
        """离开协作上下文"""
        if context_id in self.contexts:
            context = self.contexts[context_id]
            context.remove_participant(agent_id)
            logger.info(f"智能体 {agent_id} 离开协作上下文 {context_id}")

            # 如果没有参与者了，清理上下文
            if not context.participants:
                del self.contexts[context_id]
                logger.info(f"清理空的协作上下文: {context_id}")

    async def publish_state(self, context_id: str, state_snapshot: StateSnapshot) -> bool:
        """发布状态"""
        if context_id not in self.contexts:
            return False

        context = self.contexts[context_id]

        # 检查版本冲突
        current_version = context.state_versions.get(state_snapshot.state_id, 0)
        if state_snapshot.version <= current_version:
            # 版本冲突，需要解决
            await self._handle_version_conflict(context, state_snapshot)
            return True

        # 更新共享状态
        context.update_shared_state(state_snapshot)

        # 根据同步模式处理
        if self.sync_mode == StateSyncMode.REAL_TIME:
            await self._sync_state_realtime(context, state_snapshot)
        elif self.sync_mode == StateSyncMode.BATCH:
            await self._queue_batch_sync(context, state_snapshot)
        else:
            # 懒同步或定期同步
            pass

        # 触发状态变更处理器
        await self._trigger_state_handlers(state_snapshot, context)

        logger.debug(f"发布状态: {state_snapshot.state_id} v{state_snapshot.version}")
        return True

    async def subscribe_to_state(self, context_id: str, agent_id: str,
                               state_id: str, handler: Optional[StateChangeHandler] = None):
        """订阅状态变更"""
        if context_id not in self.contexts:
            return False

        context = self.contexts[context_id]
        context.subscribe_to_state(agent_id, state_id)

        if handler:
            if state_id not in self.state_handlers:
                self.state_handlers[state_id] = []
            self.state_handlers[state_id].append(handler)

        # 发送当前状态
        current_state = context.get_state_snapshot(state_id)
        if current_state:
            await self._sync_state_to_agent(context, agent_id, [current_state])

        return True

    async def get_state(self, context_id: str, state_id: str) -> Optional[StateSnapshot]:
        """获取状态"""
        if context_id not in self.contexts:
            return None

        context = self.contexts[context_id]
        return context.get_state_snapshot(state_id)

    async def get_context_states(self, context_id: str) -> Dict[str, StateSnapshot]:
        """获取上下文的所有状态"""
        if context_id not in self.contexts:
            return {}

        context = self.contexts[context_id]
        return context.get_all_states()

    async def _sync_worker(self):
        """同步工作器"""
        while self._running:
            try:
                if self.sync_mode == StateSyncMode.PERIODIC:
                    await asyncio.sleep(self.sync_interval)
                    await self._perform_periodic_sync()
                elif self.sync_mode == StateSyncMode.BATCH:
                    await self._process_batch_operations()
                else:
                    await asyncio.sleep(0.1)  # 避免忙等待

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"同步工作器错误: {e}")

    async def _sync_state_realtime(self, context: CollaborationContext,
                                 state_snapshot: StateSnapshot):
        """实时同步状态"""
        # 获取订阅者
        subscribers = context.subscribers.get(state_snapshot.state_id, set())

        # 向所有参与者同步（除了状态拥有者）
        target_agents = context.participants - {state_snapshot.owner_id}

        if subscribers:
            target_agents = target_agents & subscribers

        if target_agents:
            await self._sync_state_to_agents(context, list(target_agents), [state_snapshot])

    async def _queue_batch_sync(self, context: CollaborationContext,
                              state_snapshot: StateSnapshot):
        """批量同步队列"""
        operation = SyncOperation(
            operation_id=f"sync_{state_snapshot.state_id}_{state_snapshot.version}",
            operation_type="sync",
            state_snapshot=state_snapshot,
            target_agents=list(context.participants - {state_snapshot.owner_id})
        )

        await self.sync_queue.put(operation)

    async def _process_batch_operations(self):
        """处理批量操作"""
        batch_operations = []

        # 收集一批操作
        for _ in range(self.batch_size):
            try:
                operation = self.sync_queue.get_nowait()
                batch_operations.append(operation)
                self.sync_queue.task_done()
            except asyncio.QueueEmpty:
                break

        if not batch_operations:
            return

        # 按上下文分组
        context_batches: Dict[str, List[SyncOperation]] = {}
        for op in batch_operations:
            if op.state_snapshot:
                context_id = op.state_snapshot.state_id.split('_')[0]  # 简单的上下文提取
                if context_id not in context_batches:
                    context_batches[context_id] = []
                context_batches[context_id].append(op)

        # 批量同步每个上下文
        for context_id, operations in context_batches.items():
            if context_id in self.contexts:
                context = self.contexts[context_id]
                states_to_sync = [op.state_snapshot for op in operations if op.state_snapshot]
                target_agents = set()
                for op in operations:
                    target_agents.update(op.target_agents)

                await self._sync_state_to_agents(context, list(target_agents), states_to_sync)

    async def _perform_periodic_sync(self):
        """执行定期同步"""
        for context in self.contexts.values():
            # 检查需要同步的状态
            for state_id, subscribers in context.subscribers.items():
                if subscribers:
                    state_snapshot = context.get_state_snapshot(state_id)
                    if state_snapshot:
                        await self._sync_state_to_agents(
                            context,
                            list(subscribers),
                            [state_snapshot]
                        )

    async def _sync_state_to_agent(self, context: CollaborationContext,
                                 agent_id: str,
                                 states: Optional[List[StateSnapshot]] = None):
        """向单个智能体同步状态"""
        if states is None:
            states = list(context.shared_state.values())

        await self._sync_state_to_agents(context, [agent_id], states)

    async def _sync_state_to_agents(self, context: CollaborationContext,
                                  agent_ids: List[str],
                                  states: List[StateSnapshot]):
        """向多个智能体同步状态"""
        # 这里应该通过通信中间件发送状态同步消息
        # 暂时记录日志
        for agent_id in agent_ids:
            for state in states:
                logger.debug(f"同步状态 {state.state_id} v{state.version} 给智能体 {agent_id}")

    async def _handle_version_conflict(self, context: CollaborationContext,
                                     new_state: StateSnapshot):
        """处理版本冲突"""
        state_id = new_state.state_id
        existing_state = context.get_state_snapshot(state_id)

        if existing_state:
            # 解决冲突
            resolved_state = await self.conflict_resolver.resolve_conflict(
                [existing_state, new_state],
                strategy='last_write_wins'
            )

            # 更新为解决后的状态
            context.update_shared_state(resolved_state)
            logger.warning(f"解决状态冲突: {state_id}, 版本 {existing_state.version} -> {new_state.version}")

    async def _trigger_state_handlers(self, state_snapshot: StateSnapshot,
                                    context: CollaborationContext):
        """触发状态变更处理器"""
        state_id = state_snapshot.state_id

        if state_id in self.state_handlers:
            for handler in self.state_handlers[state_id]:
                try:
                    await handler.on_state_changed(state_snapshot, context)
                except Exception as e:
                    logger.error(f"状态处理器错误: {e}")

    def set_sync_mode(self, mode: StateSyncMode):
        """设置同步模式"""
        self.sync_mode = mode
        logger.info(f"设置同步模式: {mode.value}")

    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        if context_id not in self.contexts:
            return None

        context = self.contexts[context_id]
        return {
            'context_id': context.context_id,
            'session_id': context.session_id,
            'participants': list(context.participants),
            'shared_states': len(context.shared_state),
            'created_at': context.created_at.isoformat(),
            'last_updated': context.last_updated.isoformat()
        }

    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        total_contexts = len(self.contexts)
        total_states = sum(len(ctx.shared_state) for ctx in self.contexts.values())
        total_participants = sum(len(ctx.participants) for ctx in self.contexts.values())

        return {
            'active_contexts': total_contexts,
            'total_shared_states': total_states,
            'total_participants': total_participants,
            'sync_mode': self.sync_mode.value,
            'pending_operations': self.sync_queue.qsize()
        }


# 全局实例
_synchronizer_instance: Optional[CollaborationStateSynchronizer] = None

def get_collaboration_state_synchronizer() -> CollaborationStateSynchronizer:
    """获取协作状态同步器实例"""
    global _synchronizer_instance
    if _synchronizer_instance is None:
        _synchronizer_instance = CollaborationStateSynchronizer()
    return _synchronizer_instance
