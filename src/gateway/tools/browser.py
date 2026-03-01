"""
Browser Automation Tool - 浏览器自动化

基于 Playwright 的浏览器控制
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class BrowserMode(Enum):
    """浏览器模式"""
    HEADLESS = "headless"  # 无头模式
    VISIBLE = "visible"    # 可视模式


@dataclass
class BrowserConfig:
    """浏览器配置"""
    mode: BrowserMode = BrowserMode.HEADLESS
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout: int = 30000  # 毫秒
    slow_mo: int = 0  # 慢动作模式 (毫秒)


class BrowserTool:
    """
    浏览器自动化工具
    
    功能:
    - 打开网页
    - 点击元素
    - 填写表单
    - 截图
    - 获取页面内容
    - 执行 JavaScript
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False
    
    async def initialize(self):
        """初始化浏览器"""
        if self._initialized:
            return
        
        logger.info("Initializing browser...")
        
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.mode == BrowserMode.HEADLESS,
                slow_mo=self.config.slow_mo
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                }
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            self._initialized = True
            logger.info("Browser initialized")
            
        except ImportError:
            logger.error("playwright not installed. Run: pip install playwright && playwright install chromium")
            raise
        except Exception as e:
            logger.error(f"Browser initialization error: {e}")
            raise
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        logger.info("Browser closed")
    
    async def navigate(self, url: str) -> str:
        """导航到 URL"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.goto(url, timeout=self.config.timeout)
        
        # 等待页面加载
        await self.page.wait_for_load_state("networkidle")
        
        title = await self.page.title()
        
        logger.info(f"Navigated to: {url} (title: {title})")
        return f"Opened: {title}"
    
    async def click(self, selector: str) -> str:
        """点击元素"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.click(selector)
        logger.info(f"Clicked: {selector}")
        return f"Clicked: {selector}"
    
    async def fill(self, selector: str, value: str) -> str:
        """填写表单"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.fill(selector, value)
        logger.info(f"Filled: {selector} = {value}")
        return f"Filled: {selector}"
    
    async def type_text(self, selector: str, text: str, delay: int = 100) -> str:
        """输入文本 (模拟打字)"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.type(selector, text, delay=delay)
        logger.info(f"Typed: {text[:20]}...")
        return f"Typed: {text[:50]}..."
    
    async def screenshot(self, path: Optional[str] = None) -> str:
        """截图"""
        if not self._initialized:
            await self.initialize()
        
        if not path:
            path = f"screenshots/screenshot_{int(asyncio.get_event_loop().time())}.png"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        await self.page.screenshot(path=path, full_page=True)
        
        logger.info(f"Screenshot saved: {path}")
        return path
    
    async def get_content(self, selector: Optional[str] = None) -> str:
        """获取页面内容"""
        if not self._initialized:
            await self.initialize()
        
        if selector:
            content = await self.page.inner_text(selector)
        else:
            content = await self.page.content()
        
        return content[:5000]  # 限制长度
    
    async def evaluate(self, script: str) -> Any:
        """执行 JavaScript"""
        if not self._initialized:
            await self.initialize()
        
        result = await self.page.evaluate(script)
        return result
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> str:
        """等待元素出现"""
        if not self._initialized:
            await self.initialize()
        
        timeout = timeout or self.config.timeout
        
        await self.page.wait_for_selector(selector, timeout=timeout)
        
        logger.info(f"Element found: {selector}")
        return f"Element found: {selector}"
    
    async def get_text(self, selector: str) -> str:
        """获取元素文本"""
        if not self._initialized:
            await self.initialize()
        
        text = await self.page.inner_text(selector)
        return text
    
    async def get_attribute(self, selector: str, attribute: str) -> str:
        """获取元素属性"""
        if not self._initialized:
            await self.initialize()
        
        value = await self.page.get_attribute(selector, attribute)
        return value or ""
    
    async def is_visible(self, selector: str) -> bool:
        """检查元素是否可见"""
        if not self._initialized:
            await self.initialize()
        
        return await self.page.is_visible(selector)
    
    async def scroll(self, x: int = 0, y: int = 500) -> str:
        """滚动页面"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.mouse.wheel(x, y)
        return f"Scrolled to: {x}, {y}"
    
    async def go_back(self) -> str:
        """后退"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.go_back()
        return "Went back"
    
    async def go_forward(self) -> str:
        """前进"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.go_forward()
        return "Went forward"
    
    async def reload(self) -> str:
        """刷新页面"""
        if not self._initialized:
            await self.initialize()
        
        await self.page.reload()
        return "Page reloaded"
    
    # ==================== 便捷方法 ====================
    
    async def search_google(self, query: str) -> str:
        """搜索 Google - 使用多种selector兼容"""
        await self.navigate("https://www.google.com")
        
        # 尝试多种selector（Google可能会变化）
        selectors = [
            'textarea[name="q"]',
            'textarea[name="q"][role="combobox"]',
            '#APjFqb textarea',
            'input[name="q"]',
            '.gLFyf'
        ]
        
        search_filled = False
        for selector in selectors:
            try:
                # 检查元素是否存在
                if await self.page.locator(selector).count() > 0:
                    await self.fill(selector, query)
                    search_filled = True
                    break
            except Exception:
                continue
        
        if not search_filled:
            # 最后尝试：直接使用JavaScript
            await self.page.evaluate(f'document.querySelector("textarea[name=\"q\"]").value = "{query}"')
        
        # 按回车键
        await self.page.keyboard.press("Enter")
        await self.page.wait_for_load_state("networkidle")
        
        # 获取结果
        try:
            results = await self.page.inner_text("#search")
        except:
            results = await self.page.inner_text(".g")
        return results[:2000]
        """搜索 Google"""
        await self.navigate("https://www.google.com")
        await self.fill('textarea[name="q"]', query)
        await self.press('textarea[name="q"]', "Enter")
        await self.page.wait_for_load_state("networkidle")
        
        # 获取结果
        results = await self.page.inner_text("#search")
        return results[:2000]
    
    async def fill_form(self, form_data: Dict[str, str]) -> str:
        """填写表单"""
        results = []
        for selector, value in form_data.items():
            await self.fill(selector, value)
            results.append(f"{selector}: {value}")
        
        return "\n".join(results)


# ==================== 便捷函数 ====================

def create_browser_tool(
    headless: bool = True,
    slow_mo: int = 0
) -> BrowserTool:
    """创建浏览器工具"""
    config = BrowserConfig(
        mode=BrowserMode.HEADLESS if headless else BrowserMode.VISIBLE,
        slow_mo=slow_mo
    )
    return BrowserTool(config)
