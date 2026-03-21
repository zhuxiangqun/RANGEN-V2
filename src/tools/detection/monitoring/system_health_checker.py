#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统健康检查器 - 自动检测和修复系统问题
提供全面的系统健康检查、问题诊断和自动修复功能
"""

import asyncio
import logging
import sys
import os
import importlib
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None

@dataclass
class SystemHealthReport:
    """系统健康报告"""
    overall_status: HealthStatus
    total_checks: int
    healthy_checks: int
    warning_checks: int
    critical_checks: int
    unknown_checks: int
    check_results: List[HealthCheckResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.check_results = []
        self.auto_fix_enabled = True
        self.check_history = []
        
        # 健康检查配置
        self.check_config = {
            'import_checks': True,
            'syntax_checks': True,
            'dependency_checks': True,
            'performance_checks': True,
            'integration_checks': True,
            'security_checks': True
        }
        
        logger.info("🏥 系统健康检查器初始化完成")
    
    async def run_comprehensive_health_check(self) -> SystemHealthReport:
        """运行综合健康检查"""
        logger.info("🔍 开始综合系统健康检查")
        
        self.check_results = []
        
        # 1. 导入检查
        if self.check_config['import_checks']:
            await self._check_imports()
        
        # 2. 语法检查
        if self.check_config['syntax_checks']:
            await self._check_syntax()
        
        # 3. 依赖检查
        if self.check_config['dependency_checks']:
            await self._check_dependencies()
        
        # 4. 性能检查
        if self.check_config['performance_checks']:
            await self._check_performance()
        
        # 5. 集成检查
        if self.check_config['integration_checks']:
            await self._check_integration()
        
        # 6. 安全检查
        if self.check_config['security_checks']:
            await self._check_security()
        
        # 生成报告
        report = self._generate_health_report()
        
        # 记录到历史
        self.check_history.append(report)
        
        logger.info(f"✅ 健康检查完成: {report.overall_status.value}")
        return report
    
    async def _check_imports(self):
        """检查模块导入"""
        logger.info("🔍 检查模块导入")
        
        critical_modules = [
            'src.utils.enhanced_system_integration',
            'src.utils.mcp_protocol',
            'src.utils.advanced_rag_infrastructure',
            'src.utils.advanced_semantic_compression',
            'src.utils.enhanced_context_engineering',
            'src.agents.base_agent',
            'src.utils.unified_centers'
        ]
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
                self.check_results.append(HealthCheckResult(
                    component=f"import_{module_name}",
                    status=HealthStatus.HEALTHY,
                    message=f"模块 {module_name} 导入成功",
                    auto_fixable=False
                ))
            except ImportError as e:
                self.check_results.append(HealthCheckResult(
                    component=f"import_{module_name}",
                    status=HealthStatus.CRITICAL,
                    message=f"模块 {module_name} 导入失败: {e}",
                    auto_fixable=True,
                    fix_suggestion="检查模块路径和依赖关系"
                ))
            except Exception as e:
                self.check_results.append(HealthCheckResult(
                    component=f"import_{module_name}",
                    status=HealthStatus.CRITICAL,
                    message=f"模块 {module_name} 导入异常: {e}",
                    auto_fixable=False
                ))
    
    async def _check_syntax(self):
        """检查语法错误"""
        logger.info("🔍 检查语法错误")
        
        # 检查关键文件的语法
        critical_files = [
            'src/utils/enhanced_system_integration.py',
            'src/utils/mcp_protocol.py',
            'src/utils/advanced_rag_infrastructure.py',
            'src/utils/advanced_semantic_compression.py',
            'src/utils/enhanced_context_engineering.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试编译检查语法
                    compile(content, file_path, 'exec')
                    
                    self.check_results.append(HealthCheckResult(
                        component=f"syntax_{file_path}",
                        status=HealthStatus.HEALTHY,
                        message=f"文件 {file_path} 语法正确",
                        auto_fixable=False
                    ))
                    
                except SyntaxError as e:
                    self.check_results.append(HealthCheckResult(
                        component=f"syntax_{file_path}",
                        status=HealthStatus.CRITICAL,
                        message=f"文件 {file_path} 语法错误: {e}",
                        auto_fixable=True,
                        fix_suggestion=f"修复第 {e.lineno} 行的语法错误"
                    ))
                except Exception as e:
                    self.check_results.append(HealthCheckResult(
                        component=f"syntax_{file_path}",
                        status=HealthStatus.WARNING,
                        message=f"文件 {file_path} 检查异常: {e}",
                        auto_fixable=False
                    ))
            else:
                self.check_results.append(HealthCheckResult(
                    component=f"syntax_{file_path}",
                    status=HealthStatus.CRITICAL,
                    message=f"文件 {file_path} 不存在",
                    auto_fixable=False
                ))
    
    async def _check_dependencies(self):
        """检查依赖关系"""
        logger.info("🔍 检查依赖关系")
        
        required_packages = [
            'asyncio',
            'logging',
            'datetime',
            'typing',
            'dataclasses',
            'json',
            'threading',
            'collections'
        ]
        
        optional_packages = [
            'psutil',
            'numpy',
            'sentence_transformers',
            'faiss'
        ]
        
        # 检查必需包
        for package in required_packages:
            try:
                importlib.import_module(package)
                self.check_results.append(HealthCheckResult(
                    component=f"dependency_{package}",
                    status=HealthStatus.HEALTHY,
                    message=f"必需包 {package} 可用",
                    auto_fixable=False
                ))
            except ImportError:
                self.check_results.append(HealthCheckResult(
                    component=f"dependency_{package}",
                    status=HealthStatus.CRITICAL,
                    message=f"必需包 {package} 不可用",
                    auto_fixable=True,
                    fix_suggestion=f"安装包: pip install {package}"
                ))
        
        # 检查可选包
        for package in optional_packages:
            try:
                importlib.import_module(package)
                self.check_results.append(HealthCheckResult(
                    component=f"dependency_{package}",
                    status=HealthStatus.HEALTHY,
                    message=f"可选包 {package} 可用",
                    auto_fixable=False
                ))
            except ImportError:
                self.check_results.append(HealthCheckResult(
                    component=f"dependency_{package}",
                    status=HealthStatus.WARNING,
                    message=f"可选包 {package} 不可用，某些功能可能受限",
                    auto_fixable=True,
                    fix_suggestion=f"安装包: pip install {package}"
                ))
    
    async def _check_performance(self):
        """检查性能指标"""
        logger.info("🔍 检查性能指标")
        
        try:
            # 检查系统资源
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            # CPU使用率检查
            if cpu_usage < 50:
                cpu_status = HealthStatus.HEALTHY
                cpu_message = f"CPU使用率正常 ({cpu_usage:.1f}%)"
            elif cpu_usage < 80:
                cpu_status = HealthStatus.WARNING
                cpu_message = f"CPU使用率较高 ({cpu_usage:.1f}%)"
            else:
                cpu_status = HealthStatus.CRITICAL
                cpu_message = f"CPU使用率过高 ({cpu_usage:.1f}%)"
            
            self.check_results.append(HealthCheckResult(
                component="performance_cpu",
                status=cpu_status,
                message=cpu_message,
                details={'cpu_usage': cpu_usage},
                auto_fixable=cpu_status != HealthStatus.HEALTHY,
                fix_suggestion="优化算法或减少并发处理" if cpu_status != HealthStatus.HEALTHY else None
            ))
            
            # 内存使用率检查
            memory_usage = memory_info.percent
            if memory_usage < 70:
                memory_status = HealthStatus.HEALTHY
                memory_message = f"内存使用率正常 ({memory_usage:.1f}%)"
            elif memory_usage < 90:
                memory_status = HealthStatus.WARNING
                memory_message = f"内存使用率较高 ({memory_usage:.1f}%)"
            else:
                memory_status = HealthStatus.CRITICAL
                memory_message = f"内存使用率过高 ({memory_usage:.1f}%)"
            
            self.check_results.append(HealthCheckResult(
                component="performance_memory",
                status=memory_status,
                message=memory_message,
                details={'memory_usage': memory_usage, 'available_memory': memory_info.available},
                auto_fixable=memory_status != HealthStatus.HEALTHY,
                fix_suggestion="清理缓存或优化内存使用" if memory_status != HealthStatus.HEALTHY else None
            ))
            
        except ImportError:
            self.check_results.append(HealthCheckResult(
                component="performance_check",
                status=HealthStatus.WARNING,
                message="无法检查性能指标，psutil包未安装",
                auto_fixable=True,
                fix_suggestion="安装psutil包: pip install psutil"
            ))
        except Exception as e:
            self.check_results.append(HealthCheckResult(
                component="performance_check",
                status=HealthStatus.WARNING,
                message=f"性能检查异常: {e}",
                auto_fixable=False
            ))
    
    async def _check_integration(self):
        """检查系统集成"""
        logger.info("🔍 检查系统集成")
        
        try:
            # 检查增强系统集成
            from src.utils.enhanced_system_integration import get_enhanced_system_integration
            integration = get_enhanced_system_integration()
            
            # 测试基本功能
            test_response = await integration.process_query_enhanced(
                query="健康检查测试",
                user_id="health_checker",
                use_enhanced_features=True
            )
            
            if test_response['success']:
                self.check_results.append(HealthCheckResult(
                    component="integration_enhanced_system",
                    status=HealthStatus.HEALTHY,
                    message="增强系统集成正常",
                    details={'test_response': test_response},
                    auto_fixable=False
                ))
            else:
                self.check_results.append(HealthCheckResult(
                    component="integration_enhanced_system",
                    status=HealthStatus.CRITICAL,
                    message=f"增强系统集成异常: {test_response.get('error', '未知错误')}",
                    auto_fixable=True,
                    fix_suggestion="检查增强系统配置和依赖"
                ))
                
        except Exception as e:
            self.check_results.append(HealthCheckResult(
                component="integration_enhanced_system",
                status=HealthStatus.CRITICAL,
                message=f"增强系统集成检查失败: {e}",
                auto_fixable=True,
                fix_suggestion="重新初始化增强系统集成器"
            ))
    
    async def _check_security(self):
        """检查安全性"""
        logger.info("🔍 检查安全性")
        
        # 检查文件权限
        critical_files = [
            'src/utils/enhanced_system_integration.py',
            'src/utils/mcp_protocol.py',
            'src/utils/advanced_rag_infrastructure.py'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    stat = os.stat(file_path)
                    # 检查文件是否可读
                    if stat.st_mode & 0o444:
                        self.check_results.append(HealthCheckResult(
                            component=f"security_{file_path}",
                            status=HealthStatus.HEALTHY,
                            message=f"文件 {file_path} 权限正常",
                            auto_fixable=False
                        ))
                    else:
                        self.check_results.append(HealthCheckResult(
                            component=f"security_{file_path}",
                            status=HealthStatus.WARNING,
                            message=f"文件 {file_path} 权限异常",
                            auto_fixable=True,
                            fix_suggestion="调整文件权限"
                        ))
                except Exception as e:
                    self.check_results.append(HealthCheckResult(
                        component=f"security_{file_path}",
                        status=HealthStatus.WARNING,
                        message=f"文件 {file_path} 权限检查异常: {e}",
                        auto_fixable=False
                    ))
    
    def _generate_health_report(self) -> SystemHealthReport:
        """生成健康报告"""
        total_checks = len(self.check_results)
        healthy_checks = sum(1 for r in self.check_results if r.status == HealthStatus.HEALTHY)
        warning_checks = sum(1 for r in self.check_results if r.status == HealthStatus.WARNING)
        critical_checks = sum(1 for r in self.check_results if r.status == HealthStatus.CRITICAL)
        unknown_checks = sum(1 for r in self.check_results if r.status == HealthStatus.UNKNOWN)
        
        # 确定整体状态
        if critical_checks > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_checks > 0:
            overall_status = HealthStatus.WARNING
        elif healthy_checks == total_checks:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        # 生成建议
        recommendations = []
        if critical_checks > 0:
            recommendations.append(f"发现 {critical_checks} 个严重问题，需要立即修复")
        if warning_checks > 0:
            recommendations.append(f"发现 {warning_checks} 个警告，建议尽快处理")
        if healthy_checks == total_checks:
            recommendations.append("系统运行正常，建议定期进行健康检查")
        
        return SystemHealthReport(
            overall_status=overall_status,
            total_checks=total_checks,
            healthy_checks=healthy_checks,
            warning_checks=warning_checks,
            critical_checks=critical_checks,
            unknown_checks=unknown_checks,
            check_results=self.check_results.copy(),
            recommendations=recommendations
        )
    
    async def auto_fix_issues(self) -> Dict[str, Any]:
        """自动修复问题"""
        logger.info("🔧 开始自动修复问题")
        
        fix_results = {
            'total_issues': 0,
            'fixed_issues': 0,
            'failed_fixes': 0,
            'fix_details': []
        }
        
        for result in self.check_results:
            if result.auto_fixable and result.status != HealthStatus.HEALTHY:
                fix_results['total_issues'] += 1
                
                try:
                    # 根据问题类型执行修复
                    if result.component.startswith('import_'):
                        # 导入问题修复
                        success = await self._fix_import_issue(result)
                    elif result.component.startswith('syntax_'):
                        # 语法问题修复
                        success = await self._fix_syntax_issue(result)
                    elif result.component.startswith('dependency_'):
                        # 依赖问题修复
                        success = await self._fix_dependency_issue(result)
                    else:
                        success = False
                    
                    if success:
                        fix_results['fixed_issues'] += 1
                        fix_results['fix_details'].append({
                            'component': result.component,
                            'status': 'fixed',
                            'message': f"成功修复: {result.message}"
                        })
                    else:
                        fix_results['failed_fixes'] += 1
                        fix_results['fix_details'].append({
                            'component': result.component,
                            'status': 'failed',
                            'message': f"修复失败: {result.message}"
                        })
                        
                except Exception as e:
                    fix_results['failed_fixes'] += 1
                    fix_results['fix_details'].append({
                        'component': result.component,
                        'status': 'error',
                        'message': f"修复异常: {e}"
                    })
        
        logger.info(f"🔧 自动修复完成: {fix_results['fixed_issues']}/{fix_results['total_issues']} 个问题已修复")
        return fix_results
    
    async def _fix_import_issue(self, result: HealthCheckResult) -> bool:
        """修复导入问题"""
        # 这里可以实现具体的导入问题修复逻辑
        logger.info(f"🔧 尝试修复导入问题: {result.component}")
        return False  # 暂时返回False，实际实现需要根据具体情况
    
    async def _fix_syntax_issue(self, result: HealthCheckResult) -> bool:
        """修复语法问题"""
        # 这里可以实现具体的语法问题修复逻辑
        logger.info(f"🔧 尝试修复语法问题: {result.component}")
        return False  # 暂时返回False，实际实现需要根据具体情况
    
    async def _fix_dependency_issue(self, result: HealthCheckResult) -> bool:
        """修复依赖问题"""
        # 这里可以实现具体的依赖问题修复逻辑
        logger.info(f"🔧 尝试修复依赖问题: {result.component}")
        return False  # 暂时返回False，实际实现需要根据具体情况
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        if not self.check_history:
            return {'message': '尚未进行健康检查'}
        
        latest_report = self.check_history[-1]
        return {
            'overall_status': latest_report.overall_status.value,
            'total_checks': latest_report.total_checks,
            'healthy_checks': latest_report.healthy_checks,
            'warning_checks': latest_report.warning_checks,
            'critical_checks': latest_report.critical_checks,
            'health_percentage': (latest_report.healthy_checks / latest_report.total_checks * 100) if latest_report.total_checks > 0 else 0,
            'last_check_time': latest_report.timestamp.isoformat(),
            'recommendations': latest_report.recommendations
        }

# 全局健康检查器实例
_health_checker = None

def get_health_checker() -> SystemHealthChecker:
    """获取健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = SystemHealthChecker()
    return _health_checker

async def run_system_health_check() -> SystemHealthReport:
    """运行系统健康检查"""
    checker = get_health_checker()
    return await checker.run_comprehensive_health_check()