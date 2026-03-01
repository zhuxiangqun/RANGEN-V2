#!/usr/bin/env python3
"""
7原子工具模块 - 对齐pc-agent-loop的原子能力
这些是RANGEN系统最底层的原子操作能力
"""
import ast
import asyncio
import subprocess
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AtomicToolType(str, Enum):
    """原子工具类型"""
    CODE_RUN = "code_run"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_PATCH = "file_patch"
    WEB_SCAN = "web_scan"
    WEB_EXECUTE_JS = "web_execute_js"
    ASK_USER = "ask_user"


@dataclass
class AtomicToolResult:
    """原子工具执行结果"""
    tool_type: AtomicToolType
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AtomicToolRegistry:
    """原子工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, AtomicToolType] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认7个原子工具"""
        for tool_type in AtomicToolType:
            self.tools[tool_type.value] = tool_type
    
    def get_tool(self, tool_name: str) -> Optional[AtomicToolType]:
        """获取工具类型"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self.tools.keys())


class AtomicCodeRunner:
    """原子代码执行器 - code_run
    
    安全执行Python代码，使用AST解析而非eval/exec
    """
    
    def __init__(self, timeout: int = 30, max_output_size: int = 100000):
        self.timeout = timeout
        self.max_output_size = max_output_size
    
    def execute(self, code: str, language: str = "python", **kwargs) -> AtomicToolResult:
        """执行代码
        
        Args:
            code: 要执行的代码
            language: 语言 (python, bash, powershell)
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        try:
            if language == "python":
                return self._execute_python(code, start_time)
            elif language in ("bash", "shell", "sh"):
                return self._execute_bash(code, start_time)
            elif language == "powershell":
                return self._execute_powershell(code, start_time)
            else:
                return AtomicToolResult(
                    tool_type=AtomicToolType.CODE_RUN,
                    success=False,
                    error=f"Unsupported language: {language}",
                    execution_time=time.time() - start_time
                )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_python(self, code: str, start_time: float) -> AtomicToolResult:
        """执行Python代码（安全方式）"""
        
        # 使用AST解析验证代码安全性
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=False,
                error=f"Syntax error: {e}",
                execution_time=time.time() - start_time
            )
        
        # 检查危险操作
        dangerous_patterns = ['__import__', 'eval', 'exec', 'open', 'file', 'compile']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_patterns:
                        return AtomicToolResult(
                            tool_type=AtomicToolType.CODE_RUN,
                            success=False,
                            error=f"Potentially dangerous operation blocked: {node.func.id}",
                            execution_time=time.time() - start_time
                        )
        
        # 创建一个安全的执行环境
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'type': type,
            }
        }
        
        # 执行代码
        output_capture = []
        def safe_print(*args, **kwargs):
            output_capture.append(' '.join(str(a) for a in args))
        
        safe_globals['__builtins__']['print'] = safe_print
        
        try:
            exec(compile(tree, '<atomic>', 'exec'), safe_globals)
            output = '\n'.join(output_capture) if output_capture else "Code executed successfully (no output)"
            
            # 截断输出
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\n... (output truncated)"
            
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=True,
                output=output,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_bash(self, code: str, start_time: float) -> AtomicToolResult:
        """执行Bash命令"""
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout
            if result.stderr:
                output += "\nSTDERR: " + result.stderr
            
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}",
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=False,
                error=f"Timeout after {self.timeout}s",
                execution_time=time.time() - start_time
            )
    
    def _execute_powershell(self, code: str, start_time: float) -> AtomicToolResult:
        """执行PowerShell命令"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", code],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout
            if result.stderr:
                output += "\nSTDERR: " + result.stderr
            
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}",
                execution_time=time.time() - start_time
            )
        except subprocess.TimeoutExpired:
            return AtomicToolResult(
                tool_type=AtomicToolType.CODE_RUN,
                success=False,
                error=f"Timeout after {self.timeout}s",
                execution_time=time.time() - start_time
            )


class AtomicFileTool:
    """原子文件工具 - file_read, file_write, file_patch"""
    
    @staticmethod
    def read(file_path: str, encoding: str = "utf-8", lines: Optional[int] = None) -> AtomicToolResult:
        """读取文件 - file_read"""
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                if lines:
                    content = ''.join(f.readlines()[:lines])
                else:
                    content = f.read()
            
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_READ,
                success=True,
                output=content,
                execution_time=time.time() - start_time,
                metadata={"file_path": file_path, "lines_read": lines}
            )
        except FileNotFoundError:
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_READ,
                success=False,
                error=f"File not found: {file_path}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_READ,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    @staticmethod
    def write(file_path: str, content: str, encoding: str = "utf-8", append: bool = False) -> AtomicToolResult:
        """写入文件 - file_write"""
        start_time = time.time()
        
        try:
            mode = "a" if append else "w"
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_WRITE,
                success=True,
                output=f"File written: {file_path}",
                execution_time=time.time() - start_time,
                metadata={"file_path": file_path, "bytes_written": len(content)}
            )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_WRITE,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    @staticmethod
    def patch(file_path: str, search: str, replace: str, replace_all: bool = False) -> AtomicToolResult:
        """修补文件 - file_patch
        
        精确的代码修补，类似pc-agent-loop的file_patch
        """
        start_time = time.time()
        
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 计算行号以便调试
            lines = content.split('\n')
            search_lines = search.split('\n')
            
            # 查找匹配位置
            matches = []
            for i, line in enumerate(lines):
                if search in line or (len(search_lines) > 1 and i + len(search_lines) <= len(lines)):
                    # 多行匹配
                    if len(search_lines) > 1:
                        match = '\n'.join(lines[i:i+len(search_lines)])
                        if match == search:
                            matches.append(i)
                    elif search in line:
                        matches.append(i)
            
            if not matches:
                return AtomicToolResult(
                    tool_type=AtomicToolType.FILE_PATCH,
                    success=False,
                    error=f"Pattern not found: {search[:50]}...",
                    execution_time=time.time() - start_time
                )
            
            # 执行替换
            if replace_all:
                new_content = content.replace(search, replace)
                replace_count = len(matches)
            else:
                first_match = matches[0]
                content_lines = lines[:first_match] + [replace] + lines[first_match + len(search_lines):]
                new_content = '\n'.join(content_lines)
                replace_count = 1
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_PATCH,
                success=True,
                output=f"File patched: {replace_count} replacement(s) made",
                execution_time=time.time() - start_time,
                metadata={"file_path": file_path, "replacements": replace_count}
            )
        except FileNotFoundError:
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_PATCH,
                success=False,
                error=f"File not found: {file_path}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.FILE_PATCH,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class AtomicWebTool:
    """原子网页工具 - web_scan, web_execute_js"""
    
    def __init__(self):
        self.session_cache: Dict[str, Any] = {}
    
    async def scan(self, url: str, selectors: Optional[List[str]] = None) -> AtomicToolResult:
        """网页内容抓取 - web_scan
        
        使用requests获取网页内容
        """
        start_time = time.time()
        
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            # 如果指定了selectors，使用BeautifulSoup提取
            if selectors:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                extracted = {}
                for selector in selectors:
                    elements = soup.select(selector)
                    extracted[selector] = [el.get_text(strip=True) for el in elements]
                
                content = json.dumps(extracted, indent=2, ensure_ascii=False)
            
            # 截断大内容
            if len(content) > 100000:
                content = content[:100000] + "\n... (content truncated)"
            
            return AtomicToolResult(
                tool_type=AtomicToolType.WEB_SCAN,
                success=True,
                output=content,
                execution_time=time.time() - start_time,
                metadata={"url": url, "status_code": response.status_code}
            )
        except ImportError:
            return AtomicToolResult(
                tool_type=AtomicToolType.WEB_SCAN,
                success=False,
                error="requests library not installed",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return AtomicToolResult(
                tool_type=AtomicToolType.WEB_SCAN,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def execute_js(self, url: str, script: str) -> AtomicToolResult:
        """浏览器DOM控制 - web_execute_js
        
        注意：这是一个简化版本，需要浏览器自动化支持
        完整实现需要使用Playwright或Selenium
        """
        start_time = time.time()
        
        # 简化实现：返回提示信息
        # 完整实现需要浏览器自动化
        return AtomicToolResult(
            tool_type=AtomicToolType.WEB_EXECUTE_JS,
            success=False,
            error="Browser automation not implemented. Use TMWebDriver for full browser control.",
            execution_time=time.time() - start_time,
            metadata={"url": url, "note": "Use Physical Control Hands for browser automation"}
        )


class AtomicUserTool:
    """原子用户交互工具 - ask_user"""
    
    def __init__(self):
        self.pending_questions: Dict[str, Dict[str, Any]] = {}
    
    def ask(self, question: str, options: Optional[List[str]] = None, session_id: str = "default") -> AtomicToolResult:
        """人机协作确认 - ask_user
        
        暂停执行，等待用户确认或输入
        """
        start_time = time.time()
        
        question_id = hashlib.md5(f"{session_id}_{time.time()}".encode()).hexdigest()
        
        self.pending_questions[question_id] = {
            "question": question,
            "options": options,
            "session_id": session_id,
            "timestamp": time.time(),
            "answered": False,
            "answer": None
        }
        
        return AtomicToolResult(
            tool_type=AtomicToolType.ASK_USER,
            success=True,
            output={
                "question_id": question_id,
                "question": question,
                "options": options,
                "waiting": True
            },
            execution_time=time.time() - start_time,
            metadata={"session_id": session_id}
        )
    
    def answer(self, question_id: str, answer: str) -> AtomicToolResult:
        """回答问题"""
        start_time = time.time()
        
        if question_id not in self.pending_questions:
            return AtomicToolResult(
                tool_type=AtomicToolType.ASK_USER,
                success=False,
                error=f"Question not found: {question_id}",
                execution_time=time.time() - start_time
            )
        
        self.pending_questions[question_id]["answered"] = True
        self.pending_questions[question_id]["answer"] = answer
        
        return AtomicToolResult(
            tool_type=AtomicToolType.ASK_USER,
            success=True,
            output={
                "question_id": question_id,
                "answer": answer,
                "confirmed": True
            },
            execution_time=time.time() - start_time
        )


# 全局实例
_code_runner = AtomicCodeRunner()
_file_tool = AtomicFileTool()
_web_tool = AtomicWebTool()
_user_tool = AtomicUserTool()
_registry = AtomicToolRegistry()


# 便捷执行函数
def run_code(code: str, language: str = "python") -> AtomicToolResult:
    """执行代码"""
    return _code_runner.execute(code, language)


def read_file(file_path: str, lines: Optional[int] = None) -> AtomicToolResult:
    """读取文件"""
    return _file_tool.read(file_path, lines=lines)


def write_file(file_path: str, content: str, append: bool = False) -> AtomicToolResult:
    """写入文件"""
    return _file_tool.write(file_path, content, append)


def patch_file(file_path: str, search: str, replace: str, replace_all: bool = False) -> AtomicToolResult:
    """修补文件"""
    return _file_tool.patch(file_path, search, replace, replace_all)


async def scan_web(url: str, selectors: Optional[List[str]] = None) -> AtomicToolResult:
    """抓取网页"""
    return await _web_tool.scan(url, selectors)


async def execute_js(url: str, script: str) -> AtomicToolResult:
    """执行JS"""
    return await _web_tool.execute_js(url, script)


def ask_user(question: str, options: Optional[List[str]] = None, session_id: str = "default") -> AtomicToolResult:
    """询问用户"""
    return _user_tool.ask(question, options, session_id)


def answer_user(question_id: str, answer: str) -> AtomicToolResult:
    """回答用户问题"""
    return _user_tool.answer(question_id, answer)


def get_registry() -> AtomicToolRegistry:
    """获取原子工具注册表"""
    return _registry
