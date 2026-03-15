#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一评测运行脚本

支持运行不同类型的评测：FRAMES、统一评测、性能评测等。
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.benchmarks.frames_evaluator import FramesEvaluator
from evaluation.benchmarks.unified_evaluator import UnifiedEvaluator
from evaluation.benchmarks.performance_evaluator import PerformanceEvaluator
from evaluation.benchmarks.intelligent_quality_evaluator import IntelligentQualityAnalyzer
from evaluation.adapters.research_system_adapter import ResearchSystemAdapter
from evaluation.reports.report_generator import ReportGenerator

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('evaluation.log', encoding='utf-8')
        ]
    )

async def run_frames_evaluation(args):
    """运行FRAMES评测"""
    logger = logging.getLogger(__name__)
    logger.info("开始FRAMES基准评测")
    
    # 初始化研究系统适配器
    research_adapter = ResearchSystemAdapter()
    
    # 检查系统状态
    system_info = research_adapter.get_system_info()
    if system_info.get('status') != 'available':
        logger.error(f"研究系统不可用: {system_info}")
        return 1
    
    # 初始化FRAMES评测器
    evaluator = FramesEvaluator(
        research_system=research_adapter,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent
    )
    
    # 设置数据集路径
    if args.data_path:
        evaluator.dataset_loader.data_path = args.data_path
    
    # 执行评测
    report = await evaluator.evaluate(sample_count=args.sample_count)
    
    # 生成报告
    report_generator = ReportGenerator()
    report_content = report_generator.generate_report(report, format="markdown")
    
    # 保存报告
    report_file = os.path.join(args.output_dir, f"frames_evaluation_report_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.md")
    report_generator.save_report(report, report_file, format="markdown")
    
    # 打印结果摘要
    print_evaluation_summary("FRAMES基准评测", report, report_file)
    
    return 0

async def run_unified_evaluation(args):
    """运行统一评测"""
    logger = logging.getLogger(__name__)
    logger.info("开始统一评测")
    
    # 初始化研究系统适配器
    research_adapter = ResearchSystemAdapter()
    
    # 检查系统状态
    system_info = research_adapter.get_system_info()
    if system_info.get('status') != 'available':
        logger.error(f"研究系统不可用: {system_info}")
        return 1
    
    # 初始化统一评测器
    evaluator = UnifiedEvaluator(
        research_system=research_adapter,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent
    )
    
    # 设置数据集路径
    if args.data_path:
        evaluator.dataset_loader.data_path = args.data_path
    
    # 执行评测
    report = await evaluator.evaluate(sample_count=args.sample_count)
    
    # 生成报告
    report_generator = ReportGenerator()
    report_content = report_generator.generate_report(report, format="markdown")
    
    # 保存报告
    report_file = os.path.join(args.output_dir, f"unified_evaluation_report_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.md")
    report_generator.save_report(report, report_file, format="markdown")
    
    # 打印结果摘要
    print_evaluation_summary("统一评测", report, report_file)
    
    return 0

async def run_performance_evaluation(args):
    """运行性能评测"""
    logger = logging.getLogger(__name__)
    logger.info("开始性能评测")
    
    # 初始化研究系统适配器
    research_adapter = ResearchSystemAdapter()
    
    # 检查系统状态
    system_info = research_adapter.get_system_info()
    if system_info.get('status') != 'available':
        logger.error(f"研究系统不可用: {system_info}")
        return 1
    
    # 初始化性能评测器
    evaluator = PerformanceEvaluator(
        research_system=research_adapter,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent
    )
    
    # 设置数据集路径
    if args.data_path:
        evaluator.dataset_loader.data_path = args.data_path
    
    # 执行评测
    report = await evaluator.evaluate(sample_count=args.sample_count)
    
    # 生成报告
    report_generator = ReportGenerator()
    report_content = report_generator.generate_report(report, format="markdown")
    
    # 保存报告
    report_file = os.path.join(args.output_dir, f"performance_evaluation_report_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.md")
    report_generator.save_report(report, report_file, format="markdown")
    
    # 打印结果摘要
    print_evaluation_summary("性能评测", report, report_file)
    
    return 0

async def run_intelligent_quality_evaluation(args):
    """运行智能质量评测"""
    logger = logging.getLogger(__name__)
    logger.info("开始智能质量评测")
    
    # 智能质量分析系统完全独立，不需要研究系统适配器
    logger.info("智能质量分析系统独立运行，无需外部依赖")
    
    # 初始化智能质量评测器
    evaluator = IntelligentQualityAnalyzer(use_progressive=False)
    
    # 生成并显示详细的质量分析报告
    evaluator.generate_and_display_report()
    
    logger.info("智能质量评测完成")
    return 0

def print_evaluation_summary(evaluation_type: str, report, report_file: str):
    """打印评测结果摘要"""
    success_rate = (report.successful_queries / report.total_queries * 100) if report.total_queries > 0 else 0
    
    print("\n" + "="*60)
    print(f"{evaluation_type}结果摘要")
    print("="*60)
    print(f"总查询数: {report.total_queries}")
    print(f"成功数: {report.successful_queries}")
    print(f"失败数: {report.failed_queries}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均准确率: {report.average_accuracy:.3f}")
    print(f"平均执行时间: {report.average_execution_time:.2f}秒")
    print(f"报告文件: {report_file}")
    print("="*60)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RANGEN评测系统')
    parser.add_argument('--type', choices=['frames', 'unified', 'performance', 'intelligent_quality'], 
                       default='frames', help='评测类型')
    parser.add_argument('--sample-count', type=int, default=50, help='评测样本数量')
    parser.add_argument('--timeout', type=float, default=30.0, help='单个查询超时时间')
    parser.add_argument('--max-concurrent', type=int, default=3, help='最大并发数')
    parser.add_argument('--data-path', type=str, help='数据集路径')
    parser.add_argument('--output-dir', type=str, default='evaluation_results', help='输出目录')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    try:
        # 创建输出目录
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 根据评测类型运行相应的评测
        if args.type == 'frames':
            return await run_frames_evaluation(args)
        elif args.type == 'unified':
            return await run_unified_evaluation(args)
        elif args.type == 'performance':
            return await run_performance_evaluation(args)
        elif args.type == 'intelligent_quality':
            return await run_intelligent_quality_evaluation(args)
        else:
            print(f"不支持的评测类型: {args.type}")
            return 1
        
    except Exception as e:
        logging.error(f"评测失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
