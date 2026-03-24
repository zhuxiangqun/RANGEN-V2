"""
性能分析器
分析系统性能指标，包括响应时间、资源使用等
"""

import re
import psutil
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer

class PerformanceAnalyzer(BaseAnalyzer):
    """性能分析器"""
    
    def __init__(self):
        super().__init__("PerformanceAnalyzer")
        self.process = psutil.Process()
    
    def analyze(self, log_content: str) -> Dict[str, Any]:
        """分析性能指标"""
        return {
            "response_time": self._analyze_response_time(log_content),
            "resource_usage": self._analyze_resource_usage(log_content),
            "throughput": self._analyze_throughput(log_content),
            "memory_efficiency": self._analyze_memory_efficiency(log_content),
            "cpu_efficiency": self._analyze_cpu_efficiency(log_content)
        }
    
    def _analyze_response_time(self, log_content: str) -> Dict[str, Any]:
        """分析响应时间"""
        # 提取推理时间（计算结束时间-开始时间）
        start_times = self._extract_numeric_values(log_content, [r"推理开始时间: (\d+\.?\d*)"])
        end_times = self._extract_numeric_values(log_content, [r"推理结束时间: (\d+\.?\d*)"])
        
        # 计算实际处理时间
        times = []
        for i in range(min(len(start_times), len(end_times))):
            processing_time = end_times[i] - start_times[i]
            times.append(processing_time)
        
        # 从JSON格式中提取processing_time
        json_processing_times = self._extract_numeric_values(log_content, [r'"processing_time": (\d+\.?\d*)'])
        times.extend(json_processing_times)
        
        # 其他时间模式
        other_time_patterns = [
            r"FRAMES sample=\d+/\d+ success=True took=([\d.]+)s",  # FRAMES格式的处理时间
            r"执行时间: (\d+\.?\d*)",
            r"响应时间: (\d+\.?\d*)"
        ]
        other_times = self._extract_numeric_values(log_content, other_time_patterns)
        times.extend(other_times)
        
        time_stats = self._calculate_statistics(times)
        
        # 计算响应时间分布
        response_categories = self._categorize_response_times(times)
        
        return {
            "time_stats": time_stats,
            "response_categories": response_categories,
            "avg_response_time": time_stats["average"],
            "max_response_time": time_stats["max"],
            "min_response_time": time_stats["min"]
        }
    
    def _categorize_response_times(self, times: List[float]) -> Dict[str, int]:
        """将响应时间分类"""
        categories = {
            "fast": 0,      # < 1秒
            "normal": 0,    # 1-5秒
            "slow": 0,      # 5-10秒
            "very_slow": 0  # > 10秒
        }
        
        for time_val in times:
            if time_val < 1.0:
                categories["fast"] += 1
            elif time_val < 5.0:
                categories["normal"] += 1
            elif time_val < 10.0:
                categories["slow"] += 1
            else:
                categories["very_slow"] += 1
        
        return categories
    
    def _analyze_resource_usage(self, log_content: str) -> Dict[str, Any]:
        """分析资源使用情况"""
        # 从日志中提取资源使用信息
        memory_patterns = [
            r"系统内存总量: (\d+) 字节",
            r"系统内存已用: (\d+) 字节",
            r"内存使用率: (\d+\.?\d*)%"
        ]
        
        cpu_patterns = [
            r"系统CPU核心数: (\d+)",
            r"系统CPU频率: (\d+) MHz",
            r"CPU使用率: (\d+\.?\d*)%"
        ]
        
        disk_patterns = [
            r"系统磁盘使用: (\d+\.?\d*)%"
        ]
        
        memory_data = self._extract_numeric_values(log_content, memory_patterns)
        cpu_data = self._extract_numeric_values(log_content, cpu_patterns)
        disk_data = self._extract_numeric_values(log_content, disk_patterns)
        
        # 获取当前系统资源状态
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
        
        return {
            "memory": {
                "log_data": self._calculate_statistics(memory_data),
                "current_usage": current_memory.percent,
                "current_available": current_memory.available,
                "current_total": current_memory.total
            },
            "cpu": {
                "log_data": self._calculate_statistics(cpu_data),
                "current_usage": current_cpu,
                "core_count": self._safe_cpu_count()
            },
            "disk": {
                "log_data": self._calculate_statistics(disk_data),
                "current_usage": current_disk.percent,
                "current_free": current_disk.free,
                "current_total": current_disk.total
            }
        }

    def _safe_cpu_count(self) -> Any:
        """安全获取CPU核心数，兼容某些平台的psutil异常"""
        try:
            if hasattr(psutil, 'cpu_count'):
                return psutil.cpu_count()
        except Exception:
            try:
                import os as _os
                return _os.cpu_count()
            except Exception:
                return None
        return None
    
    def _analyze_throughput(self, log_content: str) -> Dict[str, Any]:
        """分析吞吐量"""
        # 提取处理数量和时间信息
        count_patterns = [
            r"处理样本 (\d+)/(\d+)",
            r"样本处理完成",
            r"处理完成"
        ]
        
        # 统计处理事件数量
        processing_events = len(self._extract_pattern_matches(log_content, count_patterns))
        
        # 提取时间范围
        time_patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"
        ]
        
        timestamps = self._extract_pattern_matches(log_content, time_patterns)
        
        # 计算时间跨度
        time_span = 0.0
        if len(timestamps) >= 2:
            try:
                from datetime import datetime
                start_time = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S,%f")
                end_time = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S,%f")
                time_span = (end_time - start_time).total_seconds()
            except ValueError:
                time_span = 0.0
        
        # 计算吞吐量
        throughput = processing_events / time_span if time_span > 0 else 0.0
        
        return {
            "processing_events": processing_events,
            "time_span": time_span,
            "throughput": throughput,
            "events_per_second": throughput,
            "events_per_minute": throughput * 60
        }
    
    def _analyze_memory_efficiency(self, log_content: str) -> Dict[str, Any]:
        """分析内存效率"""
        memory_patterns = [
            r"内存使用率: (\d+\.?\d*)%",
            r"系统内存已用: (\d+) 字节",
            r"系统内存总量: (\d+) 字节"
        ]
        
        memory_data = self._extract_numeric_values(log_content, memory_patterns)
        
        # 计算内存效率分数
        efficiency_score = 0.0
        if memory_data:
            avg_memory_usage = sum(memory_data) / len(memory_data)
            # 内存使用率越低，效率分数越高
            efficiency_score = max(0, 1 - avg_memory_usage / 100.0)
        
        return {
            "memory_usage_stats": self._calculate_statistics(memory_data),
            "efficiency_score": efficiency_score,
            "avg_memory_usage": sum(memory_data) / len(memory_data) if memory_data else 0.0
        }
    
    def _analyze_cpu_efficiency(self, log_content: str) -> Dict[str, Any]:
        """分析CPU效率"""
        cpu_patterns = [
            r"CPU使用率: (\d+\.?\d*)%"
        ]
        
        cpu_data = self._extract_numeric_values(log_content, cpu_patterns)
        
        # 提取系统负载 - 使用特殊处理因为返回多个捕获组
        load_pattern = r"系统负载: \((\d+\.?\d*), (\d+\.?\d*), (\d+\.?\d*)\)"
        load_matches = re.findall(load_pattern, log_content, re.IGNORECASE)
        load_values = []
        
        for match_tuple in load_matches:
            try:
                # match_tuple 是一个包含三个值的元组
                for value in match_tuple:
                    load_values.append(float(value))
            except (ValueError, IndexError):
                continue
        
        # 计算CPU效率分数
        efficiency_score = 0.0
        if cpu_data:
            avg_cpu_usage = sum(cpu_data) / len(cpu_data)
            # CPU使用率适中时效率最高
            if avg_cpu_usage < 50:
                efficiency_score = avg_cpu_usage / 50.0
            else:
                efficiency_score = max(0, 1 - (avg_cpu_usage - 50) / 50.0)
        
        return {
            "cpu_usage_stats": self._calculate_statistics(cpu_data),
            "load_stats": self._calculate_statistics(load_values),
            "efficiency_score": efficiency_score,
            "avg_cpu_usage": sum(cpu_data) / len(cpu_data) if cpu_data else 0.0
        }
