"""
Agent Test Execution Service - Execute agents and track execution progress
"""
import asyncio
import uuid
import time
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    step_type: str  # reason, act, observe, final
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    tool_name: Optional[str] = None
    tool_input: Optional[Dict] = None
    tool_output: Optional[str] = None


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    agent_id: str
    query: str
    answer: str
    status: str  # running, completed, failed, terminated
    steps: list = field(default_factory=list)
    tools_used: list = field(default_factory=list)
    total_duration: float = 0.0
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class AgentExecutor:
    """Agent执行器 - 执行Agent并跟踪执行过程"""
    
    def __init__(self):
        self.db = get_database()
        self._executions: Dict[str, ExecutionResult] = {}
    
    async def execute_agent(
        self, 
        agent_id: str, 
        query: str,
        callback: Optional[Callable[[ExecutionStep], None]] = None
    ) -> ExecutionResult:
        """执行Agent并返回结果"""
        
        # 获取Agent信息
        agent = self.db.get_agent(agent_id)
        if not agent:
            return ExecutionResult(
                execution_id="",
                agent_id=agent_id,
                query=query,
                answer="",
                status="failed",
                error=f"Agent不存在: {agent_id}"
            )
        
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        result = ExecutionResult(
            execution_id=execution_id,
            agent_id=agent_id,
            query=query,
            answer="",
            status="running"
        )
        self._executions[execution_id] = result
        
        # 获取关联的Tools和Skills
        agent_tools = self.db.get_agent_tools(agent_id)
        agent_skills = self.db.get_agent_skills(agent_id)
        
        try:
            # 步骤1: 理解需求 (Reason)
            step = ExecutionStep(
                step_id=f"{execution_id}_1",
                step_type="reason",
                content=f"理解任务: {query}"
            )
            result.steps.append(step)
            if callback:
                callback(step)
            
            await asyncio.sleep(0.1)  # 模拟思考时间
            
            # 步骤2: 计划 (Reason)
            tools_str = ", ".join([t['name'] for t in agent_tools]) or "无"
            step = ExecutionStep(
                step_id=f"{execution_id}_2",
                step_type="reason",
                content=f"计划: 需要使用工具 [{tools_str}] 来完成任务"
            )
            result.steps.append(step)
            if callback:
                callback(step)
            
            await asyncio.sleep(0.1)
            
            # 步骤3: 执行工具调用 (Act)
            for i, tool in enumerate(agent_tools):
                tool_step = ExecutionStep(
                    step_id=f"{execution_id}_3_{i}",
                    step_type="act",
                    content=f"调用工具: {tool['name']}",
                    tool_name=tool['name'],
                    tool_input={"query": query}
                )
                result.steps.append(tool_step)
                result.tools_used.append(tool['name'])
                if callback:
                    callback(tool_step)
                
                # 模拟工具执行
                await asyncio.sleep(0.2)
                
                # 观察结果 (Observe)
                observe_step = ExecutionStep(
                    step_id=f"{execution_id}_4_{i}",
                    step_type="observe",
                    content=f"工具 [{tool['name']}] 执行完成",
                    tool_name=tool['name'],
                    tool_output=f"模拟输出 for {query}"
                )
                result.steps.append(observe_step)
                if callback:
                    callback(observe_step)
            
            # 步骤4: 生成答案 (Final)
            final_step = ExecutionStep(
                step_id=f"{execution_id}_5",
                step_type="final",
                content=f"任务完成: 已处理 '{query}'"
            )
            result.steps.append(final_step)
            if callback:
                callback(final_step)
            
            # 生成答案
            result.answer = f"Agent [{agent['name']}] 已处理任务: {query}\n\n使用工具: {', '.join(result.tools_used) or '无'}\n\n(这是一个模拟执行结果，实际执行需要连接真实的LLM后端)"
            result.status = "completed"
            
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.error(f"Agent execution failed: {e}")
        
        result.total_duration = time.time() - start_time
        result.completed_at = datetime.now()
        
        return result
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """获取执行结果"""
        return self._executions.get(execution_id)
    
    def terminate_execution(self, execution_id: str) -> bool:
        """终止执行"""
        if execution_id in self._executions:
            self._executions[execution_id].status = "terminated"
            self._executions[execution_id].completed_at = datetime.now()
            return True
        return False


def get_agent_executor() -> AgentExecutor:
    """获取Agent执行器实例"""
    return AgentExecutor()
