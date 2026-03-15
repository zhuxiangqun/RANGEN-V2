#!/usr/bin/env python3
"""
增强版监控仪表板
集成运维监控系统和报警规则管理功能
提供实时监控、报警管理和系统健康检查
"""

import asyncio
import time
import json
import sys
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, '.')

try:
    from src.monitoring.operations_monitoring_system import OperationsMonitoringSystem, AlertRule, Alert
    OPS_MONITOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠  无法导入运维监控系统: {e}")
    OPS_MONITOR_AVAILABLE = False

try:
    from system_monitoring_dashboard import SystemMonitoringDashboard
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"⚠  无法导入基础仪表板: {e}")
    DASHBOARD_AVAILABLE = False


class EnhancedMonitoringDashboard:
    """增强版监控仪表板"""
    
    def __init__(self):
        """初始化增强版监控仪表板"""
        print("🚀 初始化增强版监控仪表板")
        
        # 基础仪表板
        if DASHBOARD_AVAILABLE:
            self.base_dashboard = SystemMonitoringDashboard()
        else:
            self.base_dashboard = None
            print("⚠  基础仪表板不可用，部分功能受限")
        
        # 运维监控系统
        if OPS_MONITOR_AVAILABLE:
            self.ops_monitor = OperationsMonitoringSystem()
            self._init_default_alert_rules()
        else:
            self.ops_monitor = None
            print("⚠  运维监控系统不可用，报警功能受限")
        
        # 增强功能状态
        self.running = False
        self.update_interval = 5  # 秒
        self.alert_history: List[Dict[str, Any]] = []
        self.max_alert_history = 100
        
        # 报警规则管理
        self.alert_rules: List[AlertRule] = []
        self._load_alert_rules()
    
    def _init_default_alert_rules(self):
        """初始化默认报警规则"""
        if not OPS_MONITOR_AVAILABLE:
            return
        
        try:
            # CPU使用率告警
            cpu_rule = AlertRule(
                rule_id="cpu_high_usage",
                name="CPU使用率过高",
                metric_name="cpu_percent",
                condition=">",
                threshold=80.0,  # 80%
                severity="warning",
                cooldown_minutes=5
            )
            
            # 内存使用率告警
            memory_rule = AlertRule(
                rule_id="memory_high_usage",
                name="内存使用率过高",
                metric_name="memory_percent",
                condition=">",
                threshold=85.0,  # 85%
                severity="warning",
                cooldown_minutes=5
            )
            
            # 磁盘使用率告警
            disk_rule = AlertRule(
                rule_id="disk_high_usage",
                name="磁盘使用率过高",
                metric_name="disk_percent",
                condition=">",
                threshold=90.0,  # 90%
                severity="error",
                cooldown_minutes=10
            )
            
            # 添加规则到运维监控系统
            self.ops_monitor.add_alert_rule(cpu_rule)
            self.ops_monitor.add_alert_rule(memory_rule)
            self.ops_monitor.add_alert_rule(disk_rule)
            
            print("✅ 默认报警规则已初始化")
            
        except Exception as e:
            print(f"❌ 初始化默认报警规则失败: {e}")
    
    def _load_alert_rules(self):
        """加载报警规则（从配置文件）"""
        # 暂时使用硬编码规则
        self.alert_rules = [
            {
                "id": "response_time_slow",
                "name": "响应时间过慢",
                "metric": "response_time",
                "condition": ">",
                "threshold": 2.0,  # 2秒
                "severity": "warning"
            },
            {
                "id": "success_rate_low",
                "name": "成功率过低",
                "metric": "success_rate",
                "condition": "<",
                "threshold": 95.0,  # 95%
                "severity": "error"
            },
            {
                "id": "error_rate_high",
                "name": "错误率过高",
                "metric": "error_rate",
                "condition": ">",
                "threshold": 5.0,  # 5%
                "severity": "warning"
            }
        ]
    
    def start_monitoring(self):
        """启动增强监控"""
        print("🚀 启动增强版监控仪表板")
        print("=" * 60)
        
        self.running = True
        
        # 启动基础仪表板（如果可用）
        if self.base_dashboard:
            threading.Thread(target=self.base_dashboard.start_monitoring, daemon=True).start()
        
        # 启动运维监控系统（如果可用）
        if self.ops_monitor:
            try:
                self.ops_monitor.start_monitoring()
                print("✅ 运维监控系统已启动")
            except Exception as e:
                print(f"❌ 启动运维监控系统失败: {e}")
        
        # 启动增强监控循环
        monitor_thread = threading.Thread(target=self._enhanced_monitoring_loop, daemon=True)
        monitor_thread.start()
        
        # 启动控制台界面
        self._enhanced_console_interface()
    
    def _enhanced_monitoring_loop(self):
        """增强监控循环"""
        while self.running:
            try:
                # 收集增强指标
                enhanced_metrics = self._collect_enhanced_metrics()
                
                # 检查报警规则
                if self.ops_monitor:
                    active_alerts = self.ops_monitor.get_active_alerts()
                    if active_alerts:
                        self._process_alerts(active_alerts)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"❌ 增强监控循环错误: {e}")
                time.sleep(1)
    
    def _collect_enhanced_metrics(self) -> Dict[str, Any]:
        """收集增强指标"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {},
            'performance_metrics': {},
            'security_metrics': {}
        }
        
        try:
            # 收集系统指标（CPU、内存、磁盘等）
            if self.ops_monitor:
                system_metrics = self.ops_monitor.collect_system_metrics()
                metrics['system_metrics'] = system_metrics
            
            # 收集性能指标
            if self.base_dashboard and hasattr(self.base_dashboard, 'metrics_history'):
                if self.base_dashboard.metrics_history:
                    latest = self.base_dashboard.metrics_history[-1]
                    metrics['performance_metrics'] = latest.get('performance', {})
            
            # 安全指标（如果安全检测服务可用）
            metrics['security_metrics'] = self._collect_security_metrics()
            
        except Exception as e:
            metrics['error'] = str(e)
        
        return metrics
    
    def _collect_security_metrics(self) -> Dict[str, Any]:
        """收集安全指标"""
        try:
            from src.di.bootstrap import bootstrap_application
            from src.di.unified_container import get_container
            
            # 启动应用获取安全检测服务
            app = bootstrap_application()
            container = get_container()
            
            # 尝试获取安全检测服务
            try:
                from src.services.advanced_security_detection_service import AdvancedSecurityDetectionService
                security_service = container.get_service(AdvancedSecurityDetectionService)
            except:
                try:
                    from src.services.security_detection_service import SecurityDetectionService
                    security_service = container.get_service(SecurityDetectionService)
                except:
                    return {"available": False, "message": "安全检测服务不可用"}
            
            # 获取安全统计信息
            stats = security_service.get_stats()
            recent_threats = security_service.get_recent_threats(10) if hasattr(security_service, 'get_recent_threats') else []
            
            return {
                "available": True,
                "events_processed": stats.get("events_processed", 0),
                "threats_detected": stats.get("threats_detected", 0),
                "false_positives": stats.get("false_positives", 0),
                "recent_threats_count": len(recent_threats),
                "rules_triggered": dict(stats.get("rules_triggered", {}))
            }
            
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _process_alerts(self, alerts: List[Alert]):
        """处理报警"""
        for alert in alerts:
            alert_record = {
                'id': alert.alert_id,
                'rule_id': alert.rule_id,
                'rule_name': alert.rule_name,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': datetime.now().isoformat(),
                'actual_value': alert.actual_value,
                'threshold': alert.threshold
            }
            
            # 添加到历史记录
            self.alert_history.append(alert_record)
            if len(self.alert_history) > self.max_alert_history:
                self.alert_history.pop(0)
            
            # 显示报警（根据严重性）
            if alert.severity == 'critical':
                print(f"🔴 CRITICAL ALERT: {alert.message}")
            elif alert.severity == 'error':
                print(f"🔴 ERROR ALERT: {alert.message}")
            elif alert.severity == 'warning':
                print(f"🟡 WARNING ALERT: {alert.message}")
            else:
                print(f"ℹ️  INFO ALERT: {alert.message}")
    
    def _enhanced_console_interface(self):
        """增强控制台界面"""
        try:
            while self.running:
                self._display_enhanced_dashboard()
                time.sleep(3)  # 每3秒刷新一次
        except KeyboardInterrupt:
            print("\n🛑 停止增强监控...")
            self.stop_monitoring()
    
    def _display_enhanced_dashboard(self):
        """显示增强版仪表板"""
        # 清屏
        print("\033[2J\033[H", end="")
        
        print("🚀 RANGEN增强版监控仪表板")
        print("=" * 60)
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 版本: 增强版 (报警规则管理)")
        print()
        
        # 显示系统状态摘要
        self._display_system_summary()
        print()
        
        # 显示报警规则状态
        self._display_alert_rules_status()
        print()
        
        # 显示活动报警
        self._display_active_alerts()
        print()
        
        # 显示安全状态
        self._display_security_status()
        print()
        
        # 显示控制选项
        self._display_enhanced_controls()
    
    def _display_system_summary(self):
        """显示系统状态摘要"""
        print("📊 系统状态摘要")
        print("-" * 30)
        
        if not OPS_MONITOR_AVAILABLE or not self.ops_monitor:
            print("ℹ️  运维监控系统不可用")
            return
        
        try:
            # 获取系统指标
            system_metrics = self.ops_monitor.collect_system_metrics()
            
            # CPU使用率
            cpu_percent = system_metrics.get('cpu_percent', 0)
            cpu_status = "✅" if cpu_percent < 70 else "⚠️" if cpu_percent < 85 else "🔴"
            print(f"{cpu_status} CPU使用率: {cpu_percent:.1f}%")
            
            # 内存使用率
            memory_percent = system_metrics.get('memory_percent', 0)
            memory_status = "✅" if memory_percent < 75 else "⚠️" if memory_percent < 90 else "🔴"
            print(f"{memory_status} 内存使用率: {memory_percent:.1f}%")
            
            # 磁盘使用率
            disk_percent = system_metrics.get('disk_percent', 0)
            disk_status = "✅" if disk_percent < 80 else "⚠️" if disk_percent < 95 else "🔴"
            print(f"{disk_status} 磁盘使用率: {disk_percent:.1f}%")
            
            # 系统运行时间
            if 'system_uptime' in system_metrics:
                uptime_seconds = system_metrics['system_uptime']
                uptime_str = str(timedelta(seconds=int(uptime_seconds)))
                print(f"⏱️  系统运行时间: {uptime_str}")
                
        except Exception as e:
            print(f"❌ 获取系统状态失败: {e}")
    
    def _display_alert_rules_status(self):
        """显示报警规则状态"""
        print("🔔 报警规则状态")
        print("-" * 30)
        
        if not OPS_MONITOR_AVAILABLE or not self.ops_monitor:
            print("ℹ️  运维监控系统不可用")
            return
        
        try:
            rules = self.ops_monitor.get_alert_rules()
            active_alerts = self.ops_monitor.get_active_alerts()
            
            print(f"📋 规则总数: {len(rules)}")
            print(f"🔴 活动报警: {len(active_alerts)}")
            
            # 显示启用的规则
            enabled_rules = [r for r in rules if r.enabled]
            print(f"✅ 启用规则: {len(enabled_rules)}")
            
            if enabled_rules:
                for rule in enabled_rules[:3]:  # 显示前3条规则
                    status = "正常"
                    for alert in active_alerts:
                        if alert.rule_id == rule.rule_id:
                            status = "触发"
                            break
                    
                    status_icon = "🔴" if status == "触发" else "✅"
                    print(f"  {status_icon} {rule.name}: {rule.metric_name} {rule.condition} {rule.threshold}")
            
        except Exception as e:
            print(f"❌ 获取报警规则状态失败: {e}")
    
    def _display_active_alerts(self):
        """显示活动报警"""
        print("🚨 活动报警")
        print("-" * 30)
        
        if not OPS_MONITOR_AVAILABLE or not self.ops_monitor:
            print("ℹ️  运维监控系统不可用")
            return
        
        try:
            active_alerts = self.ops_monitor.get_active_alerts()
            
            if not active_alerts:
                print("✅ 无活动报警")
                return
            
            # 按严重性排序：critical > error > warning > info
            severity_order = {'critical': 0, 'error': 1, 'warning': 2, 'info': 3}
            sorted_alerts = sorted(active_alerts, key=lambda x: severity_order.get(x.severity, 4))
            
            for alert in sorted_alerts[:5]:  # 显示前5个报警
                severity_icon = "🔴" if alert.severity == 'critical' else \
                              "🔴" if alert.severity == 'error' else \
                              "🟡" if alert.severity == 'warning' else "ℹ️"
                print(f"{severity_icon} [{alert.severity.upper()}] {alert.rule_name}")
                print(f"   {alert.message}")
                print(f"   当前值: {alert.actual_value:.2f}, 阈值: {alert.threshold}")
                print()
            
            if len(active_alerts) > 5:
                print(f"... 还有 {len(active_alerts) - 5} 个报警未显示")
                
        except Exception as e:
            print(f"❌ 获取活动报警失败: {e}")
    
    def _display_security_status(self):
        """显示安全状态"""
        print("🔒 安全状态")
        print("-" * 30)
        
        try:
            security_metrics = self._collect_security_metrics()
            
            if not security_metrics.get("available", False):
                print("ℹ️  安全检测服务不可用")
                return
            
            events_processed = security_metrics.get("events_processed", 0)
            threats_detected = security_metrics.get("threats_detected", 0)
            false_positives = security_metrics.get("false_positives", 0)
            recent_threats = security_metrics.get("recent_threats_count", 0)
            
            # 计算检测率
            detection_rate = (threats_detected / max(events_processed, 1)) * 100
            
            print(f"📊 处理事件: {events_processed}")
            print(f"🚨 检测威胁: {threats_detected}")
            print(f"📈 检测率: {detection_rate:.2f}%")
            print(f"⚠️  误报数: {false_positives}")
            print(f"🔍 最近威胁: {recent_threats}")
            
            # 规则触发统计
            rules_triggered = security_metrics.get("rules_triggered", {})
            if rules_triggered:
                print("🔔 规则触发统计:")
                for rule_id, count in list(rules_triggered.items())[:3]:
                    print(f"  {rule_id}: {count}次")
            
        except Exception as e:
            print(f"❌ 获取安全状态失败: {e}")
    
    def _display_enhanced_controls(self):
        """显示增强控制选项"""
        print("🎮 增强控制选项")
        print("-" * 30)
        print("按 Ctrl+C 停止监控")
        print("按 'r' 重新加载报警规则")
        print("按 'a' 添加报警规则")
        print("按 'l' 查看报警历史")
        print("按 's' 运行安全扫描")
        print("按 'e' 导出增强报告")
    
    def stop_monitoring(self):
        """停止增强监控"""
        self.running = False
        
        # 停止基础仪表板
        if self.base_dashboard and hasattr(self.base_dashboard, 'stop_monitoring'):
            self.base_dashboard.stop_monitoring()
        
        # 停止运维监控系统
        if self.ops_monitor and hasattr(self.ops_monitor, 'stop_monitoring'):
            self.ops_monitor.stop_monitoring()
        
        print("🛑 增强监控已停止")
    
    def run_security_scan(self):
        """运行安全扫描"""
        print("\n🔍 运行安全扫描...")
        
        try:
            from src.di.bootstrap import bootstrap_application
            from src.di.unified_container import get_container
            
            app = bootstrap_application()
            container = get_container()
            
            # 获取安全检测服务
            try:
                from src.services.advanced_security_detection_service import AdvancedSecurityDetectionService
                security_service = container.get_service(AdvancedSecurityDetectionService)
            except:
                try:
                    from src.services.security_detection_service import SecurityDetectionService
                    security_service = container.get_service(SecurityDetectionService)
                except:
                    print("❌ 安全检测服务不可用")
                    return
            
            # 获取最近威胁
            recent_threats = security_service.get_recent_threats(20) if hasattr(security_service, 'get_recent_threats') else []
            
            print(f"📊 安全扫描完成")
            print(f"🔍 分析威胁: {len(recent_threats)} 个")
            
            if recent_threats:
                print("🚨 最近检测到的威胁:")
                for threat in recent_threats[:5]:
                    if hasattr(threat, 'threat_type'):
                        print(f"  • {threat.threat_type}: {getattr(threat, 'description', 'No description')}")
                    elif isinstance(threat, dict):
                        print(f"  • {threat.get('threat_type', 'Unknown')}: {threat.get('description', 'No description')}")
            
            stats = security_service.get_stats()
            print(f"📈 统计信息: {stats}")
            
        except Exception as e:
            print(f"❌ 安全扫描失败: {e}")
    
    def export_enhanced_report(self):
        """导出增强报告"""
        print("\n📊 导出增强监控报告...")
        
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'report_type': 'enhanced_monitoring',
                'system_status': self._collect_enhanced_metrics(),
                'alert_history': self.alert_history[-20:],  # 最近20个报警
                'alert_rules': self.alert_rules,
                'security_status': self._collect_security_metrics()
            }
            
            filename = f"enhanced_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 增强报告已导出: {filename}")
            
        except Exception as e:
            print(f"❌ 导出增强报告失败: {e}")


def main():
    """主函数"""
    dashboard = EnhancedMonitoringDashboard()
    
    try:
        dashboard.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 用户中断增强监控")
    finally:
        dashboard.stop_monitoring()


if __name__ == "__main__":
    main()