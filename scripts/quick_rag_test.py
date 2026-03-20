#!/usr/bin/env python3
"""
快速RAGTool优化测试 - 仅验证基本功能
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

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=project_root / ".env")
except ImportError:
    pass

async def quick_test():
    """快速测试 - 仅验证基本功能"""
    print("🚀 快速RAGTool优化测试")
    print("=" * 60)
    
    try:
        from src.agents.tools.rag_tool import RAGTool
        from src.agents.rag_agent import RAGExpert
        
        # 测试1: RAGTool初始化
        print("\n📋 测试1: RAGTool初始化")
        print("-" * 40)
        rag_tool = RAGTool()
        print("✅ RAGTool初始化成功")
        
        # 检查内部使用的Agent类型
        rag_agent = rag_tool._get_rag_agent()
        agent_type = type(rag_agent).__name__
        print(f"✅ RAG Agent类型: {agent_type}")
        if agent_type == "RAGExpert":
            print("✅ 优化成功: 直接使用RAGExpert，已移除RAGAgentWrapper层")
        else:
            print("⚠️ 仍在使用其他Agent类型")
        
        # 测试2: RAGExpert.as_tool()
        print("\n📋 测试2: RAGExpert.as_tool()")
        print("-" * 40)
        rag_expert = RAGExpert()
        rag_tool_from_expert = rag_expert.as_tool()
        print(f"✅ RAGExpert.as_tool()成功，工具类型: {type(rag_tool_from_expert).__name__}")
        print(f"   工具名称: {rag_tool_from_expert.tool_name}")
        print(f"   工具描述: {rag_tool_from_expert.description}")
        
        # 测试3: 简单查询测试（带超时）
        print("\n📋 测试3: 简单查询测试（30秒超时）")
        print("-" * 40)
        test_query = "RAG是什么？"
        print(f"查询: {test_query}")
        
        # 测试RAGTool
        print("\n🧪 测试RAGTool...")
        try:
            start = time.time()
            result = await asyncio.wait_for(
                rag_tool.call(query=test_query),
                timeout=30.0
            )
            elapsed = time.time() - start
            if result.success:
                print(f"✅ RAGTool调用成功 ({elapsed:.2f}s)")
            else:
                print(f"⚠️ RAGTool调用完成但失败 ({elapsed:.2f}s): {result.error}")
        except asyncio.TimeoutError:
            print("❌ RAGTool调用超时（>30秒）")
        except Exception as e:
            print(f"❌ RAGTool调用异常: {e}")
        
        # 测试RAGExpert.as_tool()
        print("\n🧪 测试RAGExpert.as_tool()...")
        try:
            start = time.time()
            result = await asyncio.wait_for(
                rag_tool_from_expert.call(query=test_query),
                timeout=30.0
            )
            elapsed = time.time() - start
            if result.success:
                print(f"✅ RAGExpert.as_tool()调用成功 ({elapsed:.2f}s)")
            else:
                print(f"⚠️ RAGExpert.as_tool()调用完成但失败 ({elapsed:.2f}s): {result.error}")
        except asyncio.TimeoutError:
            print("❌ RAGExpert.as_tool()调用超时（>30秒）")
        except Exception as e:
            print(f"❌ RAGExpert.as_tool()调用异常: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 快速测试完成！")
        print("\n说明:")
        print("- 本次测试仅验证基本功能，不进行完整性能对比")
        print("- 如需完整性能测试，请使用优化后的 test_rag_tool_optimization.py")
        print("- 优化后的测试脚本已添加超时机制，避免长时间执行")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(quick_test())

