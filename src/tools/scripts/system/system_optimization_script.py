#!/usr/bin/env python3
"""
系统优化脚本
按照硬编码分析报告的建议来优化系统
"""
import os
import sys
import logging
from typing import Dict, List, Any
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_system():
    """执行系统优化"""
    print("🚀 开始系统优化...")
    print("=" * 80)
    
    try:
        # 1. 导入必要的模块
        from src.utils.hardcode_monitor import get_hardcode_monitor
        from src.utils.integrated_code_optimizer import get_integrated_optimizer
        
        # 2. 获取监控器和优化器
        monitor = get_hardcode_monitor()
        optimizer = get_integrated_optimizer()
        
        # 3. 扫描系统问题
        print("📊 扫描系统硬编码问题...")
        scan_result = monitor.scan_directory('src', recursive=True)
        
        if not scan_result['success']:
            print(f"❌ 扫描失败: {scan_result.get('error', '未知错误')}")
            return False
        
        print(f"✅ 扫描完成!")
        print(f"   📁 扫描文件数: {scan_result['scanned_files']}")
        print(f"   ⚠️  发现问题: {scan_result['violations_found']}")
        print(f"   ⏱️  扫描耗时: {scan_result['scan_time']:.2f}秒")
        print()
        
        # 4. 按照优先级优化文件
        print("🎯 按优先级优化文件...")
        
        # 获取问题最多的文件
        problem_files = []
        for violation in monitor.violations:
            if violation.file_path not in problem_files:
                problem_files.append(violation.file_path)
        
        # 按问题数量排序
        file_problem_counts = {}
        for violation in monitor.violations:
            file_path = violation.file_path
            if file_path not in file_problem_counts:
                file_problem_counts[file_path] = 0
            file_problem_counts[file_path] += 1
        
        sorted_files = sorted(file_problem_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"📋 发现 {len(sorted_files)} 个有问题的文件")
        print("🔍 问题最多的文件 (前10个):")
        for i, (file_path, count) in enumerate(sorted_files[:10]):
            print(f"  {i+1:2d}. {file_path}: {count}个问题")
        print()
        
        # 5. 优化前5个问题最多的文件
        print("🔧 优化前5个问题最多的文件...")
        top_files = [file_path for file_path, _ in sorted_files[:5]]
        
        optimization_results = []
        for i, file_path in enumerate(top_files):
            print(f"  {i+1}. 优化 {file_path}...")
            
            try:
                result = optimizer.optimize_file(file_path, backup=True)
                optimization_results.append(result)
                
                if result['success']:
                    print(f"     ✅ 成功: {result['optimizations_applied']}个优化")
                    print(f"     📊 语法修复: {result.get('syntax_fixes', 0)}个")
                    print(f"     🔧 硬编码修复: {result.get('hardcode_fixes', 0)}个")
                    print(f"     🏗️  架构优化: {result.get('architectural_fixes', 0)}个")
                    print(f"     🧠 智能配置: {result.get('smart_config_fixes', 0)}个")
                    print(f"     ⏱️  耗时: {result.get('optimization_time', 0):.2f}秒")
                else:
                    print(f"     ❌ 失败: {result.get('error', '未知错误')}")
                
            except Exception as e:
                print(f"     ❌ 异常: {e}")
                optimization_results.append({'success': False, 'error': str(e)})
            
            print()
        
        # 6. 显示优化统计
        print("📈 优化统计:")
        stats = optimizer.get_optimization_stats()
        print(f"  📁 处理文件数: {stats['total_files_processed']}")
        print(f"  🔧 总优化数: {stats['total_optimizations_applied']}")
        print(f"  ✅ 成功优化: {stats['successful_optimizations']}")
        print(f"  ❌ 失败优化: {stats['failed_optimizations']}")
        print(f"  ⏱️  总耗时: {stats['optimization_time']:.2f}秒")
        print()
        
        # 7. 重新扫描验证优化效果
        print("🔍 重新扫描验证优化效果...")
        verify_result = monitor.scan_directory('src', recursive=True)
        
        if verify_result['success']:
            original_count = scan_result['violations_found']
            new_count = verify_result['violations_found']
            reduction = original_count - new_count
            reduction_percentage = (reduction / original_count * 100) if original_count > 0 else 0
            
            print(f"✅ 验证完成!")
            print(f"  📊 原始问题数: {original_count}")
            print(f"  📊 当前问题数: {new_count}")
            print(f"  📉 减少问题数: {reduction}")
            print(f"  📈 优化效果: {reduction_percentage:.1f}%")
            print()
            
            if reduction > 0:
                print("🎉 系统优化成功!")
            else:
                print("ℹ️  未发现明显改善，可能需要更深入的优化")
        else:
            print(f"❌ 验证扫描失败: {verify_result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        logger.error(f"系统优化失败: {e}")
        print(f"❌ 系统优化失败: {e}")
        return False

def optimize_specific_files():
    """优化特定文件"""
    print("🎯 优化特定文件...")
    
    # 根据分析报告，优化问题最严重的文件
    priority_files = [
        'src/agents/enhanced_reasoning_agent.py',
        'src/agents/intelligent_strategy_agent.py',
        'src/agents/enhanced_knowledge_retrieval_agent.py',
        'src/agents/enhanced_answer_generation_agent.py',
        'src/config/defaults.py'
    ]
    
    try:
        from src.utils.integrated_code_optimizer import get_integrated_optimizer
        optimizer = get_integrated_optimizer()
        
        for file_path in priority_files:
            if os.path.exists(file_path):
                print(f"🔧 优化 {file_path}...")
                result = optimizer.optimize_file(file_path, backup=True)
                
                if result['success']:
                    print(f"  ✅ 成功: {result['optimizations_applied']}个优化")
                else:
                    print(f"  ❌ 失败: {result.get('error', '未知错误')}")
            else:
                print(f"  ⚠️  文件不存在: {file_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"特定文件优化失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 系统优化脚本")
    print("=" * 80)
    print("按照硬编码分析报告的建议优化系统")
    print("确保智能代码优化器在每次修复时都起作用")
    print()
    
    # 执行系统优化
    success = optimize_system()
    
    if success:
        print("✅ 系统优化完成!")
        
        # 可选：优化特定文件
        print("\n" + "=" * 80)
        print("🎯 额外优化特定文件...")
        optimize_specific_files()
        
    else:
        print("❌ 系统优化失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
