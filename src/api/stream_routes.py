#!/usr/bin/env python3
"""
Event Streaming API Routes - 事件流API路由

提供SSE (Server-Sent Events) 流式传输端点
集成事件驱动流式传输系统
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.core.events import (
    EventType,
    AgentEvent,
    EventStream,
    StreamingFormatter,
    create_event_stream,
    get_event_stream,
    get_event_stream_manager
)
from ..api.models import ChatRequest

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/stream", tags=["event-streaming"])


class StreamAuth:
    """流认证依赖"""
    
    @staticmethod
    async def require_stream_access(auth_data: dict = Depends(lambda: {})):
        """验证流访问权限"""
        # TODO: 实现实际的认证逻辑
        return {"allowed": True}


async def event_generator(session_id: str):
    """
    事件生成器 - 用于SSE流
    
    Args:
        session_id: 会话ID
        
    Yields:
        SSE格式的事件数据
    """
    # 获取或创建事件流
    event_stream = get_event_stream(session_id)
    if event_stream is None:
        event_stream = create_event_stream(session_id)
    
    try:
        # 发送初始连接事件
        yield f"data: {json.dumps({'event': 'connected', 'session_id': session_id})}\n\n"
        
        # 持续获取事件
        while True:
            event = await event_stream.get_event(timeout=1.0)
            
            if event:
                # 转换为SSE格式
                sse_data = StreamingFormatter.to_sse(event)
                yield sse_data
            
            # 检查是否应该停止
            if event_stream._should_stop:
                break
            
            # 短暂休眠避免CPU占用过高
            await asyncio.sleep(0.01)
            
    except asyncio.CancelledError:
        # 客户端断开连接
        logger.info(f"Stream disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    finally:
        # 清理
        event_stream.stop()


@router.get("/events/{session_id}")
async def stream_events(
    session_id: str,
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    SSE事件流端点
    
    通过Server-Sent Events流式传输Agent事件
    
    Args:
        session_id: 会话ID
        
    Returns:
        SSE流
    """
    return StreamingResponse(
        event_generator(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/events/{session_id}/start")
async def start_stream(
    session_id: str,
    query: str,
    context: Optional[dict] = None,
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    启动事件流并执行任务
    
    Args:
        session_id: 会话ID
        query: 查询内容
        context: 上下文
        
    Returns:
        启动结果
    """
    try:
        # 创建或获取事件流
        event_stream = get_event_stream(session_id)
        if event_stream is None:
            event_stream = create_event_stream(session_id)
        
        # 发送开始事件
        await event_stream.emit_simple(
            EventType.AGENT_START,
            content=f"开始处理查询: {query[:50]}...",
            data={"query": query, "context": context or {}}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Stream started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/{session_id}/stop")
async def stop_stream(
    session_id: str,
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    停止事件流
    
    Args:
        session_id: 会话ID
        
    Returns:
        停止结果
    """
    event_stream = get_event_stream(session_id)
    if event_stream:
        event_stream.stop()
        return {"success": True, "message": "Stream stopped"}
    return {"success": False, "message": "Stream not found"}


@router.get("/events/{session_id}/history")
async def get_event_history(
    session_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    获取事件历史
    
    Args:
        session_id: 会话ID
        event_type: 事件类型过滤
        limit: 返回数量限制
        
    Returns:
        事件历史列表
    """
    event_stream = get_event_stream(session_id)
    if event_stream is None:
        return {"events": []}
    
    # 解析事件类型
    evt_type = None
    if event_type:
        try:
            evt_type = EventType(event_type)
        except ValueError:
            pass
    
    # 获取历史
    events = event_stream.get_history(event_type=evt_type, limit=limit)
    
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events)
    }


@router.get("/events/{session_id}/metrics")
async def get_stream_metrics(
    session_id: str,
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    获取流指标
    
    Args:
        session_id: 会话ID
        
    Returns:
        流指标
    """
    event_stream = get_event_stream(session_id)
    if event_stream is None:
        return {"error": "Stream not found"}
    
    return event_stream.get_metrics()


@router.get("/streams")
async def list_streams(
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    列出所有活动流
    
    Returns:
        会话ID列表
    """
    manager = get_event_stream_manager()
    streams = manager.list_streams()
    
    return {
        "streams": streams,
        "count": len(streams)
    }


@router.get("/streams/metrics")
async def get_all_stream_metrics(
    auth: dict = Depends(StreamAuth.require_stream_access)
):
    """
    获取所有流的指标
    
    Returns:
        所有流的指标
    """
    manager = get_event_stream_manager()
    return manager.get_all_metrics()


# 集成到主API的便捷端点
@router.post("/chat/stream")
async def chat_with_stream(
    request: ChatRequest,
    auth: dict = Depends(lambda: {"allowed": True})
):
    """
    带事件流的聊天端点
    
    这是一个简化的版本，实际使用时可以在前端通过SSE连接
    获取实时事件
    
    Args:
        request: 聊天请求
        
    Returns:
        会话信息和流URL
    """
    import uuid
    
    # 生成会话ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # 创建事件流
    event_stream = create_event_stream(session_id)
    
    # 发送欢迎事件
    await event_stream.emit_simple(
        EventType.SYSTEM_INFO,
        content="会话已创建，等待处理...",
        data={"query": request.query}
    )
    
    return {
        "session_id": session_id,
        "stream_url": f"/stream/events/{session_id}",
        "status": "initiated"
    }
