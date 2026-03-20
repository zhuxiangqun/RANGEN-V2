"""
API Data Models
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from src.interfaces.agent import ExecutionStatus

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user query")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Final answer")
    steps: List[Any] = Field(default_factory=list, description="Reasoning steps trace")
    status: str = Field(..., description="Execution status")
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
