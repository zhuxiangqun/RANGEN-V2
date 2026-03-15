"""
前端系统自动化模块
整合浏览器自动化，实现完整的自动化流程
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .browser_automation import BrowserAutomation, SELENIUM_AVAILABLE
from .core_analyzer import CoreSystemAnalyzer
from .report_generator import ReportGenerator
from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class FrontendAutomation:
    """前端系统自动化控制器"""
    
    def __init__(self, frontend_url: Optional[str] = None, headless: bool = False):
        """
        初始化前端自动化
        
        Args:
            frontend_url: 前端系统URL
            headless: 是否使用无头模式
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium未安装，无法使用前端自动化功能")
        
        self.browser = BrowserAutomation(frontend_url)
        self.headless = headless
        self.core_analyzer = CoreSystemAnalyzer()
        self.report_generator = ReportGenerator()
        
    async def run_full_automation_cycle(
        self, 
        sample_count: int = 10,
        wait_for_completion: bool = True,
        run_evaluation: bool = True
    ) -> Dict[str, Any]:
        """
        运行完整的自动化循环：
        1. 打开前端页面
        2. 设置样本数量
        3. 点击运行核心系统按钮
        4. 等待执行完成
        5. 运行评测（可选）
        6. 分析结果
        7. 生成报告
        
        Args:
            sample_count: 样本数量
            wait_for_completion: 是否等待任务完成
            run_evaluation: 是否运行评测
            
        Returns:
            执行结果
        """
        run_id = f"auto_{int(time.time())}"
        results = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "sample_count": sample_count,
            "steps": {}
        }
        
        try:
            # 步骤1: 启动浏览器并打开前端页面
            logger.info("🌐 步骤1: 启动浏览器并打开前端页面...")
            if not self.browser.start_browser(headless=self.headless):
                raise Exception("启动浏览器失败")
            
            if not self.browser.open_frontend_page():
                raise Exception("打开前端页面失败")
            
            results["steps"]["open_frontend"] = {
                "status": "success",
                "url": self.browser.frontend_url
            }
            
            # 截图记录
            screenshot_path = self.browser.take_screenshot()
            if screenshot_path:
                results["steps"]["open_frontend"]["screenshot"] = str(screenshot_path)
            
            # 步骤2: 设置样本数量
            logger.info(f"⚙️ 步骤2: 设置样本数量为 {sample_count}...")
            if not self.browser.set_sample_count(sample_count):
                raise Exception("设置样本数量失败")
            
            results["steps"]["set_sample_count"] = {
                "status": "success",
                "sample_count": sample_count
            }
            
            # 步骤3: 点击运行核心系统按钮
            logger.info("🚀 步骤3: 点击'运行核心系统'按钮...")
            if not self.browser.click_run_core_system_button():
                raise Exception("点击运行核心系统按钮失败")
            
            results["steps"]["click_run_button"] = {
                "status": "success"
            }
            
            # 截图记录
            screenshot_path = self.browser.take_screenshot()
            if screenshot_path:
                results["steps"]["click_run_button"]["screenshot"] = str(screenshot_path)
            
            # 步骤4: 等待任务完成
            if wait_for_completion:
                logger.info("⏳ 步骤4: 等待核心系统执行完成...")
                completion_result = self.browser.wait_for_task_completion(
                    task_type="core",
                    timeout=3600  # 1小时超时
                )
                results["steps"]["wait_completion"] = completion_result
                
                if completion_result["status"] == "completed":
                    logger.info("✅ 核心系统执行完成")
                elif completion_result["status"] == "failed":
                    logger.warning("⚠️ 核心系统执行失败")
                elif completion_result["status"] == "timeout":
                    logger.warning("⚠️ 核心系统执行超时")
            
            # 步骤5: 运行评测（可选）
            if run_evaluation and wait_for_completion:
                logger.info("📊 步骤5: 运行评测系统...")
                if self.browser.click_run_evaluation_button():
                    eval_completion = self.browser.wait_for_task_completion(
                        task_type="eval",
                        timeout=600  # 10分钟超时
                    )
                    results["steps"]["evaluation"] = eval_completion
                    
                    # 获取评测结果
                    eval_results = self.browser.get_evaluation_results()
                    if eval_results:
                        results["steps"]["evaluation"]["results"] = eval_results
                else:
                    results["steps"]["evaluation"] = {
                        "status": "error",
                        "message": "点击运行评测按钮失败"
                    }
            
            # 步骤6: 分析结果
            logger.info("🔍 步骤6: 分析执行结果...")
            analysis_result = await self.core_analyzer.analyze(
                core_log_path=RPA_CONFIG["core_system"]["log_path"],
                eval_result=results.get("steps", {}).get("evaluation", {})
            )
            results["steps"]["analysis"] = analysis_result
            
            # 步骤7: 生成报告
            logger.info("📝 步骤7: 生成报告...")
            report_result = await self.report_generator.generate(
                run_id=run_id,
                results=results
            )
            results["steps"]["report"] = report_result
            results["report_path"] = report_result.get("report_path")
            
            results["status"] = "success"
            results["end_time"] = datetime.now().isoformat()
            
            logger.info(f"✅ 自动化循环完成: {run_id}")
            
        except Exception as e:
            logger.error(f"❌ 自动化循环失败: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            results["end_time"] = datetime.now().isoformat()
        
        finally:
            # 不立即关闭浏览器，让用户查看结果
            # self.browser.close_browser()
            pass
        
        return results
    
    def close(self):
        """关闭浏览器"""
        self.browser.close_browser()

