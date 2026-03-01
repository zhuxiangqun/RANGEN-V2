#!/usr/bin/env python3
"""
ML/DL模型持久化管理器
解决ML和DL模型重启后丢失的问题
"""

import json
import os
import pickle
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class MLDLPersistenceManager:
    """ML/DL模型持久化管理器"""
    
    def __init__(self, persistence_dir: str = "ml_dl_persistence"):
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(exist_ok=True)
        
        # 子目录
        self.models_dir = self.persistence_dir / "models"
        self.learning_dir = self.persistence_dir / "learning"
        self.agents_dir = self.persistence_dir / "agents"
        self.synergy_dir = self.persistence_dir / "synergy"
        
        # 创建子目录
        for dir_path in [self.models_dir, self.learning_dir, self.agents_dir, self.synergy_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("ML/DL持久化管理器初始化完成")
    
    def save_ml_model(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """保存ML模型"""
        try:
            model_file = self.models_dir / f"{model_id}_ml.json"
            
            # 准备保存数据
            save_data = {
                "model_id": model_id,
                "model_type": "ml",
                "model_data": model_data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 处理numpy数组
            save_data = self._serialize_numpy_arrays(save_data)
            
            # 保存到文件
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"ML模型保存成功: {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"ML模型保存失败: {e}")
            return False
    
    def load_ml_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """加载ML模型"""
        try:
            model_file = self.models_dir / f"{model_id}_ml.json"
            
            if not model_file.exists():
                self.logger.warning(f"ML模型文件不存在: {model_id}")
                return None
            
            with open(model_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 恢复numpy数组
            save_data = self._deserialize_numpy_arrays(save_data)
            
            self.logger.info(f"ML模型加载成功: {model_id}")
            return save_data.get("model_data")
            
        except Exception as e:
            self.logger.error(f"ML模型加载失败: {e}")
            return None
    
    def save_dl_model(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """保存DL模型"""
        try:
            model_file = self.models_dir / f"{model_id}_dl.pkl"
            
            # 准备保存数据
            save_data = {
                "model_id": model_id,
                "model_type": "dl",
                "model_data": model_data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 使用pickle保存（支持numpy数组和复杂对象）
            with open(model_file, 'wb') as f:
                pickle.dump(save_data, f)
            
            self.logger.info(f"DL模型保存成功: {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"DL模型保存失败: {e}")
            return False
    
    def load_dl_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """加载DL模型"""
        try:
            model_file = self.models_dir / f"{model_id}_dl.pkl"
            
            if not model_file.exists():
                self.logger.warning(f"DL模型文件不存在: {model_id}")
                return None
            
            with open(model_file, 'rb') as f:
                save_data = pickle.load(f)
            
            self.logger.info(f"DL模型加载成功: {model_id}")
            return save_data.get("model_data")
            
        except Exception as e:
            self.logger.error(f"DL模型加载失败: {e}")
            return None
    
    def save_learning_state(self, agent_name: str, learning_data: Dict[str, Any]) -> bool:
        """保存学习状态"""
        try:
            learning_file = self.learning_dir / f"{agent_name}_learning.json"
            
            save_data = {
                "agent_name": agent_name,
                "learning_data": learning_data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 处理numpy数组
            save_data = self._serialize_numpy_arrays(save_data)
            
            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"学习状态保存成功: {agent_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"学习状态保存失败: {e}")
            return False
    
    def load_learning_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """加载学习状态"""
        try:
            learning_file = self.learning_dir / f"{agent_name}_learning.json"
            
            if not learning_file.exists():
                self.logger.warning(f"学习状态文件不存在: {agent_name}")
                return None
            
            with open(learning_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 恢复numpy数组
            save_data = self._deserialize_numpy_arrays(save_data)
            
            self.logger.info(f"学习状态加载成功: {agent_name}")
            return save_data.get("learning_data")
            
        except Exception as e:
            self.logger.error(f"学习状态加载失败: {e}")
            return None
    
    def save_agent_state(self, agent_name: str, agent_data: Dict[str, Any]) -> bool:
        """保存智能体状态"""
        try:
            agent_file = self.agents_dir / f"{agent_name}_state.json"
            
            save_data = {
                "agent_name": agent_name,
                "agent_data": agent_data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 处理numpy数组
            save_data = self._serialize_numpy_arrays(save_data)
            
            with open(agent_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"智能体状态保存成功: {agent_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"智能体状态保存失败: {e}")
            return False
    
    def load_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """加载智能体状态"""
        try:
            agent_file = self.agents_dir / f"{agent_name}_state.json"
            
            if not agent_file.exists():
                self.logger.warning(f"智能体状态文件不存在: {agent_name}")
                return None
            
            with open(agent_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 恢复numpy数组
            save_data = self._deserialize_numpy_arrays(save_data)
            
            self.logger.info(f"智能体状态加载成功: {agent_name}")
            return save_data.get("agent_data")
            
        except Exception as e:
            self.logger.error(f"智能体状态加载失败: {e}")
            return None
    
    def save_synergy_state(self, synergy_data: Dict[str, Any]) -> bool:
        """保存ML/RL协同状态"""
        try:
            synergy_file = self.synergy_dir / "ml_rl_synergy.json"
            
            save_data = {
                "synergy_data": synergy_data,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            # 处理numpy数组
            save_data = self._serialize_numpy_arrays(save_data)
            
            with open(synergy_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("ML/RL协同状态保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"ML/RL协同状态保存失败: {e}")
            return False
    
    def load_synergy_state(self) -> Optional[Dict[str, Any]]:
        """加载ML/RL协同状态"""
        try:
            synergy_file = self.synergy_dir / "ml_rl_synergy.json"
            
            if not synergy_file.exists():
                self.logger.warning("ML/RL协同状态文件不存在")
                return None
            
            with open(synergy_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 恢复numpy数组
            save_data = self._deserialize_numpy_arrays(save_data)
            
            self.logger.info("ML/RL协同状态加载成功")
            return save_data.get("synergy_data")
            
        except Exception as e:
            self.logger.error(f"ML/RL协同状态加载失败: {e}")
            return None
    
    def _serialize_numpy_arrays(self, data: Any) -> Any:
        """序列化numpy数组"""
        if isinstance(data, np.ndarray):
            return {
                "__numpy_array__": True,
                "data": data.tolist(),
                "dtype": str(data.dtype),
                "shape": data.shape
            }
        elif isinstance(data, dict):
            return {k: self._serialize_numpy_arrays(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_numpy_arrays(item) for item in data]
        else:
            return data
    
    def _deserialize_numpy_arrays(self, data: Any) -> Any:
        """反序列化numpy数组"""
        if isinstance(data, dict) and data.get("__numpy_array__"):
            return np.array(data["data"], dtype=data["dtype"]).reshape(data["shape"])
        elif isinstance(data, dict):
            return {k: self._deserialize_numpy_arrays(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deserialize_numpy_arrays(item) for item in data]
        else:
            return data
    
    def get_persistence_summary(self) -> Dict[str, Any]:
        """获取持久化摘要"""
        try:
            summary = {
                "models": {
                    "ml_models": len(list(self.models_dir.glob("*_ml.json"))),
                    "dl_models": len(list(self.models_dir.glob("*_dl.pkl")))
                },
                "learning_states": len(list(self.learning_dir.glob("*_learning.json"))),
                "agent_states": len(list(self.agents_dir.glob("*_state.json"))),
                "synergy_state": self.synergy_dir.joinpath("ml_rl_synergy.json").exists(),
                "total_files": len(list(self.persistence_dir.rglob("*")))
            }
            return summary
        except Exception as e:
            self.logger.error(f"获取持久化摘要失败: {e}")
            return {"error": str(e)}
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """清理旧文件"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for file_path in self.persistence_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            self.logger.info(f"清理了 {cleaned_count} 个旧文件")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理旧文件失败: {e}")
            return 0


# 全局实例
_persistence_manager = None

def get_ml_dl_persistence_manager() -> MLDLPersistenceManager:
    """获取ML/DL持久化管理器实例"""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = MLDLPersistenceManager()
    return _persistence_manager

# 便捷函数
def save_ml_model(model_id: str, model_data: Dict[str, Any]) -> bool:
    """保存ML模型"""
    return get_ml_dl_persistence_manager().save_ml_model(model_id, model_data)

def load_ml_model(model_id: str) -> Optional[Dict[str, Any]]:
    """加载ML模型"""
    return get_ml_dl_persistence_manager().load_ml_model(model_id)

def save_dl_model(model_id: str, model_data: Dict[str, Any]) -> bool:
    """保存DL模型"""
    return get_ml_dl_persistence_manager().save_dl_model(model_id, model_data)

def load_dl_model(model_id: str) -> Optional[Dict[str, Any]]:
    """加载DL模型"""
    return get_ml_dl_persistence_manager().load_dl_model(model_id)

def save_learning_state(agent_name: str, learning_data: Dict[str, Any]) -> bool:
    """保存学习状态"""
    return get_ml_dl_persistence_manager().save_learning_state(agent_name, learning_data)

def load_learning_state(agent_name: str) -> Optional[Dict[str, Any]]:
    """加载学习状态"""
    return get_ml_dl_persistence_manager().load_learning_state(agent_name)
