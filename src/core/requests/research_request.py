#!/usr/bin/env python3
"""
研究请求 - 定义研究请求和响应的数据结构
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class RequestStatus(Enum):
    """请求状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestPriority(Enum):
    """请求优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ResearchRequest:
    """研究请求"""
    request_id: str
    query: str
    user_id: str
    priority: RequestPriority = RequestPriority.NORMAL
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timeout: float = float(os.getenv("DEFAULT_TIMEOUT", "30.0"))
    
    def __post_init__(self):
        """后初始化处理"""
        if not self.request_id:
            self.request_id = f"req_{int(time.time())}"
        
        if not self.created_at:
            self.created_at = time.time()
    
    def is_valid(self) -> bool:
        """验证请求是否有效"""
        try:
            # 基本字段验证
            if not self.request_id or not isinstance(self.request_id, str):
                return False
            
            if not self.query or not isinstance(self.query, str) or not self.query.strip():
                return False
            
            if not self.user_id or not isinstance(self.user_id, str):
                return False
            
            # 优先级验证
            if not isinstance(self.priority, RequestPriority):
                return False
            
            # 上下文验证
            if not isinstance(self.context, dict):
                return False
            
            # 元数据验证
            if not isinstance(self.metadata, dict):
                return False
            
            # 超时验证
            if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
                return False
            
            # 创建时间验证
            if not isinstance(self.created_at, (int, float)) or self.created_at <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "query": self.query,
            "user_id": self.user_id,
            "priority": self.priority.value,
            "context": self.context,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchRequest':
        """从字典创建"""
        return cls(
            request_id=data.get("request_id", ""),
            query=data.get("query", ""),
            user_id=data.get("user_id", ""),
            priority=RequestPriority(data.get("priority", "normal")),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            timeout=data.get("timeout", float(os.getenv("DEFAULT_TIMEOUT", "30.0")))
        )


@dataclass
class ResearchResponse:
    """研究响应"""
    request_id: str
    result: Optional[Any] = None
    confidence: float = 0.0
    status: RequestStatus = RequestStatus.PENDING
    error_message: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """后初始化处理"""
        if not self.created_at:
            self.created_at = time.time()
    
    def is_successful(self) -> bool:
        """检查是否成功"""
        return (
            self.result is not None and 
            0.0 <= self.confidence <= 1.0 and
            self.status == RequestStatus.COMPLETED
        )
    
    def is_valid(self) -> bool:
        """验证响应是否有效"""
        return (
            bool(self.request_id) and
            isinstance(self.confidence, (int, float)) and
            isinstance(self.status, RequestStatus) and
            isinstance(self.metadata, dict) and
            self.processing_time >= 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "result": self.result,
            "confidence": self.confidence,
            "status": self.status.value,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchResponse':
        """从字典创建"""
        return cls(
            request_id=data.get("request_id", ""),
            result=data.get("result"),
            confidence=data.get("confidence", 0.0),
            status=RequestStatus(data.get("status", "pending")),
            error_message=data.get("error_message"),
            processing_time=data.get("processing_time", 0.0),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time())
        )


@dataclass
class ResearchSession:
    """研究会话"""
    session_id: str
    user_id: str
    requests: List[ResearchRequest] = field(default_factory=list)
    responses: List[ResearchResponse] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """后初始化处理"""
        if not self.created_at:
            self.created_at = time.time()
        if not self.last_activity:
            self.last_activity = time.time()
    
    def add_request(self, request: ResearchRequest) -> bool:
        """添加请求"""
        try:
            if request.is_valid():
                self.requests.append(request)
                self.last_activity = time.time()
                return True
            return False
        except Exception:
            return False
    
    def add_response(self, response: ResearchResponse) -> bool:
        """添加响应"""
        try:
            if response.is_valid():
                self.responses.append(response)
                self.last_activity = time.time()
                return True
            return False
        except Exception:
            return False
    
    def get_request(self, request_id: str) -> Optional[ResearchRequest]:
        """获取请求"""
        for request in self.requests:
            if request.request_id == request_id:
                return request
        return None
    
    def get_response(self, request_id: str) -> Optional[ResearchResponse]:
        """获取响应"""
        for response in self.responses:
            if response.request_id == request_id:
                return response
        return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计"""
        total_requests = len(self.requests)
        completed_requests = len([r for r in self.responses if r.status == RequestStatus.COMPLETED])
        failed_requests = len([r for r in self.responses if r.status == RequestStatus.FAILED])
        
        avg_confidence = 0.0
        if self.responses:
            avg_confidence = sum(r.confidence for r in self.responses) / len(self.responses)
        
        avg_processing_time = 0.0
        if self.responses:
            avg_processing_time = sum(r.processing_time for r in self.responses) / len(self.responses)
        
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "success_rate": completed_requests / total_requests if total_requests > 0 else 0.0,
            "average_confidence": avg_confidence,
            "average_processing_time": avg_processing_time,
            "session_duration": time.time() - self.created_at,
            "last_activity": self.last_activity
        }
    
    def is_active(self, max_idle_time: float = 3600.0) -> bool:
        """检查会话是否活跃"""
        return time.time() - self.last_activity < max_idle_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "requests": [req.to_dict() for req in self.requests],
            "responses": [resp.to_dict() for resp in self.responses],
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchSession':
        """从字典创建"""
        session = cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            created_at=data.get("created_at", time.time()),
            last_activity=data.get("last_activity", time.time()),
            metadata=data.get("metadata", {})
        )
        
        # 重建请求列表
        for req_data in data.get("requests", []):
            request = ResearchRequest.from_dict(req_data)
            session.requests.append(request)
        
        # 重建响应列表
        for resp_data in data.get("responses", []):
            response = ResearchResponse.from_dict(resp_data)
            session.responses.append(response)
        
        return session


