"""
Tool Registry Service - Auto-discovery and metadata management for Tools
"""
import os
import importlib
import inspect
from typing import List, Dict, Any, Optional
from src.services.database import get_database
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Tool注册表 - 自动发现现有Tools"""
    
    def __init__(self):
        self.db = get_database()
        self._tool_dirs = [
            'src/agents/tools',
            'tools',
        ]
    
    def discover_tools(self) -> List[Dict[str, Any]]:
        """发现并注册现有Tools"""
        discovered = []
        
        for tool_dir in self._tool_dirs:
            if not os.path.exists(tool_dir):
                continue
            
            for root, dirs, files in os.walk(tool_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('_'):
                        file_path = os.path.join(root, file)
                        tools = self._extract_tools_from_file(file_path)
                        discovered.extend(tools)
        
        # 注册到数据库
        registered = []
        for tool in discovered:
            existing = self.db.get_tool(tool['id'])
            if not existing:
                self.db.create_tool(tool)
                registered.append(tool)
                logger.info(f"Registered tool: {tool['id']} - {tool['name']}")
            else:
                logger.debug(f"Tool already exists: {tool['id']}")
        
        return registered
    
    def _extract_tools_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """从Python文件中提取Tool定义"""
        tools = []
        
        try:
            # 计算相对模块路径
            rel_path = os.path.relpath(file_path, os.getcwd())
            module_name = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            # 尝试导入模块
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                return tools
            
            # 查找Tool类或函数
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) or inspect.isfunction(obj):
                    # 检查是否有Tool相关的docstring或属性
                    if self._is_tool_class(obj):
                        tool_info = {
                            'id': f"tool_{name.lower()}",
                            'name': name,
                            'description': inspect.getdoc(obj) or f"Auto-discovered tool: {name}",
                            'type': 'discovered',
                            'status': 'active'
                        }
                        tools.append(tool_info)
        
        except Exception as e:
            logger.warning(f"Error extracting tools from {file_path}: {e}")
        
        return tools
    
    def _is_tool_class(self, obj: Any) -> bool:
        """检查对象是否是Tool类"""
        # 简单启发式检查
        obj_name = obj.__name__.lower() if hasattr(obj, '__name__') else ''
        
        # 常见的Tool命名模式
        tool_patterns = ['tool', 'agent', 'service', 'executor', 'handler']
        
        return any(pattern in obj_name for pattern in tool_patterns)
    
    def sync_tools(self) -> Dict[str, Any]:
        """同步所有Tools到数据库"""
        discovered = self.discover_tools()
        
        return {
            'discovered': len(discovered),
            'total_tools': len(self.db.get_all_tools())
        }


def get_tool_registry() -> ToolRegistry:
    """获取Tool注册表实例"""
    return ToolRegistry()
