#!/usr/bin/env python3
"""
简单的 LangGraph 使用示例
演示如何在 UnifiedResearchSystem 中使用 LangGraph
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 🚀 首先加载 .env 文件（确保 API key 被正确加载）
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
    else:
        print(f"⚠️  .env 文件不存在: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

# 启用 LangGraph（可选）
os.environ['USE_LANGGRAPH'] = 'true'

from src.unified_research_system import create_unified_research_system, ResearchRequest


async def main():
    """主函数"""
    print("=" * 80)
    print("LangGraph 简单使用示例")
    print("=" * 80)
    print()
    
    try:
        # 创建系统实例
        print("1. 创建 UnifiedResearchSystem 实例...")
        system = await create_unified_research_system()
        print("   ✅ 系统创建成功")
        print()
        
        # 检查是否启用了 LangGraph
        if hasattr(system, '_use_langgraph') and system._use_langgraph:
            print("   ✅ LangGraph 已启用")
        else:
            print("   ⚠️  LangGraph 未启用（使用传统流程）")
            print("   提示：设置环境变量 USE_LANGGRAPH=true 启用 LangGraph")
        print()
        
        # 创建研究请求
        print("2. 创建研究请求...")
        request = ResearchRequest(
            query="What is the capital of France?",
            context={}
        )
        print(f"   查询: {request.query}")
        print()
        
        # 执行研究
        print("3. 执行研究...")
        result = await system.execute_research(request)
        print()
        
        # 显示结果
        print("4. 结果:")
        print(f"   成功: {result.success}")
        if result.success:
            print(f"   答案: {result.answer}")
            print(f"   置信度: {result.confidence:.2f}")
            print(f"   执行时间: {result.execution_time:.2f}秒")
            if result.knowledge:
                print(f"   知识来源: {len(result.knowledge)} 条")
            if result.citations:
                print(f"   引用: {len(result.citations)} 条")
        else:
            print(f"   错误: {result.error}")
        print()
        
        print("=" * 80)
        print("示例完成")
        print("=" * 80)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保已安装 LangGraph: pip install langgraph")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

