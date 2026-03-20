#!/usr/bin/env python3
"""
CLI-Anything Generator - 独立版 (无外部依赖)

完全独立的 CLI 工具生成器，不依赖任何外部 API。

工作流程：
1. 检查系统是否已安装该软件
2. 解析软件的 --help 输出
3. 分析参数结构
4. 生成 Python CLI 包装工具
5. 注册到 RANGEN 工具系统
"""

import asyncio
import subprocess
import os
import shutil
import json
import re
import inspect
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from src.services.logging_service import get_logger

logger = get_logger(__name__)


# ============================================================
# 软件 CLI 定义模板 (常见软件的预定义 CLI 接口)
# ============================================================

SOFTWARE_CLI_TEMPLATES = {
    # === 图像处理 ===
    "gimp": {
        "command": "gimp",
        "display_name": "GIMP",
        "description": "GNU Image Manipulation Program",
        "args": [
            {"name": "--no-splash", "type": "flag", "desc": "Don't show splash screen"},
            {"name": "--batch", "type": "string", "desc": "Run in batch mode"},
            {"name": "--batch-interpreter", "type": "string", "desc": "Batch interpreter to use"},
            {"name": "--no-data", "type": "flag", "desc": "Don't load fonts, patterns, gradients, etc."},
            {"name": "-f", "type": "flag", "desc": "Don't show dialogs on startup"},
        ],
        "operations": {
            "rotate": {
                "args": ["angle"],
                "desc": "Rotate image by angle",
                "example": "--batch='(gimp-image-rotate 0 90)' --batch='(gimp-quit 1)'",
            },
            "resize": {
                "args": ["width", "height"],
                "desc": "Resize image",
                "example": "--batch='(gimp-image-scale 0 800 600)' --batch='(gimp-quit 1)'",
            },
            "convert": {
                "args": ["output_format"],
                "desc": "Convert to different format",
                "example": "image.xcf",
            },
        }
    },
    "imagemagick": {
        "command": "convert",
        "display_name": "ImageMagick",
        "description": "Image manipulation program",
        "args": [
            {"name": "-resize", "type": "string", "desc": "Resize image"},
            {"name": "-rotate", "type": "string", "desc": "Rotate image"},
            {"name": "-flip", "type": "flag", "desc": "Flip image vertically"},
            {"name": "-flop", "type": "flag", "desc": "Flip image horizontally"},
            {"name": "-crop", "type": "string", "desc": "Crop image"},
            {"name": "-quality", "type": "string", "desc": "Output quality"},
            {"name": "-format", "type": "string", "desc": "Output format (jpg, png, etc.)"},
        ],
        "operations": {
            "resize": {"args": ["widthxheight"], "desc": "Resize image", "example": "convert input.jpg -resize 800x600 output.jpg"},
            "rotate": {"args": ["angle"], "desc": "Rotate image", "example": "convert input.jpg -rotate 90 output.jpg"},
            "convert": {"args": ["format"], "desc": "Convert format", "example": "convert input.jpg output.png"},
            "thumbnail": {"args": ["size"], "desc": "Create thumbnail", "example": "convert input.jpg -thumbnail 200x200 thumb.jpg"},
        }
    },
    "ffmpeg": {
        "command": "ffmpeg",
        "display_name": "FFmpeg",
        "description": "Video/Audio processing",
        "args": [
            {"name": "-i", "type": "string", "desc": "Input file"},
            {"name": "-o", "type": "string", "desc": "Output file"},
            {"name": "-c:v", "type": "string", "desc": "Video codec"},
            {"name": "-c:a", "type": "string", "desc": "Audio codec"},
            {"name": "-r", "type": "string", "desc": "Frame rate"},
            {"name": "-s", "type": "string", "desc": "Video size"},
            {"name": "-b:v", "type": "string", "desc": "Video bitrate"},
            {"name": "-b:a", "type": "string", "desc": "Audio bitrate"},
            {"name": "-t", "type": "string", "desc": "Duration"},
            {"name": "-ss", "type": "string", "desc": "Start time"},
        ],
        "operations": {
            "convert": {"args": ["input", "output"], "desc": "Convert video format", "example": "ffmpeg -i input.mp4 output.avi"},
            "extract_audio": {"args": [], "desc": "Extract audio", "example": "ffmpeg -i input.mp4 -vn -acodec copy output.aac"},
            "resize": {"args": ["resolution"], "desc": "Resize video", "example": "ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4"},
            "trim": {"args": ["start", "duration"], "desc": "Trim video", "example": "ffmpeg -i input.mp4 -ss 00:00:10 -t 00:00:30 output.mp4"},
            "gif": {"args": [], "desc": "Create GIF", "example": "ffmpeg -i input.mp4 -vf fps=10 -loop 0 output.gif"},
        }
    },
    "blender": {
        "command": "blender",
        "display_name": "Blender",
        "description": "3D creation suite",
        "args": [
            {"name": "--background", "type": "flag", "desc": "Run in background"},
            {"name": "--python", "type": "string", "desc": "Run Python script"},
            {"name": "--python-text", "type": "string", "desc": "Run Python code string"},
            {"name": "-o", "type": "string", "desc": "Set render output path"},
            {"name": "-a", "type": "flag", "desc": "Render animation"},
            {"name": "-E", "type": "string", "desc": "Render engine"},
            {"name": "-f", "type": "string", "desc": "Render specific frame"},
            {"name": "-F", "type": "string", "desc": "Output format"},
        ],
        "operations": {
            "render": {"args": ["frame"], "desc": "Render frame", "example": "blender -b scene.blend -o //render/ -f 1"},
            "render_anim": {"args": [], "desc": "Render animation", "example": "blender -b scene.blend -a"},
            "python": {"args": ["script"], "desc": "Run Python script", "example": "blender --background --python script.py"},
        }
    },
    "inkscape": {
        "command": "inkscape",
        "display_name": "Inkscape",
        "description": "Vector graphics editor",
        "args": [
            {"name": "--without-gui", "type": "flag", "desc": "Run without GUI"},
            {"name": "--batch-process", "type": "flag", "desc": "Process in batch mode"},
            {"name": "--export-filename", "type": "string", "desc": "Output file"},
            {"name": "--export-type", "type": "string", "desc": "Export type (png, pdf, svg)"},
            {"name": "--export-width", "type": "string", "desc": "Export width"},
            {"name": "--export-height", "type": "string", "desc": "Export height"},
            {"name": "--export-area-page", "type": "flag", "desc": "Export entire page"},
        ],
        "operations": {
            "convert": {"args": ["format"], "desc": "Convert to format", "example": "inkscape input.svg --export-filename=output.png --export-type=png"},
            "export_png": {"args": ["width", "height"], "desc": "Export as PNG", "example": "inkscape input.svg --export-filename=out.png --export-width=800 --export-height=600"},
        }
    },
    # === 办公软件 ===
    "libreoffice": {
        "command": "libreoffice",
        "display_name": "LibreOffice",
        "description": "Office suite",
        "args": [
            {"name": "--headless", "type": "flag", "desc": "Run without GUI"},
            {"name": "--convert-to", "type": "string", "desc": "Convert to format"},
            {"name": "--outdir", "type": "string", "desc": "Output directory"},
            {"name": "--infilter", "type": "string", "desc": "Input filter"},
        ],
        "operations": {
            "convert": {"args": ["format"], "desc": "Convert document", "example": "libreoffice --headless --convert-to pdf --outdir ./ doc.odt"},
            "pdf": {"args": [], "desc": "Convert to PDF", "example": "libreoffice --headless --convert-to pdf doc.docx"},
        }
    },
    # === 3D/模型处理 ===
    "obj2gltf": {
        "command": "obj2gltf",
        "display_name": "obj2gltf",
        "description": "Convert OBJ to glTF",
        "args": [
            {"name": "-i", "type": "string", "desc": "Input file"},
            {"name": "-o", "type": "string", "desc": "Output file"},
            {"name": "-b", "type": "flag", "desc": "Output as binary glTF"},
            {"name": "--compress", "type": "flag", "desc": "Compress meshes"},
        ],
        "operations": {
            "convert": {"args": [], "desc": "Convert OBJ to glTF", "example": "obj2gltf -i model.obj -o model.gltf"},
            "binary": {"args": [], "desc": "Convert to binary glTF", "example": "obj2gltf -i model.obj -o model.glb -b"},
        }
    },
    # === 视频/流媒体 ===
    "yt-dlp": {
        "command": "yt-dlp",
        "display_name": "yt-dlp",
        "description": "Video downloader",
        "args": [
            {"name": "-o", "type": "string", "desc": "Output template"},
            {"name": "-f", "type": "string", "desc": "Video format"},
            {"name": "--extract-audio", "type": "flag", "desc": "Extract audio only"},
            {"name": "--audio-format", "type": "string", "desc": "Audio format"},
            {"name": "--subtitle", "type": "flag", "desc": "Download subtitles"},
            {"name": "--list-formats", "type": "flag", "desc": "List available formats"},
        ],
        "operations": {
            "download": {"args": ["url"], "desc": "Download video", "example": "yt-dlp https://youtube.com/watch?v=xxx"},
            "audio": {"args": [], "desc": "Download audio", "example": "yt-dlp --extract-audio --audio-format mp3 URL"},
            "formats": {"args": [], "desc": "List formats", "example": "yt-dlp --list-formats URL"},
        }
    },
}


