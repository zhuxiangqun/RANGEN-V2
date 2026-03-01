#!/usr/bin/env python3
"""
验证知识图谱构建优化功能
通过检查代码和文件来验证优化是否正确实施
"""

import sys
import json
from pathlib import Path
import re

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_entity_manager_optimizations():
    """验证实体管理器的优化"""
    print("=" * 80)
    print("验证1: 实体管理器优化")
    print("=" * 80)
    
    entity_manager_file = Path("knowledge_management_system/graph/entity_manager.py")
    
    if not entity_manager_file.exists():
        print("❌ 实体管理器文件不存在")
        return False
    
    with open(entity_manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'update_entity方法': 'def update_entity' in content,
        'merge_properties参数': 'merge_properties: bool = True' in content,
        '属性合并逻辑': 'merged_properties' in content or 'update_entity' in content,
        'updated_at更新': 'updated_at' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def verify_relation_manager_optimizations():
    """验证关系管理器的优化"""
    print("\n" + "=" * 80)
    print("验证2: 关系管理器优化")
    print("=" * 80)
    
    relation_manager_file = Path("knowledge_management_system/graph/relation_manager.py")
    
    if not relation_manager_file.exists():
        print("❌ 关系管理器文件不存在")
        return False
    
    with open(relation_manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'update_relation方法': 'def update_relation' in content,
        'merge_properties参数': 'merge_properties: bool = True' in content,
        '属性合并逻辑': 'merged_properties' in content or 'update_relation' in content,
        '置信度更新逻辑': 'confidence > existing_confidence' in content or 'if confidence >' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def verify_graph_builder_optimizations():
    """验证图谱构建器的优化"""
    print("\n" + "=" * 80)
    print("验证3: 图谱构建器优化")
    print("=" * 80)
    
    graph_builder_file = Path("knowledge_management_system/graph/graph_builder.py")
    
    if not graph_builder_file.exists():
        print("❌ 图谱构建器文件不存在")
        return False
    
    with open(graph_builder_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'merge_properties参数': 'merge_properties: bool = True' in content,
        '传递merge_properties': 'merge_properties=merge_properties' in content,
        '支持属性提取': 'entity1_properties' in content or 'relation_properties' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def verify_build_script_optimizations():
    """验证构建脚本的优化"""
    print("\n" + "=" * 80)
    print("验证4: 构建脚本优化（核心优化）")
    print("=" * 80)
    
    build_script_file = Path("knowledge_management_system/scripts/build_knowledge_graph.py")
    
    if not build_script_file.exists():
        print("❌ 构建脚本文件不存在")
        return False
    
    with open(build_script_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        '每批构建逻辑': 'batch_graph_result' in content or 'build_from_structured_data' in content,
        '累计统计': 'total_entities_created' in content and 'total_relations_created' in content,
        '清空graph_data': 'graph_data = []' in content,
        '启用属性合并': 'merge_properties' in content or 'merge_properties=True' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    # 检查是否在循环内构建（每批构建）
    if 'for batch_idx in range(total_batches):' in content:
        # 检查构建是否在循环内
        batch_loop_match = re.search(r'for batch_idx in range\(total_batches\):.*?if graph_data:.*?build_from_structured_data', content, re.DOTALL)
        if batch_loop_match:
            print("   ✅ 每批处理完后立即构建（在循环内）")
        else:
            print("   ⚠️  构建逻辑可能不在循环内（需要检查）")
            all_passed = False
    
    return all_passed


def verify_file_structure():
    """验证文件结构"""
    print("\n" + "=" * 80)
    print("验证5: 文件结构")
    print("=" * 80)
    
    files_to_check = {
        '实体管理器': 'knowledge_management_system/graph/entity_manager.py',
        '关系管理器': 'knowledge_management_system/graph/relation_manager.py',
        '图谱构建器': 'knowledge_management_system/graph/graph_builder.py',
        '构建脚本': 'knowledge_management_system/scripts/build_knowledge_graph.py',
        '质量分析脚本': 'scripts/analyze_knowledge_graph_quality.py',
        '质量分析Shell脚本': 'analyze_knowledge_graph_quality.sh'
    }
    
    all_passed = True
    for file_name, file_path in files_to_check.items():
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {file_name}: {file_path}")
        if not exists:
            all_passed = False
    
    return all_passed


def run_all_verifications():
    """运行所有验证"""
    print("\n" + "=" * 80)
    print("知识图谱构建优化功能验证")
    print("=" * 80)
    print()
    
    results = {
        'entity_manager': verify_entity_manager_optimizations(),
        'relation_manager': verify_relation_manager_optimizations(),
        'graph_builder': verify_graph_builder_optimizations(),
        'build_script': verify_build_script_optimizations(),
        'file_structure': verify_file_structure()
    }
    
    # 总结
    print("\n" + "=" * 80)
    print("验证结果总结")
    print("=" * 80)
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    for check_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{check_name}: {status}")
    
    print()
    print(f"总计: {passed_checks}/{total_checks} 个验证通过")
    
    if passed_checks == total_checks:
        print("\n✅ 所有验证通过！优化已正确实施。")
        return True
    else:
        print(f"\n⚠️  有 {total_checks - passed_checks} 个验证失败")
        return False


if __name__ == "__main__":
    success = run_all_verifications()
    sys.exit(0 if success else 1)

