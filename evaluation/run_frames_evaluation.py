#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRAMES基准评测运行脚本

使用新的分离架构运行FRAMES基准评测。
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

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FRAMES基准评测')
    parser.add_argument('--sample-count', type=int, default=50, help='评测样本数量')
    parser.add_argument('--timeout', type=float, default=30.0, help='单个查询超时时间')
    parser.add_argument('--max-concurrent', type=int, default=3, help='最大并发数')
    parser.add_argument('--data-path', type=str, help='FRAMES数据集路径')
    parser.add_argument('--output-dir', type=str, default='comprehensive_eval_results', help='输出目录')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 创建输出目录
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 初始化研究系统适配器
        research_adapter = ResearchSystemAdapter()
        
        # 检查系统状态
        system_info = research_adapter.get_system_info()
        if system_info.get('status') != 'available':
            logger.error(f"研究系统不可用: {system_info}")
            return 1
        
        logger.info(f"研究系统状态: {system_info}")
        
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
        logger.info(f"开始FRAMES基准评测，样本数量: {args.sample_count}")
        report = await evaluator.evaluate(sample_count=args.sample_count)
        
        # 生成报告
        report_generator = ReportGenerator()
        report_content = report_generator.generate_report(report, format="markdown")
        
        # 保存报告到指定位置
        report_file = os.path.join(args.output_dir, "evaluation_report.md")
        report_generator.save_report(report, report_file, format="markdown")
        
        # 打印结果摘要
        print("\n" + "="*60)
        print("FRAMES基准评测结果摘要")
        print("="*60)
        print(f"总查询数: {report.total_queries}")
        print(f"成功数: {report.successful_queries}")
        print(f"失败数: {report.failed_queries}")
        print(f"成功率: {report.successful_queries/report.total_queries*100:.1f}%" if report.total_queries > 0 else "成功率: 0%")
        print(f"平均准确率: {report.average_accuracy:.3f}")
        print(f"平均执行时间: {report.average_execution_time:.2f}秒")
        print(f"报告文件: {report_file}")
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"FRAMES基准评测失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
