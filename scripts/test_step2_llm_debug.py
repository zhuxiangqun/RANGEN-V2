#!/usr/bin/env python3
"""
测试步骤2的LLM提示词和响应
运行一个查询以生成调试文件
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试加载.env文件（如果存在且可访问）
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=project_root / '.env')
except Exception:
    pass  # 如果无法加载.env，继续执行


async def test_step2_llm():
    """运行一个查询以触发步骤2的LLM调用"""
    print("=" * 80)
    print("测试步骤2的LLM提示词和响应")
    print("=" * 80)
    
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        
        # 初始化推理引擎
        print("\n🔧 初始化推理引擎...")
        engine = RealReasoningEngine()
        print("✅ 推理引擎已初始化")
        
        # 运行包含步骤2的查询（关于15th first lady的母亲）
        query = "If my future wife has the same first name as the 15th first lady, and her mother has the same maiden name as the mother of the second assassinated president, what would be my future wife's full name?"
        
        print(f"\n📝 查询: {query}")
        print("\n🚀 开始执行推理...")
        
        context = {
            "query": query,
            "evidence": [],
            "knowledge": []
        }
        
        result = await engine.reason(query, context)
        
        print("\n" + "=" * 80)
        print("推理结果:")
        print("=" * 80)
        print(f"成功: {result.success}")
        print(f"最终答案: {result.final_answer}")
        print(f"步骤数: {len(result.reasoning_steps)}")
        
        # 显示步骤2的信息
        if len(result.reasoning_steps) >= 2:
            step2 = result.reasoning_steps[1]
            print(f"\n步骤2信息:")
            print(f"  子查询: {step2.get('sub_query', 'N/A')}")
            print(f"  答案: {step2.get('answer', 'N/A')}")
            print(f"  证据数量: {len(step2.get('evidence', []))}")
        
        # 检查调试文件是否生成
        print("\n" + "=" * 80)
        print("检查调试文件:")
        print("=" * 80)
        
        debug_dir = project_root / "debug_logs"
        prompt_file = debug_dir / "step2_llm_prompt.txt"
        response_file = debug_dir / "step2_llm_response.txt"
        
        if prompt_file.exists():
            print(f"✅ 提示词文件已生成: {prompt_file}")
            print(f"   文件大小: {prompt_file.stat().st_size} 字节")
        else:
            print(f"⚠️ 提示词文件未生成: {prompt_file}")
        
        if response_file.exists():
            print(f"✅ 响应文件已生成: {response_file}")
            print(f"   文件大小: {response_file.stat().st_size} 字节")
        else:
            print(f"⚠️ 响应文件未生成: {response_file}")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_step2_llm())

