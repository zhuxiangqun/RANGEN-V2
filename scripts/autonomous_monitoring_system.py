#!/usr/bin/env python3
"""
自主智能监控系统
实现长期监控和自动优化机制
"""

import sys
import os
import time
import json
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AutonomousMonitoringSystem:
    """自主智能监控系统"""

    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.optimization_thread = None

        # 监控配置
        self.monitoring_config = {
            'check_interval': 300,  # 5分钟检查一次
            'optimization_interval': 3600,  # 1小时优化一次
            'performance_window': 3600,  # 1小时性能窗口
            'alert_thresholds': {
                'response_time': 5.0,  # 秒
                'error_rate': 0.1,     # 10%
                'success_rate': 0.8    # 80%
            },
            'auto_adjustment': {
                'enabled': True,
                'max_adjustment': 0.05,  # 每次最多调整5%
                'min_interval': 1800     # 最少30分钟调整间隔
            }
        }

        # 监控数据存储
        self.monitoring_data = {
            'start_time': None,
            'last_check': None,
            'last_optimization': None,
            'performance_history': [],
            'alerts': [],
            'adjustments': []
        }

        # Agent监控状态
        self.agent_status = {}

        print("🎛️ 自主智能监控系统已初始化")

    def start_monitoring(self):
        """启动监控系统"""
        if self.monitoring_active:
            print("⚠️ 监控系统已在运行中")
            return

        print("🚀 启动自主智能监控系统...")
        self.monitoring_active = True
        self.monitoring_data['start_time'] = datetime.now()

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        # 启动优化线程
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()

        print("✅ 监控系统已启动")
        print(f"   📊 检查间隔: {self.monitoring_config['check_interval']}秒")
        print(f"   🔧 优化间隔: {self.monitoring_config['optimization_interval']}秒")

    def stop_monitoring(self):
        """停止监控系统"""
        if not self.monitoring_active:
            print("⚠️ 监控系统未运行")
            return

        print("🛑 停止自主智能监控系统...")
        self.monitoring_active = False

        # 等待线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5)

        # 保存最终报告
        self._save_monitoring_report()

        print("✅ 监控系统已停止")

    def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring_active:
            try:
                self._perform_monitoring_check()
                time.sleep(self.monitoring_config['check_interval'])
            except Exception as e:
                print(f"❌ 监控循环异常: {e}")
                time.sleep(60)  # 异常时等待1分钟后重试

    def _optimization_loop(self):
        """优化主循环"""
        while self.monitoring_active:
            try:
                time.sleep(self.monitoring_config['optimization_interval'])
                if self.monitoring_active:  # 双重检查
                    self._perform_optimization()
            except Exception as e:
                print(f"❌ 优化循环异常: {e}")
                time.sleep(300)  # 异常时等待5分钟后重试

    def _perform_monitoring_check(self):
        """执行监控检查"""
        check_time = datetime.now()
        print(f"\n📊 执行监控检查 - {check_time.strftime('%H:%M:%S')}")

        # 收集性能数据
        performance_data = self._collect_performance_data()

        # 分析性能指标
        analysis = self._analyze_performance(performance_data)

        # 检查告警条件
        alerts = self._check_alerts(performance_data)

        # 记录监控数据
        check_record = {
            'timestamp': check_time.isoformat(),
            'performance': performance_data,
            'analysis': analysis,
            'alerts': alerts
        }

        self.monitoring_data['performance_history'].append(check_record)
        self.monitoring_data['last_check'] = check_time

        # 显示检查结果
        self._display_check_results(performance_data, analysis, alerts)

        # 清理旧数据
        self._cleanup_old_data()

    def _collect_performance_data(self) -> Dict[str, Any]:
        """收集性能数据"""
        try:
            # 这里应该集成实际的性能监控数据收集
            # 目前使用模拟数据
            return {
                'response_time': 0.8,  # 秒
                'success_rate': 0.92,  # 92%
                'error_rate': 0.08,    # 8%
                'throughput': 45,      # 请求/分钟
                'agent_status': {
                    'RAGExpert': {'active': True, 'replacement_rate': 0.25},
                    'ReasoningExpert': {'active': True, 'replacement_rate': 0.25},
                    'AgentCoordinator': {'active': True, 'replacement_rate': 1.0}
                }
            }
        except Exception as e:
            print(f"❌ 收集性能数据失败: {e}")
            return {}

    def _analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能数据"""
        analysis = {
            'overall_health': 'unknown',
            'trends': {},
            'recommendations': []
        }

        if not performance_data:
            return analysis

        # 整体健康度评估
        success_rate = performance_data.get('success_rate', 0)
        error_rate = performance_data.get('error_rate', 0)
        response_time = performance_data.get('response_time', 0)

        if success_rate >= 0.9 and error_rate <= 0.05 and response_time <= 2.0:
            analysis['overall_health'] = 'excellent'
        elif success_rate >= 0.8 and error_rate <= 0.1 and response_time <= 5.0:
            analysis['overall_health'] = 'good'
        elif success_rate >= 0.7 and error_rate <= 0.15:
            analysis['overall_health'] = 'fair'
        else:
            analysis['overall_health'] = 'poor'

        # 趋势分析
        if len(self.monitoring_data['performance_history']) >= 3:
            recent_data = self.monitoring_data['performance_history'][-3:]
            analysis['trends'] = self._calculate_trends(recent_data)

        # 生成建议
        analysis['recommendations'] = self._generate_recommendations(performance_data, analysis)

        return analysis

    def _check_alerts(self, performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查告警条件"""
        alerts = []

        thresholds = self.monitoring_config['alert_thresholds']

        # 响应时间告警
        if performance_data.get('response_time', 0) > thresholds['response_time']:
            alerts.append({
                'type': 'response_time',
                'level': 'warning',
                'message': f'响应时间过高: {performance_data["response_time"]:.2f}秒 > {thresholds["response_time"]}秒',
                'timestamp': datetime.now().isoformat()
            })

        # 错误率告警
        if performance_data.get('error_rate', 0) > thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'level': 'error',
                'message': f'错误率过高: {performance_data["error_rate"]:.1%} > {thresholds["error_rate"]:.1%}',
                'timestamp': datetime.now().isoformat()
            })

        # 成功率告警
        if performance_data.get('success_rate', 0) < thresholds['success_rate']:
            alerts.append({
                'type': 'success_rate',
                'level': 'warning',
                'message': f'成功率过低: {performance_data["success_rate"]:.1%} < {thresholds["success_rate"]:.1%}',
                'timestamp': datetime.now().isoformat()
            })

        # 记录告警
        self.monitoring_data['alerts'].extend(alerts)

        return alerts

    def _perform_optimization(self):
        """执行自动优化"""
        if not self.monitoring_config['auto_adjustment']['enabled']:
            return

        opt_time = datetime.now()
        print(f"\n🔧 执行自动优化 - {opt_time.strftime('%H:%M:%S')}")

        try:
            # 分析历史数据
            optimization_decisions = self._analyze_optimization_opportunities()

            # 执行优化调整
            adjustments = self._execute_optimizations(optimization_decisions)

            # 记录优化结果
            opt_record = {
                'timestamp': opt_time.isoformat(),
                'decisions': optimization_decisions,
                'adjustments': adjustments
            }

            self.monitoring_data['adjustments'].append(opt_record)
            self.monitoring_data['last_optimization'] = opt_time

            # 显示优化结果
            self._display_optimization_results(adjustments)

        except Exception as e:
            print(f"❌ 自动优化失败: {e}")

    def _analyze_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """分析优化机会"""
        opportunities = []

        # 检查最近的性能数据
        if len(self.monitoring_data['performance_history']) < 5:
            return opportunities

        recent_performance = self.monitoring_data['performance_history'][-5:]

        # 分析替换率调整机会
        for agent_name in ['RAGExpert', 'ReasoningExpert', 'AgentCoordinator']:
            agent_opportunities = self._analyze_agent_optimization(agent_name, recent_performance)
            opportunities.extend(agent_opportunities)

        return opportunities

    def _analyze_agent_optimization(self, agent_name: str, recent_performance: List[Dict]) -> List[Dict[str, Any]]:
        """分析单个Agent的优化机会"""
        opportunities = []

        # 获取Agent的当前状态
        current_status = None
        for record in reversed(recent_performance):
            if agent_name in record.get('performance', {}).get('agent_status', {}):
                current_status = record['performance']['agent_status'][agent_name]
                break

        if not current_status:
            return opportunities

        current_rate = current_status.get('replacement_rate', 0)

        # 基于性能趋势决定调整方向
        performance_trend = self._calculate_performance_trend(agent_name, recent_performance)

        if performance_trend == 'improving' and current_rate < 0.5:
            # 性能改善，可以增加替换率
            opportunities.append({
                'type': 'increase_replacement_rate',
                'agent': agent_name,
                'current_rate': current_rate,
                'suggested_rate': min(current_rate + 0.05, 0.5),
                'reason': '性能呈改善趋势，建议增加替换率',
                'confidence': 0.8
            })
        elif performance_trend == 'degrading' and current_rate > 0.05:
            # 性能下降，建议减少替换率
            opportunities.append({
                'type': 'decrease_replacement_rate',
                'agent': agent_name,
                'current_rate': current_rate,
                'suggested_rate': max(current_rate - 0.05, 0.05),
                'reason': '性能呈下降趋势，建议减少替换率',
                'confidence': 0.7
            })

        return opportunities

    def _execute_optimizations(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行优化决策"""
        adjustments = []

        for decision in decisions:
            if decision['confidence'] < 0.6:
                continue  # 置信度太低，跳过

            try:
                adjustment = self._apply_optimization(decision)
                if adjustment:
                    adjustments.append(adjustment)
            except Exception as e:
                print(f"❌ 执行优化失败 {decision['agent']}: {e}")

        return adjustments

    def _apply_optimization(self, decision: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """应用单个优化决策"""
        # 这里应该实际修改配置文件或调用API
        # 目前只记录决策

        return {
            'agent': decision['agent'],
            'type': decision['type'],
            'old_rate': decision['current_rate'],
            'new_rate': decision['suggested_rate'],
            'reason': decision['reason'],
            'timestamp': datetime.now().isoformat(),
            'status': 'simulated'  # 实际应用时改为 'applied'
        }

    def _calculate_trends(self, recent_data: List[Dict]) -> Dict[str, Any]:
        """计算性能趋势"""
        # 简化的趋势计算
        return {
            'response_time_trend': 'stable',
            'success_rate_trend': 'improving',
            'error_rate_trend': 'decreasing'
        }

    def _calculate_performance_trend(self, agent_name: str, recent_data: List[Dict]) -> str:
        """计算单个Agent的性能趋势"""
        # 简化的趋势判断
        return 'improving'

    def _generate_recommendations(self, performance_data: Dict, analysis: Dict) -> List[str]:
        """生成建议"""
        recommendations = []

        if analysis['overall_health'] == 'excellent':
            recommendations.append("系统运行状态优秀，继续保持当前配置")
        elif analysis['overall_health'] == 'good':
            recommendations.append("系统运行状态良好，可以考虑小幅优化")
        else:
            recommendations.append("系统运行状态需要关注，建议检查配置和资源")

        return recommendations

    def _display_check_results(self, performance_data: Dict, analysis: Dict, alerts: List):
        """显示检查结果"""
        health_emoji = {
            'excellent': '🟢',
            'good': '🟡',
            'fair': '🟠',
            'poor': '🔴',
            'unknown': '⚪'
        }

        health = analysis.get('overall_health', 'unknown')
        print(f"   整体健康度: {health_emoji.get(health, '⚪')} {health}")

        if performance_data:
            rt = performance_data.get('response_time', 0)
            sr = performance_data.get('success_rate', 0)
            er = performance_data.get('error_rate', 0)
            tp = performance_data.get('throughput', 0)

            print(f"   📈 响应时间: {rt:.2f}秒")
            print(f"   ✅ 成功率: {sr:.1%}")
            print(f"   ❌ 错误率: {er:.1%}")
            print(f"   🚀 吞吐量: {tp}/分钟")

        if alerts:
            print(f"   🚨 告警数量: {len(alerts)}")
            for alert in alerts[:2]:  # 只显示前2个告警
                print(f"      • {alert['message']}")

        if analysis.get('recommendations'):
            print(f"   💡 建议: {analysis['recommendations'][0]}")

    def _display_optimization_results(self, adjustments: List[Dict]):
        """显示优化结果"""
        if not adjustments:
            print("   ℹ️ 无优化调整")
            return

        print(f"   🔧 执行了 {len(adjustments)} 个优化调整:")
        for adj in adjustments:
            print(f"      • {adj['agent']}: {adj['old_rate']:.1%} → {adj['new_rate']:.1%} ({adj['reason']})")

    def _cleanup_old_data(self):
        """清理旧的监控数据"""
        # 保留最近24小时的数据
        cutoff_time = datetime.now() - timedelta(hours=24)

        self.monitoring_data['performance_history'] = [
            record for record in self.monitoring_data['performance_history']
            if datetime.fromisoformat(record['timestamp']) > cutoff_time
        ]

        # 保留最近100个告警
        if len(self.monitoring_data['alerts']) > 100:
            self.monitoring_data['alerts'] = self.monitoring_data['alerts'][-100:]

    def _save_monitoring_report(self):
        """保存监控报告"""
        try:
            report_file = f"autonomous_monitoring_report_{int(time.time())}.json"

            # 计算统计信息
            stats = self._calculate_monitoring_stats()

            report = {
                'monitoring_period': {
                    'start': self.monitoring_data['start_time'].isoformat() if self.monitoring_data['start_time'] else None,
                    'end': datetime.now().isoformat(),
                    'duration_hours': (datetime.now() - self.monitoring_data['start_time']).total_seconds() / 3600 if self.monitoring_data['start_time'] else 0
                },
                'statistics': stats,
                'final_status': self.monitoring_data,
                'recommendations': [
                    "根据监控数据调整系统配置",
                    "定期审查告警阈值设置",
                    "优化自动调整参数",
                    "扩展监控指标覆盖范围"
                ]
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            print(f"📄 监控报告已保存: {report_file}")

        except Exception as e:
            print(f"❌ 保存监控报告失败: {e}")

    def _calculate_monitoring_stats(self) -> Dict[str, Any]:
        """计算监控统计信息"""
        stats = {
            'total_checks': len(self.monitoring_data['performance_history']),
            'total_alerts': len(self.monitoring_data['alerts']),
            'total_optimizations': len(self.monitoring_data['adjustments']),
            'average_performance': {},
            'alert_summary': {}
        }

        if self.monitoring_data['performance_history']:
            # 计算平均性能指标
            response_times = []
            success_rates = []
            error_rates = []

            for record in self.monitoring_data['performance_history']:
                perf = record.get('performance', {})
                if 'response_time' in perf:
                    response_times.append(perf['response_time'])
                if 'success_rate' in perf:
                    success_rates.append(perf['success_rate'])
                if 'error_rate' in perf:
                    error_rates.append(perf['error_rate'])

            if response_times:
                stats['average_performance']['response_time'] = sum(response_times) / len(response_times)
            if success_rates:
                stats['average_performance']['success_rate'] = sum(success_rates) / len(success_rates)
            if error_rates:
                stats['average_performance']['error_rate'] = sum(error_rates) / len(error_rates)

        # 告警统计
        alert_types = {}
        for alert in self.monitoring_data['alerts']:
            alert_type = alert.get('type', 'unknown')
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        stats['alert_summary'] = alert_types

        return stats

    def get_status(self) -> Dict[str, Any]:
        """获取监控系统状态"""
        return {
            'active': self.monitoring_active,
            'start_time': self.monitoring_data['start_time'].isoformat() if self.monitoring_data['start_time'] else None,
            'last_check': self.monitoring_data['last_check'].isoformat() if self.monitoring_data['last_check'] else None,
            'last_optimization': self.monitoring_data['last_optimization'].isoformat() if self.monitoring_data['last_optimization'] else None,
            'total_checks': len(self.monitoring_data['performance_history']),
            'total_alerts': len(self.monitoring_data['alerts']),
            'total_optimizations': len(self.monitoring_data['adjustments'])
        }

def main():
    """主函数"""
    print("🎛️ 自主智能监控系统")
    print("=" * 50)

    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'start':
            # 启动监控系统
            monitor = AutonomousMonitoringSystem()
            monitor.start_monitoring()

            try:
                # 保持运行
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 接收到停止信号...")
                monitor.stop_monitoring()

        elif command == 'status':
            # 显示状态（需要现有实例，这里简化处理）
            print("⚠️ 状态检查需要运行中的监控实例")
            print("请先启动监控系统: python autonomous_monitoring_system.py start")

        else:
            print(f"❌ 未知命令: {command}")
            print("可用命令: start, status")

    else:
        print("用法:")
        print("  python autonomous_monitoring_system.py start    # 启动监控系统")
        print("  python autonomous_monitoring_system.py status   # 查看状态")
        print("\n示例:")
        print("  python autonomous_monitoring_system.py start")

if __name__ == "__main__":
    main()
