import os
#!/usr/bin/env python3
"""
依赖检查器 - 检查系统依赖包状态
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DependencyStatus(Enum):
    """依赖状态"""
    AVAILABLE = "available"
    MISSING = "missing"
    OPTIONAL = "optional"
    ERROR = "error"


@dataclass
class DependencyInfo:
    """依赖信息"""
    name: str
    status: DependencyStatus
    version: Optional[str] = None
    description: str = ""
    required: bool = False


class DependencyChecker:
    """依赖检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dependencies = self._initialize_dependencies()
    
    def _initialize_dependencies(self) -> Dict[str, DependencyInfo]:
        """初始化依赖列表"""
        dependencies = {
            # 核心依赖
            "numpy": DependencyInfo(
                name="numpy",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="数值计算库"
            ),
            "logging": DependencyInfo(
                name="logging",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="日志记录"
            ),
            "json": DependencyInfo(
                name="json",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="JSON处理"
            ),
            "time": DependencyInfo(
                name="time",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="时间处理"
            ),
            "re": DependencyInfo(
                name="re",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="正则表达式"
            ),
            "hashlib": DependencyInfo(
                name="hashlib",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="哈希算法"
            ),
            "secrets": DependencyInfo(
                name="secrets",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="安全随机数"
            ),
            "asyncio": DependencyInfo(
                name="asyncio",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="异步编程"
            ),
            "threading": DependencyInfo(
                name="threading",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="多线程"
            ),
            "concurrent.futures": DependencyInfo(
                name="concurrent.futures",
                status=DependencyStatus.AVAILABLE,
                required=True,
                description="并发执行"
            ),
            
            # 可选依赖
            "pyotp": DependencyInfo(
                name="pyotp",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="TOTP多因子认证"
            ),
            "qrcode": DependencyInfo(
                name="qrcode",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="QR码生成"
            ),
            "PIL": DependencyInfo(
                name="PIL",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="图像处理"
            ),
            "cv2": DependencyInfo(
                name="cv2",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="OpenCV计算机视觉"
            ),
            "sklearn": DependencyInfo(
                name="sklearn",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="机器学习库"
            ),
            "tensorflow": DependencyInfo(
                name="tensorflow",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="深度学习框架"
            ),
            "torch": DependencyInfo(
                name="torch",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="PyTorch深度学习"
            ),
            "nltk": DependencyInfo(
                name="nltk",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="自然语言处理"
            ),
            "spacy": DependencyInfo(
                name="spacy",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="高级NLP库"
            ),
            "psutil": DependencyInfo(
                name="psutil",
                status=DependencyStatus.OPTIONAL,
                required=False,
                description="系统监控"
            )
        }
    
    def check_all_dependencies(self) -> Dict[str, DependencyInfo]:
        """检查所有依赖"""
        for name, dep_info in self.dependencies.items():
            self._check_dependency(name, dep_info)
        
        return self.dependencies.copy()
    
    def _check_dependency(self, name: str, dep_info: DependencyInfo):
        """检查单个依赖"""
        try:
            if name == "numpy":
                import numpy  # type: ignore
                dep_info.version = getattr(numpy, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "pyotp":
                import pyotp  # type: ignore
                dep_info.version = getattr(pyotp, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "qrcode":
                import qrcode  # type: ignore
                dep_info.version = getattr(qrcode, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "PIL":
                import PIL  # type: ignore
                dep_info.version = getattr(PIL, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "cv2":
                import cv2  # type: ignore
                dep_info.version = getattr(cv2, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "sklearn":
                import sklearn  # type: ignore
                dep_info.version = getattr(sklearn, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "tensorflow":
                import tensorflow  # type: ignore
                dep_info.version = getattr(tensorflow, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "torch":
                import torch  # type: ignore
                dep_info.version = getattr(torch, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "nltk":
                import nltk  # type: ignore
                dep_info.version = getattr(nltk, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "spacy":
                import spacy  # type: ignore
                dep_info.version = getattr(spacy, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            elif name == "psutil":
                import psutil  # type: ignore
                dep_info.version = getattr(psutil, '__version__', 'unknown')
                dep_info.status = DependencyStatus.AVAILABLE
            else:
                # 对于内置模块，假设总是可用
                dep_info.status = DependencyStatus.AVAILABLE
                dep_info.version = "builtin"
                
        except ImportError:
            if dep_info.required:
                dep_info.status = DependencyStatus.MISSING
                self.logger.error(f"缺少必需依赖: {name}")
            else:
                dep_info.status = DependencyStatus.OPTIONAL
                self.logger.debug(f"可选依赖不可用: {name}")
        except Exception as e:
            dep_info.status = DependencyStatus.ERROR
            self.logger.error(f"检查依赖 {name} 时出错: {e}")
    
    def get_available_dependencies(self) -> List[str]:
        """获取可用的依赖列表"""
        return [name for name, dep in self.dependencies.items() 
                if dep.status == DependencyStatus.AVAILABLE]
    
    def get_missing_required_dependencies(self) -> List[str]:
        """获取缺失的必需依赖"""
        return [name for name, dep in self.dependencies.items() 
                if dep.status == DependencyStatus.MISSING and dep.required]
    
    def get_optional_dependencies(self) -> List[str]:
        """获取可选依赖"""
        return [name for name, dep in self.dependencies.items() 
                if not dep.required]
    
    def get_available_optional_dependencies(self) -> List[str]:
        """获取可用的可选依赖"""
        return [name for name, dep in self.dependencies.items() 
                if dep.status == DependencyStatus.AVAILABLE and not dep.required]
    
    def generate_dependency_report(self) -> Dict[str, Any]:
        """生成依赖报告"""
        self.check_all_dependencies()
        
        total_deps = len(self.dependencies)
        available_deps = len(self.get_available_dependencies())
        missing_required = len(self.get_missing_required_dependencies())
        available_optional = len(self.get_available_optional_dependencies())
        
        return {
            "summary": {
                "total_dependencies": total_deps,
                "available_dependencies": available_deps,
                "missing_required": missing_required,
                "health_score": (available_deps / total_deps) * 100
            },
            "dependencies": {
                name: {
                    "status": dep.status.value,
                    "version": dep.version,
                    "required": dep.required,
                    "description": dep.description
                }
                for name, dep in self.dependencies.items()
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []
        
        missing_required = self.get_missing_required_dependencies()
        if missing_required:
            recommendations.append(f"安装缺失的必需依赖: {', '.join(missing_required)}")
        
        available_optional = self.get_available_optional_dependencies()
        if not available_optional:
            recommendations.append("考虑安装可选依赖以增强功能")
        
        # 检查AI相关依赖
        ai_deps = ["tensorflow", "torch", "sklearn", "nltk", "spacy"]
        available_ai_deps = [dep for dep in ai_deps if dep in available_optional]
        if not available_ai_deps:
            recommendations.append("安装AI相关依赖以启用机器学习功能")
        
        # 检查安全相关依赖
        security_deps = ["pyotp", "qrcode"]
        available_security_deps = [dep for dep in security_deps if dep in available_optional]
        if not available_security_deps:
            recommendations.append("安装安全相关依赖以启用多因子认证功能")
        
        return recommendations


# 全局实例
dependency_checker = DependencyChecker()


def get_dependency_checker():
    """获取依赖检查器实例"""
    return dependency_checker
