#!/usr/bin/env python3
"""
分析失败样本的共同特征 - 使用评测系统的分析逻辑
"""

import re
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation_system.analyzers.frames_analyzer import FramesAnalyzer

def analyze_failed_samples(log_file: str = "research_system.log") -> dict:
    """使用评测系统的分析器分析失败样本"""
    
    # 读取日志文件
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # 使用FramesAnalyzer提取答案
    analyzer = FramesAnalyzer()
    frames_result = analyzer.analyze(log_content)
    
    # 提取期望答案和实际答案
    accuracy_result = frames_result.get('accuracy', {})
    expected_answers = accuracy_result.get('expected_answers', [])
    actual_answers = accuracy_result.get('actual_answers', [])
    
    # 计算每个样本的匹配情况
    failed_samples = []
    sample_data = {}
    
    # 从日志中提取样本信息
    sample_pattern = r'FRAMES sample=(\d+)/(\d+)\s+started.*?query=({[^}]+}|[^,]+)'
    sample_matches = list(re.finditer(sample_pattern, log_content, re.DOTALL))
    
    for i, match in enumerate(sample_matches):
        sample_id = int(match.group(1))
        query_text = match.group(3).strip()
        
        # 获取对应的期望答案和实际答案
        expected = expected_answers[i] if i < len(expected_answers) else None
        actual = actual_answers[i] if i < len(actual_answers) else None
        
        # 判断是否匹配
        is_match = False
        if expected and actual:
            # 使用analyzer的匹配逻辑
            match_result = analyzer._intelligent_match(
                expected.lower().strip(),
                actual.lower().strip()
            )
            is_match = match_result.get('exact_match', False)
        
        sample_info = {
            'id': sample_id,
            'query': query_text[:200] if len(query_text) > 200 else query_text,
            'expected_answer': expected,
            'actual_answer': actual,
            'is_match': is_match,
            'match_result': match_result if expected and actual else None
        }
        
        sample_data[sample_id] = sample_info
        
        if not is_match:
            failed_samples.append(sample_info)
    
    # 分析共同特征
    analysis = {
        'total_samples': len(sample_data),
        'total_failed': len(failed_samples),
        'failure_rate': len(failed_samples) / len(sample_data) if sample_data else 0,
        'common_features': {}
    }
    
    if not failed_samples:
        return analysis
    
    # 1. 查询长度分析
    query_lengths = [len(s['query']) for s in failed_samples if s['query']]
    if query_lengths:
        analysis['common_features']['query_length'] = {
            'avg': sum(query_lengths) / len(query_lengths),
            'min': min(query_lengths),
            'max': max(query_lengths),
            'median': sorted(query_lengths)[len(query_lengths) // 2]
        }
    
    # 2. 查询关键词分析
    query_keywords = defaultdict(int)
    common_words = ['who', 'what', 'when', 'where', 'why', 'how', 'which', '多少', '什么', '谁', '哪里', '何时', '为什么', '如何', 'name', 'number', 'year', 'first', 'last']
    for sample in failed_samples:
        if sample['query']:
            query_lower = sample['query'].lower()
            for word in common_words:
                if word.lower() in query_lower:
                    query_keywords[word] += 1
    analysis['common_features']['query_keywords'] = dict(sorted(query_keywords.items(), key=lambda x: x[1], reverse=True)[:15])
    
    # 3. 答案类型分析
    answer_types = defaultdict(int)
    for sample in failed_samples:
        if sample['expected_answer']:
            expected = sample['expected_answer'].strip()
            if expected.replace(',', '').replace('.', '').isdigit():
                answer_types['numerical'] += 1
            elif len(expected.split()) <= 2 and expected[0].isupper():
                answer_types['name/person'] += 1
            elif len(expected.split()) <= 3:
                answer_types['short'] += 1
            else:
                answer_types['long'] += 1
    analysis['common_features']['answer_types'] = dict(answer_types)
    
    # 4. 答案长度分析
    expected_lengths = [len(s['expected_answer']) for s in failed_samples if s['expected_answer']]
    actual_lengths = [len(s['actual_answer']) for s in failed_samples if s['actual_answer']]
    if expected_lengths:
        analysis['common_features']['expected_answer_length'] = {
            'avg': sum(expected_lengths) / len(expected_lengths),
            'min': min(expected_lengths),
            'max': max(expected_lengths)
        }
    if actual_lengths:
        analysis['common_features']['actual_answer_length'] = {
            'avg': sum(actual_lengths) / len(actual_lengths),
            'min': min(actual_lengths),
            'max': max(actual_lengths)
        }
    
    # 5. 匹配方法分析（如果可用）
    match_methods = defaultdict(int)
    for sample in failed_samples:
        if sample.get('match_result'):
            method = sample['match_result'].get('method', 'no_match')
            match_methods[method] += 1
    if match_methods:
        analysis['common_features']['match_methods'] = dict(match_methods)
    
    # 6. 答案相似度分析
    similarities = []
    for sample in failed_samples:
        if sample.get('match_result'):
            sim = sample['match_result'].get('similarity', 0)
            similarities.append(sim)
    if similarities:
        analysis['common_features']['similarity'] = {
            'avg': sum(similarities) / len(similarities),
            'min': min(similarities),
            'max': max(similarities),
            'median': sorted(similarities)[len(similarities) // 2]
        }
    
    # 7. 查询模式分析
    query_patterns = defaultdict(int)
    patterns = [
        (r'\bwho\b', 'who_question'),
        (r'\bwhat\b', 'what_question'),
        (r'\bwhen\b', 'when_question'),
        (r'\bwhere\b', 'where_question'),
        (r'\bhow\s+many\b', 'how_many_question'),
        (r'\bhow\s+long\b', 'how_long_question'),
        (r'\bfirst\b', 'first_question'),
        (r'\blast\b', 'last_question'),
        (r'\bname\b', 'name_question'),
        (r'\byear\b', 'year_question'),
        (r'\bnumber\b', 'number_question'),
    ]
    for sample in failed_samples:
        if sample['query']:
            query_lower = sample['query'].lower()
            for pattern, label in patterns:
                if re.search(pattern, query_lower):
                    query_patterns[label] += 1
    analysis['common_features']['query_patterns'] = dict(sorted(query_patterns.items(), key=lambda x: x[1], reverse=True))
    
    # 8. 样本示例（前20个）
    analysis['sample_examples'] = []
    for sample in failed_samples[:20]:
        analysis['sample_examples'].append({
            'id': sample['id'],
            'query': sample['query'][:150] if sample['query'] else None,
            'expected_answer': sample['expected_answer'],
            'actual_answer': sample['actual_answer'],
            'similarity': sample['match_result'].get('similarity', 0) if sample.get('match_result') else 0,
            'match_method': sample['match_result'].get('method', 'no_match') if sample.get('match_result') else 'no_match'
        })
    
    return analysis

if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "research_system.log"
    
    if not Path(log_file).exists():
        print(f"错误: 日志文件 {log_file} 不存在")
        sys.exit(1)
    
    print(f"正在分析日志文件: {log_file}")
    analysis = analyze_failed_samples(log_file)
    
    # 输出结果
    output_file = "comprehensive_eval_results/failed_samples_analysis.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析完成！结果已保存到: {output_file}")
    print(f"\n失败样本统计:")
    print(f"  总样本数: {analysis['total_samples']}")
    print(f"  失败样本数: {analysis['total_failed']}")
    print(f"  失败率: {analysis['failure_rate']*100:.2f}%")
    
    if analysis['common_features'].get('query_keywords'):
        print(f"\n最常见的查询关键词:")
        for keyword, count in list(analysis['common_features']['query_keywords'].items())[:10]:
            print(f"  - {keyword}: {count}次")
    
    if analysis['common_features'].get('answer_types'):
        print(f"\n答案类型分布:")
        for atype, count in analysis['common_features']['answer_types'].items():
            print(f"  - {atype}: {count}次")

