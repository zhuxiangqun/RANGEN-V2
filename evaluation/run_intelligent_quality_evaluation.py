#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能质量分析系统（集成评估系统）

完全独立于核心系统的智能质量分析工具，集成了评估系统功能。
支持从根目录或evaluation目录运行。
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime

# 智能路径检测：支持从根目录或evaluation目录运行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir.endswith('evaluation'):
    # 如果在evaluation目录中运行，添加当前目录到路径
    sys.path.insert(0, current_dir)
else:
    # 如果在根目录中运行，添加evaluation目录到路径
    evaluation_dir = os.path.join(current_dir, 'evaluation')
    sys.path.insert(0, evaluation_dir)

# 导入智能质量分析器
from benchmarks.intelligent_quality_evaluator import IntelligentQualityAnalyzer

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('intelligent_quality_evaluation.log', encoding='utf-8')
        ]
    )

async def run_intelligent_quality_evaluation(args):
    """运行智能质量评测 - 集成评估系统"""
    logger = logging.getLogger(__name__)
    logger.info("开始智能质量评测（集成评估系统）")
    
    # 智能检测src目录位置
    current_dir = os.getcwd()
    src_path = "src"
    if not os.path.exists(src_path):
        # 如果在evaluation目录中，尝试上级目录的src
        if current_dir.endswith('evaluation'):
            src_path = os.path.join(os.path.dirname(current_dir), "src")
        else:
            src_path = os.path.join(current_dir, "src")
        if not os.path.exists(src_path):
            logger.error(f"未找到src目录，当前目录: {current_dir}")
            return 1
    
    logger.info(f"使用源码路径: {src_path}")
    
    # 初始化智能质量分析器（完全独立，不依赖核心系统）
    analyzer = IntelligentQualityAnalyzer(
        source_path=src_path,
        use_progressive=args.use_progressive,
        max_files=args.sample_count
    )
    
    # 运行综合评估（质量分析 + 评估系统）
    logger.info("运行综合评估...")
    
    try:
        # 生成并显示报告
        analyzer.generate_and_display_report()
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建成功结果
        comprehensive_results = {
            "success": True,
            "timestamp": timestamp,
            "message": "智能质量分析完成"
        }
        
    except Exception as e:
        logger.error(f"综合评估失败: {e}")
        return 1
    
    # 生成并保存报告
    logger.info("生成综合评估报告...")
    
    # 保存JSON报告
    json_report_file = f"intelligent_quality_comprehensive_evaluation_{timestamp}.json"
    
    with open(json_report_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    analyzer.generate_and_display_report()
    
    # 打印结果摘要
    print_comprehensive_evaluation_summary(comprehensive_results, json_report_file)
    
    logger.info("智能质量评测（集成评估系统）完成")
    return 0

def print_comprehensive_evaluation_summary(results, report_file: str):
    """打印综合评估结果摘要"""
    print("\n" + "="*80)
    print("🧠 智能质量分析系统 - 综合评估结果摘要")
    print("="*80)
    
    # 质量分析摘要
    quality_analysis = results.get('quality_analysis', {})
    if quality_analysis is None:
        quality_analysis = {}
    print(f"📊 质量分析维度: {len(quality_analysis)} 个")
    
    # 评估结果摘要
    evaluation_results = results.get('evaluation_results', {})
    if evaluation_results is None:
        evaluation_results = {}
    print(f"🔍 评估测试: {len(evaluation_results)} 个")
    
    # 总体摘要
    summary = results.get('summary', {})
    total_score = summary.get('total_quality_score', 0)
    evaluation_status = summary.get('evaluation_status', 'unknown')
    
    print(f"📈 总体质量分数: {total_score:.3f}")
    print(f"✅ 评估状态: {evaluation_status}")
    
    # 建议
    recommendations = summary.get('recommendations', [])
    if recommendations:
        print(f"\n💡 改进建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    print("="*80)

async def main():
    """主函数 - 智能质量分析系统（集成评估系统）"""
    parser = argparse.ArgumentParser(
        description='RANGEN智能质量分析系统（集成评估系统）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_intelligent_quality_evaluation.py                    # 默认运行（评测所有文件）
  python run_intelligent_quality_evaluation.py --sample-count 50  # 评测50个文件样本
  python run_intelligent_quality_evaluation.py --use-progressive  # 使用渐进式分析
  python run_intelligent_quality_evaluation.py --show-dimensions  # 显示支持的质量维度
        """
    )
    
    parser.add_argument('--use-progressive', action='store_true',
                       help='使用渐进式分析器')
    parser.add_argument('--show-dimensions', action='store_true',
                       help='显示支持的质量维度')
    parser.add_argument('--sample-count', type=int, default=None,
                       help='评测文件样本数量（默认评测所有文件）')
    
    args = parser.parse_args()
    
    if args.show_dimensions:
        print_quality_dimensions()
        return 0
    
    return await run_intelligent_quality_evaluation(args)

def print_quality_dimensions():
    """打印质量维度说明"""
    print("\n🔍 智能质量分析系统 - 支持的质量维度:")
    print("-" * 60)
    
    dimensions = [
        ("🏗️ 架构质量", "模块耦合度、接口一致性、循环依赖检测"),
        ("⚡ 性能质量", "算法复杂度、资源使用、响应时间"),
        ("🧠 智能化程度", "伪智能检测、真实智能功能、学习能力"),
        ("🔒 安全性", "输入验证、错误处理、权限控制"),
        ("🔧 可维护性", "代码复杂度、文档完整性、模块化程度"),
        ("🧪 可测试性", "单元测试、集成测试、测试覆盖率"),
        ("📊 监控质量", "日志记录、性能监控、错误追踪"),
        ("📚 文档质量", "API文档、代码注释、用户手册"),
        ("🔗 集成质量", "模块集成、接口兼容性、数据流"),
        ("🔌 扩展性", "插件架构、配置灵活性、API设计")
    ]
    
    for dim, desc in dimensions:
        print(f"{dim:15} | {desc}")
    
    print("-" * 60)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())