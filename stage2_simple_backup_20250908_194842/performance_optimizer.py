"""
性能参数优化器
专门优化性能相关的配置参数
"""

import logging
from typing import Dict, List, Any
from .unified_config_optimizer import BaseConfigOptimizer

logger = logging.getLogger(__name__)

class PerformanceOptimizer(BaseConfigOptimizer):
    """性能参数优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化性能参数"""
        logger.info("⚡ 开始优化性能参数")
        
        optimizations = {
            'optimized_parameters': 0,
            'performance_improvements': [],
            'method': 'performance_specific'
        }
        
        # 获取性能指标
        response_time = performance_data.get('response_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        cpu_usage = performance_data.get('cpu_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        memory_usage = performance_data.get('memory_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        throughput = performance_data.get('throughput', get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
        
        # 优化批处理阈值
        if 'batch_processing_threshold' in self.config_data:
            current_threshold = self.config_data['batch_processing_threshold']
            
            # 基于响应时间调整批处理阈值
            if response_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")) and current_threshold > 20:
                new_threshold = max(20, current_threshold - get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
                self.config_data['batch_processing_threshold'] = new_threshold
                optimizations['performance_improvements'].append(
                    f"batch_processing_threshold: {current_threshold} → {new_threshold}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif response_time < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) and throughput > 50:
                new_threshold = min(200, current_threshold + 20)
                self.config_data['batch_processing_threshold'] = new_threshold
                optimizations['performance_improvements'].append(
                    f"batch_processing_threshold: {current_threshold} → {new_threshold}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化多阶段阈值
        if 'multi_stage_threshold' in self.config_data:
            current_multi_threshold = self.config_data['multi_stage_threshold']
            
            # 基于CPU使用率调整
            if cpu_usage > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and current_multi_threshold > 50:
                new_multi_threshold = max(50, current_multi_threshold - 20)
                self.config_data['multi_stage_threshold'] = new_multi_threshold
                optimizations['performance_improvements'].append(
                    f"multi_stage_threshold: {current_multi_threshold} → {new_multi_threshold}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif cpu_usage < 0.6 and memory_usage < 0.7:
                new_multi_threshold = min(300, current_multi_threshold + 30)
                self.config_data['multi_stage_threshold'] = new_multi_threshold
                optimizations['performance_improvements'].append(
                    f"multi_stage_threshold: {current_multi_threshold} → {new_multi_threshold}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化嵌入批处理大小
        if 'embedding_batch_size' in self.config_data:
            current_batch_size = self.config_data['embedding_batch_size']
            
            # 基于内存使用率调整
            if memory_usage > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and current_batch_size > 32:
                new_batch_size = max(32, current_batch_size // 2)
                self.config_data['embedding_batch_size'] = new_batch_size
                optimizations['performance_improvements'].append(
                    f"embedding_batch_size: {current_batch_size} → {new_batch_size}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif memory_usage < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) and cpu_usage < 0.7:
                new_batch_size = min(512, current_batch_size * 2)
                self.config_data['embedding_batch_size'] = new_batch_size
                optimizations['performance_improvements'].append(
                    f"embedding_batch_size: {current_batch_size} → {new_batch_size}"
                )
                optimizations['optimized_parameters'] += 1
        
        logger.info(f"✅ 性能参数优化完成: {optimizations['optimized_parameters']} 个参数已调整")
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取性能优化建议"""
        suggestions = []
        
        # 分析批处理阈值
        batch_threshold = self.config_data.get('batch_processing_threshold', 50)
        if batch_threshold < 30:
            suggestions.append("批处理阈值过低，可能影响处理效率")
        elif batch_threshold > 150:
            suggestions.append("批处理阈值过高，可能增加内存压力")
        
        # 分析多阶段阈值
        multi_threshold = self.config_data.get('multi_stage_threshold', get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")))
        if multi_threshold < 80:
            suggestions.append("多阶段阈值偏低，可能影响处理质量")
        
        # 分析嵌入批处理大小
        batch_size = self.config_data.get('embedding_batch_size', 128)
        if batch_size < 64:
            suggestions.append("嵌入批处理大小过小，GPU利用率可能不高")
        elif batch_size > 256:
            suggestions.append("嵌入批处理大小过大，可能导致内存不足")
        
        # 基于性能历史分析
        if self.performance_metrics:
            recent_metrics = self.performance_metrics[-5:]
            avg_cpu = sum(m['metrics'].get('cpu_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m['metrics'].get('memory_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for m in recent_metrics) / len(recent_metrics)
            
            if avg_cpu > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
                suggestions.append("CPU使用率持续偏高，建议优化算法或增加计算资源")
            if avg_memory > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
                suggestions.append("内存使用率持续偏高，建议优化内存管理或增加内存")
        
        return suggestions or ["性能配置运行良好"]

class BatchProcessingOptimizer(BaseConfigOptimizer):
    """批处理参数优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化批处理参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 获取性能指标
        throughput = performance_data.get('throughput', get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
        latency = performance_data.get('latency', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        error_rate = performance_data.get('error_rate', 0.05)
        
        # 优化批处理阈值
        for i in range(1, 4):  # 支持多个阈值配置
            threshold_key = f'batch_processing_threshold'
            if i > 1:
                threshold_key = f'batch_processing_threshold_{i}'
            
            if threshold_key in self.config_data:
                current_threshold = self.config_data[threshold_key]
                
                # 基于吞吐量调整阈值
                if throughput > get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")) and latency < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")):
                    new_threshold = min(current_threshold * 1.5, 500)
                elif throughput < 20 or latency > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")):
                    new_threshold = max(current_threshold * get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")), get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
                else:
                    continue
                
                if new_threshold != current_threshold:
                    self.config_data[threshold_key] = int(new_threshold)
                    optimizations['performance_improvements'].append(
                        f"{threshold_key}: {current_threshold} → {int(new_threshold)}"
                    )
                    optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取批处理优化建议"""
        suggestions = []
        
        # 检查批处理策略
        strategy = self.config_data.get('optimization_strategy')
        if strategy == 'minimize_batch_processing_for_evaluation':
            suggestions.append("当前使用最小化批处理策略，适合评估场景")
        
        # 检查阈值配置
        thresholds = [k for k in self.config_data.keys() if 'threshold' in k]
        if len(thresholds) < 2:
            suggestions.append("批处理阈值配置较少，考虑增加更多阈值等级")
        
        return suggestions or ["批处理配置运行正常"]

class ProductionConfigOptimizer(BaseConfigOptimizer):
    """生产环境配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化生产环境参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 获取性能指标
        uptime = performance_data.get('uptime', 0.99)
        error_rate = performance_data.get('error_rate', 0.01)
        resource_usage = performance_data.get('resource_usage', 0.7)
        
        # 优化并发操作数
        if 'max_concurrent_operations' in self.config_data:
            current_max = self.config_data['max_concurrent_operations']
            
            # 基于资源使用率和错误率调整
            if resource_usage > 0.9 or error_rate > 0.05:
                new_max = max(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")), int(current_max * get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))))
                self.config_data['max_concurrent_operations'] = new_max
                optimizations['performance_improvements'].append(
                    f"max_concurrent_operations: {current_max} → {new_max}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif resource_usage < 0.6 and error_rate < 0.01 and uptime > 0.995:
                new_max = min(1000, int(current_max * 1.2))
                self.config_data['max_concurrent_operations'] = new_max
                optimizations['performance_improvements'].append(
                    f"max_concurrent_operations: {current_max} → {new_max}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化缓存大小
        if 'cache_size' in self.config_data:
            current_cache = self.config_data['cache_size']
            
            # 基于命中率调整缓存大小
            cache_hit_rate = performance_data.get('cache_hit_rate', get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))
            if cache_hit_rate < 0.7:
                new_cache = min(current_cache * 1.5, 10000)
                self.config_data['cache_size'] = int(new_cache)
                optimizations['performance_improvements'].append(
                    f"cache_size: {current_cache} → {int(new_cache)}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化内存限制
        if 'memory_limit_mb' in self.config_data:
            current_memory = self.config_data['memory_limit_mb']
            
            # 基于内存使用率调整
            memory_usage = performance_data.get('memory_usage', 0.7)
            if memory_usage > 0.9:
                new_memory = int(current_memory * 0.9)
                self.config_data['memory_limit_mb'] = new_memory
                optimizations['performance_improvements'].append(
                    f"memory_limit_mb: {current_memory} → {new_memory}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取生产环境优化建议"""
        suggestions = []
        
        # 检查环境设置
        environment = self.config_data.get('environment')
        if environment != 'production':
            suggestions.append("当前不是生产环境配置，请确认环境设置")
        
        # 检查监控级别
        monitoring = self.config_data.get('monitoring_level')
        if monitoring != 'detailed':
            suggestions.append("生产环境建议使用详细监控级别")
        
        # 检查日志级别
        log_level = self.config_data.get('log_level')
        if log_level not in ['INFO', 'WARNING']:
            suggestions.append("生产环境建议使用INFO或WARNING日志级别")
        
        # 检查资源限制
        max_concurrent = self.config_data.get('max_concurrent_operations', get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")))
        if max_concurrent > 500:
            suggestions.append("并发操作数设置较高，请确保系统资源充足")
        
        return suggestions or ["生产环境配置运行良好"]
