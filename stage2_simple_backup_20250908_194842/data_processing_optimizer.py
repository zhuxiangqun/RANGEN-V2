"""
数据处理参数优化器
专门优化数据处理相关的配置参数
"""

import logging
from typing import Dict, List, Any
from .unified_config_optimizer import BaseConfigOptimizer

logger = logging.getLogger(__name__)

class DataProcessingOptimizer(BaseConfigOptimizer):
    """数据处理参数优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化数据处理参数"""
        logger.info("📊 开始优化数据处理参数")
        
        optimizations = {
            'optimized_parameters': 0,
            'performance_improvements': [],
            'method': 'data_processing_specific'
        }
        
        # 获取性能指标
        processing_time = performance_data.get('processing_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        accuracy = performance_data.get('accuracy', get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))
        data_quality = performance_data.get('data_quality', 0.85)
        resource_efficiency = performance_data.get('resource_efficiency', 0.7)
        
        # 优化向量维度
        if 'vector_dimension' in self.config_data:
            current_dimension = self.config_data['vector_dimension']
            
            # 基于准确率和处理时间调整向量维度
            if accuracy > 0.9 and processing_time < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")):
                # 高准确率且快速，可以尝试更高维度
                new_dimension = min(current_dimension + 32, 768)
                self.config_data['vector_dimension'] = new_dimension
                optimizations['performance_improvements'].append(
                    f"vector_dimension: {current_dimension} → {new_dimension}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif accuracy < 0.7 or processing_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")):
                # 准确率低或处理慢，降低维度
                new_dimension = max(current_dimension - 32, 128)
                self.config_data['vector_dimension'] = new_dimension
                optimizations['performance_improvements'].append(
                    f"vector_dimension: {current_dimension} → {new_dimension}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化相似度阈值
        if 'similarity_threshold' in self.config_data:
            current_threshold = self.config_data['similarity_threshold']
            
            # 基于数据质量和准确率调整阈值
            if data_quality > 0.9 and accuracy > 0.85:
                # 高质量数据和高准确率，可以提高阈值
                new_threshold = min(current_threshold + 0.05, 0.9)
                self.config_data['similarity_threshold'] = round(new_threshold, 3)
                optimizations['performance_improvements'].append(
                    f"similarity_threshold: {current_threshold} → {round(new_threshold, 3)}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif data_quality < 0.7 or accuracy < 0.75:
                # 低质量数据或低准确率，降低阈值
                new_threshold = max(current_threshold - 0.05, get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")))
                self.config_data['similarity_threshold'] = round(new_threshold, 3)
                optimizations['performance_improvements'].append(
                    f"similarity_threshold: {current_threshold} → {round(new_threshold, 3)}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化批处理大小（如果存在）
        if 'batch_size' in self.config_data:
            current_batch_size = self.config_data['batch_size']
            
            # 基于资源效率调整批处理大小
            if resource_efficiency > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and processing_time < get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")):
                new_batch_size = min(current_batch_size * 2, 1000)
                self.config_data['batch_size'] = int(new_batch_size)
                optimizations['performance_improvements'].append(
                    f"batch_size: {current_batch_size} → {int(new_batch_size)}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif resource_efficiency < 0.6:
                new_batch_size = max(current_batch_size // 2, get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
                self.config_data['batch_size'] = int(new_batch_size)
                optimizations['performance_improvements'].append(
                    f"batch_size: {current_batch_size} → {int(new_batch_size)}"
                )
                optimizations['optimized_parameters'] += 1
        
        logger.info(f"✅ 数据处理参数优化完成: {optimizations['optimized_parameters']} 个参数已调整")
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取数据处理优化建议"""
        suggestions = []
        
        # 分析向量维度
        vector_dim = self.config_data.get('vector_dimension', 384)
        if vector_dim < 256:
            suggestions.append("向量维度偏低，可能影响语义理解能力")
        elif vector_dim > 512:
            suggestions.append("向量维度较高，可能增加计算开销")
        
        # 分析相似度阈值
        similarity_threshold = self.config_data.get('similarity_threshold', 0.7)
        if similarity_threshold < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")):
            suggestions.append("相似度阈值偏低，可能引入过多噪声数据")
        elif similarity_threshold > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
            suggestions.append("相似度阈值偏高，可能过滤掉有用数据")
        
        # 分析数据源配置
        source_file = self.config_data.get('source_file')
        if source_file and not source_file.startswith('data/'):
            suggestions.append("建议将数据文件放在data目录下以保持一致性")
        
        # 分析方法配置
        method = self.config_data.get('method')
        if method == 'extract_from_frames_data':
            suggestions.append("当前使用框架数据提取方法，请确保数据格式兼容")
        
        # 基于性能历史给出建议
        if self.performance_metrics:
            recent_metrics = self.performance_metrics[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
            avg_accuracy = sum(m['metrics'].get('accuracy', get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))) for m in recent_metrics) / len(recent_metrics)
            avg_processing_time = sum(m['metrics'].get('processing_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))) for m in recent_metrics) / len(recent_metrics)
            
            if avg_accuracy < 0.75:
                suggestions.append("数据处理准确率偏低，建议检查数据质量或调整相似度阈值")
            
            if avg_processing_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")):
                suggestions.append("数据处理时间过长，考虑优化向量维度或批处理大小")
        
        return suggestions or ["数据处理配置运行良好"]

class FramesDataProcessingOptimizer(BaseConfigOptimizer):
    """框架数据处理优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化框架数据处理参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 优化最大并发任务数
        if 'max_concurrent_tasks' in self.config_data:
            current_tasks = self.config_data['max_concurrent_tasks']
            cpu_usage = performance_data.get('cpu_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            
            if cpu_usage > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and current_tasks > 1:
                new_tasks = current_tasks - 1
                self.config_data['max_concurrent_tasks'] = new_tasks
                optimizations['performance_improvements'].append(
                    f"max_concurrent_tasks: {current_tasks} → {new_tasks}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化查询超时时间
        if 'timeout_per_query' in self.config_data:
            current_timeout = self.config_data['timeout_per_query']
            success_rate = performance_data.get('success_rate', get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))
            
            if success_rate < 0.75 and current_timeout < 45:
                new_timeout = min(45, current_timeout + 5)
                self.config_data['timeout_per_query'] = new_timeout
                optimizations['performance_improvements'].append(
                    f"timeout_per_query: {current_timeout} → {new_timeout}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化质量评分
        if 'default_quality_score' in self.config_data:
            current_score = self.config_data['default_quality_score']
            data_quality = performance_data.get('data_quality', get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))
            
            if data_quality > 0.85 and current_score < 0.2:
                new_score = min(get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")), current_score + 0.05)
                self.config_data['default_quality_score'] = new_score
                optimizations['performance_improvements'].append(
                    f"default_quality_score: {current_score} → {new_score}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取框架数据处理优化建议"""
        suggestions = []
        
        if self.config_data.get('max_concurrent_tasks', 1) == 1:
            suggestions.append("单任务处理可能影响性能，考虑增加并发能力")
        
        if self.config_data.get('timeout_per_query', 30) < 20:
            suggestions.append("查询超时时间较短，可能影响数据完整性")
        
        quality_score = self.config_data.get('default_quality_score', 0.1)
        if quality_score > 0.2:
            suggestions.append("默认质量评分较高，可能过于乐观")
        
        return suggestions or ["框架数据处理配置运行正常"]
