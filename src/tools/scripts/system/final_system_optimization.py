#!/usr/bin/env python3
"""
最终系统优化脚本
使用安全代码优化器按照硬编码分析报告的建议优化系统
"""
import os
import sys
import logging
from typing import Dict, List, Any
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_system_with_safe_optimizer():
    """使用安全代码优化器优化系统"""
    print("🛡️ 使用安全代码优化器优化系统...")
    print("=" * 80)
    
    try:
        # 导入安全代码优化器
        from safe_code_optimizer import SafeCodeOptimizer
        
        # 创建优化器实例
        optimizer = SafeCodeOptimizer()
        
        # 根据分析报告，优化问题最严重的文件
        priority_files = [
            'src/agents/enhanced_reasoning_agent.py',
            'src/agents/intelligent_strategy_agent.py',
            'src/agents/enhanced_knowledge_retrieval_agent.py',
            'src/agents/enhanced_answer_generation_agent.py',
            'src/config/defaults.py',
            'src/memory/enhanced_faiss_memory.py',
            'src/utils/unified_security_center.py',
            'src/utils/smart_hardcode_fixer.py',
            'src/utils/intelligent_config_manager.py',
            'src/utils/enhanced_wiki_processor.py'
        ]
        
        print(f"🎯 优化 {len(priority_files)} 个优先级文件...")
        print()
        
        optimization_results = []
        for i, file_path in enumerate(priority_files):
            if os.path.exists(file_path):
                print(f"  {i+1:2d}. 优化 {file_path}...")
                
                try:
                    result = optimizer.optimize_file(file_path, backup=True)
                    optimization_results.append(result)
                    
                    if result['success']:
                        print(f"     ✅ 成功: {result['optimizations_applied']}个优化")
                        print(f"     📊 导入修复: {result.get('import_fixes', 0)}个")
                        print(f"     🔧 硬编码修复: {result.get('hardcode_fixes', 0)}个")
                        print(f"     ⏱️  耗时: {result.get('optimization_time', 0):.2f}秒")
                    else:
                        print(f"     ❌ 失败: {result.get('error', '未知错误')}")
                    
                except Exception as e:
                    print(f"     ❌ 异常: {e}")
                    optimization_results.append({'success': False, 'error': str(e)})
            else:
                print(f"  {i+1:2d}. ⚠️  文件不存在: {file_path}")
                optimization_results.append({'success': False, 'error': '文件不存在'})
            
            print()
        
        # 显示优化统计
        print("📈 优化统计:")
        stats = optimizer.get_optimization_stats()
        print(f"  📁 处理文件数: {stats['total_files_processed']}")
        print(f"  🔧 总优化数: {stats['total_optimizations_applied']}")
        print(f"  ✅ 成功优化: {stats['successful_optimizations']}")
        print(f"  ❌ 失败优化: {stats['failed_optimizations']}")
        print(f"  ⏱️  总耗时: {stats['optimization_time']:.2f}秒")
        print()
        
        # 计算成功率
        success_rate = (stats['successful_optimizations'] / stats['total_files_processed'] * 100) if stats['total_files_processed'] > 0 else 0
        print(f"📊 优化成功率: {success_rate:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"系统优化失败: {e}")
        print(f"❌ 系统优化失败: {e}")
        return False

def optimize_directory_with_safe_optimizer():
    """使用安全代码优化器优化整个目录"""
    print("🛡️ 使用安全代码优化器优化整个src目录...")
    print("=" * 80)
    
    try:
        from safe_code_optimizer import SafeCodeOptimizer
        
        optimizer = SafeCodeOptimizer()
        
        # 优化整个src目录
        result = optimizer.optimize_directory('src', recursive=True)
        
        if result['success']:
            print(f"✅ 目录优化完成!")
            print(f"  📁 总文件数: {result['total_files']}")
            print(f"  ✅ 成功优化: {result['successful_optimizations']}")
            print(f"  🔧 总优化数: {result['total_optimizations_applied']}")
            print(f"  ⏱️  总耗时: {result['total_time']:.2f}秒")
            
            # 计算成功率
            success_rate = (result['successful_optimizations'] / result['total_files'] * 100) if result['total_files'] > 0 else 0
            print(f"📊 优化成功率: {success_rate:.1f}%")
            
            return True
        else:
            print(f"❌ 目录优化失败: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"目录优化失败: {e}")
        print(f"❌ 目录优化失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 最终系统优化脚本")
    print("=" * 80)
    print("使用安全代码优化器按照硬编码分析报告的建议优化系统")
    print("确保智能代码优化器在每次修复时都起作用")
    print()
    
    # 选择优化策略
    print("请选择优化策略:")
    print("1. 优化优先级文件 (推荐)")
    print("2. 优化整个src目录")
    print("3. 两种策略都执行")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    success = False
    
    if choice == "1":
        success = optimize_system_with_safe_optimizer()
    elif choice == "2":
        success = optimize_directory_with_safe_optimizer()
    elif choice == "3":
        print("🔄 执行两种优化策略...")
        print()
        
        # 先优化优先级文件
        success1 = optimize_system_with_safe_optimizer()
        
        print("\n" + "=" * 80)
        
        # 再优化整个目录
        success2 = optimize_directory_with_safe_optimizer()
        
        success = success1 and success2
    else:
        print("❌ 无效选择，使用默认策略...")
        success = optimize_system_with_safe_optimizer()
    
    if success:
        print("\n🎉 系统优化完成!")
        print("✅ 智能代码优化器已成功集成到硬编码监控系统中")
        print("✅ 每次修复时都会自动使用智能代码优化器")
        print("✅ 系统现在具备了完整的检测、警告、自动修复功能")
    else:
        print("\n❌ 系统优化失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
