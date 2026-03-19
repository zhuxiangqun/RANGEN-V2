#!/usr/bin/env python3
"""
Central Hub - RANGEN 智能助手基盘核心

自动集成以下组件：
1. HandRegistry - Hands 自动发现与注册
2. IntentRouter - 意图识别与路由
3. TaskPlanner - 任务规划
4. IntentUnderstandingService - LLM 意图识别
5. TaskDecompositionEngine - 任务分解

使用方式：
```python
from src.hands.central_hub import CentralHub

hub = CentralHub()
result = hub.process("帮我收新邮件")
```
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    success: bool
    intent: Optional[str] = None
    hand: Optional[str] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    alternatives: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class CentralHub:
    """
    RANGEN 智能助手基盘核心
    
    统一管理意图识别、任务规划、Hands 执行。
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化"""
        if CentralHub._initialized:
            return
        
        self.logger = logger
        self.logger.info("=" * 50)
        self.logger.info("RANGEN 智能助手基盘初始化")
        self.logger.info("=" * 50)
        
        # 组件初始化
        self._registry = None
        self._intent_router = None
        self._task_planner = None
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "by_intent": {},
            "by_hand": {}
        }
        
        # 初始化组件
        self._initialize_components()
        
        CentralHub._initialized = True
        self.logger.info("✅ Central Hub 初始化完成")
    
    def _initialize_components(self):
        """初始化所有组件"""
        # 1. HandRegistry - 确保使用一致的导入路径
        self.logger.info("初始化 HandRegistry...")
        try:
            from src.hands.registry import HandRegistry
            from src.hands.base import BaseHand
            
            # 手动导入所有 Hand 文件以确保模块缓存正确
            import sys
            from pathlib import Path
            hands_dir = Path(__file__).parent
            
            for py_file in hands_dir.glob('*_hand.py'):
                if py_file.name.startswith('_'):
                    continue
                try:
                    module_name = py_file.stem
                    full_module_name = f"src.hands.{module_name}"
                    if module_name not in sys.modules:
                        import importlib.util
                        import importlib.machinery
                        loader = importlib.machinery.SourceFileLoader(
                            full_module_name, str(py_file)
                        )
                        sys.modules[full_module_name] = loader.load_module()
                except:
                    pass
            
            # 创建 registry
            self._registry = HandRegistry(auto_discover=True)
            self.logger.info(f"  ✅ 加载 {len(self._registry.hands)} 个 Hands")
        except Exception as e:
            self.logger.error(f"  ❌ HandRegistry 初始化失败: {e}")
            self._registry = None
        
        # 2. IntentRouter
        self.logger.info("初始化 IntentRouter...")
        try:
            from src.hands.intent_router import IntentRouter
            self._intent_router = IntentRouter(self._registry)
            self.logger.info("  ✅ IntentRouter 初始化成功")
        except Exception as e:
            self.logger.error(f"  ❌ IntentRouter 初始化失败: {e}")
            self._intent_router = None
        
        # 3. TaskPlanner
        self.logger.info("初始化 TaskPlanner...")
        try:
            from src.hands.task_planner import TaskPlanner
            self._task_planner = TaskPlanner(self._registry)
            self.logger.info("  ✅ TaskPlanner 初始化成功")
        except Exception as e:
            self.logger.error(f"  ❌ TaskPlanner 初始化失败: {e}")
            self._task_planner = None
    
    @property
    def registry(self):
        """获取注册表"""
        return self._registry
    
    @property
    def intent_router(self):
        """获取意图路由器"""
        return self._intent_router
    
    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            ProcessingResult: 处理结果
        """
        self._stats["total_requests"] += 1
        
        try:
            # 1. 意图识别与路由
            if self._intent_router:
                route_result = self._intent_router.route(query, context)
                intent = route_result["intent"]
                recommended_hands = route_result["recommended_hands"]
                
                self.logger.info(f"意图识别: {intent.get('intent')} (置信度: {intent.get('confidence')})")
                self.logger.info(f"推荐 Hands: {[h['hand_name'] for h in recommended_hands[:3]]}")
                
                # 2. 执行
                if recommended_hands:
                    primary_hand = recommended_hands[0]["hand"]
                    exec_result = self._intent_router.execute(query, context)
                    
                    # 更新统计
                    self._update_stats(intent.get("intent"), primary_hand.name, exec_result["success"])
                    
                    return ProcessingResult(
                        success=exec_result["success"],
                        intent=intent.get("intent"),
                        hand=exec_result.get("hand"),
                        output=exec_result.get("result"),
                        error=exec_result.get("error"),
                        alternatives=[h["hand_name"] for h in recommended_hands[1:4]]
                    )
            
            # 无可用组件
            self._stats["failed_requests"] += 1
            return ProcessingResult(
                success=False,
                error="无可用的处理组件"
            )
            
        except Exception as e:
            self.logger.error(f"处理失败: {e}")
            self._stats["failed_requests"] += 1
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _update_stats(self, intent: str, hand: str, success: bool):
        """更新统计"""
        if success:
            self._stats["successful_requests"] += 1
        else:
            self._stats["failed_requests"] += 1
        
        # 按意图统计
        if intent:
            if intent not in self._stats["by_intent"]:
                self._stats["by_intent"][intent] = {"total": 0, "success": 0}
            self._stats["by_intent"][intent]["total"] += 1
            if success:
                self._stats["by_intent"][intent]["success"] += 1
        
        # 按 Hand 统计
        if hand:
            if hand not in self._stats["by_hand"]:
                self._stats["by_hand"][hand] = {"total": 0, "success": 0}
            self._stats["by_hand"][hand]["total"] += 1
            if success:
                self._stats["by_hand"][hand]["success"] += 1
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self._stats["total_requests"]
        success = self._stats["successful_requests"]
        failed = self._stats["failed_requests"]
        
        return {
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": failed,
            "success_rate": success / total if total > 0 else 0,
            "hands_loaded": len(self._registry.hands) if self._registry else 0,
            "by_intent": self._stats["by_intent"],
            "by_hand": self._stats["by_hand"]
        }
    
    def list_hands(self) -> List[Dict[str, str]]:
        """列出所有注册的 Hands"""
        if not self._registry:
            return []
        
        return [
            {
                "name": name,
                "description": hand.description,
                "category": hand.category.value,
                "safety_level": hand.safety_level.value
            }
            for name, hand in self._registry.hands.items()
        ]
    
    def reload(self):
        """重新加载所有组件"""
        self.logger.info("重新加载 Central Hub...")
        CentralHub._initialized = False
        self._initialize_components()
        self.logger.info("✅ 重新加载完成")


# 全局实例
_central_hub: Optional[CentralHub] = None


def get_central_hub() -> CentralHub:
    """获取 Central Hub 全局实例"""
    global _central_hub
    if _central_hub is None:
        _central_hub = CentralHub()
    return _central_hub


def process_query(query: str, context: Optional[Dict[str, Any]] = None) -> ProcessingResult:
    """
    处理查询的便捷函数
    
    Args:
        query: 用户查询
        context: 上下文信息
        
    Returns:
        ProcessingResult: 处理结果
    """
    hub = get_central_hub()
    return hub.process(query, context)
