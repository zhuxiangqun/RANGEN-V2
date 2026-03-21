#!/usr/bin/env python3
"""
CLI Executor - Direct CLI Tool Execution for RANGEN

直接执行 CLI 工具，不需要 MCP 协议。
支持 CLI-Anything 生成的工具和其他命令行工具。

与 MCP 的区别：
- MCP: Agent → MCP Client → MCP Server → CLI
- CLI Executor: Agent → 直接执行 CLI

优势：
- 无需额外的 MCP 服务器
- 更低的延迟
- 更简单的架构
- 更好的可靠性
"""

import asyncio
import subprocess
import json
import os
import shutil
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class CLIExecutorError(Exception):
    """CLI 执行器错误"""
    pass


class CLIToolNotFoundError(CLIExecutorError):
    """CLI 工具未找到"""
    pass


class CLIToolExecutionError(CLIExecutorError):
    """CLI 工具执行错误"""
    pass


@dataclass
class CLITool:
    """CLI 工具定义"""
    name: str                          # 工具名称 (如 gimp, blender)
    command: str                        # 命令 (如 cli-anything-gimp)
    description: str = ""              # 描述
    version: str = ""                   # 版本
    path: Optional[str] = None         # 工具路径
    installed: bool = False             # 是否已安装
    help_output: Optional[str] = None # --help 输出


