#!/usr/bin/env python3
"""
基础服务组件 - 重构版本
使用统一的核心工具模块
"""

import logging
from typing import Any, Dict, Optional


def get_core_logger(name: str) -> logging.Logger:
    """获取核心日志记录器"""
    logger = logging.getLogger(f"core.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


class CoreService:
    """核心服务基类"""
    
    def __init__(self, name: str):
        """初始化服务"""
        self.name = name
        self.logger = get_core_logger(name)
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理服务相关资源
            self._cleanup_service_resources()
            
            # 清理缓存
            self._cleanup_caches()
            
            # 清理连接
            self._cleanup_connections()
            
            # 记录清理历史
            self._record_cleanup()
            
        except Exception as e:
            # 记录清理错误
            if not hasattr(self, 'cleanup_errors'):
                self.cleanup_errors = []
            self.cleanup_errors.append({
                'error': str(e),
                'timestamp': time.time()
            })
    
    def _cleanup_service_resources(self):
        """清理服务资源"""
        if hasattr(self, 'resources'):
            for resource in self.resources:
                if hasattr(resource, 'close'):
                    resource.close()
            self.resources.clear()
    
    def _cleanup_caches(self):
        """清理缓存"""
        if hasattr(self, 'caches'):
            for cache in self.caches.values():
                if hasattr(cache, 'clear'):
                    cache.clear()
            self.caches.clear()
    
    def _cleanup_connections(self):
        """清理连接"""
        if hasattr(self, 'connections'):
            for connection in self.connections:
                if hasattr(connection, 'close'):
                    connection.close()
            self.connections.clear()
    
    def _record_cleanup(self):
        """记录清理历史"""
        if not hasattr(self, 'cleanup_history'):
            self.cleanup_history = []
        
        self.cleanup_history.append({
            'timestamp': time.time(),
            'service': self.__class__.__name__
        })


class Component(CoreService):
    """基础服务类 - 重构版本"""
    
    def __init__(self, name: str):
        """初始化服务"""
        super().__init__(name)
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data


class ServiceManager:
    """服务管理器 - 重构版本"""
    
    def __init__(self):
        """初始化服务管理器"""
        self.logger = get_core_logger("ServiceManager")
        self.services: Dict[str, Any] = {}
    
    def register_service(self, name: str, service: Any) -> bool:
        """注册服务"""
        try:
            self.services[name] = service
            self.logger.info(f"服务 {name} 注册成功")
            return True
        except Exception as e:
            self.logger.error(f"服务 {name} 注册失败: {e}")
            return False
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务"""
        return self.services.get(name)
    
    def cleanup_all(self) -> None:
        """清理所有服务"""
        for service in self.services.values():
            if hasattr(service, 'cleanup'):
                service.cleanup()
        self.services.clear()
        self.logger.info("所有服务已清理")
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            return {
                "name": self.name,
                "services_count": len(self.services),
                "service_names": list(self.services.keys()),
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "status": "healthy",
                "services": {},
                "timestamp": time.time()
            }
            
            # 检查每个服务的健康状态
            for service_name, service in self.services.items():
                try:
                    if hasattr(service, 'health_check'):
                        service_health = service.health_check()
                        health_status["services"][service_name] = service_health
                    else:
                        health_status["services"][service_name] = {"status": "unknown"}
                except Exception as e:
                    health_status["services"][service_name] = {"status": "error", "error": str(e)}
            
            # 检查整体健康状态
            error_services = [name for name, status in health_status["services"].items() 
                            if status.get("status") == "error"]
            if error_services:
                health_status["status"] = "degraded"
                health_status["error_services"] = error_services
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        try:
            metrics = {
                "total_services": len(self.services),
                "service_types": {},
                "average_service_age": 0.0,
                "timestamp": time.time()
            }
            
            # 统计服务类型
            for service in self.services.values():
                service_type = type(service).__name__
                metrics["service_types"][service_type] = metrics["service_types"].get(service_type, 0) + 1
            
            # 计算平均服务年龄
            if hasattr(self, 'service_creation_times'):
                current_time = time.time()
                ages = [current_time - creation_time for creation_time in self.service_creation_times.values()]
                metrics["average_service_age"] = sum(ages) / len(ages) if ages else 0.0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"获取服务指标失败: {e}")
            return {"error": str(e)}
    
    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        try:
            if service_name not in self.services:
                self.logger.warning(f"服务 {service_name} 不存在")
                return False
            
            service = self.services[service_name]
            
            # 停止服务
            if hasattr(service, 'stop'):
                service.stop()
            
            # 清理服务
            if hasattr(service, 'cleanup'):
                service.cleanup()
            
            # 重新初始化服务
            if hasattr(service, 'initialize'):
                service.initialize()
            
            # 启动服务
            if hasattr(service, 'start'):
                service.start()
            
            self.logger.info(f"服务 {service_name} 重启成功")
            return True
            
        except Exception as e:
            self.logger.error(f"重启服务 {service_name} 失败: {e}")
            return False
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务信息"""
        try:
            if service_name not in self.services:
                return None
            
            service = self.services[service_name]
            info = {
                "name": service_name,
                "type": type(service).__name__,
                "module": service.__class__.__module__,
                "timestamp": time.time()
            }
            
            # 添加服务特定信息
            if hasattr(service, 'get_status'):
                info["status"] = service.get_status()
            
            if hasattr(service, 'get_metrics'):
                info["metrics"] = service.get_metrics()
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取服务信息失败: {e}")
            return None


# 添加缺失的导入
import time
from typing import Dict, Any, Optional