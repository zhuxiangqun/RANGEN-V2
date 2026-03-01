"""
持续学习系统 - 模型注册和训练调度

功能：
- 模型注册和训练调度
- 增量训练
- 版本管理
- A/B测试
- 逐步部署
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ContinuousLearningSystem:
    """持续学习系统
    
    管理ML模型的持续学习：
    - 模型注册和训练调度
    - 增量训练
    - 版本管理
    - A/B测试
    - 逐步部署
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化持续学习系统
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # 注册的模型
        self.registered_models = {}
        
        # 训练调度
        self.training_schedule = {}
        
        # 模型版本
        self.model_versions = {}
        
        # A/B测试配置
        self.ab_tests = {}
        
        # 存储路径
        self.storage_path = Path(self.config.get("storage_path", "data/ml_models"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def register_model(
        self,
        model_name: str,
        model_component: Any,
        training_config: Dict[str, Any]
    ) -> bool:
        """注册模型
        
        Args:
            model_name: 模型名称
            model_component: 模型组件（BaseMLComponent或BaseRLComponent）
            training_config: 训练配置
            
        Returns:
            是否注册成功
        """
        try:
            self.registered_models[model_name] = {
                "component": model_component,
                "config": training_config,
                "registered_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "status": "registered",
            }
            
            self.logger.info(f"✅ 模型已注册: {model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"模型注册失败: {e}")
            return False
    
    def schedule_training(
        self,
        model_name: str,
        schedule_type: str = "weekly",
        min_samples: int = 100
    ) -> bool:
        """调度训练
        
        Args:
            model_name: 模型名称
            schedule_type: 调度类型（"daily", "weekly", "monthly", "on_demand"）
            min_samples: 最小样本数
            
        Returns:
            是否调度成功
        """
        try:
            if model_name not in self.registered_models:
                self.logger.warning(f"模型未注册: {model_name}")
                return False
            
            self.training_schedule[model_name] = {
                "schedule_type": schedule_type,
                "min_samples": min_samples,
                "last_training": None,
                "next_training": None,
            }
            
            self.logger.info(f"✅ 训练已调度: {model_name} ({schedule_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"训练调度失败: {e}")
            return False
    
    def incremental_train(
        self,
        model_name: str,
        new_data: List[Any],
        labels: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """增量训练
        
        Args:
            model_name: 模型名称
            new_data: 新数据
            labels: 标签（如果是监督学习）
            
        Returns:
            训练结果
        """
        try:
            if model_name not in self.registered_models:
                return {
                    "success": False,
                    "error": f"模型未注册: {model_name}"
                }
            
            model_info = self.registered_models[model_name]
            model_component = model_info["component"]
            
            # 检查是否有train方法
            if not hasattr(model_component, "train"):
                return {
                    "success": False,
                    "error": "模型组件不支持训练"
                }
            
            # 执行增量训练
            # 对于RL组件，使用特殊的训练方法
            if hasattr(model_component, 'train') and callable(getattr(model_component, 'train')):
                if hasattr(model_component, 'replay_buffer'):
                    # RL组件：使用train方法（从replay_buffer训练）
                    training_result = model_component.train()
                else:
                    # ML组件：使用标准训练方法
                    training_result = model_component.train(new_data, labels)
            else:
                return {
                    "success": False,
                    "error": "模型组件不支持训练"
                }
            
            # 更新模型版本
            current_version = model_info["version"]
            new_version = self._increment_version(current_version)
            model_info["version"] = new_version
            model_info["last_training"] = datetime.now().isoformat()
            
            # 保存模型版本
            self._save_model_version(model_name, new_version, training_result)
            
            self.logger.info(f"✅ 增量训练完成: {model_name} -> {new_version}")
            
            return {
                "success": True,
                "version": new_version,
                "training_result": training_result,
            }
            
        except Exception as e:
            self.logger.error(f"增量训练失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_ab_test(
        self,
        model_name: str,
        variant_a: str,
        variant_b: str,
        traffic_split: float = 0.5
    ) -> bool:
        """创建A/B测试
        
        Args:
            model_name: 模型名称
            variant_a: 变体A版本
            variant_b: 变体B版本
            traffic_split: 流量分割比例（0-1，0.5表示50/50）
            
        Returns:
            是否创建成功
        """
        try:
            test_id = f"{model_name}_ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.ab_tests[test_id] = {
                "model_name": model_name,
                "variant_a": variant_a,
                "variant_b": variant_b,
                "traffic_split": traffic_split,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "metrics": {
                    "variant_a": {"requests": 0, "success": 0, "avg_confidence": 0.0},
                    "variant_b": {"requests": 0, "success": 0, "avg_confidence": 0.0},
                }
            }
            
            self.logger.info(f"✅ A/B测试已创建: {test_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"A/B测试创建失败: {e}")
            return False
    
    def get_model_version(self, model_name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取模型版本
        
        Args:
            model_name: 模型名称
            version: 版本号（如果为None，返回最新版本）
            
        Returns:
            模型版本信息
        """
        if model_name not in self.registered_models:
            return None
        
        model_info = self.registered_models[model_name]
        
        if version:
            # 返回指定版本
            version_key = f"{model_name}_{version}"
            return self.model_versions.get(version_key)
        else:
            # 返回最新版本
            return {
                "version": model_info["version"],
                "registered_at": model_info["registered_at"],
                "last_training": model_info.get("last_training"),
            }
    
    def list_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """列出模型的所有版本
        
        Args:
            model_name: 模型名称
            
        Returns:
            版本列表
        """
        versions = []
        
        # 从model_versions中查找
        for version_key, version_info in self.model_versions.items():
            if version_key.startswith(f"{model_name}_"):
                versions.append({
                    "version": version_info.get("version"),
                    "created_at": version_info.get("created_at"),
                    "training_result": version_info.get("training_result", {})
                })
        
        # 按创建时间排序
        versions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return versions
    
    def rollback_model(self, model_name: str, target_version: str) -> bool:
        """回滚模型到指定版本
        
        Args:
            model_name: 模型名称
            target_version: 目标版本号
            
        Returns:
            是否回滚成功
        """
        try:
            if model_name not in self.registered_models:
                self.logger.error(f"模型未注册: {model_name}")
                return False
            
            version_key = f"{model_name}_{target_version}"
            if version_key not in self.model_versions:
                self.logger.error(f"版本不存在: {target_version}")
                return False
            
            # 获取目标版本信息
            target_version_info = self.model_versions[version_key]
            
            # 更新模型信息
            model_info = self.registered_models[model_name]
            model_info["version"] = target_version
            model_info["last_training"] = target_version_info.get("created_at")
            
            # 尝试加载目标版本的模型文件
            model_component = model_info["component"]
            model_file = self.storage_path / f"{model_name}_{target_version}.pkl"
            
            if model_file.exists():
                if hasattr(model_component, 'load_model'):
                    model_component.load_model(str(model_file))
                    self.logger.info(f"✅ 模型已回滚到版本: {target_version}")
                    return True
                else:
                    self.logger.warning(f"⚠️ 模型组件不支持加载")
            else:
                self.logger.warning(f"⚠️ 模型文件不存在: {model_file}")
            
            # 即使文件不存在，也更新版本信息
            self.logger.info(f"✅ 模型版本信息已回滚到: {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"回滚失败: {e}")
            return False
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """获取A/B测试结果
        
        Args:
            test_id: 测试ID
            
        Returns:
            测试结果字典
        """
        return self.ab_tests.get(test_id)
    
    def update_ab_test_metrics(self, test_id: str, variant: str, success: bool, confidence: float = 0.0):
        """更新A/B测试指标
        
        Args:
            test_id: 测试ID
            variant: 变体（"variant_a"或"variant_b"）
            success: 是否成功
            confidence: 置信度
        """
        if test_id not in self.ab_tests:
            self.logger.warning(f"A/B测试不存在: {test_id}")
            return
        
        test = self.ab_tests[test_id]
        if variant not in test["metrics"]:
            self.logger.warning(f"变体不存在: {variant}")
            return
        
        metrics = test["metrics"][variant]
        metrics["requests"] = metrics.get("requests", 0) + 1
        if success:
            metrics["success"] = metrics.get("success", 0) + 1
        
        # 更新平均置信度
        current_avg = metrics.get("avg_confidence", 0.0)
        request_count = metrics.get("requests", 1)
        metrics["avg_confidence"] = (current_avg * (request_count - 1) + confidence) / request_count
    
    def get_ab_test_winner(self, test_id: str) -> Optional[str]:
        """获取A/B测试获胜者
        
        Args:
            test_id: 测试ID
            
        Returns:
            获胜变体（"variant_a"或"variant_b"），如果数据不足返回None
        """
        if test_id not in self.ab_tests:
            return None
        
        test = self.ab_tests[test_id]
        metrics_a = test["metrics"]["variant_a"]
        metrics_b = test["metrics"]["variant_b"]
        
        # 检查是否有足够的数据
        min_requests = 100  # 最小请求数
        if metrics_a["requests"] < min_requests or metrics_b["requests"] < min_requests:
            return None
        
        # 计算成功率
        success_rate_a = metrics_a["success"] / metrics_a["requests"] if metrics_a["requests"] > 0 else 0
        success_rate_b = metrics_b["success"] / metrics_b["requests"] if metrics_b["requests"] > 0 else 0
        
        # 考虑置信度
        score_a = success_rate_a * 0.7 + metrics_a["avg_confidence"] * 0.3
        score_b = success_rate_b * 0.7 + metrics_b["avg_confidence"] * 0.3
        
        if score_a > score_b:
            return "variant_a"
        elif score_b > score_a:
            return "variant_b"
        else:
            return None  # 平局
    
    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split(".")
            if len(parts) == 3:
                major, minor, patch = parts
                patch = str(int(patch) + 1)
                return f"{major}.{minor}.{patch}"
            else:
                return "1.0.1"
        except Exception:
            return "1.0.1"
    
    def _save_model_version(
        self,
        model_name: str,
        version: str,
        training_result: Dict[str, Any]
    ):
        """保存模型版本"""
        try:
            version_key = f"{model_name}_{version}"
            self.model_versions[version_key] = {
                "model_name": model_name,
                "version": version,
                "training_result": training_result,
                "created_at": datetime.now().isoformat(),
            }
            
            # 保存到文件
            version_file = self.storage_path / f"{version_key}.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_versions[version_key], f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"保存模型版本失败: {e}")
    
    def get_registered_models(self) -> List[str]:
        """获取所有注册的模型名称"""
        return list(self.registered_models.keys())
    
    def get_training_schedule(self) -> Dict[str, Any]:
        """获取训练调度信息"""
        return self.training_schedule.copy()
    
    def _get_historical_training_data(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取历史训练数据（用于增量学习）"""
        try:
            # 尝试从存储路径加载历史数据
            historical_file = self.storage_path / f"{model_name}_training_data.json"
            if historical_file.exists():
                import json
                with open(historical_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.debug(f"无法加载历史训练数据: {e}")
        return None
    
    def _save_training_data(self, model_name: str, data: List[Any], labels: Optional[List[Any]] = None):
        """保存训练数据（用于增量学习）"""
        try:
            historical_file = self.storage_path / f"{model_name}_training_data.json"
            historical_data = self._get_historical_training_data(model_name) or {"data": [], "labels": []}
            
            # 合并新数据
            historical_data["data"].extend(data)
            if labels:
                historical_data["labels"].extend(labels)
            
            # 限制历史数据大小（保留最近N条）
            max_history = self.config.get("max_training_history", 1000)
            if len(historical_data["data"]) > max_history:
                historical_data["data"] = historical_data["data"][-max_history:]
                if historical_data["labels"]:
                    historical_data["labels"] = historical_data["labels"][-max_history:]
            
            # 保存
            import json
            with open(historical_file, 'w', encoding='utf-8') as f:
                json.dump(historical_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.warning(f"保存训练数据失败: {e}")
    
    def auto_train_on_schedule(self) -> Dict[str, Any]:
        """根据调度自动训练模型（在线学习触发）"""
        results = {}
        
        for model_name, schedule_info in self.training_schedule.items():
            try:
                schedule_type = schedule_info.get("schedule_type", "on_demand")
                min_samples = schedule_info.get("min_samples", 100)
                
                # 检查是否满足训练条件
                if model_name not in self.registered_models:
                    continue
                
                model_info = self.registered_models[model_name]
                model_component = model_info["component"]
                
                # 对于RL组件，检查replay_buffer
                if hasattr(model_component, 'replay_buffer'):
                    buffer_size = len(model_component.replay_buffer)
                    if buffer_size >= min_samples:
                        training_result = model_component.train()
                        results[model_name] = training_result
                
                # 对于ML组件，检查是否有新数据
                # 🚀 新增：从DataCollectionPipeline获取新数据
                if hasattr(self, '_data_collection') and self._data_collection:
                    try:
                        # 提取训练数据
                        training_data_result = self._data_collection.extract_training_data_for_model(
                            model_name, 
                            max_samples=min_samples * 2  # 提取更多数据用于训练
                        )
                        
                        training_data = training_data_result.get("training_data", [])
                        labels = training_data_result.get("labels", [])
                        
                        if len(training_data) >= min_samples:
                            # 执行训练
                            training_result = model_component.train(training_data, labels if labels else None)
                            results[model_name] = training_result
                            self.logger.info(f"✅ 自动训练完成: {model_name} ({len(training_data)} 条数据)")
                        else:
                            self.logger.debug(f"数据不足，跳过训练: {model_name} ({len(training_data)} < {min_samples})")
                    except Exception as e:
                        self.logger.warning(f"从数据收集系统提取训练数据失败 ({model_name}): {e}")
                
            except Exception as e:
                self.logger.error(f"自动训练失败 ({model_name}): {e}")
                results[model_name] = {"success": False, "error": str(e)}
        
        return results
    
    def set_data_collection_pipeline(self, data_collection):
        """设置数据收集管道（用于自动训练）"""
        self._data_collection = data_collection
        self.logger.info("✅ 数据收集管道已连接到持续学习系统")