@dataclass
class CLIOperation:
    """CLI 操作定义"""
    name: str
    args: List[str]
    description: str
    example: str


@dataclass
class CLIToolDefinition:
    """CLI 工具定义"""
    software_name: str
    command: str
    display_name: str
    description: str
    args: List[Dict[str, str]]
    operations: Dict[str, CLIOperation]
    installed: bool = False


@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    tool_name: str
    command: str
    tool_definition: Optional[CLIToolDefinition] = None
    installation_path: Optional[str] = None
    error: Optional[str] = None


class CLIAnythingGenerator:
    """
    独立的 CLI-Anything 生成器
    
    特点：
    1. 完全独立，不依赖任何外部 API
    2. 使用预定义模板 + 动态检测
    3. 支持静态分析软件 --help
    4. 自动生成 Python 包装工具
    """
    
    def __init__(
        self,
        output_directory: str = None,
        auto_install: bool = True
    ):
        self.output_directory = output_directory or os.path.join(
            os.path.expanduser("~/.rangen"), "cli_tools"
        )
        self.auto_install = auto_install
        self.generated_tools: Dict[str, GenerationResult] = {}
        self._available_software: Dict[str, CLIToolDefinition] = {}
        
        os.makedirs(self.output_directory, exist_ok=True)
        
        # 初始化预定义模板
        self._init_templates()
    
    def _init_templates(self):
        """初始化预定义的 CLI 模板"""
        for name, template in SOFTWARE_CLI_TEMPLATES.items():
            # 转换 operations 格式
            operations = {}
            for op_name, op_data in template.get("operations", {}).items():
                operations[op_name] = CLIOperation(
                    name=op_name,
                    args=op_data.get("args", []),
                    description=op_data.get("desc", ""),
                    example=op_data.get("example", "")
                )
            
            self._available_software[name] = CLIToolDefinition(
                software_name=name,
                command=template["command"],
                display_name=template.get("display_name", name),
                description=template.get("description", ""),
                args=template.get("args", []),
                operations=operations,
                installed=False
            )
            
        logger.info(f"已加载 {len(self._available_software)} 个 CLI 工具模板")
    
    async def generate(
        self,
        software_name: str,
        **kwargs
    ) -> GenerationResult:
        """
        生成 CLI 工具
        
        Args:
            software_name: 软件名称
            
        Returns:
            GenerationResult: 生成结果
        """
        tool_name = f"cli-{software_name}"
        
        logger.info(f"开始生成 CLI 工具: {tool_name}")
        
        # 1. 检查是否有预定义模板
        template = self._available_software.get(software_name.lower())
        if not template:
            # 尝试动态检测
            template = await self._detect_software(software_name)
        
        if not template:
            return GenerationResult(
                success=False,
                tool_name=tool_name,
                command="",
                error=f"不支持的软件: {software_name}"
            )
        
        # 2. 检查软件是否已安装
        is_installed = await self._check_installation(template.command)
        template.installed = is_installed
        
        if not is_installed:
            logger.warning(f"软件未安装: {template.display_name} ({template.command})")
        
        # 3. 生成 Python 包装工具
        tool_path = await self._generate_wrapper(template)
        
        if tool_path:
            result = GenerationResult(
                success=True,
                tool_name=tool_name,
                command=template.command,
                tool_definition=template,
                installation_path=tool_path
            )
            self.generated_tools[software_name] = result
            logger.info(f"CLI 工具生成成功: {tool_name} -> {tool_path}")
            return result
        else:
            return GenerationResult(
                success=False,
                tool_name=tool_name,
                command=template.command,
                error="生成包装工具失败"
            )
    
    async def _detect_software(self, software_name: str) -> Optional[CLIToolDefinition]:
        """动态检测软件"""
        # 尝试在系统中查找
        cmd_path = shutil.which(software_name)
        if cmd_path:
            # 尝试解析 --help
            help_text = await self._get_help(software_name)
            
            return CLIToolDefinition(
                software_name=software_name,
                command=software_name,
                display_name=software_name.title(),
                description=f"Detected: {cmd_path}",
                args=self._parse_help_args(help_text) if help_text else [],
                operations={}
            )
        
        return None
    
    async def _check_installation(self, command: str) -> bool:
        """检查软件是否已安装"""
        return shutil.which(command) is not None
    
    async def _get_help(self, command: str) -> Optional[str]:
        """获取软件的帮助信息"""
        try:
            for help_flag in ["--help", "-h", "-help", "help"]:
                result = await asyncio.create_subprocess_exec(
                    command, help_flag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(
                    result.communicate(),
                    timeout=5
                )
                if result.returncode == 0 and stdout:
                    return stdout.decode("utf-8", errors="ignore")
        except Exception as e:
            logger.debug(f"获取帮助失败 {command}: {e}")
        
        return None
    
    def _parse_help_args(self, help_text: str) -> List[Dict[str, str]]:
        """解析帮助文本提取参数"""
        args = []
        
        # 简单解析：查找 -xxx 或 --xxxxx 格式
        pattern = r'(-{1,2}[\w-]+)(?:\s+(\w+))?'
        matches = re.findall(pattern, help_text)
        
        for short_or_long, arg_name in matches:
            if short_or_long.startswith("-"):
                args.append({
                    "name": short_or_long,
                    "type": "string" if arg_name else "flag",
                    "desc": f"Auto-detected: {short_or_long}"
                })
        
        return args[:20]  # 限制参数数量
    
    async def _generate_wrapper(self, template: CLIToolDefinition) -> Optional[str]:
        """生成 Python 包装工具"""
        
        # 生成工具代码
        tool_code = self._generate_tool_code(template)
        
        # 写入文件
        tool_filename = f"{template.software_name}_cli.py"
        tool_path = os.path.join(self.output_directory, tool_filename)
        
        try:
            with open(tool_path, "w") as f:
                f.write(tool_code)
            
            os.chmod(tool_path, 0o755)
            return tool_path
        except Exception as e:
            logger.error(f"生成工具文件失败: {e}")
            return None
    
    def _generate_tool_code(self, template: CLIToolDefinition) -> str:
        """生成 Python CLI 包装工具代码"""
        
        operations_code = []
        for op_name, op in template.operations.items():
            operations_code.append(f'''
    async def {op_name}(self, *args, **kwargs) -> Dict[str, Any]:
        """
        {op.description}
        
        Args:
            {', '.join(op.args) if op.args else 'None'}
            
        Example:
            {op.example}
        """
        cmd = ["{template.command}"]
        # TODO: 构建命令参数
        return await self._execute(cmd)
''')
        
        tool_code = f'''#!/usr/bin/env python3
"""
{template.display_name} CLI Wrapper

Generated by CLI-Anything Generator
Software: {template.description}
Command: {template.command}
"""

import asyncio
import subprocess
import json
from typing import Dict, Any, List, Optional


class {template.software_name.title().replace("-", "")}CLITool:
    """{template.display_name} CLI 工具"""
    
    def __init__(self):
        self.command = "{template.command}"
        self.software_name = "{template.software_name}"
    
    async def _execute(self, cmd: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """执行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=60
            )
            
            return {{
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="ignore") if stderr else "",
            }}
        except asyncio.TimeoutError:
            return {{"success": False, "error": "Command timeout"}}
        except Exception as e:
            return {{"success": False, "error": str(e)}}
    
    async def execute(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """
        执行操作
        
        Args:
            operation: 操作名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
        """
        operations = {{
{chr(10).join([f'            "{op_name}": self.{op_name},' for op_name in template.operations.keys()])}
        }}
        
        if operation not in operations:
            return {{"success": False, "error": f"Unknown operation: {{operation}}"}}
        
        return await operations[operation](*args, **kwargs)
{"".join(operations_code)}
    
    def get_operations(self) -> List[str]:
        """获取可用操作列表"""
        return list({list(template.operations.keys())})


# 全局实例
_tool_instance = None

def get_tool() -> {template.software_name.title().replace("-", "")}CLITool:
    """获取工具实例"""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = {template.software_name.title().replace("-", "")}CLITool()
    return _tool_instance


if __name__ == "__main__":
    import sys
    
    async def main():
        tool = get_tool()
        
        if len(sys.argv) < 2:
            print(f"Usage: {{sys.argv[0]}} <operation> [args...]")
            print(f"Available operations: {{tool.get_operations()}}")
            return
        
        operation = sys.argv[1]
        result = await tool.execute(operation, *sys.argv[2:])
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
'''
        
        return tool_code
    
    def get_available_tools(self) -> List[CLIToolDefinition]:
        """获取所有可用的 CLI 工具"""
        return list(self._available_software.values())
    
    def get_generated_tools(self) -> Dict[str, GenerationResult]:
        """获取已生成的工具"""
        return self.generated_tools
    
    async def list_operations(self, software_name: str) -> List[str]:
        """列出软件的可用操作"""
        template = self._available_software.get(software_name.lower())
        if template:
            return list(template.operations.keys())
        return []


# ============================================================
# 便捷函数
# ============================================================

_generator: Optional[CLIAnythingGenerator] = None


def get_cli_anything_generator() -> CLIAnythingGenerator:
    """获取全局 CLI-Anything 生成器实例"""
    global _generator
    if _generator is None:
        _generator = CLIAnythingGenerator()
    return _generator


async def generate_cli_tool(
    software_name: str,
    **kwargs
) -> GenerationResult:
    """便捷函数：生成 CLI 工具"""
    generator = get_cli_anything_generator()
    return await generator.generate(software_name, **kwargs)


async def list_available_cli_tools() -> List[str]:
    """列出所有可用的 CLI 工具"""
    generator = get_cli_anything_generator()
    return [t.software_name for t in generator.get_available_tools()]


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    async def main():
        print("=== CLI-Anything Generator (独立版) ===\n")
        
        generator = CLIAnythingGenerator()
        
        # 列出可用的工具
        tools = generator.get_available_tools()
        print(f"可用 CLI 工具模板 ({len(tools)} 个):\n")
        
        for tool in tools:
            ops = list(tool.operations.keys())
            print(f"  {tool.display_name} ({tool.command})")
            print(f"    操作: {', '.join(ops) if ops else 'N/A'}")
            print()
        
        # 测试生成
        print("\n=== 测试生成 FFmpeg 工具 ===")
        result = await generator.generate("ffmpeg")
        print(f"结果: {'✅ 成功' if result.success else '❌ 失败'}")
        if result.success:
            print(f"  命令: {result.command}")
            print(f"  路径: {result.installation_path}")
    
    asyncio.run(main())
