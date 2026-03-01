#!/usr/bin/env python3
"""
测试统一工作流（MVP版本）
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

# 启用统一工作流
os.environ['ENABLE_UNIFIED_WORKFLOW'] = 'true'
# 启用可视化
os.environ['ENABLE_BROWSER_VISUALIZATION'] = 'true'

from src.unified_research_system import create_unified_research_system, ResearchRequest


async def test_simple_query():
    """测试简单查询"""
    print("=" * 80)
    print("测试1: 简单查询")
    print("=" * 80)
    
    system = await create_unified_research_system()
    
    request = ResearchRequest(
        query="What is the capital of France?",
        context={}
    )
    
    result = await system.execute_research(request)
    
    print(f"成功: {result.success}")
    print(f"答案: {result.answer}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"执行时间: {result.execution_time:.2f}秒")
    print()


async def test_complex_query():
    """测试复杂查询"""
    print("=" * 80)
    print("测试2: 复杂查询")
    print("=" * 80)
    
    system = await create_unified_research_system()
    
    request = ResearchRequest(
        query="If my future wife has the same first name as the 15th first lady of the United States, what would her first name be?",
        context={}
    )
    
    result = await system.execute_research(request)
    
    print(f"成功: {result.success}")
    print(f"答案: {result.answer}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"执行时间: {result.execution_time:.2f}秒")
    print()


async def test_workflow_directly():
    """直接测试工作流"""
    print("=" * 80)
    print("测试3: 直接测试工作流")
    print("=" * 80)
    
    from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
    
    workflow = UnifiedResearchWorkflow(system=None)
    
    # 测试简单查询
    result = await workflow.execute("What is the capital of France?")
    print(f"简单查询结果:")
    print(f"  成功: {result['success']}")
    print(f"  答案: {result['answer']}")
    print(f"  路径: {result['route_path']}")
    print()
    
    # 测试复杂查询
    result = await workflow.execute("Compare the differences between Python and Java programming languages.")
    print(f"复杂查询结果:")
    print(f"  成功: {result['success']}")
    print(f"  答案: {result['answer']}")
    print(f"  路径: {result['route_path']}")
    print()


async def main():
    """主函数"""
    print("=" * 80)
    print("统一工作流（MVP）测试")
    print("=" * 80)
    print()
    
    try:
        # 测试1: 简单查询
        await test_simple_query()
        
        # 测试2: 复杂查询
        await test_complex_query()
        
        # 测试3: 直接测试工作流
        await test_workflow_directly()
        
        print("=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)
        print()
        print("💡 提示:")
        print("- 如果启用了可视化，可以在浏览器中访问 http://localhost:8080 查看工作流执行")
        print("- 工作流图会自动显示在可视化界面中")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

