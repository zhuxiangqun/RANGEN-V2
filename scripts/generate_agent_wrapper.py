#!/usr/bin/env python3
"""
批量生成Agent包装器和替换脚本

根据配置批量生成Agent包装器和替换脚本，提高迁移效率。
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Agent配置：源Agent名称 -> (目标Agent名称, 适配器类名, 源Agent类路径, 使用文件列表)
AGENT_CONFIGS = {
    "ContextEngineeringAgent": (
        "MemoryManager",
        "ContextEngineeringAgentAdapter",
        "src.agents.context_engineering_agent.ContextEngineeringAgent",
        ["src/core/langgraph_core_nodes.py"]
    ),
    "MemoryAgent": (
        "MemoryManager",
        "MemoryAgentAdapter",
        "src.agents.expert_agents.MemoryAgent",
        []  # 需要检查使用情况
    ),
    "OptimizedKnowledgeRetrievalAgent": (
        "RAGExpert",
        "OptimizedKnowledgeRetrievalAgentAdapter",
        "src.agents.optimized_knowledge_retrieval_agent.OptimizedKnowledgeRetrievalAgent",
        ["src/core/reasoning/engine.py"]
    ),
    "EnhancedAnalysisAgent": (
        "ReasoningExpert",
        "EnhancedAnalysisAgentAdapter",
        "src.agents.enhanced_analysis_agent.EnhancedAnalysisAgent",
        ["src/async_research_integrator.py"]
    ),
    "LearningSystem": (
        "LearningOptimizer",
        "LearningSystemAdapter",
        "src.agents.learning_system.LearningSystem",
        ["src/unified_research_system.py", "src/core/langgraph_learning_nodes.py"]
    ),
    "IntelligentStrategyAgent": (
        "AgentCoordinator",
        "IntelligentStrategyAgentAdapter",
        "src.agents.intelligent_strategy_agent.IntelligentStrategyAgent",
        ["src/async_research_integrator.py", "src/agents/agent_builder.py"]
    ),
    "FactVerificationAgent": (
        "QualityController",
        "FactVerificationAgentAdapter",
        "src.agents.fact_verification_agent.FactVerificationAgent",
        []  # 需要检查使用情况
    ),
    "IntelligentCoordinatorAgent": (
        "AgentCoordinator",
        "IntelligentCoordinatorAgentAdapter",
        "src.agents.intelligent_coordinator_agent.IntelligentCoordinatorAgent",
        []  # 需要检查使用情况
    ),
    "StrategicChiefAgent": (
        "AgentCoordinator",
        "StrategicChiefAgentAdapter",
        "src.agents.strategic_chief_agent.StrategicChiefAgent",
        [
            "src/core/layered_architecture_adapter.py",
            "src/core/langgraph_layered_workflow_fixed.py",
            "src/core/simplified_layered_workflow.py",
            "src/core/langgraph_layered_workflow.py"
        ]
    ),
}


def generate_wrapper(agent_name: str, config: Tuple[str, str, str, List[str]]) -> str:
    """生成Agent包装器代码"""
    target_agent, adapter_class, source_path, _ = config
    
    # 提取源Agent类名
    source_class = source_path.split('.')[-1]
    source_module = '.'.join(source_path.split('.')[:-1])
    
    wrapper_code = f'''#!/usr/bin/env python3
"""
{agent_name}包装器 - 使用逐步替换策略

