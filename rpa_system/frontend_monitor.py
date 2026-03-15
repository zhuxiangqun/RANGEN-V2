"""
前端系统监控和自动修复模块
"""
import asyncio
import logging
import subprocess
import socket
import http.client
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import RPA_CONFIG

try:
    from .frontend_page_checker import FrontendPageChecker, SELENIUM_AVAILABLE as PAGE_CHECKER_AVAILABLE
except ImportError:
    PAGE_CHECKER_AVAILABLE = False
    FrontendPageChecker = None

logger = logging.getLogger(__name__)


class FrontendMonitor:
    """前端系统监控和修复"""
    
    def __init__(self):
        self.config = RPA_CONFIG["frontend"]
        self.backend_path = self.config["backend_path"]
        self.frontend_path = self.config["frontend_path"]
        self.frontend_url = self.config.get("frontend_url", "http://localhost:5173")
        self.backend_url = self.config.get("backend_url", "http://localhost:5001")
        
        # 页面深度检查器（可选）
        self.page_checker = None
        if PAGE_CHECKER_AVAILABLE and FrontendPageChecker:
            try:
                self.page_checker = FrontendPageChecker(
                    frontend_url=self.frontend_url,
                    headless=True
                )
            except Exception as e:
                logger.warning(f"页面深度检查器初始化失败: {e}")
    
    async def check_and_fix(self) -> Dict[str, Any]:
        """
        检查前端系统状态，发现问题并自动修复
        
        Returns:
            检查结果，包含状态和发现的问题
        """
        issues = []
        
        # 检查1: 检查前端目录是否存在
        if not self.frontend_path.exists():
            issues.append({
                "type": "missing_directory",
                "severity": "high",
                "message": f"前端目录不存在: {self.frontend_path}",
                "fixable": False
            })
        
        # 检查2: 检查后端目录是否存在
        if not self.backend_path.exists():
            issues.append({
                "type": "missing_directory",
                "severity": "high",
                "message": f"后端目录不存在: {self.backend_path}",
                "fixable": False
            })
        
        # 检查3: 检查关键文件是否存在
        backend_app = self.backend_path / "app.py"
        if not backend_app.exists():
            issues.append({
                "type": "missing_file",
                "severity": "high",
                "message": f"后端主文件不存在: {backend_app}",
                "fixable": False
            })
        
        # 检查4: 检查Python语法错误
        if backend_app.exists():
            syntax_errors = await self._check_python_syntax(backend_app)
            if syntax_errors:
                issues.append({
                    "type": "syntax_error",
                    "severity": "high",
                    "message": f"Python语法错误: {syntax_errors}",
                    "fixable": True,
                    "details": syntax_errors
                })
        
        # 检查5: 检查依赖是否安装
        missing_deps = await self._check_dependencies()
        if missing_deps:
            issues.append({
                "type": "missing_dependencies",
                "severity": "medium",
                "message": f"缺少依赖: {', '.join(missing_deps)}",
                "fixable": True,
                "details": missing_deps
            })
        
        # 检查6: 检查前端服务是否运行
        frontend_service_status = await self._check_frontend_service()
        if not frontend_service_status["running"]:
            issues.append({
                "type": "service_not_running",
                "severity": "high",
                "message": f"前端服务未运行: {frontend_service_status.get('error', '无法连接')}",
                "fixable": True,
                "details": frontend_service_status
            })
        
        # 检查7: 检查后端服务是否运行
        backend_service_status = await self._check_backend_service()
        if not backend_service_status["running"]:
            issues.append({
                "type": "service_not_running",
                "severity": "high",
                "message": f"后端服务未运行: {backend_service_status.get('error', '无法连接')}",
                "fixable": True,
                "details": backend_service_status
            })
        
        # 检查8: 检查前端页面是否可访问
        if frontend_service_status.get("running"):
            page_status = await self._check_frontend_page()
            if not page_status["accessible"]:
                issues.append({
                    "type": "page_not_accessible",
                    "severity": "high",
                    "message": f"前端页面不可访问: {page_status.get('error', '未知错误')}",
                    "fixable": False,
                    "details": page_status
                })
        
        # 检查9: 检查后端API是否正常
        if backend_service_status.get("running"):
            api_status = await self._check_backend_api()
            if not api_status["working"]:
                issues.append({
                    "type": "api_error",
                    "severity": "high",
                    "message": f"后端API异常: {api_status.get('error', '未知错误')}",
                    "fixable": False,
                    "details": api_status
                })
        
        # 检查10: 检查端口是否被占用（但服务未运行）
        port_issues = await self._check_ports()
        if port_issues:
            issues.extend(port_issues)
        
        # 检查11-14: 深度页面检查（如果页面检查器可用且服务正在运行）
        if self.page_checker and frontend_service_status.get("running"):
            logger.info("🔍 开始深度页面检查...")
            try:
                page_check_results = await self.page_checker.run_all_checks()
                
                # 提取页面检查中的问题
                if page_check_results.get("all_issues"):
                    for page_issue in page_check_results["all_issues"]:
                        issues.append({
                            "type": f"page_{page_issue.get('type', 'unknown')}",
                            "severity": page_issue.get("severity", "medium"),
                            "message": page_issue.get("message", ""),
                            "details": page_issue.get("details", ""),
                            "source": "page_checker"
                        })
                
                # 将详细检查结果添加到返回结果中
                return {
                    "status": "ok" if not issues else "issues_found",
                    "issues": issues,
                    "checked_at": asyncio.get_event_loop().time(),
                    "page_check_results": page_check_results
                }
            except Exception as e:
                logger.warning(f"深度页面检查失败: {e}")
                issues.append({
                    "type": "page_check_error",
                    "severity": "low",
                    "message": f"深度页面检查失败: {str(e)}",
                    "fixable": False
                })
        
        status = "ok" if not issues else "issues_found"
        
        return {
            "status": status,
            "issues": issues,
            "checked_at": asyncio.get_event_loop().time()
        }
    
    async def auto_fix(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        自动修复发现的问题
        
        Args:
            issues: 发现的问题列表
            
        Returns:
            修复结果
        """
        fixes_applied = []
        fixes_failed = []
        
        for issue in issues:
            if not issue.get("fixable", False):
                fixes_failed.append({
                    "issue": issue,
                    "reason": "问题不可自动修复"
                })
                continue
            
            issue_type = issue.get("type")
            
            try:
                if issue_type == "syntax_error":
                    # 尝试修复语法错误（这里可以集成代码修复工具）
                    fix_result = await self._fix_syntax_errors(issue)
                    if fix_result["success"]:
                        fixes_applied.append({
                            "issue": issue,
                            "fix": fix_result
                        })
                    else:
                        fixes_failed.append({
                            "issue": issue,
                            "reason": fix_result.get("error", "修复失败")
                        })
                
                elif issue_type == "missing_dependencies":
                    # 安装缺失的依赖
                    fix_result = await self._install_dependencies(issue.get("details", []))
                    if fix_result["success"]:
                        fixes_applied.append({
                            "issue": issue,
                            "fix": fix_result
                        })
                    else:
                        fixes_failed.append({
                            "issue": issue,
                            "reason": fix_result.get("error", "安装依赖失败")
                        })
                
                elif issue_type == "service_not_running":
                    # 尝试启动服务
                    fix_result = await self._start_service(issue)
                    if fix_result["success"]:
                        fixes_applied.append({
                            "issue": issue,
                            "fix": fix_result
                        })
                    else:
                        fixes_failed.append({
                            "issue": issue,
                            "reason": fix_result.get("error", "启动服务失败")
                        })
                
            except Exception as e:
                logger.error(f"修复问题失败: {issue}, 错误: {e}")
                fixes_failed.append({
                    "issue": issue,
                    "reason": str(e)
                })
        
        return {
            "status": "success" if fixes_applied else "partial" if fixes_failed else "no_fixes",
            "fixes_applied": len(fixes_applied),
            "fixes_failed": len(fixes_failed),
            "details": {
                "applied": fixes_applied,
                "failed": fixes_failed
            }
        }
    
    async def _check_python_syntax(self, file_path: Path) -> List[str]:
        """检查Python文件语法"""
        try:
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "py_compile", str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                errors = stderr.decode('utf-8', errors='ignore')
                return [errors] if errors else ["未知语法错误"]
            
            return []
        except Exception as e:
            logger.error(f"检查语法错误失败: {e}")
            return [str(e)]
    
    async def _check_dependencies(self) -> List[str]:
        """检查缺失的依赖"""
        # 这里可以检查requirements.txt中的依赖
        # 简化实现：检查常见的依赖
        common_deps = ["flask", "flask-cors"]
        missing = []
        
        for dep in common_deps:
            try:
                process = await asyncio.create_subprocess_exec(
                    "python3", "-c", f"import {dep.replace('-', '_')}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                if process.returncode != 0:
                    missing.append(dep)
            except Exception:
                missing.append(dep)
        
        return missing
    
    async def _fix_syntax_errors(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """修复语法错误（占位实现）"""
        # 这里可以集成代码修复工具，如autopep8, black等
        # 或者使用LLM进行代码修复
        logger.warning(f"语法错误修复功能待实现: {issue}")
        return {
            "success": False,
            "error": "语法错误修复功能待实现"
        }
    
    async def _install_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """安装缺失的依赖"""
        try:
            cmd = ["pip", "install"] + dependencies
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"成功安装依赖: {', '.join(dependencies)}"
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode('utf-8', errors='ignore')
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_frontend_service(self) -> Dict[str, Any]:
        """检查前端服务是否运行"""
        try:
            parsed_url = urllib.parse.urlparse(self.frontend_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            # 尝试连接端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # 端口开放，尝试HTTP请求
                try:
                    conn = http.client.HTTPConnection(host, port, timeout=3)
                    conn.request("GET", "/")
                    response = conn.getresponse()
                    conn.close()
                    
                    if response.status in [200, 301, 302]:
                        return {
                            "running": True,
                            "status_code": response.status,
                            "message": "前端服务正常运行"
                        }
                    else:
                        return {
                            "running": False,
                            "error": f"HTTP状态码异常: {response.status}",
                            "status_code": response.status
                        }
                except Exception as e:
                    return {
                        "running": False,
                        "error": f"HTTP请求失败: {str(e)}"
                    }
            else:
                return {
                    "running": False,
                    "error": f"端口 {port} 未开放或服务未运行"
                }
        except Exception as e:
            return {
                "running": False,
                "error": f"检查失败: {str(e)}"
            }
    
    async def _check_backend_service(self) -> Dict[str, Any]:
        """检查后端服务是否运行"""
        try:
            parsed_url = urllib.parse.urlparse(self.backend_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            # 尝试连接端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # 端口开放，尝试API请求
                try:
                    conn = http.client.HTTPConnection(host, port, timeout=3)
                    conn.request("GET", "/api/health")  # 假设有健康检查端点
                    response = conn.getresponse()
                    conn.close()
                    
                    if response.status in [200, 404]:  # 404也算正常（端点不存在但服务运行）
                        return {
                            "running": True,
                            "status_code": response.status,
                            "message": "后端服务正常运行"
                        }
                    else:
                        return {
                            "running": False,
                            "error": f"HTTP状态码异常: {response.status}",
                            "status_code": response.status
                        }
                except Exception as e:
                    # 如果健康检查端点不存在，尝试根路径
                    try:
                        conn = http.client.HTTPConnection(host, port, timeout=3)
                        conn.request("GET", "/")
                        response = conn.getresponse()
                        conn.close()
                        
                        return {
                            "running": True,
                            "status_code": response.status,
                            "message": "后端服务正常运行（健康检查端点不存在）"
                        }
                    except:
                        return {
                            "running": False,
                            "error": f"HTTP请求失败: {str(e)}"
                        }
            else:
                return {
                    "running": False,
                    "error": f"端口 {port} 未开放或服务未运行"
                }
        except Exception as e:
            return {
                "running": False,
                "error": f"检查失败: {str(e)}"
            }
    
    async def _check_frontend_page(self) -> Dict[str, Any]:
        """检查前端页面是否可访问"""
        try:
            parsed_url = urllib.parse.urlparse(self.frontend_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            conn = http.client.HTTPConnection(host, port, timeout=5)
            conn.request("GET", "/")
            response = conn.getresponse()
            content = response.read().decode('utf-8', errors='ignore')
            conn.close()
            
            if response.status == 200:
                # 检查页面内容是否包含预期内容
                if "RANGEN" in content or "系统监控" in content or "Vue" in content:
                    return {
                        "accessible": True,
                        "status_code": response.status,
                        "message": "前端页面可正常访问"
                    }
                else:
                    return {
                        "accessible": False,
                        "error": "页面内容异常，未找到预期内容",
                        "status_code": response.status
                    }
            else:
                return {
                    "accessible": False,
                    "error": f"HTTP状态码异常: {response.status}",
                    "status_code": response.status
                }
        except Exception as e:
            return {
                "accessible": False,
                "error": f"访问失败: {str(e)}"
            }
    
    async def _check_backend_api(self) -> Dict[str, Any]:
        """检查后端API是否正常"""
        try:
            parsed_url = urllib.parse.urlparse(self.backend_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            # 尝试调用一个简单的API端点
            conn = http.client.HTTPConnection(host, port, timeout=5)
            conn.request("GET", "/api/logs")  # 尝试获取日志端点
            response = conn.getresponse()
            conn.close()
            
            if response.status in [200, 404]:  # 200正常，404也算正常（端点可能不存在）
                return {
                    "working": True,
                    "status_code": response.status,
                    "message": "后端API正常"
                }
            else:
                return {
                    "working": False,
                    "error": f"API返回异常状态码: {response.status}",
                    "status_code": response.status
                }
        except Exception as e:
            return {
                "working": False,
                "error": f"API调用失败: {str(e)}"
            }
    
    async def _check_ports(self) -> List[Dict[str, Any]]:
        """检查端口状态"""
        issues = []
        
        try:
            # 检查前端端口
            frontend_parsed = urllib.parse.urlparse(self.frontend_url)
            frontend_port = frontend_parsed.port or (443 if frontend_parsed.scheme == "https" else 80)
            
            # 检查后端端口
            backend_parsed = urllib.parse.urlparse(self.backend_url)
            backend_port = backend_parsed.port or (443 if backend_parsed.scheme == "https" else 80)
            
            # 这里可以添加更详细的端口检查逻辑
            # 比如检查端口是否被其他进程占用等
            
        except Exception as e:
            logger.debug(f"端口检查失败: {e}")
        
        return issues
    
    async def _start_service(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """尝试启动服务"""
        details = issue.get("details", {})
        error = details.get("error", "")
        
        # 判断是前端还是后端服务
        if "前端" in issue.get("message", ""):
            # 尝试启动前端服务
            return await self._start_frontend_service()
        elif "后端" in issue.get("message", ""):
            # 尝试启动后端服务
            return await self._start_backend_service()
        else:
            return {
                "success": False,
                "error": "无法确定服务类型"
            }
    
    async def _start_frontend_service(self) -> Dict[str, Any]:
        """启动前端服务"""
        try:
            # 检查是否有启动脚本
            start_script = self.frontend_path / "start.sh"
            if not start_script.exists():
                start_script = self.frontend_path / "package.json"
            
            if not start_script.exists():
                return {
                    "success": False,
                    "error": "未找到前端启动脚本"
                }
            
            # 这里可以添加启动逻辑
            # 由于启动服务是长期运行的过程，这里只返回提示
            return {
                "success": False,
                "error": "前端服务需要手动启动（npm run dev）",
                "suggestion": f"请在终端运行: cd {self.frontend_path} && npm run dev"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"启动前端服务失败: {str(e)}"
            }
    
    async def _start_backend_service(self) -> Dict[str, Any]:
        """启动后端服务"""
        try:
            backend_app = self.backend_path / "app.py"
            if not backend_app.exists():
                return {
                    "success": False,
                    "error": "后端主文件不存在"
                }
            
            # 这里可以添加启动逻辑
            # 由于启动服务是长期运行的过程，这里只返回提示
            return {
                "success": False,
                "error": "后端服务需要手动启动",
                "suggestion": f"请在终端运行: cd {self.backend_path} && python app.py"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"启动后端服务失败: {str(e)}"
            }

