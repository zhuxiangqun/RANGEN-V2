#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推理引擎实例池
提供推理引擎实例的复用，避免重复初始化LLM模型
"""

import logging
import threading
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ReasoningEnginePool:
    """推理引擎实例池 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化实例池"""
        if self._initialized:
            return
        
        self._pool: list = []
        self._pool_lock = threading.RLock()
        self._max_size = 5  # 最大池大小（可配置）
        self._min_size = 1  # 最小池大小
        self._created_count = 0
        self._discarded_count = 0  # 🚀 新增：被丢弃的实例数（池满时）
        self._in_use: set = set()  # 正在使用的实例ID集合
        self._initialized = True
        
        # 从环境变量读取配置
        import os
        self._max_size = int(os.getenv('REASONING_ENGINE_POOL_SIZE', '5'))
        self._min_size = int(os.getenv('REASONING_ENGINE_POOL_MIN_SIZE', '1'))
        
        # 🚀 新增：注册atexit处理，确保程序退出时自动清理资源
        import atexit
        atexit.register(self.clear_pool)
        
        logger.info(f"✅ 推理引擎实例池初始化完成: max_size={self._max_size}, min_size={self._min_size}")
    
    def _create_engine(self):
        """创建新的推理引擎实例"""
        try:
            from src.core.reasoning import RealReasoningEngine
            engine = RealReasoningEngine()
            self._created_count += 1
            logger.info(f"✅ 创建新的推理引擎实例 (总数: {self._created_count})")
            return engine
        except Exception as e:
            logger.error(f"❌ 创建推理引擎实例失败: {e}", exc_info=True)
            raise
    
    def _reset_engine_state(self, engine):
        """重置推理引擎状态（确保实例可复用）"""
        try:
            # 清理可能的状态数据
            if hasattr(engine, 'reasoning_history'):
                engine.reasoning_history.clear()
            if hasattr(engine, 'context_sessions'):
                engine.context_sessions.clear()
            # 注意：不清除学习数据，因为这是全局共享的
            return True
        except Exception as e:
            logger.warning(f"⚠️ 重置推理引擎状态失败: {e}")
            return False
    
    def get_engine(self) -> Any:
        """
        从池中获取推理引擎实例
        
        Returns:
            RealReasoningEngine: 推理引擎实例
        """
        with self._pool_lock:
            # 尝试从池中获取实例
            if self._pool:
                engine = self._pool.pop()
                engine_id = id(engine)
                self._in_use.add(engine_id)
                logger.info(f"🔍 从池中获取推理引擎实例 (池中剩余: {len(self._pool)}, 使用中: {len(self._in_use)})")
                return engine
            
            # 如果池为空，创建新实例
            engine = self._create_engine()
            engine_id = id(engine)
            self._in_use.add(engine_id)
            logger.info(f"🔍 创建新的推理引擎实例 (池中剩余: {len(self._pool)}, 使用中: {len(self._in_use)})")
            return engine
    
    def return_engine(self, engine: Any) -> bool:
        """
        将推理引擎实例返回到池中
        
        Args:
            engine: 推理引擎实例
            
        Returns:
            bool: 是否成功返回
        """
        if engine is None:
            return False
        
        engine_id = id(engine)
        
        with self._pool_lock:
            # 检查是否在使用的集合中（避免噪声，若不在则忽略）
            if engine_id not in self._in_use:
                logger.debug("ℹ️ 返回实例时未找到在用记录，可能重复归还或未标记获取，已忽略")
                return False
            
            # 从使用集合中移除
            self._in_use.discard(engine_id)
            
            # 重置实例状态
            self._reset_engine_state(engine)
            
            # 如果池未满，返回实例
            if len(self._pool) < self._max_size:
                self._pool.append(engine)
                logger.info(f"✅ 推理引擎实例已返回池中 (池中数量: {len(self._pool)}, 使用中: {len(self._in_use)})")
                return True
            else:
                # 池已满，不返回实例（让GC回收）
                self._discarded_count += 1  # 🚀 新增：记录丢弃的实例数
                logger.info(f"ℹ️ 推理引擎实例池已满，不返回实例 (池大小: {len(self._pool)}, 使用中: {len(self._in_use)}, 已丢弃: {self._discarded_count})")
                return False
    
    @contextmanager
    def acquire_engine(self):
        """
        上下文管理器：自动获取和返回推理引擎实例
        
        Usage:
            with pool.acquire_engine() as engine:
                result = engine.reason(query, context)
        """
        engine = None
        try:
            engine = self.get_engine()
            yield engine
        finally:
            if engine is not None:
                self.return_engine(engine)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取池的统计信息"""
        with self._pool_lock:
            total_active_instances = len(self._pool) + len(self._in_use)  # 🚀 修复：总活跃实例数（池中+使用中）
            utilization_rate = total_active_instances / self._max_size if self._max_size > 0 else 0.0  # 🚀 修复：利用率应该包括使用中的实例
            return {
                "pool_size": len(self._pool),
                "max_size": self._max_size,
                "min_size": self._min_size,
                "in_use_count": len(self._in_use),
                "created_count": self._created_count,
                "discarded_count": self._discarded_count,  # 🚀 新增：被丢弃的实例数
                "total_active_instances": total_active_instances,  # 🚀 新增：总活跃实例数
                "utilization_rate": utilization_rate
            }
    
    def clear_pool(self):
        """清空池中的所有实例"""
        with self._pool_lock:
            cleared_count = len(self._pool)
            in_use_count = len(self._in_use)
            self._pool.clear()
            self._in_use.clear()  # 🚀 新增：同时清空使用中的集合
            logger.info(f"🧹 清空推理引擎实例池: 清除了 {cleared_count} 个池中实例, {in_use_count} 个使用中实例")
            return cleared_count
    
    def __del__(self):
        """🚀 新增：程序退出时的最后保障，确保资源释放"""
        try:
            self.clear_pool()
        except Exception:
            pass  # 忽略异常，避免影响程序退出


# 全局单例实例
_pool_instance: Optional[ReasoningEnginePool] = None
_pool_lock = threading.Lock()


def get_reasoning_engine_pool() -> ReasoningEnginePool:
    """获取推理引擎实例池（单例）"""
    global _pool_instance
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                _pool_instance = ReasoningEnginePool()
    return _pool_instance


def get_reasoning_engine() -> Any:
    """
    便捷函数：从池中获取推理引擎实例
    
    Returns:
        RealReasoningEngine: 推理引擎实例
    """
    pool = get_reasoning_engine_pool()
    return pool.get_engine()


def return_reasoning_engine(engine: Any) -> bool:
    """
    便捷函数：将推理引擎实例返回到池中
    
    Args:
        engine: 推理引擎实例
        
    Returns:
        bool: 是否成功返回
    """
    pool = get_reasoning_engine_pool()
    return pool.return_engine(engine)

