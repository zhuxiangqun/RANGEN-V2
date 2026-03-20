#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重复的质量分析系统脚本
删除analysis/scripts目录下与统一100维度系统重复的文件
"""

import os
import shutil
from datetime import datetime

def clean_duplicate_quality_systems():
    """清理重复的质量分析系统"""
    print("🧹 开始清理重复的质量分析系统...")
    print("=" * 80)
    
    # 创建备份目录
    backup_dir = f"backup_duplicate_systems_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 定义重复的质量分析系统文件
    duplicate_systems = [
        # 重复的质量分析系统
        "analysis/scripts/simple_quality_analysis.py",
        "analysis/scripts/advanced_quality_analysis.py", 
        "analysis/scripts/comprehensive_system_quality_analysis.py",
        "analysis/scripts/run_system_quality_analysis.py",
        "analysis/scripts/complete_intelligent_analysis.py",
        
        # 重复的性能分析系统
        "analysis/scripts/performance_analysis.py",
        "analysis/scripts/analyze_performance_issues.py",
        "analysis/scripts/deep_performance_analysis.py",
        "analysis/scripts/fix_performance_issues.py",
        "analysis/scripts/fix_performance_monitoring.py",
        "analysis/scripts/fix_performance_center.py",
        "analysis/scripts/create_simple_performance_center.py",
        "analysis/scripts/performance_optimization_enhancer.py",
        
        # 重复的智能分析系统
        "analysis/scripts/intelligent_improvement_plan.py",
        "analysis/scripts/advanced_intelligent_improvement.py",
        "analysis/scripts/phase3_intelligent_improvement.py",
        "analysis/scripts/intelligent_system_demo.py",
        "analysis/scripts/integrate_intelligent_features.py",
        
        # 重复的配置分析系统
        "analysis/scripts/config_architecture_analysis.py",
        "analysis/scripts/config_evolution_analysis.py",
        "analysis/scripts/intelligent_config_architecture.py",
        "analysis/scripts/intelligent_config_bridge.py",
        "analysis/scripts/intelligent_config_optimizer.py",
        "analysis/scripts/demonstrate_intelligent_config.py",
        
        # 重复的ML/RL分析系统
        "analysis/scripts/ml_rl_usage_analysis.py",
        "analysis/scripts/ml_rl_function_analysis.py",
        
        # 重复的报告生成系统
        "analysis/scripts/final_code_quality_report.py",
        "analysis/scripts/final_hardcode_analysis.py",
        "analysis/scripts/system_analysis_report.py",
        "analysis/scripts/system_modules_detailed_analysis.py",
        
        # 重复的代码质量检查系统
        "analysis/scripts/check_code_quality.py",
    ]
    
    print(f"📋 发现 {len(duplicate_systems)} 个重复的质量分析系统")
    print()
    
    # 统计信息
    deleted_count = 0
    backup_count = 0
    not_found_count = 0
    
    # 处理每个重复系统
    for system_path in duplicate_systems:
        if os.path.exists(system_path):
            try:
                # 备份文件
                filename = os.path.basename(system_path)
                backup_path = os.path.join(backup_dir, filename)
                shutil.copy2(system_path, backup_path)
                backup_count += 1
                
                # 删除文件
                os.remove(system_path)
                deleted_count += 1
                
                print(f"   ✅ 已删除: {system_path}")
                
            except Exception as e:
                print(f"   ❌ 删除失败: {system_path} - {e}")
        else:
            not_found_count += 1
            print(f"   ⚠️ 文件不存在: {system_path}")
    
    print()
    print("📊 清理统计:")
    print(f"   ✅ 成功删除: {deleted_count} 个文件")
    print(f"   📁 备份文件: {backup_count} 个文件")
    print(f"   ⚠️ 文件不存在: {not_found_count} 个文件")
    print(f"   📁 备份目录: {backup_dir}")
    
    # 检查剩余的analysis/scripts文件
    print()
    print("🔍 检查剩余的analysis/scripts文件...")
    remaining_files = []
    if os.path.exists("analysis/scripts"):
        for file in os.listdir("analysis/scripts"):
            if file.endswith('.py') and not file.startswith('__'):
                remaining_files.append(file)
    
    if remaining_files:
        print(f"   📋 剩余文件 ({len(remaining_files)} 个):")
        for file in remaining_files:
            print(f"     - {file}")
    else:
        print("   ✅ analysis/scripts目录已清空")
    
    print()
    print("✅ 重复质量分析系统清理完成！")
    print("=" * 80)
    print("📋 清理结果:")
    print("   ✅ 删除了重复的质量分析系统")
    print("   ✅ 保留了统一的100维度系统")
    print("   ✅ 备份了所有删除的文件")
    print("   🎯 现在只有一个统一的智能质量分析系统")

if __name__ == "__main__":
    clean_duplicate_quality_systems()
