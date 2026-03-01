"""
工具函数 - 提供通用工具函数
"""
import logging
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Utils:
    """工具函数类"""
    
    @staticmethod
    def initialize_config() -> Dict[str, Any]:
        """初始化配置 - 支持从配置文件加载"""
        config = {
            'llm_integration': {
                'llm_provider': 'deepseek',
                'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner'),
                'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            },
            'llm_fallback': {
                'enabled': True,
                'prompt_template': "请从以下内容中提取问题的答案。问题：{query}。内容：{content}。请只返回最可能的答案，不要包含任何解释。如果无法确定答案，请返回'无法确定'。",
                'max_retries': 2,
                'timeout': 10
            },
            'validation_rules': {
                'min_answer_length': 1,
                'max_answer_length': 300,
                'exclude_common_words': []
            }
        }
        
        # 🚀 新增：尝试从配置文件加载ML训练配置
        try:
            config_file = Path('config/ml_training_config.json')
            if config_file.exists():
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 合并配置
                    config.update(file_config)
                    logger.info(f"✅ 已加载ML训练配置: {config_file}")
        except Exception as e:
            logger.debug(f"加载ML训练配置文件失败（将使用默认配置）: {e}")
        
        return config
    
    @staticmethod
    def initialize_evidence_patterns() -> Dict[str, Any]:
        """初始化证据模式"""
        return {}
    
    @staticmethod
    def has_numerical_answer(answer: str) -> bool:
        """检查答案是否包含数字"""
        return bool(re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', answer))
    
    @staticmethod
    def has_ranking_answer(answer: str) -> bool:
        """检查答案是否是排名"""
        ordinal_pattern = r'\b\d+(?:st|nd|rd|th)\b'
        ranking_keywords = ['rank', 'position', 'ordinal', '第', '排名', 'th', 'st', 'nd', 'rd']
        return bool(re.search(ordinal_pattern, answer, re.IGNORECASE) or 
                   any(keyword in answer.lower() for keyword in ranking_keywords))
    
    @staticmethod
    def calculate_completeness(answer: str, query_type: str) -> float:
        """计算答案完整性"""
        try:
            if not answer or len(answer.strip()) == 0:
                return 0.0
            
            # 基础完整性（基于长度）
            answer_length = len(answer.strip())
            min_length = 1
            max_length = 300
            
            if answer_length < min_length:
                length_score = 0.0
            elif answer_length > max_length:
                length_score = 1.0
            else:
                length_score = min(1.0, answer_length / 50.0)  # 50字符为满分
            
            # 类型特定完整性检查
            type_score = 1.0
            if query_type == 'numerical':
                # 数值查询：检查是否包含数字
                if not Utils.has_numerical_answer(answer):
                    type_score = 0.5
            elif query_type == 'ranking':
                # 排名查询：检查是否包含排名格式
                if not Utils.has_ranking_answer(answer):
                    type_score = 0.5
            elif query_type in ['person_name', 'entity']:
                # 人名/实体查询：检查是否包含多个词（完整姓名）
                words = answer.strip().split()
                if len(words) < 2:
                    type_score = 0.7  # 单名也可以，但完整姓名更好
            
            # 综合完整性分数
            completeness = (length_score * 0.6 + type_score * 0.4)
            return min(1.0, max(0.0, completeness))
            
        except Exception as e:
            logger.debug(f"计算答案完整性失败: {e}")
            return 0.5
    
    @staticmethod
    def calculate_type_match(answer: str, query_type: str) -> float:
        """计算答案类型匹配度"""
        try:
            if not answer or not query_type:
                return 0.5
            
            answer_lower = answer.lower().strip()
            
            # 根据查询类型检查答案格式
            if query_type == 'numerical':
                # 数值查询：答案应该包含数字
                if Utils.has_numerical_answer(answer):
                    return 1.0
                else:
                    return 0.3
            elif query_type == 'ranking':
                # 排名查询：答案应该包含排名格式
                if Utils.has_ranking_answer(answer):
                    return 1.0
                else:
                    return 0.3
            elif query_type in ['person_name', 'entity']:
                # 人名/实体查询：答案应该包含字母（不是纯数字）
                if re.search(r'[a-zA-Z]', answer):
                    return 1.0
                else:
                    return 0.3
            else:
                # 其他类型：默认匹配
                return 0.8
                
        except Exception as e:
            logger.debug(f"计算类型匹配失败: {e}")
            return 0.5
    
    @staticmethod
    def get_warning_threshold(is_reasoner: bool = False) -> float:
        """获取警告阈值"""
        try:
            # 从环境变量读取，如果没有则使用默认值
            if is_reasoner:
                threshold = float(os.getenv('REASONER_WARNING_THRESHOLD', '0.3'))
            else:
                threshold = float(os.getenv('WARNING_THRESHOLD', '0.5'))
            return threshold
        except Exception as e:
            logger.debug(f"获取警告阈值失败: {e}")
            return 0.5 if not is_reasoner else 0.3
    
    @staticmethod
    def get_evidence_target_length(query: str, query_type: str = "general", config_center=None) -> int:
        """基于查询特征确定证据目标长度"""
        try:
            # 策略1: 使用配置中心（如果可用）
            if config_center:
                try:
                    config_length = config_center.get_config_value(
                        "evidence_processing", "target_length_by_characteristic", {}
                    )
                    if config_length:
                        if 'numerical' in query_type or 'ranking' in query_type:
                            return config_length.get('numerical', 3000)
                        elif 'entity' in query_type or 'person_name' in query_type:
                            return config_length.get('entity', 2000)
                        else:
                            return config_length.get('default', 1500)
                except Exception:
                    pass
            
            # 策略2: 基于查询复杂度动态调整
            query_complexity = len(query.split())
            if query_complexity > 15:
                return 1500
            elif query_complexity > 8:
                return 1200
            else:
                return 1000
                
        except Exception as e:
            logger.debug(f"确定证据目标长度失败: {e}")
            return 1000
    
    @staticmethod
    def is_ranking_query(query: str, query_type: str = "general") -> bool:
        """判断是否是排名查询"""
        try:
            # 检查查询中是否包含排名关键词
            ranking_keywords = ['rank', 'ranking', 'position', 'ordinal', '第', '排名', 'th', 'st', 'nd', 'rd', 'first', 'second', 'third']
            query_lower = query.lower()
            
            # 检查是否包含排名关键词
            if any(keyword in query_lower for keyword in ranking_keywords):
                return True
            
            # 检查是否包含序数词模式
            ordinal_pattern = r'\b\d+(?:st|nd|rd|th)\b'
            if re.search(ordinal_pattern, query, re.IGNORECASE):
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"判断排名查询失败: {e}")
            return False
    
    @staticmethod
    def extract_query_features(query: str, query_type: Optional[str] = None) -> Dict[str, Any]:
        """提取查询特征"""
        try:
            features = {
                'length': len(query),
                'word_count': len(query.split()),
                'has_numbers': bool(re.search(r'\d+', query)),
                'has_question_words': bool(re.search(r'\b(what|who|where|when|why|how|which|whose|whom)\b', query, re.IGNORECASE)),
                'is_ranking': Utils.is_ranking_query(query, query_type or "general"),
                'has_numerical': Utils.has_numerical_answer(query),
                'query_type': query_type or "general"
            }
            return features
        except Exception as e:
            logger.debug(f"提取查询特征失败: {e}")
            return {}
    
    @staticmethod
    def detect_answer_type(answer: str) -> str:
        """检测答案类型"""
        try:
            if not answer:
                return "general"
            
            answer_lower = answer.lower().strip()
            
            # 检查是否是数值
            if Utils.has_numerical_answer(answer):
                if Utils.has_ranking_answer(answer):
                    return "ranking"
                else:
                    return "numerical"
            
            # 检查是否是人名（包含大写字母开头的多个词）
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', answer.strip()):
                return "person_name"
            
            # 检查是否是地点（包含常见地点关键词）
            location_keywords = ['city', 'country', 'state', 'province', 'region', 'city', 'town', 'village']
            if any(keyword in answer_lower for keyword in location_keywords):
                return "location"
            
            return "general"
            
        except Exception as e:
            logger.debug(f"检测答案类型失败: {e}")
            return "general"


# 为了向后兼容，提供函数形式的接口
def extract_query_features(query: str, query_type: Optional[str] = None) -> Dict[str, Any]:
    """提取查询特征（函数形式）"""
    return Utils.extract_query_features(query, query_type)


def detect_answer_type(answer: str) -> str:
    """检测答案类型（函数形式）"""
    return Utils.detect_answer_type(answer)