@dataclass
class CLIToolResult:
    """CLI 工具执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time: float = 0.0
    json_output: Optional[Dict] = None  # 解析的 JSON 输出


class CLIExecutor:
    """
    CLI 工具执行器
    
    直接执行命令行工具，无需 MCP 协议。
    
    使用方式：
    ```python
    executor = CLIExecutor()
    
    # 执行 CLI 工具
    result = await executor.execute(
        command="cli-anything-gimp",
        args=["--rotate", "90", "--input", "photo.jpg"]
    )
    
    # 或使用 JSON 输出
    result = await executor.execute(
        command="cli-anything-gimp",
        args=["--rotate", "90", "--input", "photo.jpg", "--json"]
    )
    ```
    """
    
    def __init__(
        self,
        tool_directories: Optional[List[str]] = None,
        auto_discover: bool = True
    ):
        """
        初始化 CLI 执行器
        
        Args:
            tool_directories: CLI 工具搜索目录
            auto_discover: 是否自动发现工具
        """
        self._tool_dirs = tool_directories or [
            os.path.expanduser("~/.local/bin"),
            "/usr/local/bin",
            "/usr/bin",
            os.path.expanduser("~/.cli-anything"),
            os.path.expanduser("~/.rangen/cli_tools"),  # CLI-Anything 生成器输出目录
            os.path.join(os.path.expanduser("~/.rangen"), "cli_tools"),
        ]
        
        self._discovered_tools: Dict[str, CLITool] = {}
        self._tool_cache: Dict[str, CLITool] = {}
        
        if auto_discover:
            self.discover_tools()
    
    def discover_tools(self) -> Dict[str, CLITool]:
        """
        发现系统中的 CLI 工具
        
        特别关注 CLI-Anything 生成的工具：
        - cli-anything-*
        - 以及其他常用 CLI 工具
        """
        self._discovered_tools.clear()
        
        # CLI-Anything 工具前缀
        cli_anything_prefixes = [
            "cli-anything-",
            "clianything-",
        ]
        
        for tool_dir in self._tool_dirs:
            if not os.path.exists(tool_dir):
                continue
            
            for file in os.listdir(tool_dir):
                tool_path = os.path.join(tool_dir, file)
                
                # 检查是否是可执行文件
                if not os.path.isfile(tool_path):
                    continue
                if not os.access(tool_path, os.X_OK):
                    continue
                
                # 检查是否是 CLI-Anything 工具
                is_cli_anything = any(
                    file.startswith(prefix) 
                    for prefix in cli_anything_prefixes
                )
                
                # CLI-Anything 生成的文件: *_cli.py 模式
                is_generated_cli = file.endswith("_cli.py")
                
                if is_cli_anything or is_generated_cli or file in ["gimp", "blender", "ffmpeg", "convert"]:
                    tool = self._create_tool_entry(file, tool_path)
                    if tool:
                        self._discovered_tools[tool.name] = tool
                        logger.info(f"Discovered CLI tool: {tool.name} at {tool.path}")
        
        return self._discovered_tools
    
    def _create_tool_entry(self, name: str, path: str) -> Optional[CLITool]:
        """创建工具条目"""
        try:
            # 尝试获取 --help 输出
            help_output = None
            try:
                result = subprocess.run(
                    [path, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                help_output = result.stdout if result.returncode == 0 else result.stderr
            except Exception:
                pass
            
            # 尝试获取版本
            version = ""
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
            except Exception:
                pass
            
            return CLITool(
                name=name,
                command=path,
                description=help_output[:200] if help_output else "",
                version=version,
                path=path,
                installed=True,
                help_output=help_output
            )
        except Exception as e:
            logger.warning(f"Failed to create tool entry for {name}: {e}")
            return None
    
    async def execute(
        self,
        command: str,
        args: Optional[List[str]] = None,
        input_data: Optional[str] = None,
        timeout: int = 60,
        capture_json: bool = True,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> CLIToolResult:
        """
        执行 CLI 命令
        
        Args:
            command: 命令名称或路径
            args: 命令参数
            input_data: stdin 输入
            timeout: 超时时间（秒）
            capture_json: 是否尝试解析 JSON 输出
            env: 环境变量
            cwd: 工作目录
            
        Returns:
            CLIToolResult: 执行结果
        """
        import time
        start_time = time.time()
        
        args = args or []
        
        # 查找命令路径
        cmd_path = self._find_command(command)
        if not cmd_path:
            raise CLIToolNotFoundError(f"CLI tool not found: {command}")
        
        # 构建完整命令
        full_cmd = [cmd_path] + args
        
        # 合并环境变量
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        logger.info(f"Executing CLI: {' '.join(full_cmd)}")
        
        try:
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=exec_env,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            execution_time = time.time() - start_time
            
            # 尝试解析 JSON 输出
            json_output = None
            if capture_json:
                json_output = self._try_parse_json(stdout_str)
            
            result = CLIToolResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode,
                execution_time=execution_time,
                json_output=json_output
            )
            
            if not result.success:
                logger.warning(
                    f"CLI command failed: {command}, "
                    f"return_code={process.returncode}, "
                    f"stderr={stderr_str[:200]}"
                )
            
            return result
            
        except asyncio.TimeoutError:
            raise CLIToolExecutionError(
                f"CLI command timeout: {command}, timeout={timeout}s"
            )
        except Exception as e:
            raise CLIToolExecutionError(
                f"CLI command failed: {command}, error={str(e)}"
            )
    
    def _find_command(self, command: str) -> Optional[str]:
        """查找命令路径"""
        # 如果是路径，直接返回
        if os.path.isabs(command) and os.path.exists(command):
            return command
        
        # 如果是相对路径
        if os.path.exists(command):
            return os.path.abspath(command)
        
        # 在 PATH 中查找
        cmd_path = shutil.which(command)
        if cmd_path:
            return cmd_path
        
        # 在工具目录中查找
        for tool_dir in self._tool_dirs:
            potential_path = os.path.join(tool_dir, command)
            if os.path.exists(potential_path) and os.access(potential_path, os.X_OK):
                return potential_path
        
        return None
    
    def _try_parse_json(self, output: str) -> Optional[Dict]:
        """尝试解析 JSON 输出"""
        # 尝试直接解析
        try:
            return json.loads(output)
        except Exception:
            pass
        
        # 尝试从输出中提取 JSON
        # 常见模式: 输出中包含 JSON 块
        json_patterns = [
            r'\{[^{}]*\}',  # 简单的单层 JSON
            r'\{.*\}',       # 贪婪匹配
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, output, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except Exception:
                    continue
        
        return None
    
    def get_tool(self, name: str) -> Optional[CLITool]:
        """获取已发现的工具"""
        return self._discovered_tools.get(name)
    
    def list_tools(self) -> List[CLITool]:
        """列出所有已发现的工具"""
        return list(self._discovered_tools.values())
    
    async def execute_with_args_from_string(
        self,
        command: str,
        args_string: str,
        timeout: int = 60
    ) -> CLIToolResult:
        """
        通过字符串参数执行命令
        
        Args:
            command: 命令
            args_string: 参数字符串 (如 "--rotate 90 --input photo.jpg")
            
        Returns:
            CLIToolResult
        """
        # 简单的参数解析
        args = self._parse_args_string(args_string)
        return await self.execute(command, args, timeout=timeout)
    
    def _parse_args_string(self, args_string: str) -> List[str]:
        """解析参数字符串"""
        # 简单的引号保持解析
        args = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in args_string:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == " " and not in_quotes:
                if current:
                    args.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            args.append(current)
        
        return args
    
    def get_tool_help(self, command: str) -> Optional[str]:
        """获取工具帮助信息"""
        tool = self.get_tool(command)
        if tool and tool.help_output:
            return tool.help_output
        
        cmd_path = self._find_command(command)
        if not cmd_path:
            return None
        
        try:
            result = subprocess.run(
                [cmd_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception:
            return None


# 全局单例
_cli_executor: Optional[CLIExecutor] = None


def get_cli_executor() -> CLIExecutor:
    """获取全局 CLI 执行器实例"""
    global _cli_executor
    if _cli_executor is None:
        _cli_executor = CLIExecutor()
    return _cli_executor


async def execute_cli_tool(
    command: str,
    args: Optional[List[str]] = None,
    **kwargs
) -> CLIToolResult:
    """
    便捷函数：执行 CLI 工具
    
    Args:
        command: 命令名称
        args: 参数列表
        **kwargs: 其他参数
        
    Returns:
        CLIToolResult
    """
    executor = get_cli_executor()
    return await executor.execute(command, args, **kwargs)


# 示例用法
if __name__ == "__main__":
    async def main():
        executor = CLIExecutor()
        
        # 发现工具
        tools = executor.discover_tools()
        print(f"Discovered {len(tools)} CLI tools:")
        for tool in tools.values():
            print(f"  - {tool.name}: {tool.version}")
        
        # 列出工具
        print("\nAvailable tools:")
        for tool in executor.list_tools():
            print(f"  - {tool.name}")
    
    asyncio.run(main())
