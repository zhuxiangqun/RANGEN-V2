#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分层工具系统 - 基于Agentic Coding架构模式

设计理念：
1. 四层工具架构：
   ├── 核心工具层 (Core Tools)：基础文件操作、系统命令、DeepSeek专用工具
   ├── 编程工具层 (Programming Tools)：代码分析、编辑、Git操作、测试生成
   ├── 外部集成层 (External Integration)：MCP协议、Web搜索、API调用、数据源连接
   └── 自定义工具层 (Custom Tools)：用户扩展、插件系统、动态工具注册

2. 工具发现与注册：自动扫描和注册可用工具
3. 权限控制：按工具层和类别控制访问权限
4. 生命周期管理：工具加载、初始化、清理
5. 性能监控：工具调用统计和性能分析

参考架构：OpenCode的四层工具系统
"""

import asyncio
import time
import logging
import inspect
from typing import Dict, Any, List, Optional, Type, Set, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
import importlib
import pkgutil
import sys
from pathlib import Path

from src.interfaces.tool import ITool, ToolConfig, ToolCategory, ToolResult
from src.agents.tools.base_tool import BaseTool
from src.services.tool_registry import get_tool_registry
from src.core.rangen_state import get_global_state_manager, StateUpdate, StateUpdateStrategy

logger = logging.getLogger(__name__)


class ToolLayer(Enum):
    """工具层级"""
    CORE = "core"                # 核心工具层：基础系统工具
    PROGRAMMING = "programming"  # 编程工具层：代码相关工具
    EXTERNAL = "external"        # 外部集成层：MCP、API等
    CUSTOM = "custom"            # 自定义工具层：用户扩展


class ToolPermission(Enum):
    """工具权限级别"""
    PUBLIC = "public"           # 公开访问，无需特殊权限
    RESTRICTED = "restricted"   # 受限访问，需要授权
    ADMIN = "admin"             # 管理员权限
    SYSTEM = "system"           # 系统级权限（仅内部使用）


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str                    # 工具名称
    description: str             # 工具描述
    layer: ToolLayer             # 所属层级
    category: ToolCategory       # 工具类别
    permission: ToolPermission   # 权限级别
    version: str = "1.0.0"       # 版本号
    dependencies: List[str] = field(default_factory=list)  # 依赖项
    tags: List[str] = field(default_factory=list)          # 标签
    requires_context: bool = False  # 是否需要上下文
    is_deprecated: bool = False    # 是否已废弃
    replacement_tool: Optional[str] = None  # 替代工具（如果废弃）
    
    @property
    def is_available(self) -> bool:
        """工具是否可用"""
        return not self.is_deprecated
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "layer": self.layer.value,
            "category": self.category.value,
            "permission": self.permission.value,
            "version": self.version,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "requires_context": self.requires_context,
            "is_deprecated": self.is_deprecated,
            "replacement_tool": self.replacement_tool,
            "is_available": self.is_available
        }


@dataclass
class ToolExecutionStats:
    """工具执行统计"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_call_time: Optional[float] = None
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def avg_time(self) -> float:
        """平均执行时间"""
        if self.total_calls == 0:
            return 0.0
        return self.total_execution_time / self.total_calls
    
    def record_call(self, success: bool, execution_time: float, error: Optional[str] = None):
        """记录调用"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            self.last_error = error
        
        self.total_execution_time += execution_time
        self.avg_execution_time = self.avg_time
        self.last_call_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": self.avg_execution_time,
            "last_call_time": self.last_call_time,
            "last_error": self.last_error
        }


class HierarchicalToolSystem:
    """分层工具系统管理器"""
    
    def __init__(self, enable_auto_discovery: bool = True):
        """
        初始化分层工具系统
        
        Args:
            enable_auto_discovery: 是否启用自动工具发现
        """
        self.enable_auto_discovery = enable_auto_discovery
        
        # 工具注册表
        self._tool_registry = get_tool_registry()
        
        # 状态管理器
        self._state_manager = get_global_state_manager()
        
        # 工具元数据映射
        self._tool_metadata: Dict[str, ToolMetadata] = {}
        
        # 工具执行统计
        self._tool_stats: Dict[str, ToolExecutionStats] = {}
        
        # 工具实例存储
        self._tool_instances: Dict[str, Any] = {}
        
        # 按层级组织的工具
        self._tools_by_layer: Dict[ToolLayer, List[str]] = {
            layer: [] for layer in ToolLayer
        }
        
        # 按类别组织的工具
        self._tools_by_category: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        
        # 工具权限映射
        self._tool_permissions: Dict[str, ToolPermission] = {}
        
        # 已加载的工具模块
        self._loaded_modules: Set[str] = set()
        
        # 初始化核心工具层
        self._initialize_core_tools()
        
        logger.info(f"分层工具系统初始化完成，启用自动发现: {enable_auto_discovery}")
    
    def _initialize_core_tools(self):
        """初始化核心工具层"""
        # 这里定义核心工具的基本元数据
        # 实际工具会在自动发现或手动注册时添加
        
        # 预定义一些核心工具类别
        core_tools_categories = {
            "file_operations": ToolCategory.UTILITY,
            "system_commands": ToolCategory.UTILITY,
            "deepseek_tools": ToolCategory.COMPUTE,
            "context_management": ToolCategory.UTILITY,
        }
        
        logger.info(f"核心工具类别初始化: {list(core_tools_categories.keys())}")
    
    async def discover_and_register_tools(self, module_paths: Optional[List[str]] = None):
        """
        发现并注册工具
        
        Args:
            module_paths: 要扫描的模块路径列表，如果为None则扫描默认路径
        """
        if not self.enable_auto_discovery:
            logger.info("自动工具发现已禁用")
            return
        
        if module_paths is None:
            # 默认扫描路径
            module_paths = [
                "src.agents.tools",
                "src.gateway.tools",
                "src.core.context_engineering",
            ]
        
        discovered_count = 0
        
        for module_path in module_paths:
            try:
                count = await self._discover_tools_in_module(module_path)
                discovered_count += count
                logger.info(f"在模块 {module_path} 中发现 {count} 个工具")
            except Exception as e:
                logger.warning(f"扫描模块 {module_path} 失败: {e}")
        
        # 更新状态管理器
        self._update_state_with_tool_info()
        
        logger.info(f"工具发现完成，共发现 {discovered_count} 个工具")
        return discovered_count
    
    async def _discover_tools_in_module(self, module_path: str) -> int:
        """在指定模块中发现工具"""
        discovered_count = 0
        
        try:
            module = importlib.import_module(module_path)
            
            # 遍历模块中的所有类
            for name, obj in inspect.getmembers(module):
                if self._is_tool_class(obj):
                    try:
                        # 创建工具实例
                        tool_instance = await self._create_tool_instance(obj)
                        if tool_instance:
                            # 注册工具
                            metadata = self._create_tool_metadata(tool_instance, module_path)
                            await self.register_tool(tool_instance, metadata)
                            discovered_count += 1
                    except Exception as e:
                        logger.warning(f"创建工具实例 {name} 失败: {e}")
            
            # 递归扫描子模块
            if hasattr(module, "__path__"):
                for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
                    if is_pkg:
                        submodule_path = f"{module_path}.{submodule_name}"
                        count = await self._discover_tools_in_module(submodule_path)
                        discovered_count += count
        
        except ImportError as e:
            logger.warning(f"无法导入模块 {module_path}: {e}")
        
        return discovered_count
    
    def _is_tool_class(self, obj) -> bool:
        """判断对象是否为工具类"""
        if not inspect.isclass(obj):
            return False
        
        # 检查是否继承自 BaseTool 或 ITool
        try:
            if issubclass(obj, BaseTool) and obj != BaseTool:
                return True
        except:
            pass
        
        try:
            if issubclass(obj, ITool) and obj != ITool:
                return True
        except:
            pass
        
        return False
    
    async def _create_tool_instance(self, tool_class: Type) -> Optional[Any]:
        """创建工具实例"""
        try:
            # 检查是否有合适的初始化参数
            sig = inspect.signature(tool_class.__init__)
            params = sig.parameters
            
            # 尝试不同的初始化方式
            if len(params) <= 1:  # 只有 self 参数
                instance = tool_class()
            elif "tool_name" in params:
                # 对于 BaseTool 派生类
                instance = tool_class(tool_name=tool_class.__name__.lower())
            elif "config" in params:
                # 对于 ITool 派生类
                config = ToolConfig(
                    name=tool_class.__name__.lower(),
                    description=f"Auto-discovered tool: {tool_class.__name__}",
                    category=ToolCategory.UTILITY
                )
                instance = tool_class(config)
            else:
                logger.warning(f"无法确定工具类 {tool_class.__name__} 的初始化参数")
                return None
            
            return instance
        except Exception as e:
            logger.warning(f"创建工具实例 {tool_class.__name__} 失败: {e}")
            return None
    
    def _create_tool_metadata(self, tool_instance: Any, source_module: str) -> ToolMetadata:
        """根据工具实例创建元数据"""
        tool_name = ""
        description = ""
        
        # 提取工具信息
        if hasattr(tool_instance, 'tool_name'):
            tool_name = tool_instance.tool_name
        elif hasattr(tool_instance, 'config') and hasattr(tool_instance.config, 'name'):
            tool_name = tool_instance.config.name
        
        if hasattr(tool_instance, 'description'):
            description = tool_instance.description
        elif hasattr(tool_instance, 'config') and hasattr(tool_instance.config, 'description'):
            description = tool_instance.config.description
        
        # 确定工具层级
        layer = self._determine_tool_layer(tool_name, description, source_module)
        
        # 确定工具类别
        category = self._determine_tool_category(tool_name, description)
        
        # 确定权限级别
        permission = self._determine_tool_permission(layer, category)
        
        return ToolMetadata(
            name=tool_name,
            description=description,
            layer=layer,
            category=category,
            permission=permission,
            version="1.0.0",
            dependencies=[],
            tags=self._extract_tool_tags(tool_name, description),
            requires_context=self._check_requires_context(tool_instance),
            source_module=source_module
        )
    
    def _determine_tool_layer(self, tool_name: str, description: str, source_module: str) -> ToolLayer:
        """确定工具层级"""
        tool_name_lower = tool_name.lower()
        description_lower = description.lower()
        
        # 核心工具层
        core_keywords = ["file", "read", "write", "edit", "bash", "system", "deepseek", "cost", "budget"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in core_keywords):
            return ToolLayer.CORE
        
        # 编程工具层
        programming_keywords = ["code", "git", "test", "refactor", "analyze", "syntax", "debug"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in programming_keywords):
            return ToolLayer.PROGRAMMING
        
        # 外部集成层
        external_keywords = ["mcp", "web", "search", "api", "browser", "http", "rag", "retrieval"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in external_keywords):
            return ToolLayer.EXTERNAL
        
        # 默认：自定义工具层
        return ToolLayer.CUSTOM
    
    def _determine_tool_category(self, tool_name: str, description: str) -> ToolCategory:
        """确定工具类别"""
        tool_name_lower = tool_name.lower()
        description_lower = description.lower()
        
        # 检索类工具
        retrieval_keywords = ["search", "retrieval", "rag", "find", "lookup"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in retrieval_keywords):
            return ToolCategory.RETRIEVAL
        
        # 计算类工具
        compute_keywords = ["calculator", "compute", "calculate", "math", "reason", "analyze"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in compute_keywords):
            return ToolCategory.COMPUTE
        
        # API类工具
        api_keywords = ["api", "http", "rest", "graphql", "webhook"]
        if any(keyword in tool_name_lower or keyword in description_lower for keyword in api_keywords):
            return ToolCategory.API
        
        # 默认：工具类
        return ToolCategory.UTILITY
    
    def _determine_tool_permission(self, layer: ToolLayer, category: ToolCategory) -> ToolPermission:
        """确定工具权限级别"""
        # 核心工具层和系统级工具需要更高权限
        if layer == ToolLayer.CORE:
            if category in [ToolCategory.COMPUTE, ToolCategory.API]:
                return ToolPermission.RESTRICTED
            return ToolPermission.PUBLIC
        
        # 编程工具需要一定权限
        elif layer == ToolLayer.PROGRAMMING:
            return ToolPermission.RESTRICTED
        
        # 外部集成工具通常需要授权
        elif layer == ToolLayer.EXTERNAL:
            return ToolPermission.RESTRICTED
        
        # 自定义工具默认公开
        else:
            return ToolPermission.PUBLIC
    
    def _extract_tool_tags(self, tool_name: str, description: str) -> List[str]:
        """提取工具标签"""
        tags = []
        
        # 基于名称的标签
        tags.append(tool_name)
        
        # 基于描述的简单关键词提取
        keywords = ["file", "search", "code", "api", "web", "analysis", "debug", "test"]
        for keyword in keywords:
            if keyword in description.lower():
                tags.append(keyword)
        
        return list(set(tags))  # 去重
    
    def _check_requires_context(self, tool_instance: Any) -> bool:
        """检查工具是否需要上下文"""
        # 检查 call 或 execute 方法的参数
        call_method = None
        if hasattr(tool_instance, 'call'):
            call_method = tool_instance.call
        elif hasattr(tool_instance, 'execute'):
            call_method = tool_instance.execute
        
        if call_method:
            try:
                sig = inspect.signature(call_method)
                params = sig.parameters
                
                # 检查是否包含 context 或类似参数
                context_params = ["context", "session", "state", "request"]
                return any(param in params for param in context_params)
            except:
                pass
        
        return False
    
    async def register_tool(self, tool_instance: Any, metadata: ToolMetadata):
        """
        注册工具
        
        Args:
            tool_instance: 工具实例
            metadata: 工具元数据
        """
        try:
            # 注册到工具注册表（如果支持）
            try:
                if hasattr(self._tool_registry, 'register_tool'):
                    self._tool_registry.register_tool(tool_instance)
                elif hasattr(self._tool_registry, 'register'):
                    self._tool_registry.register(tool_instance)
                elif hasattr(self._tool_registry, 'add_tool'):
                    self._tool_registry.add_tool(tool_instance)
                else:
                    logger.warning(f"工具注册表不支持注册方法，跳过注册: {metadata.name}")
            except Exception as reg_error:
                logger.warning(f"工具注册表注册失败，继续处理元数据: {reg_error}")
            
            # 存储元数据
            self._tool_metadata[metadata.name] = metadata
            
            # 存储工具实例
            self._tool_instances[metadata.name] = tool_instance
            
            # 按层级组织
            self._tools_by_layer[metadata.layer].append(metadata.name)
            
            # 按类别组织
            self._tools_by_category[metadata.category].append(metadata.name)
            
            # 存储权限
            self._tool_permissions[metadata.name] = metadata.permission
            
            # 初始化统计
            if metadata.name not in self._tool_stats:
                self._tool_stats[metadata.name] = ToolExecutionStats()
            
            logger.info(f"注册工具: {metadata.name} (层级: {metadata.layer.value}, 类别: {metadata.category.value}, 权限: {metadata.permission.value})")
            
            # 更新状态
            self._update_state_with_tool_info()
            
        except Exception as e:
            logger.error(f"注册工具 {metadata.name} 失败: {e}")
            raise
    
    async def execute_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None, 
                          user_context: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数（兼容旧版本）
            user_context: 用户上下文（用于权限检查）
            **kwargs: 工具参数（如果params为None，则使用kwargs）
            
        Returns:
            工具执行结果
        """
        start_time = time.time()
        
        try:
            # 处理参数：优先使用params，然后是kwargs
            tool_params = {}
            if params is not None:
                tool_params.update(params)
            tool_params.update(kwargs)
            
            # 存储用户上下文以供权限检查使用
            if user_context is not None:
                self._last_user_context = user_context
            
            # 检查工具是否存在
            if tool_name not in self._tool_metadata:
                error_msg = f"工具不存在: {tool_name}"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    output=None,
                    execution_time=0.0,
                    error=error_msg
                )
            
            # 检查权限（使用用户上下文增强检查）
            metadata = self._tool_metadata[tool_name]
            if not self._check_permission(metadata.permission, user_context):
                error_msg = f"权限不足，无法执行工具: {tool_name}"
                logger.warning(error_msg)
                return ToolResult(
                    success=False,
                    output=None,
                    execution_time=0.0,
                    error=error_msg
                )
            
            # 获取工具实例（首先从本地存储获取）
            tool = self._tool_instances.get(tool_name)
            if tool is None:
                # 尝试从工具注册表获取（如果可用）
                if hasattr(self._tool_registry, 'get_tool'):
                    tool = self._tool_registry.get_tool(tool_name)
                elif hasattr(self._tool_registry, 'get'):
                    tool = self._tool_registry.get(tool_name)
                elif hasattr(self._tool_registry, 'find_tool'):
                    tool = self._tool_registry.find_tool(tool_name)
                
                if tool is None:
                    error_msg = f"无法获取工具实例: {tool_name}"
                    logger.error(error_msg)
                    return ToolResult(
                        success=False,
                        output=None,
                        execution_time=time.time() - start_time,
                        error=error_msg
                    )
            
            # 执行工具（优先使用call方法，然后是execute方法）
            if hasattr(tool, 'call'):
                result = await tool.call(**tool_params)
            elif hasattr(tool, 'execute'):
                result = await tool.execute(**tool_params)
            else:
                error_msg = f"工具 {tool_name} 没有可调用的方法"
                logger.error(error_msg)
                return ToolResult(
                    success=False,
                    output=None,
                    execution_time=time.time() - start_time,
                    error=error_msg
                )
            
            # 记录统计
            execution_time = time.time() - start_time
            self._tool_stats[tool_name].record_call(
                success=result.success,
                execution_time=execution_time,
                error=result.error
            )
            
            # 更新状态管理器
            self._update_state_with_tool_execution(tool_name, result, execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            
            # 记录错误统计
            if tool_name in self._tool_stats:
                self._tool_stats[tool_name].record_call(
                    success=False,
                    execution_time=execution_time,
                    error=str(e)
                )
            
            return ToolResult(
                success=False,
                output=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _check_permission(self, required_permission: ToolPermission, 
                          user_context: Optional[Dict[str, Any]] = None) -> bool:
        """检查权限（简化实现，实际项目中需要更复杂的权限系统）"""
        # 这里可以集成实际的权限检查逻辑
        # 例如：检查用户角色、API密钥、会话上下文等
        
        # 如果没有用户上下文，使用简化的权限检查
        if user_context is None:
            # 简化实现：暂时允许所有权限
            return True
        
        # 从用户上下文中提取权限信息
        user_permissions = user_context.get('permissions', [])
        user_roles = user_context.get('roles', [])
        user_id = user_context.get('user_id', 'anonymous')
        
        # 根据权限级别进行简单的检查
        if required_permission == ToolPermission.PUBLIC:
            # 公开工具：任何人都可以访问
            return True
        elif required_permission == ToolPermission.RESTRICTED:
            # 受限工具：需要特定权限
            # 这里简化实现：检查是否包含相关权限
            return len(user_permissions) > 0 or len(user_roles) > 0
        elif required_permission == ToolPermission.ADMIN:
            # 管理员工具：需要管理员角色
            return 'admin' in user_roles or 'administrator' in user_roles
        elif required_permission == ToolPermission.SYSTEM:
            # 系统工具：只允许系统内部使用
            return user_id == 'system' or 'system' in user_roles
        
        # 默认拒绝
        return False
    
    def _update_state_with_tool_info(self):
        """更新状态管理器中的工具信息"""
        tool_summary = {
            "total_tools": len(self._tool_metadata),
            "tools_by_layer": {
                layer.value: len(tools) for layer, tools in self._tools_by_layer.items()
            },
            "tools_by_category": {
                category.value: len(tools) for category, tools in self._tools_by_category.items()
            },
            "available_tools": list(self._tool_metadata.keys())
        }
        
        self._state_manager.update_state({
            "tool_system_info": tool_summary
        })
    
    def _update_state_with_tool_execution(self, tool_name: str, result: ToolResult, execution_time: float):
        """更新状态管理器中的工具执行信息"""
        update_data = {
            "last_tool_execution": {
                "tool_name": tool_name,
                "success": result.success,
                "execution_time": execution_time,
                "timestamp": time.time(),
                "error": result.error
            }
        }
        
        # 更新工具统计
        if tool_name in self._tool_stats:
            update_data[f"tool_stats_{tool_name}"] = self._tool_stats[tool_name].to_dict()
        
        self._state_manager.update_state(update_data)
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if tool_name not in self._tool_metadata:
            return None
        
        metadata = self._tool_metadata[tool_name]
        stats = self._tool_stats.get(tool_name, ToolExecutionStats())
        
        return {
            "metadata": metadata.to_dict(),
            "stats": stats.to_dict(),
            "is_registered": tool_name in self._tool_instances
        }
    
    def get_tool_stats(self, tool_name: str) -> Optional[ToolExecutionStats]:
        """获取工具执行统计"""
        return self._tool_stats.get(tool_name)
    
    def get_tools_by_layer(self, layer: ToolLayer) -> List[str]:
        """获取指定层级的工具名称列表"""
        return self._tools_by_layer.get(layer, [])
    
    def list_tools(self, layer: Optional[ToolLayer] = None, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        """列出工具"""
        tools = []
        
        # 确定要列出的工具名称
        tool_names = []
        
        if layer is not None:
            if category is not None:
                # 按层级和类别过滤
                tool_names = [
                    name for name in self._tools_by_layer[layer]
                    if name in self._tools_by_category[category]
                ]
            else:
                # 仅按层级过滤
                tool_names = self._tools_by_layer[layer]
        elif category is not None:
            # 仅按类别过滤
            tool_names = self._tools_by_category[category]
        else:
            # 所有工具
            tool_names = list(self._tool_metadata.keys())
        
        # 构建工具信息
        for name in tool_names:
            if name in self._tool_metadata:
                tools.append(self.get_tool_info(name))
        
        return tools
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        total_tools = len(self._tool_metadata)
        total_calls = sum(stats.total_calls for stats in self._tool_stats.values())
        avg_success_rate = sum(stats.success_rate for stats in self._tool_stats.values()) / len(self._tool_stats) if self._tool_stats else 0.0
        
        return {
            "total_tools": total_tools,
            "total_tool_calls": total_calls,
            "average_success_rate": avg_success_rate,
            "tools_by_layer": {
                layer.value: len(tools) for layer, tools in self._tools_by_layer.items()
            },
            "top_tools_by_calls": self._get_top_tools_by_calls(limit=5),
            "recent_errors": self._get_recent_errors(limit=10)
        }
    
    def _get_top_tools_by_calls(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取调用次数最多的工具"""
        sorted_tools = sorted(
            self._tool_stats.items(),
            key=lambda x: x[1].total_calls,
            reverse=True
        )[:limit]
        
        return [
            {
                "tool_name": name,
                "total_calls": stats.total_calls,
                "success_rate": stats.success_rate,
                "avg_execution_time": stats.avg_time
            }
            for name, stats in sorted_tools
        ]
    
    def _get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        errors = []
        
        for tool_name, stats in self._tool_stats.items():
            if stats.last_error and stats.last_call_time:
                errors.append({
                    "tool_name": tool_name,
                    "error": stats.last_error,
                    "timestamp": stats.last_call_time,
                    "call_count": stats.total_calls
                })
        
        # 按时间戳排序
        errors.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return errors[:limit]
    
    async def initialize(self):
        """初始化工具系统"""
        logger.info("开始初始化分层工具系统...")
        
        # 自动发现工具
        discovered_count = await self.discover_and_register_tools()
        
        # 加载核心工具（如果自动发现未找到）
        await self._load_core_tools_if_needed()
        
        # 验证工具系统
        await self._validate_tool_system()
        
        logger.info(f"分层工具系统初始化完成，共 {len(self._tool_metadata)} 个工具可用")
        
        return {
            "status": "initialized",
            "total_tools": len(self._tool_metadata),
            "discovered_tools": discovered_count,
            "layers_available": [
                layer.value for layer, tools in self._tools_by_layer.items() if tools
            ]
        }
    
    async def _load_core_tools_if_needed(self):
        """加载核心工具（如果需要）"""
        # 检查是否缺少必要的核心工具
        required_core_tools = ["file_read", "file_write", "bash", "deepseek_cost_check"]
        
        missing_tools = []
        for tool_name in required_core_tools:
            if tool_name not in self._tool_metadata:
                missing_tools.append(tool_name)
        
        if missing_tools:
            logger.warning(f"缺少核心工具: {missing_tools}")
            # 这里可以添加动态加载核心工具的逻辑
    
    async def _validate_tool_system(self):
        """验证工具系统"""
        validation_results = {
            "total_tools": len(self._tool_metadata),
            "layers_with_tools": [],
            "categories_with_tools": [],
            "tools_with_errors": []
        }
        
        # 检查各层级是否有工具
        for layer, tools in self._tools_by_layer.items():
            if tools:
                validation_results["layers_with_tools"].append(layer.value)
        
        # 检查各类别是否有工具
        for category, tools in self._tools_by_category.items():
            if tools:
                validation_results["categories_with_tools"].append(category.value)
        
        # 验证工具可用性
        for tool_name in self._tool_metadata.keys():
            tool = self._tool_registry.get_tool(tool_name)
            if not tool:
                validation_results["tools_with_errors"].append({
                    "tool_name": tool_name,
                    "error": "未在注册表中找到"
                })
        
        logger.info(f"工具系统验证完成: {validation_results}")
        
        return validation_results


# 全局工具系统实例
_global_tool_system: Optional[HierarchicalToolSystem] = None


def get_global_tool_system() -> HierarchicalToolSystem:
    """获取全局分层工具系统（单例）"""
    global _global_tool_system
    if _global_tool_system is None:
        _global_tool_system = HierarchicalToolSystem()
    return _global_tool_system


async def initialize_global_tool_system():
    """初始化全局工具系统"""
    system = get_global_tool_system()
    return await system.initialize()


# 与双层循环处理器链集成
def integrate_with_double_loop_processor():
    """
    将分层工具系统集成到双层循环处理器链
    
    使用示例：
    1. 在 double_loop_processor_chain.py 中导入此模块
    2. 在处理器链中使用分层工具系统执行工具
    3. 获取工具统计和性能数据
    """
    return get_global_tool_system()


if __name__ == "__main__":
    # 示例用法
    import asyncio
    
    async def example():
        # 初始化工具系统
        system = HierarchicalToolSystem()
        await system.initialize()
        
        # 获取系统摘要
        summary = system.get_system_summary()
        print(f"工具系统摘要: {summary}")
        
        # 列出所有工具
        all_tools = system.list_tools()
        print(f"共 {len(all_tools)} 个工具可用")
        
        # 按层级列出工具
        core_tools = system.list_tools(layer=ToolLayer.CORE)
        print(f"核心工具: {len(core_tools)} 个")
        
        # 按类别列出工具
        utility_tools = system.list_tools(category=ToolCategory.UTILITY)
        print(f"工具类工具: {len(utility_tools)} 个")
        
        # 获取特定工具信息
        if core_tools:
            tool_info = system.get_tool_info(core_tools[0]["metadata"]["name"])
            print(f"工具信息示例: {tool_info}")
    
    asyncio.run(example())