class RequestValidator:
    """请求验证器"""
    
    @staticmethod
    def validate_request(request: ResearchRequest) -> List[str]:
        """验证请求"""
        errors = []
        
        if not request.request_id:
            errors.append("请求ID不能为空")
        
        if not request.query or len(request.query.strip()) == 0:
            errors.append("查询内容不能为空")
        
        if len(request.query) > int(os.getenv("MAX_QUERY_LENGTH", "1000")):
            errors.append("查询内容过长")
        
        if not request.user_id:
            errors.append("用户ID不能为空")
        
        if request.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        if request.timeout > float(os.getenv("MAX_TIMEOUT", "300.0")):
            errors.append("超时时间过长")
        
        return errors
    
    @staticmethod
    def validate_response(response: ResearchResponse) -> List[str]:
        """验证响应"""
        errors = []
        
        if not response.request_id:
            errors.append("请求ID不能为空")
        
        if not isinstance(response.confidence, (int, float)):
            errors.append("置信度必须是数字")
        elif not (0.0 <= response.confidence <= 1.0):
            errors.append("置信度必须在0-1之间")
        
        if response.processing_time < 0:
            errors.append("处理时间不能为负数")
        
        return errors


def create_research_request(query: str, user_id: str, 
                          priority: RequestPriority = RequestPriority.NORMAL,
                          context: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> ResearchRequest:
    """创建研究请求"""
    return ResearchRequest(
        request_id=f"req_{int(time.time())}",
        query=query,
        user_id=user_id,
        priority=priority,
        context=context or {},
        metadata=metadata or {}
    )


def create_research_response(request_id: str, result: Any = None,
                           confidence: float = 0.0,
                           status: RequestStatus = RequestStatus.COMPLETED,
                           error_message: Optional[str] = None,
                           processing_time: float = 0.0) -> ResearchResponse:
    """创建研究响应"""
    return ResearchResponse(
        request_id=request_id,
        result=result,
        confidence=confidence,
        status=status,
        error_message=error_message,
        processing_time=processing_time
    )


if __name__ == "__main__":
    # 测试研究请求和响应
    request = create_research_request(
        query="测试查询",
        user_id="test_user",
        priority=RequestPriority.HIGH,
        context={"source": "test"},
        metadata={"test": True}
    )
    
    print(f"请求: {request.to_dict()}")
    print(f"请求有效: {request.is_valid()}")
    
    response = create_research_response(
        request_id=request.request_id,
        result="测试结果",
        confidence=0.9,
        processing_time=1.5
    )
    
    print(f"响应: {response.to_dict()}")
    print(f"响应成功: {response.is_successful()}")
    
    # 测试会话
    session = ResearchSession(
        session_id="test_session",
        user_id="test_user"
    )
    
    session.add_request(request)
    session.add_response(response)
    
    print(f"会话统计: {session.get_session_stats()}")