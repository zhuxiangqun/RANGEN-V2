"""
LangGraph 子图构建器

用于将复杂的工作流路径封装为子图，提升模块化和可维护性
"""
import logging
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class ReasoningSubgraphBuilder:
    """推理路径子图构建器"""
    
    def __init__(self, reasoning_nodes):
        """初始化推理子图构建器
        
        Args:
            reasoning_nodes: ReasoningNodes 实例
        """
        self.reasoning_nodes = reasoning_nodes
    
    def build_subgraph(self) -> Optional[StateGraph]:
        """构建推理路径子图
        
        Returns:
            推理子图，如果不可用则返回 None
        """
        if not LANGGRAPH_AVAILABLE or not self.reasoning_nodes:
            return None
        
        try:
            subgraph = StateGraph(ResearchSystemState)
            
            # 添加推理节点
            subgraph.add_node("generate_steps", self.reasoning_nodes.generate_steps_node)
            subgraph.add_node("execute_step", self.reasoning_nodes.execute_step_node)
            subgraph.add_node("gather_evidence", self.reasoning_nodes.gather_evidence_node)
            subgraph.add_node("extract_step_answer", self.reasoning_nodes.extract_step_answer_node)
            subgraph.add_node("synthesize_reasoning_answer", self.reasoning_nodes.synthesize_answer_node)
            
            # 设置入口点
            subgraph.set_entry_point("generate_steps")
            
            # 添加边
            subgraph.add_edge("generate_steps", "execute_step")
            subgraph.add_edge("execute_step", "gather_evidence")
            subgraph.add_edge("gather_evidence", "extract_step_answer")
            
            # 条件路由：判断是否继续执行推理步骤
            # 注意：_should_continue_reasoning 方法在 UnifiedResearchWorkflow 中
            # 这里需要从 workflow 实例获取，或者创建一个包装函数
            # 暂时使用一个简单的条件函数
            def should_continue(state: ResearchSystemState) -> str:
                """判断是否继续推理"""
                steps = state.get('reasoning_steps', [])
                current_step_index = state.get('current_reasoning_step_index', 0)
                
                if current_step_index >= len(steps):
                    return "synthesize"
                
                # 检查是否有错误
                if state.get('error'):
                    return "end"
                
                return "continue"
            
            subgraph.add_conditional_edges(
                "extract_step_answer",
                should_continue,
                {
                    "continue": "execute_step",
                    "synthesize": "synthesize_reasoning_answer",
                    "end": END
                }
            )
            
            subgraph.add_edge("synthesize_reasoning_answer", END)
            
            logger.info("✅ [子图构建] 推理路径子图构建完成")
            return subgraph
            
        except Exception as e:
            logger.error(f"❌ [子图构建] 推理路径子图构建失败: {e}")
            return None


class MultiAgentSubgraphBuilder:
    """多智能体协调子图构建器"""
    
    def __init__(self, agent_nodes):
        """初始化多智能体子图构建器
        
        Args:
            agent_nodes: AgentNodes 实例
        """
        self.agent_nodes = agent_nodes
    
    def build_subgraph(self, include_chief_agent: bool = True) -> Optional[StateGraph]:
        """构建多智能体协调子图
        
        Args:
            include_chief_agent: 是否包含 ChiefAgent（核心大脑）
        
        Returns:
            多智能体子图，如果不可用则返回 None
        """
        if not LANGGRAPH_AVAILABLE or not self.agent_nodes:
            return None
        
        try:
            subgraph = StateGraph(ResearchSystemState)
            
            # 添加专家智能体节点
            if include_chief_agent:
                subgraph.add_node("chief_agent", self.agent_nodes.chief_agent_node)
                entry_point = "chief_agent"
            else:
                entry_point = "memory_agent"
            
            subgraph.add_node("memory_agent", self.agent_nodes.memory_agent_node)
            subgraph.add_node("knowledge_retrieval_agent", self.agent_nodes.knowledge_retrieval_agent_node)
            subgraph.add_node("reasoning_agent", self.agent_nodes.reasoning_agent_node)
            subgraph.add_node("answer_generation_agent", self.agent_nodes.answer_generation_agent_node)
            subgraph.add_node("citation_agent", self.agent_nodes.citation_agent_node)
            
            # 设置入口点
            subgraph.set_entry_point(entry_point)
            
            # 添加边：专家智能体执行序列
            if include_chief_agent:
                subgraph.add_edge("chief_agent", "memory_agent")
            
            subgraph.add_edge("memory_agent", "knowledge_retrieval_agent")
            subgraph.add_edge("knowledge_retrieval_agent", "reasoning_agent")
            subgraph.add_edge("reasoning_agent", "answer_generation_agent")
            subgraph.add_edge("answer_generation_agent", "citation_agent")
            subgraph.add_edge("citation_agent", END)
            
            logger.info("✅ [子图构建] 多智能体协调子图构建完成")
            return subgraph
            
        except Exception as e:
            logger.error(f"❌ [子图构建] 多智能体协调子图构建失败: {e}")
            return None

