"""
标准化CLI工具封装 - CLI Tool Wrapper

将常见的CLI命令封装为标准Tool，优先级高于MCP
遵循文章观点：CLI是可组合、可调试、无额外协议层的最佳执行层
"""

import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.interfaces.tool import ITool, ToolConfig, ToolCategory, ToolResult
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class CLICommand:
    """CLI命令定义"""
    command: str           # 命令模板，如 "git {subcommand}"
    args: List[str]        # 默认参数
    env: Optional[Dict[str, str]] = None  # 环境变量


class CLITool(ITool):
    """
    CLI工具封装
    
    优势：
    - 可组合（Unix管道哲学）
    - 可调试（直接跑命令看输出）
    - 无额外协议层
    - 输出是纯文本，LLM天然能理解
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        commands: Dict[str, CLICommand],
        category: ToolCategory = ToolCategory.UTILITY
    ):
        config = ToolConfig(
            name=name,
            description=description,
            category=category
        )
        super().__init__(config)
        self._commands = commands
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": list(self._commands.keys()),
                    "description": "要执行的CLI操作"
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "传递给命令的参数"
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "超时时间（秒）"
                }
            },
            "required": ["action"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action")
        args = kwargs.get("args", [])
        timeout = kwargs.get("timeout", 30)
        
        if action not in self._commands:
            return ToolResult(
                success=False,
                output="",
                execution_time=0,
                error=f"Unknown action: {action}. Available: {list(self._commands.keys())}"
            )
        
        cmd_spec = self._commands[action]
        
        # 构建命令
        full_cmd = cmd_spec.command.split() + cmd_spec.args + args
        
        logger.info(f"Executing CLI: {' '.join(full_cmd)}")
        
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=cmd_spec.env or {}
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            return ToolResult(
                success=success,
                output=output,
                execution_time=0,  # 可扩展为实际执行时间
                error=None if success else f"Exit code: {result.returncode}",
                metadata={
                    "returncode": result.returncode,
                    "command": " ".join(full_cmd)
                }
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                execution_time=timeout,
                error=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                execution_time=0,
                error=str(e)
            )
    
    async def call(self, **kwargs) -> ToolResult:
        return await self.execute(**kwargs)


# 预定义的CLI工具

def create_git_tool() -> CLITool:
    """Git CLI工具"""
    return CLITool(
        name="git",
        description="Git版本控制操作（克隆、提交、推送等）",
        commands={
            "clone": CLICommand(command="git clone", args=[]),
            "status": CLICommand(command="git status", args=[]),
            "add": CLICommand(command="git add", args=["."]),
            "commit": CLICommand(command="git commit", args=["-m"]),
            "push": CLICommand(command="git push", args=[]),
            "pull": CLICommand(command="git pull", args=[]),
            "branch": CLICommand(command="git branch", args=[]),
            "checkout": CLICommand(command="git checkout", args=[]),
            "log": CLICommand(command="git log", args=["--oneline", "-10"]),
            "diff": CLICommand(command="git diff", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_file_tool() -> CLITool:
    """文件系统CLI工具"""
    return CLITool(
        name="filesystem",
        description="文件系统操作（ls、cp、mv、rm等）",
        commands={
            "list": CLICommand(command="ls", args=["-la"]),
            "copy": CLICommand(command="cp", args=[]),
            "move": CLICommand(command="mv", args=[]),
            "remove": CLICommand(command="rm", args=["-rf"]),
            "mkdir": CLICommand(command="mkdir", args=["-p"]),
            "exists": CLICommand(command="test", args=["-e"]),
            "isdir": CLICommand(command="test", args=["-d"]),
            "isfile": CLICommand(command="test", args=["-f"]),
            "read": CLICommand(command="cat", args=[]),
            "write": CLICommand(command="tee", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_docker_tool() -> CLITool:
    """Docker CLI工具"""
    return CLITool(
        name="docker",
        description="Docker容器操作",
        commands={
            "ps": CLICommand(command="docker ps", args=["-a"]),
            "images": CLICommand(command="docker images", args=[]),
            "run": CLICommand(command="docker run", args=["-d"]),
            "stop": CLICommand(command="docker stop", args=[]),
            "rm": CLICommand(command="docker rm", args=[]),
            "logs": CLICommand(command="docker logs", args=[]),
            "exec": CLICommand(command="docker exec", args=[]),
            "build": CLICommand(command="docker build", args=["-t"]),
            "pull": CLICommand(command="docker pull", args=[]),
            "push": CLICommand(command="docker push", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_npm_tool() -> CLITool:
    """npm CLI工具"""
    return CLITool(
        name="npm",
        description="Node.js包管理操作",
        commands={
            "install": CLICommand(command="npm install", args=[]),
            "run": CLICommand(command="npm run", args=[]),
            "test": CLICommand(command="npm test", args=[]),
            "build": CLICommand(command="npm run build", args=[]),
            "dev": CLICommand(command="npm run dev", args=[]),
            "list": CLICommand(command="npm list", args=["--depth=0"]),
            "outdated": CLICommand(command="npm outdated", args=[]),
            "update": CLICommand(command="npm update", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_curl_tool() -> CLITool:
    """curl CLI工具"""
    return CLITool(
        name="curl",
        description="HTTP请求操作",
        commands={
            "get": CLICommand(command="curl", args=["-s"]),
            "post": CLICommand(command="curl", args=["-X", "POST"]),
            "put": CLICommand(command="curl", args=["-X", "PUT"]),
            "delete": CLICommand(command="curl", args=["-X", "DELETE"]),
            "headers": CLICommand(command="curl", args=["-I"]),
        },
        category=ToolCategory.API
    )


def create_search_tool() -> CLITool:
    """搜索工具（grep, find, ag等）"""
    return CLITool(
        name="search",
        description="文本搜索和文件查找操作",
        commands={
            "grep": CLICommand(command="grep", args=[]),
            "find": CLICommand(command="find", args=[]),
            "ag": CLICommand(command="ag", args=[]),  # Silver Searcher
            "rg": CLICommand(command="rg", args=[]),  # Ripgrep
            "locate": CLICommand(command="locate", args=[]),
        },
        category=ToolCategory.RETRIEVAL
    )


def create_process_tool() -> CLITool:
    """进程管理工具"""
    return CLITool(
        name="process",
        description="进程查看和管理",
        commands={
            "ps": CLICommand(command="ps", args=["aux"]),
            "top": CLICommand(command="top", args=["-b", "-n", "1"]),
            "htop": CLICommand(command="htop", args=[]),
            "kill": CLICommand(command="kill", args=[]),
            "pkill": CLICommand(command="pkill", args=[]),
            "jobs": CLICommand(command="jobs", args=[]),
            "lsof": CLICommand(command="lsof", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_network_tool() -> CLITool:
    """网络工具"""
    return CLITool(
        name="network",
        description="网络诊断和操作",
        commands={
            "ping": CLICommand(command="ping", args=["-c", "4"]),
            "curl": CLICommand(command="curl", args=["-s"]),
            "wget": CLICommand(command="wget", args=[]),
            "ssh": CLICommand(command="ssh", args=[]),
            "scp": CLICommand(command="scp", args=[]),
            "netstat": CLICommand(command="netstat", args=["-tuln"]),
            "dig": CLICommand(command="dig", args=[]),
            "nslookup": CLICommand(command="nslookup", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_system_tool() -> CLITool:
    """系统信息工具"""
    return CLITool(
        name="system",
        description="系统信息和监控",
        commands={
            "uname": CLICommand(command="uname", args=["-a"]),
            "df": CLICommand(command="df", args=["-h"]),
            "du": CLICommand(command="du", args=["-sh"]),
            "free": CLICommand(command="free", args=["-h"]),
            "uptime": CLICommand(command="uptime", args=[]),
            "whoami": CLICommand(command="whoami", args=[]),
            "date": CLICommand(command="date", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_python_tool() -> CLITool:
    """Python环境工具"""
    return CLITool(
        name="python",
        description="Python环境管理和脚本运行",
        commands={
            "run": CLICommand(command="python", args=[]),
            "pip_list": CLICommand(command="pip", args=["list"]),
            "pip_install": CLICommand(command="pip", args=["install"]),
            "venv_create": CLICommand(command="python", args=["-m", "venv"]),
            "black_check": CLICommand(command="black", args=["--check"]),
            "flake8": CLICommand(command="flake8", args=[]),
            "pytest": CLICommand(command="pytest", args=[]),
        },
        category=ToolCategory.UTILITY
    )


def create_grep_tool() -> CLITool:
    """专门的文件内容搜索工具"""
    return CLITool(
        name="grep",
        description="文件内容搜索（高级版）",
        commands={
            "search": CLICommand(command="grep", args=[]),
            "search_recursive": CLICommand(command="grep", args=["-r"]),
            "search_ignore_case": CLICommand(command="grep", args=["-i"]),
            "search_count": CLICommand(command="grep", args=["-c"]),
            "search_files_only": CLICommand(command="grep", args=["-l"]),
            "ripgrep": CLICommand(command="rg", args=[]),
            "ripgrep_verbose": CLICommand(command="rg", args=["-v"]),
            "ripgrep_json": CLICommand(command="rg", args=["--json"]),
        },
        category=ToolCategory.RETRIEVAL
    )


# 全局CLI工具注册
_cli_tools: Dict[str, CLITool] = {}


def register_cli_tool(name: str, tool: CLITool) -> None:
    """注册CLI工具"""
    _cli_tools[name] = tool
    logger.info(f"Registered CLI tool: {name}")


def get_cli_tool(name: str) -> Optional[CLITool]:
    """获取CLI工具"""
    return _cli_tools.get(name)


def get_all_cli_tools() -> List[CLITool]:
    """获取所有CLI工具"""
    return list(_cli_tools.values())


# 初始化默认CLI工具
def init_default_cli_tools():
    """初始化默认的CLI工具"""
    register_cli_tool("git", create_git_tool())
    register_cli_tool("filesystem", create_file_tool())
    register_cli_tool("docker", create_docker_tool())
    register_cli_tool("npm", create_npm_tool())
    register_cli_tool("curl", create_curl_tool())
    logger.info("Initialized default CLI tools")


# 自动初始化
init_default_cli_tools()


def create_extended_cli_tools():
    """扩展CLI工具注册"""
    register_cli_tool("search", create_search_tool())
    register_cli_tool("process", create_process_tool())
    register_cli_tool("network", create_network_tool())
    register_cli_tool("system", create_system_tool())
    register_cli_tool("python", create_python_tool())
    register_cli_tool("grep", create_grep_tool())