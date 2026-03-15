"""
动态领域管理系统
支持动态添加和管理领域配置，实现领域种类的灵活扩展
"""

import logging
from typing import Dict, List, Any, Optional, Callable
# 移除config依赖，避免循环导入
# from src.config import config
# 延迟导入以避免循环依赖
# from src.utils.intelligent_keyword_discovery import get_keyword_discovery

logger = logging.getLogger(__name__)

class DomainProcessor:
    """领域处理器"""

    def __init__(self, domain_config: Dict[str, Any]):
        self.name = domain_config.get("name", "")
        self.core_keywords = domain_config.get("core_keywords", [])
        self.extended_keywords = domain_config.get("extended_keywords", [])
        self.description = domain_config.get("description", "")
        self.enabled = domain_config.get("enabled", True)
        self.priority = domain_config.get("priority", 1)

    def get_all_keywords(self) -> List[str]:
        """获取所有关键词"""
        return self.core_keywords + self.extended_keywords

    def generate_variations(self, query: str) -> List[str]:
        """生成查询变体"""
        variations = []
        keywords = self.get_all_keywords()

        for keyword in keywords:
            if keyword not in query.lower():
                variations.append(f"{query} {keyword}")

        return variations

class DomainManager:
    """领域管理器 - 支持动态领域管理"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.domains: Dict[str, DomainProcessor] = {}
            self.domain_handlers: Dict[str, Callable] = {}
            self._load_default_domains()
            logger.info(f"✅ 领域管理器初始化完成，支持 {len(self.domains)} 个领域")

    def _load_default_domains(self):
        """加载默认领域配置"""
        try:
            # 使用新的配置加载器而不是硬编码配置
            from src.utils.domain_config_loader import get_domain_config_loader
            config_loader = get_domain_config_loader()
            domain_keywords = config_loader.get_domains()

            for domain_name, domain_config in domain_keywords.items():
                # 确保配置格式正确
                if not isinstance(domain_config, dict):
                    logger.warning(f"⚠️ 领域 {domain_name} 配置格式错误，跳过")
                    continue

                # 标准化配置格式
                standardized_config = {
                    "name": domain_name,
                    "core_keywords": domain_config.get("core_keywords", []),
                    "extended_keywords": domain_config.get("extended_keywords", []),
                    "description": domain_config.get("description", f"{domain_name} 领域"),
                    "enabled": domain_config.get("enabled", True),
                    "priority": domain_config.get("priority", 1)
                }

                # 创建领域处理器
                processor = DomainProcessor(standardized_config)
                self.domains[domain_name] = processor

                logger.info(f"📚 已加载领域: {domain_name} ({len(processor.get_all_keywords())} 个关键词)")

        except Exception as e:
            logger.error(f"❌ 加载默认领域配置失败: {e}")

    def add_domain(self, domain_name: str, domain_config: Dict[str, Any]) -> bool:
        """动态添加新领域"""
        try:
            # 验证配置
            is_valid, error_msg = self.validate_domain_config(domain_config)
            if not is_valid:
                logger.error(f"❌ 领域配置验证失败: {error_msg}")
                return False

            if domain_name in self.domains:
                logger.warning(f"⚠️ 领域 {domain_name} 已存在，将被覆盖")

            # 标准化配置
            standardized_config = {
                "name": domain_name,
                **domain_config
            }

            processor = DomainProcessor(standardized_config)
            self.domains[domain_name] = processor

            # 保存到配置文件
            from src.utils.domain_config_loader import get_domain_config_loader
            config_loader = get_domain_config_loader()
            config_success = config_loader.add_domain(domain_name, domain_config)

            if not config_success:
                logger.warning(f"⚠️ 领域 {domain_name} 已添加到内存，但保存到配置文件失败")

            logger.info(f"✅ 已添加领域: {domain_name} ({len(processor.get_all_keywords())} 个关键词)")
            return True

        except Exception as e:
            logger.error(f"❌ 添加领域 {domain_name} 失败: {e}")
            return False

    def remove_domain(self, domain_name: str) -> bool:
        """移除领域"""
        try:
            # 从内存中移除
            if domain_name in self.domains:
                del self.domains[domain_name]

            # 从配置文件中移除
            from src.utils.domain_config_loader import get_domain_config_loader
            config_loader = get_domain_config_loader()
            success = config_loader.remove_domain(domain_name)

            if success:
                logger.info(f"🗑️ 已移除领域: {domain_name}")
                return True
            else:
                # 如果配置文件中移除失败，但内存中已移除，仍然返回True
                logger.warning(f"⚠️ 从配置文件移除领域 {domain_name} 失败，但已从内存中移除")
                return True

        except Exception as e:
            logger.error(f"❌ 移除领域 {domain_name} 失败: {e}")
            return False

    def get_domain(self, domain_name: str) -> Optional[DomainProcessor]:
        """获取领域处理器"""
        return self.domains.get(domain_name)

    def list_domains(self) -> List[str]:
        """列出所有可用领域"""
        return list(self.domains.keys())

    def get_enabled_domains(self) -> List[str]:
        """获取所有启用的领域"""
        return [name for name, processor in self.domains.items() if processor.enabled]

    def generate_variations(self, query: str, domain_name: str) -> List[str]:
        """为指定领域生成查询变体"""
        processor = self.get_domain(domain_name)
        if processor and processor.enabled:
            return processor.generate_variations(query)
        else:
            logger.warning(f"⚠️ 领域 {domain_name} 不存在或未启用")
            return []

    def generate_all_domain_variations(self, query: str) -> Dict[str, List[str]]:
        """为所有启用的领域生成查询变体"""
        variations = {}

        for domain_name in self.get_enabled_domains():
            domain_variations = self.generate_variations(query, domain_name)
            if domain_variations:
                variations[domain_name] = domain_variations

        return variations

    def get_domain_info(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """获取领域信息"""
        processor = self.get_domain(domain_name)
        if processor:
            return {
                "name": processor.name,
                "description": processor.description,
                "enabled": processor.enabled,
                "priority": processor.priority,
                "core_keywords_count": len(processor.core_keywords),
                "extended_keywords_count": len(processor.extended_keywords),
                "total_keywords_count": len(processor.get_all_keywords())
            }
        return None

    def get_all_domain_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有领域信息"""
        info = {}
        for domain_name in self.domains.keys():
            domain_info = self.get_domain_info(domain_name)
            if domain_info:
                info[domain_name] = domain_info
        return info

    def validate_domain_config(self, domain_config: Dict[str, Any]) -> "tuple[bool, str]":
        """验证领域配置"""
        if not isinstance(domain_config, dict):
            return False, "配置必须是字典格式"

        required_fields = ["core_keywords", "extended_keywords"]
        for field in required_fields:
            if field not in domain_config:
                return False, f"缺少必需字段: {field}"
            if not isinstance(domain_config[field], list):
                return False, f"字段 {field} 必须是列表格式"

        return True, "配置验证通过"

    def generate_domain_keywords_from_queries(self, queries: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        从用户查询中智能生成领域关键词配置
        替代硬编码的领域关键词

        Args:
            queries: 用户查询列表

        Returns:
            智能生成的领域关键词配置
        """
        logger.info(f"🤖 开始从 {len(queries)} 个查询中智能生成领域关键词")

        try:
            # 使用智能关键词发现系统 (延迟导入避免循环依赖)
            from src.utils.intelligent_keyword_discovery import get_keyword_discovery
            discovery = get_keyword_discovery()

            # 批量发现关键词
            batch_results = discovery.batch_discover_from_queries(queries)

            # 按领域分组和聚合关键词
            domain_keywords = self._aggregate_keywords_by_domain(batch_results)

            # 生成标准化配置
            smart_domains = {}
            for domain_name, keywords in domain_keywords.items():
                if len(keywords) >= 3:  # 至少需要3个关键词才算有效领域
                    smart_domains[domain_name] = self._generate_domain_config(domain_name, keywords)

            logger.info(f"✅ 智能生成了 {len(smart_domains)} 个领域配置")
            return smart_domains

        except Exception as e:
            logger.error(f"❌ 智能生成领域关键词失败: {e}")
            return {}

    def _aggregate_keywords_by_domain(self, batch_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        按领域聚合关键词
        """
        domain_keywords = {}

        for item in batch_results.get('discovered_keywords', []):
            domain = item['domain']
            keyword = item['keyword']

            if domain not in domain_keywords:
                domain_keywords[domain] = []

            if keyword not in domain_keywords[domain]:
                domain_keywords[domain].append(keyword)

        return domain_keywords

    def _generate_domain_config(self, domain_name: str, keywords: List[str]) -> Dict[str, Any]:
        """
        生成标准化的领域配置
        """
        # 将关键词分为核心关键词和扩展关键词
        core_keywords = keywords[:min(5, len(keywords)//2 + 1)]
        extended_keywords = keywords[len(core_keywords):]

        return {
            "name": domain_name,
            "core_keywords": core_keywords,
            "extended_keywords": extended_keywords,
            "description": f"{domain_name} 领域 (智能生成)",
            "enabled": True,
            "priority": 1,
            "generated_by": "intelligent_system",
            "confidence": get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
        }

    def merge_smart_domains(self, smart_domains: Dict[str, Dict[str, Any]]) -> int:
        """
        将智能生成的领域合并到现有配置中

        Args:
            smart_domains: 智能生成的领域配置

        Returns:
            新增领域数量
        """
        new_domains_count = 0

        for domain_name, domain_config in smart_domains.items():
            if domain_name not in self.domains:
                # 添加新领域
                processor = DomainProcessor(domain_config)
                self.domains[domain_name] = processor
                new_domains_count += 1
                logger.info(f"🆕 添加智能生成领域: {domain_name} ({len(processor.get_all_keywords())} 个关键词)")
            else:
                # 更新现有领域
                existing_processor = self.domains[domain_name]
                self._merge_domain_keywords(existing_processor, domain_config)

        if new_domains_count > 0:
            logger.info(f"✅ 成功合并 {new_domains_count} 个新领域到系统")

        return new_domains_count

    def _merge_domain_keywords(self, existing_processor: DomainProcessor,
                              new_config: Dict[str, Any]):
        """
        合并领域关键词
        """
        # 合并核心关键词
        for keyword in new_config.get('core_keywords', []):
            if keyword not in existing_processor.core_keywords:
                existing_processor.core_keywords.append(keyword)

        # 合并扩展关键词
        for keyword in new_config.get('extended_keywords', []):
            if keyword not in existing_processor.extended_keywords:
                existing_processor.extended_keywords.append(keyword)

        logger.info(f"🔄 更新领域 {existing_processor.name}: +{len(new_config.get('core_keywords', []))} 核心词, +{len(new_config.get('extended_keywords', []))} 扩展词")

    def get_domain_statistics(self) -> Dict[str, Any]:
        """
        获取领域统计信息
        """
        stats = {
            'total_domains': len(self.domains),
            'total_keywords': 0,
            'domains': {},
            'keyword_distribution': {}
        }

        for domain_name, processor in self.domains.items():
            keywords = processor.get_all_keywords()
            stats['total_keywords'] += len(keywords)
            stats['domains'][domain_name] = {
                'core_keywords': len(processor.core_keywords),
                'extended_keywords': len(processor.extended_keywords),
                'total_keywords': len(keywords),
                'enabled': processor.enabled,
                'priority': processor.priority
            }

        # 关键词分布统计
        keyword_counts = []
        for processor in self.domains.values():
            keyword_counts.extend([len(processor.core_keywords), len(processor.extended_keywords)])

        if keyword_counts:
            stats['keyword_distribution'] = {
                'average': sum(keyword_counts) / len(keyword_counts),
                'max': max(keyword_counts),
                'min': min(keyword_counts)
            }

        return stats

# 全局领域管理器实例
_domain_manager = None

def get_domain_manager() -> DomainManager:
    """获取领域管理器实例"""
    global _domain_manager
    if _domain_manager is None:
        _domain_manager = DomainManager()
    return _domain_manager
