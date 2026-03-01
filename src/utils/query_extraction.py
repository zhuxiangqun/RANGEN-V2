
# src/utils/query_extraction.py
"""统一的查询提取工具"""

import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class QueryExtractionTool:
    """统一的查询提取工具，确保所有组件使用相同逻辑"""

    # 完整的正则表达式模式，按优先级排序
    QUERY_PATTERNS = [
        # StepGenerator格式（最高优先级）
        r'# 📋 THE QUERY YOU MUST ANALYZE:\s*\n(.*?)(?=\n#|\n\*\*|\n\d+\.|$)',

        # 中英文Query格式
        r'Query[：:]\s*([^\n]+)',
        r'查询[：:]\s*([^\n]+)',

        # 中英文Question格式
        r'Question[：:]\s*([^\n]+)',
        r'问题[：:]\s*([^\n]+)',

        # 复杂查询模式（需要放在简单模式之前）
        r'(If\s+[^\n?？]*[\?？]?)',
        r'(Imagine\s+[^\n?？]*[\?？]?)',
        r'(Suppose\s+[^\n?？]*[\?？]?)',
        r'(假设\s+[^\n?？]*[\?？]?)',

        # 其他常见格式
        r'(What is\s+[^\n?？]*[\?？]?)',
        r'(Who is\s+[^\n?？]*[\?？]?)',
        r'(How\s+[^\n?？]*[\?？]?)',
        r'(Where\s+[^\n?？]*[\?？]?)',
    ]
    
    @staticmethod
    def extract_query(prompt: str) -> Optional[str]:
        """统一的查询提取方法"""
        if not prompt or not isinstance(prompt, str):
            return None
        
        # 逐个尝试模式
        for pattern in QueryExtractionTool.QUERY_PATTERNS:
            try:
                match = re.search(pattern, prompt, re.MULTILINE | re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    
                    # 验证查询合理性
                    if QueryExtractionTool._validate_query(query):
                        logger.debug(f"查询提取成功: {query[:50]}...")
                        return query
                        
            except Exception as e:
                logger.warning(f"查询提取模式失败: {e}")
                continue
        
        # 兜底策略：如果输入本身看起来像查询，直接返回
        stripped_prompt = prompt.strip()
        if QueryExtractionTool._validate_query(stripped_prompt):
            logger.debug(f"使用兜底策略提取查询: {stripped_prompt[:50]}...")
            return stripped_prompt

        logger.warning("所有查询提取方法都失败")
        return None
    
    @staticmethod
    def _validate_query(query: str) -> bool:
        """验证提取的查询是否合理"""
        if not query or len(query) < 5:
            return False
        
        # 必须包含一定数量的字母数字字符
        alphanumeric_chars = sum(1 for c in query if c.isalnum())
        if alphanumeric_chars < 5:
            return False
        
        # 不能太长
        if len(query) > 500:
            return False
        
        return True
    
    @staticmethod
    def validate_query_consistency(prompt: str, expected_query: Optional[str] = None) -> Dict[str, Any]:
        """验证查询提取的一致性"""
        extracted = QueryExtractionTool.extract_query(prompt)
        
        result = {
            'extracted_query': extracted,
            'is_consistent': True,
            'confidence': 0.0,
            'issues': []
        }
        
        if expected_query and extracted:
            # 计算相似度
            similarity = QueryExtractionTool._calculate_similarity(expected_query, extracted)
            result['confidence'] = similarity
            
            if similarity < 0.8:
                result['is_consistent'] = False
                result['issues'].append(
                    f'查询不一致: 期望"{expected_query[:30]}...", 提取"{extracted[:30]}" (相似度:{similarity:.2f})'
                )
        
        elif not extracted:
            result['is_consistent'] = False
            result['issues'].append('无法提取查询')
        
        return result
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def test_extraction(test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """测试查询提取功能"""
        results = {
            'total': len(test_cases),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for i, test_case in enumerate(test_cases):
            prompt = test_case['prompt']
            expected = test_case.get('expected')
            
            try:
                extracted = QueryExtractionTool.extract_query(prompt)
                success = extracted is not None
                
                if expected and extracted:
                    similarity = QueryExtractionTool._calculate_similarity(expected, extracted)
                    success = similarity > 0.8
                
                result = {
                    'test_id': i + 1,
                    'prompt': prompt[:50] + '...',
                    'expected': expected,
                    'extracted': extracted,
                    'success': success
                }
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append(result)
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'test_id': i + 1,
                    'error': str(e),
                    'success': False
                })
        
        results['success_rate'] = results['successful'] / results['total'] if results['total'] > 0 else 0
        return results
