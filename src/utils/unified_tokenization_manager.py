"""
统一分词策略管理器
根据不同任务和场景自动选择最优分词方案
"""
import logging
import time
from typing import List, Dict, Any, Optional
from enum import Enum

# 导入统一中心系统的函数
from .unified_centers import get_smart_config, create_query_context

class TokenizationStrategy(Enum):
    """分词策略枚举"""
    MULTILINGUAL = "multilingual"      # 多语言Unicode脚本分词
    TRADITIONAL = "traditional"        # 传统工具(Jieba/LTP)
    SUBWORD = "subword"               # 子词分词(BERT/GPT)
    DOMAIN = "domain"                 # 领域特定分词
    HYBRID = "hybrid"                 # 混合策略

class UnifiedTokenizationManager:
    """统一分词策略管理器"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tokenizers = {}

        self._load_tokenizers()
    
    def _create_fallback_multilingual_tokenizer(self):
        """创建回退多语言分词器"""
        class FallbackMultilingualTokenizer:
            def tokenize(self, text: str) -> List[Dict[str, Any]]:
                # 简单的空格分词
                tokens = text.split()
                return [{'token': token, 'start': i, 'end': i + len(token)} 
                       for i, token in enumerate(tokens)]
        
        return FallbackMultilingualTokenizer()
    
    def _create_fallback_traditional_tokenizer(self):
        """创建回退传统分词器"""
        class FallbackTraditionalTokenizer:
            def tokenize(self, text: str) -> List[Dict[str, Any]]:
                # 简单的空格分词
                tokens = text.split()
                return [{'token': token, 'start': i, 'end': i + len(token)} 
                       for i, token in enumerate(tokens)]
        
        return FallbackTraditionalTokenizer()

    def _load_tokenizers(self):
        """延迟加载分词器以避免初始化错误"""
        try:
            from multilingual_tokenizer import get_multilingual_tokenizer
            self.tokenizers[TokenizationStrategy.MULTILINGUAL] = get_multilingual_tokenizer()
            self.logger.info("✅ 多语言分词器加载成功")
        except ImportError:
            # 使用回退分词器，不显示错误日志
            self.tokenizers[TokenizationStrategy.MULTILINGUAL] = self._create_fallback_multilingual_tokenizer()
            self.logger.debug("使用回退多语言分词器")
        except Exception as e:
            self.logger.warning(f"多语言分词器加载失败: {e}")
            # 创建回退分词器
            self.tokenizers[TokenizationStrategy.MULTILINGUAL] = self._create_fallback_multilingual_tokenizer()

        try:
            from traditional_tokenizer import get_traditional_tokenizer
            self.tokenizers[TokenizationStrategy.TRADITIONAL] = get_traditional_tokenizer()
            self.logger.info("✅ 传统分词器加载成功")
        except ImportError:
            # 使用回退分词器，不显示错误日志
            self.tokenizers[TokenizationStrategy.TRADITIONAL] = self._create_fallback_traditional_tokenizer()
            self.logger.debug("使用回退传统分词器")
        except Exception as e:
            self.logger.warning(f"传统分词器加载失败: {e}")
            # 创建回退分词器
            self.tokenizers[TokenizationStrategy.TRADITIONAL] = self._create_fallback_traditional_tokenizer()

        try:
            from subword_tokenizer import get_subword_tokenizer
            self.tokenizers[TokenizationStrategy.SUBWORD] = get_subword_tokenizer()
            self.logger.info("✅ 子词分词器加载成功")
        except ImportError:
            # 使用回退分词器，不显示错误日志
            self.logger.debug("使用回退子词分词器")
        except Exception as e:
            self.logger.warning("子词分词器加载失败: {e}")

        try:
            from domain_tokenizer import get_domain_tokenizer
            self.tokenizers[TokenizationStrategy.DOMAIN] = get_domain_tokenizer()
            self.logger.info("✅ 领域分词器加载成功")
        except ImportError:
            # 使用回退分词器，不显示错误日志
            self.logger.debug("使用回退领域分词器")
        except Exception as e:
            self.logger.warning("领域分词器加载失败: {e}")

    def select_strategy(self, text: str, task_type: str = "general",
                       domain: Optional[str] = None) -> TokenizationStrategy:
        """根据文本和任务自动选择最优分词策略"""

        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        chinese_ratio = chinese_chars / max(total_chars, 1)

        if domain and domain in ["medical", "legal", "finance", "ai_tech"]:
            if TokenizationStrategy.DOMAIN in self.tokenizers:
                self.logger.info("选择领域分词策略: {domain}")
                return TokenizationStrategy.DOMAIN

        if task_type in ["bert_classification", "model_inference", "embedding"]:
            if TokenizationStrategy.SUBWORD in self.tokenizers:
                self.logger.info("选择子词分词策略(预训练模型兼容)")
                return TokenizationStrategy.SUBWORD

        if task_type in ["classification", "sentiment", "ner", "pos_tagging"]:
            context_medium = create_query_context("medium_threshold")
            if chinese_ratio > get_smart_config("medium_threshold", context_medium) and TokenizationStrategy.TRADITIONAL in self.tokenizers:
                self.logger.info("选择传统分词策略(中文NLP任务)")
                return TokenizationStrategy.TRADITIONAL

        context_high = create_query_context("high_threshold")
        if chinese_ratio < get_smart_config("high_threshold", context_high) and chinese_ratio > 0.2:  # 混合语言
            if TokenizationStrategy.MULTILINGUAL in self.tokenizers:
                self.logger.info("选择多语言分词策略(混合语言)")
                return TokenizationStrategy.MULTILINGUAL

        if TokenizationStrategy.MULTILINGUAL in self.tokenizers:
            self.logger.info("选择默认多语言分词策略")
            return TokenizationStrategy.MULTILINGUAL

        for strategy in [TokenizationStrategy.TRADITIONAL,
                        TokenizationStrategy.SUBWORD,
                        TokenizationStrategy.DOMAIN]:
            if strategy in self.tokenizers:
                self.logger.info("使用备用分词策略: {strategy.value}")
                return strategy

        raise RuntimeError("没有可用的分词策略")

    def tokenize(self, text: str, strategy: Optional[TokenizationStrategy] = None,
                task_type: str = "general", domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """执行分词"""

        if strategy is None:
            strategy = self.select_strategy(text, task_type, domain)

        if strategy not in self.tokenizers:
            raise ValueError(f"分词策略 {strategy.value} 不可用")

        tokenizer = self.tokenizers[strategy]

        try:
            if strategy == TokenizationStrategy.MULTILINGUAL:
                return self._multilingual_tokenize(tokenizer, text)

            elif strategy == TokenizationStrategy.TRADITIONAL:
                return self._traditional_tokenize(tokenizer, text, task_type)

            elif strategy == TokenizationStrategy.SUBWORD:
                return self._subword_tokenize(tokenizer, text, task_type)

            elif strategy == TokenizationStrategy.DOMAIN:
                return self._domain_tokenize(tokenizer, text, domain)

            else:
                raise ValueError(f"未实现的分词策略: {strategy.value}")

        except Exception as e:
            self.logger.error("分词执行失败 ({strategy.value}): {e}")
            return self._fallback_tokenize(text)

    def _multilingual_tokenize(self, tokenizer, text: str) -> List[Dict[str, Any]]:
        """多语言分词"""
        tokens = tokenizer.smart_tokenize(text)
        return [
            {
                "word": token["text"],
                "type": f"multilingual_{token['script']}",
                "confidence": get_smart_config("high_threshold", create_query_context("high_threshold")),
                "strategy": "multilingual"
            }
            for token in tokens if token["text"].strip()
        ]

    def _traditional_tokenize(self, tokenizer, text: str, task_type: str) -> List[Dict[str, Any]]:
        """传统分词"""
        segments = tokenizer.smart_segment_for_task(text, task_type)
        return [
            {
                "word": seg["word"],
                "type": seg["type"],
                "pos": seg.get("pos", ""),
                "confidence": seg["confidence"],
                "strategy": "traditional"
            }
            for seg in segments
        ]

    def _subword_tokenize(self, tokenizer, text: str, task_type: str) -> List[Dict[str, Any]]:
        """子词分词"""
        tokens = tokenizer.smart_tokenize_for_model(text, task_type)
        return [
            {
                "word": token["token"],
                "text": token["text"],
                "type": token["type"],
                "confidence": token["confidence"],
                "is_subword": token.get("is_subword", False),
                "strategy": "subword"
            }
            for token in tokens
        ]

    def _domain_tokenize(self, tokenizer, text: str, domain: Optional[str]) -> List[Dict[str, Any]]:
        """领域分词"""
        if domain:
            segments = tokenizer.segment_domain_text(text, domain)
        else:
            segments = tokenizer.auto_segment(text)

        return [
            {
                "word": seg["word"],
                "type": seg["type"],
                "category": seg.get("category", ""),
                "confidence": seg["confidence"],
                "is_domain_term": seg.get("is_domain_term", False),
                "strategy": "domain"
            }
            for seg in segments
        ]

    def _fallback_tokenize(self, text: str) -> List[Dict[str, Any]]:
        """备用分词方案"""
        import re
        words = re.findall(r'\b\w+\b|[\u4e00-\u9fff]', text)
        return [
            {
                "word": word,
                "type": "fallback",
                "confidence": get_smart_config("low_threshold", create_query_context("low_threshold")),
                "strategy": "fallback"
            }
            for word in words if word.strip()
        ]

    def compare_strategies(self, text: str, strategies: List[TokenizationStrategy]) -> Dict[str, Any]:
        """比较不同分词策略的效果"""
        results = {}

        for strategy in strategies:
            if strategy in self.tokenizers:
                try:
                    tokens = self.tokenize(text, strategy)
                    results[strategy.value] = {
                        "tokens": tokens,
                        "token_count": len(tokens),
                        "avg_confidence": sum(t.get("confidence", 0) for t in tokens) / max(len(tokens), 1)
                    }
                except Exception as e:
                    results[strategy.value] = {"error": str(e)}

        return results

_unified_manager = None

def get_unified_tokenization_manager() -> UnifiedTokenizationManager:
    """获取统一分词管理器单例"""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedTokenizationManager()
    return _unified_manager

def smart_tokenize(text: str, task_type: str = "general",
                  domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """智能分词接口 - 自动选择最优策略"""
    manager = get_unified_tokenization_manager()
    return manager.tokenize(text, task_type=task_type, domain=domain)

def tokenize_for_task(text: str, task_type: str) -> List[str]:
    """任务导向分词接口 - 只返回词汇列表"""
    tokens = smart_tokenize(text, task_type=task_type)
    return [token["word"] for token in tokens]
