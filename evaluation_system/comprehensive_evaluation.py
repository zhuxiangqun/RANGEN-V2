#!/usr/bin/env python3
"""
基于日志的评测系统 - 纯评测功能
通过分析核心系统的日志文件来评估系统性能和质量
"""

import json
import time
import os
import asyncio
import logging
import re
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 评测系统只分析日志，不直接调用核心系统

# 评测系统使用自己的日志模块，不依赖核心系统
import logging

# 导入模块化分析器
from analyzers import (
    FramesAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    IntelligenceAnalyzer,
    SystemHealthAnalyzer,
    ReasoningAnalyzer
)

class LogBasedEvaluator:
    """基于日志的评测器 - 纯评测功能"""
    
    def __init__(self, log_file: Optional[str] = None):
        # 先初始化logger
        self.logger = logging.getLogger(__name__)
        
        # 如果没有指定日志文件，自动查找最新的日志文件
        if log_file is None:
            self.log_file = self._find_latest_log_file()
        else:
            # 确保日志文件路径正确
            if not os.path.isabs(log_file):
                # 如果是相对路径，尝试从项目根目录查找
                project_root = Path(__file__).parent.parent.parent.parent
                log_file_path = project_root / log_file
                if log_file_path.exists():
                    self.log_file = str(log_file_path)
                else:
                    self.log_file = log_file
            else:
                self.log_file = log_file
        
        # 评测系统只分析日志，不初始化核心系统
        
        # 初始化模块化分析器
        self.frames_analyzer = FramesAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.intelligence_analyzer = IntelligenceAnalyzer()
        self.system_health_analyzer = SystemHealthAnalyzer()
        self.reasoning_analyzer = ReasoningAnalyzer()
        
        # 评测结果存储
        self.evaluation_results = {}
        self.performance_metrics = {}
        self.quality_metrics = {}
    
    def _find_latest_log_file(self) -> str:
        """查找最新的日志文件"""
        try:
            # 从当前工作目录向上查找项目根目录
            current_dir = Path.cwd()
            project_root = current_dir.parent if current_dir.name == "evaluation_system" else current_dir
            log_dir = project_root
            
            # 优先查找 research_system.log 文件
            default_log = log_dir / "research_system.log"
            if default_log.exists():
                self.logger.info(f"找到标准日志文件: {default_log}")
                return str(default_log)
            
            # 如果没有找到标准日志文件，查找带时间戳的日志文件
            log_files = list(log_dir.glob("research_system_*.log"))
            
            if log_files:
                # 按修改时间排序，返回最新的
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                self.logger.info(f"找到时间戳日志文件: {latest_log}")
                return str(latest_log)
            else:
                raise FileNotFoundError("未找到任何日志文件")
            
        except Exception as e:
            self.logger.error(f"查找最新日志文件失败: {e}")
            # 返回默认日志文件路径
            project_root = Path(__file__).parent.parent.parent.parent
            return str(project_root / "research_system.log")
        
    def run_frames_evaluation(self, sample_count: int = 50) -> Dict[str, Any]:
        """运行FRAMES评测 - 只分析日志"""
        self.logger.error("评测系统只分析日志，不支持直接运行FRAMES评测")
        return {"error": "评测系统只分析日志，请先运行核心系统生成日志"}
    
    def _load_frames_dataset(self, sample_count: int) -> List[Dict[str, Any]]:
        """加载FRAMES数据集"""
        try:
            # 检查多个可能的数据集位置
            dataset_paths = [
                "data/frames_dataset.json",
                "data/frames-benchmark/queries.json",
                "data/frames_benchmark/frames_dataset.json"
            ]
            
            for dataset_path in dataset_paths:
                if os.path.exists(dataset_path):
                    with open(dataset_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list) and len(data) > 0:
                        # 限制样本数量
                        if sample_count < len(data):
                            data = data[:sample_count]
                        self.logger.info(f"成功加载 {len(data)} 个FRAMES样本")
                        return data
            
            self.logger.error("未找到FRAMES数据集文件")
            return []
            
        except Exception as e:
            self.logger.error(f"加载FRAMES数据集失败: {e}")
            return []

    def analyze_log_file(self) -> Dict[str, Any]:
        """分析核心系统的日志文件 - 使用模块化分析器"""
        if not os.path.exists(self.log_file):
            self.logger.warning(f"日志文件 {self.log_file} 不存在")
            return {"error": "日志文件不存在"}
        
        try:
            # 尝试多种编码方式读取日志文件
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk', 'gb2312']
            log_content = None
            for encoding in encodings:
                try:
                    with open(self.log_file, 'r', encoding=encoding, errors='replace') as f:
                        log_content = f.read()
                    self.logger.info(f"成功使用编码 {encoding} 读取日志文件")
                    break
                except Exception:
                    continue
            
            if log_content is None:
                # 如果所有编码都失败，使用二进制模式读取并替换无效字节
                with open(self.log_file, 'rb') as f:
                    raw_content = f.read()
                log_content = raw_content.decode('utf-8', errors='replace')
            
            self.logger.info(f"开始分析日志文件: {self.log_file}")
            
            # 提取样本数
            sample_count = self._extract_sample_count(log_content)
            
            # 使用模块化分析器进行分析
            # 🚀 修复：先获取intelligence_analyzer结果，然后合并ai_algorithm_score
            intelligence_analyzer_result = self.intelligence_analyzer.analyze(log_content)
            intelligence_level_result = self._analyze_intelligence_level(log_content)
            
            # 🚀 修复：添加ai_algorithm_score字段到intelligence_score中，并重新计算整体分数
            if 'intelligence_score' in intelligence_analyzer_result:
                ai_algorithm_score = intelligence_level_result.get('ai_algorithm_score', 0.0)
                intelligence_analyzer_result['intelligence_score']['ai_algorithm_score'] = ai_algorithm_score
                
                # 🚀 修复：使用ai_algorithm_score重新计算整体智能分数（简单平均）
                learning_score = intelligence_analyzer_result['intelligence_score'].get('learning_score', 0.0)
                reasoning_score = intelligence_analyzer_result['intelligence_score'].get('reasoning_score', 0.0)
                adaptation_score = intelligence_analyzer_result['intelligence_score'].get('adaptation_score', 0.0)
                
                # 使用简单平均，更公平
                overall_score = (ai_algorithm_score + learning_score + reasoning_score + adaptation_score) / 4.0
                intelligence_analyzer_result['intelligence_score']['overall_intelligence_score'] = overall_score
            
            analysis_result = {
                "log_file": self.log_file,
                "analysis_time": datetime.now().isoformat(),
                "file_size": len(log_content),
                "total_lines": len(log_content.split('\n')),
                "sample_count": sample_count,
                
                # 使用模块化分析器
                "frames_analysis": self.frames_analyzer.analyze(log_content),
                "performance_analysis": self.performance_analyzer.analyze(log_content),
                "quality_analysis": self.quality_analyzer.analyze(log_content),
                "intelligence_analysis": intelligence_analyzer_result,
                "system_health_analysis": self.system_health_analyzer.analyze(log_content),
                "reasoning_analysis": self.reasoning_analyzer.analyze(log_content),
                
                # 兼容性字段（保持原有接口）
                "frames_accuracy": self.frames_analyzer.analyze(log_content)["accuracy"],
                "reasoning_efficiency": self.frames_analyzer.analyze(log_content)["reasoning_efficiency"],
                "method_innovation": self.frames_analyzer.analyze(log_content)["innovation"],
                "intelligence_level": self.intelligence_analyzer.analyze(log_content)["intelligence_score"]["overall_intelligence_score"],
                "agent_coordination": self.quality_analyzer.analyze(log_content)["maintainability"],
                "module_integration": self.quality_analyzer.analyze(log_content)["maintainability"],
                
                # 4. 系统自我学习程度
                "ml_learning": self._analyze_ml_learning(log_content),
                "rl_learning": self._analyze_rl_learning(log_content),
                "self_learning": self._analyze_self_learning(log_content),
                
                # 5. 系统性能
                "performance_metrics": self._analyze_performance(log_content),
                "system_health": self._analyze_system_health(log_content),
                
                # 6. 详实的研究报告
                "research_report_quality": self._analyze_research_report_quality(log_content),
                
                # 协同作用分析
                "ml_rl_synergy": self._analyze_ml_rl_synergy(log_content),
                "prompt_context_synergy": self._analyze_prompt_context_synergy(log_content),
                
                # 复杂逻辑推理能力
                "complex_reasoning": self._analyze_complex_reasoning(log_content),
                
                # RANGEN查询处理流程
                "query_processing_flow": self._analyze_query_processing_flow(log_content),
                
                # 基础指标
                "queries_analyzed": self._extract_query_count(log_content),
                "query_count": self._extract_query_count(log_content),  # 添加query_count字段
                # 🚀 改进：明确区分查询成功率和样本成功率
                "success_rate_analysis": self._calculate_success_rate(log_content),
                "success_rate": self._calculate_success_rate(log_content)["success_rate"],  # 兼容性：使用样本成功率
                "error_analysis": self._analyze_errors(log_content)
            }
            
            self.evaluation_results = analysis_result
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"分析日志文件失败: {e}")
            return {"error": str(e)}
    
    def _extract_query_count(self, log_content: str) -> int:
        """提取查询数量 - 🚀 修复：只统计唯一样本ID，避免重复统计"""
        # 方法1: 从FRAMES样本格式提取唯一样本ID（优先）
        frames_sample_pattern = r"FRAMES sample=(\d+)/\d+"
        sample_ids = set(re.findall(frames_sample_pattern, log_content, re.IGNORECASE))
        
        if sample_ids:
            return len(sample_ids)
        
        # 方法2: 回退到原有逻辑（如果没有FRAMES格式）
        query_patterns = [
            r"处理查询|Processing query|Query processed",
            r"开始分析|Starting analysis|Analysis started",
            r"查询请求|Query request|Request received"
        ]
        
        total_queries = 0
        for pattern in query_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            total_queries += len(matches)
        
        return total_queries
    
    def _calculate_success_rate(self, log_content: str) -> Dict[str, Any]:
        """🚀 改进：计算查询成功率和样本成功率（明确区分）"""
        # 1. 查询成功率（基于FRAMES样本格式，更准确）
        # 🚀 修复：优先使用FRAMES格式，避免匹配诊断信息
        frames_success_pattern = r"FRAMES sample=\d+/\d+\s+success=True"
        frames_success_matches = re.findall(frames_success_pattern, log_content, re.IGNORECASE)
        query_success_count = len(frames_success_matches)
        
        frames_error_pattern = r"FRAMES sample=\d+/\d+\s+success=False"
        frames_error_matches = re.findall(frames_error_pattern, log_content, re.IGNORECASE)
        query_error_count = len(frames_error_matches)
        
        # 如果没有FRAMES格式，回退到原有逻辑（但排除诊断信息）
        if query_success_count == 0:
            query_success_patterns = [
                r"查询成功(?!.*success=True)",  # 排除包含success=True的行（诊断信息）
                r"Query successful(?!.*success=True)",
                r"分析完成|Analysis completed",
                r"结果生成|Result generated"
            ]
            
            query_success_count = 0
            for pattern in query_success_patterns:
                matches = re.findall(pattern, log_content, re.IGNORECASE)
                query_success_count += len(matches)
        
        if query_error_count == 0:
            query_error_patterns = [
                r"查询失败|Query failed",
                r"分析错误|Analysis error",
                r"异常|Exception occurred"
            ]
            
            query_error_count = 0
            for pattern in query_error_patterns:
                matches = re.findall(pattern, log_content, re.IGNORECASE)
                query_error_count += len(matches)
        
        # 🚀 修复：排除误匹配的"Error"（如"error=None"、"error: None"等）
        # 查找所有包含"Error"的行，但排除"error=None"等情况
        error_lines = re.findall(r'^.*Error.*$', log_content, re.MULTILINE | re.IGNORECASE)
        false_positive_patterns = [
            r'error\s*[:=]\s*(?:None|null|False|0)',
            r'error\s*[:=]\s*$',  # error: 后面是空
            r'has_data=True.*error=None',
            r'success=True.*error=None',
        ]
        
        # 统计误匹配的数量
        false_positive_count = 0
        for line in error_lines:
            for fp_pattern in false_positive_patterns:
                if re.search(fp_pattern, line, re.IGNORECASE):
                    false_positive_count += 1
                    break
        
        # 从query_error_count中减去误匹配的数量
        # 注意：这里假设所有误匹配的"Error"都来自"error=None"等情况
        query_error_count = max(0, query_error_count - false_positive_count)
        
        query_total = query_success_count + query_error_count
        query_success_rate = query_success_count / query_total if query_total > 0 else 0.0
        
        # 2. 样本成功率（基于样本数量，与准确率使用相同基准）
        # 🚀 修复：支持多种日志格式，包括"FRAMES sample=...success=True"格式
        sample_success_count = 0
        
        # 方法1: 从"FRAMES sample=...success=True"格式提取（优先）
        frames_sample_pattern = r"FRAMES sample=\d+/\d+\s+success=True"
        frames_sample_matches = re.findall(frames_sample_pattern, log_content, re.IGNORECASE)
        if frames_sample_matches:
            sample_success_count = len(frames_sample_matches)
        
        # 方法2: 从"查询完成.*样本ID=...success=True"格式提取
        if sample_success_count == 0:
            sample_completed_pattern = r"查询完成.*样本ID=(\d+)|查询完成.*sample[_\s]*ID[=:](\d+)"
            sample_completed_matches = re.findall(sample_completed_pattern, log_content, re.IGNORECASE)
            
            sample_success_ids = set()
            for match in sample_completed_matches:
                sample_id = match[0] if match[0] else match[1] if len(match) > 1 else None
                if sample_id:
                    # 查找该样本ID对应的查询完成日志，检查是否成功
                    pattern_with_id = rf"查询完成.*样本ID={sample_id}.*success=True|查询完成.*success=True.*样本ID={sample_id}"
                    if re.search(pattern_with_id, log_content, re.IGNORECASE):
                        sample_success_ids.add(sample_id)
            
            sample_success_count = len(sample_success_ids)
        
        # 方法3: 从其他样本成功模式提取
        if sample_success_count == 0:
            sample_success_patterns = [
                r"样本.*成功|Sample.*success|样本.*完成|Sample.*completed",
                r"查询完成.*success=True.*样本|Query completed.*success=True.*sample",
                r"样本.*处理完成|Sample.*processing completed"
            ]
            
            for pattern in sample_success_patterns:
                matches = re.findall(pattern, log_content, re.IGNORECASE)
                if matches:
                    sample_success_count = len(matches)
                    break
        
        # 方法4: 如果无法从日志中提取样本级别的成功/失败，使用"查询完成"数量作为样本成功数（fallback）
        if sample_success_count == 0:
            query_completed_pattern = r"查询完成.*success=True"
            query_completed_matches = re.findall(query_completed_pattern, log_content, re.IGNORECASE)
            sample_success_count = len(query_completed_matches)
        
        # 获取样本数量（与准确率计算使用相同的基准）
        sample_count = self._extract_sample_count(log_content)
        sample_success_rate = sample_success_count / sample_count if sample_count > 0 else 0.0
        
        return {
            "query_success_rate": query_success_rate,
            "query_success_count": query_success_count,
            "query_error_count": query_error_count,
            "query_total": query_total,
            "sample_success_rate": sample_success_rate,
            "sample_success_count": sample_success_count,
            "sample_total": sample_count,
            # 兼容性：保持原有字段名（使用样本成功率，与准确率统一基准）
            "success_rate": sample_success_rate
        }
    
    def _analyze_performance(self, log_content: str) -> Dict[str, Any]:
        """分析性能指标"""
        # 提取时间相关日志
        time_patterns = [
            r"耗时|Duration|Time taken: (\d+\.?\d*)",
            r"处理时间|Processing time: (\d+\.?\d*)",
            r"响应时间|Response time: (\d+\.?\d*)"
        ]
        
        times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                try:
                    times.append(float(match))
                except ValueError:
                    continue
        
        if not times:
            return {"average_time": 0.0, "max_time": 0.0, "min_time": 0.0}
        
        return {
            "average_time": sum(times) / len(times),
            "max_time": max(times),
            "min_time": min(times),
            "total_operations": len(times)
        }
    
    def _analyze_quality(self, log_content: str) -> Dict[str, Any]:
        """分析质量指标"""
        # 提取质量相关日志
        quality_patterns = [
            r"质量分数|Quality score: (\d+\.?\d*)",
            r"准确率|Accuracy: (\d+\.?\d*)",
            r"置信度|Confidence: (\d+\.?\d*)"
        ]
        
        scores = []
        for pattern in quality_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                try:
                    scores.append(float(match))
                except ValueError:
                    continue
        
        if not scores:
            return {"average_quality": 0.0, "max_quality": 0.0, "min_quality": 0.0}
        
        return {
            "average_quality": sum(scores) / len(scores),
            "max_quality": max(scores),
            "min_quality": min(scores),
            "total_scores": len(scores)
        }
    
    def _analyze_errors(self, log_content: str) -> Dict[str, Any]:
        """分析错误信息
        
        🚀 修复：只统计实际错误事件，而非关键词匹配
        - 统计JSON格式的错误日志（event_type为"error"的实际错误）
        - 避免统计JSON字段名中的"error"关键词
        - 避免统计代码中的"error"关键词
        """
        error_counts = {
            "error|错误|exception|异常": 0,
            "warning|警告|warning": 0,
            "critical|严重|critical": 0
        }
        
        # 🚀 修复：只统计实际的错误事件（JSON格式的event_type）
        # 匹配JSON格式：{"event_type": "error", ...}
        json_error_pattern = r'\{"event_type"\s*:\s*"error"'
        json_warning_pattern = r'\{"event_type"\s*:\s*"warning"'
        json_critical_pattern = r'\{"event_type"\s*:\s*"critical"'
        json_timeout_pattern = r'\{"event_type"\s*:\s*"timeout"'
        
        # 统计JSON格式的错误事件
        json_errors = len(re.findall(json_error_pattern, log_content, re.IGNORECASE))
        json_warnings = len(re.findall(json_warning_pattern, log_content, re.IGNORECASE))
        json_critical = len(re.findall(json_critical_pattern, log_content, re.IGNORECASE))
        json_timeouts = len(re.findall(json_timeout_pattern, log_content, re.IGNORECASE))
        
        # 🚀 修复：timeout也算作错误事件
        error_counts["error|错误|exception|异常"] = json_errors + json_timeouts
        error_counts["warning|警告|warning"] = json_warnings
        error_counts["critical|严重|critical"] = json_critical
        
        return error_counts
    
    def _analyze_system_health(self, log_content: str) -> Dict[str, Any]:
        """分析系统健康状态"""
        # 提取系统状态信息
        health_indicators = {
            "memory_usage": self._extract_memory_usage(log_content),
            "cpu_usage": self._extract_cpu_usage(log_content),
            "active_connections": self._extract_connections(log_content),
            "cache_hit_rate": self._extract_cache_hit_rate(log_content),
            "reasoning_engine_pool": self._extract_reasoning_engine_pool_stats(log_content)  # 🚀 新增：推理引擎实例池统计
        }
        
        return health_indicators
    
    def _extract_memory_usage(self, log_content: str) -> float:
        """提取内存使用率"""
        # 🚀 修复：优先从系统健康指标中提取内存使用率
        # 格式：系统健康指标: 内存使用率 X.X% (RSS: XXX.X MB)
        health_pattern = r"系统健康指标:\s*内存使用率\s*(\d+\.?\d*)%"
        health_matches = re.findall(health_pattern, log_content, re.IGNORECASE)
        
        if health_matches:
            try:
                # 返回最后一个记录的内存使用率
                return float(health_matches[-1])
            except ValueError:
                pass
        
        # 回退：从原始系统数据中计算内存使用率
        total_pattern = r"系统内存总量: (\d+) 字节"
        used_pattern = r"系统内存已用: (\d+) 字节"
        
        total_matches = re.findall(total_pattern, log_content, re.IGNORECASE)
        used_matches = re.findall(used_pattern, log_content, re.IGNORECASE)
        
        if total_matches and used_matches:
            try:
                total = float(total_matches[-1])
                used = float(used_matches[-1])
                return (used / total) * 100 if total > 0 else 0.0
            except ValueError:
                pass
        
        return 0.0
    
    def _extract_cpu_usage(self, log_content: str) -> float:
        """提取CPU使用率"""
        # 🚀 修复：优先从系统健康指标中提取CPU使用率
        # 格式：系统健康指标: CPU使用率 X.X%
        health_pattern = r"系统健康指标:\s*CPU使用率\s*(\d+\.?\d*)%"
        health_matches = re.findall(health_pattern, log_content, re.IGNORECASE)
        
        if health_matches:
            try:
                # 返回最后一个记录的CPU使用率
                return float(health_matches[-1])
            except ValueError:
                pass
        
        # 回退：从原始系统数据中计算CPU使用率
        load_pattern = r"系统负载: \((\d+\.?\d*), (\d+\.?\d*), (\d+\.?\d*)\)"
        cores_pattern = r"系统CPU核心数: (\d+)"
        
        load_matches = re.findall(load_pattern, log_content, re.IGNORECASE)
        cores_matches = re.findall(cores_pattern, log_content, re.IGNORECASE)
        
        if load_matches and cores_matches:
            try:
                load_1min = float(load_matches[-1][0])
                cores = float(cores_matches[-1])
                # 计算CPU使用率：1分钟负载 / CPU核心数 * 100%
                return (load_1min / cores) * 100 if cores > 0 else 0.0
            except ValueError:
                pass
        
        return 0.0
    
    def _extract_connections(self, log_content: str) -> int:
        """提取活跃连接数"""
        # 🚀 修复：优先从系统健康指标中提取活跃连接数
        # 格式：系统健康指标: 活跃连接数 X
        health_pattern = r"系统健康指标:\s*活跃连接数\s*(\d+)"
        health_matches = re.findall(health_pattern, log_content, re.IGNORECASE)
        
        if health_matches:
            try:
                # 返回最后一个记录的活跃连接数
                return int(health_matches[-1])
            except ValueError:
                pass
        
        # 回退：从原始系统数据中提取网络连接数
        connection_pattern = r"系统网络连接数: (\d+)"
        
        matches = re.findall(connection_pattern, log_content, re.IGNORECASE)
        if matches:
            try:
                return int(matches[-1])
            except ValueError:
                pass
        
        return 0
    
    def _extract_reasoning_engine_pool_stats(self, log_content: str) -> Dict[str, Any]:
        """🚀 新增：提取推理引擎实例池统计信息"""
        # 🚀 优化：支持新的日志格式（包含总活跃实例数和被丢弃实例数）
        # 格式：系统健康指标: 推理引擎实例池 - 池中实例数=X, 使用中实例数=Y, 总创建数=Z, 最大池大小=W, 总活跃实例数=A, 被丢弃实例数=B, 利用率=P%
        pool_pattern_new = r"系统健康指标:\s*推理引擎实例池\s*-\s*池中实例数=(\d+),\s*使用中实例数=(\d+),\s*总创建数=(\d+),\s*最大池大小=(\d+),\s*总活跃实例数=(\d+),\s*被丢弃实例数=(\d+),\s*利用率=(\d+\.?\d*)%"
        matches_new = re.findall(pool_pattern_new, log_content, re.IGNORECASE)
        
        if matches_new:
            # 返回最后一个记录的统计信息（新格式）
            try:
                last_match = matches_new[-1]
                return {
                    "pool_size": int(last_match[0]),
                    "in_use_count": int(last_match[1]),
                    "created_count": int(last_match[2]),
                    "max_size": int(last_match[3]),
                    "total_active_instances": int(last_match[4]),  # 🚀 新增
                    "discarded_count": int(last_match[5]),  # 🚀 新增
                    "utilization_rate": float(last_match[6]) / 100.0
                }
            except (ValueError, IndexError):
                pass
        
        # 🚀 兼容旧格式（如果没有新格式，尝试旧格式）
        pool_pattern_old = r"系统健康指标:\s*推理引擎实例池\s*-\s*池中实例数=(\d+),\s*使用中实例数=(\d+),\s*总创建数=(\d+),\s*最大池大小=(\d+),\s*利用率=(\d+\.?\d*)%"
        matches_old = re.findall(pool_pattern_old, log_content, re.IGNORECASE)
        
        if matches_old:
            # 返回最后一个记录的统计信息（旧格式）
            try:
                last_match = matches_old[-1]
                pool_size = int(last_match[0])
                in_use_count = int(last_match[1])
                return {
                    "pool_size": pool_size,
                    "in_use_count": in_use_count,
                    "created_count": int(last_match[2]),
                    "max_size": int(last_match[3]),
                    "total_active_instances": pool_size + in_use_count,  # 🚀 计算总活跃实例数
                    "discarded_count": 0,  # 🚀 旧格式没有此信息，默认为0
                    "utilization_rate": float(last_match[4]) / 100.0
                }
            except (ValueError, IndexError):
                pass
        
        # 如果没有找到，返回默认值
        return {
            "pool_size": 0,
            "in_use_count": 0,
            "created_count": 0,
            "max_size": 0,
            "utilization_rate": 0.0
        }
    
    def _extract_cache_hit_rate(self, log_content: str) -> float:
        """提取缓存命中率"""
        # 🚀 修复：从日志中提取缓存命中率
        # 匹配模式：缓存命中率: X.X% 或 系统健康指标: 缓存命中率 X.X%
        cache_hit_patterns = [
            r"缓存命中率:\s*(\d+\.?\d*)%",
            r"系统健康指标:\s*缓存命中率\s*(\d+\.?\d*)%"
        ]
        
        hit_rates = []
        for pattern in cache_hit_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                try:
                    hit_rate = float(match)
                    hit_rates.append(hit_rate)
                except ValueError:
                    continue
        
        # 返回最新的缓存命中率（如果有多个，取最后一个）
        if hit_rates:
            return hit_rates[-1] / 100.0  # 转换为0-1之间的值
        
        # 如果没有找到，尝试从缓存命中/未命中统计计算
        cache_hit_pattern = r"缓存命中率:.*?命中:\s*(\d+).*?未命中:\s*(\d+)"
        match = re.search(cache_hit_pattern, log_content, re.IGNORECASE)
        if match:
            try:
                hits = int(match.group(1))
                misses = int(match.group(2))
                total = hits + misses
                if total > 0:
                    return hits / total
            except (ValueError, IndexError):
                pass
        
        return 0.0
    
    def _extract_expected_answers(self, log_content: str) -> List[str]:
        """从日志中提取期望答案"""
        expected_pattern = r"期望答案: (.+?)(?:\n|$)"
        matches = re.findall(expected_pattern, log_content, re.IGNORECASE)
        return [match.strip() for match in matches]
    
    def _extract_actual_answers(self, log_content: str) -> List[str]:
        """从日志中提取实际答案"""
        # 优先使用新的标准化答案格式
        system_answer_pattern = r"系统答案: ([^\n]+)"
        system_answers = re.findall(system_answer_pattern, log_content, re.IGNORECASE)
        
        if system_answers:
            return [answer.strip() for answer in system_answers]
        
        # 如果没有找到标准化答案，回退到原有方法
        answer_patterns = [
            r"答案: ([^\n]+)",  # 从"答案: xxx"中提取
            r"结果: ([^\n]+)",  # 从简单结果中提取
            r"研究完成.*?置信度.*?结果: (.+?)(?:\n|$)",  # 原有模式
            r"业务处理完成.*?结果: (.+?)(?:\n|$)"  # 原有模式
        ]
        
        answers = []
        for pattern in answer_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned_match = match.strip()
                # 过滤掉太长的结果和无效答案
                if (len(cleaned_match) < 200 and 
                    not cleaned_match.startswith('🚀') and 
                    not cleaned_match.startswith('[') and
                    cleaned_match not in answers):  # 避免重复
                    answers.append(cleaned_match)
        
        # 如果没有找到短答案，尝试从复杂结果中提取
        if not answers:
            complex_pattern = r"核心系统处理完成，结果: (.+?)(?:\n|$)"
            complex_matches = re.findall(complex_pattern, log_content, re.IGNORECASE | re.DOTALL)
            for match in complex_matches:
                # 尝试从复杂结果中提取答案行
                answer_match = re.search(r"答案: ([^\n]+)", match)
                if answer_match:
                    answer = answer_match.group(1).strip()
                    if answer not in answers:  # 避免重复
                        answers.append(answer)
        
        return answers
    
    def _calculate_real_accuracy(self, expected_answers: List[str], actual_answers: List[str]) -> Dict[str, Any]:
        """计算真正的准确率"""
        if not expected_answers or not actual_answers:
            return {
                "accuracy": 0.0,
                "total_comparisons": 0,
                "correct_count": 0,
                "exact_matches": 0,
                "similarity_matches": 0
            }
        
        # 比较答案
        exact_matches = 0
        similarity_matches = 0
        total_comparisons = min(len(expected_answers), len(actual_answers))
        similarity_threshold = 0.8  # 相似度阈值
        
        for i in range(total_comparisons):
            expected = expected_answers[i].lower().strip()
            actual = actual_answers[i].lower().strip()
            
            if expected == actual:
                exact_matches += 1
            else:
                # 计算相似度
                similarity = self._calculate_similarity(expected, actual)
                if similarity > similarity_threshold:
                    similarity_matches += similarity
        
        correct_count = exact_matches + similarity_matches
        accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "total_comparisons": total_comparisons,
            "correct_count": correct_count,
            "exact_matches": exact_matches,
            "similarity_matches": similarity_matches
        }
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度 - Jaccard相似度"""
        if not s1 or not s2:
            return 0.0
        
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_sample_count(self, log_content: str) -> int:
        """从日志中提取样本数量"""
        import re
        
        # 匹配 "样本数量: X" 的模式（按优先级排序）
        sample_patterns = [
            r"FRAMES.*开始执行样本.*样本数量:\s*(\d+)",  # 优先匹配FRAMES执行时的样本数量
            r"开始FRAMES数据集评测.*样本数量:\s*(\d+)",
            r"成功加载\s*(\d+)\s*个FRAMES样本",
            r"样本数量:\s*(\d+)",
            r"总样本数:\s*(\d+)",
        ]
        
        all_matches = []
        for pattern in sample_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            if matches:
                try:
                    # 收集所有匹配的样本数
                    all_matches.extend([int(m) for m in matches if isinstance(m, str) and m.isdigit()])
                except (ValueError, TypeError):
                    # 如果匹配结果是元组，取第一个数字
                    for match in matches:
                        if isinstance(match, tuple):
                            for item in match:
                                if isinstance(item, str) and item.isdigit():
                                    all_matches.append(int(item))
                        elif isinstance(match, str) and match.isdigit():
                            all_matches.append(int(match))
        
        if all_matches:
            # 返回最常见的样本数量（如果有多个不同的值，返回出现次数最多的）
            from collections import Counter
            counter = Counter(all_matches)
            # 优先返回最大的值（通常是实际执行的样本数）
            return max(all_matches)
        
        # 如果无法从日志中提取，尝试从期望答案数量推断
        expected_answers = self._extract_expected_answers(log_content)
        if expected_answers:
            # 如果期望答案数量合理（1-1000之间），使用它作为样本数量
            answer_count = len(expected_answers)
            if 1 <= answer_count <= 1000:
                self.logger.info(f"无法从日志中提取样本数量，从期望答案数量推断: {answer_count}")
                return answer_count
        
        return 0
    
    # 1. FRAMES评测基准指标
    def _analyze_frames_accuracy(self, log_content: str) -> Dict[str, Any]:
        """分析FRAMES基准准确率 - 真正的答案比较"""
        # 1. 提取期望答案
        expected_answers = self._extract_expected_answers(log_content)
        
        # 2. 提取实际答案
        actual_answers = self._extract_actual_answers(log_content)
        
        # 3. 计算真正的准确率
        real_accuracy_result = self._calculate_real_accuracy(expected_answers, actual_answers)
        
        # 4. 提取置信度（作为参考）
        confidence_patterns = [
            r"结果置信度: (\d+\.?\d*)",
            r"置信度: (\d+\.?\d*)",
            r"confidence: (\d+\.?\d*)"
        ]
        
        confidence_scores = []
        for pattern in confidence_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                try:
                    confidence_scores.append(float(match))
                except ValueError:
                    continue
        
        # 5. 提取向量搜索结果
        vector_similarity_pattern = r"相似度=(\d+\.?\d*)"
        vector_scores = []
        vector_matches = re.findall(vector_similarity_pattern, log_content, re.IGNORECASE)
        for match in vector_matches:
            try:
                vector_scores.append(float(match))
            except ValueError:
                continue
        
        # 计算向量搜索质量
        vector_quality = 0.0
        if vector_scores:
            vector_quality = sum(vector_scores) / len(vector_scores)
        
        return {
            # 真正的准确率指标
            "real_accuracy": real_accuracy_result["accuracy"],
            "total_comparisons": real_accuracy_result["total_comparisons"],
            "correct_count": real_accuracy_result["correct_count"],
            "exact_matches": real_accuracy_result["exact_matches"],
            "similarity_matches": real_accuracy_result["similarity_matches"],
            "expected_answers": expected_answers,
            "actual_answers": actual_answers,
            
            # 置信度指标（作为参考）
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
            "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
            "confidence_tests": len(confidence_scores),
            
            # 向量搜索质量
            "vector_search_quality": vector_quality,
            "vector_search_count": len(vector_scores),
            "average_similarity": vector_quality,
            
            # 兼容性（保持原有字段名）
            "average_accuracy": real_accuracy_result["accuracy"],
            "max_accuracy": real_accuracy_result["accuracy"],
            "min_accuracy": real_accuracy_result["accuracy"],
            "total_tests": real_accuracy_result["total_comparisons"]
        }
    
    def _analyze_reasoning_efficiency(self, log_content: str) -> Dict[str, Any]:
        """分析推理效率"""
        # 🚀 修复：优先使用样本级别的推理时间（避免重复匹配导致配对错误）
        times = []
        steps = []
        
        # 策略1: 优先使用"样本推理开始时间"和"样本推理结束时间"（更准确）
        sample_start_pattern = r"样本推理开始时间: (\d+\.?\d*)"
        sample_end_pattern = r"样本推理结束时间: (\d+\.?\d*)"
        
        sample_start_matches = re.findall(sample_start_pattern, log_content, re.IGNORECASE)
        sample_end_matches = re.findall(sample_end_pattern, log_content, re.IGNORECASE)
        
        # 如果找到了样本级别的时间戳，使用它们
        if sample_start_matches and sample_end_matches:
            min_pairs = min(len(sample_start_matches), len(sample_end_matches))
            for i in range(min_pairs):
                try:
                    start_time = float(sample_start_matches[i])
                    end_time = float(sample_end_matches[i])
                    reasoning_time = end_time - start_time
                    if 0 < reasoning_time < 1000:  # 合理的推理时间范围
                        times.append(reasoning_time)
                except (ValueError, IndexError):
                    continue
        
        # 策略2: 如果样本级别的时间戳不足，使用普通的"推理开始时间"和"推理结束时间"
        # 但使用负向前瞻确保不匹配"样本推理开始时间"（避免重复）
        if len(times) < 5:  # 如果样本级别的配对不足，使用备用方案
            start_pattern = r"(?<!样本)推理开始时间: (\d+\.?\d*)"
            end_pattern = r"(?<!样本)推理结束时间: (\d+\.?\d*)"
            
            start_matches = re.findall(start_pattern, log_content, re.IGNORECASE)
            end_matches = re.findall(end_pattern, log_content, re.IGNORECASE)
            
            min_pairs = min(len(start_matches), len(end_matches))
            for i in range(min_pairs):
                try:
                    start_time = float(start_matches[i])
                    end_time = float(end_matches[i])
                    reasoning_time = end_time - start_time
                    if 0 < reasoning_time < 1000:
                        times.append(reasoning_time)
                except (ValueError, IndexError):
                    continue
        
        # 提取推理步骤数
        steps_pattern = r"推理步骤数: (\d+)"
        steps_matches = re.findall(steps_pattern, log_content, re.IGNORECASE)
        for match in steps_matches:
            try:
                steps.append(int(match))
            except ValueError:
                continue
        
        # 策略3: 如果通过时间戳计算的times为空，尝试从其他日志中提取
        if not times:
            # 从JSON或兼容行中提取processing_time（使用正则表达式直接提取）
            json_pattern = r'"processing_time": (\d+\.?\d*)'
            compat_patterns = [r"执行时间: (\d+\.?\d*)", r"响应时间: (\d+\.?\d*)"]
            
            for match in re.findall(json_pattern, log_content, re.IGNORECASE):
                try:
                    times.append(float(match))
                except ValueError:
                    continue
            
            for pattern in compat_patterns:
                for match in re.findall(pattern, log_content, re.IGNORECASE):
                    try:
                        times.append(float(match))
                    except ValueError:
                        continue
        
        # 🚀 修复：使用正确的推理效率分数计算（基于时间和步骤）
        time_stats = self._calculate_statistics(times) if times else {"average": 0.0, "count": 0}
        step_stats = self._calculate_statistics([float(s) for s in steps]) if steps else {"average": 0.0, "count": 0}
        efficiency_score = self._calculate_efficiency_score(time_stats, step_stats)
        
        return {
            "average_time": time_stats.get("average", 0.0),
            "average_steps": int(step_stats.get("average", 0)),
            "time_stats": time_stats,
            "step_stats": step_stats,
            "efficiency_score": efficiency_score
        }
    
    def _calculate_efficiency_score(self, time_stats: Dict[str, Any], step_stats: Dict[str, Any]) -> float:
        """🚀 优化：计算效率分数（使用更灵活的评分曲线）"""
        if time_stats.get("count", 0) == 0 or step_stats.get("count", 0) == 0:
            return 0.0
        
        avg_time = time_stats.get("average", 0.0)
        avg_steps = step_stats.get("average", 0.0)
        
        # 🚀 优化：使用更灵活的评分曲线，而不是简单的线性递减
        # 时间分数：分段评分，更公平地评估不同时间范围
        if avg_time <= 30:
            # 30秒以内：满分
            time_score = 1.0
        elif avg_time <= 60:
            # 30-60秒：线性递减，从1.0到0.8
            time_score = 1.0 - (avg_time - 30) / 150.0  # 30秒时1.0，60秒时0.8
        elif avg_time <= 120:
            # 60-120秒：线性递减，从0.8到0.5
            time_score = 0.8 - (avg_time - 60) / 200.0  # 60秒时0.8，120秒时0.5
        elif avg_time <= 180:
            # 120-180秒：线性递减，从0.5到0.3
            time_score = 0.5 - (avg_time - 120) / 300.0  # 120秒时0.5，180秒时0.3
        else:
            # 超过180秒：继续递减，但不会到0
            time_score = max(0.1, 0.3 - (avg_time - 180) / 600.0)  # 180秒时0.3，240秒时0.2，300秒时0.1
        
        # 步骤分数：保持原有逻辑（100步为满分）
        step_score = max(0, 1 - avg_steps / 100.0)
        
        # 🚀 优化：调整权重，降低时间权重，提高步骤权重（因为步骤数更能反映推理质量）
        # 从原来的 时间60% + 步骤40% 改为 时间50% + 步骤50%
        efficiency_score = (time_score * 0.5 + step_score * 0.5)
        
        return efficiency_score
    
    def _analyze_method_innovation(self, log_content: str) -> Dict[str, Any]:
        """分析方法创新性"""
        # 从原始日志数据中提取新颖度
        novelty_patterns = [
            r"方法新颖度: (\d+\.?\d*)",
            r"新颖度: (\d+\.?\d*)",
            r"novelty: (\d+\.?\d*)"
        ]
        
        novelty_scores = []
        for pattern in novelty_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                try:
                    novelty_scores.append(float(match))
                except ValueError:
                    continue
        
        # 计算创新性指标
        innovation_count = len(novelty_scores)
        average_novelty = sum(novelty_scores) / len(novelty_scores) if novelty_scores else 0.0
        
        return {
            "innovation_count": innovation_count,
            "average_novelty": average_novelty,
            "innovation_score": min(average_novelty, 1.0)  # 归一化到0-1
        }
    
    # 2. 系统智能化程度
    def _analyze_intelligence_level(self, log_content: str) -> Dict[str, Any]:
        """分析系统智能化程度 - 增强版"""
        intelligence_patterns = [
            r"智能分析|Intelligent analysis|AI分析|AI analysis",
            r"机器学习|Machine learning|ML|ML算法",
            r"深度学习|Deep learning|神经网络|Neural network",
            r"强化学习|Reinforcement learning|RL|RL算法",
            r"自适应|Adaptive|自学习|Self-learning",
            r"基于深度研究|深度分析|智能推理|intelligent reasoning",
            r"分析要点|推理过程|reasoning process|analysis points",
            r"置信度|confidence|智能评分|intelligent scoring",
            r"知识检索|knowledge retrieval|智能检索|intelligent search",
            r"答案生成|answer generation|智能生成|intelligent generation",
            r"统一智能|unified intelligent|智能中心|intelligent center",
            r"AI算法|AI algorithm|智能算法|intelligent algorithm",
            r"大脑决策|brain decision|智能决策|intelligent decision",
            r"证据积累|evidence accumulation|智能积累|intelligent accumulation"
        ]
        
        intelligence_indicators = {}
        for pattern in intelligence_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            intelligence_indicators[pattern.split('|')[0]] = len(matches)
        
        # 计算各种智能活动
        ai_algorithm_score = self._calculate_ai_algorithm_score(log_content)
        learning_score = self._calculate_learning_score(log_content)
        reasoning_score = self._calculate_reasoning_score(log_content)
        adaptive_score = self._calculate_adaptive_score(log_content)
        
        total_indicators = sum(intelligence_indicators.values())
        overall_score = (ai_algorithm_score + learning_score + reasoning_score + adaptive_score) / 4.0
        
        return {
            "intelligence_indicators": intelligence_indicators,
            "total_indicators": total_indicators,
            "ai_algorithm_score": ai_algorithm_score,
            "learning_score": learning_score,
            "reasoning_score": reasoning_score,
            "adaptive_score": adaptive_score,
            "overall_intelligence_score": overall_score,
            "intelligence_score": min(overall_score, 1.0)  # 归一化到0-1
        }
    
    def _calculate_ai_algorithm_score(self, log_content: str) -> float:
        """
        计算AI算法分数（🚀 使用配置文件，保持评测系统独立性）
        
        评测系统必须完全独立于核心系统，只从配置文件读取关键字配置
        """
        # 🚀 评测系统独立配置：从配置文件或环境变量读取，不依赖核心系统
        ai_keywords = self._load_ai_keywords_config()
        
        # 智能匹配：使用灵活的字符串匹配
        total_matches = 0
        for keyword in ai_keywords:
            # 对于每个关键字，检查是否在日志中出现（支持部分匹配）
            keyword_lower = keyword.lower()
            if keyword_lower in log_content.lower():
                # 计算出现次数
                count = log_content.lower().count(keyword_lower)
                total_matches += count
        
        # 计算分数（阈值：20个匹配 = 1.0分）
        return min(total_matches / 20.0, 1.0)
    
    def _load_ai_keywords_config(self) -> List[str]:
        """
        加载AI算法关键字配置（🚀 评测系统独立配置，不依赖核心系统）
        
        优先级：
        1. 环境变量 EVALUATION_AI_KEYWORDS（JSON格式）
        2. 配置文件 evaluation_config.json
        3. 默认配置（包含所有已知关键字）
        """
        # 1. 尝试从环境变量读取
        import os
        env_keywords = os.getenv("EVALUATION_AI_KEYWORDS")
        if env_keywords:
            try:
                import json
                keywords = json.loads(env_keywords)
                if isinstance(keywords, list):
                    return keywords
            except Exception:
                pass
        
        # 2. 尝试从配置文件读取
        config_file = Path(__file__).parent / "evaluation_config.json"
        if config_file.exists():
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "ai_algorithm_keywords" in config:
                        keywords = config["ai_algorithm_keywords"]
                        if isinstance(keywords, list):
                            return keywords
            except Exception as e:
                self.logger.warning(f"无法从配置文件读取AI关键字配置: {e}")
        
        # 3. 使用默认配置（包含所有已知关键字，包括新增的）
        return [
            "AI算法", "AI algorithm", "智能算法", "intelligent algorithm",
            "统一智能", "unified intelligent", "智能中心", "intelligent center",
            "大脑决策", "brain decision", "智能决策", "intelligent decision",
            "智能分析", "intelligent analysis", "AI分析", "AI analysis",
            "基于深度研究", "深度分析", "智能推理", "intelligent reasoning",
            # 🚀 新增关键字（从核心系统日志中发现，但配置在评测系统中）
            "深度学习模型推理", "机器学习算法分析", "神经网络推理",
            "统一智能中心处理", "智能决策系统运行中", "AI算法执行中"
        ]
    
    def _calculate_learning_score(self, log_content: str) -> float:
        """计算学习能力分数"""
        learning_patterns = [
            r"机器学习|Machine learning|ML|ML算法",
            r"深度学习|Deep learning|神经网络|Neural network",
            r"强化学习|Reinforcement learning|RL|RL算法",
            r"自学习|Self-learning|自适应|Adaptive",
            r"学习活动|learning activity|学习分数|learning score"
        ]
        
        total_matches = 0
        for pattern in learning_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            total_matches += len(matches)
        
        return min(total_matches / 5.0, 1.0)
    
    def _calculate_reasoning_score(self, log_content: str) -> float:
        """计算推理能力分数"""
        reasoning_patterns = [
            r"推理过程|reasoning process|智能推理|intelligent reasoning",
            r"分析要点|analysis points|深度分析|deep analysis",
            r"基于深度研究|深度研究|intelligent research",
            r"证据积累|evidence accumulation|智能积累|intelligent accumulation"
        ]
        
        total_matches = 0
        for pattern in reasoning_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            total_matches += len(matches)
        
        return min(total_matches / 50.0, 1.0)  # 大幅降低阈值
    
    def _calculate_adaptive_score(self, log_content: str) -> float:
        """计算适应能力分数"""
        adaptive_patterns = [
            r"自适应|Adaptive|自学习|Self-learning",
            r"智能适应|intelligent adaptation|动态调整|dynamic adjustment",
            r"智能优化|intelligent optimization|智能调整|intelligent adjustment"
        ]
        
        total_matches = 0
        for pattern in adaptive_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            total_matches += len(matches)
        
        return min(total_matches / 3.0, 1.0)
    
    # 3. 智能体和模块配合程度
    def _analyze_agent_coordination(self, log_content: str) -> Dict[str, Any]:
        """分析智能体协调程度"""
        coordination_patterns = [
            r"智能体协作|Agent collaboration|Agent coordination",
            r"多智能体|Multi-agent|Agent interaction",
            r"协调|Coordination|协作|Collaboration",
            r"任务分配|Task allocation|任务协调|Task coordination"
        ]
        
        coordination_count = 0
        for pattern in coordination_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            coordination_count += len(matches)
        
        return {
            "coordination_count": coordination_count,
            "coordination_score": min(coordination_count / 15.0, 1.0)
        }
    
    def _analyze_module_integration(self, log_content: str) -> Dict[str, Any]:
        """分析模块集成程度"""
        integration_patterns = [
            r"模块集成|Module integration|模块协作|Module collaboration",
            r"统一接口|Unified interface|接口调用|Interface call",
            r"模块通信|Module communication|模块交互|Module interaction"
        ]
        
        integration_count = 0
        for pattern in integration_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            integration_count += len(matches)
        
        return {
            "integration_count": integration_count,
            "integration_score": min(integration_count / 10.0, 1.0)
        }
    
    # 4. 系统自我学习程度
    def _analyze_ml_learning(self, log_content: str) -> Dict[str, Any]:
        """分析机器学习学习程度"""
        # 🚀 修复：优先匹配"ML学习活动"日志（更准确）
        ml_activity_pattern = r"🤖\s*ML学习活动|ML学习活动"
        ml_activity_matches = re.findall(ml_activity_pattern, log_content, re.IGNORECASE)
        ml_count_from_log = len(ml_activity_matches)
        
        # 如果从日志中找到了ML学习活动，直接使用
        if ml_count_from_log > 0:
            # 🚀 优化：基于样本数量归一化（每个样本应该有3-5个ML学习活动）
            sample_count = self._extract_sample_count(log_content)
            if sample_count > 0:
                # 每个样本期望3个ML学习活动，满分
                expected_per_sample = 3.0
                ml_score = min(ml_count_from_log / (sample_count * expected_per_sample), 1.0)
            else:
                # 如果没有样本信息，使用固定阈值（20个活动=满分）
                ml_score = min(ml_count_from_log / 20.0, 1.0)
            
            return {
                "ml_activities": ml_count_from_log,
                "ml_score": ml_score
            }
        
        # 回退：使用关键词匹配
        ml_patterns = [
            r"模型训练|Model training|训练|Training",
            r"参数更新|Parameter update|权重更新|Weight update",
            r"损失函数|Loss function|梯度下降|Gradient descent",
            r"学习率|Learning rate|优化器|Optimizer"
        ]
        
        ml_count = 0
        for pattern in ml_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            ml_count += len(matches)
        
        # 🚀 优化：基于样本数量归一化
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            expected_per_sample = 3.0
            ml_score = min(ml_count / (sample_count * expected_per_sample), 1.0)
        else:
            ml_score = min(ml_count / 20.0, 1.0)
        
        return {
            "ml_activities": ml_count,
            "ml_score": ml_score
        }
    
    def _analyze_rl_learning(self, log_content: str) -> Dict[str, Any]:
        """分析强化学习学习程度"""
        rl_patterns = [
            r"强化学习|Reinforcement learning|RL|Q-learning",
            r"奖励|Reward|惩罚|Penalty|奖励函数|Reward function",
            r"策略更新|Policy update|动作选择|Action selection",
            r"环境交互|Environment interaction|状态|State"
        ]
        
        rl_count = 0
        for pattern in rl_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            rl_count += len(matches)
        
        # 🚀 优化：基于样本数量归一化（每个样本期望1-2次RL活动）
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            # 每个样本期望1.5次RL活动，满分
            expected_per_sample = 1.5
            rl_score = min(rl_count / (sample_count * expected_per_sample), 1.0)
        else:
            # 如果没有样本信息，使用固定阈值（15次=满分）
            rl_score = min(rl_count / 15.0, 1.0)
        
        return {
            "rl_activities": rl_count,
            "rl_score": rl_score
        }
    
    def _analyze_self_learning(self, log_content: str) -> Dict[str, Any]:
        """分析自我学习程度"""
        # 🚀 修复：改进模式匹配，确保能匹配到emoji和中文
        self_learning_patterns = [
            r"🧠\s*自我学习活动",  # 🚀 修复：匹配emoji格式
            r"自我学习活动",  # 匹配中文
            r"自我学习|Self-learning|自主学习|Autonomous learning",
            r"经验积累|Experience accumulation|知识更新|Knowledge update",
            r"持续学习|Continuous learning|在线学习|Online learning",
            r"反馈学习|Feedback learning|适应性学习|Adaptive learning"
        ]
        
        self_learning_count = 0
        for pattern in self_learning_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            self_learning_count += len(matches)
        
        # 🚀 优化：基于样本数量归一化（每个样本期望1次自我学习活动）
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            # 每个样本期望1次自我学习活动，满分
            expected_per_sample = 1.0
            self_learning_score = min(self_learning_count / (sample_count * expected_per_sample), 1.0)
        else:
            # 如果没有样本信息，使用固定阈值（10次=满分）
            self_learning_score = min(self_learning_count / 10.0, 1.0)
        
        return {
            "self_learning_activities": self_learning_count,
            "self_learning_score": self_learning_score
        }
    
    # 6. 详实的研究报告
    def _analyze_research_report_quality(self, log_content: str) -> Dict[str, Any]:
        """分析研究报告质量"""
        report_patterns = [
            r"研究报告|Research report|详细报告|Detailed report",
            r"分析报告|Analysis report|评估报告|Evaluation report",
            r"结论|Conclusion|建议|Recommendation|总结|Summary"
        ]
        
        report_count = 0
        for pattern in report_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            report_count += len(matches)
        
        return {
            "report_count": report_count,
            "report_quality_score": min(report_count / 5.0, 1.0)
        }
    
    # 协同作用分析
    def _analyze_ml_rl_synergy(self, log_content: str) -> Dict[str, Any]:
        """分析ML和RL协同作用"""
        synergy_patterns = [
            r"ML-RL协同|ML-RL synergy|机器学习-强化学习|ML-RL integration",
            r"混合学习|Hybrid learning|协同学习|Synergistic learning",
            r"ML指导RL|ML guiding RL|RL优化ML|RL optimizing ML"
        ]
        
        synergy_count = 0
        for pattern in synergy_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            synergy_count += len(matches)
        
        # 🚀 优化：基于样本数量归一化（每个样本期望1次协同活动）
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            # 每个样本期望1次协同活动，满分
            expected_per_sample = 1.0
            synergy_score = min(synergy_count / (sample_count * expected_per_sample), 1.0)
        else:
            # 如果没有样本信息，使用固定阈值（8次=满分）
            synergy_score = min(synergy_count / 8.0, 1.0)
        
        return {
            "synergy_count": synergy_count,
            "synergy_score": synergy_score
        }
    
    def _analyze_prompt_context_synergy(self, log_content: str) -> Dict[str, Any]:
        """分析提示词和上下文协同作用"""
        # 🚀 修复：优先匹配"提示词-上下文协同"日志（更准确）
        synergy_pattern = r"提示词-上下文协同|Prompt-context synergy"
        synergy_matches = re.findall(synergy_pattern, log_content, re.IGNORECASE)
        synergy_count_from_log = len(synergy_matches)
        
        # 如果从日志中找到了协同活动，直接使用
        if synergy_count_from_log > 0:
            # 🚀 优化：基于样本数量归一化（每个样本应该有1个协同活动）
            sample_count = self._extract_sample_count(log_content)
            if sample_count > 0:
                # 每个样本期望1个协同活动，满分
                expected_per_sample = 1.0
                synergy_score = min(synergy_count_from_log / (sample_count * expected_per_sample), 1.0)
            else:
                # 如果没有样本信息，使用固定阈值（6次=满分）
                synergy_score = min(synergy_count_from_log / 6.0, 1.0)
            
            return {
                "prompt_context_synergy_count": synergy_count_from_log,
                "prompt_context_synergy_score": synergy_score
            }
        
        # 回退：使用关键词匹配
        prompt_context_patterns = [
            r"提示词-上下文|Prompt-context|提示工程|Prompt engineering",
            r"上下文增强|Context enhancement|动态提示|Dynamic prompt",
            r"上下文感知|Context-aware|智能提示|Intelligent prompt"
        ]
        
        synergy_count = 0
        for pattern in prompt_context_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            synergy_count += len(matches)
        
        # 🚀 优化：基于样本数量归一化
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            expected_per_sample = 1.0
            synergy_score = min(synergy_count / (sample_count * expected_per_sample), 1.0)
        else:
            synergy_score = min(synergy_count / 6.0, 1.0)
        
        return {
            "prompt_context_synergy_count": synergy_count,
            "prompt_context_synergy_score": synergy_score
        }
    
    # 复杂逻辑推理能力
    def _analyze_complex_reasoning(self, log_content: str) -> Dict[str, Any]:
        """分析复杂逻辑推理能力（🚀 优化：基于时间戳识别推理活动）"""
        # 🚀 优化：优先使用时间戳来识别推理活动（更准确）
        start_pattern = r"推理开始时间: (\d+\.?\d*)"
        end_pattern = r"推理结束时间: (\d+\.?\d*)"
        steps_pattern = r"推理步骤数: (\d+)"
        
        start_times = re.findall(start_pattern, log_content, re.IGNORECASE)
        end_times = re.findall(end_pattern, log_content, re.IGNORECASE)
        steps_matches = re.findall(steps_pattern, log_content, re.IGNORECASE)
        
        # 推理活动次数 = 匹配的开始时间数量（或结束时间数量，取较大值）
        reasoning_activities = max(len(start_times), len(end_times))
        
        # 计算平均推理步骤
        steps = []
        for match in steps_matches:
            try:
                steps.append(int(match))
            except ValueError:
                continue
        
        avg_steps = sum(steps) / len(steps) if steps else 0.0
        
        # 如果时间戳方式没有找到，回退到关键词匹配
        if reasoning_activities == 0:
            reasoning_patterns = [
                r"复杂推理|Complex reasoning|逻辑推理|Logical reasoning",
                r"多步推理|Multi-step reasoning|因果推理|Causal reasoning",
                r"归纳推理|Inductive reasoning|演绎推理|Deductive reasoning",
                r"推理链|Reasoning chain|推理图|Reasoning graph"
            ]
            
            reasoning_count = 0
            for pattern in reasoning_patterns:
                matches = re.findall(pattern, log_content, re.IGNORECASE)
                reasoning_count += len(matches)
            reasoning_activities = reasoning_count
        
        # 🚀 优化：计算推理能力分数（基于样本数量归一化）
        sample_count = self._extract_sample_count(log_content)
        if sample_count > 0:
            # 每个样本期望2次推理活动，满分
            expected_per_sample = 2.0
            reasoning_score = min(1.0, reasoning_activities / (sample_count * expected_per_sample))
        else:
            # 如果没有样本信息，使用固定阈值（10次活动=满分）
            reasoning_score = min(1.0, reasoning_activities / 10.0)
        
        return {
            "reasoning_activities": reasoning_activities,
            "average_steps": avg_steps,
            "reasoning_score": reasoning_score
        }
    
    # RANGEN查询处理流程
    def _analyze_query_processing_flow(self, log_content: str) -> Dict[str, Any]:
        """分析RANGEN查询处理流程（🚀 改进：区分查询级别和样本级别）"""
        # 1. 查询级别的流程（所有查询）
        flow_patterns = [
            r"查询接收|Query received|查询分析|Query analysis",
            r"查询处理|Query processing|查询执行|Query execution",
            r"结果生成|Result generation|结果返回|Result return",
            r"查询完成|Query completed|处理完成|Processing completed"
        ]
        
        flow_steps = {}
        for pattern in flow_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            flow_steps[pattern.split('|')[0]] = len(matches)
        
        # 2. 样本级别的流程（只统计包含样本ID的查询）
        sample_flow_patterns = [
            r"查询接收.*样本ID=(\d+)|查询接收.*样本ID=(\d+)",
            r"查询处理.*样本ID=(\d+)|查询处理.*样本ID=(\d+)",
            r"查询完成.*样本ID=(\d+)|查询完成.*样本ID=(\d+)"
        ]
        
        sample_flow_steps = {
            "查询接收": 0,
            "查询处理": 0,
            "查询完成": 0
        }
        
        # 提取所有样本ID
        sample_ids = set()
        for pattern in sample_flow_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            for match in matches:
                sample_id = match[0] if match[0] else match[1] if len(match) > 1 else None
                if sample_id:
                    sample_ids.add(sample_id)
                    if "查询接收" in pattern:
                        sample_flow_steps["查询接收"] += 1
                    elif "查询处理" in pattern:
                        sample_flow_steps["查询处理"] += 1
                    elif "查询完成" in pattern:
                        sample_flow_steps["查询完成"] += 1
        
        total_flow_activities = sum(flow_steps.values())
        sample_total_flow_activities = sum(sample_flow_steps.values())
        
        # 🚀 优化：基于样本数量归一化流程完整性分数
        sample_count = len(sample_ids) if len(sample_ids) > 0 else self._extract_sample_count(log_content)
        if sample_count > 0:
            # 每个样本期望10个流程活动（查询级别），满分
            expected_per_sample_query = 10.0
            flow_completeness_score = min(total_flow_activities / (sample_count * expected_per_sample_query), 1.0)
            
            # 每个样本期望3个流程活动（样本级别），满分
            expected_per_sample_sample = 3.0
            sample_flow_completeness_score = min(sample_total_flow_activities / (sample_count * expected_per_sample_sample), 1.0) if len(sample_ids) > 0 else 0.0
        else:
            # 如果没有样本信息，使用固定阈值
            flow_completeness_score = min(total_flow_activities / 20.0, 1.0)
            sample_flow_completeness_score = min(sample_total_flow_activities / 20.0, 1.0) if len(sample_ids) > 0 else 0.0
        
        return {
            "flow_steps": flow_steps,  # 查询级别
            "sample_flow_steps": sample_flow_steps,  # 样本级别
            "total_flow_activities": total_flow_activities,
            "sample_total_flow_activities": sample_total_flow_activities,
            "unique_sample_ids": len(sample_ids),  # 唯一样本ID数量
            "flow_completeness_score": flow_completeness_score,
            "sample_flow_completeness_score": sample_flow_completeness_score
        }
    
    def generate_report(self) -> str:
        """生成评测报告"""
        if not self.evaluation_results:
            return "没有评测结果可生成报告"
        
        report = []
        report.append("# 基于日志的评测报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"日志文件: {self.evaluation_results.get('log_file', 'N/A')}")
        report.append("")
        
        # 基本统计
        report.append("## 基本统计")
        report.append(f"- 文件大小: {self.evaluation_results.get('file_size', 0)} 字节")
        report.append(f"- 总行数: {self.evaluation_results.get('total_lines', 0)}")
        report.append(f"- 样本数量: {self.evaluation_results.get('sample_count', 0)}")
        report.append(f"- 查询数量: {self.evaluation_results.get('queries_analyzed', 0)}")
        
        # 🚀 改进：明确区分查询成功率和样本成功率
        success_rate_analysis = self.evaluation_results.get('success_rate_analysis', {})
        if isinstance(success_rate_analysis, dict):
            report.append(f"- 查询成功率: {success_rate_analysis.get('query_success_rate', 0.0):.2%} (基于{success_rate_analysis.get('query_total', 0)}个查询)")
            report.append(f"- 样本成功率: {success_rate_analysis.get('sample_success_rate', 0.0):.2%} (基于{success_rate_analysis.get('sample_total', 0)}个样本，与准确率统一基准)")
            report.append(f"- 成功率: {success_rate_analysis.get('success_rate', 0.0):.2%} (兼容性字段，使用样本成功率)")
        else:
            # 兼容性：如果success_rate_analysis不是字典，使用原有方式
            report.append(f"- 成功率: {self.evaluation_results.get('success_rate', 0.0):.2%}")
        report.append("")
        
        # 1. FRAMES评测基准指标
        frames = self.evaluation_results.get('frames_accuracy', {})
        report.append("## 1. FRAMES评测基准指标")
        report.append(f"- 平均准确率: {frames.get('average_accuracy', 0.0):.2%}")
        report.append(f"- 最高准确率: {frames.get('max_accuracy', 0.0):.2%}")
        report.append(f"- 最低准确率: {frames.get('min_accuracy', 0.0):.2%}")
        report.append(f"- 测试次数: {frames.get('total_tests', 0)}")
        
        # 向量搜索质量
        if 'vector_search_quality' in frames:
            report.append(f"- 向量搜索质量: {frames.get('vector_search_quality', 0.0):.3f}")
            report.append(f"- 向量搜索次数: {frames.get('vector_search_count', 0)}")
            report.append(f"- 平均相似度: {frames.get('average_similarity', 0.0):.3f}")
        
        reasoning = self.evaluation_results.get('reasoning_efficiency', {})
        # 🚀 优化：从step_stats中获取average（如果average_steps不存在）
        average_steps = reasoning.get('average_steps', 0)
        if average_steps == 0:
            # 尝试从step_stats中获取
            step_stats = reasoning.get('step_stats', {})
            average_steps = step_stats.get('average', 0)
        
        # 🚀 修复：兼容两种数据结构（average_time 或 time_stats.average）
        average_time = reasoning.get('average_time', 0.0)
        if average_time == 0.0:
            # 尝试从time_stats中获取
            time_stats = reasoning.get('time_stats', {})
            average_time = time_stats.get('average', 0.0)
        
        report.append(f"- 平均推理时间: {average_time:.2f} 秒")
        report.append(f"- 平均推理步骤: {average_steps}")
        report.append(f"- 推理效率分数: {reasoning.get('efficiency_score', 0.0):.2f}")
        
        innovation = self.evaluation_results.get('method_innovation', {})
        report.append(f"- 创新方法数量: {innovation.get('innovation_count', 0)}")
        report.append(f"- 创新性分数: {innovation.get('innovation_score', 0.0):.2f}")
        report.append("")
        
        # 2. 系统智能化程度
        intelligence_analysis = self.evaluation_results.get('intelligence_analysis', {})
        # 🚀 修复：兼容两种数据结构（intelligence_score和直接的intelligence_analysis字段）
        if 'intelligence_score' in intelligence_analysis:
            intelligence_score = intelligence_analysis.get('intelligence_score', {})
        else:
            # 如果intelligence_score不存在，尝试从intelligence_analysis直接获取
            intelligence_score = intelligence_analysis
        
        # 🚀 修复：优先使用ai_algorithm_score（comprehensive_evaluation计算的，更准确），如果没有则使用ai_score（intelligence_analyzer计算的）
        ai_algorithm_score = intelligence_score.get('ai_algorithm_score') or intelligence_score.get('ai_score', 0.0)
        
        report.append("## 2. 系统智能化程度")
        report.append(f"- 整体智能分数: {intelligence_score.get('overall_intelligence_score', 0.0):.2f}")
        report.append(f"- AI算法分数: {ai_algorithm_score:.2f}")
        report.append(f"- 学习能力分数: {intelligence_score.get('learning_score', 0.0):.2f}")
        report.append(f"- 推理能力分数: {intelligence_score.get('reasoning_score', 0.0):.2f}")
        report.append(f"- 适应能力分数: {intelligence_score.get('adaptation_score', 0.0):.2f}")
        report.append("")
        
        # 3. 智能体和模块配合程度
        quality_analysis = self.evaluation_results.get('quality_analysis', {})
        maintainability = quality_analysis.get('maintainability', {})
        report.append("## 3. 智能体和模块配合程度")
        report.append(f"- 可维护性分数: {maintainability.get('maintainability_score', 0.0):.2f}")
        report.append(f"- 维护指标数: {maintainability.get('maintenance_indicators', 0)}")
        report.append(f"- 模块化指标数: {maintainability.get('modularity_indicators', 0)}")
        report.append(f"- 文档指标数: {maintainability.get('documentation_indicators', 0)}")
        report.append("")
        
        # 4. 系统自我学习程度
        ml = self.evaluation_results.get('ml_learning', {})
        rl = self.evaluation_results.get('rl_learning', {})
        self_learning = self.evaluation_results.get('self_learning', {})
        report.append("## 4. 系统自我学习程度")
        report.append(f"- ML学习活动: {ml.get('ml_activities', 0)}")
        report.append(f"- ML学习分数: {ml.get('ml_score', 0.0):.2f}")
        report.append(f"- RL学习活动: {rl.get('rl_activities', 0)}")
        report.append(f"- RL学习分数: {rl.get('rl_score', 0.0):.2f}")
        report.append(f"- 自我学习活动: {self_learning.get('self_learning_activities', 0)}")
        report.append(f"- 自我学习分数: {self_learning.get('self_learning_score', 0.0):.2f}")
        report.append("")
        
        # 5. 系统性能
        perf_analysis = self.evaluation_results.get('performance_analysis', {})
        response_time = perf_analysis.get('response_time', {})
        time_stats = response_time.get('time_stats', {})
        
        report.append("## 5. 系统性能")
        report.append(f"- 平均处理时间: {time_stats.get('average', 0.0):.2f} 秒")
        report.append(f"- 最大处理时间: {time_stats.get('max', 0.0):.2f} 秒")
        report.append(f"- 最小处理时间: {time_stats.get('min', 0.0):.2f} 秒")
        report.append(f"- 总操作数: {time_stats.get('count', 0)}")
        
        # 🚀 修复：优先使用system_health（从日志提取），回退到system_health_analysis（当前系统状态）
        system_health = self.evaluation_results.get('system_health', {})
        system_health_analysis = self.evaluation_results.get('system_health_analysis', {})
        
        # 优先使用从日志提取的系统健康指标
        memory_usage = system_health.get('memory_usage', 0.0)
        cpu_usage = system_health.get('cpu_usage', 0.0)
        active_connections = system_health.get('active_connections', 0)
        cache_hit_rate = system_health.get('cache_hit_rate', 0.0)
        
        # 如果从日志提取的值为0，尝试从system_health_analysis获取
        if memory_usage == 0.0:
            resource_usage = system_health_analysis.get('resource_usage', {})
            memory = resource_usage.get('memory', {})
            memory_usage = memory.get('current_usage', 0.0)
        
        if cpu_usage == 0.0:
            resource_usage = system_health_analysis.get('resource_usage', {})
            cpu = resource_usage.get('cpu', {})
            cpu_usage = cpu.get('current_usage', 0.0)
        
        report.append(f"- 内存使用率: {memory_usage:.1f}%")
        report.append(f"- CPU使用率: {cpu_usage:.1f}%")
        report.append(f"- 活跃连接数: {active_connections}")
        report.append(f"- 缓存命中率: {cache_hit_rate:.1f}%")
        
        # 🚀 新增：显示推理引擎实例池统计信息
        reasoning_engine_pool = system_health.get('reasoning_engine_pool', {})
        if reasoning_engine_pool:
            pool_size = reasoning_engine_pool.get('pool_size', 0)
            in_use_count = reasoning_engine_pool.get('in_use_count', 0)
            created_count = reasoning_engine_pool.get('created_count', 0)
            max_size = reasoning_engine_pool.get('max_size', 0)
            utilization_rate = reasoning_engine_pool.get('utilization_rate', 0.0)
            
            report.append("")
            report.append("### 推理引擎实例池统计")
            report.append(f"- 池中实例数: {pool_size}")
            report.append(f"- 使用中实例数: {in_use_count}")
            report.append(f"- 总创建实例数: {created_count}")
            report.append(f"- 最大池大小: {max_size}")
            total_active = reasoning_engine_pool.get('total_active_instances', pool_size + in_use_count)  # 🚀 新增
            discarded_count = reasoning_engine_pool.get('discarded_count', 0)  # 🚀 新增
            report.append(f"- 总活跃实例数: {total_active}")  # 🚀 新增
            report.append(f"- 被丢弃实例数: {discarded_count}")  # 🚀 新增
            report.append(f"- 实例池利用率: {utilization_rate:.2%}")
            report.append(f"- 模型实例活跃数: {total_active}")  # 🚀 新增：模型实例活跃数（池中+使用中）
        
        report.append("")
        
        # 6. 详实的研究报告
        report_quality = self.evaluation_results.get('research_report_quality', {})
        report.append("## 6. 详实的研究报告")
        report.append(f"- 报告数量: {report_quality.get('report_count', 0)}")
        report.append(f"- 报告质量分数: {report_quality.get('report_quality_score', 0.0):.2f}")
        report.append("")
        
        # 协同作用分析
        ml_rl_synergy = self.evaluation_results.get('ml_rl_synergy', {})
        prompt_context_synergy = self.evaluation_results.get('prompt_context_synergy', {})
        report.append("## 协同作用分析")
        report.append(f"- ML-RL协同次数: {ml_rl_synergy.get('synergy_count', 0)}")
        report.append(f"- ML-RL协同分数: {ml_rl_synergy.get('synergy_score', 0.0):.2f}")
        report.append(f"- 提示词-上下文协同次数: {prompt_context_synergy.get('prompt_context_synergy_count', 0)}")
        report.append(f"- 提示词-上下文协同分数: {prompt_context_synergy.get('prompt_context_synergy_score', 0.0):.2f}")
        report.append("")
        
        # 复杂逻辑推理能力
        complex_reasoning = self.evaluation_results.get('complex_reasoning', {})
        report.append("## 复杂逻辑推理能力")
        report.append(f"- 推理活动次数: {complex_reasoning.get('reasoning_activities', 0)}")
        report.append(f"- 复杂推理能力分数: {complex_reasoning.get('reasoning_score', 0.0):.2f}")  # 🚀 修复：重命名避免与系统智能化程度中的推理能力分数重复
        report.append("")
        
        # RANGEN查询处理流程
        query_flow = self.evaluation_results.get('query_processing_flow', {})
        report.append("## RANGEN查询处理流程")
        report.append(f"- 流程活动总数（查询级别）: {query_flow.get('total_flow_activities', 0)}")
        report.append(f"- 流程完整性分数（查询级别）: {query_flow.get('flow_completeness_score', 0.0):.2f}")
        flow_steps = query_flow.get('flow_steps', {})
        for step, count in flow_steps.items():
            if count > 0:
                report.append(f"  - {step}: {count} 次")
        
        # 🚀 改进：显示样本级别的流程统计
        sample_flow_steps = query_flow.get('sample_flow_steps', {})
        if sample_flow_steps:
            report.append(f"- 流程活动总数（样本级别）: {query_flow.get('sample_total_flow_activities', 0)}")
            report.append(f"- 流程完整性分数（样本级别）: {query_flow.get('sample_flow_completeness_score', 0.0):.2f}")
            report.append(f"- 唯一样本ID数量: {query_flow.get('unique_sample_ids', 0)}")
            for step_name, count in sample_flow_steps.items():
                if count > 0:
                    report.append(f"  - {step_name}（样本级别）: {count} 次")
        report.append("")
        
        # 错误分析
        errors = self.evaluation_results.get('error_analysis', {})
        report.append("## 错误分析")
        for error_type, count in errors.items():
            report.append(f"- {error_type}: {count} 次")
        
        return "\n".join(report)
    
    def save_results(self, output_file: str = "evaluation_results.json"):
        """保存评测结果"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.evaluation_results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"评测结果已保存到 {output_file}")
        except Exception as e:
            self.logger.error(f"保存评测结果失败: {e}")

def main():
    """主函数"""
    import argparse
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建评测器
    evaluator = LogBasedEvaluator()
    
    # 分析日志文件
    print(f"开始分析日志文件: {evaluator.log_file}")
    results = evaluator.analyze_log_file()
    
    if "error" in results:
        print(f"分析失败: {results['error']}")
        return
    
    # 生成报告
    print("生成评测报告...")
    report = evaluator.generate_report()
    print(report)
    
    # 保存MD报告文件到comprehensive_eval_results目录
    import os
    report_dir = "comprehensive_eval_results"
    os.makedirs(report_dir, exist_ok=True)
    report_filename = os.path.join(report_dir, "evaluation_report.md")
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 评测报告已保存到: {report_filename}")
    except Exception as e:
        print(f"⚠️ 保存MD报告失败: {e}")
    
    # 保存结果
    evaluator.save_results()
    print("评测完成！")

if __name__ == "__main__":
    main()