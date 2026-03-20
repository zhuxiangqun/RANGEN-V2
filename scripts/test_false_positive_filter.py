#!/usr/bin/env python3
"""
测试智能误报过滤器的效果
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from evaluation.benchmarks.analyzers.unimplemented_method_analyzer import UnimplementedMethodAnalyzer
from evaluation.benchmarks.analyzers.smart_false_positive_filter import SmartFalsePositiveFilter
from evaluation.benchmarks.analyzers.smart_mock_data_filter import SmartMockDataFilter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_false_positive_filter():
    """测试误报过滤器"""
    logger.info("🧪 开始测试智能误报过滤器...")
    
    # 获取Python文件列表
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"📁 找到 {len(python_files)} 个Python文件")
    
    # 创建分析器
    analyzer = UnimplementedMethodAnalyzer(python_files)
    
    # 分析所有文件
    logger.info("🔍 开始分析未实现方法...")
    all_issues = []
    
    for file_path in python_files:
        issues = analyzer.analyze_file(file_path)
        all_issues.extend(issues)
    
    logger.info(f"📊 分析完成，发现 {len(all_issues)} 个问题")
    
    # 统计问题类型
    issue_types = {}
    for issue in all_issues:
        issue_type = issue.issue_type.value
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    logger.info("📈 问题类型分布:")
    for issue_type, count in issue_types.items():
        logger.info(f"  {issue_type}: {count} 个")
    
    # 测试误报过滤器
    logger.info("\n🔧 测试误报过滤器...")
    
    # 创建独立的过滤器进行测试
    filter_instance = SmartFalsePositiveFilter()
    
    # 模拟一些测试问题
    test_issues = [
        # 抽象方法（应该被过滤）
        type('TestIssue', (), {
            'issue_type': type('IssueType', (), {'value': 'unimplemented_method'}),
            'description': '方法 get_service 可能缺少重要逻辑',
            'code_snippet': 'def get_service(self, interface: Type):\n    """获取服务实例"""\n    pass',
            'line_number': 10
        })(),
        
        # 设计模式方法（应该被过滤）
        type('TestIssue', (), {
            'issue_type': type('IssueType', (), {'value': 'simplified_implementation'}),
            'description': '方法 create_factory 实现过于简化',
            'code_snippet': 'def create_factory(self):\n    """创建工厂"""\n    return None',
            'line_number': 20
        })(),
        
        # 真实未实现方法（不应该被过滤）
        type('TestIssue', (), {
            'issue_type': type('IssueType', (), {'value': 'unimplemented_method'}),
            'description': '方法 process_data 为空实现',
            'code_snippet': 'def process_data(self, data):\n    """处理数据"""\n    pass',
            'line_number': 30
        })(),
    ]
    
    # 测试过滤效果
    filtered_issues = filter_instance.filter_issues(test_issues, "")
    
    logger.info(f"✅ 过滤测试完成:")
    logger.info(f"  原始问题: {len(test_issues)} 个")
    logger.info(f"  过滤后问题: {len(filtered_issues)} 个")
    logger.info(f"  过滤率: {(len(test_issues) - len(filtered_issues)) / len(test_issues) * 100:.1f}%")
    
    # 测试模拟数据过滤器
    logger.info("\n🔧 测试模拟数据过滤器...")
    
    mock_filter = SmartMockDataFilter()
    
    # 模拟一些测试数据
    test_mock_issues = [
        # 注释中的示例（应该被过滤）
        {
            'text': '# 这里使用mock数据进行测试',
            'line': '# 这里使用mock数据进行测试',
            'description': '发现模拟数据'
        },
        
        # 实际的模拟数据（不应该被过滤）
        {
            'text': 'mock_data = {"test": "value"}',
            'line': 'mock_data = {"test": "value"}',
            'description': '发现模拟数据'
        },
        
        # 检测逻辑中的关键词（应该被过滤）
        {
            'text': '检测到mock数据',
            'line': '检测到mock数据',
            'description': '发现模拟数据'
        }
    ]
    
    filtered_mock_issues = mock_filter.filter_mock_data_issues(test_mock_issues, "")
    
    logger.info(f"✅ 模拟数据过滤测试完成:")
    logger.info(f"  原始问题: {len(test_mock_issues)} 个")
    logger.info(f"  过滤后问题: {len(filtered_mock_issues)} 个")
    logger.info(f"  过滤率: {(len(test_mock_issues) - len(filtered_mock_issues)) / len(test_mock_issues) * 100:.1f}%")
    
    logger.info("\n🎉 误报过滤器测试完成！")

if __name__ == "__main__":
    test_false_positive_filter()
