#!/usr/bin/env python3
"""
综合系统健康检查脚本
集成Mock检测和现有的监控系统，提供完整的系统健康状态
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSystemHealthChecker:
    """综合系统健康检查器"""
    
    def __init__(self):
        self.health_report = {}
        self.mock_detection_monitor = None
        self.performance_monitor = None
        self.resource_monitor = None
        self.error_recovery_manager = None
        
    async def initialize_monitors(self):
        """初始化所有监控器"""
        logger.info("🔧 初始化监控系统...")
        
        try:
            # 初始化Mock检测监控器
            from utils.mock_detection_monitor import get_mock_detection_monitor
            self.mock_detection_monitor = get_mock_detection_monitor()
            logger.info("✅ Mock检测监控器初始化成功")
            
            # 初始化性能监控器
            from utils.performance_monitor import get_global_monitor
            self.performance_monitor = get_global_monitor()
            logger.info("✅ 性能监控器初始化成功")
            
            # 初始化资源监控器
            from utils.resource_monitor import ResourceMonitor
            self.resource_monitor = ResourceMonitor()
            logger.info("✅ 资源监控器初始化成功")
            
            # 初始化错误恢复管理器
            from utils.error_recovery_manager import ErrorRecoveryManager
            self.error_recovery_manager = ErrorRecoveryManager()
            logger.info("✅ 错误恢复管理器初始化成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 监控器初始化失败: {e}")
            return False
    
    async def check_mock_usage_health(self):
        """检查Mock使用健康状态"""
        logger.info("🔍 检查Mock使用健康状态...")
        
        try:
            if not self.mock_detection_monitor:
                logger.warning("⚠️ Mock检测监控器未初始化")
                return False
            
            # 检查Mock使用情况
            summary = self.mock_detection_monitor.check_system_mock_usage()
            
            self.health_report['mock_usage'] = {
                'status': 'checked',
                'summary': summary,
                'health_level': summary['system_health'],
                'total_modules': summary['total_modules'],
                'active_mock_modules': len(summary['active_mock_modules'])
            }
            
            logger.info(f"✅ Mock使用健康检查完成，状态: {summary['system_health']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mock使用健康检查失败: {e}")
            self.health_report['mock_usage'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    async def check_performance_health(self):
        """检查性能健康状态"""
        logger.info("🔍 检查性能健康状态...")
        
        try:
            if not self.performance_monitor:
                logger.warning("⚠️ 性能监控器未初始化")
                return False
            
            # 获取性能指标
            current_metrics = self.performance_monitor.get_current_metrics()
            metrics_summary = self.performance_monitor.get_metrics_summary()
            
            self.health_report['performance'] = {
                'status': 'checked',
                'current_metrics': current_metrics,
                'metrics_summary': metrics_summary,
                'health_level': self._assess_performance_health(current_metrics)
            }
            
            logger.info("✅ 性能健康检查完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 性能健康检查失败: {e}")
            self.health_report['performance'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def _assess_performance_health(self, metrics: dict) -> str:
        """评估性能健康状态"""
        if not metrics:
            return "unknown"
        
        cpu_percent = metrics.get('cpu_percent', 0)
        memory_percent = metrics.get('memory_percent', 0)
        
        if cpu_percent > 90 or memory_percent > 90:
            return "critical"
        elif cpu_percent > 80 or memory_percent > 80:
            return "warning"
        elif cpu_percent > 70 or memory_percent > 70:
            return "attention"
        else:
            return "healthy"
    
    def generate_overall_health_assessment(self) -> str:
        """生成整体健康评估"""
        health_levels = []
        
        for component, status in self.health_report.items():
            if status['status'] == 'checked' and 'health_level' in status:
                health_levels.append(status['health_level'])
        
        if not health_levels:
            return "unknown"
        
        # 计算整体健康状态
        if "critical" in health_levels:
            return "critical"
        elif "warning" in health_levels:
            return "warning"
        elif "attention" in health_levels:
            return "attention"
        else:
            return "healthy"
    
    def print_health_report(self):
        """打印健康报告"""
        print("\n" + "="*60)
        print("🏥 综合系统健康检查报告")
        print("="*60)
        
        # 整体健康状态
        overall_health = self.generate_overall_health_assessment()
        health_emoji = {
            "healthy": "✅",
            "attention": "⚠️",
            "warning": "🚨",
            "critical": "💥",
            "unknown": "❓"
        }
        
        print(f"\n📊 整体健康状态: {health_emoji.get(overall_health, '❓')} {overall_health.upper()}")
        
        # 各组件健康状态
        for component, status in self.health_report.items():
            print(f"\n🔍 {component.replace('_', ' ').title()}:")
            
            if status['status'] == 'checked':
                health_level = status.get('health_level', 'unknown')
                emoji = health_emoji.get(health_level, '❓')
                print(f"  状态: {emoji} {health_level}")
                
                if component == 'mock_usage':
                    summary = status['summary']
                    print(f"  模块数: {summary['total_modules']}")
                    print(f"  Mock使用模块: {summary['active_mock_modules']}")
                    
                elif component == 'performance':
                    if 'current_metrics' in status and status['current_metrics']:
                        metrics = status['current_metrics']
                        print(f"  CPU: {metrics.get('cpu_percent', 'N/A')}%")
                        print(f"  内存: {metrics.get('memory_percent', 'N/A')}%")
                    
            else:
                print(f"  状态: ❌ {status['status']}")
                if 'error' in status:
                    print(f"  错误: {status['error']}")
        
        print("\n" + "="*60)
    
    async def run_comprehensive_check(self):
        """运行综合健康检查"""
        logger.info("🚀 开始综合系统健康检查...")
        
        # 初始化监控器
        if not await self.initialize_monitors():
            logger.error("❌ 监控器初始化失败，无法进行健康检查")
            return False
        
        # 运行各项检查
        checks = [
            self.check_mock_usage_health(),
            self.check_performance_health()
        ]
        
        # 等待所有检查完成
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # 统计检查结果
        successful_checks = sum(1 for result in results if result is True)
        total_checks = len(checks)
        
        logger.info(f"✅ 健康检查完成: {successful_checks}/{total_checks} 项检查成功")
        
        # 生成报告
        self.print_health_report()
        
        return successful_checks == total_checks

async def main():
    """主函数"""
    checker = ComprehensiveSystemHealthChecker()
    success = await checker.run_comprehensive_check()
    
    if success:
        logger.info("🎉 所有健康检查项目完成！")
        return 0
    else:
        logger.warning("⚠️ 部分健康检查项目失败，请检查系统状态")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
