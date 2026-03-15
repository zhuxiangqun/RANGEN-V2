"""
Agent Test Execution API - Execute agents with real-time visualization
"""
import asyncio
import json
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.services.test_execution import get_agent_executor, ExecutionStep
from src.services.database import get_database

router = APIRouter(prefix="/api/v1/test", tags=["test"])


class TestExecuteRequest(BaseModel):
    """测试执行请求"""
    agent_id: str = Field(..., description="Agent ID")
    query: str = Field(..., description="测试任务")
    stream: bool = Field(default=True, description="是否使用SSE流式推送")


class TestExecuteResponse(BaseModel):
    """测试执行响应"""
    execution_id: str
    agent_id: str
    query: str
    status: str
    answer: Optional[str] = None
    steps: list = []
    tools_used: list = []
    total_duration: float = 0.0
    error: Optional[str] = None


@router.post("/execute", response_model=TestExecuteResponse)
async def execute_agent_test(request: TestExecuteRequest):
    """
    执行Agent测试 (非流式)
    """
    # 验证Agent存在
    db = get_database()
    agent = db.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {request.agent_id}"
        )
    
    executor = get_agent_executor()
    
    try:
        result = await executor.execute_agent(
            agent_id=request.agent_id,
            query=request.query
        )
        
        return TestExecuteResponse(
            execution_id=result.execution_id,
            agent_id=result.agent_id,
            query=result.query,
            status=result.status,
            answer=result.answer,
            steps=[{
                "step_id": s.step_id,
                "step_type": s.step_type,
                "content": s.content,
                "tool_name": s.tool_name,
                "tool_input": s.tool_input,
                "tool_output": s.tool_output,
                "timestamp": s.timestamp.isoformat()
            } for s in result.steps],
            tools_used=result.tools_used,
            total_duration=result.total_duration,
            error=result.error
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行失败: {str(e)}"
        )


async def generate_sse(executor, agent_id: str, query: str):
    """生成SSE流式响应"""
    execution_id = None
    
    try:
        # 步骤1: 开始执行
        execution_id = f"exec_{int(time.time() * 1000)}"
        yield f"data: {json.dumps({'type': 'start', 'execution_id': execution_id, 'query': query})}\n\n"
        
        # 获取Agent
        db = get_database()
        agent = db.get_agent(agent_id)
        if not agent:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Agent不存在: {agent_id}'})}\n\n"
            return
        
        # 获取关联的Tools
        agent_tools = db.get_agent_tools(agent_id)
        
        # 步骤2: 推理
        yield f"data: {json.dumps({'type': 'step', 'step_type': 'reason', 'content': f'理解任务: {query}', 'step': 1})}\n\n"
        await asyncio.sleep(0.3)
        
        # 步骤3: 计划
        tools_str = ", ".join([t['name'] for t in agent_tools]) or "无"
        yield f"data: {json.dumps({'type': 'step', 'step_type': 'reason', 'content': f'计划: 需要使用工具 [{tools_str}] 来完成任务', 'step': 2})}\n\n"
        await asyncio.sleep(0.3)
        
        # 步骤4: 执行工具
        for i, tool in enumerate(agent_tools):
            yield f"data: {json.dumps({'type': 'step', 'step_type': 'act', 'content': f'调用工具: {tool["name"]}', 'tool_name': tool['name'], 'step': 3 + i})}\n\n"
            await asyncio.sleep(0.2)
            
            yield f"data: {json.dumps({'type': 'step', 'step_type': 'observe', 'content': f'工具 [{tool["name"]}] 执行完成', 'tool_name': tool['name'], 'step': 4 + i})}\n\n"
            await asyncio.sleep(0.2)
        
        # 步骤5: 完成
        answer = f"Agent [{agent['name']}] 已处理任务: {query}\n\n使用工具: {', '.join([t['name'] for t in agent_tools]) or '无'}\n\n(模拟执行结果)"
        
        yield f"data: {json.dumps({'type': 'step', 'step_type': 'final', 'content': '任务完成', 'step': 10})}\n\n"
        
        yield f"data: {json.dumps({'type': 'complete', 'answer': answer, 'tools_used': [t['name'] for t in agent_tools]})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/execute/stream")
async def execute_agent_test_stream(request: TestExecuteRequest):
    """
    执行Agent测试 (SSE流式)
    """
    # 验证Agent存在
    db = get_database()
    agent = db.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent不存在: {request.agent_id}"
        )
    
    return StreamingResponse(
        generate_sse(get_agent_executor(), request.agent_id, request.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """获取执行状态"""
    executor = get_agent_executor()
    result = executor.get_execution(execution_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行不存在: {execution_id}"
        )
    
    return {
        "execution_id": result.execution_id,
        "agent_id": result.agent_id,
        "query": result.query,
        "status": result.status,
        "answer": result.answer,
        "steps": len(result.steps),
        "tools_used": result.tools_used,
        "total_duration": result.total_duration,
        "error": result.error
    }


@router.post("/terminate/{execution_id}")
async def terminate_execution(execution_id: str):
    """终止执行"""
    executor = get_agent_executor()
    success = executor.terminate_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行不存在: {execution_id}"
        )
    
    return {"message": "执行已终止", "execution_id": execution_id}
