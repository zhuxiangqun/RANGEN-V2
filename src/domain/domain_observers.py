#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域观察者模块
提供领域事件的观察者模式实现
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod


@dataclass
class DomainEvent:
    """领域事件数据类"""
    event_type: str
    domain_name: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None


class DomainObserver(ABC):
    """领域观察者基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_history = []
        self.error_log = []
    
    @abstractmethod
    def update(self, event: DomainEvent) -> None:
        """更新观察者状态"""
        pass


class DomainEventManager:
    """领域事件管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("DomainEventManager")
        self.observers: List[DomainObserver] = []
        self.event_queue: List[DomainEvent] = []
        self.max_queue_size = 1000
        self.processing_enabled = True
    
    def register_observer(self, observer: DomainObserver) -> bool:
        """注册观察者"""
        try:
            if observer not in self.observers:
                self.observers.append(observer)
                self.logger.info(f"注册观察者成功: {observer.__class__.__name__}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"注册观察者失败: {e}")
            return False
    
    def unregister_observer(self, observer: DomainObserver) -> bool:
        """注销观察者"""
        try:
            if observer in self.observers:
                self.observers.remove(observer)
                self.logger.info(f"注销观察者成功: {observer.__class__.__name__}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"注销观察者失败: {e}")
            return False
    
    def publish_event(self, event: DomainEvent) -> bool:
        """发布事件"""
        try:
            if not self.processing_enabled:
                return False
            
            if len(self.event_queue) >= self.max_queue_size:
                self.event_queue.pop(0)
            
            self.event_queue.append(event)
            
            for observer in self.observers:
                try:
                    observer.update(event)
                except Exception as e:
                    self.logger.error(f"观察者处理事件失败: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"发布事件失败: {e}")
            return False
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "initialized": True,
            "total_observers": len(self.observers),
            "queue_size": len(self.event_queue),
            "processing_enabled": self.processing_enabled,
            "timestamp": time.time()
        }
