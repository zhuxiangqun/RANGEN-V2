"""
LLM训练数据收集器

自动收集模型失败案例和低质量响应，用于训练增强本地模型功能。
与现有的DataCollectionPipeline集成，提供LLM特定的数据收集功能。

## 与原有训练框架的关系

本模块是**专门针对LLM训练**的数据收集器，与系统原有的通用训练框架既有区别又有联系：

### 区别与定位
1. **目标不同**：
   - 原有框架：收集**推理执行轨迹**数据，用于训练推理优化ML组件（如parallel_query_classifier、deep_confidence_estimator等）
   - 本模块：收集**LLM交互数据**（失败案例、低质量响应），用于训练LLM模型（如step-3.5-flash、local-llama等）

2. **数据来源不同**：
   - 原有框架：`DataCollectionPipeline`收集系统执行过程中的计划、步骤、结果等轨迹数据
   - 本模块：从多模型路由器（MultiModelRouter）的实时交互中收集LLM调用数据

3. **检测逻辑不同**：
   - 原有框架：基于执行结果、性能指标等评估推理质量
   - 本模块：基于success字段、错误码、置信度、用户反馈等检测LLM响应质量

### 集成关系
1. **数据管道集成**：本模块尝试导入并使用原有的`DataCollectionPipeline`，将LLM训练数据也记录到统一的数据管道中
2. **架构相似性**：采用了与原有框架相似的数据收集、缓冲、存储模式，确保架构一致性
3. **独立运行**：即使原有数据管道不可用，本模块也可独立运行，保证功能完备性

### 使用场景
- 当需要增强本地LLM模型能力时，自动收集训练数据
- 与`LLMTrainingOrchestrator`配合，形成完整的LLM训练闭环
- 为多模型路由器的决策优化提供数据支持

**注意**：本模块不是原有训练框架的替代品，而是针对LLM训练场景的专业化扩展。
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


class LLMTrainingDataCollector:
    """
    LLM训练数据收集器
    
    自动收集模型失败案例和低质量响应，用于训练增强本地模型功能。
    支持：
    - 实时监控模型响应
    - 失败案例检测（基于success字段、错误码、异常）
    - 低质量响应检测（基于置信度、评分、用户反馈）
    - 训练数据存储和标注
    - 与现有DataCollectionPipeline集成
    
    与原有训练框架的关系：
    本类是专门针对LLM训练设计的数据收集器，与系统原有的通用数据收集框架
    (DataCollectionPipeline) 既有区别又有集成：
    
    1. 数据源不同：原有框架收集推理执行轨迹，本类收集LLM交互数据
    2. 检测逻辑不同：原有框架评估推理质量，本类检测LLM响应质量
    3. 集成方式：尝试导入并使用原有的DataCollectionPipeline，实现数据管道统一
    4. 独立运行：即使原有管道不可用，本类也可独立收集LLM训练数据
    
    原有框架继续负责推理执行数据的收集，本类负责LLM交互数据的收集，两者互补。
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_auto_detection: bool = True,
        quality_threshold: float = 0.7,
        failure_detection_methods: List[str] = None
    ):
        """
        初始化LLM训练数据收集器
        
        Args:
            storage_path: 数据存储路径
            enable_auto_detection: 是否启用自动检测
            quality_threshold: 质量阈值（低于此值视为低质量）
            failure_detection_methods: 失败检测方法列表
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 存储配置
        self.storage_path = Path(storage_path) if storage_path else Path("data/llm_training")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 检测配置
        self.enable_auto_detection = enable_auto_detection
        self.quality_threshold = quality_threshold
        self.failure_detection_methods = failure_detection_methods or [
            "success_field", "error_code", "exception", "low_confidence"
        ]
        
        # 数据存储
        self.failure_cases = []  # 失败案例
        self.low_quality_cases = []  # 低质量案例
        self.training_data = []  # 所有训练数据
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "failures_detected": 0,
            "low_quality_detected": 0,
            "training_samples": 0,
            "last_collection": None
        }
        
        # 线程安全锁
        self.lock = threading.RLock()
        
        # 尝试导入现有的DataCollectionPipeline
        try:
            from core.reasoning.ml_framework.data_collection import DataCollectionPipeline
            self.data_pipeline = DataCollectionPipeline(storage_path=str(self.storage_path / "pipeline"))
            self.has_pipeline = True
            logger.info("成功集成现有DataCollectionPipeline")
        except ImportError:
            self.data_pipeline = None
            self.has_pipeline = False
            logger.info("未找到DataCollectionPipeline，使用独立存储")
        
        logger.info(f"LLM训练数据收集器初始化完成，存储路径: {self.storage_path}")
    
    def record_model_interaction(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        response: Dict[str, Any],
        user_feedback: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录模型交互，自动检测失败和低质量案例
        
        Args:
            model_name: 模型名称
            messages: 输入消息列表
            response: 模型响应
            user_feedback: 用户反馈（可选）
            metadata: 附加元数据（可选）
        
        Returns:
            检测结果字典
        """
        with self.lock:
            self.stats["total_requests"] += 1
            
            detection_result = {
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "is_failure": False,
                "is_low_quality": False,
                "detection_reasons": [],
                "confidence": None
            }
            
            # 提取置信度（如果存在）
            confidence = response.get("confidence")
            if confidence is not None:
                detection_result["confidence"] = confidence
            
            # 检测失败案例
            is_failure = self._detect_failure(response, metadata)
            if is_failure:
                detection_result["is_failure"] = True
                detection_result["detection_reasons"].append("failure")
                
                # 收集失败案例
                failure_case = self._create_training_sample(
                    model_name, messages, response, 
                    sample_type="failure", 
                    detection_reasons=detection_result["detection_reasons"],
                    user_feedback=user_feedback,
                    metadata=metadata
                )
                
                self.failure_cases.append(failure_case)
                self.stats["failures_detected"] += 1
                self.logger.info(f"检测到失败案例: {model_name}, 原因: {detection_result['detection_reasons']}")
            
            # 检测低质量响应
            is_low_quality = self._detect_low_quality(response, user_feedback, metadata)
            if is_low_quality and not is_failure:  # 失败案例不重复标记为低质量
                detection_result["is_low_quality"] = True
                detection_result["detection_reasons"].append("low_quality")
                
                # 收集低质量案例
                low_quality_case = self._create_training_sample(
                    model_name, messages, response,
                    sample_type="low_quality",
                    detection_reasons=detection_result["detection_reasons"],
                    user_feedback=user_feedback,
                    metadata=metadata
                )
                
                self.low_quality_cases.append(low_quality_case)
                self.stats["low_quality_detected"] += 1
                self.logger.info(f"检测到低质量响应: {model_name}, 置信度: {confidence}")
            
            # 如果是训练样本（失败或低质量），添加到总训练数据
            if is_failure or is_low_quality:
                training_sample = self._create_training_sample(
                    model_name, messages, response,
                    sample_type="training",
                    detection_reasons=detection_result["detection_reasons"],
                    user_feedback=user_feedback,
                    metadata=metadata
                )
                
                self.training_data.append(training_sample)
                self.stats["training_samples"] += 1
                
                # 保存到磁盘
                if len(self.training_data) % 10 == 0:  # 每10个样本保存一次
                    self._save_training_data()
            
            # 记录到现有数据管道（如果可用）
            if self.has_pipeline and (is_failure or is_low_quality):
                self._record_to_pipeline(model_name, messages, response, detection_result)
            
            self.stats["last_collection"] = datetime.now().isoformat()
            
            return detection_result
    
    def _detect_failure(self, response: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        检测响应是否失败
        
        Args:
            response: 模型响应
            metadata: 元数据
        
        Returns:
            是否失败
        """
        detection_methods = {
            "success_field": lambda: not response.get("success", True),
            "error_code": lambda: response.get("error") is not None or response.get("error_code") is not None,
            "exception": lambda: response.get("exception") is not None or response.get("error_type") == "exception",
            "timeout": lambda: metadata and metadata.get("timeout", False),
            "rate_limit": lambda: metadata and metadata.get("rate_limited", False)
        }
        
        for method_name in self.failure_detection_methods:
            if method_name in detection_methods:
                try:
                    if detection_methods[method_name]():
                        return True
                except Exception as e:
                    self.logger.debug(f"失败检测方法 '{method_name}' 执行失败: {e}")
        
        return False
    
    def _detect_low_quality(
        self, 
        response: Dict[str, Any], 
        user_feedback: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检测响应是否低质量
        
        Args:
            response: 模型响应
            user_feedback: 用户反馈
            metadata: 元数据
        
        Returns:
            是否低质量
        """
        # 检查置信度
        confidence = response.get("confidence")
        if confidence is not None and confidence < self.quality_threshold:
            return True
        
        # 检查用户评分
        if user_feedback:
            rating = user_feedback.get("rating")
            if rating is not None and rating < 3:  # 1-5评分，低于3视为低质量
                return True
            
            explicit_feedback = user_feedback.get("feedback")
            if explicit_feedback and any(keyword in explicit_feedback.lower() 
                                       for keyword in ["不好", "错误", "不准确", "不满意", "差"]):
                return True
        
        # 检查响应长度（过短可能是低质量）
        content = response.get("content") or response.get("message") or ""
        if isinstance(content, str) and len(content.strip()) < 10:
            return True
        
        # 检查元数据中的质量标记
        if metadata and metadata.get("quality_score", 1.0) < self.quality_threshold:
            return True
        
        return False
    
    def _create_training_sample(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        response: Dict[str, Any],
        sample_type: str,
        detection_reasons: List[str],
        user_feedback: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建训练样本
        
        Args:
            model_name: 模型名称
            messages: 消息列表
            response: 模型响应
            sample_type: 样本类型
            detection_reasons: 检测原因
            user_feedback: 用户反馈
            metadata: 元数据
        
        Returns:
            训练样本字典
        """
        sample = {
            "sample_id": f"{sample_type}_{int(time.time())}_{len(self.training_data)}",
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "sample_type": sample_type,
            "detection_reasons": detection_reasons,
            "input_messages": messages,
            "model_response": response,
            "user_feedback": user_feedback or {},
            "metadata": metadata or {},
            "needs_annotation": sample_type in ["failure", "low_quality"],
            "annotation_status": "pending",
            "corrected_response": None,  # 用于存储人工标注的正确响应
            "training_priority": self._calculate_priority(sample_type, detection_reasons, response)
        }
        
        return sample
    
    def _calculate_priority(
        self,
        sample_type: str,
        detection_reasons: List[str],
        response: Dict[str, Any]
    ) -> int:
        """
        计算训练优先级
        
        Args:
            sample_type: 样本类型
            detection_reasons: 检测原因
            response: 模型响应
        
        Returns:
            优先级（1-10，越高越优先）
        """
        priority = 5  # 默认优先级
        
        # 失败案例优先级更高
        if sample_type == "failure":
            priority += 3
        
        # 严重错误优先级更高
        if "error_code" in detection_reasons or "exception" in detection_reasons:
            priority += 2
        
        # 低置信度优先级较高
        confidence = response.get("confidence")
        if confidence is not None and confidence < 0.3:
            priority += 2
        
        return min(max(priority, 1), 10)  # 限制在1-10范围内
    
    def _record_to_pipeline(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        response: Dict[str, Any],
        detection_result: Dict[str, Any]
    ):
        """
        记录到现有DataCollectionPipeline
        
        Args:
            model_name: 模型名称
            messages: 消息列表
            response: 模型响应
            detection_result: 检测结果
        """
        try:
            trace_data = {
                "query": str(messages),
                "plan": {"model": model_name, "detection_result": detection_result},
                "execution": [{"response": response}],
                "result": {"success": not detection_result["is_failure"]},
                "metrics": {
                    "confidence": detection_result.get("confidence"),
                    "is_failure": detection_result["is_failure"],
                    "is_low_quality": detection_result["is_low_quality"]
                }
            }
            
            self.data_pipeline.collect_execution_trace(trace_data)
        except Exception as e:
            self.logger.warning(f"记录到DataCollectionPipeline失败: {e}")
    
    def _save_training_data(self):
        """保存训练数据到磁盘"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存失败案例
            if self.failure_cases:
                failure_file = self.storage_path / f"failure_cases_{timestamp}.json"
                with open(failure_file, "w", encoding="utf-8") as f:
                    json.dump(self.failure_cases, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"失败案例已保存: {failure_file}")
            
            # 保存低质量案例
            if self.low_quality_cases:
                low_quality_file = self.storage_path / f"low_quality_cases_{timestamp}.json"
                with open(low_quality_file, "w", encoding="utf-8") as f:
                    json.dump(self.low_quality_cases, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"低质量案例已保存: {low_quality_file}")
            
            # 保存所有训练数据
            if self.training_data:
                training_file = self.storage_path / f"training_data_{timestamp}.json"
                with open(training_file, "w", encoding="utf-8") as f:
                    json.dump(self.training_data, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"训练数据已保存: {training_file}")
            
            # 保存统计信息
            stats_file = self.storage_path / "collection_stats.json"
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存训练数据失败: {e}")
    
    def get_training_data(
        self,
        sample_type: Optional[str] = None,
        model_name: Optional[str] = None,
        min_priority: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取训练数据
        
        Args:
            sample_type: 样本类型筛选
            model_name: 模型名称筛选
            min_priority: 最小优先级
            limit: 返回数量限制
        
        Returns:
            训练数据列表
        """
        with self.lock:
            filtered_data = []
            
            for sample in self.training_data:
                # 类型筛选
                if sample_type and sample["sample_type"] != sample_type:
                    continue
                
                # 模型筛选
                if model_name and sample["model_name"] != model_name:
                    continue
                
                # 优先级筛选
                if sample["training_priority"] < min_priority:
                    continue
                
                filtered_data.append(sample)
            
            # 按优先级排序（降序）
            filtered_data.sort(key=lambda x: x["training_priority"], reverse=True)
            
            return filtered_data[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取收集器统计信息"""
        with self.lock:
            stats = self.stats.copy()
            stats["failure_cases_count"] = len(self.failure_cases)
            stats["low_quality_cases_count"] = len(self.low_quality_cases)
            stats["training_data_count"] = len(self.training_data)
            stats["storage_path"] = str(self.storage_path)
            return stats
    
    def clear_data(self, sample_type: Optional[str] = None):
        """
        清除数据
        
        Args:
            sample_type: 清除指定类型的数据（None表示清除所有）
        """
        with self.lock:
            if sample_type is None or sample_type == "failure":
                self.failure_cases.clear()
            if sample_type is None or sample_type == "low_quality":
                self.low_quality_cases.clear()
            if sample_type is None or sample_type == "training":
                self.training_data.clear()
            
            self.logger.info(f"数据已清除，类型: {sample_type or 'all'}")


# 全局单例
_llm_training_collector: Optional[LLMTrainingDataCollector] = None


def get_llm_training_collector(config: Optional[Dict[str, Any]] = None) -> LLMTrainingDataCollector:
    """
    获取LLM训练数据收集器单例
    
    Args:
        config: 配置字典
    
    Returns:
        LLMTrainingDataCollector 实例
    """
    global _llm_training_collector
    
    if _llm_training_collector is None:
        _llm_training_collector = LLMTrainingDataCollector(
            storage_path=config.get("storage_path") if config else None,
            enable_auto_detection=config.get("enable_auto_detection", True) if config else True,
            quality_threshold=config.get("quality_threshold", 0.7) if config else 0.7
        )
    
    return _llm_training_collector