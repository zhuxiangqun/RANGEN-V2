"""
Smart Conversation API Routes
===========================

对话式智能助手接口 - 支持多轮对话
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.agents.smart_conversation_agent import get_smart_conversation_agent
from src.api.auth import require_read, require_write

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ConversationRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = None  # 支持传递历史记录


class ConversationResponse(BaseModel):
    response: str
    type: str  # text, confirmation, action
    session_id: str
    suggested_actions: Optional[List[str]] = None
    entity: Optional[Dict[str, str]] = None


@router.post("/chat", response_model=ConversationResponse)
async def chat(
    request: ConversationRequest,
    auth_data: dict = Depends(require_write)
):
    """
    对话接口 - 智能对话助手
    
    输入：
    - message: 用户消息
    - session_id: 会话ID（可选，用于多轮对话）
    - user_id: 用户ID（可选）
    
    输出：
    - response: AI回复
    - type: 回复类型 (text/confirmation/action)
    - session_id: 会话ID
    - suggested_actions: 建议的后续操作
    """
    try:
        agent = get_smart_conversation_agent()
        
        # 转换历史记录格式
        history_list = []
        if request.history:
            history_list = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        result = await agent.execute(
            inputs={
                "query": request.message,
                "session_id": request.session_id
            },
            context={
                "user_id": request.user_id,
                "auth": auth_data,
                "history": history_list
            }
        )
        
        if result.status.value == "completed":
            output = result.output or {}
            return ConversationResponse(
                response=output.get("response", "处理完成"),
                type=output.get("type", "text"),
                session_id=request.session_id or "new",
                suggested_actions=output.get("suggested_actions"),
                entity=output.get("entity")
            )
        else:
            raise HTTPException(status_code=500, detail=result.error or "处理失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    auth_data: dict = Depends(require_read)
):
    """
    获取对话历史
    """
    try:
        agent = get_smart_conversation_agent()
        ctx = agent.get_session_context(session_id)
        
        if not ctx:
            return {"history": [], "session_id": session_id}
        
        return {
            "history": ctx.history,
            "session_id": session_id,
            "created_entities": ctx.created_entities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    auth_data: dict = Depends(require_write)
):
    """
    清除对话历史
    """
    try:
        agent = get_smart_conversation_agent()
        agent.clear_session(session_id)
        
        return {"status": "success", "message": "对话历史已清除"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    auth_data: dict = Depends(require_read)
):
    """
    列出所有活动会话
    """
    try:
        agent = get_smart_conversation_agent()
        sessions = list(agent._conversation_sessions.keys())
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
