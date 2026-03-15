#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN系统优化建议生成器
基于系统监控数据生成智能优化建议
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import statistics

# 添加src到路径
sys.path.insert(0, 'src')

from utils.enhanced_system_integration import get_enhanced_system_integration
from utils.system_monitor_optimizer import get_system_monitor
from utils.system_health_checker import run_system_health_check, HealthStatus

class OptimizationAdvisor:
    """系统优化建议生成器"""
    
    def __init__(self):
        self.integration = get_enhanced_system_integration()
        self.monitor = get_system_monitor()
        self.optimization_rules = self._load_optimization_rules()
        
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """加载优化规则"""
        return {
            'performance': {
                'response_time_threshold': 1.0,  # 秒
                'success_rate_threshold': 95.0,  # 百分比
                'throughput_threshold': 100,     # 查询/秒
                'memory_usage_threshold': 80.0   # 百分比
            },
            'reliability': {
                'error_rate_threshold': 5.0,     # 百分比
                'uptime_threshold': 99.0,        # 百分比
                'health_check_threshold': 90.0   # 百分比
            },
            'scalability': {
                'concurrent_users_threshold': 100,
                'queue_size_threshold': 50,
                'resource_utilization_threshold': 70.0
            }
        }
    
    async def analyze_system_performance(self) -> Dict[str, Any]:
        """分析系统性能"""
        print("🔍 分析系统性能...")
        
        try:
            # 获取系统状态
            system_status = self.integration.get_system_status()
            
            # 获取性能指标
            performance_metrics = self.monitor.get_performance_metrics()
            
            # 运行健康检查
            health_report = await run_system_health_check()
            
            # 分析性能
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'performance_metrics': performance_metrics,
            'health_report': {
                'overall_status': health_report.overall_status.value,
                'healthy_checks': health_report.healthy_checks,
                'total_checks': health_report.total_checks,
                'issues': [result.message for result in health_report.check_results if result.status != HealthStatus.HEALTHY]
            },
                'analysis_results': {}
            }
            
            # 性能分析
            analysis['analysis_results']['performance'] = self._analyze_performance_metrics(performance_metrics)
            
            # 可靠性分析
            analysis['analysis_results']['reliability'] = self._analyze_reliability(system_status.__dict__, health_report)
            
            # 可扩展性分析
            analysis['analysis_results']['scalability'] = self._analyze_scalability(system_status.__dict__, performance_metrics)
            
            # 生成优化建议
            analysis['optimization_recommendations'] = self._generate_optimization_recommendations(analysis['analysis_results'])
            
            return analysis
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'analysis_results': {},
                'optimization_recommendations': []
            }
    
    def _analyze_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能指标"""
        analysis = {
            'status': 'good',
            'issues': [],
            'recommendations': []
        }
        
        # 分析响应时间
        response_times = metrics.get('response_times', {})
        avg_response_time = response_times.get('average', 0)
        
        if avg_response_time > self.optimization_rules['performance']['response_time_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"平均响应时间过长: {avg_response_time:.3f}s")
            analysis['recommendations'].append("考虑优化查询处理逻辑或增加缓存机制")
        
        # 分析成功率
        query_stats = metrics.get('query_stats', {})
        total_queries = query_stats.get('total_queries', 0)
        successful_queries = query_stats.get('successful_queries', 0)
        
        if total_queries > 0:
            success_rate = (successful_queries / total_queries) * 100
            if success_rate < self.optimization_rules['performance']['success_rate_threshold']:
                analysis['status'] = 'warning'
                analysis['issues'].append(f"成功率过低: {success_rate:.1f}%")
                analysis['recommendations'].append("检查错误处理逻辑和异常情况")
        
        # 分析吞吐量
        throughput = metrics.get('throughput', 0)
        if throughput < self.optimization_rules['performance']['throughput_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"吞吐量过低: {throughput:.1f} 查询/秒")
            analysis['recommendations'].append("考虑优化并发处理或增加系统资源")
        
        # 分析内存使用
        memory_usage = metrics.get('memory_usage', {})
        memory_percentage = memory_usage.get('percentage', 0)
        if memory_percentage > self.optimization_rules['performance']['memory_usage_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"内存使用率过高: {memory_percentage:.1f}%")
            analysis['recommendations'].append("考虑优化内存使用或增加内存资源")
        
        return analysis
    
    def _analyze_reliability(self, system_status: Dict[str, Any], health_report: Any) -> Dict[str, Any]:
        """分析可靠性"""
        analysis = {
            'status': 'good',
            'issues': [],
            'recommendations': []
        }
        
        # 分析健康检查结果
        health_percentage = (health_report.healthy_checks / health_report.total_checks) * 100
        if health_percentage < self.optimization_rules['reliability']['health_check_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"健康检查通过率过低: {health_percentage:.1f}%")
            analysis['recommendations'].append("修复健康检查中发现的问题")
        
        # 分析系统组件状态
        components = getattr(system_status, 'components', {})
        if isinstance(components, dict):
            failed_components = [comp for comp, status in components.items() if status != 'active']
            
            if failed_components:
                analysis['status'] = 'warning'
                analysis['issues'].append(f"组件状态异常: {', '.join(failed_components)}")
                analysis['recommendations'].append("检查并修复异常组件的配置")
        
        # 分析错误率
        error_rate = getattr(system_status, 'error_rate', 0)
        if error_rate > self.optimization_rules['reliability']['error_rate_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"错误率过高: {error_rate:.1f}%")
            analysis['recommendations'].append("加强错误处理和监控")
        
        return analysis
    
    def _analyze_scalability(self, system_status: Dict[str, Any], performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """分析可扩展性"""
        analysis = {
            'status': 'good',
            'issues': [],
            'recommendations': []
        }
        
        # 分析并发用户数
        concurrent_users = getattr(system_status, 'concurrent_users', 0)
        if concurrent_users > self.optimization_rules['scalability']['concurrent_users_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"并发用户数过高: {concurrent_users}")
            analysis['recommendations'].append("考虑增加服务器资源或优化并发处理")
        
        # 分析队列大小
        queue_size = getattr(system_status, 'queue_size', 0)
        if queue_size > self.optimization_rules['scalability']['queue_size_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"队列大小过大: {queue_size}")
            analysis['recommendations'].append("优化任务处理速度或增加处理能力")
        
        # 分析资源利用率
        resource_utilization = getattr(system_status, 'resource_utilization', {})
        if isinstance(resource_utilization, dict):
            cpu_usage = resource_utilization.get('cpu', 0)
            memory_usage = resource_utilization.get('memory', 0)
        else:
            cpu_usage = 0
            memory_usage = 0
        
        if cpu_usage > self.optimization_rules['scalability']['resource_utilization_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"CPU使用率过高: {cpu_usage:.1f}%")
            analysis['recommendations'].append("优化CPU密集型操作或增加CPU资源")
        
        if memory_usage > self.optimization_rules['scalability']['resource_utilization_threshold']:
            analysis['status'] = 'warning'
            analysis['issues'].append(f"内存使用率过高: {memory_usage:.1f}%")
            analysis['recommendations'].append("优化内存使用或增加内存资源")
        
        return analysis
    
    def _generate_optimization_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        # 性能优化建议
        performance_analysis = analysis_results.get('performance', {})
        if performance_analysis.get('status') == 'warning':
            recommendations.extend(self._generate_performance_recommendations(performance_analysis))
        
        # 可靠性优化建议
        reliability_analysis = analysis_results.get('reliability', {})
        if reliability_analysis.get('status') == 'warning':
            recommendations.extend(self._generate_reliability_recommendations(reliability_analysis))
        
        # 可扩展性优化建议
        scalability_analysis = analysis_results.get('scalability', {})
        if scalability_analysis.get('status') == 'warning':
            recommendations.extend(self._generate_scalability_recommendations(scalability_analysis))
        
        # 通用优化建议
        recommendations.extend(self._generate_general_recommendations(analysis_results))
        
        return recommendations
    
    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成性能优化建议"""
        recommendations = []
        
        for issue in analysis.get('issues', []):
            if '响应时间' in issue:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'high',
                    'title': '优化响应时间',
                    'description': '系统响应时间过长，影响用户体验',
                    'suggestions': [
                        '启用查询缓存机制',
                        '优化数据库查询语句',
                        '使用异步处理提高并发能力',
                        '考虑使用CDN加速静态资源'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'high'
                })
            
            elif '成功率' in issue:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'high',
                    'title': '提高查询成功率',
                    'description': '查询成功率过低，需要改进错误处理',
                    'suggestions': [
                        '加强输入验证和错误处理',
                        '实现重试机制',
                        '优化异常情况处理',
                        '增加监控和告警'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'high'
                })
            
            elif '吞吐量' in issue:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': '提高系统吞吐量',
                    'description': '系统吞吐量不足，需要优化并发处理',
                    'suggestions': [
                        '优化并发处理逻辑',
                        '增加服务器资源',
                        '使用负载均衡',
                        '实现任务队列优化'
                    ],
                    'implementation_difficulty': 'high',
                    'expected_impact': 'medium'
                })
            
            elif '内存' in issue:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': '优化内存使用',
                    'description': '内存使用率过高，需要优化内存管理',
                    'suggestions': [
                        '优化数据结构减少内存占用',
                        '实现内存池管理',
                        '增加内存资源',
                        '优化垃圾回收策略'
                    ],
                    'implementation_difficulty': 'high',
                    'expected_impact': 'medium'
                })
        
        return recommendations
    
    def _generate_reliability_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成可靠性优化建议"""
        recommendations = []
        
        for issue in analysis.get('issues', []):
            if '健康检查' in issue:
                recommendations.append({
                    'category': 'reliability',
                    'priority': 'high',
                    'title': '修复健康检查问题',
                    'description': '系统健康检查通过率过低',
                    'suggestions': [
                        '检查并修复健康检查中发现的问题',
                        '优化健康检查逻辑',
                        '增加健康检查监控',
                        '实现自动修复机制'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'high'
                })
            
            elif '组件状态' in issue:
                recommendations.append({
                    'category': 'reliability',
                    'priority': 'high',
                    'title': '修复异常组件',
                    'description': '系统组件状态异常',
                    'suggestions': [
                        '检查异常组件的配置',
                        '重启异常组件',
                        '检查组件依赖关系',
                        '实现组件自动恢复'
                    ],
                    'implementation_difficulty': 'low',
                    'expected_impact': 'high'
                })
            
            elif '错误率' in issue:
                recommendations.append({
                    'category': 'reliability',
                    'priority': 'high',
                    'title': '降低系统错误率',
                    'description': '系统错误率过高',
                    'suggestions': [
                        '加强错误处理和监控',
                        '实现错误重试机制',
                        '优化异常情况处理',
                        '增加错误日志分析'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'high'
                })
        
        return recommendations
    
    def _generate_scalability_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成可扩展性优化建议"""
        recommendations = []
        
        for issue in analysis.get('issues', []):
            if '并发用户' in issue:
                recommendations.append({
                    'category': 'scalability',
                    'priority': 'high',
                    'title': '优化并发处理能力',
                    'description': '并发用户数过高，需要优化并发处理',
                    'suggestions': [
                        '增加服务器资源',
                        '实现负载均衡',
                        '优化并发处理逻辑',
                        '使用分布式架构'
                    ],
                    'implementation_difficulty': 'high',
                    'expected_impact': 'high'
                })
            
            elif '队列大小' in issue:
                recommendations.append({
                    'category': 'scalability',
                    'priority': 'medium',
                    'title': '优化任务队列处理',
                    'description': '任务队列大小过大',
                    'suggestions': [
                        '优化任务处理速度',
                        '增加处理能力',
                        '实现任务优先级管理',
                        '使用分布式任务队列'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'medium'
                })
            
            elif 'CPU使用率' in issue:
                recommendations.append({
                    'category': 'scalability',
                    'priority': 'medium',
                    'title': '优化CPU使用',
                    'description': 'CPU使用率过高',
                    'suggestions': [
                        '优化CPU密集型操作',
                        '增加CPU资源',
                        '使用多核并行处理',
                        '优化算法复杂度'
                    ],
                    'implementation_difficulty': 'high',
                    'expected_impact': 'medium'
                })
            
            elif '内存使用率' in issue:
                recommendations.append({
                    'category': 'scalability',
                    'priority': 'medium',
                    'title': '优化内存使用',
                    'description': '内存使用率过高',
                    'suggestions': [
                        '优化内存使用',
                        '增加内存资源',
                        '实现内存池管理',
                        '优化数据结构'
                    ],
                    'implementation_difficulty': 'medium',
                    'expected_impact': 'medium'
                })
        
        return recommendations
    
    def _generate_general_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成通用优化建议"""
        recommendations = []
        
        # 监控和告警建议
        recommendations.append({
            'category': 'monitoring',
            'priority': 'medium',
            'title': '增强系统监控',
            'description': '建议增强系统监控和告警机制',
            'suggestions': [
                '实现实时监控仪表板',
                '设置关键指标告警',
                '增加性能趋势分析',
                '实现自动故障检测'
            ],
            'implementation_difficulty': 'medium',
            'expected_impact': 'medium'
        })
        
        # 文档和培训建议
        recommendations.append({
            'category': 'documentation',
            'priority': 'low',
            'title': '完善系统文档',
            'description': '建议完善系统文档和操作指南',
            'suggestions': [
                '编写系统架构文档',
                '创建操作手册',
                '提供故障排除指南',
                '建立知识库'
            ],
            'implementation_difficulty': 'low',
            'expected_impact': 'low'
        })
        
        return recommendations
    
    def generate_optimization_report(self, analysis: Dict[str, Any]) -> str:
        """生成优化报告"""
        report = []
        report.append("# RANGEN系统优化建议报告")
        report.append(f"生成时间: {analysis['timestamp']}")
        report.append("")
        
        # 系统状态摘要
        report.append("## 系统状态摘要")
        report.append("")
        
        if 'error' in analysis:
            report.append(f"❌ 分析过程中出现错误: {analysis['error']}")
            return "\n".join(report)
        
        # 性能分析
        performance_analysis = analysis['analysis_results'].get('performance', {})
        report.append("### 性能分析")
        report.append(f"状态: {performance_analysis.get('status', 'unknown').upper()}")
        if performance_analysis.get('issues'):
            report.append("发现的问题:")
            for issue in performance_analysis['issues']:
                report.append(f"- {issue}")
        report.append("")
        
        # 可靠性分析
        reliability_analysis = analysis['analysis_results'].get('reliability', {})
        report.append("### 可靠性分析")
        report.append(f"状态: {reliability_analysis.get('status', 'unknown').upper()}")
        if reliability_analysis.get('issues'):
            report.append("发现的问题:")
            for issue in reliability_analysis['issues']:
                report.append(f"- {issue}")
        report.append("")
        
        # 可扩展性分析
        scalability_analysis = analysis['analysis_results'].get('scalability', {})
        report.append("### 可扩展性分析")
        report.append(f"状态: {scalability_analysis.get('status', 'unknown').upper()}")
        if scalability_analysis.get('issues'):
            report.append("发现的问题:")
            for issue in scalability_analysis['issues']:
                report.append(f"- {issue}")
        report.append("")
        
        # 优化建议
        recommendations = analysis.get('optimization_recommendations', [])
        if recommendations:
            report.append("## 优化建议")
            report.append("")
            
            # 按优先级分组
            high_priority = [r for r in recommendations if r.get('priority') == 'high']
            medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
            low_priority = [r for r in recommendations if r.get('priority') == 'low']
            
            if high_priority:
                report.append("### 🔴 高优先级建议")
                for i, rec in enumerate(high_priority, 1):
                    report.append(f"#### {i}. {rec['title']}")
                    report.append(f"**描述**: {rec['description']}")
                    report.append(f"**实施难度**: {rec['implementation_difficulty']}")
                    report.append(f"**预期影响**: {rec['expected_impact']}")
                    report.append("**建议措施**:")
                    for suggestion in rec['suggestions']:
                        report.append(f"- {suggestion}")
                    report.append("")
            
            if medium_priority:
                report.append("### 🟡 中优先级建议")
                for i, rec in enumerate(medium_priority, 1):
                    report.append(f"#### {i}. {rec['title']}")
                    report.append(f"**描述**: {rec['description']}")
                    report.append(f"**实施难度**: {rec['implementation_difficulty']}")
                    report.append(f"**预期影响**: {rec['expected_impact']}")
                    report.append("**建议措施**:")
                    for suggestion in rec['suggestions']:
                        report.append(f"- {suggestion}")
                    report.append("")
            
            if low_priority:
                report.append("### 🟢 低优先级建议")
                for i, rec in enumerate(low_priority, 1):
                    report.append(f"#### {i}. {rec['title']}")
                    report.append(f"**描述**: {rec['description']}")
                    report.append(f"**实施难度**: {rec['implementation_difficulty']}")
                    report.append(f"**预期影响**: {rec['expected_impact']}")
                    report.append("**建议措施**:")
                    for suggestion in rec['suggestions']:
                        report.append(f"- {suggestion}")
                    report.append("")
        
        return "\n".join(report)
    
    async def run_optimization_analysis(self):
        """运行优化分析"""
        print("🚀 启动RANGEN系统优化分析")
        print("=" * 60)
        
        # 分析系统性能
        analysis = await self.analyze_system_performance()
        
        # 生成优化报告
        report = self.generate_optimization_report(analysis)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"optimization_report_{timestamp}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 优化分析完成，报告已保存: {report_filename}")
        
        # 显示摘要
        recommendations = analysis.get('optimization_recommendations', [])
        if recommendations:
            high_priority = len([r for r in recommendations if r.get('priority') == 'high'])
            medium_priority = len([r for r in recommendations if r.get('priority') == 'medium'])
            low_priority = len([r for r in recommendations if r.get('priority') == 'low'])
            
            print(f"\n📊 优化建议摘要:")
            print(f"  🔴 高优先级: {high_priority} 项")
            print(f"  🟡 中优先级: {medium_priority} 项")
            print(f"  🟢 低优先级: {low_priority} 项")
            print(f"  📝 总计: {len(recommendations)} 项建议")
        
        return analysis

async def main():
    """主函数"""
    advisor = OptimizationAdvisor()
    analysis = await advisor.run_optimization_analysis()
    return analysis

if __name__ == "__main__":
    asyncio.run(main())
