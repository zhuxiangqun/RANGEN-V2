#!/usr/bin/env python3
"""
Evolution Engine Hook - 请求级轻量进化钩子
用于在 UnifiedResearchSystem / ChiefAgent 执行结束后进行轻量反思和模式记录
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EvolutionHook:
    """进化引擎轻量钩子 - 用于请求级的轻量反思和模式记录"""
    
    def __init__(self, enabled: bool = None, frequency: str = "always"):
        """
        初始化进化钩子
        
        Args:
            enabled: 是否启用（None 则从环境变量读取）
            frequency: 触发频率 ("always" | "on_error" | "periodic")
        """
        # 从环境变量读取配置
        if enabled is None:
            enabled = os.getenv("RANGEN_EVOLUTION_HOOK_ENABLED", "false").lower() == "true"
        
        if frequency not in ("always", "on_error", "periodic"):
            frequency = os.getenv("RANGEN_EVOLUTION_HOOK_FREQUENCY", "on_error")
        
        self.enabled = enabled
        self.frequency = frequency
        
        # 周期性触发计数器
        self._call_counter = 0
        self._periodic_interval = int(os.getenv("RANGEN_EVOLUTION_HOOK_PERIODIC_INTERVAL", "10"))
        
        # 存储轻量模式
        self._pattern_store: Dict[str, Any] = {}
        
        # 是否已初始化完整 EvolutionEngine
        self._evolution_engine = None
        
        logger.info(f"🧬 EvolutionHook 初始化完成: enabled={enabled}, frequency={frequency}")
    
    def _get_evolution_engine(self):
        """懒加载完整 EvolutionEngine"""
        if self._evolution_engine is None and self.enabled:
            try:
                from src.evolution.engine import EvolutionEngine
                self._evolution_engine = EvolutionEngine()
                logger.info("✅ EvolutionEngine 已加载")
            except Exception as e:
                logger.warning(f"⚠️ EvolutionEngine 加载失败: {e}")
                self._evolution_engine = False  # 标记加载失败
        return self._evolution_engine if self._evolution_engine else None
    
    def should_trigger(self, success: bool = True) -> bool:
        """判断是否应该触发进化钩子"""
        if not self.enabled:
            return False
        
        if self.frequency == "always":
            return True
        elif self.frequency == "on_error":
            return not success
        elif self.frequency == "periodic":
            self._call_counter += 1
            return self._call_counter % self._periodic_interval == 0
        
        return False
    
    async def trigger(
        self,
        query: str,
        result: Any,
        success: bool = True,
        execution_time: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        触发进化钩子 - 轻量反思和模式记录
        
        Args:
            query: 用户查询
            result: 执行结果
            success: 是否成功
            execution_time: 执行时间
            metadata: 额外元数据
            
        Returns:
            进化结果（如果有）
        """
        if not self.should_trigger(success):
            return None
        
        try:
            # 1. 记录轻量模式（不调用完整 EvolutionEngine）
            pattern_key = self._extract_pattern_key(query)
            self._pattern_store[pattern_key] = {
                "query": query,
                "success": success,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # 2. 如果完整 EvolutionEngine 可用，尝试调用
            evolution_engine = self._get_evolution_engine()
            if evolution_engine and hasattr(evolution_engine, 'record_execution'):
                # 调用完整的进化引擎记录
                evolution_record = await evolution_engine.record_execution(
                    query=query,
                    result=result,
                    success=success,
                    execution_time=execution_time,
                    metadata=metadata
                )
                logger.info(f"🧬 进化引擎记录完成: {pattern_key}")
                return evolution_record
            
            logger.debug(f"🧬 轻量模式记录完成: {pattern_key}")
            return {"status": "lightweight_record", "pattern_key": pattern_key}
            
        except Exception as e:
            logger.error(f"❌ EvolutionHook 触发失败: {e}")
            return None
    
    def _extract_pattern_key(self, query: str) -> str:
        """提取模式键 - 用于去重和存储"""
        # 简单实现：使用查询的前50个字符作为键
        return f"pattern_{hash(query[:50])}"
    
    def get_patterns(self) -> Dict[str, Any]:
        """获取已记录的模式"""
        return self._pattern_store.copy()
    
    def clear_patterns(self):
        """清除已记录的模式"""
        self._pattern_store.clear()
        logger.info("🧬 模式存储已清除")


# 全局单例
_evolution_hook: Optional[EvolutionHook] = None


def get_evolution_hook() -> EvolutionHook:
    """获取全局 EvolutionHook 实例"""
    global _evolution_hook
    if _evolution_hook is None:
        _evolution_hook = EvolutionHook()
    return _evolution_hook


def create_evolution_hook(
    enabled: bool = None,
    frequency: str = "on_error"
) -> EvolutionHook:
    """创建新的 EvolutionHook 实例"""
    return EvolutionHook(enabled=enabled, frequency=frequency)
