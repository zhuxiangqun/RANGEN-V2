#!/usr/bin/env python3
"""
Hands能力包基础定义
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class HandCategory(Enum):
    """Hand能力类别"""
    FILE_OPERATION = "file_operation"  # 文件操作
    CODE_MODIFICATION = "code_modification"  # 代码修改
    API_INTEGRATION = "api_integration"  # API集成
    DATA_PROCESSING = "data_processing"  # 数据处理
    SYSTEM_COMMAND = "system_command"  # 系统命令
    TEST_EXECUTION = "test_execution"  # 测试执行
    MONITORING = "monitoring"  # 监控
    DEPLOYMENT = "deployment"  # 部署
    VALIDATION = "validation"  # 验证


class HandSafetyLevel(Enum):
    """Hand安全级别"""
    SAFE = "safe"  # 安全操作，可自动执行
    MODERATE = "moderate"  # 中等风险，需要简单确认
    RISKY = "risky"  # 高风险，需要详细审查
    DANGEROUS = "dangerous"  # 危险操作，需要创业者确认


@dataclass
class HandCapability:
    """Hand能力定义"""
    name: str  # 能力名称
    description: str  # 能力描述
    category: HandCategory  # 能力类别
    safety_level: HandSafetyLevel  # 安全级别
    version: str = "1.0.0"  # 版本
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数定义
    dependencies: List[str] = field(default_factory=list)  # 依赖
    examples: List[Dict[str, Any]] = field(default_factory=list)  # 使用示例


@dataclass
class HandExecutionResult:
    """Hand执行结果"""
    hand_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0  # 执行时间（秒）
    safety_check_passed: bool = True
    validation_results: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseHand(ABC):
    """Hand能力包基类"""
    
    def __init__(self, name: str, description: str, category: HandCategory, 
                 safety_level: HandSafetyLevel = HandSafetyLevel.SAFE):
        self.name = name
        self.description = description
        self.category = category
        self.safety_level = safety_level
        self.logger = logging.getLogger(f"hand.{name}")
        self.version = "1.0.0"
        
        # 能力定义
        self.capability = HandCapability(
            name=name,
            description=description,
            category=category,
            safety_level=safety_level,
            version=self.version
        )
        
        self.logger.info(f"初始化Hand: {name} ({category.value})")
    
    @abstractmethod
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行Hand能力"""
        pass
    
    @abstractmethod
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        pass
    
    def get_capability(self) -> HandCapability:
        """获取能力定义"""
        return self.capability
    
    def _measure_execution_time(self, func: Callable) -> Callable:
        """测量执行时间的装饰器"""
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                if hasattr(result, 'execution_time'):
                    result.execution_time = execution_time
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                self.logger.error(f"执行失败 (耗时: {execution_time:.2f}s): {e}")
                raise
        
        return wrapper
    
    async def safety_check(self, **kwargs) -> bool:
        """安全检查"""
        # 根据安全级别实现不同的检查逻辑
        if self.safety_level == HandSafetyLevel.SAFE:
            return True
        elif self.safety_level == HandSafetyLevel.MODERATE:
            # 检查关键参数
            return self._check_moderate_safety(kwargs)
        elif self.safety_level == HandSafetyLevel.RISKY:
            # 需要更严格的检查
            return self._check_risky_safety(kwargs)
        else:  # DANGEROUS
            # 危险操作默认返回False，需要外部确认
            return False
    
    def _check_moderate_safety(self, kwargs: Dict[str, Any]) -> bool:
        """检查中等安全级别的操作"""
        # 默认实现：检查是否有破坏性参数
        dangerous_keys = ["delete", "remove", "drop", "truncate", "format"]
        for key, value in kwargs.items():
            if any(dangerous in str(key).lower() for dangerous in dangerous_keys):
                self.logger.warning(f"检测到潜在危险参数: {key}={value}")
                return False
        return True
    
    def _check_risky_safety(self, kwargs: Dict[str, Any]) -> bool:
        """检查高风险级别的操作"""
        # 更严格的检查
        if not kwargs:
            return True
        
        # 检查文件路径操作
        if "path" in kwargs or "file" in kwargs:
            path_value = kwargs.get("path") or kwargs.get("file")
            if path_value:
                path_str = str(path_value)
                # 避免操作关键系统文件
                system_paths = ["/etc/", "/bin/", "/usr/", "/var/", "/root/", "/boot/"]
                if any(path_str.startswith(sys_path) for sys_path in system_paths):
                    self.logger.error(f"禁止操作系统路径: {path_str}")
                    return False
        
        return self._check_moderate_safety(kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.category.value}) - {self.description}"