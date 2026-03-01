"""
File Management Tool - 文件管理

提供安全的文件操作功能
"""

import asyncio
import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class FilePermission(Enum):
    """文件权限"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass
class FileConfig:
    """文件管理配置"""
    # 工作目录 (限制在指定目录内)
    workspace_dir: str = "data/workspace"
    # 允许的操作
    allow_delete: bool = True
    allow_upload: bool = True
    allow_download: bool = True
    # 文件大小限制 (字节)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    # 禁止访问的路径
    blocked_paths: List[str] = None
    
    def __post_init__(self):
        if self.blocked_paths is None:
            self.blocked_paths = [".env", ".git", "__pycache__", ".DS_Store"]


class FileTool:
    """
    文件管理工具
    
    功能:
    - 列出文件
    - 读取文件
    - 写入文件
    - 创建目录
    - 删除文件/目录
    - 复制/移动
    - 获取文件信息
    - 计算哈希
    """
    
    def __init__(self, config: Optional[FileConfig] = None):
        self.config = config or FileConfig()
        
        # 确保工作目录存在
        os.makedirs(self.config.workspace_dir, exist_ok=True)
    
    def _is_safe_path(self, path: str) -> bool:
        """检查路径是否安全 (防止路径穿越)"""
        # 获取绝对路径
        abs_path = os.path.abspath(os.path.join(self.config.workspace_dir, path))
        
        # 确保在工作目录内
        workspace_abs = os.path.abspath(self.config.workspace_dir)
        
        if not abs_path.startswith(workspace_abs):
            logger.warning(f"Path outside workspace: {path}")
            return False
        
        # 检查禁止的路径
        for blocked in self.config.blocked_paths:
            if blocked in abs_path:
                logger.warning(f"Blocked path: {path}")
                return False
        
        return True
    
    async def list_files(
        self,
        path: str = ".",
        pattern: Optional[str] = None,
        show_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出文件
        
        Args:
            path: 目录路径
            pattern: 文件名模式 (如 "*.txt")
            show_hidden: 是否显示隐藏文件
            
        Returns:
            List[Dict]: 文件列表
        """
        if not self._is_safe_path(path):
            return []
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        if not os.path.exists(full_path):
            return []
        
        files = []
        
        for item in os.listdir(full_path):
            # 跳过隐藏文件
            if not show_hidden and item.startswith("."):
                continue
            
            item_path = os.path.join(full_path, item)
            
            stat = os.stat(item_path)
            
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": os.path.join(path, item)
            })
        
        # 排序: 目录在前, 文件按名字
        files.sort(key=lambda x: (x["type"] != "file", x["name"]))
        
        # 应用过滤
        if pattern:
            import fnmatch
            files = [f for f in files if fnmatch.fnmatch(f["name"], pattern)]
        
        return files
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容
        
        Args:
            path: 文件路径
            encoding: 编码
        """
        if not self._is_safe_path(path):
            return "Error: Invalid path"
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        if not os.path.exists(full_path):
            return f"Error: File not found: {path}"
        
        if not os.path.isfile(full_path):
            return f"Error: Not a file: {path}"
        
        # 检查文件大小
        size = os.path.getsize(full_path)
        if size > self.config.max_file_size:
            return f"Error: File too large: {size} bytes (max: {self.config.max_file_size})"
        
        try:
            with open(full_path, "r", encoding=encoding) as f:
                content = f.read()
            
            logger.info(f"Read file: {path} ({len(content)} chars)")
            return content
            
        except UnicodeDecodeError:
            # 二进制文件
            return f"Error: Binary file (use download instead)"
        except Exception as e:
            return f"Error reading file: {e}"
    
    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> str:
        """
        写入文件
        
        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码
            create_dirs: 是否创建父目录
        """
        if not self._is_safe_path(path):
            return "Error: Invalid path"
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        # 创建父目录
        if create_dirs:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 检查文件大小
        if len(content.encode(encoding)) > self.config.max_file_size:
            return f"Error: Content too large"
        
        try:
            with open(full_path, "w", encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"Wrote file: {path} ({len(content)} chars)")
            return f"File written: {path}"
            
        except Exception as e:
            return f"Error writing file: {e}"
    
    async def create_directory(self, path: str) -> str:
        """创建目录"""
        if not self._is_safe_path(path):
            return "Error: Invalid path"
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return f"Directory created: {path}"
        except Exception as e:
            return f"Error creating directory: {e}"
    
    async def delete(self, path: str) -> str:
        """删除文件或目录"""
        if not self._is_safe_path(path):
            return "Error: Invalid path"
        
        if not self.config.allow_delete:
            return "Error: Delete not allowed"
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        if not os.path.exists(full_path):
            return f"Error: Not found: {path}"
        
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                logger.info(f"Deleted directory: {path}")
            else:
                os.remove(full_path)
                logger.info(f"Deleted file: {path}")
            
            return f"Deleted: {path}"
        except Exception as e:
            return f"Error deleting: {e}"
    
    async def copy(self, source: str, destination: str) -> str:
        """复制文件或目录"""
        if not self._is_safe_path(source) or not self._is_safe_path(destination):
            return "Error: Invalid path"
        
        src_path = os.path.join(self.config.workspace_dir, source)
        dst_path = os.path.join(self.config.workspace_dir, destination)
        
        if not os.path.exists(src_path):
            return f"Error: Source not found: {source}"
        
        try:
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            logger.info(f"Copied: {source} -> {destination}")
            return f"Copied: {source} -> {destination}"
        except Exception as e:
            return f"Error copying: {e}"
    
    async def move(self, source: str, destination: str) -> str:
        """移动文件或目录"""
        if not self._is_safe_path(source) or not self._is_safe_path(destination):
            return "Error: Invalid path"
        
        src_path = os.path.join(self.config.workspace_dir, source)
        dst_path = os.path.join(self.config.workspace_dir, destination)
        
        if not os.path.exists(src_path):
            return f"Error: Source not found: {source}"
        
        try:
            shutil.move(src_path, dst_path)
            logger.info(f"Moved: {source} -> {destination}")
            return f"Moved: {source} -> {destination}"
        except Exception as e:
            return f"Error moving: {e}"
    
    async def get_info(self, path: str) -> Dict[str, Any]:
        """获取文件/目录信息"""
        if not self._is_safe_path(path):
            return {"error": "Invalid path"}
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        if not os.path.exists(full_path):
            return {"error": "Not found"}
        
        stat = os.stat(full_path)
        
        info = {
            "name": os.path.basename(path),
            "path": path,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        
        # 额外信息
        if os.path.isfile(full_path):
            info["extension"] = os.path.splitext(path)[1]
            info["hash_md5"] = await self._calculate_hash(full_path, "md5")
        
        return info
    
    async def _calculate_hash(self, path: str, algorithm: str = "md5") -> str:
        """计算文件哈希"""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    async def search(self, query: str, path: str = ".") -> List[Dict[str, Any]]:
        """搜索文件"""
        if not self._is_safe_path(path):
            return []
        
        full_path = os.path.join(self.config.workspace_dir, path)
        
        results = []
        
        query_lower = query.lower()
        
        for root, dirs, files in os.walk(full_path):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            for name in files:
                if name.startswith("."):
                    continue
                
                # 匹配名字
                if query_lower in name.lower():
                    file_path = os.path.join(root, name)
                    rel_path = os.path.relpath(file_path, self.config.workspace_dir)
                    
                    results.append({
                        "name": name,
                        "path": rel_path,
                        "type": "file"
                    })
        
        return results[:50]  # 限制结果数量
    
    async def get_workspace_path(self) -> str:
        """获取工作区路径"""
        return self.config.workspace_dir


# ==================== 便捷函数 ====================

def create_file_tool(workspace_dir: str = "data/workspace") -> FileTool:
    """创建文件管理工具"""
    config = FileConfig(workspace_dir=workspace_dir)
    return FileTool(config)
