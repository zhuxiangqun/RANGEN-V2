#!/usr/bin/env python3
"""
ML/RL系统健康检查

全面检查ML/RL集成系统的健康状态，包括配置、数据收集、工具等。
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_configuration():
    """检查配置"""
    print("=" * 80)
    print("1. 配置检查")
    print("=" * 80)
    
    issues = []
    
    # 检查配置文件
    config_file = project_root / "config" / "ml_training_config.json"
    if config_file.exists():
        print(f"✅ 配置文件存在: {config_file}")
        
        # 验证JSON格式
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                ml_config = config.get('ml_training', {})
                
                if ml_config.get('data_collection_enabled', False):
                    print(f"   ✅ 数据收集已启用")
                else:
                    print(f"   ⚠️ 数据收集未启用")
                    issues.append("数据收集未启用")
                
                if ml_config.get('parallel_classifier_enabled', False):
                    print(f"   ✅ 并行分类器已启用")
                else:
                    print(f"   ⚠️ 并行分类器未启用")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON格式错误: {e}")
            issues.append(f"配置文件JSON格式错误: {e}")
    else:
        print(f"❌ 配置文件不存在: {config_file}")
        issues.append("配置文件不存在")
    
    return issues


def check_data_directory():
    """检查数据目录"""
    print(f"\n{'=' * 80}")
    print("2. 数据目录检查")
    print("=" * 80)
    
    issues = []
    
    data_dir = project_root / "data" / "ml_training"
    if data_dir.exists():
        print(f"✅ 数据目录存在: {data_dir}")
        
        # 检查权限
        if os.access(data_dir, os.W_OK):
            print(f"   ✅ 目录可写")
        else:
            print(f"   ❌ 目录不可写")
            issues.append("数据目录不可写")
        
        # 检查现有数据
        jsonl_files = list(data_dir.glob("*.jsonl"))
        if jsonl_files:
            total_lines = 0
            for file in jsonl_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        total_lines += sum(1 for _ in f)
                except Exception as e:
                    print(f"   ⚠️ 读取文件失败 {file.name}: {e}")
            
            print(f"   📊 现有数据: {len(jsonl_files)} 个文件, {total_lines} 条记录")
        else:
            print(f"   ℹ️ 暂无数据文件（这是正常的，如果刚开始收集）")
    else:
        print(f"⚠️ 数据目录不存在: {data_dir}")
        print(f"   （将在首次运行时自动创建）")
    
    return issues


def check_code_modules():
    """检查代码模块"""
    print(f"\n{'=' * 80}")
    print("3. 代码模块检查")
    print("=" * 80)
    
    issues = []
    modules = [
        "src.core.reasoning.ml_framework.base_ml_component",
        "src.core.reasoning.ml_framework.data_collection",
        "src.core.reasoning.ml_framework.parallel_query_classifier",
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            issues.append(f"模块导入失败: {module_name}")
    
    return issues


def check_tools():
    """检查工具脚本"""
    print(f"\n{'=' * 80}")
    print("4. 工具脚本检查")
    print("=" * 80)
    
    issues = []
    tools = [
        "scripts/enable_ml_data_collection.py",
        "scripts/verify_ml_config.py",
        "scripts/collect_ml_training_data.py",
        "scripts/monitor_data_collection.py",
        "scripts/test_data_collection.py",
    ]
    
    for tool_path in tools:
        tool_file = project_root / tool_path
        if tool_file.exists():
            if os.access(tool_file, os.X_OK):
                print(f"✅ {tool_path}")
            else:
                print(f"⚠️ {tool_path} (不可执行)")
        else:
            print(f"❌ {tool_path} (不存在)")
            issues.append(f"工具脚本不存在: {tool_path}")
    
    return issues


def check_documentation():
    """检查文档"""
    print(f"\n{'=' * 80}")
    print("5. 文档检查")
    print("=" * 80)
    
    issues = []
    docs = [
        "docs/improvements/README_ML_RL.md",
        "docs/improvements/ml_data_collection_quickstart.md",
        "docs/improvements/ml_data_collection_guide.md",
        "docs/improvements/ml_data_collection_workflow.md",
        "docs/improvements/ml_rl_integration_roadmap.md",
        "docs/improvements/ml_rl_integration_status.md",
        "docs/improvements/ml_rl_ready_for_production.md",
        "docs/improvements/ml_rl_implementation_complete.md",
    ]
    
    for doc_path in docs:
        doc_file = project_root / doc_path
        if doc_file.exists():
            print(f"✅ {doc_path}")
        else:
            print(f"❌ {doc_path} (不存在)")
            issues.append(f"文档不存在: {doc_path}")
    
    return issues


def check_system_integration():
    """检查系统集成"""
    print(f"\n{'=' * 80}")
    print("6. 系统集成检查")
    print("=" * 80)
    
    issues = []
    
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        engine = RealReasoningEngine()
        
        if hasattr(engine, 'data_collection_enabled'):
            if engine.data_collection_enabled:
                print(f"✅ RealReasoningEngine 数据收集已启用")
                if engine.data_collection:
                    print(f"   ✅ 数据收集管道已初始化")
                else:
                    print(f"   ⚠️ 数据收集管道未初始化")
                    issues.append("数据收集管道未初始化")
            else:
                print(f"⚠️ RealReasoningEngine 数据收集未启用")
                issues.append("RealReasoningEngine数据收集未启用")
        else:
            print(f"⚠️ RealReasoningEngine 未找到data_collection_enabled属性")
            issues.append("RealReasoningEngine缺少数据收集属性")
        
        if hasattr(engine, 'step_generator'):
            step_gen = engine.step_generator
            if hasattr(step_gen, 'parallel_classifier_enabled'):
                if step_gen.parallel_classifier_enabled:
                    print(f"✅ StepGenerator 并行分类器已启用")
                else:
                    print(f"⚠️ StepGenerator 并行分类器未启用")
            else:
                print(f"⚠️ StepGenerator 未找到并行分类器属性")
        
    except Exception as e:
        print(f"❌ 系统集成检查失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()[:200]}")
        issues.append(f"系统集成检查失败: {e}")
    
    return issues


def main():
    """主函数"""
    print("=" * 80)
    print("ML/RL系统健康检查")
    print("=" * 80)
    
    all_issues = []
    
    # 执行各项检查
    all_issues.extend(check_configuration())
    all_issues.extend(check_data_directory())
    all_issues.extend(check_code_modules())
    all_issues.extend(check_tools())
    all_issues.extend(check_documentation())
    all_issues.extend(check_system_integration())
    
    # 总结
    print(f"\n{'=' * 80}")
    print("检查总结")
    print("=" * 80)
    
    if not all_issues:
        print("\n✅ 所有检查通过！系统健康状态良好。")
        print("\n下一步:")
        print("1. 运行数据收集: python scripts/collect_ml_training_data.py")
        print("2. 监控数据收集: python scripts/monitor_data_collection.py")
    else:
        print(f"\n⚠️ 发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n建议:")
        print("1. 运行配置启用脚本: python scripts/enable_ml_data_collection.py")
        print("2. 验证配置: python scripts/verify_ml_config.py")
    
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()

