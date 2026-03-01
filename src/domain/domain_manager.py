import os
#!/usr/bin/env python3
"""
领域管理器 - 简化版本
功能已合并到utils模块中
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DomainConfig:
    """领域配置"""
    domain_name: str
    keywords: List[str]
    patterns: List[str]
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class Component:
    """领域事件"""
    event_type: str
    domain_name: str
    data: Dict[str, Any]
    timestamp: float


class DomainManager:
    """领域管理器 - 简化版本"""
    
    def __init__(self):
        """初始化领域管理器"""
        self.logger = logging.getLogger(__name__)
        self.domain_configs: Dict[str, DomainConfig] = {}
        self.domain_stats = {
            "total_domains": 0,
            "active_domains": 0,
            "events_processed": 0
        }
        self.logger.info("领域管理器初始化完成")
    
    def add_domain(self, domain_name: str, keywords: List[str], description: str = "") -> bool:
        """添加领域"""
        try:
            if not self._validate_domain_data(domain_name, keywords):
                return False
            
            # 创建领域配置
            domain_config = DomainConfig(
                domain_name=domain_name,
                keywords=keywords,
                patterns=[],
                confidence=0.8,
                metadata={}
            )
            
            self.domain_configs[domain_name] = domain_config
            self.domain_stats["total_domains"] += 1
            self.domain_stats["active_domains"] += 1
            
            self.logger.info(f"领域添加成功: {domain_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加领域失败: {e}")
            return False
    
    def remove_domain(self, domain_name: str) -> bool:
        """移除领域"""
        try:
            if domain_name in self.domain_configs:
                del self.domain_configs[domain_name]
                self.domain_stats["active_domains"] -= 1
                self.logger.info(f"领域移除成功: {domain_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除领域失败: {e}")
            return False
    
    def get_domain(self, domain_name: str) -> Optional[DomainConfig]:
        """获取领域配置"""
        return self.domain_configs.get(domain_name)
    
    def list_domains(self) -> List[str]:
        """列出所有领域"""
        return list(self.domain_configs.keys())
    
    def classify_text(self, text: str) -> List[Dict[str, Any]]:
        """分类文本"""
        try:
            results = []
            
            for domain_name, config in self.domain_configs.items():
                confidence = self._calculate_domain_confidence(text, config)
                if confidence >= config.confidence:
                    results.append({
                        "domain": domain_name,
                        "confidence": confidence,
                        "keywords_found": self._find_matching_keywords(text, config.keywords)
                    })
            
            # 按置信度排序
            results.sort(key=lambda x: x["confidence"], reverse=True)
            
            self.domain_stats["events_processed"] += 1
            return results
            
        except Exception as e:
            self.logger.error(f"文本分类失败: {e}")
            return []
    
    def _validate_domain_data(self, domain_name: str, keywords: List[str]) -> bool:
        """验证领域数据"""
        if not domain_name or not keywords:
            self.logger.warning("领域名称和关键词不能为空")
            return False
        
        if len(keywords) < 2:
            self.logger.warning("至少需要2个关键词")
            return False
        
        return True
    
    def _calculate_domain_confidence(self, text: str, config: DomainConfig) -> float:
        """计算领域置信度"""
        # 简单的关键词匹配算法
        text_lower = text.lower()
        matching_keywords = 0
        
        for keyword in config.keywords:
            if keyword.lower() in text_lower:
                matching_keywords += 1
        
        if not config.keywords:
            return 0.0
        
        return matching_keywords / len(config.keywords)
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """查找匹配的关键词"""
        text_lower = text.lower()
        matching = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matching.append(keyword)
        
        return matching
    
    def get_domain_stats(self) -> Dict[str, Any]:
        """获取领域统计信息"""
        return self.domain_stats.copy()
    
    def update_domain_confidence(self, domain_name: str, confidence: float) -> bool:
        """更新领域置信度"""
        try:
            if domain_name in self.domain_configs:
                self.domain_configs[domain_name].confidence = confidence
                self.logger.info(f"领域置信度已更新: {domain_name} -> {confidence}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"更新领域置信度失败: {e}")
            return False


# 全局实例
domain_manager = DomainManager()


def get_domain_manager() -> DomainManager:
    """获取领域管理器实例"""
    return domain_manager