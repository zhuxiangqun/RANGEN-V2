#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN系统监控仪表板
实时监控系统状态、性能和健康指标
"""

import asyncio
import time
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import threading
import queue

# 添加src到路径
sys.path.insert(0, 'src')

from utils.enhanced_system_integration import get_enhanced_system_integration
from utils.system_monitor_optimizer import get_system_monitor
from utils.system_health_checker import run_system_health_check

class SystemMonitoringDashboard:
    """系统监控仪表板"""
    
    def __init__(self):
        self.integration = get_enhanced_system_integration()
        self.monitor = get_system_monitor()
        self.running = False
        self.metrics_history = []
        self.max_history = 1000
        self.update_interval = 5  # 秒
        
    def start_monitoring(self):
        """启动监控"""
        print("🚀 启动RANGEN系统监控仪表板")
        print("=" * 60)
        
        self.running = True
        self.monitor.start_monitoring()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 启动控制台界面
        self._console_interface()
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 收集系统指标
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 保持历史记录在限制内
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                time.sleep(1)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # 获取系统状态
            system_status = self.integration.get_system_status()
            
            # 获取性能指标
            performance_metrics = self.monitor.get_performance_metrics()
            
            # 获取系统能力
            capabilities = self.integration.get_system_capabilities()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'performance': performance_metrics,
                'capabilities': capabilities,
                'uptime': time.time()
            }
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'uptime': time.time()
            }
    
    def _console_interface(self):
        """控制台界面"""
        try:
            while self.running:
                self._display_dashboard()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n🛑 停止监控...")
            self.stop_monitoring()
    
    def _display_dashboard(self):
        """显示仪表板"""
        # 清屏
        print("\033[2J\033[H", end="")
        
        print("🚀 RANGEN系统监控仪表板")
        print("=" * 60)
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if not self.metrics_history:
            print("⏳ 正在收集系统指标...")
            return
        
        # 获取最新指标
        latest_metrics = self.metrics_history[-1]
        
        # 显示系统状态
        self._display_system_status(latest_metrics)
        print()
        
        # 显示性能指标
        self._display_performance_metrics(latest_metrics)
        print()
        
        # 显示系统能力
        self._display_capabilities(latest_metrics)
        print()
        
        # 显示历史趋势
        self._display_trends()
        print()
        
        # 显示控制选项
        self._display_controls()
    
    def _display_system_status(self, metrics: Dict[str, Any]):
        """显示系统状态"""
        print("📊 系统状态")
        print("-" * 30)
        
        if 'error' in metrics:
            print(f"❌ 错误: {metrics['error']}")
            return
        
        system_status = metrics.get('system_status', {})
        
        # 系统健康状态
        health_status = system_status.get('health_status', 'unknown')
        health_icon = "✅" if health_status == "healthy" else "⚠️" if health_status == "warning" else "❌"
        print(f"{health_icon} 健康状态: {health_status.upper()}")
        
        # 系统组件状态
        components = system_status.get('components', {})
        for component, status in components.items():
            status_icon = "✅" if status == "active" else "❌"
            print(f"  {status_icon} {component}: {status}")
        
        # 系统负载
        load = system_status.get('load', {})
        if load:
            print(f"📈 系统负载: {load.get('cpu', 'N/A')}% CPU, {load.get('memory', 'N/A')}% 内存")
    
    def _display_performance_metrics(self, metrics: Dict[str, Any]):
        """显示性能指标"""
        print("⚡ 性能指标")
        print("-" * 30)
        
        if 'error' in metrics:
            print("❌ 无法获取性能指标")
            return
        
        performance = metrics.get('performance', {})
        
        # 查询统计
        query_stats = performance.get('query_stats', {})
        if query_stats:
            total_queries = query_stats.get('total_queries', 0)
            successful_queries = query_stats.get('successful_queries', 0)
            success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
            
            print(f"📝 查询统计:")
            print(f"  总查询数: {total_queries}")
            print(f"  成功查询: {successful_queries}")
            print(f"  成功率: {success_rate:.1f}%")
        
        # 响应时间
        response_times = performance.get('response_times', {})
        if response_times:
            avg_time = response_times.get('average', 0)
            min_time = response_times.get('min', 0)
            max_time = response_times.get('max', 0)
            
            print(f"⏱️ 响应时间:")
            print(f"  平均: {avg_time:.3f}s")
            print(f"  最快: {min_time:.3f}s")
            print(f"  最慢: {max_time:.3f}s")
        
        # 吞吐量
        throughput = performance.get('throughput', 0)
        if throughput > 0:
            print(f"🚀 吞吐量: {throughput:.1f} 查询/秒")
    
    def _display_capabilities(self, metrics: Dict[str, Any]):
        """显示系统能力"""
        print("🔧 系统能力")
        print("-" * 30)
        
        if 'error' in metrics:
            print("❌ 无法获取系统能力")
            return
        
        capabilities = metrics.get('capabilities', {})
        
        # 核心功能
        core_features = capabilities.get('core_features', [])
        if core_features:
            print("🎯 核心功能:")
            for feature in core_features:
                print(f"  ✅ {feature}")
        
        # 增强功能
        enhanced_features = capabilities.get('enhanced_features', [])
        if enhanced_features:
            print("🚀 增强功能:")
            for feature in enhanced_features:
                print(f"  ✅ {feature}")
        
        # 集成状态
        integrations = capabilities.get('integrations', {})
        if integrations:
            print("🔗 集成状态:")
            for integration, status in integrations.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {integration}")
    
    def _display_trends(self):
        """显示历史趋势"""
        print("📈 历史趋势")
        print("-" * 30)
        
        if len(self.metrics_history) < 2:
            print("⏳ 数据不足，无法显示趋势")
            return
        
        # 计算趋势
        recent_metrics = self.metrics_history[-5:]  # 最近5个数据点
        
        # 成功率趋势
        success_rates = []
        for metrics in recent_metrics:
            if 'error' not in metrics:
                performance = metrics.get('performance', {})
                query_stats = performance.get('query_stats', {})
                total = query_stats.get('total_queries', 0)
                successful = query_stats.get('successful_queries', 0)
                if total > 0:
                    success_rates.append(successful / total * 100)
        
        if success_rates:
            avg_success_rate = sum(success_rates) / len(success_rates)
            trend_icon = "📈" if len(success_rates) > 1 and success_rates[-1] > success_rates[0] else "📉"
            print(f"{trend_icon} 平均成功率: {avg_success_rate:.1f}%")
        
        # 响应时间趋势
        response_times = []
        for metrics in recent_metrics:
            if 'error' not in metrics:
                performance = metrics.get('performance', {})
                response_times_data = performance.get('response_times', {})
                avg_time = response_times_data.get('average', 0)
                if avg_time > 0:
                    response_times.append(avg_time)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            trend_icon = "📈" if len(response_times) > 1 and response_times[-1] > response_times[0] else "📉"
            print(f"{trend_icon} 平均响应时间: {avg_response_time:.3f}s")
    
    def _display_controls(self):
        """显示控制选项"""
        print("🎮 控制选项")
        print("-" * 30)
        print("按 Ctrl+C 停止监控")
        print("按 Enter 刷新数据")
        print("按 'h' 显示帮助")
        print("按 'r' 运行健康检查")
        print("按 't' 运行测试")
        print("按 'e' 导出报告")
    
    def run_health_check(self):
        """运行健康检查"""
        print("\n🏥 运行系统健康检查...")
        try:
            health_report = asyncio.run(run_system_health_check())
            print(f"健康状态: {health_report.overall_status.value.upper()}")
            print(f"健康检查项: {health_report.healthy_checks}/{health_report.total_checks}")
            
            if health_report.issues:
                print("发现的问题:")
                for issue in health_report.issues:
                    print(f"  ❌ {issue}")
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
    
    def run_tests(self):
        """运行系统测试"""
        print("\n🧪 运行系统测试...")
        try:
            test_results = asyncio.run(self.integration.run_comprehensive_tests())
            print(f"测试结果: {test_results.get('overall_status', 'unknown')}")
            print(f"通过测试: {test_results.get('passed_tests', 0)}/{test_results.get('total_tests', 0)}")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    def export_report(self):
        """导出监控报告"""
        print("\n📊 导出监控报告...")
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_duration': len(self.metrics_history) * self.update_interval,
                'metrics_count': len(self.metrics_history),
                'latest_metrics': self.metrics_history[-1] if self.metrics_history else None,
                'trend_analysis': self._analyze_trends()
            }
            
            filename = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 报告已导出: {filename}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        if len(self.metrics_history) < 2:
            return {}
        
        # 分析成功率趋势
        success_rates = []
        response_times = []
        
        for metrics in self.metrics_history:
            if 'error' not in metrics:
                # 成功率
                performance = metrics.get('performance', {})
                query_stats = performance.get('query_stats', {})
                total = query_stats.get('total_queries', 0)
                successful = query_stats.get('successful_queries', 0)
                if total > 0:
                    success_rates.append(successful / total * 100)
                
                # 响应时间
                response_times_data = performance.get('response_times', {})
                avg_time = response_times_data.get('average', 0)
                if avg_time > 0:
                    response_times.append(avg_time)
        
        return {
            'success_rate_trend': self._calculate_trend(success_rates),
            'response_time_trend': self._calculate_trend(response_times),
            'avg_success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.05:
            return "increasing"
        elif second_avg < first_avg * 0.95:
            return "decreasing"
        else:
            return "stable"
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self.monitor.stop_monitoring()
        print("🛑 监控已停止")

def main():
    """主函数"""
    dashboard = SystemMonitoringDashboard()
    
    try:
        dashboard.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 用户中断监控")
    finally:
        dashboard.stop_monitoring()

if __name__ == "__main__":
    main()
