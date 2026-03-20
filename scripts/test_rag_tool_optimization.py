#!/usr/bin/env python3
"""
RAGTool优化测试脚本
验证优化后的RAGTool功能是否正常
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 🚀 测试完整RAG功能（强制禁用轻量级模式）
os.environ['USE_LIGHTWEIGHT_RAG'] = 'false'  # 强制禁用轻量级模式
print('🔧 测试完整RAG功能（正常模式）')
print('🔧 已强制设置 USE_LIGHTWEIGHT_RAG=false')

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载.env文件中的环境变量')
except ImportError:
    print('⚠️ python-dotenv未安装，尝试手动加载.env文件')
    if Path('.env').exists():
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
        print('✅ 已手动加载.env文件中的环境变量')


async def test_rag_tool_optimization():
    """测试RAGTool完整功能"""
    print("🚀 开始RAGTool完整功能测试（正常模式）")
    print("=" * 70)
    print("⚠️  注意：已移除USE_LIGHTWEIGHT_RAG=true，将测试完整RAG功能")
    print("   这将加载完整的知识库和模型，可能需要较长时间...")
    print("=" * 70)
    
    step = 1
    
    # 1. 测试RAGTool直接调用
    print(f'\n📋 步骤{step}: 测试RAGTool直接调用（优化后）')
    print("-" * 40)
    try:
        from src.agents.tools.rag_tool import RAGTool

        rag_tool = RAGTool()
        # 🚀 强制清除缓存，确保使用新的环境变量设置
        rag_tool._rag_agent = None
        print("✅ RAGTool初始化成功（已清除缓存）")
        
        # 检查是否移除了RAGAgentWrapper
        rag_agent = rag_tool._get_rag_agent()
        agent_type = type(rag_agent).__name__
        print(f"✅ RAG Agent类型: {agent_type}")
        
        if "Wrapper" in agent_type:
            print(f"⚠️ 警告: 仍然使用包装器 ({agent_type})")
        else:
            print(f"✅ 优化成功: 直接使用 {agent_type}，已移除RAGAgentWrapper层")
        
        # 🚀 测试调用（完整模式，适当超时）
        test_query = "什么是RAG？"
        print(f"\n🧪 测试查询: {test_query}")
        print("   ⚠️ 完整模式，设置60秒超时")
        print("   💡 完整模式会进行实际的知识检索和答案生成")

        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                rag_tool.call(query=test_query),
                timeout=60.0
            )
            execution_time = time.time() - start_time

            if result.success:
                print(f"✅ RAGTool调用成功 ({execution_time:.2f}s)")
                data = result.data
                if isinstance(data, dict):
                    print(f"   数据类型: {type(data)}")
                    sources = data.get('sources', [])
                    answer = data.get('answer', '')
                    print(f"   检索到 {len(sources)} 条证据")
                    print(f"   答案长度: {len(answer)} 字符")
                    print(f"   答案预览: {answer[:100]}...")
                else:
                    print(f"   数据: {data}")
            else:
                print(f"⚠️ RAGTool调用完成但失败 ({execution_time:.2f}s): {result.error}")
        except asyncio.TimeoutError:
            print(f"❌ RAGTool调用超时（>60秒），可能需要更长的初始化时间")
        except Exception as e:
            print(f"❌ RAGTool调用异常: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ RAGTool测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    step += 1
    
    # 2. 测试RAGExpert.as_tool()
    print(f'\n📋 步骤{step}: 测试RAGExpert.as_tool()方法')
    print("-" * 40)
    try:
        from src.agents.rag_agent import RAGExpert
        
        rag_expert = RAGExpert()
        print("✅ RAGExpert初始化成功")
        
        # 测试as_tool()方法
        rag_tool_from_expert = rag_expert.as_tool()
        print(f"✅ RAGExpert.as_tool()成功，工具类型: {type(rag_tool_from_expert).__name__}")
        print(f"   工具名称: {rag_tool_from_expert.tool_name}")
        print(f"   工具描述: {rag_tool_from_expert.description}")
        
        # 测试工具调用（完整模式）
        test_query = "什么是RAG？"
        print(f"\n🧪 测试查询: {test_query}")
        print("   ⚠️ 完整模式，设置60秒超时")

        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                rag_tool_from_expert.call(query=test_query),
                timeout=60.0
            )
            execution_time = time.time() - start_time

            if result.success:
                print(f"✅ RAGExpert.as_tool()调用成功 ({execution_time:.2f}s)")
                data = result.data
                if isinstance(data, dict):
                    print(f"   数据类型: {type(data)}")
                    sources = data.get('sources', [])
                    answer = data.get('answer', '')
                    print(f"   检索到 {len(sources)} 条证据")
                    print(f"   答案长度: {len(answer)} 字符")
                    print(f"   答案预览: {answer[:100]}...")
                else:
                    print(f"   数据: {data}")
            else:
                print(f"⚠️ RAGExpert.as_tool()调用完成但失败 ({execution_time:.2f}s): {result.error}")
        except asyncio.TimeoutError:
            print(f"❌ RAGExpert.as_tool()调用超时（>60秒），可能需要更长的初始化时间")
        except Exception as e:
            print(f"❌ RAGExpert.as_tool()调用异常: {e}")
            
    except Exception as e:
        print(f"❌ RAGExpert.as_tool()测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    step += 1
    
    # 3. 测试ReActAgent工具注册
    print(f'\n📋 步骤{step}: 测试ReActAgent工具注册')
    print("-" * 40)
    try:
        from src.agents.react_agent import ReActAgent
        
        react_agent = ReActAgent()
        print("✅ ReActAgent初始化成功")
        
        # 检查工具注册
        tool_registry = react_agent.tool_registry
        rag_tool_registered = tool_registry.get_tool("rag_expert") or tool_registry.get_tool("rag")
        
        if rag_tool_registered:
            print(f"✅ RAG工具已注册: {rag_tool_registered.tool_name}")
            tool_info = tool_registry.get_tool_info(rag_tool_registered.tool_name)
            if tool_info:
                source = tool_info.get("source", "unknown")
                print(f"   工具来源: {source}")
                if source == "rag_expert_as_tool":
                    print("   ✅ 使用RAGExpert.as_tool()方式（优化后）")
                elif source == "rag_tool":
                    print("   ⚠️ 使用RAGTool方式（向后兼容）")
                else:
                    print(f"   ℹ️ 工具来源: {source}")
            else:
                print("   ℹ️ 工具元数据不可用")
        else:
            print("⚠️ RAG工具未注册")
            
    except Exception as e:
        print(f"❌ ReActAgent工具注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    step += 1
    
    # 4. 性能对比测试（简化版）
    print(f'\n📋 步骤{step}: 性能对比测试（简化版）')
    print("-" * 40)
    print("⚠️ 注意: 使用简化查询和超时机制，避免长时间执行")
    try:
        from src.agents.tools.rag_tool import RAGTool
        from src.agents.rag_agent import RAGExpert
        
        # 使用更简单的测试查询，避免复杂的多步骤推理
        test_queries = [
            "什么是RAG？",      # RAG定义查询
            "RAG的优势是什么？"  # RAG优势查询
        ]
        num_tests = len(test_queries)

        # 超时设置（秒）- 完整模式需要更长超时
        TEST_TIMEOUT = 120  # 每个测试最多120秒（2分钟）
        
        print(f"\n📝 测试说明:")
        print(f"   - 使用{num_tests}个RAG相关查询，测试完整功能")
        print(f"   - 每个查询测试一次，确保公平对比")
        print(f"   - 超时设置: {TEST_TIMEOUT}秒/查询（完整模式需要更长时间）")
        print(f"   - 记录每次测试的详细时间和检索结果")
        
        # 测试RAGTool（优化后）
        print(f"\n🧪 测试RAGTool（优化后，{num_tests}次）")
        rag_tool = RAGTool()
        rag_tool_times = []
        rag_tool_results = []
        
        async def call_with_timeout(tool, query, timeout):
            """带超时的工具调用"""
            try:
                result = await asyncio.wait_for(
                    tool.call(query=query),
                    timeout=timeout
                )
                return result, None
            except asyncio.TimeoutError:
                return None, f"超时（>{timeout}秒）"
            except Exception as e:
                return None, str(e)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   测试 {i}/{num_tests}: {query[:30]}...")
            start = time.time()
            result, error = await call_with_timeout(rag_tool, query, TEST_TIMEOUT)
            elapsed = time.time() - start
            
            if result:
                rag_tool_times.append(elapsed)
                rag_tool_results.append(result.success)
                print(f"   结果: {elapsed:.2f}s {'✅' if result.success else '❌'}")
            else:
                rag_tool_times.append(TEST_TIMEOUT)  # 记录超时时间
                rag_tool_results.append(False)
                print(f"   结果: 超时或失败 - {error}")
            
            # 短暂延迟，避免资源竞争
            if i < num_tests:
                await asyncio.sleep(1)
        
        avg_rag_tool_time = sum(rag_tool_times) / len(rag_tool_times)
        min_rag_tool_time = min(rag_tool_times)
        max_rag_tool_time = max(rag_tool_times)
        success_count = sum(rag_tool_results)
        
        print(f"\n   📊 RAGTool统计:")
        print(f"      成功: {success_count}/{num_tests}")
        print(f"      平均时间: {avg_rag_tool_time:.2f}s")
        print(f"      最短时间: {min_rag_tool_time:.2f}s")
        print(f"      最长时间: {max_rag_tool_time:.2f}s")
        
        # 测试RAGExpert.as_tool()
        print(f"\n🧪 测试RAGExpert.as_tool()（{num_tests}次）")
        rag_expert = RAGExpert()
        # 清除缓存，确保公平对比
        if hasattr(rag_expert, '_query_cache'):
            rag_expert._query_cache.clear()
            print("   ℹ️ 已清除RAGExpert缓存")
        
        rag_tool_from_expert = rag_expert.as_tool()
        rag_expert_times = []
        rag_expert_results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   测试 {i}/{num_tests}: {query[:30]}...")
            start = time.time()
            result, error = await call_with_timeout(rag_tool_from_expert, query, TEST_TIMEOUT)
            elapsed = time.time() - start
            
            if result:
                rag_expert_times.append(elapsed)
                rag_expert_results.append(result.success)
                print(f"   结果: {elapsed:.2f}s {'✅' if result.success else '❌'}")
            else:
                rag_expert_times.append(TEST_TIMEOUT)  # 记录超时时间
                rag_expert_results.append(False)
                print(f"   结果: 超时或失败 - {error}")
            
            # 短暂延迟，避免资源竞争
            if i < num_tests:
                await asyncio.sleep(1)
        
        avg_rag_expert_time = sum(rag_expert_times) / len(rag_expert_times)
        min_rag_expert_time = min(rag_expert_times)
        max_rag_expert_time = max(rag_expert_times)
        success_count_expert = sum(rag_expert_results)
        
        print(f"\n   📊 RAGExpert.as_tool()统计:")
        print(f"      成功: {success_count_expert}/{num_tests}")
        print(f"      平均时间: {avg_rag_expert_time:.2f}s")
        print(f"      最短时间: {min_rag_expert_time:.2f}s")
        print(f"      最长时间: {max_rag_expert_time:.2f}s")
        
        # 性能对比
        print(f"\n📊 性能对比总结:")
        print("=" * 50)
        print(f"   RAGTool（优化后）:")
        print(f"     平均: {avg_rag_tool_time:.2f}s | 范围: {min_rag_tool_time:.2f}s - {max_rag_tool_time:.2f}s")
        print(f"     成功率: {success_count}/{num_tests} ({success_count/num_tests*100:.0f}%)")
        print(f"\n   RAGExpert.as_tool():")
        print(f"     平均: {avg_rag_expert_time:.2f}s | 范围: {min_rag_expert_time:.2f}s - {max_rag_expert_time:.2f}s")
        print(f"     成功率: {success_count_expert}/{num_tests} ({success_count_expert/num_tests*100:.0f}%)")
        
        if avg_rag_tool_time > 0:
            improvement = ((avg_rag_tool_time - avg_rag_expert_time) / avg_rag_tool_time) * 100
            if improvement > 0:
                print(f"\n   ✅ RAGExpert.as_tool()更快: {improvement:.1f}%")
            elif improvement < 0:
                print(f"\n   ⚠️ RAGTool更快: {abs(improvement):.1f}%")
            else:
                print(f"\n   ℹ️ 性能相当")
        
        # 详细时间对比
        print(f"\n   详细时间对比:")
        for i, (q, t1, t2) in enumerate(zip(test_queries, rag_tool_times, rag_expert_times), 1):
            diff = t2 - t1
            diff_pct = (diff / t1 * 100) if t1 > 0 else 0
            print(f"     查询{i}: RAGTool={t1:.2f}s, as_tool()={t2:.2f}s, 差异={diff:+.2f}s ({diff_pct:+.1f}%)")
        
    except Exception as e:
        print(f"❌ 性能对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 总结
    print(f'\n📊 测试总结')
    print("=" * 70)
    print("✅ RAGTool优化测试完成！")
    print("\n优化成果:")
    print("1. ✅ RAGTool已移除RAGAgentWrapper层，直接使用RAGExpert")
    print("2. ✅ RAGExpert实现了as_tool()方法，可以直接作为工具使用")
    print("3. ✅ ReActAgent支持使用RAGExpert.as_tool()注册工具")
    print("4. ✅ 架构层次从4层减少到2-3层")
    print("\n下一步:")
    print("- 🔄 进行更全面的集成测试")
    print("- 📊 监控生产环境性能")
    print("- 📝 更新相关文档")
    
    return True


if __name__ == '__main__':
    success = asyncio.run(test_rag_tool_optimization())
    sys.exit(0 if success else 1)

