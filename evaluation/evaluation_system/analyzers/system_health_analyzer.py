"""
系统健康分析器
分析系统健康状态，包括资源使用、错误率、性能指标等
"""

import re
import psutil
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer

class SystemHealthAnalyzer(BaseAnalyzer):
    """系统健康分析器"""
    
    def __init__(self):
        super().__init__("SystemHealthAnalyzer")
        self.process = psutil.Process()
    
    def analyze(self, log_content: str) -> Dict[str, Any]:
        """分析系统健康指标"""
        return {
            "resource_health": self._analyze_resource_health(log_content),
            "error_health": self._analyze_error_health(log_content),
            "performance_health": self._analyze_performance_health(log_content),
            "stability_health": self._analyze_stability_health(log_content),
            "overall_health": self._calculate_overall_health(log_content)
        }
    
    def _analyze_resource_health(self, log_content: str) -> Dict[str, Any]:
        """分析资源健康状态"""
        # 🚀 修复：优先从系统健康指标中提取资源使用信息
        # 提取资源使用信息
        memory_patterns = [
            r"系统健康指标:\s*内存使用率\s*(\d+\.?\d*)%",  # 🚀 修复：优先匹配系统健康指标格式
            r"内存使用率: (\d+\.?\d*)%",
            r"系统内存已用: (\d+) 字节",
            r"系统内存总量: (\d+) 字节"
        ]
        
        cpu_patterns = [
            r"系统健康指标:\s*CPU使用率\s*(\d+\.?\d*)%",  # 🚀 修复：优先匹配系统健康指标格式
            r"CPU使用率: (\d+\.?\d*)%",
            r"系统负载: \((\d+\.?\d*), (\d+\.?\d*), (\d+\.?\d*)\)"
        ]
        
        disk_patterns = [
            r"系统磁盘使用: (\d+\.?\d*)%"
        ]
        
        memory_data = self._extract_numeric_values(log_content, memory_patterns)
        cpu_data = self._extract_numeric_values(log_content, cpu_patterns)
        disk_data = self._extract_numeric_values(log_content, disk_patterns)
        
        # 获取当前系统状态
        try:
            current_memory = psutil.virtual_memory()
        except Exception:
            current_memory = None
        try:
            current_cpu = psutil.cpu_percent(interval=0.1)
        except Exception:
            current_cpu = None
        try:
            current_disk = psutil.disk_usage('/')
        except Exception:
            current_disk = None
        
        # 计算资源健康分数
        memory_health = self._calculate_memory_health(memory_data, current_memory)
        cpu_health = self._calculate_cpu_health(cpu_data, current_cpu)
        disk_health = self._calculate_disk_health(disk_data, current_disk)
        
        return {
            "memory": {
                "health_score": memory_health,
                "current_usage": current_memory.percent,
                "log_data": self._calculate_statistics(memory_data),
                "status": self._classify_resource_status(current_memory.percent, "memory")
            },
            "cpu": {
                "health_score": cpu_health,
                "current_usage": current_cpu,
                "log_data": self._calculate_statistics(cpu_data),
                "status": self._classify_resource_status(current_cpu, "cpu")
            },
            "disk": {
                "health_score": disk_health,
                "current_usage": current_disk.percent,
                "log_data": self._calculate_statistics(disk_data),
                "status": self._classify_resource_status(current_disk.percent, "disk")
            }
        }
    
    def _calculate_memory_health(self, memory_data: List[float], current_memory: Any) -> float:
        """计算内存健康分数"""
        if memory_data:
            avg_memory = sum(memory_data) / len(memory_data)
        else:
            avg_memory = current_memory.percent
        
        # 内存使用率越低，健康分数越高
        if avg_memory < 50:
            return 1.0
        elif avg_memory < 70:
            return 0.8
        elif avg_memory < 85:
            return 0.6
        elif avg_memory < 95:
            return 0.3
        else:
            return 0.0
    
    def _calculate_cpu_health(self, cpu_data: List[float], current_cpu: float) -> float:
        """计算CPU健康分数"""
        if cpu_data:
            avg_cpu = sum(cpu_data) / len(cpu_data)
        else:
            avg_cpu = current_cpu
        
        # CPU使用率适中时健康分数最高
        if avg_cpu < 30:
            return 1.0
        elif avg_cpu < 50:
            return 0.9
        elif avg_cpu < 70:
            return 0.7
        elif avg_cpu < 90:
            return 0.4
        else:
            return 0.1
    
    def _calculate_disk_health(self, disk_data: List[float], current_disk: Any) -> float:
        """计算磁盘健康分数"""
        if disk_data:
            avg_disk = sum(disk_data) / len(disk_data)
        else:
            avg_disk = current_disk.percent
        
        # 磁盘使用率越低，健康分数越高
        if avg_disk < 60:
            return 1.0
        elif avg_disk < 80:
            return 0.8
        elif avg_disk < 90:
            return 0.5
        elif avg_disk < 95:
            return 0.2
        else:
            return 0.0
    
    def _classify_resource_status(self, usage: float, resource_type: str) -> str:
        """分类资源状态"""
        thresholds = {
            "memory": {"good": 50, "warning": 70, "critical": 85},
            "cpu": {"good": 30, "warning": 50, "critical": 70},
            "disk": {"good": 60, "warning": 80, "critical": 90}
        }
        
        if resource_type not in thresholds:
            return "unknown"
        
        thresh = thresholds[resource_type]
        if usage < thresh["good"]:
            return "good"
        elif usage < thresh["warning"]:
            return "warning"
        elif usage < thresh["critical"]:
            return "critical"
        else:
            return "danger"
    
    def _analyze_error_health(self, log_content: str) -> Dict[str, Any]:
        """分析错误健康状态"""
        # 提取错误信息
        error_patterns = [
            r"ERROR - (.+)",
            r"错误: (.+)",
            r"失败: (.+)",
            r"异常: (.+)"
        ]
        
        warning_patterns = [
            r"WARNING - (.+)",
            r"警告: (.+)"
        ]
        
        errors = self._extract_pattern_matches(log_content, error_patterns)
        warnings = self._extract_pattern_matches(log_content, warning_patterns)
        
        # 分析错误趋势
        error_trend = self._analyze_error_trend(log_content)
        
        # 计算错误健康分数
        total_log_lines = len(log_content.split('\n'))
        error_rate = len(errors) / total_log_lines if total_log_lines > 0 else 0.0
        warning_rate = len(warnings) / total_log_lines if total_log_lines > 0 else 0.0
        
        # 错误率越低，健康分数越高
        error_health = max(0, 1 - error_rate * 100)
        warning_health = max(0, 1 - warning_rate * 50)
        
        return {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "error_rate": error_rate,
            "warning_rate": warning_rate,
            "error_health_score": error_health,
            "warning_health_score": warning_health,
            "error_trend": error_trend,
            "overall_error_health": (error_health + warning_health) / 2
        }
    
    def _analyze_error_trend(self, log_content: str) -> str:
        """分析错误趋势"""
        # 按时间分割日志
        log_lines = log_content.split('\n')
        if len(log_lines) < 10:
            return "insufficient_data"
        
        # 将日志分为前半部分和后半部分
        mid_point = len(log_lines) // 2
        first_half = log_lines[:mid_point]
        second_half = log_lines[mid_point:]
        
        # 计算每半部分的错误数
        first_half_errors = len([line for line in first_half if 'ERROR' in line or '错误' in line])
        second_half_errors = len([line for line in second_half if 'ERROR' in line or '错误' in line])
        
        # 计算趋势
        if second_half_errors > first_half_errors * 1.2:
            return "increasing"
        elif second_half_errors < first_half_errors * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_performance_health(self, log_content: str) -> Dict[str, Any]:
        """分析性能健康状态"""
        # 提取性能指标
        response_time_patterns = [
            r"响应时间: (\d+\.?\d*)",
            r"执行时间: (\d+\.?\d*)",
            r"processing_time: (\d+\.?\d*)"
        ]
        
        throughput_patterns = [
            r"吞吐量: (\d+\.?\d*)",
            r"throughput: (\d+\.?\d*)",
            r"处理速度: (\d+\.?\d*)"
        ]
        
        response_times = self._extract_numeric_values(log_content, response_time_patterns)
        throughputs = self._extract_numeric_values(log_content, throughput_patterns)
        
        # 计算性能健康分数
        response_health = self._calculate_response_time_health(response_times)
        throughput_health = self._calculate_throughput_health(throughputs)
        
        return {
            "response_time": {
                "health_score": response_health,
                "stats": self._calculate_statistics(response_times),
                "status": self._classify_performance_status(response_times, "response_time")
            },
            "throughput": {
                "health_score": throughput_health,
                "stats": self._calculate_statistics(throughputs),
                "status": self._classify_performance_status(throughputs, "throughput")
            },
            "overall_performance_health": (response_health + throughput_health) / 2
        }
    
    def _calculate_response_time_health(self, response_times: List[float]) -> float:
        """计算响应时间健康分数"""
        if not response_times:
            return 0.5  # 默认分数
        
        avg_response_time = sum(response_times) / len(response_times)
        
        # 响应时间越短，健康分数越高
        if avg_response_time < 1.0:
            return 1.0
        elif avg_response_time < 3.0:
            return 0.8
        elif avg_response_time < 5.0:
            return 0.6
        elif avg_response_time < 10.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_throughput_health(self, throughputs: List[float]) -> float:
        """计算吞吐量健康分数"""
        if not throughputs:
            return 0.5  # 默认分数
        
        avg_throughput = sum(throughputs) / len(throughputs)
        
        # 吞吐量越高，健康分数越高
        if avg_throughput > 100:
            return 1.0
        elif avg_throughput > 50:
            return 0.8
        elif avg_throughput > 20:
            return 0.6
        elif avg_throughput > 10:
            return 0.4
        else:
            return 0.2
    
    def _classify_performance_status(self, values: List[float], metric_type: str) -> str:
        """分类性能状态"""
        if not values:
            return "unknown"
        
        avg_value = sum(values) / len(values)
        
        if metric_type == "response_time":
            if avg_value < 1.0:
                return "excellent"
            elif avg_value < 3.0:
                return "good"
            elif avg_value < 5.0:
                return "average"
            else:
                return "poor"
        elif metric_type == "throughput":
            if avg_value > 100:
                return "excellent"
            elif avg_value > 50:
                return "good"
            elif avg_value > 20:
                return "average"
            else:
                return "poor"
        else:
            return "unknown"
    
    def _analyze_stability_health(self, log_content: str) -> Dict[str, Any]:
        """分析稳定性健康状态"""
        # 提取稳定性相关指标
        restart_patterns = [
            r"系统重启",
            r"restart",
            r"重新启动"
        ]
        
        recovery_patterns = [
            r"恢复",
            r"recovery",
            r"重试",
            r"retry"
        ]
        
        success_patterns = [
            r"成功",
            r"success",
            r"完成",
            r"completed"
        ]
        
        restarts = len(self._extract_pattern_matches(log_content, restart_patterns))
        recoveries = len(self._extract_pattern_matches(log_content, recovery_patterns))
        successes = len(self._extract_pattern_matches(log_content, success_patterns))
        
        # 计算稳定性分数
        stability_score = self._calculate_stability_score(restarts, recoveries, successes)
        
        return {
            "restart_count": restarts,
            "recovery_count": recoveries,
            "success_count": successes,
            "stability_score": stability_score,
            "stability_status": self._classify_stability_status(stability_score)
        }
    
    def _calculate_stability_score(self, restarts: int, recoveries: int, successes: int) -> float:
        """计算稳定性分数"""
        total_operations = successes + restarts
        if total_operations == 0:
            return 0.5
        
        # 重启次数越少，恢复能力越强，成功次数越多，稳定性越高
        restart_penalty = restarts / total_operations
        recovery_bonus = min(0.2, recoveries / total_operations)
        success_bonus = successes / total_operations
        
        stability = success_bonus - restart_penalty + recovery_bonus
        return max(0, min(1, stability))
    
    def _classify_stability_status(self, stability_score: float) -> str:
        """分类稳定性状态"""
        if stability_score >= 0.8:
            return "excellent"
        elif stability_score >= 0.6:
            return "good"
        elif stability_score >= 0.4:
            return "average"
        elif stability_score >= 0.2:
            return "poor"
        else:
            return "critical"
    
    def _calculate_overall_health(self, log_content: str) -> Dict[str, Any]:
        """计算整体健康状态"""
        # 获取各维度健康分析结果
        resource_health = self._analyze_resource_health(log_content)
        error_health = self._analyze_error_health(log_content)
        performance_health = self._analyze_performance_health(log_content)
        stability_health = self._analyze_stability_health(log_content)
        
        # 计算各维度健康分数
        resource_score = (
            resource_health["memory"]["health_score"] +
            resource_health["cpu"]["health_score"] +
            resource_health["disk"]["health_score"]
        ) / 3
        
        error_score = error_health["overall_error_health"]
        performance_score = performance_health["overall_performance_health"]
        stability_score = stability_health["stability_score"]
        
        # 计算整体健康分数
        overall_score = (
            resource_score * 0.3 +
            error_score * 0.25 +
            performance_score * 0.25 +
            stability_score * 0.2
        )
        
        return {
            "overall_health_score": overall_score,
            "health_level": self._classify_health_level(overall_score),
            "dimension_scores": {
                "resource": resource_score,
                "error": error_score,
                "performance": performance_score,
                "stability": stability_score
            },
            "recommendations": self._generate_health_recommendations(
                resource_score, error_score, performance_score, stability_score
            )
        }
    
    def _classify_health_level(self, score: float) -> str:
        """分类健康水平"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "average"
        elif score >= 0.3:
            return "poor"
        else:
            return "critical"
    
    def _generate_health_recommendations(self, resource_score: float, error_score: float, 
                                       performance_score: float, stability_score: float) -> List[str]:
        """生成健康建议"""
        recommendations = []
        
        if resource_score < 0.5:
            recommendations.append("资源使用率过高，建议优化内存和CPU使用")
        
        if error_score < 0.5:
            recommendations.append("错误率较高，建议检查系统日志并修复问题")
        
        if performance_score < 0.5:
            recommendations.append("性能较差，建议优化响应时间和吞吐量")
        
        if stability_score < 0.5:
            recommendations.append("系统稳定性不足，建议增加错误处理和恢复机制")
        
        if not recommendations:
            recommendations.append("系统运行状况良好，继续保持")
        
        return recommendations
