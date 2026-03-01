"""
LangGraph 使用示例
演示如何使用 LangGraph 版本的 ReAct Agent 和推理工作流
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.langgraph_react_agent import LangGraphReActAgent
from src.core.reasoning.langgraph_reasoning_workflow import LangGraphReasoningWorkflow


async def example_react_agent():
    """示例：使用 LangGraph ReAct Agent"""
    print("=" * 80)
    print("示例1: LangGraph ReAct Agent")
    print("=" * 80)
    
    try:
        # 创建 Agent
        agent = LangGraphReActAgent(agent_name="ExampleReActAgent")
        
        # 执行查询
        context = {
            "query": "What is the capital of France?"
        }
        
        print(f"\n查询: {context['query']}")
        print("\n执行中...")
        
        result = await agent.execute(context)
        
        print(f"\n✅ 执行成功: {result.success}")
        print(f"答案: {result.data.get('answer', '') if result.data else 'N/A'}")
        print(f"迭代次数: {result.metadata.get('iterations', 0) if result.metadata else 0}")
        print(f"置信度: {result.confidence}")
        print(f"执行时间: {result.processing_time:.2f}秒")
        
        if result.data:
            print(f"\n思考历史:")
            for i, thought in enumerate(result.data.get('thoughts', []), 1):
                print(f"  {i}. {thought[:100]}...")
        
    except ImportError as e:
        print(f"❌ LangGraph 未安装: {e}")
        print("请运行: pip install langgraph")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def example_reasoning_workflow():
    """示例：使用 LangGraph 推理工作流"""
    print("\n" + "=" * 80)
    print("示例2: LangGraph 推理工作流")
    print("=" * 80)
    
    try:
        # 创建工作流
        workflow = LangGraphReasoningWorkflow()
        
        # 执行推理
        query = "Who was the 15th first lady of the United States?"
        thread_id = "example_reasoning_123"
        
        print(f"\n查询: {query}")
        print(f"线程ID: {thread_id}")
        print("\n执行中...")
        
        result = await workflow.execute(query, thread_id=thread_id)
        
        print(f"\n✅ 执行成功: {result['success']}")
        print(f"答案: {result.get('answer', '')}")
        print(f"步骤数: {len(result.get('steps', []))}")
        print(f"证据数: {len(result.get('evidence', []))}")
        
        if result.get('error'):
            print(f"错误: {result['error']}")
        
    except ImportError as e:
        print(f"❌ LangGraph 未安装: {e}")
        print("请运行: pip install langgraph")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def example_checkpoint_recovery():
    """示例：检查点和恢复"""
    print("\n" + "=" * 80)
    print("示例3: 检查点和恢复")
    print("=" * 80)
    
    try:
        agent = LangGraphReActAgent(agent_name="CheckpointAgent")
        
        # 第一次执行（创建检查点）
        thread_id = "checkpoint_example_123"
        context = {
            "query": "What is the capital of France?"
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"\n第一次执行（创建检查点）...")
        initial_state = {
            'query': context['query'],
            'thoughts': [],
            'observations': [],
            'actions': [],
            'task_complete': False,
            'iteration': 0,
            'max_iterations': 10,
            'error': None,
            'current_thought': None,
            'current_action': None,
            'current_observation': None
        }
        
        # 执行到某个节点（这里简化，实际应该执行部分节点）
        print("执行中...")
        result = await agent.workflow.ainvoke(initial_state, config)
        
        print(f"✅ 第一次执行完成")
        print(f"迭代次数: {result.get('iteration', 0)}")
        
        # 从检查点恢复（示例）
        print(f"\n从检查点恢复...")
        print("（注意：这需要根据 LangGraph 的实际 API 调整）")
        
    except ImportError as e:
        print(f"❌ LangGraph 未安装: {e}")
        print("请运行: pip install langgraph")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("LangGraph 使用示例")
    print("=" * 80)
    print("\n这些示例演示了如何使用 LangGraph 框架实现可描述、可治理、")
    print("可复用、可恢复的 Agent 工作流。")
    print("\n注意：需要先安装 LangGraph:")
    print("  pip install langgraph")
    print("\n" + "=" * 80)
    
    # 运行示例
    await example_react_agent()
    await example_reasoning_workflow()
    await example_checkpoint_recovery()
    
    print("\n" + "=" * 80)
    print("示例完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

