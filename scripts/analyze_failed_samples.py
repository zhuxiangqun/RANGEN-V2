#!/usr/bin/env python3
"""
分析失败样本的共同特征
"""

import re
import json
from collections import Counter, defaultdict
from typing import Dict, List, Any
from pathlib import Path

def analyze_failed_samples(log_file: str = "research_system.log") -> Dict[str, Any]:
    """分析失败样本的共同特征"""
    
    failed_samples = []
    sample_data = {}
    current_sample_id = None
    
    # 读取日志文件
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 查找样本ID
            sample_match = re.search(r'样本ID[=:](\d+)|FRAMES sample[=:](\d+)/(\d+)', line)
            if sample_match:
                sample_id = sample_match.group(1) or sample_match.group(2)
                current_sample_id = sample_id
                if sample_id not in sample_data:
                    sample_data[sample_id] = {
                        'id': sample_id,
                        'success': True,
                        'queries': [],
                        'answers': [],
                        'expected_answers': [],
                        'errors': [],
                        'processing_times': [],
                        'query_types': [],
                        'evidence_counts': [],
                        'confidence_scores': []
                    }
            
            if current_sample_id and current_sample_id in sample_data:
                sample = sample_data[current_sample_id]
                
                # 提取查询
                query_match = re.search(r'查询接收.*?query[=:]([^,}]+)', line, re.IGNORECASE)
                if query_match:
                    query = query_match.group(1).strip().strip('"\'')
                    if query and query not in sample['queries']:
                        sample['queries'].append(query)
                
                # 提取答案
                answer_match = re.search(r'答案[=:]([^,}]+)|answer[=:]([^,}]+)', line, re.IGNORECASE)
                if answer_match:
                    answer = (answer_match.group(1) or answer_match.group(2)).strip().strip('"\'')
                    if answer and answer not in sample['answers']:
                        sample['answers'].append(answer)
                
                # 提取期望答案
                expected_match = re.search(r'期望答案[=:]([^,}]+)|expected[=:]([^,}]+)', line, re.IGNORECASE)
                if expected_match:
                    expected = (expected_match.group(1) or expected_match.group(2)).strip().strip('"\'')
                    if expected and expected not in sample['expected_answers']:
                        sample['expected_answers'].append(expected)
                
                # 检查成功/失败 - 通过比较期望答案和实际答案
                # 如果期望答案和实际答案都存在，比较它们
                if sample['expected_answers'] and sample['answers']:
                    # 简单比较：如果答案不匹配，标记为失败
                    expected = sample['expected_answers'][0].lower().strip() if sample['expected_answers'] else ''
                    actual = sample['answers'][0].lower().strip() if sample['answers'] else ''
                    if expected and actual:
                        # 如果答案不匹配，标记为失败
                        if expected != actual and expected not in actual and actual not in expected:
                            sample['success'] = False
                        else:
                            sample['success'] = True
                
                # 检查成功/失败标记（如果存在）
                if '查询完成' in line:
                    if 'success=False' in line or 'success=false' in line:
                        sample['success'] = False
                    elif 'success=True' in line or 'success=true' in line:
                        sample['success'] = True
                
                # 检查FRAMES样本标记
                frames_match = re.search(r'FRAMES sample=(\d+)/\d+\s+success=(True|False)', line)
                if frames_match:
                    sample_id = frames_match.group(1)
                    if sample_id in sample_data:
                        sample_data[sample_id]['success'] = frames_match.group(2) == 'True'
                
                # 提取错误信息
                if 'error' in line.lower() or '失败' in line or 'exception' in line.lower():
                    error_match = re.search(r'(error|exception|失败)[:=]([^,\n}]+)', line, re.IGNORECASE)
                    if error_match:
                        error = error_match.group(2).strip().strip('"\'')
                        if error and error not in sample['errors']:
                            sample['errors'].append(error)
                
                # 提取处理时间
                time_match = re.search(r'耗时[=:](\d+\.?\d*)\s*秒|processing_time[=:](\d+\.?\d*)', line, re.IGNORECASE)
                if time_match:
                    time_val = float(time_match.group(1) or time_match.group(2))
                    sample['processing_times'].append(time_val)
                
                # 提取查询类型
                type_match = re.search(r'query_type[=:]([^,}]+)|查询类型[=:]([^,}]+)', line, re.IGNORECASE)
                if type_match:
                    qtype = (type_match.group(1) or type_match.group(2)).strip().strip('"\'')
                    if qtype and qtype not in sample['query_types']:
                        sample['query_types'].append(qtype)
                
                # 提取证据数量
                evidence_match = re.search(r'evidence_count[=:](\d+)|证据数量[=:](\d+)', line, re.IGNORECASE)
                if evidence_match:
                    count = int(evidence_match.group(1) or evidence_match.group(2))
                    sample['evidence_counts'].append(count)
                
                # 提取置信度
                conf_match = re.search(r'confidence[=:](\d+\.?\d*)|置信度[=:](\d+\.?\d*)', line, re.IGNORECASE)
                if conf_match:
                    conf = float(conf_match.group(1) or conf_match.group(2))
                    sample['confidence_scores'].append(conf)
    
    # 筛选失败样本
    failed_samples = [s for s in sample_data.values() if not s['success']]
    
    # 分析共同特征
    analysis = {
        'total_failed': len(failed_samples),
        'total_samples': len(sample_data),
        'failure_rate': len(failed_samples) / len(sample_data) if sample_data else 0,
        'common_features': {}
    }
    
    if not failed_samples:
        return analysis
    
    # 1. 错误类型统计
    all_errors = []
    for sample in failed_samples:
        all_errors.extend(sample['errors'])
    error_counter = Counter(all_errors)
    analysis['common_features']['error_types'] = dict(error_counter.most_common(10))
    
    # 2. 查询类型统计
    all_query_types = []
    for sample in failed_samples:
        all_query_types.extend(sample['query_types'] if sample['query_types'] else ['unknown'])
    query_type_counter = Counter(all_query_types)
    analysis['common_features']['query_types'] = dict(query_type_counter.most_common(10))
    
    # 3. 查询长度分析
    query_lengths = []
    for sample in failed_samples:
        for query in sample['queries']:
            query_lengths.append(len(query))
    if query_lengths:
        analysis['common_features']['query_length'] = {
            'avg': sum(query_lengths) / len(query_lengths),
            'min': min(query_lengths),
            'max': max(query_lengths),
            'median': sorted(query_lengths)[len(query_lengths) // 2]
        }
    
    # 4. 处理时间分析
    all_processing_times = []
    for sample in failed_samples:
        all_processing_times.extend(sample['processing_times'])
    if all_processing_times:
        analysis['common_features']['processing_time'] = {
            'avg': sum(all_processing_times) / len(all_processing_times),
            'min': min(all_processing_times),
            'max': max(all_processing_times),
            'median': sorted(all_processing_times)[len(all_processing_times) // 2]
        }
    
    # 5. 证据数量分析
    all_evidence_counts = []
    for sample in failed_samples:
        all_evidence_counts.extend(sample['evidence_counts'])
    if all_evidence_counts:
        analysis['common_features']['evidence_count'] = {
            'avg': sum(all_evidence_counts) / len(all_evidence_counts),
            'min': min(all_evidence_counts),
            'max': max(all_evidence_counts),
            'median': sorted(all_evidence_counts)[len(all_evidence_counts) // 2]
        }
    else:
        analysis['common_features']['evidence_count'] = {
            'note': '大多数失败样本没有证据数量记录'
        }
    
    # 6. 置信度分析
    all_confidence = []
    for sample in failed_samples:
        all_confidence.extend(sample['confidence_scores'])
    if all_confidence:
        analysis['common_features']['confidence'] = {
            'avg': sum(all_confidence) / len(all_confidence),
            'min': min(all_confidence),
            'max': max(all_confidence),
            'median': sorted(all_confidence)[len(all_confidence) // 2]
        }
    
    # 7. 答案特征分析
    answer_lengths = []
    empty_answers = 0
    for sample in failed_samples:
        if not sample['answers']:
            empty_answers += 1
        for answer in sample['answers']:
            answer_lengths.append(len(answer))
    analysis['common_features']['answer_characteristics'] = {
        'empty_answer_rate': empty_answers / len(failed_samples) if failed_samples else 0,
        'avg_length': sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0,
        'min_length': min(answer_lengths) if answer_lengths else 0,
        'max_length': max(answer_lengths) if answer_lengths else 0
    }
    
    # 8. 查询关键词分析
    query_keywords = defaultdict(int)
    common_words = ['who', 'what', 'when', 'where', 'why', 'how', 'which', '多少', '什么', '谁', '哪里', '何时', '为什么', '如何']
    for sample in failed_samples:
        for query in sample['queries']:
            query_lower = query.lower()
            for word in common_words:
                if word.lower() in query_lower:
                    query_keywords[word] += 1
    analysis['common_features']['query_keywords'] = dict(sorted(query_keywords.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # 9. 样本示例（前10个）
    analysis['sample_examples'] = []
    for sample in failed_samples[:10]:
        analysis['sample_examples'].append({
            'id': sample['id'],
            'queries': sample['queries'][:3],  # 只取前3个查询
            'answers': sample['answers'][:3],
            'expected_answers': sample['expected_answers'][:3],
            'errors': sample['errors'][:3],
            'query_types': sample['query_types']
        })
    
    return analysis

if __name__ == "__main__":
    import sys
    
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
    
    if analysis['common_features'].get('error_types'):
        print(f"\n最常见的错误类型:")
        for error, count in list(analysis['common_features']['error_types'].items())[:5]:
            print(f"  - {error}: {count}次")

