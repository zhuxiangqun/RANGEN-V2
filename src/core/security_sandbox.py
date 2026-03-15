#!/usr/bin/env python3
"""
安全沙箱体系
Security Sandbox System

V3核心理念：全面沙箱化和默认隔离的安全体系。
实现工具执行沙箱化、网络访问控制、资源限制和隔离、权限最小化原则、安全审计和日志。
"""
import asyncio
import logging
import time
import subprocess
import threading
import sys
import os
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from enum import Enum
from datetime import datetime
import json
import traceback
import resource
import signal
import socket

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别"""
    UNTRUSTED = "untrusted"    # 完全不可信，严格隔离
    RESTRICTED = "restricted"  # 受限访问，部分隔离
    TRUSTED = "trusted"        # 可信执行，最小限制
    PRIVILEGED = "privileged"  # 特权执行，无限制（仅系统内部使用）


class SandboxViolationType(Enum):
    """沙箱违规类型"""
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    NETWORK_ACCESS_DENIED = "network_access_denied"
    FILE_ACCESS_DENIED = "file_access_denied"
    SYSTEM_CALL_DENIED = "system_call_denied"
    EXECUTION_TIMEOUT = "execution_timeout"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    PERMISSION_DENIED = "permission_denied"


class SandboxViolation(Exception):
    """沙箱违规异常"""
    
    def __init__(self, violation_type: SandboxViolationType, message: str, details: Dict[str, Any] = None):
        self.violation_type = violation_type
        self.message = message
        self.details = details or {}
        super().__init__(f"{violation_type.value}: {message}")


class ResourceQuota:
    """资源配额配置"""
    
    def __init__(
        self,
        cpu_time_seconds: float = 30.0,
        memory_mb: int = 256,
        disk_space_mb: int = 100,
        max_processes: int = 10,
        network_bandwidth_mb: int = 10,
        max_file_descriptors: int = 100
    ):
        self.cpu_time_seconds = cpu_time_seconds
        self.memory_mb = memory_mb
        self.disk_space_mb = disk_space_mb
        self.max_processes = max_processes
        self.network_bandwidth_mb = network_bandwidth_mb
        self.max_file_descriptors = max_file_descriptors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_time_seconds": self.cpu_time_seconds,
            "memory_mb": self.memory_mb,
            "disk_space_mb": self.disk_space_mb,
            "max_processes": self.max_processes,
            "network_bandwidth_mb": self.network_bandwidth_mb,
            "max_file_descriptors": self.max_file_descriptors
        }


class NetworkPolicy:
    """网络访问策略"""
    
    def __init__(
        self,
        allow_outbound: bool = False,
        allowed_hosts: List[str] = None,
        allowed_ports: List[int] = None,
        max_connections: int = 5
    ):
        self.allow_outbound = allow_outbound
        self.allowed_hosts = allowed_hosts or []
        self.allowed_ports = allowed_ports or []
        self.max_connections = max_connections
    
    def is_allowed(self, host: str, port: int) -> bool:
        """检查网络访问是否允许"""
        if not self.allow_outbound:
            return False
        
        # 检查主机白名单
        if self.allowed_hosts and host not in self.allowed_hosts:
            return False
        
        # 检查端口白名单
        if self.allowed_ports and port not in self.allowed_ports:
            return False
        
        return True


class FileAccessPolicy:
    """文件访问策略"""
    
    def __init__(
        self,
        allowed_paths: List[str] = None,
        denied_paths: List[str] = None,
        read_only: bool = True,
        max_file_size_mb: int = 10
    ):
        self.allowed_paths = allowed_paths or []
        self.denied_paths = denied_paths or []
        self.read_only = read_only
        self.max_file_size_mb = max_file_size_mb
    
    def is_allowed(self, file_path: str, operation: str = "read") -> bool:
        """检查文件访问是否允许"""
        # 检查拒绝列表（优先级更高）
        for denied in self.denied_paths:
            if file_path.startswith(denied):
                return False
        
        # 检查允许列表
        if self.allowed_paths:
            allowed = False
            for allowed_path in self.allowed_paths:
                if file_path.startswith(allowed_path):
                    allowed = True
                    break
            if not allowed:
                return False
        
        # 检查读写权限
        if operation == "write" and self.read_only:
            return False
        
        return True


class SecurityAuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or "/tmp/security_sandbox_audit.log"
        self.audit_entries: List[Dict[str, Any]] = []
    
    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Dict[str, Any] = None,
        user: str = None,
        tool: str = None
    ):
        """记录安全审计事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "details": details or {},
            "user": user or "unknown",
            "tool": tool or "unknown"
        }
        
        self.audit_entries.append(entry)
        
        # 写入日志文件
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")
        
        # 同时记录到系统日志
        log_message = f"[SECURITY] {event_type}: {message}"
        if severity == "critical":
            logger.critical(log_message)
        elif severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的审计事件"""
        return self.audit_entries[-limit:]


class SecuritySandbox:
    """安全沙箱 - 核心沙箱执行环境"""
    
    def __init__(
        self,
        sandbox_id: str,
        security_level: SecurityLevel = SecurityLevel.RESTRICTED,
        resource_quota: ResourceQuota = None,
        network_policy: NetworkPolicy = None,
        file_access_policy: FileAccessPolicy = None
    ):
        self.sandbox_id = sandbox_id
        self.security_level = security_level
        self.resource_quota = resource_quota or ResourceQuota()
        self.network_policy = network_policy or NetworkPolicy()
        self.file_access_policy = file_access_policy or FileAccessPolicy()
        self.audit_logger = SecurityAuditLogger()
        self.temp_dir = None
        self.created_at = time.time()
        self.is_active = False
        
        # 初始化沙箱环境
        self._init_sandbox_environment()
        
        logger.info(f"安全沙箱初始化完成: {sandbox_id}, 安全级别: {security_level.value}")
    
    def _init_sandbox_environment(self):
        """初始化沙箱环境"""
        try:
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp(prefix=f"sandbox_{self.sandbox_id}_")
            logger.debug(f"沙箱临时目录: {self.temp_dir}")
            
            # 根据安全级别设置默认策略
            if self.security_level == SecurityLevel.UNTRUSTED:
                self.resource_quota = ResourceQuota(
                    cpu_time_seconds=10.0,
                    memory_mb=128,
                    disk_space_mb=50,
                    max_processes=5,
                    network_bandwidth_mb=1,
                    max_file_descriptors=50
                )
                self.network_policy = NetworkPolicy(allow_outbound=False)
                self.file_access_policy = FileAccessPolicy(
                    allowed_paths=[self.temp_dir],
                    read_only=False
                )
            
            elif self.security_level == SecurityLevel.RESTRICTED:
                self.resource_quota = ResourceQuota(
                    cpu_time_seconds=30.0,
                    memory_mb=256,
                    disk_space_mb=100,
                    max_processes=10,
                    network_bandwidth_mb=10,
                    max_file_descriptors=100
                )
                self.network_policy = NetworkPolicy(
                    allow_outbound=True,
                    allowed_hosts=["api.deepseek.com", "localhost"],
                    allowed_ports=[80, 443, 8080, 8081]
                )
                self.file_access_policy = FileAccessPolicy(
                    allowed_paths=[self.temp_dir, "/tmp", "/var/tmp"],
                    read_only=False
                )
            
            elif self.security_level == SecurityLevel.TRUSTED:
                self.resource_quota = ResourceQuota(
                    cpu_time_seconds=60.0,
                    memory_mb=512,
                    disk_space_mb=500,
                    max_processes=20,
                    network_bandwidth_mb=100,
                    max_file_descriptors=200
                )
                self.network_policy = NetworkPolicy(allow_outbound=True)
                self.file_access_policy = FileAccessPolicy(read_only=False)
        
        except Exception as e:
            logger.error(f"沙箱环境初始化失败: {e}")
            raise
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """在沙箱中执行工具"""
        self.is_active = True
        start_time = time.time()
        
        # 记录执行开始
        self.audit_logger.log_event(
            event_type="tool_execution_start",
            severity="info",
            message=f"开始执行工具: {tool_name}",
            details={
                "sandbox_id": self.sandbox_id,
                "security_level": self.security_level.value,
                "args": str(args),
                "kwargs": str(kwargs)
            },
            tool=tool_name
        )
        
        try:
            # 应用资源限制
            self._apply_resource_limits()
            
            # 执行前检查
            await self._pre_execution_checks(tool_name, args, kwargs)
            
            # 执行工具函数
            if asyncio.iscoroutinefunction(tool_func):
                result = await self._execute_with_timeout(tool_func, *args, **kwargs)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._execute_sync_with_timeout, tool_func, args, kwargs
                )
            
            # 执行成功
            execution_time = time.time() - start_time
            
            self.audit_logger.log_event(
                event_type="tool_execution_success",
                severity="info",
                message=f"工具执行成功: {tool_name}",
                details={
                    "sandbox_id": self.sandbox_id,
                    "execution_time": execution_time,
                    "result_type": type(result).__name__
                },
                tool=tool_name
            )
            
            return result
            
        except SandboxViolation as e:
            # 沙箱违规
            execution_time = time.time() - start_time
            
            self.audit_logger.log_event(
                event_type="sandbox_violation",
                severity="warning",
                message=f"沙箱违规: {e.violation_type.value}",
                details={
                    "sandbox_id": self.sandbox_id,
                    "violation_type": e.violation_type.value,
                    "message": e.message,
                    "execution_time": execution_time,
                    "details": e.details
                },
                tool=tool_name
            )
            
            raise
            
        except Exception as e:
            # 其他执行错误
            execution_time = time.time() - start_time
            
            self.audit_logger.log_event(
                event_type="tool_execution_error",
                severity="error",
                message=f"工具执行错误: {str(e)}",
                details={
                    "sandbox_id": self.sandbox_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "execution_time": execution_time,
                    "traceback": traceback.format_exc()
                },
                tool=tool_name
            )
            
            raise
            
        finally:
            self.is_active = False
            # 清理资源
            await self._cleanup()
    
    def _apply_resource_limits(self):
        """应用资源限制（Unix系统）"""
        try:
            # 设置CPU时间限制
            cpu_time = int(self.resource_quota.cpu_time_seconds)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))
            
            # 设置内存限制
            memory_bytes = self.resource_quota.memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            
            # 设置文件描述符限制
            resource.setrlimit(resource.RLIMIT_NOFILE, 
                             (self.resource_quota.max_file_descriptors, 
                              self.resource_quota.max_file_descriptors))
            
            # 设置进程数限制
            resource.setrlimit(resource.RLIMIT_NPROC,
                             (self.resource_quota.max_processes,
                              self.resource_quota.max_processes))
            
        except (resource.error, AttributeError) as e:
            # 在某些系统或环境下可能不支持某些限制
            logger.debug(f"资源限制设置部分失败（可能不支持）: {e}")
    
    async def _pre_execution_checks(self, tool_name: str, args: tuple, kwargs: dict):
        """执行前安全检查"""
        # 检查网络访问
        if self._requires_network_access(tool_name, args, kwargs):
            self._check_network_access()
        
        # 检查文件访问
        file_accesses = self._extract_file_accesses(tool_name, args, kwargs)
        for file_path, operation in file_accesses:
            self._check_file_access(file_path, operation)
    
    def _requires_network_access(self, tool_name: str, args: tuple, kwargs: dict) -> bool:
        """检查工具是否需要网络访问"""
        # 这里可以根据工具名称或参数判断是否需要网络访问
        network_tools = ["curl", "wget", "http", "api_call", "download", "fetch"]
        return any(network_tool in tool_name.lower() for network_tool in network_tools)
    
    def _check_network_access(self):
        """检查网络访问权限"""
        if not self.network_policy.allow_outbound:
            raise SandboxViolation(
                violation_type=SandboxViolationType.NETWORK_ACCESS_DENIED,
                message="网络访问被策略禁止",
                details={"policy": self.network_policy.__dict__}
            )
    
    def _extract_file_accesses(self, tool_name: str, args: tuple, kwargs: dict) -> List[Tuple[str, str]]:
        """从参数中提取文件访问信息"""
        file_accesses = []
        
        # 检查参数中的文件路径
        for arg in args:
            if isinstance(arg, str) and ("/" in arg or "\\" in arg):
                # 简单判断是否为文件路径
                file_accesses.append((arg, "read"))
        
        # 检查kwargs中的文件路径
        for key, value in kwargs.items():
            if isinstance(value, str) and ("/" in value or "\\" in value):
                file_accesses.append((value, "write" if "write" in key.lower() or "output" in key.lower() else "read"))
        
        return file_accesses
    
    def _check_file_access(self, file_path: str, operation: str = "read"):
        """检查文件访问权限"""
        if not self.file_access_policy.is_allowed(file_path, operation):
            raise SandboxViolation(
                violation_type=SandboxViolationType.FILE_ACCESS_DENIED,
                message=f"文件访问被拒绝: {file_path} ({operation})",
                details={
                    "file_path": file_path,
                    "operation": operation,
                    "policy": self.file_access_policy.__dict__
                }
            )
    
    async def _execute_with_timeout(self, coro_func, *args, **kwargs):
        """带超时的异步执行"""
        try:
            return await asyncio.wait_for(
                coro_func(*args, **kwargs),
                timeout=self.resource_quota.cpu_time_seconds
            )
        except asyncio.TimeoutError:
            raise SandboxViolation(
                violation_type=SandboxViolationType.EXECUTION_TIMEOUT,
                message=f"执行超时 ({self.resource_quota.cpu_time_seconds}秒)",
                details={"timeout_seconds": self.resource_quota.cpu_time_seconds}
            )
    
    def _execute_sync_with_timeout(self, func, args, kwargs):
        """带超时的同步执行（在线程池中）"""
        result = [None]
        exception = [None]
        
        def wrapper():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=wrapper)
        thread.start()
        thread.join(timeout=self.resource_quota.cpu_time_seconds)
        
        if thread.is_alive():
            # 线程仍在运行，超时了
            # 注意：这里无法真正终止线程，只能标记超时
            raise SandboxViolation(
                violation_type=SandboxViolationType.EXECUTION_TIMEOUT,
                message=f"执行超时 ({self.resource_quota.cpu_time_seconds}秒)",
                details={"timeout_seconds": self.resource_quota.cpu_time_seconds}
            )
        
        if exception[0] is not None:
            raise exception[0]
        
        return result[0]
    
    async def _cleanup(self):
        """清理沙箱资源"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                # 删除临时目录
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.debug(f"清理沙箱临时目录: {self.temp_dir}")
        except Exception as e:
            logger.error(f"沙箱清理失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取沙箱状态"""
        return {
            "sandbox_id": self.sandbox_id,
            "security_level": self.security_level.value,
            "is_active": self.is_active,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "uptime_seconds": time.time() - self.created_at,
            "resource_quota": self.resource_quota.to_dict(),
            "temp_dir": self.temp_dir
        }


class SecuritySandboxManager:
    """安全沙箱管理器"""
    
    def __init__(self):
        self.sandboxes: Dict[str, SecuritySandbox] = {}
        self.default_security_level = SecurityLevel.RESTRICTED
        self.audit_logger = SecurityAuditLogger()
        logger.info("安全沙箱管理器初始化完成")
    
    def create_sandbox(
        self,
        sandbox_id: str = None,
        security_level: SecurityLevel = None,
        resource_quota: ResourceQuota = None,
        network_policy: NetworkPolicy = None,
        file_access_policy: FileAccessPolicy = None
    ) -> SecuritySandbox:
        """创建新的安全沙箱"""
        if sandbox_id is None:
            sandbox_id = f"sandbox_{int(time.time())}_{len(self.sandboxes)}"
        
        if sandbox_id in self.sandboxes:
            raise ValueError(f"沙箱ID已存在: {sandbox_id}")
        
        security_level = security_level or self.default_security_level
        
        sandbox = SecuritySandbox(
            sandbox_id=sandbox_id,
            security_level=security_level,
            resource_quota=resource_quota,
            network_policy=network_policy,
            file_access_policy=file_access_policy
        )
        
        self.sandboxes[sandbox_id] = sandbox
        
        self.audit_logger.log_event(
            event_type="sandbox_created",
            severity="info",
            message=f"创建安全沙箱: {sandbox_id}",
            details={
                "sandbox_id": sandbox_id,
                "security_level": security_level.value
            }
        )
        
        return sandbox
    
    def get_sandbox(self, sandbox_id: str) -> Optional[SecuritySandbox]:
        """获取沙箱实例"""
        return self.sandboxes.get(sandbox_id)
    
    def destroy_sandbox(self, sandbox_id: str):
        """销毁沙箱"""
        if sandbox_id in self.sandboxes:
            sandbox = self.sandboxes[sandbox_id]
            if sandbox.is_active:
                logger.warning(f"尝试销毁活动中的沙箱: {sandbox_id}")
            
            # 清理沙箱
            asyncio.create_task(sandbox._cleanup())
            
            del self.sandboxes[sandbox_id]
            
            self.audit_logger.log_event(
                event_type="sandbox_destroyed",
                severity="info",
                message=f"销毁安全沙箱: {sandbox_id}",
                details={"sandbox_id": sandbox_id}
            )
    
    async def execute_in_sandbox(
        self,
        tool_name: str,
        tool_func: Callable,
        sandbox_id: str = None,
        *args,
        **kwargs
    ) -> Any:
        """在沙箱中执行工具"""
        if sandbox_id is None:
            # 创建临时沙箱
            sandbox = self.create_sandbox()
            destroy_after = True
        else:
            sandbox = self.get_sandbox(sandbox_id)
            if sandbox is None:
                raise ValueError(f"沙箱不存在: {sandbox_id}")
            destroy_after = False
        
        try:
            result = await sandbox.execute_tool(tool_name, tool_func, *args, **kwargs)
            return result
        finally:
            if destroy_after:
                self.destroy_sandbox(sandbox.sandbox_id)
    
    def get_all_sandbox_status(self) -> Dict[str, Any]:
        """获取所有沙箱状态"""
        status = {}
        for sandbox_id, sandbox in self.sandboxes.items():
            status[sandbox_id] = sandbox.get_status()
        return status
    
    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        recent_events = self.audit_logger.get_recent_events(limit=50)
        
        # 统计违规类型
        violation_counts = {}
        for event in recent_events:
            if event["event_type"] == "sandbox_violation":
                violation_type = event["details"].get("violation_type")
                if violation_type:
                    violation_counts[violation_type] = violation_counts.get(violation_type, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_sandboxes": len(self.sandboxes),
            "active_sandboxes": sum(1 for s in self.sandboxes.values() if s.is_active),
            "recent_events_count": len(recent_events),
            "violation_counts": violation_counts,
            "recent_events": recent_events[-10:]  # 最近10个事件
        }


# 全局实例和便捷函数
_sandbox_manager: Optional[SecuritySandboxManager] = None

def get_security_sandbox_manager() -> SecuritySandboxManager:
    """获取安全沙箱管理器实例"""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SecuritySandboxManager()
    return _sandbox_manager

async def execute_in_sandbox(tool_name: str, tool_func: Callable, *args, **kwargs) -> Any:
    """在沙箱中执行工具（便捷函数）"""
    manager = get_security_sandbox_manager()
    return await manager.execute_in_sandbox(tool_name, tool_func, *args, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def test_sandbox():
        print("=" * 60)
        print("测试安全沙箱系统")
        print("=" * 60)
        
        manager = SecuritySandboxManager()
        
        # 测试工具函数
        def test_tool(file_path: str):
            with open(file_path, "w") as f:
                f.write("test content")
            return "file_written"
        
        # 在沙箱中执行
        try:
            result = await manager.execute_in_sandbox(
                "test_file_tool",
                test_tool,
                "/tmp/test_file.txt"  # 这个路径应该被允许或拒绝
            )
            print(f"工具执行结果: {result}")
        except SandboxViolation as e:
            print(f"沙箱违规（预期中）: {e}")
        except Exception as e:
            print(f"其他错误: {e}")
        
        # 获取状态报告
        status = manager.get_all_sandbox_status()
        print(f"\n沙箱状态: {len(status)} 个沙箱")
        
        report = manager.get_security_report()
        print(f"安全报告: {report['total_sandboxes']} 个沙箱, {report['recent_events_count']} 个事件")
        
        print("=" * 60)
        print("✅ 安全沙箱系统测试完成")
        print("=" * 60)
    
    asyncio.run(test_sandbox())