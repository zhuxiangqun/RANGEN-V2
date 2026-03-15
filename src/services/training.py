"""
统一训练服务模块

合并以下服务:
- LLMTrainingOrchestrator (training_orchestrator.py)
- AdaptiveTuningService (adaptive_tuning_service.py)
- TrainingDataCollector (training_data_collector.py)
- ModelBenchmarkService (model_benchmark_service.py)

使用示例:
```python
from src.services.training import TrainingService

training = TrainingService()
training.collect_failure_samples()
training.tune_parameters()
```
"""

import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field


# ============== Enums ==============

class TrainingLevel(str, Enum):
    """训练级别"""
    QUICK_FINETUNE = "quick_finetune"        # 快速微调 (分钟级)
    DOMAIN_ADAPTATION = "domain_adaptation"  # 领域适应 (小时级)
    FULL_TRAINING = "full_training"          # 完整训练 (天级)


class TuningMethod(str, Enum):
    """调优方法"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GRADIENT = "gradient"


class DataSource(str, Enum):
    """数据来源"""
    FAILURE = "failure"
    LOW_QUALITY = "low_quality"
    USER_FEEDBACK = "user_feedback"
    SYNTHETIC = "synthetic"


# ============== Data Classes ==============

@dataclass
class TrainingData:
    """训练数据"""
    source: DataSource
    samples: List[Dict[str, Any]]
    size: int
    quality_score: float
    timestamp: float


@dataclass
class TuningConfig:
    """调优配置"""
    method: TuningMethod
    max_iterations: int
    learning_rate: float
    batch_size: int
    epochs: int


@dataclass
class TuningResult:
    """调优结果"""
    best_params: Dict[str, Any]
    best_score: float
    history: List[Dict[str, Any]]
    training_time: float


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    model: str
    metrics: Dict[str, float]
    latency: float
    timestamp: float


# ============== Main Class ==============

class TrainingService:
    """
    统一训练服务
    
    提供:
    - 数据收集 (Data Collection)
    - 参数调优 (Parameter Tuning)
    - 基准测试 (Benchmarking)
    - 模型训练 (Model Training)
    """
    
    def __init__(self):
        self._training_data: Dict[DataSource, TrainingData] = {}
        self._failure_samples: List[Dict[str, Any]] = []
        self._low_quality_samples: List[Dict[str, Any]] = []
        self._benchmarks: Dict[str, BenchmarkResult] = {}
        self._tuning_history: List[TuningResult] = []
        
        # Thresholds
        self._failure_threshold = 0.3  # 30% failure rate
        self._min_samples = 10
    
    # ============== Data Collection ==============
    
    def collect_failure_samples(
        self,
        samples: List[Dict[str, Any]],
        min_samples: int = 10
    ) -> int:
        """收集失败样本"""
        # Filter valid samples
        valid_samples = [
            s for s in samples
            if "query" in s and "error" in s
        ]
        
        self._failure_samples.extend(valid_samples)
        
        # Keep only recent samples
        max_samples = min_samples * 10
        if len(self._failure_samples) > max_samples:
            self._failure_samples = self._failure_samples[-max_samples:]
        
        self._training_data[DataSource.FAILURE] = TrainingData(
            source=DataSource.FAILURE,
            samples=self._failure_samples,
            size=len(self._failure_samples),
            quality_score=self._calculate_quality_score(self._failure_samples),
            timestamp=time.time()
        )
        
        return len(valid_samples)
    
    def collect_low_quality_samples(
        self,
        samples: List[Dict[str, Any]]
    ) -> int:
        """收集低质量样本"""
        valid_samples = [
            s for s in samples
            if "query" in s and "quality_score" in s and s["quality_score"] < 0.6
        ]
        
        self._low_quality_samples.extend(valid_samples)
        
        max_samples = 200
        if len(self._low_quality_samples) > max_samples:
            self._low_quality_samples = self._low_quality_samples[-max_samples:]
        
        self._training_data[DataSource.LOW_QUALITY] = TrainingData(
            source=DataSource.LOW_QUALITY,
            samples=self._low_quality_samples,
            size=len(self._low_quality_samples),
            quality_score=0.5,  # Already low quality
            timestamp=time.time()
        )
        
        return len(valid_samples)
    
    def add_user_feedback(
        self,
        query: str,
        feedback: str,
        rating: int  # 1-5
    ) -> None:
        """添加用户反馈"""
        sample = {
            "query": query,
            "feedback": feedback,
            "rating": rating,
            "timestamp": time.time()
        }
        
        source = DataSource.USER_FEEDBACK
        if source not in self._training_data:
            self._training_data[source] = TrainingData(
                source=source,
                samples=[],
                size=0,
                quality_score=0.0,
                timestamp=time.time()
            )
        
        self._training_data[source].samples.append(sample)
        self._training_data[source].size = len(self._training_data[source].samples)
    
    def _calculate_quality_score(self, samples: List[Dict[str, Any]]) -> float:
        """计算质量分数"""
        if not samples:
            return 0.0
        
        # Based on error types
        error_weights = {
            "timeout": 0.8,
            "invalid_output": 0.9,
            "low_confidence": 0.7,
            "other": 0.5
        }
        
        total_score = 0.0
        for sample in samples:
            error_type = sample.get("error_type", "other")
            weight = error_weights.get(error_type, 0.5)
            total_score += weight
        
        return total_score / len(samples)
    
    # ============== Parameter Tuning ==============
    
    def tune_parameters(
        self,
        base_params: Dict[str, Any],
        objective: str = "quality",
        config: Optional[TuningConfig] = None
    ) -> TuningResult:
        """调优参数"""
        if config is None:
            config = TuningConfig(
                method=TuningMethod.GRID_SEARCH,
                max_iterations=10,
                learning_rate=0.01,
                batch_size=8,
                epochs=3
            )
        
        start_time = time.time()
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(
            base_params,
            config.method,
            config.max_iterations
        )
        
        # Evaluate each combination
        history = []
        best_params = base_params.copy()
        best_score = 0.0
        
        for params in param_combinations:
            score = self._evaluate_params(params, objective)
            history.append({
                "params": params,
                "score": score,
                "timestamp": time.time()
            })
            
            if score > best_score:
                best_score = score
                best_params = params.copy()
        
        result = TuningResult(
            best_params=best_params,
            best_score=best_score,
            history=history,
            training_time=time.time() - start_time
        )
        
        self._tuning_history.append(result)
        
        return result
    
    def _generate_param_combinations(
        self,
        base_params: Dict[str, Any],
        method: TuningMethod,
        max_iterations: int
    ) -> List[Dict[str, Any]]:
        """生成参数组合"""
        if method == TuningMethod.GRID_SEARCH:
            # Simple grid search
            combinations = []
            for lr in [0.001, 0.01, 0.1]:
                for bs in [4, 8, 16]:
                    params = base_params.copy()
                    params["learning_rate"] = lr
                    params["batch_size"] = bs
                    combinations.append(params)
            return combinations[:max_iterations]
        
        elif method == TuningMethod.RANDOM_SEARCH:
            # Random search
            import random
            combinations = []
            for _ in range(max_iterations):
                params = base_params.copy()
                params["learning_rate"] = random.choice([0.001, 0.01, 0.1, 0.5])
                params["batch_size"] = random.choice([4, 8, 16, 32])
                params["temperature"] = random.uniform(0.5, 1.0)
                combinations.append(params)
            return combinations
        
        else:
            # Default: return base params
            return [base_params]
    
    def _evaluate_params(
        self,
        params: Dict[str, Any],
        objective: str
    ) -> float:
        """评估参数"""
        # Simplified evaluation (in production would actually train)
        
        # Use training data if available
        if DataSource.FAILURE in self._training_data:
            data = self._training_data[DataSource.FAILURE]
            base_score = data.quality_score
        else:
            base_score = 0.5
        
        # Adjust based on parameters
        lr = params.get("learning_rate", 0.01)
        bs = params.get("batch_size", 8)
        
        # Higher learning rate might overfit
        lr_factor = 1.0 - abs(lr - 0.01) * 10
        
        score = base_score * lr_factor
        
        return max(0.0, min(1.0, score))
    
    # ============== Benchmarking ==============
    
    def run_benchmark(
        self,
        model_name: str,
        test_cases: List[Dict[str, Any]]
    ) -> BenchmarkResult:
        """运行基准测试"""
        import time
        
        start_time = time.time()
        
        # Run test cases
        results = []
        for case in test_cases:
            # Simplified: just measure time
            case_start = time.time()
            # Would actually run inference here
            _ = case.get("query", "")
            case_time = time.time() - case_start
            results.append(case_time)
        
        # Calculate metrics
        avg_latency = sum(results) / len(results) if results else 0
        
        # Quality metrics (simplified)
        metrics = {
            "avg_latency": avg_latency,
            "p50_latency": sorted(results)[len(results)//2] if results else 0,
            "p95_latency": sorted(results)[int(len(results)*0.95)] if results else 0,
            "success_rate": 0.95,  # Simplified
        }
        
        result = BenchmarkResult(
            model=model_name,
            metrics=metrics,
            latency=avg_latency,
            timestamp=time.time()
        )
        
        self._benchmarks[model_name] = result
        
        return result
    
    def compare_models(
        self,
        model_names: List[str],
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, BenchmarkResult]:
        """比较模型"""
        results = {}
        
        for model in model_names:
            results[model] = self.run_benchmark(model, test_cases)
        
        return results
    
    # ============== Analysis ==============
    
    def get_training_data_summary(self) -> Dict[str, Any]:
        """获取训练数据摘要"""
        summary = {}
        
        for source, data in self._training_data.items():
            summary[source.value] = {
                "size": data.size,
                "quality_score": data.quality_score,
                "timestamp": data.timestamp,
            }
        
        return summary
    
    def should_train(
        self,
        model_name: str,
        failure_rate_threshold: float = 0.3,
        min_samples: int = 10
    ) -> bool:
        """判断是否应该训练"""
        # Check failure samples
        failure_rate = len(self._failure_samples) / max(1, sum(
            d.size for d in self._training_data.values()
        ))
        
        if failure_rate > failure_rate_threshold:
            return True
        
        if len(self._failure_samples) >= min_samples:
            return True
        
        return False
    
    def get_tuning_history(self) -> List[TuningResult]:
        """获取调优历史"""
        return self._tuning_history
    
    def get_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """获取基准测试结果"""
        return self._benchmarks


# ============== Factory ==============

def get_training_service() -> TrainingService:
    """获取训练服务"""
    return TrainingService()
