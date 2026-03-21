#!/usr/bin/env python3
"""
执行时间预测模型
用于预测不同执行路径的执行时间，辅助智能协调层的资源分配
"""

import logging
import pickle
import os
from typing import Dict, Any, Optional, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import numpy as np

from .base_ml_component import BaseMLComponent

logger = logging.getLogger(__name__)


class ExecutionTimePredictor(BaseMLComponent):
    """执行时间预测模型
    
    预测不同执行路径（MAS、标准循环、传统流程、ReAct）的执行时间
    """
    
    def __init__(self):
        """初始化执行时间预测模型"""
        super().__init__()
        self.models = {}  # 每个执行路径一个模型
        self.scaler = StandardScaler()
        self.execution_paths = ['mas', 'standard_loop', 'traditional', 'react']
        self.model_name = "execution_time_predictor"
    
    def _extract_features(self, query: str, complexity: str, system_state: Dict[str, Any]) -> np.ndarray:
        """提取特征
        
        Args:
            query: 查询文本
            complexity: 复杂度级别
            system_state: 系统状态
            
        Returns:
            特征向量
        """
        query_lower = query.lower()
        words = query.split()
        
        # 复杂度编码
        complexity_encoding = {
            'simple': 1.0,
            'medium': 2.0,
            'complex': 3.0
        }
        
        features = [
            len(words),  # 查询长度
            len(query),  # 字符数
            complexity_encoding.get(complexity, 2.0),  # 复杂度
            system_state.get('load', 0.0) / 100.0,  # 系统负载（归一化）
            system_state.get('mas_healthy', True) * 1.0,  # MAS健康状态
            system_state.get('tools_available', True) * 1.0,  # 工具可用性
            query.count("'s "),  # 所有格数量
            query.count(" and "),  # 并列连接词
            query_lower.count("who"),  # who查询
            query_lower.count("what"),  # what查询
            query_lower.count("when"),  # when查询
            query_lower.count("where"),  # where查询
            query_lower.count("why"),  # why查询
            query_lower.count("how"),  # how查询
            query_lower.count("mother"),  # 关系查询
            query_lower.count("father"),  # 关系查询
            query_lower.count("wife"),  # 关系查询
            query_lower.count("husband"),  # 关系查询
        ]
        
        return np.array(features, dtype=np.float32)
    
    def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """训练执行时间预测模型
        
        Args:
            training_data: 训练数据，包含 'queries', 'complexities', 'system_states', 'execution_paths', 'execution_times'
            
        Returns:
            训练结果
        """
        try:
            queries = training_data.get('queries', [])
            complexities = training_data.get('complexities', [])
            system_states = training_data.get('system_states', [])
            execution_paths = training_data.get('execution_paths', [])
            execution_times = training_data.get('execution_times', [])
            
            if not queries or not execution_times:
                logger.warning("训练数据为空")
                return {"success": False, "error": "训练数据为空"}
            
            if len(queries) != len(execution_times):
                logger.warning("查询和执行时间数量不匹配")
                return {"success": False, "error": "数据数量不匹配"}
            
            # 为每个执行路径训练模型
            results = {}
            for path in self.execution_paths:
                # 筛选该路径的数据
                path_indices = [i for i, p in enumerate(execution_paths) if p == path]
                
                if len(path_indices) < 5:  # 至少需要5个样本
                    logger.warning(f"路径 {path} 的样本数不足（{len(path_indices)}），跳过训练")
                    continue
                
                # 提取特征
                X = np.array([
                    self._extract_features(
                        queries[i],
                        complexities[i] if i < len(complexities) else 'medium',
                        system_states[i] if i < len(system_states) else {}
                    )
                    for i in path_indices
                ])
                
                # 提取执行时间
                y = np.array([execution_times[i] for i in path_indices])
                
                # 标准化特征
                X_scaled = self.scaler.fit_transform(X)
                
                # 训练模型
                model = RandomForestRegressor(
                    n_estimators=50,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                model.fit(X_scaled, y)
                
                self.models[path] = model
                
                # 评估模型
                score = model.score(X_scaled, y)
                mae = np.mean(np.abs(model.predict(X_scaled) - y))
                
                results[path] = {
                    "samples": len(path_indices),
                    "r2_score": score,
                    "mae": mae
                }
                
                logger.info(f"✅ 路径 {path} 的执行时间预测模型训练完成，R²={score:.2%}, MAE={mae:.2f}秒")
            
            return {
                "success": True,
                "paths": results,
                "model_type": "RandomForestRegressor"
            }
            
        except Exception as e:
            logger.error(f"训练执行时间预测模型失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def predict(self, query: str, complexity: str, system_state: Dict[str, Any], execution_path: str) -> Dict[str, Any]:
        """预测执行时间
        
        Args:
            query: 查询文本
            complexity: 复杂度级别
            system_state: 系统状态
            execution_path: 执行路径（'mas', 'standard_loop', 'traditional', 'react'）
            
        Returns:
            预测结果，包含 'predicted_time' 和 'confidence'
        """
        try:
            if execution_path not in self.models:
                # 如果该路径的模型未训练，使用规则预测
                return self._predict_by_rules(query, complexity, system_state, execution_path)
            
            # 提取特征
            features = self._extract_features(query, complexity, system_state)
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # 预测
            model = self.models[execution_path]
            predicted_time = float(model.predict(features_scaled)[0])
            
            # 计算置信度（基于特征的重要性）
            # 简化：使用预测值的合理性作为置信度
            confidence = 0.7 if 0.1 <= predicted_time <= 300 else 0.5  # 合理范围：0.1-300秒
            
            return {
                "predicted_time": max(0.1, predicted_time),  # 至少0.1秒
                "confidence": confidence,
                "execution_path": execution_path
            }
            
        except Exception as e:
            logger.warning(f"执行时间预测失败: {e}，使用规则预测")
            return self._predict_by_rules(query, complexity, system_state, execution_path)
    
    def predict_all_paths(self, query: str, complexity: str, system_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """预测所有执行路径的执行时间
        
        Args:
            query: 查询文本
            complexity: 复杂度级别
            system_state: 系统状态
            
        Returns:
            所有路径的预测结果
        """
        results = {}
        for path in self.execution_paths:
            results[path] = self.predict(query, complexity, system_state, path)
        return results
    
    def _predict_by_rules(self, query: str, complexity: str, system_state: Dict[str, Any], execution_path: str) -> Dict[str, Any]:
        """基于规则的执行时间预测（回退方案）
        
        Args:
            query: 查询文本
            complexity: 复杂度级别
            system_state: 系统状态
            execution_path: 执行路径
            
        Returns:
            预测结果
        """
        # 基础时间（秒）
        base_times = {
            'simple': {'standard_loop': 0.5, 'traditional': 1.0, 'mas': 2.0, 'react': 1.5},
            'medium': {'standard_loop': 2.0, 'traditional': 3.0, 'mas': 5.0, 'react': 4.0},
            'complex': {'standard_loop': 5.0, 'traditional': 8.0, 'mas': 10.0, 'react': 12.0}
        }
        
        base_time = base_times.get(complexity, base_times['medium']).get(execution_path, 3.0)
        
        # 根据系统负载调整
        load = system_state.get('load', 0.0) / 100.0
        adjusted_time = base_time * (1.0 + load * 0.5)  # 负载高时增加50%
        
        # 根据查询长度调整
        query_length = len(query.split())
        if query_length > 30:
            adjusted_time *= 1.5
        elif query_length > 50:
            adjusted_time *= 2.0
        
        return {
            "predicted_time": adjusted_time,
            "confidence": 0.5,  # 规则预测的置信度较低
            "execution_path": execution_path
        }
    
    def _save_model_impl(self, filepath: str) -> bool:
        """保存模型实现
        
        Args:
            filepath: 保存路径
            
        Returns:
            是否成功
        """
        try:
            model_data = {
                'models': self.models,
                'scaler': self.scaler,
                'execution_paths': self.execution_paths
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            return True
        except Exception as e:
            logger.error(f"保存执行时间预测模型失败: {e}")
            return False
    
    def _load_model_impl(self, filepath: str) -> bool:
        """加载模型实现
        
        Args:
            filepath: 模型路径
            
        Returns:
            是否成功
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data.get('models', {})
            self.scaler = model_data.get('scaler', StandardScaler())
            self.execution_paths = model_data.get('execution_paths', ['mas', 'standard_loop', 'traditional', 'react'])
            
            return True
        except Exception as e:
            logger.error(f"加载执行时间预测模型失败: {e}")
            return False

