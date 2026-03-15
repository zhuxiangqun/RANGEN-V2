#!/usr/bin/env python3
"""
智能模拟数据过滤器
基于代码语义分析，过滤掉合理的"模拟数据"检测
"""

import re
import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass


@dataclass
class MockDataRule:
    """模拟数据规则"""
    name: str
    description: str
    pattern: str
    is_false_positive: bool
    confidence: float = 1.0


class SmartMockDataFilter:
    """智能模拟数据过滤器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.false_positive_rules = self._initialize_false_positive_rules()
        self.true_positive_rules = self._initialize_true_positive_rules()
    
    def _initialize_false_positive_rules(self) -> List[MockDataRule]:
        """初始化误报规则"""
        return [
            # 1. 注释中的示例代码
            MockDataRule(
                name="comment_examples",
                description="注释中的示例代码",
                pattern=r'#.*(mock|test|dummy|fake)',
                is_false_positive=True,
                confidence=1.0
            ),
            
            # 2. 文档字符串中的示例
            MockDataRule(
                name="docstring_examples",
                description="文档字符串中的示例",
                pattern=r'""".*(mock|test|dummy|fake).*"""',
                is_false_positive=True,
                confidence=1.0
            ),
            
            # 3. 检测逻辑中的关键词
            MockDataRule(
                name="detection_logic",
                description="检测逻辑中的关键词",
                pattern=r'(检测|检测到|发现).*(mock|test|dummy|fake)',
                is_false_positive=True,
                confidence=0.9
            ),
            
            # 4. 日志消息中的关键词
            MockDataRule(
                name="log_messages",
                description="日志消息中的关键词",
                pattern=r'(log|logger|print).*(mock|test|dummy|fake)',
                is_false_positive=True,
                confidence=0.8
            ),
            
            # 5. 变量名中的关键词（但不是实际数据）
            MockDataRule(
                name="variable_names",
                description="变量名中的关键词",
                pattern=r'(mock|test|dummy|fake)_(count|num|total|detected)',
                is_false_positive=True,
                confidence=0.7
            ),
            
            # 6. 测试文件中的合理使用
            MockDataRule(
                name="test_files",
                description="测试文件中的合理使用",
                pattern=r'test.*\.py',
                is_false_positive=True,
                confidence=0.6
            ),
            
            # 7. 配置和设置中的关键词
            MockDataRule(
                name="config_settings",
                description="配置和设置中的关键词",
                pattern=r'(config|setting|option).*(mock|test|dummy|fake)',
                is_false_positive=True,
                confidence=0.8
            ),
            
            # 8. 错误处理中的关键词
            MockDataRule(
                name="error_handling",
                description="错误处理中的关键词",
                pattern=r'(except|error|warning).*(mock|test|dummy|fake)',
                is_false_positive=True,
                confidence=0.8
            )
        ]
    
    def _initialize_true_positive_rules(self) -> List[MockDataRule]:
        """初始化真实阳性规则"""
        return [
            # 1. 实际的模拟数据赋值
            MockDataRule(
                name="mock_data_assignment",
                description="实际的模拟数据赋值",
                pattern=r'(mock|test|dummy|fake)\s*=\s*[^#\n]+',
                is_false_positive=False,
                confidence=1.0
            ),
            
            # 2. 模拟数据在函数调用中
            MockDataRule(
                name="mock_data_in_calls",
                description="模拟数据在函数调用中",
                pattern=r'\([^)]*(mock|test|dummy|fake)[^)]*\)',
                is_false_positive=False,
                confidence=0.9
            ),
            
            # 3. 模拟数据在数据结构中
            MockDataRule(
                name="mock_data_in_structures",
                description="模拟数据在数据结构中",
                pattern=r'[\[\{][^\]\}]*["\'](mock|test|dummy|fake)["\'][^\]\}]*[\]\}]',
                is_false_positive=False,
                confidence=0.9
            ),
            
            # 4. 模拟数据在字符串中
            MockDataRule(
                name="mock_data_in_strings",
                description="模拟数据在字符串中",
                pattern=r'["\'][^"\']*(mock|test|dummy|fake)[^"\']*["\']',
                is_false_positive=False,
                confidence=0.8
            )
        ]
    
    def filter_mock_data_issues(self, mock_data_issues: List[Dict[str, Any]], file_content: str) -> List[Dict[str, Any]]:
        """过滤模拟数据问题"""
        filtered_issues = []
        
        for issue in mock_data_issues:
            if self._should_filter_mock_data_issue(issue, file_content):
                self.logger.debug(f"过滤模拟数据误报: {issue.get('description', 'Unknown')}")
                continue
            
            filtered_issues.append(issue)
        
        self.logger.info(f"模拟数据过滤前: {len(mock_data_issues)} 个问题, 过滤后: {len(filtered_issues)} 个问题")
        return filtered_issues
    
    def _should_filter_mock_data_issue(self, issue: Dict[str, Any], file_content: str) -> bool:
        """判断是否应该过滤该模拟数据问题"""
        issue_text = issue.get('text', '')
        issue_line = issue.get('line', '')
        
        # 检查是否是误报
        for rule in self.false_positive_rules:
            if self._matches_rule(issue_text, issue_line, rule):
                return True
        
        # 检查是否是真实阳性
        for rule in self.true_positive_rules:
            if self._matches_rule(issue_text, issue_line, rule):
                return False
        
        # 默认不过滤（保守策略）
        return False
    
    def _matches_rule(self, text: str, line: str, rule: MockDataRule) -> bool:
        """检查文本是否匹配规则"""
        try:
            if re.search(rule.pattern, text, re.IGNORECASE):
                return True
            if re.search(rule.pattern, line, re.IGNORECASE):
                return True
        except re.error as e:
            self.logger.warning(f"正则表达式错误: {rule.pattern}, 错误: {e}")
        
        return False
    
    def analyze_mock_data_context(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """分析文件中的模拟数据上下文"""
        analysis = {
            'total_mock_mentions': 0,
            'false_positives': 0,
            'true_positives': 0,
            'context_analysis': {},
            'recommendations': []
        }
        
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 统计所有模拟数据提及
            mock_mentions = re.findall(r'\b(mock|test|dummy|fake)\b', line_lower)
            analysis['total_mock_mentions'] += len(mock_mentions)
            
            # 分析每一行的上下文
            context = self._analyze_line_context(line, i, lines)
            if context['is_mock_related']:
                if context['is_false_positive']:
                    analysis['false_positives'] += 1
                else:
                    analysis['true_positives'] += 1
                
                analysis['context_analysis'][f'line_{i+1}'] = context
        
        # 生成建议
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_line_context(self, line: str, line_num: int, all_lines: List[str]) -> Dict[str, Any]:
        """分析单行的上下文"""
        context = {
            'is_mock_related': False,
            'is_false_positive': False,
            'context_type': 'unknown',
            'confidence': 0.0
        }
        
        line_lower = line.lower()
        
        # 检查是否包含模拟数据关键词
        if not re.search(r'\b(mock|test|dummy|fake)\b', line_lower):
            return context
        
        context['is_mock_related'] = True
        
        # 检查是否是注释
        if line.strip().startswith('#'):
            context['is_false_positive'] = True
            context['context_type'] = 'comment'
            context['confidence'] = 1.0
            return context
        
        # 检查是否是文档字符串
        if '"""' in line or "'''" in line:
            context['is_false_positive'] = True
            context['context_type'] = 'docstring'
            context['confidence'] = 0.9
            return context
        
        # 检查是否是日志消息
        if any(keyword in line_lower for keyword in ['log', 'logger', 'print', 'debug', 'info']):
            context['is_false_positive'] = True
            context['context_type'] = 'logging'
            context['confidence'] = 0.8
            return context
        
        # 检查是否是检测逻辑
        if any(keyword in line_lower for keyword in ['检测', '发现', '找到', 'count', 'total']):
            context['is_false_positive'] = True
            context['context_type'] = 'detection_logic'
            context['confidence'] = 0.9
            return context
        
        # 检查是否是实际数据使用
        if re.search(r'(mock|test|dummy|fake)\s*[=:]\s*[^#\n]+', line):
            context['is_false_positive'] = False
            context['context_type'] = 'data_assignment'
            context['confidence'] = 0.9
            return context
        
        # 检查是否在函数调用中
        if re.search(r'\([^)]*(mock|test|dummy|fake)[^)]*\)', line):
            context['is_false_positive'] = False
            context['context_type'] = 'function_call'
            context['confidence'] = 0.8
            return context
        
        # 默认情况
        context['is_false_positive'] = True
        context['context_type'] = 'unknown'
        context['confidence'] = 0.5
        
        return context
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        total = analysis['total_mock_mentions']
        false_positives = analysis['false_positives']
        true_positives = analysis['true_positives']
        
        if total == 0:
            recommendations.append("未发现模拟数据相关问题")
            return recommendations
        
        false_positive_rate = false_positives / total if total > 0 else 0
        
        if false_positive_rate > 0.8:
            recommendations.append("大部分模拟数据检测是误报，建议调整检测规则")
        elif false_positive_rate > 0.5:
            recommendations.append("存在较多误报，建议优化检测逻辑")
        else:
            recommendations.append("模拟数据检测相对准确")
        
        if true_positives > 0:
            recommendations.append(f"发现 {true_positives} 个真实的模拟数据问题，需要处理")
        
        return recommendations
