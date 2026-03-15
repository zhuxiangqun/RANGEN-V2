"""
评估参数优化器
专门优化评估相关的配置参数
"""

import logging
from typing import Dict, List, Any
from .unified_config_optimizer import BaseConfigOptimizer

logger = logging.getLogger(__name__)

class EvaluationOptimizer(BaseConfigOptimizer):
    """评估参数优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化评估参数"""
        logger.info("🔬 开始优化评估参数")
        
        optimizations = {
            'optimized_parameters': 0,
            'performance_improvements': [],
            'method': 'evaluation_specific'
        }
        
        # 分析性能数据
        accuracy = performance_data.get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        response_time = performance_data.get('response_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        success_rate = performance_data.get('success_rate', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        
        # 优化并发评估数量
        if 'max_concurrent_evaluations' in self.config_data:
            current_value = self.config_data['max_concurrent_evaluations']
            
            # 基于响应时间调整并发数
            if response_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")) and current_value > 1:
                new_value = max(1, current_value - 1)
                self.config_data['max_concurrent_evaluations'] = new_value
                optimizations['performance_improvements'].append(
                    f"max_concurrent_evaluations: {current_value} → {new_value}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif response_time < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) and accuracy > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
                new_value = min(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")), current_value + 1)
                self.config_data['max_concurrent_evaluations'] = new_value
                optimizations['performance_improvements'].append(
                    f"max_concurrent_evaluations: {current_value} → {new_value}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化超时时间
        if 'timeout_seconds' in self.config_data:
            current_timeout = self.config_data['timeout_seconds']
            
            # 基于成功率调整超时时间
            if success_rate < 0.7 and current_timeout < 120:
                new_timeout = min(120, current_timeout + get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")))
                self.config_data['timeout_seconds'] = new_timeout
                optimizations['performance_improvements'].append(
                    f"timeout_seconds: {current_timeout} → {new_timeout}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif success_rate > 0.9 and current_timeout > 30:
                new_timeout = max(30, current_timeout - 5)
                self.config_data['timeout_seconds'] = new_timeout
                optimizations['performance_improvements'].append(
                    f"timeout_seconds: {current_timeout} → {new_timeout}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化工作线程数
        if 'max_workers' in self.config_data:
            current_workers = self.config_data['max_workers']
            
            # 基于CPU使用率和响应时间调整
            cpu_usage = performance_data.get('cpu_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            if cpu_usage > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and response_time > 1.5:
                new_workers = max(1, current_workers - 1)
                self.config_data['max_workers'] = new_workers
                optimizations['performance_improvements'].append(
                    f"max_workers: {current_workers} → {new_workers}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif cpu_usage < 0.6 and response_time < get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
                new_workers = min(8, current_workers + 1)
                self.config_data['max_workers'] = new_workers
                optimizations['performance_improvements'].append(
                    f"max_workers: {current_workers} → {new_workers}"
                )
                optimizations['optimized_parameters'] += 1
        
        logger.info(f"✅ 评估参数优化完成: {optimizations['optimized_parameters']} 个参数已调整")
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 分析当前配置
        if self.config_data.get('max_concurrent_evaluations', 0) > 5:
            suggestions.append("考虑降低并发评估数量以减少资源消耗")
        
        if self.config_data.get('timeout_seconds', 0) > 60:
            suggestions.append("评估超时时间较长，考虑优化评估算法")
        
        if self.config_data.get('max_workers', 0) < 2:
            suggestions.append("工作线程数较少，考虑增加以提高并发性能")
        
        # 基于性能历史给出建议
        if self.performance_metrics:
            recent_metrics = self.performance_metrics[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
            avg_accuracy = sum(m['metrics'].get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for m in recent_metrics) / len(recent_metrics)
            
            if avg_accuracy < 0.7:
                suggestions.append("评估准确率偏低，建议改进评估算法或增加训练数据")
            elif avg_accuracy > 0.9:
                suggestions.append("评估准确率良好，可以考虑进一步优化性能参数")
        
        if not suggestions:
            suggestions.append("当前配置运行良好，无需重大调整")
        
        return suggestions

class FramesEvaluationOptimizer(BaseConfigOptimizer):
    """框架评估配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化框架评估参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 优化并发任务数
        if 'max_concurrent_tasks' in self.config_data:
            current_tasks = self.config_data['max_concurrent_tasks']
            response_time = performance_data.get('response_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
            
            if response_time > get_smart_config("DEFAULT_TWO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_two_value")) and current_tasks > 1:
                new_tasks = current_tasks - 1
                self.config_data['max_concurrent_tasks'] = new_tasks
                optimizations['performance_improvements'].append(
                    f"max_concurrent_tasks: {current_tasks} → {new_tasks}"
                )
                optimizations['optimized_parameters'] += 1
        
        # 优化查询超时时间
        if 'timeout_per_query' in self.config_data:
            current_timeout = self.config_data['timeout_per_query']
            success_rate = performance_data.get('success_rate', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            
            if success_rate < get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")) and current_timeout < 60:
                new_timeout = min(60, current_timeout + 5)
                self.config_data['timeout_per_query'] = new_timeout
                optimizations['performance_improvements'].append(
                    f"timeout_per_query: {current_timeout} → {new_timeout}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取框架评估优化建议"""
        suggestions = []
        
        if self.config_data.get('max_concurrent_tasks', 1) == 1:
            suggestions.append("当前只支持单任务处理，考虑增加并发能力")
        
        if self.config_data.get('timeout_per_query', 30) < 20:
            suggestions.append("查询超时时间较短，可能影响评估质量")
        
        return suggestions or ["框架评估配置运行正常"]

class FastEvaluationOptimizer(BaseConfigOptimizer):
    """快速评估配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化快速评估参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 优化采样数量
        if 'sample_count' in self.config_data:
            current_samples = self.config_data['sample_count']
            accuracy = performance_data.get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            
            if accuracy > 0.85 and current_samples > 2:
                # 准确率高，可以减少采样以提高速度
                new_samples = max(2, current_samples - 1)
                self.config_data['sample_count'] = new_samples
                optimizations['performance_improvements'].append(
                    f"sample_count: {current_samples} → {new_samples}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif accuracy < 0.7 and current_samples < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
                # 准确率低，需要增加采样
                new_samples = min(get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")), current_samples + 1)
                self.config_data['sample_count'] = new_samples
                optimizations['performance_improvements'].append(
                    f"sample_count: {current_samples} → {new_samples}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取快速评估优化建议"""
        suggestions = []
        
        sample_count = self.config_data.get('sample_count', 3)
        if sample_count < 3:
            suggestions.append("采样数量较少，可能影响评估准确性")
        
        timeout = self.config_data.get('timeout_seconds', 30)
        if timeout > 60:
            suggestions.append("快速评估超时时间较长，可能影响性能")
        
        return suggestions or ["快速评估配置运行正常"]

class LightweightEvaluationOptimizer(BaseConfigOptimizer):
    """轻量级评估配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化轻量级评估参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 轻量级评估主要关注性能和资源使用
        response_time = performance_data.get('response_time', get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
        memory_usage = performance_data.get('memory_usage', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        
        # 调整推理步骤数
        if 'max_reasoning_steps' in self.config_data:
            current_steps = self.config_data['max_reasoning_steps']
            
            if response_time > 1.5 and current_steps > 1:
                new_steps = current_steps - 1
                self.config_data['max_reasoning_steps'] = new_steps
                optimizations['performance_improvements'].append(
                    f"max_reasoning_steps: {current_steps} → {new_steps}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif response_time < get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) and memory_usage < 0.7:
                new_steps = min(5, current_steps + 1)
                self.config_data['max_reasoning_steps'] = new_steps
                optimizations['performance_improvements'].append(
                    f"max_reasoning_steps: {current_steps} → {new_steps}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取轻量级评估优化建议"""
        suggestions = []
        
        if self.config_data.get('max_reasoning_steps', 2) < 2:
            suggestions.append("推理步骤数较少，可能影响评估深度")
        
        if self.config_data.get('timeout_seconds', 60) > 120:
            suggestions.append("轻量级评估超时时间过长")
        
        return suggestions or ["轻量级评估配置运行正常"]

class DynamicConfidenceOptimizer(BaseConfigOptimizer):
    """动态置信度配置优化器"""
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化动态置信度参数"""
        optimizations = {'optimized_parameters': 0, 'performance_improvements': []}
        
        # 优化默认置信度
        if 'default' in self.config_data:
            current_default = self.config_data['default']
            accuracy = performance_data.get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            
            # 根据准确率调整默认置信度
            if accuracy > 0.85 and current_default < 0.7:
                new_default = min(0.7, current_default + 0.05)
                self.config_data['default'] = new_default
                optimizations['performance_improvements'].append(
                    f"default_confidence: {current_default} → {new_default}"
                )
                optimizations['optimized_parameters'] += 1
            
            elif accuracy < 0.6 and current_default > get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")):
                new_default = max(get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")), current_default - 0.05)
                self.config_data['default'] = new_default
                optimizations['performance_improvements'].append(
                    f"default_confidence: {current_default} → {new_default}"
                )
                optimizations['optimized_parameters'] += 1
        
        return optimizations
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取动态置信度优化建议"""
        suggestions = []
        
        default_confidence = self.config_data.get('default', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
        if default_confidence < 0.4:
            suggestions.append("默认置信度偏低，可能影响决策质量")
        elif default_confidence > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
            suggestions.append("默认置信度偏高，可能过于保守")
        
        return suggestions or ["动态置信度配置运行正常"]
