"""
智能领域管理系统
集成关键词发现、多语言支持和智能学习功能
"""

import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

from src.utils.domain_manager import get_domain_manager, DomainManager, DomainProcessor
from src.utils.intelligent_keyword_discovery import get_keyword_discovery
from src.utils.multilingual_keyword_library import get_multilingual_library
from src.config import config

logger = logging.getLogger(__name__)

class IntelligentDomainManager:
    """智能领域管理器"""

    def __init__(self):
        self.domain_manager = get_domain_manager()
        self.keyword_discovery = get_keyword_discovery()
        self.multilingual_library = get_multilingual_library()

        # 学习统计
        self.learning_stats = {
            'queries_processed': 0,
            'keywords_learned': 0,
            'domains_discovered': 0,
            'translations_added': 0,
            'last_learning_update': None
        }

        # 自动学习配置
        self.auto_learning_config = {
            'enabled': True,
            'min_confidence_threshold': 0.6,
            'max_keywords_per_session': 50,
            'learning_interval_minutes': 60,
            'auto_translate_new_keywords': True
        }

    def process_query_intelligently(self, query: str, user_language: str = 'en') -> Dict[str, Any]:
        """
        智能处理查询
        自动发现关键词、分类领域、生成多语言变体
        """
        self.learning_stats['queries_processed'] += 1

        result = {
            'original_query': query,
            'user_language': user_language,
            'discovered_keywords': [],
            'inferred_domains': [],
            'multilingual_variants': {},
            'processing_time': datetime.now()
        }

        # 1. 智能关键词发现
        discovered_keywords = self.keyword_discovery.discover_keywords_from_query(query)
        result['discovered_keywords'] = discovered_keywords

        # 2. 领域推理和分类
        domains_with_scores = self._infer_domains_from_query(query, discovered_keywords)
        result['inferred_domains'] = domains_with_scores

        # 3. 多语言查询变体生成
        multilingual_variants = self._generate_multilingual_variants(query, user_language)
        result['multilingual_variants'] = multilingual_variants

        # 4. 自动学习更新
        if self.auto_learning_config['enabled']:
            self._update_learning_from_query(query, discovered_keywords, domains_with_scores)

        return result

    def _infer_domains_from_query(self, query: str, discovered_keywords: List[Tuple[str, float, str]]) -> List[Tuple[str, float]]:
        """从查询和发现的关键词中推理领域"""
        domain_scores = defaultdict(float)

        # 基于发现的关键词
        for keyword, confidence, inferred_domain in discovered_keywords:
            if inferred_domain != "general":
                domain_scores[inferred_domain] += confidence

        # 基于现有领域关键词的匹配
        query_lower = query.lower()
        for domain_name in self.domain_manager.list_domains():
            domain_processor = self.domain_manager.domains.get(domain_name)
            if domain_processor:
                all_keywords = domain_processor.core_keywords + domain_processor.extended_keywords
                matches = sum(1 for kw in all_keywords if kw.lower() in query_lower)
                if matches > 0:
                    domain_scores[domain_name] += matches * 0.1

        # 排序并返回前5个
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_domains[:5]

    def _generate_multilingual_variants(self, query: str, user_language: str) -> Dict[str, List[str]]:
        """生成多语言查询变体"""
        variants = {}

        # 为每种支持的语言生成变体
        supported_languages = ['en', 'zh', 'ja', 'ko', 'es', 'fr', 'de']

        for lang in supported_languages:
            if lang != user_language:
                # 这里可以集成翻译服务
                # 目前返回原始查询作为占位符
                variants[lang] = [query]  # TODO: 实际翻译

        return variants

    def _update_learning_from_query(self, query: str, discovered_keywords: List[Tuple[str, float, str]],
                                   domains_with_scores: List[Tuple[str, float]]):
        """从查询中更新学习"""
        # 1. 学习新的关键词
        for keyword, confidence, domain in discovered_keywords:
            if confidence >= self.auto_learning_config['min_confidence_threshold']:
                # 检查是否需要添加到领域
                if domain != "general":
                    domain_info = self.domain_manager.get_domain_info(domain)
                    if domain_info and keyword not in domain_info['core_keywords'] + domain_info['extended_keywords']:
                        # 添加到扩展关键词
                        self._add_keyword_to_domain(domain, keyword, confidence)

        # 2. 更新领域使用统计
        for domain, score in domains_with_scores:
            # 这里可以更新领域使用频率统计
            pass

    def _add_keyword_to_domain(self, domain: str, keyword: str, confidence: float):
        """将关键词添加到领域"""
        try:
            # 获取现有领域配置
            domain_info = self.domain_manager.get_domain_info(domain)
            if not domain_info:
                return

            # 创建新的领域处理器配置
            new_config = {
                "name": domain,
                "core_keywords": domain_info['core_keywords'],
                "extended_keywords": domain_info['extended_keywords'] + [keyword],
                "description": domain_info['description'],
                "enabled": domain_info['enabled'],
                "priority": domain_info['priority']
            }

            # 重新添加领域（实际上是更新）
            self.domain_manager.add_domain(domain, new_config)

            # 更新多语言库
            if self.auto_learning_config['auto_translate_new_keywords']:
                self.multilingual_library.add_keyword(
                    domain,
                    self.multilingual_library.MultilingualKeyword(
                        english=keyword,
                        confidence=confidence,
                        source="auto_discovered"
                    )
                )

            self.learning_stats['keywords_learned'] += 1
            logger.info(f"自动学习关键词 '{keyword}' 添加到领域 '{domain}'")

        except Exception as e:
            logger.error(f"添加关键词到领域失败: {e}")

    def discover_new_domains_from_queries(self, queries: List[str]) -> Dict[str, Any]:
        """从查询批量中发现新领域"""
        logger.info(f"开始从 {len(queries)} 个查询中发现新领域")

        # 批量关键词发现
        discovery_result = self.keyword_discovery.batch_discover_from_queries(queries)

        # 分析新领域建议
        new_domain_suggestions = self.keyword_discovery.suggest_new_domains(
            discovery_result['discovered_keywords']
        )

        # 为建议的领域创建配置
        created_domains = []
        for suggestion in new_domain_suggestions:
            domain_name = suggestion['suggested_domain']

            # 创建领域配置
            domain_config = {
                "name": domain_name,
                "core_keywords": suggestion['core_keywords'],
                "extended_keywords": suggestion['extended_keywords'],
                "description": f"自动发现的领域：{domain_name}",
                "enabled": True,
                "priority": 1
            }

            # 添加领域
            if self.domain_manager.add_domain(domain_name, domain_config):
                created_domains.append(domain_name)
                self.learning_stats['domains_discovered'] += 1

                # 添加到多语言库
                for keyword in suggestion['core_keywords'] + suggestion['extended_keywords']:
                    self.multilingual_library.add_keyword(
                        domain_name,
                        self.multilingual_library.MultilingualKeyword(
                            english=keyword,
                            source="auto_discovered"
                        )
                    )

        result = {
            'queries_processed': len(queries),
            'keywords_discovered': len(discovery_result['discovered_keywords']),
            'domains_created': len(created_domains),
            'domain_distribution': discovery_result['domain_distribution'],
            'created_domain_names': created_domains,
            'discovery_stats': self.keyword_discovery.get_discovery_stats()
        }

        logger.info(f"领域发现完成：创建了 {len(created_domains)} 个新领域")
        return result

    def get_multilingual_domain_variants(self, query: str, domains: List[str] = None,
                                       languages: List[str] = None) -> Dict[str, Dict[str, List[str]]]:
        """获取多语言领域查询变体"""
        if languages is None:
            languages = ['zh', 'ja', 'ko', 'es', 'fr', 'de']

        if domains is None:
            domains = self.domain_manager.get_enabled_domains()

        result = {}

        for domain in domains:
            result[domain] = {}

            # 获取领域关键词的翻译
            for lang in languages:
                domain_keywords = self.multilingual_library.get_domain_keywords(domain, lang)
                if domain_keywords:
                    # 生成基于翻译关键词的查询变体
                    variants = []
                    for keyword in domain_keywords[:5]:  # 限制关键词数量
                        variant = f"{query} {keyword}"
                        variants.append(variant)
                    result[domain][lang] = variants

        return result

    def optimize_domain_coverage(self) -> Dict[str, Any]:
        """优化领域覆盖范围"""
        logger.info("开始优化领域覆盖范围")

        optimization_result = {
            'missing_translations': {},
            'low_coverage_domains': [],
            'suggested_keywords': {},
            'optimization_actions': []
        }

        # 1. 检查翻译覆盖
        for domain in self.domain_manager.list_domains():
            missing_translations = self.multilingual_library.suggest_translations(domain, 'zh')
            if missing_translations:
                optimization_result['missing_translations'][domain] = missing_translations
                optimization_result['optimization_actions'].append(
                    f"为领域 '{domain}' 添加 {len(missing_translations)} 个中文翻译"
                )

        # 2. 识别关键词覆盖不足的领域
        for domain in self.domain_manager.list_domains():
            domain_info = self.domain_manager.get_domain_info(domain)
            if domain_info and domain_info['total_keywords_count'] < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
                optimization_result['low_coverage_domains'].append({
                    'domain': domain,
                    'current_count': domain_info['total_keywords_count'],
                    'suggested_min': 15
                })

        # 3. 建议新关键词
        for domain in optimization_result['low_coverage_domains']:
            # 这里可以实现更复杂的关键词建议逻辑
            optimization_result['suggested_keywords'][domain['domain']] = [
                f"{domain['domain']}_concept_1",
                f"{domain['domain']}_concept_2",
                f"{domain['domain']}_concept_3"
            ]

        return optimization_result

    def export_learning_data(self, filepath: str = None) -> bool:
        """导出学习数据"""
        if filepath is None:
            filepath = f"data/learning_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            export_data = {
                'learning_stats': self.learning_stats,
                'domain_stats': self.domain_manager.get_all_domain_info(),
                'keyword_discovery_stats': self.keyword_discovery.get_discovery_stats(),
                'multilingual_coverage': self.multilingual_library.get_language_coverage(),
                'export_time': datetime.now().isoformat(),
                'version': 'get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))'
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"学习数据已导出到 {filepath}")
            return True

        except Exception as e:
            logger.error(f"导出学习数据失败: {e}")
            return False

    def get_intelligence_report(self) -> Dict[str, Any]:
        """获取智能系统报告"""
        return {
            'learning_stats': self.learning_stats,
            'domain_coverage': {
                'total_domains': len(self.domain_manager.list_domains()),
                'enabled_domains': len(self.domain_manager.get_enabled_domains()),
                'domain_details': self.domain_manager.get_all_domain_info()
            },
            'multilingual_support': {
                'supported_languages': list(self.multilingual_library.SUPPORTED_LANGUAGES.keys()),
                'language_coverage': self.multilingual_library.get_language_coverage(),
                'translation_stats': dict(self.multilingual_library.language_stats)
            },
            'keyword_discovery': {
                'stats': self.keyword_discovery.get_discovery_stats(),
                'auto_learning_enabled': self.auto_learning_config['enabled'],
                'min_confidence_threshold': self.auto_learning_config['min_confidence_threshold']
            },
            'last_updated': datetime.now().isoformat()
        }


# 全局智能领域管理器实例
_intelligent_domain_manager = None

def get_intelligent_domain_manager() -> IntelligentDomainManager:
    """获取智能领域管理器实例"""
    global _intelligent_domain_manager
    if _intelligent_domain_manager is None:
        _intelligent_domain_manager = IntelligentDomainManager()
    return _intelligent_domain_manager
