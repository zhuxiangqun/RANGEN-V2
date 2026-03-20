"""
持续学习闭环 (Continuous Learning Loop)

实现系统的持续学习和改进循环：
- 学习周期管理
- 反馈收集和分析
- 模型更新和部署
- 学习效果评估
- 自适应学习策略
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class LearningPhase(Enum):
    """学习阶段"""
    DATA_COLLECTION = "data_collection"      # 数据收集
    MODEL_TRAINING = "model_training"        # 模型训练
    VALIDATION = "validation"                # 验证
    DEPLOYMENT = "deployment"                # 部署
    MONITORING = "monitoring"                # 监控
    OPTIMIZATION = "optimization"            # 优化


class LearningTrigger(Enum):
    """学习触发器"""
    SCHEDULED = "scheduled"      # 定时触发
    PERFORMANCE_DROP = "performance_drop"    # 性能下降
    NEW_DATA_AVAILABLE = "new_data_available" # 新数据可用
    MANUAL = "manual"           # 手动触发
    ERROR_RATE_SPIKE = "error_rate_spike"    # 错误率激增


@dataclass
class LearningCycle:
    """学习周期"""
    cycle_id: str
    trigger_type: LearningTrigger
    start_time: datetime
    end_time: Optional[datetime] = None
    phases: List[Dict[str, Any]] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    improvement_achieved: Dict[str, float] = field(default_factory=dict)
    status: str = "in_progress"  # in_progress, completed, failed
    error_message: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """周期持续时间（秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def complete_phase(self, phase_name: str, result: Dict[str, Any]):
        """完成阶段"""
        phase_record = {
            'phase': phase_name,
            'completed_at': datetime.now(),
            'result': result,
            'duration': None
        }

        # 计算阶段持续时间
        if self.phases:
            last_phase = self.phases[-1]
            if 'completed_at' in last_phase:
                phase_record['duration'] = (
                    phase_record['completed_at'] - last_phase['completed_at']
                ).total_seconds()

        self.phases.append(phase_record)

    def finalize_cycle(self, success: bool, error_message: Optional[str] = None):
        """完成周期"""
        self.end_time = datetime.now()
        self.status = 'completed' if success else 'failed'
        self.error_message = error_message

        # 计算改进
        if self.metrics_before and self.metrics_after:
            for metric, before_value in self.metrics_before.items():
                after_value = self.metrics_after.get(metric)
                if after_value is not None:
                    # 对于大多数指标，数值增加表示改进
                    if metric in ['accuracy', 'performance', 'efficiency']:
                        improvement = after_value - before_value
                    else:
                        # 对于如响应时间这样的指标，数值减少表示改进
                        improvement = before_value - after_value

                    self.improvement_achieved[metric] = improvement


@dataclass
class LearningModel:
    """学习模型"""
    model_id: str
    model_type: str
    version: str
    trained_at: datetime
    performance_metrics: Dict[str, float]
    training_data_size: int
    validation_score: float
    is_active: bool = False
    deployment_time: Optional[datetime] = None


@dataclass
class LearningFeedback:
    """学习反馈"""
    feedback_id: str
    model_id: str
    feedback_type: str
    metrics: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime
    severity: str = "info"


