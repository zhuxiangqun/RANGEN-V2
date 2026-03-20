#!/usr/bin/env python3
"""
ReActAgent快速验证脚本
快速验证ReActAgent → ReasoningExpert的迁移功能（只测试新Agent）
"""

import asyncio
import sys
import os
import time
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# 启用推理引擎的调试日志
logging.getLogger("src.core.reasoning").setLevel(logging.DEBUG)
logging.getLogger("src.core.llm_integration").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def run_quick_verification():
    """运行快速验证"""
    print("🚀 开始ReActAgent快速验证")
    print("=" * 70)

    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=Path(".env"))
    except ImportError:
        print("⚠️ dotenv模块未安装，跳过.env文件加载 (假设环境变量已设置)")
    except Exception as e:
        print(f"❌ 环境变量加载异常: {e}")
    
    # 检查关键环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 错误: DEEPSEEK_API_KEY未设置")
        return

    # 组件导入
    try:
        from src.agents.react_agent import ReActAgent
        from src.agents.reasoning_expert import ReasoningExpert
        from src.adapters.react_agent_adapter import ReActAgentAdapter
        from src.strategies.gradual_replacement import GradualReplacementStrategy
    except Exception as e:
        print(f"❌ 组件导入失败: {e}")
        return

    # 实例创建
    try:
        old_agent = ReActAgent()
        new_agent = ReasoningExpert()
        adapter = ReActAgentAdapter()
        # strategy = GradualReplacementStrategy(old_agent, new_agent, adapter) # 暂时注释掉
    except Exception as e:
        print(f"❌ 实例创建失败: {e}")
        return

    # 只测试 100% 替换比例
    print('\n🧪 测试场景: 100% 使用新Agent (ReasoningExpert)')
    
    context = {
        "query": "为什么天空是蓝色的？请简要解释。",
        "max_iterations": 1,
        "use_tools": False,
        "enable_knowledge_retrieval": False
    }

    try:
        # 1. 尝试直接调用适配器，验证新Agent是否正常工作
        print('\n⚡ [诊断] 尝试直接调用适配器 (绕过策略)...')
        try:
            adapter_start_time = time.time()
            # 添加超时保护，防止无限循环
            print("⏳ 正在执行适配器调用 (超时设置: 180秒)...")
            direct_result = await asyncio.wait_for(adapter.execute_adapted(context), timeout=180.0)
            adapter_time = time.time() - adapter_start_time
            print(f'✅ [诊断] 适配器直接调用成功 ({adapter_time:.3f}s)')
            # 打印直接调用的结果类型
            print(f'   结果类型: {type(direct_result)}')
            
            if direct_result:
                 print(f"   结果预览: {str(direct_result)[:200]}...")

        except asyncio.TimeoutError:
            print(f'❌ [诊断] 适配器调用超时 (60s) - 可能存在死循环或API响应过慢')
        except Exception as e:
            print(f'❌ [诊断] 适配器直接调用失败: {e}')
            import traceback
            traceback.print_exc()
            
        # 2. 通过策略调用 (暂时跳过，先验证直接调用)
        # print('\n⚡ 开始执行策略测试...')
        # strategy.replacement_rate = 1.0
        # ...
        
        print("\n🏁 诊断测试完成")
        return

        # execution_time = time.time() - start_time

        executed_by = result.get("_executed_by", "unknown")
        success = result.get("success", False)
        
        print(f'⏱️ 执行耗时: {execution_time:.3f}s')
        print(f'👤 执行者: {executed_by}')
        print(f'✅ 成功状态: {success}')
        
        if result.get("error"):
            print(f'❌ 错误: {result.get("error")}')
            
        data = result.get("data")
        if data:
            print(f'📝 结果数据类型: {type(data)}')
            if isinstance(data, dict):
                answer = data.get('answer', data.get('content', 'No answer found'))
                print(f'📄 答案预览: {str(answer)[:100]}...')
        
        if success and executed_by == "new_agent":
            print("\n🎉 快速验证成功！ReActAgent已成功迁移到ReasoningExpert。")
        else:
            print("\n❌ 快速验证失败。")

    except Exception as e:
        print(f'❌ 执行异常: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(run_quick_verification())
