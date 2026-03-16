#!/usr/bin/env python3
"""
Browser Automation Tool - 浏览器自动化工具
基于 Playwright 的浏览器控制
"""

import time
import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class BrowserTool(BaseTool):
    """浏览器自动化工具"""
    
    def __init__(self):
        """初始化浏览器工具"""
        super().__init__(
            tool_name="browser",
            description="""浏览器自动化工具：打开网页、点击元素、填写表单、截图、获取页面内容

支持两种模式：
- headless=False (默认): 可视模式，弹出浏览器窗口，用户可以看到操作过程
- headless=True: 无头模式，后台运行，适合批量处理

常见操作：
- navigate: 打开网页 (url参数)
- click: 点击元素 (selector参数)  
- fill: 填写表单 (selector, value参数)
- screenshot: 截图 (path参数可选)
- get_content: 获取页面内容
- scroll: 滚动页面 (direction参数: up/down)
"""
        )
        self._browser = None
        self._config = None
    
    async def call(self, action: str, url: str = "", selector: str = "", 
                   value: str = "", text: str = "", headless: bool = False,
                   **kwargs) -> ToolResult:
        """调用浏览器工具
        
        Args:
            headless: 是否使用无头模式。
                     False=可视模式(默认)，弹出浏览器窗口，用户可见
                     True=无头模式，后台运行
        """
        start_time = time.time()
        
        try:
            from src.gateway.tools.browser import BrowserTool as GatewayBrowserTool
            from src.gateway.tools.browser import BrowserConfig, BrowserMode
            
            # 根据 headless 参数决定模式
            mode = BrowserMode.HEADLESS if headless else BrowserMode.VISIBLE
            
            # 只有模式变化时才重新创建浏览器
            if self._browser is None or (self._config and self._config.mode != mode):
                if self._browser:
                    await self._browser.close()
                
                self._config = BrowserConfig(
                    mode=mode,
                    viewport_width=1280,
                    viewport_height=800
                )
                self._browser = GatewayBrowserTool(self._config)
                await self._browser.initialize()
                logger.info(f"Browser initialized in {'headless' if headless else 'visible'} mode")
            
            result_data = {}
            
            if action == "navigate":
                result = await self._browser.navigate(url)
                result_data = {"url": url, "title": result}
                
            elif action == "click":
                result = await self._browser.click(selector)
                result_data = {"selector": selector, "result": result}
                
            elif action == "fill":
                result = await self._browser.fill(selector, value)
                result_data = {"selector": selector, "value": value[:50], "result": result}
                
            elif action == "type":
                delay = kwargs.get("delay", 100)
                result = await self._browser.type_text(selector, text, delay)
                result_data = {"selector": selector, "text": text[:50], "result": result}
                
            elif action == "screenshot":
                path = kwargs.get("path", "screenshot.png")
                result = await self._browser.screenshot(path)
                result_data = {"path": path, "result": result}
                
            elif action == "get_content":
                content = await self._browser.get_content(selector) if selector else await self._browser.get_content()
                result_data = {"content": content[:1000], "full_length": len(content)}
                
            elif action == "execute_script":
                script = kwargs.get("script", "")
                result = await self._browser.evaluate(script)
                result_data = {"script": script[:100], "result": str(result)}
                
            elif action == "search":
                query = kwargs.get("query", "")
                result = await self._browser.search_google(query)
                result_data = {"query": query, "result": result}
                
            else:
                raise ValueError(f"Unknown action: {action}")
            
            execution_time = time.time() - start_time
            self._record_call(True)
            
            return ToolResult(
                success=True,
                data=result_data,
                metadata={"action": action, "execution_time": execution_time},
                execution_time=execution_time
            )
            
        except ImportError as e:
            self.logger.error(f"playwright not installed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error="playwright not installed",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Browser tool error: {str(e)[:100]}")
            self._record_call(False)
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取工具参数模式"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["navigate", "click", "fill", "type", "screenshot", "get_content", "execute_script", "search"]
                },
                "url": {"type": "string", "description": "网页URL"},
                "selector": {"type": "string", "description": "CSS选择器"},
                "value": {"type": "string", "description": "填写值"},
                "text": {"type": "string", "description": "输入文本"},
                "path": {"type": "string", "description": "截图保存路径"},
                "delay": {"type": "integer", "description": "打字延迟"},
                "script": {"type": "string", "description": "JavaScript代码"},
                "query": {"type": "string", "description": "搜索查询"}
            },
            "required": ["action"]
        }
