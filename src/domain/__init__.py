#!/usr/bin/env python3
"""
领域模块 - 统一导入
"""

from .domain_observers import (
    DomainObserver,
    DomainEvent,
    DomainEventManager
)

from .domain_manager import (
    DomainManager,
    get_domain_manager,
    DomainConfig
)

__all__ = [
    # 观察者模式
    'DomainObserver',
    'DomainEvent',
    'DomainEventManager',
    
    # 管理器
    'DomainManager',
    'get_domain_manager',
    'DomainConfig'
]
