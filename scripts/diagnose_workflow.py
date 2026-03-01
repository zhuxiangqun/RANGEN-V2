#!/usr/bin/env python3
"""
诊断 LangGraph 工作流初始化问题
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print("=" * 60)
print("LangGraph 工作流诊断工具")
print("=" * 60)
print()

# 1. 检查环境变量
print("1. 检查环境变量...")
enable_workflow = os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true')
use_langgraph = os.getenv('USE_LANGGRAPH', 'false')
print(f"   ENABLE_UNIFIED_WORKFLOW: {enable_workflow}")
print(f"   USE_LANGGRAPH: {use_langgraph}")
print()

# 2. 检查 LangGraph 安装
print("2. 检查 LangGraph 安装...")
try:
    import langgraph
    # 尝试获取版本号（不同版本可能有不同的属性）
    version = "unknown"
    if hasattr(langgraph, '__version__'):
        version = langgraph.__version__
    elif hasattr(langgraph, 'version'):
        version = langgraph.version
    else:
        # 尝试从 importlib.metadata 获取（Python 3.8+，推荐方法）
        try:
            from importlib.metadata import version as get_package_version
            version = get_package_version('langgraph')
        except ImportError:
            # Python < 3.8 回退到 importlib_metadata
            try:
                from importlib_metadata import version as get_package_version
                version = get_package_version('langgraph')
            except ImportError:
                # 最后回退到 pkg_resources（已弃用，但作为最后手段）
                try:
                    import pkg_resources
                    version = pkg_resources.get_distribution('langgraph').version
                except Exception:
                    version = "installed (version unknown)"
    
    print(f"   ✅ LangGraph 已安装: {version}")
except ImportError:
    print("   ❌ LangGraph 未安装")
    print("   💡 安装命令: pip install langgraph")
    sys.exit(1)
print()

# 3. 检查工作流模块
print("3. 检查工作流模块...")
try:
    from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow, LANGGRAPH_AVAILABLE
    if LANGGRAPH_AVAILABLE:
        print("   ✅ 工作流模块可用")
    else:
        print("   ❌ 工作流模块不可用（LANGGRAPH_AVAILABLE=False）")
        sys.exit(1)
except ImportError as e:
    print(f"   ❌ 无法导入工作流模块: {e}")
    sys.exit(1)
print()

# 4. 尝试初始化工作流
print("4. 尝试初始化工作流...")
try:
    workflow = UnifiedResearchWorkflow(system=None)
    print("   ✅ 工作流初始化成功")
    print(f"   ✅ 工作流对象: {workflow}")
    print(f"   ✅ 工作流图: {workflow.workflow is not None}")
except Exception as e:
    print(f"   ❌ 工作流初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 5. 检查系统初始化
print("5. 检查系统初始化...")
try:
    from src.unified_research_system import UnifiedResearchSystem
    print("   ✅ UnifiedResearchSystem 模块可用")
    
    # 检查是否有初始化方法
    if hasattr(UnifiedResearchSystem, '_initialize_unified_workflow'):
        print("   ✅ _initialize_unified_workflow 方法存在")
    else:
        print("   ❌ _initialize_unified_workflow 方法不存在")
        
except Exception as e:
    print(f"   ❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 60)
print("✅ 诊断完成！")
print("=" * 60)
print()
print("如果所有检查都通过，工作流应该能够正常初始化。")
print("如果仍有问题，请查看系统初始化日志。")

