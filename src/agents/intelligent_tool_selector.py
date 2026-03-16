#!/usr/bin/env python3
"""
Intelligent Tool Selector - 智能工具选择器

核心功能：
1. 需求分析 - 理解用户想要什么
2. 工具匹配 - 判断现有工具是否能满足
3. 工具生成 - 如果不满足，自动触发 CLI-Anything
4. 参数自适应 - 根据意图自动调整工具参数
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class IntentType(Enum):
    """用户意图类型"""
    BROWSE = "browse"           # 浏览网页
    SEARCH = "search"           # 搜索信息
    CALCULATE = "calculate"    # 计算
    READ_FILE = "read_file"     # 读取文件
    WRITE_FILE = "write_file"   # 写入文件
    EXECUTE_CODE = "execute"   # 执行代码
    MEDIA_PROCESS = "media"     # 媒体处理
    VIDEO = "video"            # 视频处理
    AUDIO = "audio"            # 音频处理
    UNKNOWN = "unknown"


@dataclass
class Requirement:
    """用户需求"""
    original_query: str
    intent: IntentType
    entities: List[str]           # 识别的实体 (URL, 文件名等)
    constraints: Dict[str, Any]   # 约束条件 (可视化、批量处理等)
    missing_capabilities: List[str] # 现有工具缺失的能力


@dataclass
class ToolAdaptation:
    """工具适配方案"""
    tool_name: str
    parameters: Dict[str, Any]
    reason: str


class IntelligentToolSelector:
    """
    智能工具选择器
    
    工作流程：
    1. 分析用户需求 → Requirement
    2. 检查现有工具 → 能否满足？
    3. 如果不能 → 触发 CLI-Anything 生成
    4. 适配参数 → 返回最佳工具和参数
    """
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        IntentType.BROWSE: ["打开", "访问", "浏览", "看", "网页", "网站", "打开网页", "打开网站", "visit", "browse", "open"],
        IntentType.SEARCH: ["搜索", "查找", "找", "search", "find", "google"],
        IntentType.CALCULATE: ["计算", "算", "calculate", "compute"],
        IntentType.READ_FILE: ["读取", "打开文件", "看文件", "read", "open file"],
        IntentType.WRITE_FILE: ["写入", "保存", "写", "write", "save"],
        IntentType.EXECUTE_CODE: ["执行", "运行", "run", "execute"],
        IntentType.MEDIA_PROCESS: ["转换", "处理", "视频", "音频", "图片", "convert", "process", "video", "audio", "image"],
    }
    
    # 约束条件关键词
    CONSTRAINT_KEYWORDS = {
        "visible": ["我要看", "可视化", "显示", "打开窗口", "弹出", "看到", "可见", "visible", "show me", "open window"],
        "headless": ["后台", "静默", "批量", "自动化", "headless", "background", "batch", "automate"],
        "interactive": ["交互", "点击", "填写", "interactive", "click", "fill"],
    }
    
    def __init__(self, tool_registry, cli_executor=None):
        self.tool_registry = tool_registry
        self.cli_executor = cli_executor
        self._generated_tools_cache = {}
    
    async def analyze_and_select(
        self, 
        query: str, 
        available_tools: List[Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict], Optional[ToolAdaptation]]:
        """
        分析需求并选择工具
        
        Returns:
            (needs_new_tool, tool_name, tool_instance, adaptation)
        """
        # Step 1: 需求分析
        requirement = self._analyze_requirement(query)
        logger.info(f"需求分析: intent={requirement.intent.value}, constraints={requirement.constraints}")
        
        # Step 2: 检查现有工具是否满足
        tool_match = self._find_matching_tool(requirement, available_tools)
        
        if tool_match:
            # Step 3: 适配参数
            adaptation = self._adapt_parameters(requirement, tool_match)
            tool_name = tool_match.base_tool.tool_name
            logger.info(f"使用现有工具: {tool_name}, 参数: {adaptation.parameters}")
            return False, tool_name, tool_match, adaptation
        
        # Step 4: 现有工具不满足，尝试生成新工具
        new_tool = await self._generate_tool_if_needed(requirement)
        
        if new_tool:
            adaptation = self._adapt_parameters(requirement, new_tool, is_generated=True)
            tool_name = new_tool.base_tool.tool_name
            logger.info(f"生成新工具: {tool_name}, 参数: {adaptation.parameters}")
            return True, tool_name, new_tool, adaptation
        
        # 真的找不到工具
        return False, None, None, None
    
    def _analyze_requirement(self, query: str) -> Requirement:
        """分析用户需求"""
        query_lower = query.lower()
        
        # 1. 识别意图
        intent = IntentType.UNKNOWN
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                intent = intent_type
                break
        
        # 2. 识别实体 (URL, 文件名等)
        entities = []
        
        # URL 匹配
        url_pattern = r'https?://[^\s]+'
        entities.extend(re.findall(url_pattern, query))
        
        # 文件名匹配
        file_pattern = r'[a-zA-Z]:\\[^\s]+|/[^\s]+\.[a-zA-Z]+'
        entities.extend(re.findall(file_pattern, query))
        
        # 3. 识别约束条件
        constraints = {}
        
        # 可视化需求
        if any(kw in query_lower for kw in self.CONSTRAINT_KEYWORDS["visible"]):
            constraints["visible"] = True
            constraints["headless"] = False
        
        # 无头模式需求
        elif any(kw in query_lower for kw in self.CONSTRAINT_KEYWORDS["headless"]):
            constraints["visible"] = False
            constraints["headless"] = True
        
        # 交互需求
        if any(kw in query_lower for kw in self.CONSTRAINT_KEYWORDS["interactive"]):
            constraints["interactive"] = True
        
        return Requirement(
            original_query=query,
            intent=intent,
            entities=entities,
            constraints=constraints,
            missing_capabilities=[]
        )
    
    def _get_tool_name(self, tool) -> str:
        """获取工具名称 - 支持多种方式"""
        # 方式 1: 直接属性
        name = getattr(tool, "tool_name", None)
        if name and isinstance(name, str):
            return name
        
        # 方式 2: base_tool 属性 (适配器模式)
        base_tool = getattr(tool, "base_tool", None)
        if base_tool:
            name = getattr(base_tool, "tool_name", None)
            if name:
                return name
        
        # 方式 3: name 属性
        name = getattr(tool, "name", None)
        if name and isinstance(name, str):
            return name
        
        # 方式 4: 转换为字符串
        return str(tool)
    
    def _find_matching_tool(self, requirement: Requirement, tools: List[Any]) -> Optional[Any]:
        """查找匹配的工具"""
        
        intent_tool_map = {
            IntentType.BROWSE: ["browser", "BrowserTool"],
            IntentType.SEARCH: ["search", "SearchTool", "web_search"],
            IntentType.CALCULATE: ["calculator", "CalculatorTool"],
            IntentType.READ_FILE: ["file_read", "FileReadTool"],
            IntentType.WRITE_FILE: ["file_write", "FileWriteTool"],
            IntentType.MEDIA_PROCESS: ["ffmpeg", "image", "convert"],
        }
        
        # 获取该意图对应的工具关键词
        tool_keywords = intent_tool_map.get(requirement.intent, [])
        
        for tool in tools:
            tool_name = self._get_tool_name(tool)
            tool_name_lower = tool_name.lower()
            
            # 检查工具名是否匹配
            if any(kw.lower() in tool_name_lower for kw in tool_keywords):
                return tool
        
        return None
    
    def _adapt_parameters(
        self, 
        requirement: Requirement, 
        tool: Any,
        is_generated: bool = False
    ) -> ToolAdaptation:
        """根据需求适配工具参数"""
        
        tool_name = self._get_tool_name(tool)
        
        # 初始化参数
        parameters = {}
        
        # 1. 浏览器工具参数适配
        if "browser" in tool_name.lower():
            # 可视化参数
            if requirement.constraints.get("visible"):
                parameters["headless"] = False
                parameters["action"] = "navigate"
            elif requirement.constraints.get("headless"):
                parameters["headless"] = True
                parameters["action"] = "navigate"
            else:
                # 默认可视化
                parameters["headless"] = False
            
            # URL 参数
            if requirement.entities:
                for entity in requirement.entities:
                    if entity.startswith("http"):
                        parameters["url"] = entity
            
            # 确保浏览器工具有 action 参数
            parameters["action"] = "navigate"
        
        # 2. 搜索工具参数适配
        elif "search" in tool_name.lower():
            parameters["action"] = "search"
            # 从查询中提取搜索词
            search_query = requirement.original_query
            for kw in ["搜索", "查找", "search", "find"]:
                search_query = re.sub(f"{kw}\\s*", "", search_query, flags=re.IGNORECASE)
            parameters["query"] = search_query
        
        # 3. 媒体处理工具
        elif any(kw in tool_name.lower() for kw in ["ffmpeg", "convert", "media"]):
            parameters["action"] = "convert"
        
        return ToolAdaptation(
            tool_name=tool_name,
            parameters=parameters,
            reason=f"基于意图 {requirement.intent.value} 和约束 {requirement.constraints}"
        )
    
    async def _generate_tool_if_needed(self, requirement: Requirement) -> Optional[Any]:
        """如果需要，生成新工具"""
        
        # 检查是否已经有生成的工具缓存
        cache_key = requirement.intent.value
        if cache_key in self._generated_tools_cache:
            return self._generated_tools_cache[cache_key]
        
        # 根据意图确定需要什么软件
        software_map = {
            IntentType.BROWSE: "firefox",
            IntentType.MEDIA_PROCESS: "ffmpeg",
            IntentType.VIDEO: "ffmpeg",
            IntentType.AUDIO: "ffmpeg",
        }
        
        software = software_map.get(requirement.intent)
        
        if not software:
            # 尝试使用 CLI-Anything 生成器
            try:
                from src.core.cli_anything_generator import get_cli_anything_generator
                generator = get_cli_anything_generator()
                
                # 根据需求推断软件
                query = requirement.original_query
                
                # 常见的软件关键词
                software_keywords = {
                    "gimp": "gimp", "图像": "imagemagick", "图片": "imagemagick",
                    "blender": "blender", "3d": "blender",
                    "视频": "ffmpeg", "音频": "ffmpeg",
                    "office": "libreoffice", "文档": "libreoffice",
                }
                
                for kw, sw in software_keywords.items():
                    if kw in query.lower():
                        software = sw
                        break
                
                if software:
                    logger.info(f"尝试生成 CLI 工具: {software}")
                    result = await generator.generate(software)
                    
                    if result.success:
                        # 重新发现工具
                        if self.cli_executor:
                            self.cli_executor.discover_tools()
                        
                        # 返回生成的工具
                        tool = self._find_matching_tool(requirement, [])
                        if tool:
                            self._generated_tools_cache[cache_key] = tool
                            return tool
                            
            except Exception as e:
                logger.warning(f"CLI-Anything 生成失败: {e}")
        
        return None


# 全局单例
_selector: Optional[IntelligentToolSelector] = None


def get_intelligent_tool_selector(
    tool_registry=None, 
    cli_executor=None
) -> IntelligentToolSelector:
    """获取智能工具选择器实例"""
    global _selector
    if _selector is None:
        _selector = IntelligentToolSelector(tool_registry, cli_executor)
    return _selector
