#!/usr/bin/env python3
"""
测试之前出错的样本，验证优化是否起作用
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.unified_research_system import UnifiedResearchSystem, ResearchRequest


async def test_error_samples():
    """测试之前出错的样本"""
    
    # 读取错误样本信息
    error_samples_file = project_root / 'error_samples_to_test.json'
    if not error_samples_file.exists():
        print("❌ 错误样本文件不存在，请先运行提取错误样本的脚本")
        return
    
    with open(error_samples_file, 'r', encoding='utf-8') as f:
        error_samples = json.load(f)
    
    # 读取数据集
    dataset_file = project_root / 'data' / 'frames_dataset.json'
    if not dataset_file.exists():
        print(f"❌ 数据集文件不存在: {dataset_file}")
        return
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # 如果是字典格式，提取samples
    if isinstance(dataset, dict) and 'samples' in dataset:
        dataset = dataset['samples']
    
    print("=" * 80)
    print("测试之前出错的样本")
    print("=" * 80)
    print(f"错误样本数量: {len(error_samples)}")
    print()
    
    # 初始化系统
    print("正在初始化系统...")
    system = UnifiedResearchSystem()
    
    results = []
    
    for error_sample in error_samples:
        idx = error_sample['index'] - 1  # 转换为0-based索引
        expected = error_sample['expected']
        previous_actual = error_sample['actual']
        difference = error_sample['difference']
        
        if idx >= len(dataset):
            print(f"⚠️ 样本{error_sample['index']}索引超出范围，跳过")
            continue
        
        sample = dataset[idx]
        query = sample.get('Prompt') or sample.get('query') or sample.get('question', '')
        
        print(f"\n{'='*80}")
        print(f"测试样本 {error_sample['index']}")
        print(f"{'='*80}")
        print(f"查询: {query}")
        print(f"期望答案: {expected}")
        print(f"之前实际答案: {previous_actual} (差异: {difference})")
        print()
        
        # 创建请求
        request = ResearchRequest(
            query=query,
            context={
                "dataset": "FRAMES",
                "sample_id": error_sample['index'],
                "expected_answer": expected,
                "test_error_sample": True
            },
            timeout=300.0  # 5分钟超时
        )
        
        # 执行查询
        start_time = time.time()
        try:
            result = await system.execute_research(request)
            elapsed_time = time.time() - start_time
            
            actual_answer = result.answer if result else None
            
            # 判断是否正确
            is_correct = False
            if actual_answer:
                # 尝试数值比较
                try:
                    exp_num = float(expected)
                    act_num = float(actual_answer)
                    is_correct = abs(exp_num - act_num) <= 1.0  # 允许1的误差
                except:
                    # 字符串比较
                    is_correct = str(expected).strip().lower() == str(actual_answer).strip().lower()
            
            status = "✅ 正确" if is_correct else "❌ 错误"
            
            print(f"实际答案: {actual_answer}")
            print(f"状态: {status}")
            print(f"耗时: {elapsed_time:.2f}秒")
            
            results.append({
                'index': error_sample['index'],
                'query': query,
                'expected': expected,
                'previous_actual': previous_actual,
                'current_actual': actual_answer,
                'previous_difference': difference,
                'is_correct': is_correct,
                'elapsed_time': elapsed_time,
                'status': status
            })
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ 错误: {e}")
            results.append({
                'index': error_sample['index'],
                'query': query,
                'expected': expected,
                'previous_actual': previous_actual,
                'current_actual': None,
                'previous_difference': difference,
                'is_correct': False,
                'elapsed_time': elapsed_time,
                'error': str(e),
                'status': "❌ 异常"
            })
    
    # 输出总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    correct_count = sum(1 for r in results if r.get('is_correct', False))
    total_count = len(results)
    accuracy = correct_count / total_count if total_count > 0 else 0
    
    print(f"总样本数: {total_count}")
    print(f"正确数: {correct_count}")
    print(f"错误数: {total_count - correct_count}")
    print(f"准确率: {accuracy*100:.2f}%")
    print()
    
    print("详细结果:")
    for r in results:
        print(f"  样本{r['index']}: {r['status']} | 期望={r['expected']} | "
              f"之前={r['previous_actual']} | 现在={r.get('current_actual', 'N/A')}")
    
    # 保存结果
    results_file = project_root / 'error_samples_test_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_samples': total_count,
            'correct_count': correct_count,
            'accuracy': accuracy,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 测试结果已保存到: {results_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_error_samples())

