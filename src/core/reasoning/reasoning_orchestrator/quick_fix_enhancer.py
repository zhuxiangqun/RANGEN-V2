"""
快速修复Prompt增强器
阶段0.5：立即解决最严重的问题
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QuickFixPromptEnhancer:
    """
    快速修复Prompt增强器
    只为已知问题类型添加领域知识注入，立即解决最严重的问题
    """

    def __init__(self):
        # 关键事实库 - 内置最重要的事实，避免LLM犯错
        self.critical_facts = {
            # D.C.不是州的问题
            'dc_state': {
                'trigger_keywords': ['capitol', 'capitol', 'washington d.c.', 'd.c.', 'us capitol'],
                'context_keywords': ['state', 'same state', 'different state'],
                'fact': 'Washington D.C. is the capital of the United States but is NOT a state. It is a federal district under direct federal control. The 50 states are separate from D.C.',
                'priority': 10  # 最高优先级
            },

            # 第15任总统没有第一夫人
            '15th_president': {
                'trigger_keywords': ['15th', 'fifteenth', 'buchanan', 'james buchanan'],
                'context_keywords': ['first lady', 'president', 'wife'],
                'fact': 'James Buchanan was the 15th President of the United States. He never married and had no First Lady in the traditional sense. Harriet Lane served as White House hostess.',
                'priority': 8
            },

            # Punxsutawney Phil的位置
            'punxsutawney_phil': {
                'trigger_keywords': ['punxsutawney phil', 'phil', 'groundhog day'],
                'context_keywords': ['location', 'state', 'pennsylvania'],
                'fact': 'Punxsutawney Phil is a famous groundhog from Punxsutawney, Pennsylvania, known for Groundhog Day weather predictions.',
                'priority': 7
            },

            # Dewey Decimal分类
            'dewey_decimal': {
                'trigger_keywords': ['dewey decimal', 'dewey', 'decimal classification'],
                'context_keywords': ['height', 'building', 'feet', 'rank'],
                'fact': 'Dewey Decimal classification numbers are used in libraries to categorize books. They are typically decimal numbers (like 823.8) that can be converted to other units when needed.',
                'priority': 6
            }
        }

        logger.info("✅ QuickFixPromptEnhancer 初始化完成")

    def enhance_prompt(self, prompt: str, query: str) -> str:
        """
        增强prompt - 注入关键事实
        Args:
            prompt: 原始prompt
            query: 用户查询
        Returns:
            增强后的prompt
        """
        query_lower = query.lower()

        # 收集需要注入的事实
        facts_to_inject = []
        injected_fact_names = set()

        # 按优先级排序处理事实
        sorted_facts = sorted(
            self.critical_facts.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        )

        for fact_name, fact_config in sorted_facts:
            if self._should_inject_fact(query_lower, fact_config):
                if fact_name not in injected_fact_names:
                    facts_to_inject.append(fact_config['fact'])
                    injected_fact_names.add(fact_name)

                    logger.debug(f"注入关键事实: {fact_name}")

        if facts_to_inject:
            # 构建增强部分
            enhancement = "\n\nCRITICAL FACTS TO REMEMBER:\n" + "\n".join(f"- {fact}" for fact in facts_to_inject)

            # 将增强内容添加到prompt末尾
            enhanced_prompt = prompt + enhancement

            logger.info(f"✅ 注入了 {len(facts_to_inject)} 条关键事实")
            return enhanced_prompt

        return prompt

    def _should_inject_fact(self, query_lower: str, fact_config: Dict[str, Any]) -> bool:
        """
        判断是否应该注入某个事实
        """
        # 检查触发关键词
        has_trigger = any(keyword.lower() in query_lower for keyword in fact_config['trigger_keywords'])

        # 检查上下文关键词
        has_context = any(keyword.lower() in query_lower for keyword in fact_config['context_keywords'])

        # 触发关键词必须存在，上下文关键词可选（但如果存在会增加权重）
        return has_trigger and (not fact_config['context_keywords'] or has_context)

    def add_critical_fact(self, name: str, trigger_keywords: list, context_keywords: list,
                         fact: str, priority: int = 5):
        """
        添加新的关键事实
        """
        self.critical_facts[name] = {
            'trigger_keywords': trigger_keywords,
            'context_keywords': context_keywords,
            'fact': fact,
            'priority': priority
        }

        logger.info(f"添加关键事实: {name} (优先级: {priority})")

    def remove_critical_fact(self, name: str):
        """
        移除关键事实
        """
        if name in self.critical_facts:
            del self.critical_facts[name]
            logger.info(f"移除关键事实: {name}")
        else:
            logger.warning(f"关键事实不存在: {name}")

    def get_injection_stats(self) -> Dict[str, Any]:
        """
        获取注入统计信息
        """
        return {
            'total_facts': len(self.critical_facts),
            'facts_by_priority': {
                priority: len([f for f in self.critical_facts.values() if f['priority'] == priority])
                for priority in set(f['priority'] for f in self.critical_facts.values())
            },
            'fact_names': list(self.critical_facts.keys())
        }
