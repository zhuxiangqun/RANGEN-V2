"""
Skill Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field


class SkillScope(str, Enum):
    """Skill 作用域"""
    BUNDLED = "bundled"
    MANAGED = "managed"
    WORKSPACE = "workspace"


class SkillCategory(str, Enum):
    """Skill 类别"""
    CODE = "code"
    DOCUMENT = "document"
    ANALYSIS = "analysis"
    WRITING = "writing"
    REASONING = "reasoning"
    RETRIEVAL = "retrieval"
    TOOL = "tool"
    WORKFLOW = "workflow"
    GENERAL = "general"


class SkillMetadata(BaseModel):
    """Skill 元数据"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    category: SkillCategory = SkillCategory.GENERAL
    tags: List[str] = Field(default_factory=list)
    scope: SkillScope = SkillScope.BUNDLED
    dependencies: List[str] = Field(default_factory=list)


class ToolSchema(BaseModel):
    """工具 Schema"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    """Skill 执行结果"""
    success: bool
    output: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ISkill(ABC):
    """
    Skill 标准接口
    
    所有 Skill 必须实现此接口，确保：
    1. 统一的执行方法
    2. 标准化的元数据
    3. 工具注册机制
    4. Schema 定义能力
    """
    
    def __init__(self, metadata: SkillMetadata):
        """
        初始化 Skill
        
        Args:
            metadata: Skill 元数据
        """
        self._metadata = metadata
        self._tools: Dict[str, Any] = {}
        self._prompt_template: str = ""
    
    @property
    def name(self) -> str:
        """Skill 名称"""
        return self._metadata.name
    
    @property
    def version(self) -> str:
        """Skill 版本"""
        return self._metadata.version
    
    @property
    def description(self) -> str:
        """Skill 描述"""
        return self._metadata.description
    
    @property
    def category(self) -> SkillCategory:
        """Skill 类别"""
        return self._metadata.category
    
    @property
    def scope(self) -> SkillScope:
        """Skill 作用域"""
        return self._metadata.scope
    
    @property
    def tools(self) -> Dict[str, Any]:
        """Skill 拥有的工具"""
        return self._tools
    
    @property
    def prompt_template(self) -> str:
        """Prompt 模板"""
        return self._prompt_template
    
    @property
    def metadata(self) -> SkillMetadata:
        """Skill 元数据"""
        return self._metadata
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        """
        执行 Skill 任务
        
        Args:
            context: 执行上下文，包含输入数据
            
        Returns:
            SkillResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_schemas(self) -> List[ToolSchema]:
        """
        获取工具 Schema 列表
        
        Returns:
            List[ToolSchema]: 工具 Schema 列表
        """
        pass
    
    def register_tool(self, name: str, tool: Any) -> None:
        """
        注册工具
        
        Args:
            name: 工具名称
            tool: 工具实例
        """
        self._tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Any]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，不存在返回 None
        """
        return self._tools.get(name)
    
    def validate(self) -> bool:
        """
        验证 Skill 配置是否有效
        
        Returns:
            bool: 是否有效
        """
        if not self._metadata.name:
            return False
        if not self._metadata.version:
            return False
        return True
