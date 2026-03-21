"""
基于 LangGraph 的推理工作流
将多步骤推理链表示为图结构，支持可视化、检查点和恢复
"""
import logging
import time
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any, List

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not available. Install with: pip install langgraph")

logger = logging.getLogger(__name__)


class ReasoningState(TypedDict):
    """推理状态定义"""
    query: str
    steps: Annotated[List[Dict[str, Any]], "推理步骤列表"]
    current_step_index: int
    evidence: Annotated[List[Dict[str, Any]], "证据列表"]
    answers: Annotated[List[str], "步骤答案列表"]
    final_answer: Optional[str]
    error: Optional[str]
    completed: bool


class LangGraphReasoningWorkflow:
    """基于 LangGraph 的推理工作流
    
    工作流结构：
    START → generate_steps → (循环) → execute_step → gather_evidence → 
    extract_answer → (条件判断) → execute_step 或 synthesize → END
    """
    
    def __init__(self, reasoning_engine=None):
        """初始化推理工作流"""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required. Install with: pip install langgraph")
        
        self.reasoning_engine = reasoning_engine
        self.checkpointer = MemorySaver()
        self.workflow = self._build_workflow()
        logger.info("✅ LangGraph 推理工作流初始化完成")
    
    def _build_workflow(self) -> StateGraph:
        """构建推理工作流图"""
        workflow = StateGraph(ReasoningState)
        
        # 添加节点
        workflow.add_node("generate_steps", self._generate_steps_node)
        workflow.add_node("execute_step", self._execute_step_node)
        workflow.add_node("gather_evidence", self._gather_evidence_node)
        workflow.add_node("extract_answer", self._extract_answer_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # 设置入口点
        workflow.set_entry_point("generate_steps")
        
        # 定义边
        workflow.add_edge("generate_steps", "execute_step")
        workflow.add_edge("execute_step", "gather_evidence")
        workflow.add_edge("gather_evidence", "extract_answer")
        
        # 条件路由：判断是否还有更多步骤
        workflow.add_conditional_edges(
            "extract_answer",
            self._has_more_steps,
            {
                "continue": "execute_step",
                "synthesize": "synthesize",
                "end": END
            }
        )
        
        workflow.add_edge("synthesize", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _generate_steps_node(self, state: ReasoningState) -> ReasoningState:
        """生成推理步骤节点"""
        try:
            logger.info("📝 [Generate Steps] 开始生成推理步骤")
            
            if self.reasoning_engine:
                # 使用推理引擎生成步骤
                steps = await self.reasoning_engine.generate_reasoning_steps(state['query'])
                state['steps'] = steps
            else:
                # 简化实现：直接创建步骤
                state['steps'] = [{'sub_query': state['query'], 'type': 'evidence_gathering'}]
            
            state['current_step_index'] = 0
            logger.info(f"✅ [Generate Steps] 生成了 {len(state['steps'])} 个步骤")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [Generate Steps] 失败: {e}", exc_info=True)
            state['error'] = f"生成步骤失败: {str(e)}"
            state['completed'] = True
            return state
    
    async def _execute_step_node(self, state: ReasoningState) -> ReasoningState:
        """执行步骤节点"""
        try:
            step_index = state['current_step_index']
            steps = state['steps']
            
            if step_index >= len(steps):
                state['completed'] = True
                return state
            
            current_step = steps[step_index]
            logger.info(f"🔄 [Execute Step] 执行步骤 {step_index + 1}/{len(steps)}: {current_step.get('sub_query', '')[:50]}...")
            
            # 执行步骤逻辑（简化实现）
            # 实际应该调用推理引擎的步骤执行逻辑
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [Execute Step] 失败: {e}", exc_info=True)
            state['error'] = f"执行步骤失败: {str(e)}"
            state['completed'] = True
            return state
    
    async def _gather_evidence_node(self, state: ReasoningState) -> ReasoningState:
        """收集证据节点"""
        try:
            step_index = state['current_step_index']
            current_step = state['steps'][step_index]
            
            logger.info(f"🔍 [Gather Evidence] 为步骤 {step_index + 1} 收集证据")
            
            # 收集证据逻辑（简化实现）
            # 实际应该调用证据处理器的收集逻辑
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [Gather Evidence] 失败: {e}", exc_info=True)
            state['error'] = f"收集证据失败: {str(e)}"
            state['completed'] = True
            return state
    
    async def _extract_answer_node(self, state: ReasoningState) -> ReasoningState:
        """提取答案节点"""
        try:
            step_index = state['current_step_index']
            
            logger.info(f"💡 [Extract Answer] 从步骤 {step_index + 1} 提取答案")
            
            # 提取答案逻辑（简化实现）
            # 实际应该调用答案提取器的提取逻辑
            
            state['current_step_index'] += 1
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [Extract Answer] 失败: {e}", exc_info=True)
            state['error'] = f"提取答案失败: {str(e)}"
            state['completed'] = True
            return state
    
    async def _synthesize_node(self, state: ReasoningState) -> ReasoningState:
        """合成最终答案节点"""
        try:
            logger.info("🔗 [Synthesize] 合成最终答案")
            
            # 合成答案逻辑（简化实现）
            # 实际应该调用答案合成器的合成逻辑
            
            state['completed'] = True
            logger.info("✅ [Synthesize] 最终答案合成完成")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [Synthesize] 失败: {e}", exc_info=True)
            state['error'] = f"合成答案失败: {str(e)}"
            state['completed'] = True
            return state
    
    def _has_more_steps(self, state: ReasoningState) -> Literal["continue", "synthesize", "end"]:
        """条件路由：判断是否还有更多步骤"""
        if state.get('error'):
            return "end"
        
        if state.get('completed'):
            return "end"
        
        current_index = state['current_step_index']
        total_steps = len(state.get('steps', []))
        
        if current_index >= total_steps:
            # 所有步骤完成，需要合成最终答案
            return "synthesize"
        
        return "continue"
    
    async def execute(self, query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """执行推理工作流
        
        Args:
            query: 查询
            thread_id: 线程ID（用于检查点）
            
        Returns:
            推理结果
        """
        initial_state: ReasoningState = {
            'query': query,
            'steps': [],
            'current_step_index': 0,
            'evidence': [],
            'answers': [],
            'final_answer': None,
            'error': None,
            'completed': False
        }
        
        config = {"configurable": {"thread_id": thread_id or f"reasoning_{int(time.time())}"}}
        
        try:
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            return {
                'success': final_state.get('completed', False) and not final_state.get('error'),
                'answer': final_state.get('final_answer', ''),
                'steps': final_state.get('steps', []),
                'evidence': final_state.get('evidence', []),
                'error': final_state.get('error')
            }
        except Exception as e:
            logger.error(f"推理工作流执行失败: {e}", exc_info=True)
            return {
                'success': False,
                'answer': '',
                'error': str(e)
            }

