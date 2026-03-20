#!/usr/bin/env python3
"""
RANGEN Gateway控制平面
基于OpenClaw Gateway架构设计，作为系统的神经中枢与控制平面

核心职责：
1. 统一接入：支持多协议、多前端的消息统一接入
2. 消息路由：智能分发消息到正确的Agent + Session
3. 安全前置检查：在任务开始前完成权限、预算、合规性检查
4. Agent装备：为Agent注入Session状态、工具集、能力上下文
5. 车道式队列调度：显式并行、默认串行的智能调度
6. 状态管理与监控：全链路可观测性和审计追踪

设计原则：
- 控制平面上移：将Agent的控制逻辑上提到Gateway
- 安全前置化：在任务开始前完成安全边界装配
- 关注点分离：Agent只专注于推理与执行
- 插件化适配：支持多渠道、多协议的插件化适配器
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .rangen_state import get_global_state_manager, RANGENState
from .hierarchical_tool_system import get_global_tool_system, ToolLayer, ToolPermission
from .double_loop_processor_chain import OuterSessionLoop, InnerExecutionLoop, LoopSignal
from ..services.deepseek_cost_controller import get_global_deepseek_cost_controller

logger = logging.getLogger(__name__)


class MessageChannel(Enum):
    """消息渠道类型枚举"""
    HTTP_API = "http_api"           # HTTP RESTful API
    WEBSOCKET = "websocket"         # WebSocket实时通信
    MCP = "mcp"                     # Model Context Protocol
    CLI = "cli"                     # 命令行接口
    TELEGRAM = "telegram"          # Telegram Bot
    DISCORD = "discord"            # Discord Bot
    CUSTOM = "custom"              # 自定义渠道


class MessagePriority(Enum):
    """消息优先级枚举"""
    CRITICAL = "critical"          # 关键任务（立即执行）
    HIGH = "high"                  # 高优先级（优先执行）
    NORMAL = "normal"              # 普通优先级（默认）
    LOW = "low"                    # 低优先级（可延迟执行）
    BACKGROUND = "background"      # 后台任务（空闲时执行）


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"            # 等待处理
    ROUTING = "routing"            # 路由中
    PRE_CHECKING = "pre_checking"  # 安全前置检查中
    AGENT_ASSEMBLING = "agent_assembling"  # Agent装备中
    EXECUTING = "executing"        # 执行中
    COMPLETED = "completed"        # 完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 取消


@dataclass
class GatewayMessage:
    """Gateway统一消息格式"""
    message_id: str
    channel: MessageChannel
    sender: Dict[str, Any]          # 发送者信息
    content: Dict[str, Any]         # 消息内容
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL


@dataclass
class RoutingRule:
    """路由规则"""
    condition: Callable[[GatewayMessage], bool]  # 路由条件函数
    target_agent: str                           # 目标Agent类型
    target_session: Optional[str] = None        # 目标Session ID（可选）


@dataclass
class SafetyCheckResult:
    """安全前置检查结果"""
    allowed: bool                               # 是否允许执行
    message: str                                # 检查结果消息
    warnings: List[str] = field(default_factory=list)  # 警告信息
    required_actions: List[str] = field(default_factory=list)  # 需要执行的动作


@dataclass
class AgentAssemblyContext:
    """Agent装备上下文"""
    agent_type: str                             # Agent类型
    session_state: Dict[str, Any]               # 会话状态
    available_tools: List[str]                  # 可用工具列表
    user_context: Dict[str, Any]                # 用户上下文
    constraints: Dict[str, Any] = field(default_factory=dict)  # 执行约束


@dataclass
class TaskExecutionResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RANGENGateway:
    """RANGEN Gateway控制平面"""
    
    def __init__(self):
        """初始化Gateway控制平面"""
        logger.info("初始化RANGEN Gateway控制平面")
        
        # 核心组件集成
        self.state_manager = get_global_state_manager()
        self.tool_system = get_global_tool_system()
        self.cost_controller = get_global_deepseek_cost_controller()
        
        # 路由规则引擎
        self.routing_rules: List[RoutingRule] = []
        
        # 任务队列（按优先级组织）将在start()方法中初始化
        self.task_queues: Dict[MessagePriority, asyncio.Queue] = {}
        
        # 执行状态跟踪
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[TaskExecutionResult] = []
        
        # 车道式队列管理器
        self.lane_manager = LaneQueueManager()
        
        # 插件化适配器注册表
        self.channel_adapters: Dict[MessageChannel, Any] = {}
        
        # 初始化默认路由规则
        self._initialize_default_routing_rules()
        
        # 启动任务处理器
        self._task_processor_task = None
        
        logger.info("RANGEN Gateway控制平面初始化完成")
    
    def _initialize_default_routing_rules(self):
        """初始化默认路由规则"""
        # 根据任务类型路由到不同的Agent
        self.routing_rules.append(
            RoutingRule(
                condition=lambda msg: msg.content.get("task_type") == "code_generation",
                target_agent="code_agent",
                target_session=None
            )
        )
        
        self.routing_rules.append(
            RoutingRule(
                condition=lambda msg: msg.content.get("task_type") == "analysis",
                target_agent="analysis_agent",
                target_session=None
            )
        )
        
        self.routing_rules.append(
            RoutingRule(
                condition=lambda msg: msg.content.get("task_type") == "research",
                target_agent="research_agent",
                target_session=None
            )
        )
        
        logger.info(f"初始化了 {len(self.routing_rules)} 个默认路由规则")
    
    async def start(self):
        """启动Gateway服务"""
        logger.info("启动Gateway服务...")
        
        # 初始化任务队列
        self.task_queues = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        
        # 启动任务处理器
        self._task_processor_task = asyncio.create_task(self._process_tasks())
        
        # 启动各渠道适配器
        for channel, adapter in self.channel_adapters.items():
            if hasattr(adapter, 'start'):
                await adapter.start()
        
        logger.info("Gateway服务启动完成")
    
    async def stop(self):
        """停止Gateway服务"""
        logger.info("停止Gateway服务...")
        
        # 停止任务处理器
        if self._task_processor_task:
            self._task_processor_task.cancel()
            try:
                await self._task_processor_task
            except asyncio.CancelledError:
                pass
        
        # 停止各渠道适配器
        for channel, adapter in self.channel_adapters.items():
            if hasattr(adapter, 'stop'):
                await adapter.stop()
        
        logger.info("Gateway服务已停止")
    
    def register_channel_adapter(self, channel: MessageChannel, adapter: Any):
        """注册渠道适配器"""
        self.channel_adapters[channel] = adapter
        logger.info(f"注册渠道适配器: {channel.value}")
    
    async def receive_message(self, channel: MessageChannel, raw_message: Dict[str, Any]) -> str:
        """
        接收消息并进行统一处理
        
        Args:
            channel: 消息渠道
            raw_message: 原始消息
            
        Returns:
            任务ID
        """
        try:
            # 1. 统一消息格式转换
            gateway_message = self._convert_to_gateway_format(channel, raw_message)
            
            # 2. 路由决策
            routing_result = await self._route_message(gateway_message)
            
            # 3. 创建任务
            task_id = f"task_{int(time.time()*1000)}_{gateway_message.message_id[-6:]}"
            
            # 4. 入队处理（按优先级）
            task_data = {
                "task_id": task_id,
                "message": gateway_message,
                "routing_result": routing_result,
                "timestamp": datetime.now()
            }
            
            await self.task_queues[gateway_message.priority].put(task_data)
            
            # 5. 记录状态
            self.active_tasks[task_id] = {
                "status": TaskStatus.PENDING,
                "message": gateway_message,
                "created_at": datetime.now()
            }
            
            logger.info(f"收到消息并创建任务: {task_id}, 渠道: {channel.value}, 优先级: {gateway_message.priority.value}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"接收消息失败: {e}")
            raise
    
    def _convert_to_gateway_format(self, channel: MessageChannel, raw_message: Dict[str, Any]) -> GatewayMessage:
        """将原始消息转换为Gateway统一格式"""
        # 这里应该根据不同的渠道进行格式转换
        # 简化实现：假设原始消息已经包含必要字段
        
        message_id = raw_message.get("message_id", f"msg_{int(time.time()*1000)}")
        sender = raw_message.get("sender", {"type": "unknown", "id": "unknown"})
        content = raw_message.get("content", {})
        metadata = raw_message.get("metadata", {})
        
        # 解析优先级
        priority_str = raw_message.get("priority", "normal").lower()
        try:
            priority = MessagePriority(priority_str)
        except ValueError:
            priority = MessagePriority.NORMAL
        
        return GatewayMessage(
            message_id=message_id,
            channel=channel,
            sender=sender,
            content=content,
            metadata=metadata,
            priority=priority
        )
    
    async def _route_message(self, message: GatewayMessage) -> Dict[str, Any]:
        """路由消息到合适的Agent和Session"""
        # 应用路由规则
        for rule in self.routing_rules:
            try:
                if rule.condition(message):
                    # 找到匹配的路由规则
                    session_id = rule.target_session
                    if not session_id:
                        # 如果没有指定Session，根据发送者创建或查找Session
                        session_id = self._get_or_create_session(message.sender)
                    
                    return {
                        "agent_type": rule.target_agent,
                        "session_id": session_id,
                        "matched_rule": rule
                    }
            except Exception as e:
                logger.warning(f"路由规则执行失败: {e}")
                continue
        
        # 默认路由：使用通用Agent
        session_id = self._get_or_create_session(message.sender)
        return {
            "agent_type": "general_agent",
            "session_id": session_id,
            "matched_rule": None
        }
    
    def _get_or_create_session(self, sender: Dict[str, Any]) -> str:
        """获取或创建会话ID"""
        # 简化的Session管理：基于发送者ID创建Session
        sender_id = sender.get("id", "anonymous")
        session_id = f"session_{sender_id}_{int(time.time())}"
        return session_id
    
    async def _process_tasks(self):
        """任务处理主循环"""
        logger.info("任务处理器启动")
        
        try:
            while True:
                # 按优先级顺序处理任务
                for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                                MessagePriority.NORMAL, MessagePriority.LOW, 
                                MessagePriority.BACKGROUND]:
                    
                    if not self.task_queues[priority].empty():
                        try:
                            # 获取任务
                            task_data = await asyncio.wait_for(
                                self.task_queues[priority].get(),
                                timeout=0.1
                            )
                            
                            # 处理任务
                            asyncio.create_task(self._execute_task(task_data))
                            
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"获取任务失败: {e}")
                
                # 短暂休眠避免CPU占用过高
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            logger.info("任务处理器被取消")
        except Exception as e:
            logger.error(f"任务处理器异常: {e}")
    
    async def _execute_task(self, task_data: Dict[str, Any]):
        """执行单个任务"""
        task_id = task_data["task_id"]
        message = task_data["message"]
        routing_result = task_data["routing_result"]
        
        try:
            # 更新任务状态
            self.active_tasks[task_id]["status"] = TaskStatus.ROUTING
            self.active_tasks[task_id]["routing_result"] = routing_result
            
            logger.info(f"开始执行任务: {task_id}, Agent类型: {routing_result['agent_type']}")
            
            # 1. 安全前置检查
            self.active_tasks[task_id]["status"] = TaskStatus.PRE_CHECKING
            safety_result = await self._perform_safety_checks(message, routing_result)
            
            if not safety_result.allowed:
                # 安全检查失败
                result = TaskExecutionResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=f"安全前置检查失败: {safety_result.message}",
                    execution_time=0.0,
                    cost=0.0
                )
                
                self._finalize_task(task_id, result)
                return
            
            # 2. Agent装备
            self.active_tasks[task_id]["status"] = TaskStatus.AGENT_ASSEMBLING
            assembly_context = await self._assemble_agent_context(message, routing_result, safety_result)
            
            # 3. 执行任务
            self.active_tasks[task_id]["status"] = TaskStatus.EXECUTING
            execution_result = await self._execute_agent_task(
                task_id, message, routing_result, assembly_context
            )
            
            # 4. 记录结果
            self._finalize_task(task_id, execution_result)
            
        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            
            result = TaskExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=0.0,
                cost=0.0
            )
            
            self._finalize_task(task_id, result)
    
    async def _perform_safety_checks(self, message: GatewayMessage, routing_result: Dict[str, Any]) -> SafetyCheckResult:
        """执行安全前置检查"""
        warnings = []
        required_actions = []
        
        # 1. 权限检查
        sender_permissions = message.sender.get("permissions", [])
        agent_type = routing_result["agent_type"]
        
        # 简化的权限检查：这里可以根据实际需求实现更复杂的权限系统
        if agent_type == "admin_agent" and "admin" not in sender_permissions:
            return SafetyCheckResult(
                allowed=False,
                message="权限不足：需要管理员权限",
                warnings=warnings,
                required_actions=required_actions
            )
        
        # 2. 预算检查（集成DeepSeek成本控制器）
        try:
            sender_id = message.sender.get("id", "anonymous")
            project_id = message.metadata.get("project_id", "default")
            
            # 这里可以调用成本控制器的预算检查功能
            # 简化实现：总是通过
            budget_check = {"allowed": True, "message": "预算检查通过"}
            
            if not budget_check.get("allowed", True):
                warnings.append(f"预算检查警告: {budget_check.get('message')}")
        
        except Exception as e:
            logger.warning(f"预算检查失败: {e}")
            warnings.append(f"预算检查异常: {e}")
        
        # 3. 合规性检查（示例）
        content_str = str(message.content).lower()
        blocked_keywords = ["sensitive", "confidential", "secret"]
        
        for keyword in blocked_keywords:
            if keyword in content_str:
                warnings.append(f"内容包含敏感词汇: {keyword}")
        
        return SafetyCheckResult(
            allowed=True,
            message="安全前置检查通过",
            warnings=warnings,
            required_actions=required_actions
        )
    
    async def _assemble_agent_context(self, message: GatewayMessage, routing_result: Dict[str, Any], 
                                     safety_result: SafetyCheckResult) -> AgentAssemblyContext:
        """装配Agent执行上下文"""
        # 获取或创建Session状态
        session_id = routing_result["session_id"]
        session_state = await self._get_session_state(session_id, message.sender)
        
        # 获取可用工具列表（基于用户权限和任务类型）
        available_tools = await self._get_available_tools(message.sender, routing_result["agent_type"])
        
        # 构建用户上下文
        user_context = {
            "user_id": message.sender.get("id", "anonymous"),
            "permissions": message.sender.get("permissions", []),
            "roles": message.sender.get("roles", []),
            "metadata": message.sender.get("metadata", {})
        }
        
        # 构建执行约束
        constraints = {
            "max_cost": message.metadata.get("max_cost", 1.0),  # 默认1美元
            "timeout_seconds": message.metadata.get("timeout_seconds", 60.0),
            "max_iterations": message.metadata.get("max_iterations", 10),
            "safety_warnings": safety_result.warnings
        }
        
        return AgentAssemblyContext(
            agent_type=routing_result["agent_type"],
            session_state=session_state,
            available_tools=available_tools,
            user_context=user_context,
            constraints=constraints
        )
    
    async def _get_session_state(self, session_id: str, sender: Dict[str, Any]) -> Dict[str, Any]:
        """获取或创建会话状态"""
        # 这里应该集成状态管理器
        # 简化实现：返回基本状态
        return {
            "session_id": session_id,
            "user_id": sender.get("id", "anonymous"),
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "total_cost": 0.0
        }
    
    async def _get_available_tools(self, sender: Dict[str, Any], agent_type: str) -> List[str]:
        """获取可用工具列表"""
        # 这里应该集成分层工具系统
        # 简化实现：返回所有公开工具
        
        available_tools = []
        
        # 获取所有工具
        all_tools = self.tool_system.list_tools()
        
        for tool_info in all_tools:
            tool_name = tool_info.get("metadata", {}).get("name")
            if tool_name:
                # 简化的权限检查：只返回公开工具
                tool_metadata = self.tool_system.get_tool_info(tool_name)
                if tool_metadata:
                    metadata_dict = tool_metadata.get("metadata", {})
                    if metadata_dict.get("permission") == ToolPermission.PUBLIC.value:
                        available_tools.append(tool_name)
        
        return available_tools
    
    async def _execute_agent_task(self, task_id: str, message: GatewayMessage, 
                                 routing_result: Dict[str, Any], assembly_context: AgentAssemblyContext) -> TaskExecutionResult:
        """执行Agent任务"""
        start_time = time.time()
        
        try:
            # 这里应该根据agent_type选择不同的执行策略
            # 简化实现：使用通用的双层循环处理器
            
            # 创建外层循环配置
            from .double_loop_processor_chain import SessionConfig
            
            session_config = SessionConfig(
                session_id=assembly_context.session_state["session_id"],
                max_iterations=assembly_context.constraints.get("max_iterations", 10),
                timeout_seconds=assembly_context.constraints.get("timeout_seconds", 60.0),
                enable_doom_loop_detection=True,
                enable_context_compaction=True,
                budget_limit=assembly_context.constraints.get("max_cost", 1.0)
            )
            
            # 创建外层循环实例
            outer_loop = OuterSessionLoop(config=session_config)
            
            # 准备请求数据
            request_data = {
                "query": message.content.get("query", ""),
                "task_type": message.content.get("task_type", "general"),
                "session_id": assembly_context.session_state["session_id"],
                "user_id": assembly_context.user_context["user_id"],
                "available_tools": assembly_context.available_tools,
                "constraints": assembly_context.constraints
            }
            
            # 执行会话
            session_result = await outer_loop.run_session(request_data)
            
            # 计算执行时间和成本
            execution_time = time.time() - start_time
            
            # 获取实际成本（这里简化处理）
            cost = assembly_context.constraints.get("max_cost", 1.0) * 0.1  # 假设消耗10%的预算
            
            return TaskExecutionResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result=session_result,
                execution_time=execution_time,
                cost=cost,
                metadata={
                    "agent_type": routing_result["agent_type"],
                    "session_id": assembly_context.session_state["session_id"],
                    "tool_count": len(assembly_context.available_tools)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskExecutionResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                cost=0.0
            )
    
    def _finalize_task(self, task_id: str, result: TaskExecutionResult):
        """最终化任务处理"""
        # 更新任务状态
        self.active_tasks[task_id]["status"] = result.status
        self.active_tasks[task_id]["completed_at"] = datetime.now()
        self.active_tasks[task_id]["result"] = result
        
        # 添加到历史记录
        self.task_history.append(result)
        
        # 清理活跃任务（保留最近100个）
        if len(self.active_tasks) > 100:
            # 移除最早的任务
            oldest_tasks = sorted(self.active_tasks.items(), key=lambda x: x[1].get("created_at", datetime.min))
            for old_id, _ in oldest_tasks[:len(self.active_tasks) - 100]:
                del self.active_tasks[old_id]
        
        logger.info(f"任务完成: {task_id}, 状态: {result.status.value}, 耗时: {result.execution_time:.2f}s, 成本: ${result.cost:.6f}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # 在历史记录中查找
        for result in reversed(self.task_history):
            if result.task_id == task_id:
                return {
                    "task_id": task_id,
                    "status": result.status,
                    "result": result.result,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "cost": result.cost,
                    "completed": True
                }
        
        return None
    
    def get_gateway_stats(self) -> Dict[str, Any]:
        """获取Gateway统计信息"""
        active_by_status = {}
        for task_id, task_data in self.active_tasks.items():
            status = task_data.get("status", TaskStatus.PENDING)
            active_by_status[status.value] = active_by_status.get(status.value, 0) + 1
        
        completed_count = len(self.task_history)
        failed_count = sum(1 for r in self.task_history if r.status == TaskStatus.FAILED)
        
        total_cost = sum(r.cost for r in self.task_history)
        
        return {
            "active_tasks": len(self.active_tasks),
            "active_by_status": active_by_status,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "total_cost": total_cost,
            "queue_sizes": {p.value: q.qsize() for p, q in self.task_queues.items()}
        }


class LaneQueueManager:
    """车道式队列管理器"""
    
    def __init__(self):
        self.lanes: Dict[str, asyncio.Queue] = {}
        self.lane_rules: Dict[str, Callable] = {}
    
    def create_lane(self, lane_id: str, condition: Callable):
        """创建车道"""
        self.lanes[lane_id] = asyncio.Queue()
        self.lane_rules[lane_id] = condition
        return lane_id
    
    def route_to_lane(self, task_data: Dict[str, Any]) -> Optional[str]:
        """路由任务到合适的车道"""
        for lane_id, condition in self.lane_rules.items():
            try:
                if condition(task_data):
                    return lane_id
            except Exception:
                continue
        return None
    
    async def process_lane(self, lane_id: str, processor: Callable):
        """处理车道中的任务"""
        if lane_id not in self.lanes:
            raise ValueError(f"车道不存在: {lane_id}")
        
        queue = self.lanes[lane_id]
        
        while True:
            task_data = await queue.get()
            try:
                await processor(task_data)
            except Exception as e:
                logger.error(f"车道处理失败: {lane_id}, 错误: {e}")
            finally:
                queue.task_done()


# 全局Gateway实例
_global_gateway: Optional[RANGENGateway] = None

def get_global_gateway() -> RANGENGateway:
    """获取全局Gateway实例"""
    global _global_gateway
    if _global_gateway is None:
        _global_gateway = RANGENGateway()
    return _global_gateway

async def initialize_global_gateway():
    """初始化全局Gateway"""
    gateway = get_global_gateway()
    await gateway.start()
    return gateway