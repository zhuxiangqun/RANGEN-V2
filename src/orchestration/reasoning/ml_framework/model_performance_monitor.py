"""
模型性能监控

监控ML模型在实际使用中的性能，包括预测准确率、响应时间等指标。
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ModelPerformanceMonitor:
    """模型性能监控器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """初始化性能监控器
        
        Args:
            storage_path: 性能数据存储路径
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.storage_path = Path(storage_path) if storage_path else Path("data/ml_models/performance")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 性能数据缓冲区
        self.performance_buffer = []
        self.buffer_size = 100
        
        # 模型统计信息
        self.model_stats = {}
    
    def record_prediction(
        self,
        model_name: str,
        input_data: Any,
        prediction: Dict[str, Any],
        execution_time: float,
        ground_truth: Optional[Any] = None
    ):
        """记录预测性能
        
        Args:
            model_name: 模型名称
            input_data: 输入数据
            prediction: 预测结果
            execution_time: 执行时间（秒）
            ground_truth: 真实标签（可选，用于计算准确率）
        """
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "model_name": model_name,
                "execution_time": execution_time,
                "prediction": prediction,
                "ground_truth": ground_truth,
                "has_ground_truth": ground_truth is not None
            }
            
            # 计算准确率（如果有真实标签）
            if ground_truth is not None:
                if isinstance(prediction, dict):
                    pred_value = prediction.get("prediction") or prediction.get("is_parallel") or prediction.get("confidence")
                else:
                    pred_value = prediction
                
                # 简单的准确率计算（根据模型类型调整）
                is_correct = self._check_correctness(pred_value, ground_truth, model_name)
                record["is_correct"] = is_correct
                record["accuracy"] = 1.0 if is_correct else 0.0
            else:
                record["is_correct"] = None
                record["accuracy"] = None
            
            self.performance_buffer.append(record)
            
            # 更新模型统计信息
            self._update_model_stats(model_name, record)
            
            # 定期保存
            if len(self.performance_buffer) >= self.buffer_size:
                self._save_buffer()
                
        except Exception as e:
            self.logger.warning(f"记录预测性能失败: {e}")
    
    def _check_correctness(self, prediction: Any, ground_truth: Any, model_name: str) -> bool:
        """检查预测是否正确"""
        try:
            # 根据模型类型进行不同的比较
            if model_name == "parallel_query_classifier":
                # 布尔值比较
                pred_bool = bool(prediction) if isinstance(prediction, (bool, int, float)) else False
                truth_bool = bool(ground_truth) if isinstance(ground_truth, (bool, int, float)) else False
                return pred_bool == truth_bool
            elif model_name == "deep_confidence_estimator":
                # 置信度比较（允许一定误差）
                if isinstance(prediction, dict):
                    pred_value = prediction.get("prediction", 0.0)
                else:
                    pred_value = float(prediction) if prediction else 0.0
                truth_value = float(ground_truth) if ground_truth else 0.0
                return abs(pred_value - truth_value) < 0.1  # 允许0.1的误差
            else:
                # 默认：直接比较
                return prediction == ground_truth
        except Exception:
            return False
    
    def _update_model_stats(self, model_name: str, record: Dict[str, Any]):
        """更新模型统计信息"""
        if model_name not in self.model_stats:
            self.model_stats[model_name] = {
                "total_predictions": 0,
                "total_time": 0.0,
                "correct_predictions": 0,
                "total_with_ground_truth": 0,
                "avg_execution_time": 0.0,
                "avg_accuracy": 0.0
            }
        
        stats = self.model_stats[model_name]
        stats["total_predictions"] += 1
        stats["total_time"] += record["execution_time"]
        stats["avg_execution_time"] = stats["total_time"] / stats["total_predictions"]
        
        if record["has_ground_truth"]:
            stats["total_with_ground_truth"] += 1
            if record.get("is_correct"):
                stats["correct_predictions"] += 1
            
            if stats["total_with_ground_truth"] > 0:
                stats["avg_accuracy"] = stats["correct_predictions"] / stats["total_with_ground_truth"]
    
    def _save_buffer(self):
        """保存缓冲区数据"""
        if not self.performance_buffer:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.storage_path / f"performance_{timestamp}.jsonl"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for record in self.performance_buffer:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            self.logger.info(f"💾 性能数据已保存: {file_path} ({len(self.performance_buffer)} 条记录)")
            self.performance_buffer.clear()
            
        except Exception as e:
            self.logger.error(f"保存性能数据失败: {e}")
    
    def get_model_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """获取模型统计信息
        
        Args:
            model_name: 模型名称（None表示所有模型）
            
        Returns:
            统计信息字典
        """
        if model_name:
            return self.model_stats.get(model_name, {})
        else:
            return self.model_stats.copy()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        # 保存缓冲区
        if self.performance_buffer:
            self._save_buffer()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "model_stats": self.model_stats,
            "summary": {
                "total_models": len(self.model_stats),
                "total_predictions": sum(s["total_predictions"] for s in self.model_stats.values()),
                "models_with_ground_truth": sum(1 for s in self.model_stats.values() if s["total_with_ground_truth"] > 0)
            }
        }
    
    def save_performance_report(self, report_path: Optional[str] = None):
        """保存性能报告"""
        report = self.get_performance_report()
        
        if report_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.storage_path / f"performance_report_{timestamp}.json"
        else:
            report_path = Path(report_path)
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 性能报告已保存: {report_path}")
        return report_path

