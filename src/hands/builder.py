#!/usr/bin/env python3
"""
Hands动态构建器 - 从原子工具动态构建完整Hand
"""
import logging
from typing import Dict, Any, Optional, List, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class HandsBuilder:
    """Hands动态构建器
    
    从原子工具动态构建完整Hand的能力包装器
    """
    
    def __init__(self):
        self._hand_factories: Dict[str, Any] = {}  # type: ignore[misc]
        self._registered_hands: Dict[str, Any] = {}
        self._initialize_default_factories()
    
    def _initialize_default_factories(self):
        """初始化默认工厂"""
        from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel
        from src.tools.atomic import AtomicToolType, AtomicCodeRunner, AtomicFileTool, AtomicWebTool, AtomicUserTool
        
        # code_run Hand
        self._hand_factories[AtomicToolType.CODE_RUN.value] = self._create_code_hand
        
        # file_* Hands
        for tool_type in [AtomicToolType.FILE_READ, AtomicToolType.FILE_WRITE, AtomicToolType.FILE_PATCH]:
            self._hand_factories[tool_type.value] = self._create_file_hand
        
        # web_* Hands
        for tool_type in [AtomicToolType.WEB_SCAN, AtomicToolType.WEB_EXECUTE_JS]:
            self._hand_factories[tool_type.value] = self._create_web_hand
        
        # ask_user Hand
        self._hand_factories[AtomicToolType.ASK_USER.value] = self._create_user_hand
    
    def _create_code_hand(self, name: str, description: str, **kwargs) -> BaseHand:  # type: ignore[misc]
        """创建代码执行Hand"""
        from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel
        from src.tools.atomic import AtomicCodeRunner
        
        class CodeHand(BaseHand):
            def __init__(self):
                super().__init__(
                    name=name,
                    description=description,
                    category=HandCategory.CODE_MODIFICATION,
                    safety_level=HandSafetyLevel.MODERATE
                )
                self.runner = AtomicCodeRunner()
            
            async def execute(self, **kwargs) -> HandExecutionResult:
                code = kwargs.get("code", "")
                language = kwargs.get("language", "python")
                result = self.runner.execute(code, language)
                return HandExecutionResult(
                    hand_name=self.name,
                    success=result.success,
                    output=result.output,
                    error=result.error,
                    execution_time=result.execution_time
                )
            
            def validate_parameters(self, **kwargs) -> bool:
                return "code" in kwargs
        
        return CodeHand()
    
    def _create_file_hand(self, name: str, description: str, **kwargs) -> BaseHand:  # type: ignore[misc]
        """创建文件操作Hand"""
        from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel
        from src.tools.atomic import AtomicFileTool
        
        class FileHand(BaseHand):
            def __init__(self):
                super().__init__(
                    name=name,
                    description=description,
                    category=HandCategory.FILE_OPERATION,
                    safety_level=HandSafetyLevel.RISKY
                )
                self.file_tool = AtomicFileTool()
            
            async def execute(self, **kwargs) -> HandExecutionResult:
                action = kwargs.get("action", "read")
                path = kwargs.get("path", "")
                content = kwargs.get("content", "")
                
                if action == "read":
                    result = self.file_tool.read(path)
                elif action == "write":
                    result = self.file_tool.write(path, content)
                elif action == "patch":
                    result = self.file_tool.patch(path, kwargs.get("patch", ""), replace=kwargs.get("replace", True))  # type: ignore
                else:
                    result = self.file_tool.read(path)
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=result.success if hasattr(result, 'success') else False,  # type: ignore
                    output=result.output if hasattr(result, 'output') else str(result),  # type: ignore
                    error=result.error if hasattr(result, 'error') else ""  # type: ignore
                )
            
            def validate_parameters(self, **kwargs) -> bool:
                return "path" in kwargs
        
        return FileHand()
    
    def _create_web_hand(self, name: str, description: str, **kwargs) -> BaseHand:  # type: ignore[misc]
        """创建Web操作Hand"""
        from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel
        from src.tools.atomic import AtomicWebTool
        
        class WebHand(BaseHand):
            def __init__(self):
                super().__init__(
                    name=name,
                    description=description,
                    category=HandCategory.API_INTEGRATION,
                    safety_level=HandSafetyLevel.MODERATE
                )
                self.web_tool = AtomicWebTool()
            
            async def execute(self, **kwargs) -> HandExecutionResult:
                url = kwargs.get("url", "")
                action = kwargs.get("action", "scan")
                
                if action == "scan":
                    result = await self.web_tool.scan(url) if hasattr(self.web_tool.scan, '__await__') else self.web_tool.scan(url)
                elif action == "execute_js":
                    result = await self.web_tool.execute_js(url, kwargs.get("script", "")) if hasattr(self.web_tool.execute_js, '__await__') else self.web_tool.execute_js(url, kwargs.get("script", ""))
                else:
                    result = await self.web_tool.scan(url) if hasattr(self.web_tool.scan, '__await__') else self.web_tool.scan(url)
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=getattr(result, 'success', False),
                    output=getattr(result, 'output', str(result)),
                    error=getattr(result, 'error', "")
                )
            
            def validate_parameters(self, **kwargs) -> bool:
                return "url" in kwargs
        
        return WebHand()
    
    def _create_user_hand(self, name: str, description: str, **kwargs) -> BaseHand:  # type: ignore[misc]
        """创建用户交互Hand"""
        from src.hands.base import BaseHand, HandExecutionResult, HandCategory, HandSafetyLevel
        from src.tools.atomic import AtomicUserTool
        
        class UserHand(BaseHand):
            def __init__(self):
                super().__init__(
                    name=name,
                    description=description,
                    category=HandCategory.SYSTEM_COMMAND,
                    safety_level=HandSafetyLevel.SAFE
                )
                self.user_tool = AtomicUserTool()
            
            async def execute(self, **kwargs) -> HandExecutionResult:
                question = kwargs.get("question", "")
                options = kwargs.get("options", [])
                result = self.user_tool.ask(question, options)
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=result.success,
                    output=result.output,
                    error=result.error
                )
            
            def validate_parameters(self, **kwargs) -> bool:
                return "question" in kwargs
        
        return UserHand()
    
    def build_hand(self, tool_type: str, name: Optional[str] = None, description: Optional[str] = None, **kwargs):
        """从原子工具类型构建Hand
        
        Args:
            tool_type: 原子工具类型 (code_run, file_read, etc.)
            name: Hand名称
            description: Hand描述
            **kwargs: 其他参数
            
        Returns:
            构建的Hand实例
        """
        factory = self._hand_factories.get(tool_type)
        if not factory:
            raise ValueError(f"Unknown tool type: {tool_type}")
        
        default_names = {
            "code_run": "CodeRunnerHand",
            "file_read": "FileReaderHand",
            "file_write": "FileWriterHand",
            "file_patch": "FilePatcherHand",
            "web_scan": "WebScannerHand",
            "web_execute_js": "WebJSExecutorHand",
            "ask_user": "UserAskerHand"
        }
        
        default_descriptions = {
            "code_run": "执行Python/Bash代码",
            "file_read": "读取文件内容",
            "file_write": "写入文件内容",
            "file_patch": "修补文件内容",
            "web_scan": "扫描网页内容",
            "web_execute_js": "执行网页JavaScript",
            "ask_user": "向用户提问"
        }
        
        hand_name = name or default_names.get(tool_type, f"{tool_type}Hand")
        hand_desc = description or default_descriptions.get(tool_type, f"{tool_type} handler")
        
        hand = factory(hand_name, hand_desc, **kwargs)
        self._registered_hands[hand_name] = hand
        
        logger.info(f"✅ Built hand: {hand_name} from {tool_type}")
        return hand
    
    def get_hand(self, name: str):
        """获取已注册的Hand"""
        return self._registered_hands.get(name)
    
    def list_hands(self) -> List[str]:
        """列出所有已注册的Hand"""
        return list(self._registered_hands.keys())


# 全局实例
_hands_builder: Optional[HandsBuilder] = None


def get_hands_builder() -> HandsBuilder:
    """获取HandsBuilder单例"""
    global _hands_builder
    if _hands_builder is None:
        _hands_builder = HandsBuilder()
    return _hands_builder
