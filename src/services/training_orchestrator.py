"""
LLM训练流程管理器

管理LLM模型的训练流程，支持多种训练级别：
1. 快速微调（Few-shot Learning）- 分钟级，提示工程优化
2. 领域适应训练（Domain Adaptation）- 小时级，领域特定优化  
3. 完整定制训练（Full Custom Training）- 天级，从头训练或深度微调

集成现有组件：ContinuousLearningSystem, DataCollectionPipeline, ModelPerformanceMonitor

## 与原有训练框架的关系

本模块是**专门针对LLM训练**的流程管理器，与系统原有的通用训练框架既有区别又有联系：

### 区别与定位
1. **目标模型不同**：
   - 原有框架：管理**推理ML组件**的训练（如分类器、预测器、优化器等）
   - 本模块：管理**大语言模型（LLM）** 的训练（如step-3.5-flash、local-llama、local-qwen等）

2. **训练范式不同**：
   - 原有框架：使用传统ML/深度学习训练范式（scikit-learn、PyTorch等）
   - 本模块：使用LLM特定训练技术（LoRA微调、P-Tuning、领域适应训练等）

3. **训练级别不同**：
   - 原有框架：主要进行增量训练、模型更新
   - 本模块：支持三级训练（快速微调、领域适应、完整训练），适应不同资源和时间需求

### 集成关系
1. **组件重用**：本模块导入并重用原有的`ContinuousLearningSystem`进行模型注册和训练调度
2. **数据管道集成**：通过`LLMTrainingDataCollector`与原有`DataCollectionPipeline`集成
3. **架构兼容**：遵循原有的训练状态管理、任务调度模式，确保系统一致性

### 与原有框架的协作流程
1. **数据收集**：`LLMTrainingDataCollector`收集LLM交互数据
2. **训练触发**：本模块检测训练需求，决定训练级别
3. **训练执行**：执行LLM特定训练（当前为模拟实现，预留实际训练接口）
4. **模型注册**：训练后的模型注册到`ContinuousLearningSystem`
5. **调度管理**：通过原有系统进行定期重新训练调度

### 使用场景
- 当本地LLM模型能力不足时，自动触发训练增强
- 根据失败率和质量评分动态调整训练策略
- 与多模型路由器集成，优先使用训练后的增强模型

**注意**：本模块不是原有训练框架的替代品，而是针对LLM训练场景的专业化扩展。原有框架继续负责推理ML组件的训练，本模块负责LLM模型的训练。
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class TrainingLevel(str, Enum):
    """训练级别"""
    QUICK_FINETUNE = "quick_finetune"      # 快速微调：提示工程，LoRA微调
    DOMAIN_ADAPTATION = "domain_adaptation"  # 领域适应：继续预训练，领域特定词表
    FULL_TRAINING = "full_training"        # 完整训练：从头训练或深度微调


class TrainingStatus(str, Enum):
    """训练状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"


