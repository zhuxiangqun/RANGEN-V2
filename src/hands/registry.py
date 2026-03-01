#!/usr/bin/env python3
"""
Hands能力包注册表
"""

import logging
from typing import Dict, List, Any, Optional, Type, Set
from pathlib import Path
import importlib
import inspect

from .base import BaseHand, HandCategory, HandSafetyLevel, HandCapability


class HandRegistry:
    """Hands能力包注册表"""
    
    def __init__(self, auto_discover: bool = True):
        self.logger = logging.getLogger(__name__)
        self.hands: Dict[str, BaseHand] = {}  # 名称 -> Hand实例
        self.hand_classes: Dict[str, Type[BaseHand]] = {}  # 名称 -> Hand类
        self.categories: Dict[HandCategory, List[str]] = {}  # 类别 -> Hand名称列表
        self.safety_levels: Dict[HandSafetyLevel, List[str]] = {}  # 安全级别 -> Hand名称列表
        
        # 初始化分类字典
        for category in HandCategory:
            self.categories[category] = []
        for safety_level in HandSafetyLevel:
            self.safety_levels[safety_level] = []
        
        self.logger.info("Hand注册表初始化完成")
        
        # 自动发现和加载Hands
        if auto_discover:
            try:
                current_dir = Path(__file__).parent
                loaded_count = self.load_hands_from_directory(str(current_dir))
                self.logger.info(f"自动发现并加载了 {loaded_count} 个Hands")
            except Exception as e:
                self.logger.warning(f"自动发现Hands失败: {e}")
    
    def register(self, hand: BaseHand) -> bool:
        """注册Hand实例"""
        try:
            hand_name = hand.name
            
            if hand_name in self.hands:
                self.logger.warning(f"Hand '{hand_name}' 已存在，将进行更新")
            
            # 注册实例
            self.hands[hand_name] = hand
            
            # 更新分类索引
            self._update_category_index(hand_name, hand.category)
            self._update_safety_index(hand_name, hand.safety_level)
            
            self.logger.info(f"注册Hand: {hand_name} ({hand.category.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"注册Hand失败: {e}")
            return False
    
    def register_class(self, hand_class: Type[BaseHand], **kwargs) -> bool:
        """注册Hand类并创建实例"""
        try:
            # 创建实例
            hand_instance = hand_class(**kwargs)
            return self.register(hand_instance)
            
        except Exception as e:
            self.logger.error(f"注册Hand类失败: {e}")
            return False
    
    def _update_category_index(self, hand_name: str, category: HandCategory):
        """更新类别索引"""
        if hand_name not in self.categories[category]:
            self.categories[category].append(hand_name)
    
    def _update_safety_index(self, hand_name: str, safety_level: HandSafetyLevel):
        """更新安全级别索引"""
        if hand_name not in self.safety_levels[safety_level]:
            self.safety_levels[safety_level].append(hand_name)
    
    def get_hand(self, hand_name: str) -> Optional[BaseHand]:
        """获取Hand实例"""
        return self.hands.get(hand_name)
    
    def get_capability(self, hand_name: str) -> Optional[HandCapability]:
        """获取Hand能力定义"""
        hand = self.get_hand(hand_name)
        return hand.get_capability() if hand else None
    
    def get_hands_by_category(self, category: HandCategory) -> List[BaseHand]:
        """根据类别获取Hands"""
        hand_names = self.categories.get(category, [])
        return [self.hands[name] for name in hand_names if name in self.hands]
    
    def get_hands_by_safety_level(self, safety_level: HandSafetyLevel) -> List[BaseHand]:
        """根据安全级别获取Hands"""
        hand_names = self.safety_levels.get(safety_level, [])
        return [self.hands[name] for name in hand_names if name in self.hands]
    
    def get_all_hands(self) -> List[BaseHand]:
        """获取所有Hands"""
        return list(self.hands.values())
    
    def get_all_capabilities(self) -> List[HandCapability]:
        """获取所有能力定义"""
        return [hand.get_capability() for hand in self.get_all_hands()]
    
    def search_hands(self, keyword: str) -> List[BaseHand]:
        """搜索Hands"""
        keyword_lower = keyword.lower()
        results = []
        
        for hand in self.get_all_hands():
            if (keyword_lower in hand.name.lower() or 
                keyword_lower in hand.description.lower() or
                keyword_lower in hand.category.value.lower()):
                results.append(hand)
        
        return results
    
    def unregister(self, hand_name: str) -> bool:
        """注销Hand"""
        if hand_name not in self.hands:
            self.logger.warning(f"Hand '{hand_name}' 不存在")
            return False
        
        try:
            hand = self.hands[hand_name]
            
            # 从分类索引中移除
            if hand_name in self.categories[hand.category]:
                self.categories[hand.category].remove(hand_name)
            
            # 从安全级别索引中移除
            if hand_name in self.safety_levels[hand.safety_level]:
                self.safety_levels[hand.safety_level].remove(hand_name)
            
            # 从主字典中移除
            del self.hands[hand_name]
            
            self.logger.info(f"注销Hand: {hand_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销Hand失败: {e}")
            return False
    
    def load_hands_from_directory(self, directory_path: str) -> int:
        """从目录加载Hands"""
        loaded_count = 0
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"目录不存在: {directory_path}")
            return 0
        
        # 查找Python模块
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("_") or py_file.name == "registry.py":
                continue
            
            module_name = py_file.stem
            try:
                # 动态导入模块 - 兼容Python 3.14+
                spec = importlib.util.spec_from_file_location(
                    f"hands.{module_name}", py_file
                )
                if spec is None or spec.loader is None:
                    # 回退到SourceFileLoader方法
                    from importlib.machinery import SourceFileLoader
                    loader = SourceFileLoader(f"hands.{module_name}", str(py_file))
                    module = loader.load_module()
                else:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                
                # 查找BaseHand的子类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseHand) and 
                        obj != BaseHand):
                        
                        try:
                            # 创建实例并注册
                            hand_instance = obj()
                            if self.register(hand_instance):
                                loaded_count += 1
                                self.logger.info(f"从 {py_file.name} 加载Hand: {hand_instance.name}")
                        except Exception as e:
                            self.logger.error(f"创建Hand实例失败 {name}: {e}")
                            
            except Exception as e:
                self.logger.error(f"加载模块失败 {py_file}: {e}")
        
        self.logger.info(f"从目录 {directory_path} 加载了 {loaded_count} 个Hands")
        return loaded_count
    
    def clear(self):
        """清空注册表"""
        self.hands.clear()
        self.hand_classes.clear()
        
        for category in self.categories:
            self.categories[category].clear()
        for safety_level in self.safety_levels:
            self.safety_levels[safety_level].clear()
        
        self.logger.info("Hand注册表已清空")
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_hands = len(self.hands)
        
        category_stats = {}
        for category, hand_names in self.categories.items():
            category_stats[category.value] = len(hand_names)
        
        safety_stats = {}
        for safety_level, hand_names in self.safety_levels.items():
            safety_stats[safety_level.value] = len(hand_names)
        
        return {
            "total_hands": total_hands,
            "by_category": category_stats,
            "by_safety_level": safety_stats,
            "hand_names": list(self.hands.keys())
        }