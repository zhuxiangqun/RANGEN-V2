#!/usr/bin/env python3
"""
简化版RAGAgent迁移测试
可以直接在Python解释器中运行
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

async def test_rag_migration():
    """测试RAGAgent迁移"""
    print("🚀 RAGAgent迁移测试")
    print("=" * 60)
    
    # 导入组件
    from src.agents.rag_agent import RAGAgent, RAGExpert
    from src.adapters.rag_agent_adapter import RAGAgentAdapter
    from src.strategies.gradual_replacement import GradualReplacementStrategy
    
    # 创建实例
    old_agent = RAGAgent()
    new_agent = RAGExpert()
    adapter = RAGAgentAdapter()
    strategy = GradualReplacementStrategy(old_agent, new_agent, adapter)
    
    # 测试场景
    test_cases = [
        (0.0, "旧Agent"),
        (0.5, "混合"),
        (1.0, "新Agent")
    ]
    
    for rate, desc in test_cases:
        print(f"\n测试: {desc} (替换比例: {rate:.0%})")
        strategy.replacement_rate = rate
        
        context = {
            "query": f"测试RAG迁移 - {desc}",
            "type": "rag",
            "max_iterations": 1,
            "enable_knowledge_retrieval": True
        }
        
        try:
            result = await strategy.execute_with_gradual_replacement(context)
            executed_by = result.get("_executed_by", "unknown")
            success = result.get("success", False)
            icon = "✅" if success else "❌"
            agent_name = "RAGAgent" if executed_by == "old_agent" else "RAGExpert"
            print(f"  {icon} {agent_name}: success={success}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
        
        await asyncio.sleep(1)
    
    print("\n✅ 测试完成")

if __name__ == '__main__':
    asyncio.run(test_rag_migration())

