"""
RPA系统核心控制器
负责协调各个模块，实现自动化运行、评测、修复和改进
"""
import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import RPA_CONFIG, PROJECT_ROOT
from .frontend_monitor import FrontendMonitor
from .core_analyzer import CoreSystemAnalyzer
from .report_generator import ReportGenerator
from .system_improver import SystemImprover

try:
    from .frontend_automation import FrontendAutomation, SELENIUM_AVAILABLE
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("前端自动化模块不可用（Selenium未安装）")

logger = logging.getLogger(__name__)


class RPAController:
    """RPA系统主控制器"""
    
    def __init__(self):
        self.config = RPA_CONFIG
        self.state_file = self.config["rpa"]["state_file"]
        self.state = self._load_state()
        
        # 初始化各个模块
        self.frontend_monitor = FrontendMonitor()
        self.core_analyzer = CoreSystemAnalyzer()
        self.report_generator = ReportGenerator()
        self.system_improver = SystemImprover()
        
        # 前端自动化（可选）
        self.frontend_automation = None
        if SELENIUM_AVAILABLE:
            try:
                self.frontend_automation = FrontendAutomation()
            except Exception as e:
                logger.warning(f"前端自动化初始化失败: {e}")
        
        # 运行状态
        self.is_running = False
        self.current_run_id = None
        
    def _load_state(self) -> Dict[str, Any]:
        """加载运行状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        return {
            "last_run_id": None,
            "total_runs": 0,
            "last_run_time": None,
            "current_config": {
                "sample_count": 10,
                "timeout": 1800.0,
            }
        }
    
    def _save_state(self):
        """保存运行状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    async def run_full_cycle(
        self, 
        sample_count: Optional[int] = None, 
        timeout: Optional[float] = None,
        use_frontend_automation: bool = False,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        运行完整的自动化循环：
        1. 检查前端系统
        2. 运行核心系统
        3. 运行评测
        4. 分析问题
        5. 生成报告
        """
        self.is_running = True
        self.current_run_id = f"run_{int(time.time())}"
        
        logger.info(f"🚀 开始RPA自动化循环: {self.current_run_id}")
        
        # 更新配置
        if sample_count:
            self.state["current_config"]["sample_count"] = sample_count
        if timeout:
            self.state["current_config"]["timeout"] = timeout
        
        results = {
            "run_id": self.current_run_id,
            "start_time": datetime.now().isoformat(),
            "config": self.state["current_config"].copy(),
            "steps": {}
        }
        
        try:
            # 步骤1: 检查并修复前端系统
            logger.info("📋 步骤1: 检查前端系统...")
            frontend_result = await self.frontend_monitor.check_and_fix()
            results["steps"]["frontend_check"] = frontend_result
            
            if not frontend_result.get("status") == "ok":
                logger.warning(f"⚠️ 前端系统检查发现问题: {frontend_result.get('issues')}")
                # 尝试自动修复
                fix_result = await self.frontend_monitor.auto_fix(frontend_result.get("issues", []))
                results["steps"]["frontend_fix"] = fix_result
            
            # 步骤2: 运行核心系统（通过前端自动化或直接运行）
            eval_result = {}
            if use_frontend_automation and self.frontend_automation:
                logger.info("🌐 步骤2: 通过前端自动化运行核心系统...")
                automation_result = await self.frontend_automation.run_full_automation_cycle(
                    sample_count=self.state["current_config"]["sample_count"],
                    wait_for_completion=True,
                    run_evaluation=True  # 前端自动化中包含评测
                )
                results["steps"]["frontend_automation"] = automation_result
                # 从自动化结果中提取核心系统结果
                core_result = automation_result.get("steps", {}).get("wait_completion", {})
                results["steps"]["core_system"] = core_result
                # 从自动化结果中提取评测结果
                eval_result = automation_result.get("steps", {}).get("evaluation", {})
                results["steps"]["evaluation"] = eval_result
            else:
                logger.info("🚀 步骤2: 直接运行核心系统...")
                core_result = await self._run_core_system(
                    sample_count=self.state["current_config"]["sample_count"],
                    timeout=self.state["current_config"]["timeout"]
                )
                results["steps"]["core_system"] = core_result
                
                # 步骤3: 运行评测（仅当不使用前端自动化时）
                logger.info("📊 步骤3: 运行评测...")
                eval_result = await self._run_evaluation()
                results["steps"]["evaluation"] = eval_result
            
            # 步骤4: 分析核心系统问题
            logger.info("🔍 步骤4: 分析核心系统问题...")
            analysis_result = await self.core_analyzer.analyze(
                core_log_path=self.config["core_system"]["log_path"],
                eval_result=eval_result
            )
            results["steps"]["analysis"] = analysis_result
            
            # 步骤5: 生成改进方案
            logger.info("🔧 步骤5: 生成改进方案...")
            improvement_result = await self.system_improver.analyze_and_improve(
                analysis_result=analysis_result,
                eval_result=eval_result
            )
            results["steps"]["improvements"] = improvement_result
            
            # 步骤6: 生成报告
            logger.info("📝 步骤6: 生成报告...")
            report_result = await self.report_generator.generate(
                run_id=self.current_run_id,
                results=results
            )
            results["steps"]["report"] = report_result
            results["report_path"] = report_result.get("report_path")
            
            # 更新状态
            self.state["last_run_id"] = self.current_run_id
            self.state["total_runs"] += 1
            self.state["last_run_time"] = datetime.now().isoformat()
            self._save_state()
            
            results["end_time"] = datetime.now().isoformat()
            results["status"] = "success"
            
            logger.info(f"✅ RPA自动化循环完成: {self.current_run_id}")
            
        except Exception as e:
            logger.error(f"❌ RPA自动化循环失败: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            results["end_time"] = datetime.now().isoformat()
        
        finally:
            self.is_running = False
        
        return results
    
    async def _run_core_system(self, sample_count: int, timeout: float) -> Dict[str, Any]:
        """运行核心系统"""
        script_path = self.config["core_system"]["script_path"]
        log_path = self.config["core_system"]["log_path"]
        
        # 清空之前的日志（可选）
        # if log_path.exists():
        #     log_path.unlink()
        
        cmd = [
            "python3",
            str(script_path),
            "--sample-count", str(sample_count),
        ]
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT)
            )
            
            # 等待完成或超时
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                return_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "status": "timeout",
                    "error": f"核心系统运行超时（{timeout}秒）",
                    "duration": timeout
                }
            
            duration = time.time() - start_time
            
            return {
                "status": "success" if return_code == 0 else "error",
                "return_code": return_code,
                "duration": duration,
                "stdout": stdout.decode('utf-8', errors='ignore')[:1000],  # 限制长度
                "stderr": stderr.decode('utf-8', errors='ignore')[:1000],
                "log_path": str(log_path),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def _run_evaluation(self) -> Dict[str, Any]:
        """运行评测系统"""
        script_path = self.config["evaluation_system"]["script_path"]
        
        cmd = [
            "python3",
            str(script_path),
        ]
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT)
            )
            
            stdout, stderr = await process.communicate()
            return_code = process.returncode
            duration = time.time() - start_time
            
            return {
                "status": "success" if return_code == 0 else "error",
                "return_code": return_code,
                "duration": duration,
                "stdout": stdout.decode('utf-8', errors='ignore')[:2000],
                "stderr": stderr.decode('utf-8', errors='ignore')[:2000],
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "is_running": self.is_running,
            "current_run_id": self.current_run_id,
            "state": self.state,
        }
    
    def update_config(self, sample_count: Optional[int] = None, 
                     timeout: Optional[float] = None):
        """更新运行配置"""
        if sample_count:
            self.state["current_config"]["sample_count"] = sample_count
        if timeout:
            self.state["current_config"]["timeout"] = timeout
        self._save_state()