将{agent_name}的调用包装为使用逐步替换策略，实现平滑迁移到{target_agent}。
"""

import logging
from typing import Dict, Any, Optional
from {source_module.replace('src.', '..') if source_module.startswith('src.') else source_module} import {source_class}
from .base_agent import BaseAgent
from ..adapters.{adapter_class.lower().replace('adapter', '_adapter')} import {adapter_class}
from ..strategies.gradual_replacement import GradualReplacementStrategy

logger = logging.getLogger(__name__)


class {agent_name}Wrapper(BaseAgent):
    """{agent_name}包装器 - 使用逐步替换策略
    
    这个包装器实现了与{agent_name}相同的接口，但内部使用逐步替换策略
    将请求逐步从{agent_name}迁移到{target_agent}。
    """
    
    def __init__(self, enable_gradual_replacement: bool = True, initial_replacement_rate: float = 0.01, **kwargs):
        """
        初始化{agent_name}包装器
        
        Args:
            enable_gradual_replacement: 是否启用逐步替换
            initial_replacement_rate: 初始替换比例（默认1%）
            **kwargs: 传递给源Agent的其他参数
        """
        # 初始化BaseAgent（保持兼容性）
        from .base_agent import AgentConfig
        config = AgentConfig(
            agent_id="{agent_name.lower()}",
            agent_type="{agent_name.lower()}_wrapper"
        )
        super().__init__("{agent_name.lower()}", ["migration", "gradual_replacement"], config)
        
        # 创建旧Agent实例
        self.old_agent = {source_class}(**kwargs)
        
        self.enable_gradual_replacement = enable_gradual_replacement
        self.replacement_strategy: Optional[GradualReplacementStrategy] = None
        
        if enable_gradual_replacement:
            try:
                # 创建适配器
                adapter = {adapter_class}()
                new_agent = adapter.target_agent
                
                # 创建逐步替换策略
                self.replacement_strategy = GradualReplacementStrategy(
                    old_agent=self.old_agent,
                    new_agent=new_agent,
                    adapter=adapter
                )
                self.replacement_strategy.replacement_rate = initial_replacement_rate
                
                logger.info(
                    f"✅ {agent_name}包装器初始化成功，逐步替换已启用 "
                    f"(初始替换比例: {{initial_replacement_rate:.0%}})"
                )
            except Exception as e:
                logger.warning(f"⚠️ 逐步替换策略初始化失败，将使用旧Agent: {{e}}")
                self.enable_gradual_replacement = False
                self.replacement_strategy = None
        else:
            logger.info("ℹ️ {agent_name}包装器初始化成功，逐步替换未启用")
    
    async def execute(self, context: Dict[str, Any]) -> Any:
        """
        执行任务 - 使用逐步替换策略
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if self.enable_gradual_replacement and self.replacement_strategy:
            # 使用逐步替换策略
            try:
                result = await self.replacement_strategy.execute_with_gradual_replacement(context)
                return result
            except Exception as e:
                logger.error(f"❌ 逐步替换执行失败，回退到旧Agent: {{e}}")
                # 回退到旧Agent
                return await self.old_agent.execute(context)
        else:
            # 直接使用旧Agent
            return await self.old_agent.execute(context)
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        处理查询 - 实现BaseAgent的抽象方法
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            
        Returns:
            AgentResult: 处理结果
        """
        # 准备上下文
        exec_context = {{"query": query}}
        if context:
            exec_context.update(context)
        
        # 使用同步包装异步execute方法
        import asyncio
        
        try:
            # 如果已有事件循环，使用它
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，使用线程池执行
                import concurrent.futures
                def run_in_thread():
                    return asyncio.run(self.execute(exec_context))
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()
            else:
                return loop.run_until_complete(self.execute(exec_context))
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(self.execute(exec_context))
    
    def get_replacement_stats(self) -> Optional[Dict[str, Any]]:
        """获取替换统计信息"""
        if self.replacement_strategy:
            return self.replacement_strategy.get_replacement_stats()
        return None
    
    def increase_replacement_rate(self, step: float = 0.1) -> Optional[float]:
        """增加替换比例"""
        if self.replacement_strategy:
            return self.replacement_strategy.increase_replacement_rate(step)
        return None
    
    def should_increase_rate(self) -> bool:
        """判断是否应该增加替换比例"""
        if self.replacement_strategy:
            return self.replacement_strategy.should_increase_rate()
        return False
'''
    return wrapper_code


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量生成Agent包装器和替换脚本")
    parser.add_argument(
        "--agent",
        help="指定要生成的Agent名称（可选，默认生成所有）"
    )
    parser.add_argument(
        "--output-dir",
        default="src/agents",
        help="输出目录（默认: src/agents）"
    )
    
    args = parser.parse_args()
    
    agents_to_generate = [args.agent] if args.agent else list(AGENT_CONFIGS.keys())
    
    print("=" * 80)
    print("批量生成Agent包装器")
    print("=" * 80)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for agent_name in agents_to_generate:
        if agent_name not in AGENT_CONFIGS:
            print(f"⚠️ 未知的Agent: {agent_name}")
            continue
        
        config = AGENT_CONFIGS[agent_name]
        wrapper_code = generate_wrapper(agent_name, config)
        
        wrapper_file = output_dir / f"{agent_name.lower()}_wrapper.py"
        wrapper_file.write_text(wrapper_code, encoding='utf-8')
        print(f"✅ 生成包装器: {wrapper_file}")
    
    print("\n" + "=" * 80)
    print("生成完成")
    print("=" * 80)


if __name__ == "__main__":
    main()

