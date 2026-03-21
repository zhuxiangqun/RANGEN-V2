#!/usr/bin/env python3
"""
测试结果数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class TestResult:
    """沙盒测试结果"""
    test_id: str
    skill_name: str
    status: TestStatus
    execution_time: float
    output: Optional[str] = None
    error: Optional[str] = None
    error_trace: Optional[str] = None
    retry_count: int = 0
    suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_success(self) -> bool:
        return self.status == TestStatus.PASSED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "skill_name": self.skill_name,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "output": self.output,
            "error": self.error,
            "retry_count": self.retry_count,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }
