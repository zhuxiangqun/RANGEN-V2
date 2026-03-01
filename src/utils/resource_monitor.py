#!/usr/bin/env python3
"""
资源监控模块 - P1优化
监控内存使用、文件描述符数量，超过阈值时主动清理
"""

import os
import gc
import psutil
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class ResourceThresholds:
    """资源阈值配置"""
    memory_percent: float = 80.0  # 内存使用率阈值（%）
    memory_mb: float = 4000.0     # 内存使用量阈值（MB）
    file_descriptors: int = 500   # 文件描述符数量阈值
    cpu_percent: float = 90.0     # CPU使用率阈值（%）
    mps_memory_gb: float = 16.0   # MPS内存使用量阈值（GB，默认16GB，接近18.13GB上限）


class ResourceMonitor:
    """资源监控器 - 监控系统资源并在超过阈值时触发清理"""
    
    def __init__(self, thresholds: Optional[ResourceThresholds] = None):
        """初始化资源监控器"""
        self.logger = logging.getLogger(__name__)
        self.thresholds = thresholds or ResourceThresholds()
        self.cleanup_callbacks: list[Callable[[], None]] = []
        
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """注册清理回调函数"""
        self.cleanup_callbacks.append(callback)
    
    def get_resource_status(self) -> Dict[str, Any]:
        """获取当前资源状态"""
        try:
            process = psutil.Process()
            
            # 内存信息
            memory = psutil.virtual_memory()
            process_memory = process.memory_info()
            
            # CPU信息
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # 文件描述符数量（Unix系统）
            num_fds = 0
            try:
                if hasattr(process, 'num_fds'):
                    num_fds = process.num_fds()
                elif os.name != 'nt':  # Unix系统
                    num_fds = len(process.open_files())
            except (psutil.AccessDenied, AttributeError):
                # 某些系统可能无法获取文件描述符数量
                num_fds = -1
            
            # 🚀 P0修复：获取MPS内存使用情况
            mps_memory_gb = 0.0
            mps_available = False
            try:
                import torch
                if torch.backends.mps.is_available():
                    mps_available = True
                    # 获取MPS内存使用情况（通过torch.mps.current_allocated_memory()）
                    # 注意：这个方法可能不存在，需要检查
                    try:
                        if hasattr(torch.mps, 'current_allocated_memory'):
                            mps_memory_bytes = torch.mps.current_allocated_memory()
                            mps_memory_gb = mps_memory_bytes / (1024 ** 3)
                    except AttributeError:
                        # 如果方法不存在，尝试其他方式
                        # PyTorch可能没有直接的方法获取MPS内存，这里先设为0
                        mps_memory_gb = 0.0
            except ImportError:
                # PyTorch未安装
                pass
            except Exception as e:
                # 其他错误，记录但不影响主流程
                self.logger.debug(f"获取MPS内存信息失败: {e}")
            
            return {
                "memory": {
                    "system_percent": memory.percent,
                    "system_used_mb": memory.used / (1024 * 1024),
                    "system_available_mb": memory.available / (1024 * 1024),
                    "process_rss_mb": process_memory.rss / (1024 * 1024),
                    "process_vms_mb": process_memory.vms / (1024 * 1024),
                },
                "cpu": {
                    "process_percent": cpu_percent,
                    "system_percent": psutil.cpu_percent(interval=0.1),
                },
                "file_descriptors": {
                    "count": num_fds,
                },
                "mps": {
                    "available": mps_available,
                    "memory_gb": mps_memory_gb,
                },
                "status": "ok"
            }
        except Exception as e:
            self.logger.error(f"获取资源状态失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_and_cleanup(self) -> Dict[str, Any]:
        """检查资源使用情况，如果超过阈值则触发清理"""
        status = self.get_resource_status()
        
        if status.get("status") != "ok":
            return status
        
        memory = status["memory"]
        cpu = status["cpu"]
        fds = status["file_descriptors"]
        mps = status.get("mps", {})
        
        issues = []
        should_cleanup = False
        
        # 检查内存使用率
        if memory["system_percent"] > self.thresholds.memory_percent:
            issues.append(f"系统内存使用率过高: {memory['system_percent']:.1f}% > {self.thresholds.memory_percent}%")
            should_cleanup = True
        
        # 检查进程内存使用量
        if memory["process_rss_mb"] > self.thresholds.memory_mb:
            issues.append(f"进程内存使用量过高: {memory['process_rss_mb']:.1f}MB > {self.thresholds.memory_mb}MB")
            should_cleanup = True
        
        # 检查文件描述符数量
        if fds["count"] > 0 and fds["count"] > self.thresholds.file_descriptors:
            issues.append(f"文件描述符数量过多: {fds['count']} > {self.thresholds.file_descriptors}")
            should_cleanup = True
        
        # 🚀 P0修复：检查MPS内存使用量
        if mps.get("available") and mps.get("memory_gb", 0) > self.thresholds.mps_memory_gb:
            issues.append(f"MPS内存使用量过高: {mps['memory_gb']:.2f}GB > {self.thresholds.mps_memory_gb}GB")
            should_cleanup = True
        
        # 检查CPU使用率
        if cpu["process_percent"] > self.thresholds.cpu_percent:
            issues.append(f"进程CPU使用率过高: {cpu['process_percent']:.1f}% > {self.thresholds.cpu_percent}%")
            # CPU过高不触发清理，只是记录警告
        
        if should_cleanup:
            self.logger.warning(f"⚠️ 资源使用超过阈值，触发清理: {', '.join(issues)}")
            self._perform_cleanup()
            status["cleanup_performed"] = True
            status["cleanup_reason"] = issues
        else:
            status["cleanup_performed"] = False
        
        status["issues"] = issues
        return status
    
    def _perform_cleanup(self):
        """执行清理操作"""
        try:
            # 执行注册的清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.warning(f"清理回调执行失败: {e}")
            
            # 🚀 P0修复：清理MPS内存
            try:
                import torch
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                    self.logger.info("🧹 MPS内存已清理")
            except ImportError:
                pass  # PyTorch未安装
            except Exception as e:
                self.logger.debug(f"MPS内存清理失败: {e}")
            
            # 强制垃圾回收
            collected = gc.collect()
            self.logger.info(f"🧹 资源清理完成，垃圾回收释放了 {collected} 个对象")
        except Exception as e:
            self.logger.error(f"执行清理操作失败: {e}")
    
    def log_resource_status(self, prefix: str = ""):
        """记录资源状态到日志"""
        status = self.get_resource_status()
        if status.get("status") == "ok":
            memory = status["memory"]
            cpu = status["cpu"]
            fds = status["file_descriptors"]
            
            self.logger.info(
                f"{prefix}资源状态: "
                f"内存={memory['process_rss_mb']:.1f}MB/{memory['system_percent']:.1f}%, "
                f"CPU={cpu['process_percent']:.1f}%, "
                f"文件描述符={fds['count']}"
            )

