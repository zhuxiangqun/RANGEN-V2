"""
RPA 工具模块 - 自动化运行、评测、修复和改进核心系统

主要功能：
1. 浏览器自动化 - Selenium 控制浏览器
2. 前端监控 - 检测和修复前端问题
3. 核心分析 - 分析系统日志和错误
4. 系统改进 - 生成改进方案

使用方式:
    from src.tools.rpa import BrowserAutomation
    
    browser = BrowserAutomation()
    browser.start_browser()
"""

from .browser_automation import BrowserAutomation, SELENIUM_AVAILABLE
from .frontend_monitor import FrontendMonitor
from .core_analyzer import CoreAnalyzer
from .system_improver import SystemImprover
from .report_generator import ReportGenerator

__version__ = "2.0.0"

__all__ = [
    "BrowserAutomation",
    "SELENIUM_AVAILABLE",
    "FrontendMonitor",
    "CoreAnalyzer",
    "SystemImprover",
    "ReportGenerator",
]
