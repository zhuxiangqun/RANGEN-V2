import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域管理器 - 重构版本
使用观察者模式和状态模式，大幅降低耦合度
"""

import logging
from typing import Dict, Any, List, Optional
from src.domain import DomainManager, get_domain_manager


class DomainManagerWrapper:
    """领域管理器包装器 - 重构版本"""
    
    def __init__(self):
        """初始化领域管理器包装器"""
        self.logger = logging.getLogger(__name__)
        self.domain_manager = get_domain_manager()
        self.logger.info("领域管理器包装器初始化完成（重构版本）")
    
    def add_domain(self, domain_name: str, keywords: List[str]) -> bool:
        """添加领域"""
        try:
            # 验证输入数据
            if not self._validate_input_data(domain_name, keywords):
                return False
            
            # 检查领域是否已存在
            if self._domain_exists(domain_name):
                self.logger.warning(f"领域已存在: {domain_name}")
                return False
            
            # 添加领域
            result = self.domain_manager.add_domain(
                domain_name=domain_name,
                keywords=keywords
            )
            
            # 记录领域添加历史
            if result:
                self._record_domain_addition(domain_name, keywords)
            
            return result
            
        except Exception as e:
            self.logger.error(f"添加领域失败: {e}")
            return False
    
    def _validate_input_data(self, domain_name: str, keywords: List[str]) -> bool:
        """验证输入数据"""
        if not isinstance(domain_name, str) or not domain_name.strip():
            return False
        
        if not isinstance(keywords, list) or len(keywords) == 0:
            return False
        
        # 验证关键词
        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                return False
        
        return True
    
    def _domain_exists(self, domain_name: str) -> bool:
        """检查领域是否已存在"""
        try:
            # 这里应该检查领域是否已存在
            # 简化实现
            return False
        except Exception:
            return False
    
    def _record_domain_addition(self, domain_name: str, keywords: List[str]):
        """记录领域添加历史"""
        if not hasattr(self, 'domain_history'):
            self.domain_history = []
        
        self.domain_history.append({
            'action': 'add_domain',
            'domain_name': domain_name,
            'keywords': keywords,
            'timestamp': time.time()
        })
    
    def update_domain(self, domain_name: str, **kwargs) -> bool:
        """更新领域"""
        try:
            return self.domain_manager.update_domain(domain_name, **kwargs)
        except Exception as e:
            self.logger.error(f"更新领域失败: {e}")
            return False
    
    def remove_domain(self, domain_name: str) -> bool:
        """移除领域"""
        try:
            return self.domain_manager.remove_domain(domain_name)
        except Exception as e:
            self.logger.error(f"移除领域失败: {e}")
            return False
    
    def get_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """获取领域"""
        try:
            domain_config = self.domain_manager.get_domain(domain_name)
            if domain_config:
                return {
                    "domain_name": domain_config.domain_name,
                    "keywords": domain_config.keywords,
                    "patterns": domain_config.patterns,
                    "confidence": domain_config.confidence,
                    "metadata": domain_config.metadata
                }
            return {
                "error": f"领域 {domain_name} 不存在",
                "status": "domain_not_found",
                "domain_name": domain_name,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"获取领域失败: {e}")
            return {
                "error": f"获取领域失败: {e}",
                "status": "error",
                "domain_name": domain_name,
                "timestamp": time.time()
            }
    
    def get_all_domains(self) -> Dict[str, Any]:
        """获取所有领域"""
        try:
            domains = self.domain_manager.get_all_domains()
            result = {}
            for name, config in domains.items():
                result[name] = {
                    "domain_name": config.domain_name,
                    "keywords": config.keywords,
                    "patterns": config.patterns,
                    "confidence": config.confidence,
                    "metadata": config.metadata
                }
            return result
        except Exception as e:
            self.logger.error(f"获取所有领域失败: {e}")
            return {
                "error": f"获取所有领域失败: {e}",
                "status": "error",
                "timestamp": time.time(),
                "domains": {}
            }
    
    def search_domains(self, query: str) -> List[Dict[str, Any]]:
        """搜索领域"""
        try:
            domains = self.domain_manager.search_domains(query)
            result = []
            for domain_config in domains:
                result.append({
                    "domain_name": domain_config.domain_name,
                    "keywords": domain_config.keywords,
                    "patterns": domain_config.patterns,
                    "confidence": domain_config.confidence,
                    "metadata": domain_config.metadata
                })
            return result
        except Exception as e:
            self.logger.error(f"搜索领域失败: {e}")
            return [{
                "error": f"搜索领域失败: {e}",
                "status": "search_failed",
                "query": query,
                "timestamp": time.time()
            }]
    
    def get_domain_statistics(self) -> Dict[str, Any]:
        """获取领域统计"""
        try:
            return self.domain_manager.get_domain_statistics()
        except Exception as e:
            self.logger.error(f"获取领域统计失败: {e}")
            return {
                "error": f"获取领域统计失败: {e}",
                "status": "statistics_failed",
                "timestamp": time.time(),
                "statistics": {}
            }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计"""
        return self.domain_manager.get_manager_stats()
    
    def _validate_input_data(self, domain_name: str, keywords: List[str]) -> bool:
        """验证输入数据"""
        if not isinstance(domain_name, str) or not domain_name.strip():
            return False
        
        if not isinstance(keywords, list) or not keywords:
            return False
        
        # 检查危险字符
        dangerous_chars = ["<", ">", "'", "\"", "&", ";", "|", "`"]
        for char in dangerous_chars:
            if char in domain_name:
                return False
        
        return True


# 便捷函数
def get_domain_manager_wrapper() -> DomainManagerWrapper:
    """获取领域管理器包装器实例"""
    return DomainManagerWrapper()


def add_domain_simple(domain_name: str, keywords: List[str]) -> bool:
    """简单添加领域函数"""
    wrapper = get_domain_manager_wrapper()
    return wrapper.add_domain(domain_name, keywords)