class LLMTrainingOrchestrator:
    """
    LLM训练流程管理器
    
    管理LLM模型的完整训练流程：
    - 训练数据准备和预处理
    - 训练配置和调度
    - 训练执行和监控
    - 模型评估和验证
    - 模型部署和集成
    
    与原有训练框架的关系：
    本类是专门针对LLM训练设计的流程管理器，与系统原有的通用训练框架
    (ContinuousLearningSystem, continuous_learning_loop.py) 既有区别又有集成：
    
    1. 目标不同：原有框架训练推理ML组件，本类训练大语言模型(LLM)
    2. 技术不同：原有框架使用传统ML训练，本类使用LLM微调技术
    3. 集成方式：重用ContinuousLearningSystem进行模型注册和调度
    4. 数据来源：通过LLMTrainingDataCollector获取LLM交互数据
    
    原有框架继续负责推理ML组件的训练，本类负责LLM模型的训练，两者互补。
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_auto_training: bool = True,
        training_thresholds: Optional[Dict[str, Any]] = None
    ):
        """
        初始化训练流程管理器
        
        Args:
            storage_path: 存储路径
            enable_auto_training: 是否启用自动训练
            training_thresholds: 训练触发阈值
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 存储配置
        self.storage_path = Path(storage_path) if storage_path else Path("data/llm_training/orchestrator")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 训练配置
        self.enable_auto_training = enable_auto_training
        self.training_thresholds = training_thresholds or {
            "min_failure_samples": 10,      # 最少失败样本数
            "min_low_quality_samples": 20,  # 最少低质量样本数
            "failure_rate_threshold": 0.3,  # 失败率阈值（30%）
            "quality_score_threshold": 0.6, # 质量分阈值
            "training_interval_hours": 24   # 训练间隔（小时）
        }
        
        # 集成现有组件
        try:
            from core.reasoning.ml_framework.continuous_learning_system import ContinuousLearningSystem
            from services.training_data_collector import get_llm_training_collector
            from core.reasoning.ml_framework.model_performance_monitor import ModelPerformanceMonitor
            
            self.continuous_learning = ContinuousLearningSystem({
                "storage_path": str(self.storage_path / "continuous_learning")
            })
            self.data_collector = get_llm_training_collector()
            self.performance_monitor = ModelPerformanceMonitor(
                str(self.storage_path / "performance")
            )
            self.components_available = True
            self.logger.info("成功集成所有训练组件")
        except ImportError as e:
            self.logger.warning(f"部分训练组件导入失败: {e}")
            self.components_available = False
        
        # 训练状态管理
        self.training_jobs = {}  # job_id -> job_info
        self.model_training_history = {}  # model_name -> [training_history]
        self.last_training_time = {}  # model_name -> last_training_timestamp
        
        # 线程安全
        self.lock = threading.RLock()
        
        logger.info(f"LLM训练流程管理器初始化完成，自动训练: {enable_auto_training}")
    
    def _get_model_adapter(self, model_name: str):
        """获取模型适配器
        
        Args:
            model_name: 模型名称，如 'local-llama', 'local-qwen', 'step-3.5-flash'
        
        Returns:
            适配器实例或None
        """
        try:
            from src.adapters.llm_adapter_factory import LLMAdapterFactory
            from src.adapters.llm_adapter_base import LLMProvider, AdapterConfig, AdapterCapability
            
            # 模型名称到LLMProvider的映射
            model_to_provider = {
                "local-llama": LLMProvider.LOCAL_LLAMA,
                "local-qwen": LLMProvider.LOCAL_QWEN,
                "local-phi3": LLMProvider.LOCAL_PHI3,
                "step-3.5-flash": LLMProvider.STEPFLASH,
            }
            
            if model_name not in model_to_provider:
                self.logger.warning(f"未知的模型名称: {model_name}")
                return None
            
            provider = model_to_provider[model_name]
            
            # 尝试从配置服务获取模型配置
            try:
                from src.services.multi_model_config_service import get_multi_model_config_service
                config_service = get_multi_model_config_service()
                model_config = config_service.get_model_config(model_name)
                
                if model_config:
                    # 使用配置中的参数
                    config = AdapterConfig(
                        provider=provider,
                        model_name=model_config.get("model", model_name),
                        base_url=model_config.get("base_url"),
                        api_key=model_config.get("api_key"),
                        capabilities=[AdapterCapability.CHAT_COMPLETION]
                    )
                else:
                    # 使用默认配置
                    config = AdapterConfig(
                        provider=provider,
                        model_name=model_name,
                        capabilities=[AdapterCapability.CHAT_COMPLETION]
                    )
            except ImportError:
                # 配置服务不可用，使用默认配置
                config = AdapterConfig(
                    provider=provider,
                    model_name=model_name,
                    capabilities=[AdapterCapability.CHAT_COMPLETION]
                )
            
            # 创建适配器
            adapter = LLMAdapterFactory.create_adapter(config)
            return adapter
            
        except Exception as e:
            self.logger.warning(f"获取模型适配器失败 {model_name}: {e}")
            return None
    
    def check_training_needed(
        self,
        model_name: str,
        force_check: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        检查模型是否需要训练
        
        Args:
            model_name: 模型名称
            force_check: 强制检查（忽略时间间隔）
        
        Returns:
            (是否需要训练, 检查结果详情)
        """
        if not self.components_available:
            return False, {"error": "训练组件不可用"}
        
        with self.lock:
            check_result = {
                "model_name": model_name,
                "timestamp": datetime.now().isoformat(),
                "checks_passed": [],
                "checks_failed": [],
                "recommended_level": None,
                "reason": ""
            }
            
            # 检查时间间隔
            last_time = self.last_training_time.get(model_name)
            if last_time and not force_check:
                time_since_last = (datetime.now() - datetime.fromisoformat(last_time)).total_seconds() / 3600
                if time_since_last < self.training_thresholds["training_interval_hours"]:
                    check_result["checks_failed"].append("training_interval")
                    check_result["reason"] = f"距离上次训练仅 {time_since_last:.1f} 小时，未达到间隔要求"
                    return False, check_result
            
            # 获取模型统计信息
            try:
                stats = self.data_collector.get_stats()
                failure_count = stats.get("failure_cases_count", 0)
                low_quality_count = stats.get("low_quality_cases_count", 0)
                
                # 获取失败率（如果有足够数据）
                failure_rate = 0.0
                if stats.get("total_requests", 0) > 0:
                    failure_rate = stats.get("failures_detected", 0) / stats.get("total_requests", 0)
                
                # 检查失败样本数
                if failure_count >= self.training_thresholds["min_failure_samples"]:
                    check_result["checks_passed"].append("failure_samples")
                    check_result["reason"] += f"失败样本数足够: {failure_count}"
                else:
                    check_result["checks_failed"].append("failure_samples")
                
                # 检查低质量样本数
                if low_quality_count >= self.training_thresholds["min_low_quality_samples"]:
                    check_result["checks_passed"].append("low_quality_samples")
                    check_result["reason"] += f"，低质量样本数足够: {low_quality_count}"
                else:
                    check_result["checks_failed"].append("low_quality_samples")
                
                # 检查失败率
                if failure_rate >= self.training_thresholds["failure_rate_threshold"]:
                    check_result["checks_passed"].append("failure_rate")
                    check_result["reason"] += f"，失败率过高: {failure_rate:.1%}"
                else:
                    check_result["checks_failed"].append("failure_rate")
                
                # 决定是否需要训练
                needs_training = len(check_result["checks_passed"]) > 0
                
                if needs_training:
                    # 推荐训练级别
                    if failure_rate > 0.5 or failure_count > 50:
                        check_result["recommended_level"] = TrainingLevel.FULL_TRAINING
                    elif failure_count > 20 or low_quality_count > 30:
                        check_result["recommended_level"] = TrainingLevel.DOMAIN_ADAPTATION
                    else:
                        check_result["recommended_level"] = TrainingLevel.QUICK_FINETUNE
                    
                    check_result["reason"] = f"需要{check_result['recommended_level'].value}训练: {check_result['reason']}"
                
                return needs_training, check_result
                
            except Exception as e:
                self.logger.error(f"检查训练需求失败: {e}")
                check_result["error"] = str(e)
                return False, check_result
    
    def prepare_training_data(
        self,
        model_name: str,
        training_level: TrainingLevel,
        max_samples: int = 1000
    ) -> Dict[str, Any]:
        """
        准备训练数据
        
        Args:
            model_name: 模型名称
            training_level: 训练级别
            max_samples: 最大样本数
        
        Returns:
            数据准备结果
        """
        if not self.components_available:
            return {"success": False, "error": "训练组件不可用"}
        
        try:
            # 获取训练数据
            training_data = self.data_collector.get_training_data(
                model_name=model_name,
                min_priority=3 if training_level == TrainingLevel.QUICK_FINETUNE else 1,
                limit=max_samples
            )
            
            if not training_data:
                return {
                    "success": False,
                    "error": f"没有找到模型 {model_name} 的训练数据",
                    "data_count": 0
                }
            
            # 根据训练级别处理数据
            processed_data = self._process_training_data(training_data, training_level)
            
            # 保存处理后的数据
            data_file = self.storage_path / f"training_data_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "data_count": len(training_data),
                "processed_count": len(processed_data),
                "data_file": str(data_file),
                "training_level": training_level.value
            }
            
        except Exception as e:
            self.logger.error(f"准备训练数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_training_data(
        self,
        raw_data: List[Dict[str, Any]],
        training_level: TrainingLevel
    ) -> List[Dict[str, Any]]:
        """
        处理训练数据
        
        Args:
            raw_data: 原始训练数据
            training_level: 训练级别
        
        Returns:
            处理后的训练数据
        """
        processed_data = []
        
        for sample in raw_data:
            try:
                # 提取输入和输出
                messages = sample.get("input_messages", [])
                response = sample.get("model_response", {})
                
                # 根据训练级别创建不同的训练样本格式
                if training_level == TrainingLevel.QUICK_FINETUNE:
                    # 快速微调：使用原始对话格式
                    processed_sample = {
                        "messages": messages,
                        "response": response.get("content") or response.get("message") or "",
                        "original_response": response,
                        "sample_type": sample.get("sample_type"),
                        "priority": sample.get("training_priority", 5)
                    }
                
                elif training_level == TrainingLevel.DOMAIN_ADAPTATION:
                    # 领域适应：提取领域特定内容
                    processed_sample = {
                        "text": self._extract_text_for_domain_adaptation(messages, response),
                        "domain_keywords": self._extract_domain_keywords(messages),
                        "sample_type": sample.get("sample_type")
                    }
                
                elif training_level == TrainingLevel.FULL_TRAINING:
                    # 完整训练：完整的训练格式
                    processed_sample = {
                        "instruction": self._extract_instruction(messages),
                        "input": self._extract_input(messages),
                        "output": self._extract_expected_output(response, sample),
                        "metadata": {
                            "sample_type": sample.get("sample_type"),
                            "detection_reasons": sample.get("detection_reasons", []),
                            "user_feedback": sample.get("user_feedback", {})
                        }
                    }
                
                processed_data.append(processed_sample)
                
            except Exception as e:
                self.logger.debug(f"处理训练样本失败: {e}")
                continue
        
        return processed_data
    
    def _extract_text_for_domain_adaptation(self, messages: List[Dict[str, str]], response: Dict[str, Any]) -> str:
        """提取领域适应训练的文本"""
        text_parts = []
        
        for msg in messages:
            if msg.get("role") in ["user", "system"]:
                text_parts.append(msg.get("content", ""))
        
        response_text = response.get("content") or response.get("message") or ""
        if response_text:
            text_parts.append(response_text)
        
        return " ".join(text_parts)
    
    def _extract_domain_keywords(self, messages: List[Dict[str, str]]) -> List[str]:
        """提取领域关键词（简化实现）"""
        # 实际实现应使用关键词提取算法
        keywords = []
        for msg in messages:
            content = msg.get("content", "").lower()
            # 简单关键词检测
            if "代码" in content or "编程" in content:
                keywords.append("编程")
            if "数据" in content or "分析" in content:
                keywords.append("数据分析")
            if "文档" in content or "总结" in content:
                keywords.append("文档处理")
        
        return list(set(keywords))
    
    def _extract_instruction(self, messages: List[Dict[str, str]]) -> str:
        """提取指令"""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content", "")
        
        # 如果没有system消息，使用第一个user消息
        for msg in messages:
            if msg.get("role") == "user":
                return msg.get("content", "")[:100]  # 截断
        
        return ""
    
    def _extract_input(self, messages: List[Dict[str, str]]) -> str:
        """提取输入"""
        input_parts = []
        for msg in messages:
            if msg.get("role") == "user":
                input_parts.append(msg.get("content", ""))
        
        return " ".join(input_parts)
    
    def _extract_expected_output(self, response: Dict[str, Any], sample: Dict[str, Any]) -> str:
        """提取期望输出"""
        # 如果有修正的响应，使用修正后的
        corrected = sample.get("corrected_response")
        if corrected:
            return corrected
        
        # 否则使用原始响应
        content = response.get("content") or response.get("message") or ""
        
        # 如果是失败案例，可能需要生成更好的输出
        # 这里简化处理，实际应使用更好的方法
        if sample.get("sample_type") == "failure":
            return f"[需要修正] {content}"
        
        return content
    
    def start_training_job(
        self,
        model_name: str,
        training_level: TrainingLevel,
        training_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动训练任务
        
        Args:
            model_name: 模型名称
            training_level: 训练级别
            training_config: 训练配置
        
        Returns:
            训练任务信息
        """
        if not self.components_available:
            return {"success": False, "error": "训练组件不可用"}
        
        job_id = f"train_{model_name}_{int(time.time())}"
        
        with self.lock:
            # 创建训练任务
            job_info = {
                "job_id": job_id,
                "model_name": model_name,
                "training_level": training_level,
                "status": TrainingStatus.PREPARING,
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "config": training_config or {},
                "progress": 0.0,
                "logs": [],
                "result": None
            }
            
            self.training_jobs[job_id] = job_info
            
            # 在后台启动训练
            threading.Thread(
                target=self._execute_training_job,
                args=(job_id,),
                daemon=True
            ).start()
            
            self.logger.info(f"训练任务已启动: {job_id} ({training_level.value})")
            
            return {
                "success": True,
                "job_id": job_id,
                "job_info": job_info
            }
    
    def _execute_training_job(self, job_id: str):
        """执行训练任务（后台线程）"""
        with self.lock:
            job_info = self.training_jobs.get(job_id)
            if not job_info:
                return
            
            model_name = job_info["model_name"]
            training_level = job_info["training_level"]
            config = job_info["config"]
        
        try:
            # 更新状态：准备数据
            self._update_job_status(job_id, TrainingStatus.PREPARING, 10.0)
            self._add_job_log(job_id, "开始准备训练数据")
            
            # 准备数据
            data_result = self.prepare_training_data(
                model_name, training_level, 
                config.get("max_samples", 1000)
            )
            
            if not data_result.get("success"):
                self._update_job_status(job_id, TrainingStatus.FAILED, 0.0, 
                                       {"error": f"数据准备失败: {data_result.get('error')}"})
                return
            
            self._add_job_log(job_id, f"训练数据准备完成: {data_result['processed_count']} 个样本")
            
            # 更新状态：训练中
            self._update_job_status(job_id, TrainingStatus.TRAINING, 30.0)
            self._add_job_log(job_id, f"开始{training_level.value}训练")
            
            # 执行训练（实际训练逻辑）
            training_result = self._perform_training(
                model_name, training_level, data_result, config
            )
            
            if not training_result.get("success"):
                self._update_job_status(job_id, TrainingStatus.FAILED, 50.0,
                                       {"error": f"训练失败: {training_result.get('error')}"})
                return
            
            self._add_job_log(job_id, "训练完成，开始评估")
            
            # 更新状态：评估中
            self._update_job_status(job_id, TrainingStatus.EVALUATING, 70.0)
            
            # 评估模型
            evaluation_result = self._evaluate_trained_model(
                model_name, training_level, training_result, config
            )
            
            self._add_job_log(job_id, f"评估完成: {evaluation_result.get('score', 'N/A')}")
            
            # 更新状态：部署中
            self._update_job_status(job_id, TrainingStatus.DEPLOYING, 90.0)
            self._add_job_log(job_id, "开始部署训练后的模型")
            
            # 部署模型
            deployment_result = self._deploy_trained_model(
                model_name, training_level, training_result, evaluation_result, config
            )
            
            # 更新状态：完成
            final_result = {
                "training": training_result,
                "evaluation": evaluation_result,
                "deployment": deployment_result,
                "data_preparation": data_result
            }
            
            self._update_job_status(
                job_id, TrainingStatus.COMPLETED, 100.0, final_result
            )
            self._add_job_log(job_id, "训练任务完成")
            
            # 更新训练历史
            self._record_training_history(model_name, job_info, final_result)
            self.last_training_time[model_name] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"训练任务执行失败: {e}")
            self._update_job_status(job_id, TrainingStatus.FAILED, 0.0, {"error": str(e)})
    
    def _perform_training(
        self,
        model_name: str,
        training_level: TrainingLevel,
        data_result: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行实际训练
        
        Args:
            model_name: 模型名称
            training_level: 训练级别
            data_result: 数据准备结果
            config: 训练配置
        
        Returns:
            训练结果
        """
        # 检查是否为本地模型
        local_models = ["local-llama", "local-qwen", "local-phi3", "step-3.5-flash"]
        is_local_model = model_name in local_models
        
        if is_local_model:
            # 尝试获取模型适配器
            adapter = self._get_model_adapter(model_name)
            
            if adapter:
                self.logger.info(f"为本地模型 {model_name} 获取到适配器，开始模拟训练")
                
                # 模拟训练逻辑 - 在实际实现中，这里应该：
                # 1. 准备训练数据
                # 2. 调用本地训练框架（如LoRA微调、P-Tuning等）
                # 3. 保存训练后的模型
                # 4. 更新模型配置
                
                # 根据训练级别决定训练时间
                training_times = {
                    TrainingLevel.QUICK_FINETUNE: 5.0,
                    TrainingLevel.DOMAIN_ADAPTATION: 30.0,
                    TrainingLevel.FULL_TRAINING: 120.0
                }
                
                training_time = training_times.get(training_level, 10.0)
                self.logger.info(f"模拟训练 {model_name} ({training_level.value})，耗时 {training_time} 秒")
                time.sleep(min(training_time, 5.0))  # 测试时最多等待5秒
                
                # 记录适配器信息用于调试
                adapter_info = {
                    "provider": adapter.provider.value,
                    "model_name": adapter.model_name,
                    "base_url": adapter.base_url,
                    "capabilities": [c.value for c in adapter.capabilities] if adapter.capabilities else []
                }
                
                return {
                    "success": True,
                    "training_level": training_level.value,
                    "model_name": model_name,
                    "trained_model_path": f"models/{model_name}_trained_{int(time.time())}",
                    "training_time_seconds": training_time,
                    "parameters_trained": "模拟参数（实际应包含LoRA权重等）",
                    "loss_history": [0.5, 0.3, 0.2, 0.15, 0.12],
                    "checkpoints": [],
                    "adapter_info": adapter_info,
                    "training_method": "local_adapter_simulation",
                    "data_samples": data_result.get("processed_count", 0)
                }
            else:
                self.logger.warning(f"无法为本地模型 {model_name} 获取适配器，使用通用模拟训练")
                # 继续通用模拟训练流程
        
        # 通用模拟训练（非本地模型或适配器不可用）
        training_times = {
            TrainingLevel.QUICK_FINETUNE: 2.0,
            TrainingLevel.DOMAIN_ADAPTATION: 10.0,
            TrainingLevel.FULL_TRAINING: 30.0
        }
        
        training_time = training_times.get(training_level, 5.0)
        self.logger.info(f"模拟训练 {model_name} ({training_level.value})，耗时 {training_time} 秒")
        time.sleep(min(training_time, 2.0))  # 测试时最多等待2秒
        
        return {
            "success": True,
            "training_level": training_level.value,
            "model_name": model_name,
            "trained_model_path": f"models/{model_name}_trained_{int(time.time())}",
            "training_time_seconds": training_time,
            "parameters_trained": "模拟参数",
            "loss_history": [0.5, 0.3, 0.2, 0.15, 0.12],
            "checkpoints": [],
            "data_samples": data_result.get("processed_count", 0)
        }
    
    def _evaluate_trained_model(
        self,
        model_name: str,
        training_level: TrainingLevel,
        training_result: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估训练后的模型
        
        Args:
            model_name: 模型名称
            training_level: 训练级别
            training_result: 训练结果
            config: 配置
        
        Returns:
            评估结果
        """
        # 实际评估逻辑应在此实现
        # 这里返回模拟结果
        
        return {
            "success": True,
            "model_name": model_name,
            "evaluation_score": 0.85,  # 模拟得分
            "improvement": 0.15,  # 改进幅度
            "metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85
            },
            "test_samples": 50,
            "evaluation_time_seconds": 1.0
        }
    
    def _deploy_trained_model(
        self,
        model_name: str,
        training_level: TrainingLevel,
        training_result: Dict[str, Any],
        evaluation_result: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        部署训练后的模型
        
        Args:
            model_name: 模型名称
            training_level: 训练级别
            training_result: 训练结果
            evaluation_result: 评估结果
            config: 配置
        
        Returns:
            部署结果
        """
        # 实际部署逻辑应在此实现
        # 这里返回模拟结果
        
        # 注册到持续学习系统
        try:
            # 创建模拟模型组件
            class MockTrainedModel:
                def predict(self, data):
                    return {"success": True, "content": "模拟响应"}
                
                def train(self, data, labels=None):
                    return {"success": True}
            
            model_component = MockTrainedModel()
            
            self.continuous_learning.register_model(
                f"{model_name}_trained",
                model_component,
                {
                    "training_level": training_level.value,
                    "original_model": model_name,
                    "evaluation_score": evaluation_result.get("evaluation_score", 0.0)
                }
            )
            
            # 调度定期重新训练
            self.continuous_learning.schedule_training(
                f"{model_name}_trained",
                schedule_type="monthly",
                min_samples=100
            )
            
            return {
                "success": True,
                "deployed_model_name": f"{model_name}_trained",
                "deployment_time": datetime.now().isoformat(),
                "registered_in_cls": True,
                "scheduled_retraining": True
            }
            
        except Exception as e:
            self.logger.error(f"模型部署失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "deployed_model_name": None
            }
    
    def _update_job_status(
        self,
        job_id: str,
        status: TrainingStatus,
        progress: float,
        result: Optional[Dict[str, Any]] = None
    ):
        """更新任务状态"""
        with self.lock:
            if job_id in self.training_jobs:
                job_info = self.training_jobs[job_id]
                job_info["status"] = status
                job_info["progress"] = progress
                
                if result:
                    job_info["result"] = result
                
                if status == TrainingStatus.COMPLETED or status == TrainingStatus.FAILED:
                    job_info["end_time"] = datetime.now().isoformat()
    
    def _add_job_log(self, job_id: str, message: str):
        """添加任务日志"""
        with self.lock:
            if job_id in self.training_jobs:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                }
                self.training_jobs[job_id]["logs"].append(log_entry)
    
    def _record_training_history(
        self,
        model_name: str,
        job_info: Dict[str, Any],
        final_result: Dict[str, Any]
    ):
        """记录训练历史"""
        history_entry = {
            "job_id": job_info["job_id"],
            "training_level": job_info["training_level"],
            "start_time": job_info["start_time"],
            "end_time": job_info.get("end_time"),
            "status": job_info["status"],
            "result": final_result
        }
        
        if model_name not in self.model_training_history:
            self.model_training_history[model_name] = []
        
        self.model_training_history[model_name].append(history_entry)
        
        # 限制历史记录数量
        if len(self.model_training_history[model_name]) > 20:
            self.model_training_history[model_name] = self.model_training_history[model_name][-20:]
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self.lock:
            return self.training_jobs.get(job_id)
    
    def get_training_history(self, model_name: str) -> List[Dict[str, Any]]:
        """获取训练历史"""
        with self.lock:
            return self.model_training_history.get(model_name, [])
    
    def auto_training_loop(self):
        """自动训练循环（应作为后台服务运行）"""
        if not self.enable_auto_training:
            return
        
        self.logger.info("启动自动训练循环")
        
        while True:
            try:
                # 检查所有本地模型
                local_models = ["step-3.5-flash", "local-llama", "local-qwen", "local-phi3"]
                
                for model_name in local_models:
                    try:
                        needs_training, check_result = self.check_training_needed(model_name)
                        
                        if needs_training:
                            self.logger.info(f"自动触发训练: {model_name}, 原因: {check_result['reason']}")
                            
                            # 启动训练任务
                            result = self.start_training_job(
                                model_name=model_name,
                                training_level=check_result["recommended_level"]
                            )
                            
                            if result.get("success"):
                                self.logger.info(f"训练任务已创建: {result['job_id']}")
                        
                    except Exception as e:
                        self.logger.error(f"检查模型 {model_name} 训练需求失败: {e}")
                
                # 每小时检查一次
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"自动训练循环异常: {e}")
                time.sleep(300)  # 异常后等待5分钟


# 全局单例
_training_orchestrator: Optional[LLMTrainingOrchestrator] = None


def get_training_orchestrator(config: Optional[Dict[str, Any]] = None) -> LLMTrainingOrchestrator:
    """
    获取训练流程管理器单例
    
    Args:
        config: 配置字典
    
    Returns:
        LLMTrainingOrchestrator 实例
    """
    global _training_orchestrator
    
    if _training_orchestrator is None:
        _training_orchestrator = LLMTrainingOrchestrator(
            storage_path=config.get("storage_path") if config else None,
            enable_auto_training=config.get("enable_auto_training", True) if config else True,
            training_thresholds=config.get("training_thresholds") if config else None
        )
    
    return _training_orchestrator