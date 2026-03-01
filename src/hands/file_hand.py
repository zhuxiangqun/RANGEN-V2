#!/usr/bin/env python3
"""
文件操作Hands
"""

import os
import shutil
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import BaseHand, HandCategory, HandSafetyLevel, HandExecutionResult


class FileReadHand(BaseHand):
    """文件读取Hand"""
    
    def __init__(self):
        super().__init__(
            name="file_read",
            description="读取文件内容",
            category=HandCategory.FILE_OPERATION,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行文件读取"""
        try:
            file_path = Path(kwargs["path"])
            encoding = kwargs.get("encoding", "utf-8")
            
            if not file_path.exists():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"文件不存在: {file_path}"
                )
            
            if not file_path.is_file():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"不是文件: {file_path}"
                )
            
            # 读取文件
            content = file_path.read_text(encoding=encoding)
            
            # 可选的格式处理
            if kwargs.get("parse_json", False):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError as e:
                    return HandExecutionResult(
                        hand_name=self.name,
                        success=False,
                        output=None,
                        error=f"JSON解析失败: {e}"
                    )
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output=content,
                validation_results={
                    "file_size": os.path.getsize(file_path),
                    "file_type": file_path.suffix,
                    "encoding": encoding
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"读取文件失败: {e}"
            )


class FileWriteHand(BaseHand):
    """文件写入Hand"""
    
    def __init__(self):
        super().__init__(
            name="file_write",
            description="写入文件内容",
            category=HandCategory.FILE_OPERATION,
            safety_level=HandSafetyLevel.MODERATE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path", "content"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行文件写入"""
        try:
            file_path = Path(kwargs["path"])
            content = kwargs["content"]
            encoding = kwargs.get("encoding", "utf-8")
            mode = kwargs.get("mode", "w")  # w: 覆盖, a: 追加
            
            # 检查目录是否存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 处理JSON内容
            if isinstance(content, (dict, list)):
                content = json.dumps(content, indent=2, ensure_ascii=False)
            
            # 写入文件
            if mode == "a":
                with open(file_path, "a", encoding=encoding) as f:
                    f.write(content)
            else:
                file_path.write_text(content, encoding=encoding)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "path": str(file_path),
                    "size": os.path.getsize(file_path) if file_path.exists() else 0
                },
                validation_results={
                    "file_created": not file_path.exists() or mode == "w",
                    "file_appended": mode == "a" and file_path.exists(),
                    "encoding": encoding
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"写入文件失败: {e}"
            )


class DirectoryCreateHand(BaseHand):
    """目录创建Hand"""
    
    def __init__(self):
        super().__init__(
            name="directory_create",
            description="创建目录",
            category=HandCategory.FILE_OPERATION,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["path"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行目录创建"""
        try:
            dir_path = Path(kwargs["path"])
            parents = kwargs.get("parents", True)
            exist_ok = kwargs.get("exist_ok", True)
            
            # 创建目录
            dir_path.mkdir(parents=parents, exist_ok=exist_ok)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "path": str(dir_path),
                    "created": dir_path.exists()
                },
                validation_results={
                    "directory_exists": dir_path.exists(),
                    "is_directory": dir_path.is_dir()
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"创建目录失败: {e}"
            )


class FileCopyHand(BaseHand):
    """文件复制Hand"""
    
    def __init__(self):
        super().__init__(
            name="file_copy",
            description="复制文件或目录",
            category=HandCategory.FILE_OPERATION,
            safety_level=HandSafetyLevel.MODERATE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        required = ["source", "destination"]
        return all(key in kwargs for key in required)
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行文件复制"""
        try:
            source = Path(kwargs["source"])
            destination = Path(kwargs["destination"])
            
            if not source.exists():
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"源路径不存在: {source}"
                )
            
            # 确保目标目录存在
            if source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
            else:
                destination.mkdir(parents=True, exist_ok=True)
            
            # 执行复制
            if source.is_file():
                shutil.copy2(source, destination)
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            
            return HandExecutionResult(
                hand_name=self.name,
                success=True,
                output={
                    "source": str(source),
                    "destination": str(destination),
                    "type": "file" if source.is_file() else "directory"
                },
                validation_results={
                    "destination_exists": destination.exists(),
                    "copied_successfully": True
                }
            )
            
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"复制文件失败: {e}"
            )


class TemporaryFileHand(BaseHand):
    """临时文件Hand"""
    
    def __init__(self):
        super().__init__(
            name="temporary_file",
            description="创建和管理临时文件",
            category=HandCategory.FILE_OPERATION,
            safety_level=HandSafetyLevel.SAFE
        )
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数"""
        return True  # 所有参数都是可选的
    
    async def execute(self, **kwargs) -> HandExecutionResult:
        """执行临时文件操作"""
        try:
            operation = kwargs.get("operation", "create")  # create, read, delete
            content = kwargs.get("content", "")
            suffix = kwargs.get("suffix", ".tmp")
            
            if operation == "create":
                # 创建临时文件
                with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
                    f.write(content)
                    temp_path = f.name
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=True,
                    output={
                        "path": temp_path,
                        "operation": "created"
                    },
                    validation_results={
                        "file_exists": os.path.exists(temp_path),
                        "is_temp_file": True
                    }
                )
            
            elif operation == "read":
                # 读取临时文件
                path = kwargs.get("path")
                if not path or not os.path.exists(path):
                    return HandExecutionResult(
                        hand_name=self.name,
                        success=False,
                        output=None,
                        error="临时文件不存在"
                    )
                
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=True,
                    output={
                        "path": path,
                        "content": content,
                        "operation": "read"
                    }
                )
            
            elif operation == "delete":
                # 删除临时文件
                path = kwargs.get("path")
                if not path:
                    return HandExecutionResult(
                        hand_name=self.name,
                        success=False,
                        output=None,
                        error="未指定要删除的文件路径"
                    )
                
                if os.path.exists(path):
                    os.unlink(path)
                
                return HandExecutionResult(
                    hand_name=self.name,
                    success=True,
                    output={
                        "path": path,
                        "deleted": not os.path.exists(path),
                        "operation": "delete"
                    }
                )
            
            else:
                return HandExecutionResult(
                    hand_name=self.name,
                    success=False,
                    output=None,
                    error=f"不支持的操作: {operation}"
                )
                
        except Exception as e:
            return HandExecutionResult(
                hand_name=self.name,
                success=False,
                output=None,
                error=f"临时文件操作失败: {e}"
            )