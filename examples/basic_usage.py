import asyncio
import sys
"""
基本Use示例
演示如何Use深度研究智能体系统
"""
# 添加项目根目录到Python路径
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.research_system_improved_v6 import ImprovedResearchSystemV6 as DeepResearchSystem

async def main():
    """主函数"""
    print("🚀 启动深度研究智能体系统...")
    # 初始化系统
    system = DeepResearchSystem()
    await system.initialize()
    # 示例查询
    query = "2025年美国所有从事AI智能体研发的公司列表，要求至少100家，包含名称、网站、产品、描述、智能体类型和行业领域。"
    print(f"\n📝 执行研究查询: {query}")
    print("=" * 80)
    # 执行研究任务
    result = await system.research(query)
    # 显示结果
    if result.success:
        print("✅ 研究任务完成!")
        print(f"⏱️  执行时间: {result.execution_time:.2f}秒")
        print(f"📊 元数据: {result.metadata}")
        print("\n📄 研究报告:")
        print("-" * 40)
        print(result.report)
        print(f"\n📚 引用 ({len(result.citations)} 个):")
        print("-" * 40)
        for i, citation in enumerate(result.citations, 1):
            print(f"{i}. {citation.get('citation_text', 'N/A')}")
    else:
        print("❌ 研究任务失败!")
        print(f"错误信息: {result.error_message}")
    # 获取系统状态
    print("\n🔍 系统状态:")
    print("-" * 40)
    status = await system.get_system_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    # 清理资源
    await system.cleanup()
    print("\n🧹 系统资源已清理")

if __name__ == "__main__":
    asyncio.run(main())