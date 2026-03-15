"""
前端页面深度检查模块
使用浏览器自动化检查前端系统的各种问题
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        WebDriverException, StaleElementReferenceException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium未安装，前端页面深度检查功能不可用")

from .config import RPA_CONFIG

logger = logging.getLogger(__name__)


class FrontendPageChecker:
    """前端页面深度检查器"""
    
    def __init__(self, frontend_url: Optional[str] = None, headless: bool = True):
        """
        初始化页面检查器
        
        Args:
            frontend_url: 前端系统URL
            headless: 是否使用无头模式
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium未安装，无法使用前端页面检查功能")
        
        self.frontend_url = frontend_url or RPA_CONFIG["frontend"].get("frontend_url", "http://localhost:5173")
        self.headless = headless
        self.driver = None
        self.visited_urls: Set[str] = set()  # 已访问的URL，避免重复检查
        self.max_depth = 3  # 最大爬取深度
        self.timeout = 10  # 页面加载超时时间（秒）
        
    def _init_driver(self) -> bool:
        """初始化浏览器驱动"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(5)
            return True
        except Exception as e:
            logger.error(f"初始化浏览器驱动失败: {e}")
            return False
    
    def _close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    async def check_all_links(self) -> Dict[str, Any]:
        """
        检查1: 检查所有可点击的链接
        
        检查范围：
        - 首页所有链接
        - 导航栏链接
        - 服务栏目链接
        - 办事指南内链
        - "一件事"专区链接
        - 所有平台模块链接
        
        Returns:
            检查结果
        """
        if not self.driver:
            if not self._init_driver():
                return {
                    "status": "error",
                    "error": "无法初始化浏览器驱动"
                }
        
        issues = []
        checked_links = []
        
        try:
            # 访问首页
            logger.info(f"🌐 访问首页: {self.frontend_url}")
            self.driver.get(self.frontend_url)
            await asyncio.sleep(2)  # 等待页面加载
            
            # 收集所有链接
            all_links = self._collect_all_links()
            logger.info(f"📋 找到 {len(all_links)} 个链接")
            
            # 检查每个链接
            for link_info in all_links:
                link_result = await self._check_single_link(link_info)
                checked_links.append(link_result)
                
                if link_result["status"] != "ok":
                    issues.append({
                        "type": "link_issue",
                        "severity": "high" if link_result["status"] == "error" else "medium",
                        "link_text": link_info.get("text", ""),
                        "link_url": link_info.get("url", ""),
                        "issue": link_result["status"],
                        "details": link_result.get("details", "")
                    })
            
            return {
                "status": "completed",
                "total_links": len(all_links),
                "checked_links": len(checked_links),
                "issues": issues,
                "details": checked_links
            }
            
        except Exception as e:
            logger.error(f"检查链接失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _collect_all_links(self) -> List[Dict[str, Any]]:
        """收集页面中的所有链接"""
        links = []
        
        try:
            # 查找所有a标签
            a_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for element in a_elements:
                try:
                    href = element.get_attribute("href")
                    text = element.text.strip()
                    
                    if href and href not in self.visited_urls:
                        # 处理相对路径
                        if href.startswith("/"):
                            href = urljoin(self.frontend_url, href)
                        elif not href.startswith("http"):
                            continue  # 跳过javascript:、mailto:等
                        
                        links.append({
                            "text": text or href,
                            "url": href,
                            "element": element
                        })
                        self.visited_urls.add(href)
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"收集链接时出错: {e}")
            
            # 查找所有按钮（可能包含跳转功能）
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    onclick = button.get_attribute("onclick")
                    if onclick and "window.location" in onclick or "href" in onclick:
                        text = button.text.strip()
                        links.append({
                            "text": text or "按钮",
                            "url": onclick,
                            "element": button,
                            "type": "button"
                        })
                except:
                    continue
            
        except Exception as e:
            logger.error(f"收集链接失败: {e}")
        
        return links
    
    async def _check_single_link(self, link_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查单个链接"""
        url = link_info.get("url", "")
        text = link_info.get("text", "")
        
        try:
            # 检查链接类型
            if url.startswith("javascript:") or url.startswith("mailto:") or url.startswith("#"):
                return {
                    "status": "skipped",
                    "url": url,
                    "text": text,
                    "reason": "非HTTP链接"
                }
            
            # 尝试访问链接
            original_url = self.driver.current_url
            
            try:
                # 在新标签页中打开链接（避免影响当前页面）
                self.driver.execute_script(f"window.open('{url}', '_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # 等待页面加载
                wait = WebDriverWait(self.driver, self.timeout)
                wait.until(lambda d: d.ready_state == "complete")
                
                await asyncio.sleep(1)  # 额外等待1秒
                
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                # 检查页面状态
                issues = []
                
                # 检查1: 404错误
                if "404" in page_source or "not found" in page_source.lower() or "页面不存在" in page_source:
                    issues.append("404错误")
                
                # 检查2: 空白页面
                if len(page_source.strip()) < 100:  # 页面内容太少
                    issues.append("空白页面")
                
                # 检查3: 错误页面
                error_keywords = ["error", "错误", "exception", "异常", "crash", "崩溃"]
                if any(keyword in page_source.lower() for keyword in error_keywords):
                    issues.append("错误页面")
                
                # 检查4: 加载超时（已经在wait中处理）
                
                # 关闭标签页，返回原页面
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                if issues:
                    return {
                        "status": "error",
                        "url": url,
                        "text": text,
                        "details": ", ".join(issues),
                        "current_url": current_url
                    }
                else:
                    return {
                        "status": "ok",
                        "url": url,
                        "text": text,
                        "current_url": current_url
                    }
                    
            except TimeoutException:
                # 关闭可能打开的标签页
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                return {
                    "status": "error",
                    "url": url,
                    "text": text,
                    "details": "加载超时"
                }
            except Exception as e:
                # 关闭可能打开的标签页
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                return {
                    "status": "error",
                    "url": url,
                    "text": text,
                    "details": f"访问失败: {str(e)}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "text": text,
                "details": f"检查失败: {str(e)}"
            }
    
    async def check_application_health(self) -> Dict[str, Any]:
        """
        检查2: 检查所有应用是否存在崩溃、无响应、页面空白、加载超时等问题
        
        Returns:
            检查结果
        """
        if not self.driver:
            if not self._init_driver():
                return {
                    "status": "error",
                    "error": "无法初始化浏览器驱动"
                }
        
        issues = []
        
        try:
            # 访问首页
            self.driver.get(self.frontend_url)
            await asyncio.sleep(2)
            
            # 检查浏览器控制台错误
            console_errors = self._get_console_errors()
            if console_errors:
                issues.append({
                    "type": "console_errors",
                    "severity": "high",
                    "message": f"发现 {len(console_errors)} 个控制台错误",
                    "details": console_errors
                })
            
            # 检查页面加载时间
            load_time = self._get_page_load_time()
            if load_time > 10:  # 超过10秒认为加载超时
                issues.append({
                    "type": "slow_load",
                    "severity": "medium",
                    "message": f"页面加载时间过长: {load_time:.2f}秒",
                    "load_time": load_time
                })
            
            # 检查页面是否空白
            if self._is_page_blank():
                issues.append({
                    "type": "blank_page",
                    "severity": "high",
                    "message": "页面内容为空"
                })
            
            # 检查是否有JavaScript错误
            js_errors = self._check_javascript_errors()
            if js_errors:
                issues.append({
                    "type": "javascript_errors",
                    "severity": "high",
                    "message": f"发现 {len(js_errors)} 个JavaScript错误",
                    "details": js_errors
                })
            
            return {
                "status": "completed",
                "issues": issues,
                "load_time": load_time,
                "console_errors": console_errors,
                "javascript_errors": js_errors
            }
            
        except Exception as e:
            logger.error(f"检查应用健康状态失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_console_errors(self) -> List[str]:
        """获取浏览器控制台错误"""
        errors = []
        try:
            logs = self.driver.get_log('browser')
            for log in logs:
                if log['level'] == 'SEVERE':
                    errors.append(log['message'])
        except:
            pass
        return errors
    
    def _get_page_load_time(self) -> float:
        """获取页面加载时间"""
        try:
            navigation_timing = self.driver.execute_script(
                "return window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;"
            )
            return navigation_timing / 1000.0  # 转换为秒
        except:
            return 0.0
    
    def _is_page_blank(self) -> bool:
        """检查页面是否空白"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = body.text.strip()
            return len(text) < 50  # 内容太少认为是空白
        except:
            return True
    
    def _check_javascript_errors(self) -> List[str]:
        """检查JavaScript错误"""
        errors = []
        try:
            # 检查是否有未捕获的异常
            js_code = """
            var errors = [];
            window.addEventListener('error', function(e) {
                errors.push(e.message + ' at ' + e.filename + ':' + e.lineno);
            });
            return errors;
            """
            errors = self.driver.execute_script(js_code)
        except:
            pass
        return errors
    
    async def check_page_layout(self) -> Dict[str, Any]:
        """
        检查3: 检查页面布局问题
        
        检查项：
        - 是否需要横向滚动
        - 元素是否过小
        - 响应式布局问题
        
        Returns:
            检查结果
        """
        if not self.driver:
            if not self._init_driver():
                return {
                    "status": "error",
                    "error": "无法初始化浏览器驱动"
                }
        
        issues = []
        
        try:
            # 访问首页
            self.driver.get(self.frontend_url)
            await asyncio.sleep(2)
            
            # 检查横向滚动
            has_horizontal_scroll = self._check_horizontal_scroll()
            if has_horizontal_scroll:
                issues.append({
                    "type": "horizontal_scroll",
                    "severity": "medium",
                    "message": "页面需要横向滚动，可能影响用户体验"
                })
            
            # 检查元素大小
            small_elements = self._check_small_elements()
            if small_elements:
                issues.append({
                    "type": "small_elements",
                    "severity": "medium",
                    "message": f"发现 {len(small_elements)} 个过小的元素",
                    "details": small_elements
                })
            
            # 检查响应式布局
            responsive_issues = self._check_responsive_layout()
            if responsive_issues:
                issues.extend(responsive_issues)
            
            return {
                "status": "completed",
                "issues": issues,
                "has_horizontal_scroll": has_horizontal_scroll,
                "small_elements_count": len(small_elements) if small_elements else 0
            }
            
        except Exception as e:
            logger.error(f"检查页面布局失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _check_horizontal_scroll(self) -> bool:
        """检查是否需要横向滚动"""
        try:
            scroll_width = self.driver.execute_script("return document.documentElement.scrollWidth;")
            client_width = self.driver.execute_script("return document.documentElement.clientWidth;")
            return scroll_width > client_width
        except:
            return False
    
    def _check_small_elements(self) -> List[Dict[str, Any]]:
        """检查过小的元素"""
        small_elements = []
        try:
            # 检查所有可点击元素
            clickable_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a, button, input[type='button'], input[type='submit']"
            )
            
            for element in clickable_elements:
                try:
                    size = element.size
                    if size['width'] < 44 or size['height'] < 44:  # 最小触摸目标44x44px
                        small_elements.append({
                            "tag": element.tag_name,
                            "text": element.text[:50],
                            "size": f"{size['width']}x{size['height']}"
                        })
                except:
                    continue
        except:
            pass
        return small_elements
    
    def _check_responsive_layout(self) -> List[Dict[str, Any]]:
        """检查响应式布局问题"""
        issues = []
        try:
            # 测试不同屏幕尺寸
            test_sizes = [
                (375, 667),   # iPhone
                (768, 1024),  # iPad
                (1920, 1080)  # Desktop
            ]
            
            for width, height in test_sizes:
                self.driver.set_window_size(width, height)
                await asyncio.sleep(1)
                
                # 检查是否需要横向滚动
                if self._check_horizontal_scroll():
                    issues.append({
                        "type": "responsive_issue",
                        "severity": "medium",
                        "message": f"在 {width}x{height} 分辨率下需要横向滚动"
                    })
        except Exception as e:
            logger.debug(f"检查响应式布局失败: {e}")
        
        return issues
    
    async def check_button_navigation(self) -> Dict[str, Any]:
        """
        检查4: 检查按钮跳转问题
        
        检查项：
        - 按钮是否可正常跳转至申报页面
        - 是否有404、错链、空链、卡顿等问题
        
        Returns:
            检查结果
        """
        if not self.driver:
            if not self._init_driver():
                return {
                    "status": "error",
                    "error": "无法初始化浏览器驱动"
                }
        
        issues = []
        checked_buttons = []
        
        try:
            # 访问首页
            self.driver.get(self.frontend_url)
            await asyncio.sleep(2)
            
            # 查找所有按钮
            buttons = self._find_all_buttons()
            logger.info(f"📋 找到 {len(buttons)} 个按钮")
            
            # 检查每个按钮
            for button_info in buttons:
                button_result = await self._check_single_button(button_info)
                checked_buttons.append(button_result)
                
                if button_result["status"] != "ok":
                    issues.append({
                        "type": "button_issue",
                        "severity": "high" if button_result["status"] == "error" else "medium",
                        "button_text": button_info.get("text", ""),
                        "issue": button_result["status"],
                        "details": button_result.get("details", "")
                    })
            
            return {
                "status": "completed",
                "total_buttons": len(buttons),
                "checked_buttons": len(checked_buttons),
                "issues": issues,
                "details": checked_buttons
            }
            
        except Exception as e:
            logger.error(f"检查按钮跳转失败: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _find_all_buttons(self) -> List[Dict[str, Any]]:
        """查找所有按钮"""
        buttons = []
        
        try:
            # 查找button标签
            button_elements = self.driver.find_elements(By.TAG_NAME, "button")
            for element in button_elements:
                try:
                    text = element.text.strip()
                    onclick = element.get_attribute("onclick")
                    href = element.get_attribute("href")
                    
                    buttons.append({
                        "text": text or "按钮",
                        "element": element,
                        "onclick": onclick,
                        "href": href
                    })
                except:
                    continue
            
            # 查找input[type="button"]和input[type="submit"]
            input_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "input[type='button'], input[type='submit']"
            )
            for element in input_buttons:
                try:
                    text = element.get_attribute("value") or element.text.strip()
                    onclick = element.get_attribute("onclick")
                    
                    buttons.append({
                        "text": text or "按钮",
                        "element": element,
                        "onclick": onclick
                    })
                except:
                    continue
            
            # 查找带有按钮样式的链接
            styled_links = self.driver.find_elements(
                By.CSS_SELECTOR, "a[class*='button'], a[class*='btn']"
            )
            for element in styled_links:
                try:
                    text = element.text.strip()
                    href = element.get_attribute("href")
                    
                    if href and href not in [b.get("href") for b in buttons]:
                        buttons.append({
                            "text": text or href,
                            "element": element,
                            "href": href
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"查找按钮失败: {e}")
        
        return buttons
    
    async def _check_single_button(self, button_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查单个按钮"""
        text = button_info.get("text", "")
        element = button_info.get("element")
        
        try:
            # 检查按钮是否可见和可点击
            if not element.is_displayed():
                return {
                    "status": "warning",
                    "button_text": text,
                    "details": "按钮不可见"
                }
            
            if not element.is_enabled():
                return {
                    "status": "warning",
                    "button_text": text,
                    "details": "按钮已禁用"
                }
            
            # 记录点击前URL
            original_url = self.driver.current_url
            
            # 点击按钮
            start_time = time.time()
            element.click()
            
            # 等待页面变化或跳转
            await asyncio.sleep(2)
            
            # 检查是否有跳转
            current_url = self.driver.current_url
            load_time = time.time() - start_time
            
            # 检查加载时间（卡顿）
            if load_time > 5:
                return {
                    "status": "error",
                    "button_text": text,
                    "details": f"点击后响应时间过长: {load_time:.2f}秒（可能卡顿）"
                }
            
            # 检查是否跳转到新页面
            if current_url != original_url:
                # 检查新页面状态
                page_source = self.driver.page_source
                
                # 检查404
                if "404" in page_source or "not found" in page_source.lower():
                    # 返回原页面
                    self.driver.back()
                    await asyncio.sleep(1)
                    
                    return {
                        "status": "error",
                        "button_text": text,
                        "details": "跳转后出现404错误",
                        "target_url": current_url
                    }
                
                # 检查空白页面
                if len(page_source.strip()) < 100:
                    # 返回原页面
                    self.driver.back()
                    await asyncio.sleep(1)
                    
                    return {
                        "status": "error",
                        "button_text": text,
                        "details": "跳转后页面空白",
                        "target_url": current_url
                    }
                
                # 返回原页面
                self.driver.back()
                await asyncio.sleep(1)
                
                return {
                    "status": "ok",
                    "button_text": text,
                    "target_url": current_url,
                    "load_time": load_time
                }
            else:
                # 没有跳转，可能是表单提交或其他操作
                return {
                    "status": "ok",
                    "button_text": text,
                    "details": "按钮点击成功（无页面跳转）",
                    "load_time": load_time
                }
                
        except TimeoutException:
            return {
                "status": "error",
                "button_text": text,
                "details": "点击后加载超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "button_text": text,
                "details": f"点击失败: {str(e)}"
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        results = {
            "start_time": time.time(),
            "checks": {}
        }
        
        try:
            # 检查1: 所有链接
            logger.info("🔍 开始检查1: 所有链接...")
            results["checks"]["links"] = await self.check_all_links()
            
            # 检查2: 应用健康状态
            logger.info("🔍 开始检查2: 应用健康状态...")
            results["checks"]["application_health"] = await self.check_application_health()
            
            # 检查3: 页面布局
            logger.info("🔍 开始检查3: 页面布局...")
            results["checks"]["page_layout"] = await self.check_page_layout()
            
            # 检查4: 按钮跳转
            logger.info("🔍 开始检查4: 按钮跳转...")
            results["checks"]["button_navigation"] = await self.check_button_navigation()
            
            # 汇总所有问题
            all_issues = []
            for check_name, check_result in results["checks"].items():
                if isinstance(check_result, dict) and "issues" in check_result:
                    all_issues.extend(check_result["issues"])
            
            results["total_issues"] = len(all_issues)
            results["all_issues"] = all_issues
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            results["status"] = "completed" if not all_issues else "issues_found"
            
        except Exception as e:
            logger.error(f"运行所有检查失败: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
        finally:
            self._close_driver()
        
        return results
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._close_driver()