class DataCollectionManager:
    """数据收集管理器"""

    def __init__(self, collection_window: int = 3600):  # 1小时收集窗口
        self.collection_window = collection_window
        self.feedback_buffer: deque = deque(maxlen=10000)
        self.metric_collectors: Dict[str, Callable] = {}
        self.collection_tasks: Dict[str, asyncio.Task] = {}

    async def start_collection(self):
        """启动数据收集"""
        # 启动所有收集器
        for collector_name, collector_func in self.metric_collectors.items():
            task = asyncio.create_task(self._run_collector(collector_name, collector_func))
            self.collection_tasks[collector_name] = task

        logger.info(f"数据收集管理器启动，{len(self.metric_collectors)}个收集器正在运行")

    async def stop_collection(self):
        """停止数据收集"""
        for task in self.collection_tasks.values():
            task.cancel()

        await asyncio.gather(*self.collection_tasks.values(), return_exceptions=True)
        logger.info("数据收集管理器已停止")

    def register_collector(self, name: str, collector_func: Callable):
        """注册收集器"""
        self.metric_collectors[name] = collector_func

    async def collect_feedback(self, feedback: LearningFeedback):
        """收集反馈"""
        self.feedback_buffer.append(feedback)

    def get_recent_feedback(self, model_id: Optional[str] = None,
                           hours: int = 24) -> List[LearningFeedback]:
        """获取最近反馈"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_feedback = [
            f for f in self.feedback_buffer
            if f.timestamp > cutoff_time
        ]

        if model_id:
            recent_feedback = [f for f in recent_feedback if f.model_id == model_id]

        return recent_feedback

    async def _run_collector(self, name: str, collector_func: Callable):
        """运行收集器"""
        while True:
            try:
                feedback_data = await collector_func()
                if feedback_data:
                    if isinstance(feedback_data, list):
                        for feedback in feedback_data:
                            await self.collect_feedback(feedback)
                    else:
                        await self.collect_feedback(feedback_data)

                await asyncio.sleep(60)  # 每分钟收集一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"收集器 {name} 错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试


class ModelTrainingManager:
    """模型训练管理器"""

    def __init__(self):
        self.active_models: Dict[str, LearningModel] = {}
        self.training_history: List[Dict[str, Any]] = []
        self.training_strategies: Dict[str, Dict[str, Any]] = {}

    async def train_model(self, model_type: str, training_data: List[Dict[str, Any]],
                         validation_data: List[Dict[str, Any]]) -> LearningModel:
        """训练模型"""
        model_id = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        training_start = datetime.now()

        try:
            # 这里应该实现实际的模型训练逻辑
            # 暂时模拟训练过程
            await asyncio.sleep(5)  # 模拟训练时间

            # 生成模拟的性能指标
            performance_metrics = {
                'accuracy': 0.85 + (0.1 * (len(training_data) / 1000)),  # 基于数据量调整
                'precision': 0.82,
                'recall': 0.88,
                'f1_score': 0.85
            }

            validation_score = statistics.mean([
                performance_metrics.get('accuracy', 0.8),
                performance_metrics.get('f1_score', 0.8)
            ])

            model = LearningModel(
                model_id=model_id,
                model_type=model_type,
                version="1.0.0",
                trained_at=datetime.now(),
                performance_metrics=performance_metrics,
                training_data_size=len(training_data),
                validation_score=validation_score
            )

            # 记录训练历史
            training_record = {
                'model_id': model_id,
                'training_start': training_start,
                'training_end': datetime.now(),
                'data_size': len(training_data),
                'performance': performance_metrics,
                'validation_score': validation_score,
                'status': 'success'
            }
            self.training_history.append(training_record)

            logger.info(f"模型训练完成: {model_id}, 验证分数: {validation_score:.3f}")
            return model

        except Exception as e:
            # 记录失败的训练
            training_record = {
                'model_id': model_id,
                'training_start': training_start,
                'training_end': datetime.now(),
                'error': str(e),
                'status': 'failed'
            }
            self.training_history.append(training_record)

            logger.error(f"模型训练失败: {e}")
            raise

    async def validate_model(self, model: LearningModel,
                           test_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """验证模型"""
        try:
            # 这里应该实现实际的模型验证逻辑
            # 暂时返回模拟验证结果
            validation_metrics = {
                'test_accuracy': model.performance_metrics.get('accuracy', 0.8) * 0.95,  # 轻微下降
                'test_precision': model.performance_metrics.get('precision', 0.8) * 0.95,
                'test_recall': model.performance_metrics.get('recall', 0.8) * 0.95,
                'generalization_score': 0.85
            }

            return validation_metrics

        except Exception as e:
            logger.error(f"模型验证失败: {e}")
            return {}

    def deploy_model(self, model: LearningModel) -> bool:
        """部署模型"""
        try:
            # 取消之前活跃模型
            for m in self.active_models.values():
                if m.model_type == model.model_type:
                    m.is_active = False

            # 激活新模型
            model.is_active = True
            model.deployment_time = datetime.now()
            self.active_models[model.model_id] = model

            logger.info(f"模型部署成功: {model.model_id}")
            return True

        except Exception as e:
            logger.error(f"模型部署失败: {e}")
            return False

    def get_active_model(self, model_type: str) -> Optional[LearningModel]:
        """获取活跃模型"""
        for model in self.active_models.values():
            if model.model_type == model_type and model.is_active:
                return model
        return None

    def get_training_statistics(self) -> Dict[str, Any]:
        """获取训练统计"""
        total_trainings = len(self.training_history)
        successful_trainings = len([t for t in self.training_history if t['status'] == 'success'])

        if successful_trainings > 0:
            avg_validation_score = statistics.mean([
                t['validation_score'] for t in self.training_history
                if t['status'] == 'success'
            ])
        else:
            avg_validation_score = 0

        return {
            'total_trainings': total_trainings,
            'successful_trainings': successful_trainings,
            'success_rate': successful_trainings / total_trainings if total_trainings > 0 else 0,
            'average_validation_score': avg_validation_score,
            'active_models': len([m for m in self.active_models.values() if m.is_active])
        }


class LearningEffectivenessEvaluator:
    """学习效果评估器"""

    def __init__(self):
        self.baseline_metrics: Dict[str, float] = {}
        self.evaluation_history: List[Dict[str, Any]] = []

    def establish_baseline(self, metrics: Dict[str, float]):
        """建立基线"""
        self.baseline_metrics.update(metrics)
        logger.info(f"建立学习基线: {metrics}")

    async def evaluate_learning_effect(self, cycle: LearningCycle) -> Dict[str, Any]:
        """评估学习效果"""
        evaluation = {
            'cycle_id': cycle.cycle_id,
            'evaluation_time': datetime.now(),
            'baseline_comparison': {},
            'improvement_analysis': {},
            'statistical_significance': {},
            'overall_effectiveness': 0.0
        }

        # 与基线比较
        for metric, before_value in cycle.metrics_before.items():
            baseline_value = self.baseline_metrics.get(metric)
            after_value = cycle.metrics_after.get(metric)

            if baseline_value is not None and after_value is not None:
                baseline_diff = after_value - baseline_value
                cycle_improvement = cycle.improvement_achieved.get(metric, 0)

                evaluation['baseline_comparison'][metric] = {
                    'baseline_value': baseline_value,
                    'final_value': after_value,
                    'baseline_difference': baseline_diff,
                    'cycle_improvement': cycle_improvement
                }

        # 改进分析
        significant_improvements = []
        for metric, improvement in cycle.improvement_achieved.items():
            if abs(improvement) > 0.05:  # 5%显著改进
                significant_improvements.append({
                    'metric': metric,
                    'improvement': improvement,
                    'significance': 'high' if abs(improvement) > 0.1 else 'medium'
                })

        evaluation['improvement_analysis'] = {
            'significant_improvements': significant_improvements,
            'total_improvement_score': sum(cycle.improvement_achieved.values())
        }

        # 统计显著性（简化计算）
        evaluation['statistical_significance'] = self._assess_statistical_significance(cycle)

        # 总体有效性评分
        improvement_score = evaluation['improvement_analysis']['total_improvement_score']
        significance_score = 1.0 if evaluation['statistical_significance'].get('is_significant', False) else 0.5

        evaluation['overall_effectiveness'] = (improvement_score + significance_score) / 2

        self.evaluation_history.append(evaluation)
        return evaluation

    def _assess_statistical_significance(self, cycle: LearningCycle) -> Dict[str, Any]:
        """评估统计显著性"""
        # 简化的显著性测试
        significant_metrics = 0
        total_metrics = len(cycle.improvement_achieved)

        for improvement in cycle.improvement_achieved.values():
            if abs(improvement) > 0.08:  # 8%阈值
                significant_metrics += 1

        is_significant = significant_metrics >= total_metrics * 0.6  # 60%以上指标显著改进

        return {
            'is_significant': is_significant,
            'significant_metrics': significant_metrics,
            'total_metrics': total_metrics,
            'significance_ratio': significant_metrics / total_metrics if total_metrics > 0 else 0
        }


class ContinuousLearningLoop:
    """
    持续学习闭环

    实现完整的学习周期管理：
    - 学习触发和周期控制
    - 数据收集和模型训练
    - 验证、部署和监控
    - 效果评估和策略调整
    - 自适应学习优化
    """

    def __init__(self):
        self.data_collector = DataCollectionManager()
        self.model_trainer = ModelTrainingManager()
        self.effectiveness_evaluator = LearningEffectivenessEvaluator()

        self.learning_cycles: List[LearningCycle] = []
        self.active_cycle: Optional[LearningCycle] = None

        # 学习配置
        self.learning_interval = 7200  # 2小时学习一次
        self.performance_drop_threshold = 0.05  # 5%性能下降触发学习
        self.error_rate_spike_threshold = 0.1   # 10%错误率激增触发学习

        self._learning_task: Optional[asyncio.Task] = None
        self._running = False

    async def start_learning_loop(self):
        """启动学习闭环"""
        if self._running:
            return

        self._running = True

        # 启动数据收集
        await self.data_collector.start_collection()

        # 启动学习循环
        self._learning_task = asyncio.create_task(self._learning_loop())

        logger.info("持续学习闭环已启动")

    async def stop_learning_loop(self):
        """停止学习闭环"""
        if not self._running:
            return

        self._running = False

        # 停止数据收集
        await self.data_collector.stop_collection()

        # 取消学习任务
        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass

        logger.info("持续学习闭环已停止")

    async def trigger_learning_cycle(self, trigger_type: LearningTrigger,
                                    context: Dict[str, Any] = None) -> str:
        """触发学习周期"""
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 如果有活跃周期，先完成它
        if self.active_cycle:
            self.active_cycle.finalize_cycle(False, "被新周期中断")

        # 创建新周期
        cycle = LearningCycle(
            cycle_id=cycle_id,
            trigger_type=trigger_type,
            start_time=datetime.now(),
            metrics_before=self._collect_current_metrics()
        )

        self.active_cycle = cycle
        self.learning_cycles.append(cycle)

        # 异步执行学习周期
        asyncio.create_task(self._execute_learning_cycle(cycle, context or {}))

        logger.info(f"学习周期已触发: {cycle_id}, 触发类型: {trigger_type.value}")
        return cycle_id

    async def _learning_loop(self):
        """学习循环"""
        while self._running:
            try:
                # 检查是否需要触发学习
                trigger_needed = await self._check_learning_triggers()

                if trigger_needed:
                    await self.trigger_learning_cycle(LearningTrigger.SCHEDULED)

                await asyncio.sleep(self.learning_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"学习循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待

    async def _check_learning_triggers(self) -> bool:
        """检查学习触发器"""
        # 检查性能下降
        current_metrics = self._collect_current_metrics()
        if self.effectiveness_evaluator.baseline_metrics:
            for metric, current_value in current_metrics.items():
                baseline_value = self.effectiveness_evaluator.baseline_metrics.get(metric)
                if baseline_value:
                    drop_ratio = (baseline_value - current_value) / baseline_value
                    if drop_ratio > self.performance_drop_threshold:
                        logger.info(f"检测到性能下降触发学习: {metric} 下降 {drop_ratio:.2%}")
                        return True

        # 检查新数据可用性
        recent_feedback = self.data_collector.get_recent_feedback(hours=1)
        if len(recent_feedback) > 100:  # 最近1小时有大量新数据
            logger.info(f"检测到新数据可用触发学习: {len(recent_feedback)} 条反馈")
            return True

        # 检查错误率激增
        error_feedback = [f for f in recent_feedback if f.feedback_type == 'error']
        if len(recent_feedback) > 10:
            error_rate = len(error_feedback) / len(recent_feedback)
            if error_rate > self.error_rate_spike_threshold:
                logger.info(f"检测到错误率激增触发学习: 错误率 {error_rate:.2%}")
                return True

        return False

    async def _execute_learning_cycle(self, cycle: LearningCycle, context: Dict[str, Any]):
        """执行学习周期"""
        try:
            logger.info(f"开始执行学习周期: {cycle.cycle_id}")

            # 1. 数据收集阶段
            await self._execute_data_collection_phase(cycle)
            cycle.complete_phase('data_collection', {'status': 'completed'})

            # 2. 模型训练阶段
            training_result = await self._execute_model_training_phase(cycle)
            cycle.complete_phase('model_training', training_result)

            # 3. 验证阶段
            validation_result = await self._execute_validation_phase(cycle, training_result)
            cycle.complete_phase('validation', validation_result)

            # 4. 部署阶段
            deployment_result = await self._execute_deployment_phase(cycle, training_result)
            cycle.complete_phase('deployment', deployment_result)

            # 5. 监控阶段（开始监控）
            monitoring_result = await self._start_monitoring_phase(cycle)
            cycle.complete_phase('monitoring', monitoring_result)

            # 收集最终指标
            cycle.metrics_after = self._collect_current_metrics()

            # 评估学习效果
            effectiveness_evaluation = await self.effectiveness_evaluator.evaluate_learning_effect(cycle)

            # 完成周期
            cycle.finalize_cycle(True)

            # 更新基线
            self.effectiveness_evaluator.establish_baseline(cycle.metrics_after)

            logger.info(f"学习周期执行完成: {cycle.cycle_id}, 效果评分: {effectiveness_evaluation['overall_effectiveness']:.3f}")

        except Exception as e:
            error_msg = f"学习周期执行失败: {str(e)}"
            logger.error(error_msg)
            cycle.finalize_cycle(False, error_msg)

    async def _execute_data_collection_phase(self, cycle: LearningCycle):
        """执行数据收集阶段"""
        # 收集训练数据
        recent_feedback = self.data_collector.get_recent_feedback(hours=24)

        # 按类型组织数据
        training_data = []
        for feedback in recent_feedback:
            data_point = {
                'features': feedback.context,
                'target': feedback.metrics,
                'feedback_type': feedback.feedback_type,
                'timestamp': feedback.timestamp
            }
            training_data.append(data_point)

        # 存储到周期上下文（简化实现）
        cycle.phases.append({
            'phase': 'data_collection',
            'data_points_collected': len(training_data),
            'data_sources': list(set(f.feedback_type for f in recent_feedback))
        })

    async def _execute_model_training_phase(self, cycle: LearningCycle) -> Dict[str, Any]:
        """执行模型训练阶段"""
        # 准备训练数据（简化）
        training_data = [
            {'features': {'input': i}, 'target': {'output': i * 2}}
            for i in range(100)
        ]
        validation_data = training_data[-20:]  # 最后20个作为验证数据
        training_data = training_data[:-20]

        # 训练模型
        model = await self.model_trainer.train_model(
            'performance_predictor',
            training_data,
            validation_data
        )

        return {
            'model_id': model.model_id,
            'training_data_size': len(training_data),
            'validation_score': model.validation_score,
            'performance_metrics': model.performance_metrics
        }

    async def _execute_validation_phase(self, cycle: LearningCycle,
                                      training_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行验证阶段"""
        model_id = training_result['model_id']
        model = self.model_trainer.active_models.get(model_id)

        if model:
            # 准备测试数据
            test_data = [
                {'features': {'input': i}, 'target': {'output': i * 2}}
                for i in range(20, 40)
            ]

            validation_metrics = await self.model_trainer.validate_model(model, test_data)

            return {
                'validation_metrics': validation_metrics,
                'is_valid': validation_metrics.get('generalization_score', 0) > 0.7
            }
        else:
            return {'error': '模型不存在'}

    async def _execute_deployment_phase(self, cycle: LearningCycle,
                                      training_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行部署阶段"""
        model_id = training_result['model_id']
        model = self.model_trainer.active_models.get(model_id)

        if model:
            success = self.model_trainer.deploy_model(model)

            return {
                'deployment_success': success,
                'model_id': model_id,
                'deployment_time': datetime.now()
            }
        else:
            return {'deployment_success': False, 'error': '模型不存在'}

    async def _start_monitoring_phase(self, cycle: LearningCycle) -> Dict[str, Any]:
        """开始监控阶段"""
        # 这里应该启动持续监控
        # 暂时返回监控配置
        return {
            'monitoring_started': True,
            'monitored_metrics': ['accuracy', 'response_time', 'error_rate'],
            'alert_thresholds': {
                'performance_drop': 0.05,
                'error_rate_spike': 0.1
            }
        }

    def _collect_current_metrics(self) -> Dict[str, float]:
        """收集当前指标"""
        # 这里应该从实际监控系统收集指标
        # 暂时返回模拟指标
        return {
            'accuracy': 0.85,
            'response_time': 1.2,
            'error_rate': 0.03,
            'throughput': 150.0
        }

    def get_learning_loop_status(self) -> Dict[str, Any]:
        """获取学习闭环状态"""
        active_cycles = len([c for c in self.learning_cycles if c.status == 'in_progress'])
        completed_cycles = len([c for c in self.learning_cycles if c.status == 'completed'])

        return {
            'running': self._running,
            'active_cycles': active_cycles,
            'completed_cycles': completed_cycles,
            'total_cycles': len(self.learning_cycles),
            'data_collector_status': {
                'feedback_buffer_size': len(self.data_collector.feedback_buffer),
                'active_collectors': len(self.data_collector.metric_collectors)
            },
            'model_trainer_status': self.model_trainer.get_training_statistics(),
            'learning_interval': self.learning_interval
        }

    def get_cycle_performance_summary(self) -> Dict[str, Any]:
        """获取周期性能总结"""
        completed_cycles = [c for c in self.learning_cycles if c.status == 'completed']

        if not completed_cycles:
            return {'total_completed_cycles': 0}

        total_improvement = 0
        improvement_counts = defaultdict(int)

        for cycle in completed_cycles:
            cycle_improvement = sum(cycle.improvement_achieved.values())
            total_improvement += cycle_improvement

            for metric, improvement in cycle.improvement_achieved.items():
                if improvement > 0:
                    improvement_counts[f"{metric}_improved"] += 1
                elif improvement < 0:
                    improvement_counts[f"{metric}_degraded"] += 1

        avg_improvement = total_improvement / len(completed_cycles)

        return {
            'total_completed_cycles': len(completed_cycles),
            'average_improvement': avg_improvement,
            'improvement_distribution': dict(improvement_counts),
            'most_improved_metric': max(improvement_counts.items(), key=lambda x: x[1])[0] if improvement_counts else None
        }


# 全局实例
_continuous_learning_loop_instance: Optional[ContinuousLearningLoop] = None

def get_continuous_learning_loop() -> ContinuousLearningLoop:
    """获取持续学习闭环实例"""
    global _continuous_learning_loop_instance
    if _continuous_learning_loop_instance is None:
        _continuous_learning_loop_instance = ContinuousLearningLoop()
    return _continuous_learning_loop_instance
