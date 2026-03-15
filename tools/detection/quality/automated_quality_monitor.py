#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化质量监控系统
提供持续的质量检测和报告功能
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .unified_intelligent_quality_center import analyze_code_quality
from src.utils.unified_centers import get_unified_center

# 初始化日志
logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """质量指标"""
    timestamp: str
    file_path: str
    total_issues: int
    hardcoded_values: int
    pseudo_intelligence: int
    mock_responses: int
    simplified_logic: int
    missing_error_handling: int
    quality_score: float
    severity_breakdown: Dict[str, int]

@dataclass
class QualityTrend:
    """质量趋势"""
    period: str
    total_files: int
    total_issues: int
    average_quality_score: float
    improvement_rate: float
    top_issues: List[Tuple[str, int]]

class AutomatedQualityMonitor:
    """自动化质量监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化质量监控器"""
        self.config = config or {}
        self.metrics_history: List[QualityMetrics] = []
        self.trends: List[QualityTrend] = []
        
        # 从配置系统获取设置
        smart_config = get_unified_center('get_smart_config')
        if smart_config and hasattr(smart_config, 'get_config'):
            self.monitor_interval = smart_config.get_config('quality_monitor_interval', self.config, 3600)  # 1小时
            self.quality_threshold = smart_config.get_config('quality_threshold', self.config, 0.7)
            self.alert_threshold = smart_config.get_config('alert_threshold', self.config, 0.5)
            self.report_directory = smart_config.get_config('report_directory', self.config, 'quality_reports')
        else:
            self.monitor_interval = 3600
            self.quality_threshold = 0.7
            self.alert_threshold = 0.5
            self.report_directory = 'quality_reports'
        
        # 确保报告目录存在
        os.makedirs(self.report_directory, exist_ok=True)
        
        logger.info("自动化质量监控器初始化完成")
    
    def scan_directory(self, directory: str, file_patterns: List[str] = None) -> List[str]:
        """扫描目录获取文件列表"""
        if file_patterns is None:
            file_patterns = ['*.py']
        
        files = []
        directory_path = Path(directory)
        
        for pattern in file_patterns:
            files.extend(directory_path.rglob(pattern))
        
        return [str(f) for f in files if f.is_file()]
    
    def analyze_file_quality(self, file_path: str) -> QualityMetrics:
        """分析单个文件的质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = analyze_code_quality(file_path, 'intelligent')
            
            # 统计问题类型
            issue_counts = {
                'hardcoded_value': 0,
                'pseudo_intelligence': 0,
                'mock_response': 0,
                'simplified_logic': 0,
                'missing_error_handling': 0
            }
            
            severity_counts = {
                'low': 0,
                'medium': 0,
                'high': 0,
                'critical': 0
            }
            
            for issue in issues:
                issue_type = issue.issue_type.value
                if issue_type in issue_counts:
                    issue_counts[issue_type] += 1
                
                severity = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            # 计算质量分数
            total_issues = len(issues)
            quality_score = max(0, 1.0 - (total_issues / 100))  # 基于问题数量计算分数
            
            return QualityMetrics(
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                total_issues=total_issues,
                hardcoded_values=issue_counts['hardcoded_value'],
                pseudo_intelligence=issue_counts['pseudo_intelligence'],
                mock_responses=issue_counts['mock_response'],
                simplified_logic=issue_counts['simplified_logic'],
                missing_error_handling=issue_counts['missing_error_handling'],
                quality_score=quality_score,
                severity_breakdown=severity_counts
            )
            
        except Exception as e:
            logger.error(f"分析文件 {file_path} 质量失败: {e}")
            return QualityMetrics(
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                total_issues=0,
                hardcoded_values=0,
                pseudo_intelligence=0,
                mock_responses=0,
                simplified_logic=0,
                missing_error_handling=0,
                quality_score=0.0,
                severity_breakdown={}
            )
    
    def run_quality_scan(self, directories: List[str]) -> List[QualityMetrics]:
        """运行质量扫描"""
        logger.info("开始质量扫描...")
        
        all_metrics = []
        
        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"目录不存在: {directory}")
                continue
            
            files = self.scan_directory(directory)
            logger.info(f"扫描目录 {directory}: 找到 {len(files)} 个文件")
            
            for file_path in files:
                metrics = self.analyze_file_quality(file_path)
                all_metrics.append(metrics)
                self.metrics_history.append(metrics)
        
        logger.info(f"质量扫描完成: 分析了 {len(all_metrics)} 个文件")
        return all_metrics
    
    def calculate_trends(self, period_hours: int = 24) -> QualityTrend:
        """计算质量趋势"""
        cutoff_time = datetime.now() - timedelta(hours=period_hours)
        
        # 过滤指定时间段内的指标
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_time
        ]
        
        if not recent_metrics:
            return QualityTrend(
                period=f"{period_hours}小时",
                total_files=0,
                total_issues=0,
                average_quality_score=0.0,
                improvement_rate=0.0,
                top_issues=[]
            )
        
        # 计算统计信息
        total_files = len(set(m.file_path for m in recent_metrics))
        total_issues = sum(m.total_issues for m in recent_metrics)
        average_quality_score = sum(m.quality_score for m in recent_metrics) / len(recent_metrics)
        
        # 计算改进率(与之前时间段比较)
        older_cutoff = cutoff_time - timedelta(hours=period_hours)
        older_metrics = [
            m for m in self.metrics_history
            if cutoff_time > datetime.fromisoformat(m.timestamp) >= older_cutoff
        ]
        
        if older_metrics:
            older_avg_score = sum(m.quality_score for m in older_metrics) / len(older_metrics)
            improvement_rate = (average_quality_score - older_avg_score) / older_avg_score if older_avg_score > 0 else 0
        else:
            improvement_rate = 0.0
        
        # 统计最常见的问题
        issue_counts = {}
        for metric in recent_metrics:
            if metric.hardcoded_values > 0:
                issue_counts['hardcoded_values'] = issue_counts.get('hardcoded_values', 0) + metric.hardcoded_values
            if metric.pseudo_intelligence > 0:
                issue_counts['pseudo_intelligence'] = issue_counts.get('pseudo_intelligence', 0) + metric.pseudo_intelligence
            if metric.mock_responses > 0:
                issue_counts['mock_responses'] = issue_counts.get('mock_responses', 0) + metric.mock_responses
            if metric.simplified_logic > 0:
                issue_counts['simplified_logic'] = issue_counts.get('simplified_logic', 0) + metric.simplified_logic
            if metric.missing_error_handling > 0:
                issue_counts['missing_error_handling'] = issue_counts.get('missing_error_handling', 0) + metric.missing_error_handling
        
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        trend = QualityTrend(
            period=f"{period_hours}小时",
            total_files=total_files,
            total_issues=total_issues,
            average_quality_score=average_quality_score,
            improvement_rate=improvement_rate,
            top_issues=top_issues
        )
        
        self.trends.append(trend)
        return trend
    
    def generate_quality_report(self, metrics: List[QualityMetrics], trend: QualityTrend) -> Dict[str, Any]:
        """生成质量报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files_analyzed': len(metrics),
                'total_issues_found': sum(m.total_issues for m in metrics),
                'average_quality_score': sum(m.quality_score for m in metrics) / len(metrics) if metrics else 0,
                'quality_threshold': self.quality_threshold,
                'alert_threshold': self.alert_threshold
            },
            'trend_analysis': asdict(trend),
            'issue_breakdown': {
                'hardcoded_values': sum(m.hardcoded_values for m in metrics),
                'pseudo_intelligence': sum(m.pseudo_intelligence for m in metrics),
                'mock_responses': sum(m.mock_responses for m in metrics),
                'simplified_logic': sum(m.simplified_logic for m in metrics),
                'missing_error_handling': sum(m.missing_error_handling for m in metrics)
            },
            'file_details': [asdict(m) for m in metrics],
            'recommendations': self._generate_recommendations(metrics, trend)
        }
        
        return report
    
    def _generate_recommendations(self, metrics: List[QualityMetrics], trend: QualityTrend) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于问题类型生成建议
        issue_breakdown = {
            'hardcoded_values': sum(m.hardcoded_values for m in metrics),
            'pseudo_intelligence': sum(m.pseudo_intelligence for m in metrics),
            'mock_responses': sum(m.mock_responses for m in metrics),
            'simplified_logic': sum(m.simplified_logic for m in metrics),
            'missing_error_handling': sum(m.missing_error_handling for m in metrics)
        }
        
        if issue_breakdown['hardcoded_values'] > 0:
            recommendations.append("清理硬编码值，使用配置系统管理常量")
        
        if issue_breakdown['pseudo_intelligence'] > 0:
            recommendations.append("修复伪智能问题，实现真正的智能逻辑")
        
        if issue_breakdown['mock_responses'] > 0:
            recommendations.append("移除模拟响应，实现真实的功能逻辑")
        
        if issue_breakdown['simplified_logic'] > 0:
            recommendations.append("增强业务逻辑复杂度，避免过度简化")
        
        if issue_breakdown['missing_error_handling'] > 0:
            recommendations.append("完善错误处理机制，提高系统稳定性")
        
        # 基于质量分数生成建议
        avg_score = sum(m.quality_score for m in metrics) / len(metrics) if metrics else 0
        if avg_score < self.alert_threshold:
            recommendations.append("质量分数过低，需要全面改进")
        elif avg_score < self.quality_threshold:
            recommendations.append("质量分数低于阈值，建议改进")
        
        # 基于趋势生成建议
        if trend.improvement_rate < 0:
            recommendations.append("质量呈下降趋势，需要加强质量控制")
        elif trend.improvement_rate > 0.1:
            recommendations.append("质量改进良好，继续保持")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """保存质量报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quality_report_{timestamp}.json"
        
        filepath = os.path.join(self.report_directory, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"质量报告已保存: {filepath}")
        return filepath
    
    def run_continuous_monitoring(self, directories: List[str], interval_hours: int = 1):
        """运行持续监控"""
        logger.info(f"开始持续监控，间隔: {interval_hours}小时")
        
        while True:
            try:
                # 运行质量扫描
                metrics = self.run_quality_scan(directories)
                
                # 计算趋势
                trend = self.calculate_trends(interval_hours)
                
                # 生成报告
                report = self.generate_quality_report(metrics, trend)
                
                # 保存报告
                self.save_report(report)
                
                # 检查是否需要告警
                avg_score = report['summary']['average_quality_score']
                if avg_score < self.alert_threshold:
                    logger.warning(f"质量分数过低: {avg_score:.2f} < {self.alert_threshold}")
                
                # 等待下次扫描
                import time
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("监控已停止")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                import time
                time.sleep(60)  # 错误后等待1分钟再重试

def get_quality_monitor(config: Optional[Dict[str, Any]] = None) -> AutomatedQualityMonitor:
    """获取质量监控器实例"""
    return AutomatedQualityMonitor(config)

# 便捷函数
def run_quality_scan(directories: List[str], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """运行质量扫描并生成报告"""
    monitor = get_quality_monitor(config)
    metrics = monitor.run_quality_scan(directories)
    trend = monitor.calculate_trends()
    report = monitor.generate_quality_report(metrics, trend)
    return report
