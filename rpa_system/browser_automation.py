"""
浏览器自动化模块
使用Selenium自动打开前端系统页面，点击按钮，监控执行结果
"""
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium未安装，浏览器自动化功能不可用。请运行: pip install selenium")

from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """浏览器自动化控制器"""
    
    def __init__(self, frontend_url: Optional[str] = None):
        """
        初始化浏览器自动化
        
        Args:
            frontend_url: 前端系统URL，默认从配置读取
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium未安装，无法使用浏览器自动化功能")
        
        self.frontend_url = frontend_url or self._get_frontend_url()
        self.driver = None
        self.wait_timeout = 30  # 等待元素出现的超时时间（秒）
        
    def _get_frontend_url(self) -> str:
        """获取前端系统URL"""
        # 默认前端URL（Vue开发服务器）
        # 可以从环境变量或配置文件读取
        import os
        return os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    def start_browser(self, headless: bool = False) -> bool:
        """
        启动浏览器
        
        Args:
            headless: 是否使用无头模式（不显示浏览器窗口）
            
        Returns:
            是否成功启动
        """
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 尝试创建Chrome驱动
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                logger.warning(f"Chrome驱动创建失败: {e}，尝试使用Firefox")
                try:
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions
                    firefox_options = FirefoxOptions()
                    if headless:
                        firefox_options.add_argument('--headless')
                    self.driver = webdriver.Firefox(options=firefox_options)
                except Exception as e2:
                    logger.error(f"Firefox驱动创建也失败: {e2}")
                    return False
            
            self.driver.implicitly_wait(10)  # 隐式等待10秒
            logger.info(f"✅ 浏览器启动成功: {self.driver.name}")
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return False
    
    def open_frontend_page(self) -> bool:
        """
        打开前端系统页面
        
        Returns:
            是否成功打开
        """
        try:
            if not self.driver:
                if not self.start_browser():
                    return False
            
            logger.info(f"🌐 打开前端页面: {self.frontend_url}")
            self.driver.get(self.frontend_url)
            
            # 等待页面加载完成
            time.sleep(3)
            
            # 检查页面是否加载成功
            if "RANGEN" in self.driver.title or "系统监控" in self.driver.page_source:
                logger.info("✅ 前端页面加载成功")
                return True
            else:
                logger.warning("⚠️ 前端页面可能未正确加载")
                return False
                
        except Exception as e:
            logger.error(f"打开前端页面失败: {e}")
            return False
    
    def set_sample_count(self, count: int) -> bool:
        """
        设置样本数量
        
        Args:
            count: 样本数量
            
        Returns:
            是否成功设置
        """
        try:
            # 等待输入框出现
            # 根据前端代码，输入框可能有多种选择器
            selectors = [
                "input[type='number']",
                ".el-input-number__input",
                "input.el-input__inner",
                "input[placeholder*='样本']",
            ]
            
            input_element = None
            for selector in selectors:
                try:
                    wait = WebDriverWait(self.driver, self.wait_timeout)
                    input_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_element:
                        break
                except TimeoutException:
                    continue
            
            if not input_element:
                logger.error("❌ 未找到样本数量输入框")
                return False
            
            # 清空并设置值
            input_element.clear()
            input_element.send_keys(str(count))
            time.sleep(0.5)  # 等待输入完成
            
            logger.info(f"✅ 样本数量已设置为: {count}")
            return True
            
        except Exception as e:
            logger.error(f"设置样本数量失败: {e}")
            return False
    
    def click_run_core_system_button(self) -> bool:
        """
        点击"运行核心系统"按钮
        
        Returns:
            是否成功点击
        """
        try:
            # 等待按钮出现
            # 根据前端代码，按钮可能有多种选择器
            selectors = [
                "button:contains('运行核心系统')",
                "button.el-button--success",
                "button[type='button']:contains('运行')",
                "//button[contains(text(), '运行核心系统')]",  # XPath
            ]
            
            button = None
            for selector in selectors:
                try:
                    wait = WebDriverWait(self.driver, self.wait_timeout)
                    if selector.startswith("//"):
                        # XPath选择器
                        button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS选择器
                        button = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if button:
                        break
                except TimeoutException:
                    continue
            
            if not button:
                logger.error("❌ 未找到'运行核心系统'按钮")
                return False
            
            # 检查按钮是否可用（未禁用）
            if not button.is_enabled():
                logger.warning("⚠️ '运行核心系统'按钮已禁用，可能正在运行中")
                return False
            
            # 点击按钮
            button.click()
            time.sleep(1)  # 等待点击响应
            
            logger.info("✅ 已点击'运行核心系统'按钮")
            return True
            
        except Exception as e:
            logger.error(f"点击'运行核心系统'按钮失败: {e}")
            return False
    
    def click_run_evaluation_button(self) -> bool:
        """
        点击"运行评测系统"按钮
        
        Returns:
            是否成功点击
        """
        try:
            # 等待按钮出现
            selectors = [
                "//button[contains(text(), '运行评测系统')]",  # XPath
                "button.el-button--primary",
                "button:contains('运行评测')",
            ]
            
            button = None
            for selector in selectors:
                try:
                    wait = WebDriverWait(self.driver, self.wait_timeout)
                    if selector.startswith("//"):
                        button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        button = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if button:
                        break
                except TimeoutException:
                    continue
            
            if not button:
                logger.error("❌ 未找到'运行评测系统'按钮")
                return False
            
            if not button.is_enabled():
                logger.warning("⚠️ '运行评测系统'按钮已禁用，可能正在运行中")
                return False
            
            button.click()
            time.sleep(1)
            
            logger.info("✅ 已点击'运行评测系统'按钮")
            return True
            
        except Exception as e:
            logger.error(f"点击'运行评测系统'按钮失败: {e}")
            return False
    
    def wait_for_task_completion(self, task_type: str = "core", timeout: int = 3600) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_type: 任务类型（"core"或"eval"）
            timeout: 超时时间（秒）
            
        Returns:
            任务完成状态信息
        """
        start_time = time.time()
        last_status = None
        
        try:
            while time.time() - start_time < timeout:
                # 检查任务状态
                # 可以通过检查按钮状态、进度条、日志等来判断
                status = self._check_task_status(task_type)
                
                if status != last_status:
                    logger.info(f"📊 任务状态: {status}")
                    last_status = status
                
                if status in ["completed", "failed"]:
                    return {
                        "status": status,
                        "duration": time.time() - start_time,
                        "message": f"任务{status}"
                    }
                
                time.sleep(5)  # 每5秒检查一次
            
            # 超时
            return {
                "status": "timeout",
                "duration": timeout,
                "message": f"任务超时（{timeout}秒）"
            }
            
        except Exception as e:
            logger.error(f"等待任务完成失败: {e}")
            return {
                "status": "error",
                "duration": time.time() - start_time,
                "message": str(e)
            }
    
    def _check_task_status(self, task_type: str) -> str:
        """
        检查任务状态
        
        Args:
            task_type: 任务类型
            
        Returns:
            任务状态（"running", "completed", "failed", "idle"）
        """
        try:
            # 检查按钮状态
            if task_type == "core":
                button_text = "运行核心系统"
            else:
                button_text = "运行评测系统"
            
            # 查找按钮
            try:
                button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{button_text}')]")
                button_text_content = button.text
                
                if "运行中" in button_text_content or button.get_attribute("disabled"):
                    return "running"
                else:
                    # 检查是否有完成或失败的提示
                    page_source = self.driver.page_source.lower()
                    if "完成" in page_source or "success" in page_source:
                        return "completed"
                    elif "失败" in page_source or "error" in page_source or "失败" in page_source:
                        return "failed"
                    else:
                        return "idle"
            except NoSuchElementException:
                return "unknown"
                
        except Exception as e:
            logger.debug(f"检查任务状态失败: {e}")
            return "unknown"
    
    def get_evaluation_results(self) -> Optional[Dict[str, Any]]:
        """
        获取评测结果
        
        Returns:
            评测结果数据
        """
        try:
            # 切换到评测结果标签页
            # 根据前端代码，可能需要点击"评测结果"标签
            try:
                eval_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '评测结果')]"))
                )
                eval_tab.click()
                time.sleep(2)  # 等待内容加载
            except TimeoutException:
                logger.warning("未找到评测结果标签页")
            
            # 提取评测结果
            # 这里可以根据实际的前端结构来提取数据
            page_source = self.driver.page_source
            
            # 尝试从页面中提取结果（简化实现）
            # 实际应该解析具体的DOM结构
            results = {
                "accuracy": None,
                "total_samples": None,
                "success_count": None,
                "failed_count": None,
            }
            
            # 这里可以添加更复杂的解析逻辑
            # 或者通过API直接获取结果
            
            return results
            
        except Exception as e:
            logger.error(f"获取评测结果失败: {e}")
            return None
    
    def take_screenshot(self, file_path: Optional[Path] = None) -> Optional[Path]:
        """
        截图
        
        Args:
            file_path: 保存路径，如果为None则自动生成
            
        Returns:
            截图文件路径
        """
        try:
            if not file_path:
                screenshots_dir = RPA_CONFIG["rpa"]["work_dir"] / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                file_path = screenshots_dir / f"screenshot_{int(time.time())}.png"
            
            self.driver.save_screenshot(str(file_path))
            logger.info(f"📸 截图已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("✅ 浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_browser()

