#!/usr/bin/env python3
"""
测试修复后的RAGExpert
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# 修复1: 增加递归深度限制
print("🔧 修复1: 增加递归深度限制")
sys.setrecursionlimit(2000)
print(f"   递归深度限制设置为: {sys.getrecursionlimit()}")

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 确保移除轻量级模式
if 'USE_LIGHTWEIGHT_RAG' in os.environ:
    del os.environ['USE_LIGHTWEIGHT_RAG']
os.environ['USE_NEW_AGENTS'] = 'true'

async def test_fixed_rag():
    """测试修复后的RAG"""
    print("\n🚀 测试修复后的RAGExpert")
    print("=" * 50)

    try:
        # 导入组件
        from src.agents.rag_agent import RAGExpert

        # 创建实例
        print("🔧 创建RAGExpert实例...")
        rag_expert = RAGExpert()

        # 检查模式
        lightweight = getattr(rag_expert, '_lightweight_mode', False)
        print(f"   轻量级模式: {lightweight}")

        if lightweight:
            print("❌ 仍在使用轻量级模式")
            return False

        # 测试简单查询
        test_query = "什么是RAG？"
        print(f"\n🧪 测试查询: {test_query}")
        print("   超时设置: 45秒（比原来短，但应该足够）")

        context = {
            "query": test_query,
            "max_iterations": 2,  # 限制推理步数
            "timeout": 30.0  # 内部超时
        }

        start_time = time.time()

        try:
            # 使用asyncio.wait_for添加超时
            result = await asyncio.wait_for(
                rag_expert.execute(context),
                timeout=45.0  # 45秒超时
            )

            execution_time = time.time() - start_time

            print(".2f"            print(f"   成功: {result.success}")

            if result.success:
                data = result.data
                if isinstance(data, dict):
                    sources = data.get('sources', [])
                    answer = data.get('answer', '')
                    print(f"   证据数量: {len(sources)}")
                    print(f"   答案长度: {len(answer)}")

                    if len(sources) > 0:
                        print("✅ 成功检索到证据")
                    else:
                        print("⚠️ 未检索到证据")

                    if len(answer) > 20:
                        print("✅ 有实质性答案")
                        print(f"   答案预览: {answer[:100]}...")
                        return True
                    else:
                        print("❌ 答案太短")
                        return False
                else:
                    print(f"   数据格式错误: {type(data)}")
                    return False
            else:
                print(f"❌ 执行失败: {result.error}")
                return False

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            print(".2f"            print("❌ 执行超时")
            return False

        except Exception as e:
            execution_time = time.time() - start_time
            print(".2f"            print(f"❌ 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_fixed_rag())
    print(f"\n结果: {'✅ 修复成功' if success else '❌ 仍需修复'}")
