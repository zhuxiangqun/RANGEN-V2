#!/usr/bin/env python3
"""
LangGraph SOP节点模块 - SOP召回、执行和学习
将SOP学习系统与LangGraph工作流深度集成
"""
import logging
import time
from typing import Dict, Any, Optional, List, TypedDict, Annotated
import operator

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent 状态定义"""
    query: str
    context: Dict[str, Any]
    route: str
    steps: Annotated[list, operator.add]
    final_answer: str
    error: str
    quality_score: float
    quality_passed: bool
    quality_feedback: str
    retry_count: int
    task_id: str
    lint_issues: List[Dict[str, Any]]
    review_passed: bool
    review_feedback: str
    contract_fulfilled: bool
    harness_metrics: Dict[str, Any]
    sop_recall_results: List[Dict[str, Any]]
    sop_execution_results: List[Dict[str, Any]]
    sop_execution_success: bool
    has_relevant_sops: bool
    sop_error: Optional[str]


# 延迟导入避免循环依赖
def _get_sop_learning_system():
    from src.core.sop_learning import SOPLearningSystem, get_sop_learning_system as _get
    return _get()


class SOPNodes:
    """SOP相关LangGraph节点集合"""
    
    def __init__(self, sop_system=None):
        """初始化SOP节点
        
        Args:
            sop_system: SOPLearningSystem实例（可选，默认单例）
        """
        self.sop_system = sop_system or _get_sop_learning_system()
        logger.info("SOP nodes initialized")
    
    async def sop_recall_node(self, state: AgentState) -> AgentState:
        """SOP召回节点
        
        从SOP记忆系统中召回与当前任务相关的SOP
        """
        logger.info("SOP Recall: Starting SOP recall...")
        start_time = time.time()
        
        try:
            # 获取任务描述
            task_description = state.get("query", "") or state.get("task_description", "")
            
            if not task_description:
                logger.warning("SOP Recall: No task description, skipping")
                state["sop_recall_results"] = []
                return state
            
            # 获取上下文
            context = {
                "session_id": state.get("session_id"),
                "agent_type": state.get("agent_type"),
                "capabilities": state.get("capabilities", [])
            }
            
            # 调用SOP学习系统的召回功能
            recalled_sops = self.sop_system.recall_sop(task_description, context)
            
            # 格式化结果
            sop_results = []
            for sop_data in recalled_sops:
                sop_results.append({
                    "sop_id": sop_data["sop"].sop_id,
                    "name": sop_data["sop"].name,
                    "description": sop_data["sop"].description,
                    "relevance": sop_data["relevance"],
                    "steps": [{"hand": step.hand_name, "description": step.description} 
                             for step in sop_data["sop"].steps],
                    "success_rate": sop_data["sop"].success_rate,
                    "execution_count": sop_data["sop"].execution_count
                })
            
            # 更新状态
            state["sop_recall_results"] = sop_results
            state["has_relevant_sops"] = len(sop_results) > 0
            
            elapsed = time.time() - start_time
            logger.info(f"SOP Recall: Found {len(sop_results)} relevant SOPs (elapsed: {elapsed:.2f}s)")
            
        except Exception as e:
            logger.error(f"SOP Recall failed: {e}")
            state["sop_recall_results"] = []
            state["sop_error"] = str(e)
        
        return state
    
    async def sop_execution_node(self, state: AgentState) -> AgentState:
        """SOP执行节点
        
        执行已召回的SOP步骤序列
        """
        logger.info("SOP Execution: Starting SOP execution...")
        start_time = time.time()
        
        try:
            # 获取召回的SOP
            recalled_sops = state.get("sop_recall_results", [])
            
            if not recalled_sops:
                logger.info("SOP Execution: No recalled SOPs, skipping")
                state["sop_execution_results"] = []
                return state
            
            # 选择最高相关性的SOP
            selected_sop = recalled_sops[0]
            logger.info(f"SOP Execution: Selected SOP: {selected_sop['name']}")
            
            # 获取SOP详情
            sop_id = selected_sop["sop_id"]
            sop = self.sop_system.get_sop(sop_id)
            
            if not sop:
                logger.error(f"SOP Execution: Cannot get SOP: {sop_id}")
                state["sop_execution_results"] = []
                return state
            
            # 执行SOP步骤
            execution_results = []
            from src.hands.registry import HandRegistry
            
            hand_registry = HandRegistry()
            
            for i, step in enumerate(sop.steps):
                step_result = {
                    "step_id": step.step_id,
                    "hand_name": step.hand_name,
                    "description": step.description,
                    "success": False,
                    "error": None
                }
                
                try:
                    # 获取Hand并执行
                    hand = hand_registry.get_hand(step.hand_name)
                    
                    if hand:
                        # 执行Hand
                        result = await hand.execute(**step.parameters)
                        step_result["success"] = result.success
                        step_result["output"] = result.output
                        if result.error:
                            step_result["error"] = result.error
                    else:
                        step_result["error"] = f"Hand not found: {step.hand_name}"
                        
                except Exception as e:
                    step_result["error"] = str(e)
                    logger.error(f"Step {i+1} execution failed: {e}")
                
                execution_results.append(step_result)
                
                # 如果步骤失败且不可跳过，停止执行
                if not step_result["success"] and step_result["error"]:
                    logger.warning(f"Step {i+1} failed, stopping execution")
                    break
            
            # 记录执行结果
            state["sop_execution_results"] = execution_results
            state["sop_execution_success"] = all(r.get("success", False) for r in execution_results)
            
            elapsed = time.time() - start_time
            success_count = sum(1 for r in execution_results if r.get("success", False))
            logger.info(f"SOP Execution: {success_count}/{len(execution_results)} steps succeeded (elapsed: {elapsed:.2f}s)")
            
            # 触发学习（如果执行成功）
            if state["sop_execution_success"]:
                await self._trigger_sop_learning(state, sop, execution_results)
            
        except Exception as e:
            logger.error(f"SOP Execution failed: {e}")
            state["sop_execution_results"] = []
            state["sop_error"] = str(e)
        
        return state
    
    async def _trigger_sop_learning(self, state: AgentState, sop, execution_results: List[Dict]) -> None:
        """触发SOP学习
        
        从成功执行中学习，更新SOP
        """
        try:
            # 转换为学习系统需要的格式
            execution_steps = []
            for result in execution_results:
                execution_steps.append({
                    "hand_name": result["hand_name"],
                    "description": result["description"],
                    "parameters": {},
                    "success": result.get("success", False)
                })
            
            # 调用学习
            task_name = state.get("query", "unknown_task")
            execution_id = f"exec_{int(time.time())}"
            
            self.sop_system.learn_from_execution(
                task_name=task_name,
                execution_steps=execution_steps,
                success=True,
                execution_id=execution_id,
                importance=1.0
            )
            
            logger.info(f"SOP Learning: Learned from execution: {task_name}")
            
        except Exception as e:
            logger.warning(f"SOP Learning failed: {e}")
    
    async def sop_learning_hook(self, state: AgentState) -> AgentState:
        """SOP学习钩子节点
        
        在任务完成后自动触发学习
        """
        logger.info("SOP Learning Hook: Checking if learning is needed...")
        
        try:
            # 检查是否有执行历史
            execution_history = state.get("execution_history", [])
            
            if not execution_history:
                logger.info("SOP Learning Hook: No execution history, skipping")
                return state
            
            # 获取最后执行的步骤
            last_execution = execution_history[-1] if execution_history else None
            
            if last_execution and last_execution.get("success", False):
                task_name = state.get("query", "unknown_task")
                execution_id = f"exec_{int(time.time())}"
                
                # 学习
                self.sop_system.learn_from_execution(
                    task_name=task_name,
                    execution_steps=last_execution.get("steps", []),
                    success=last_execution.get("success", False),
                    execution_id=execution_id,
                    importance=1.0
                )
                
                logger.info(f"SOP Learning Hook: Learning completed: {task_name}")
            
        except Exception as e:
            logger.warning(f"SOP Learning Hook failed: {e}")
        
        return state
    
    def get_sop_statistics(self) -> Dict[str, Any]:
        """获取SOP系统统计信息"""
        return self.sop_system.get_statistics()


# 便捷函数：创建SOP节点实例
def create_sop_nodes() -> "SOPNodes":
    """创建SOP节点实例（工厂函数）"""
    return SOPNodes()


# LangGraph节点函数（与状态类型兼容）
async def sop_recall(state: AgentState) -> AgentState:
    """SOP召回节点函数（LangGraph兼容）"""
    nodes = SOPNodes()
    return await nodes.sop_recall_node(state)


async def sop_execute(state: AgentState) -> AgentState:
    """SOP执行节点函数（LangGraph兼容）"""
    nodes = SOPNodes()
    return await nodes.sop_execution_node(state)


async def sop_learn(state: AgentState) -> AgentState:
    """SOP学习节点函数（LangGraph兼容）"""
    nodes = SOPNodes()
    return await nodes.sop_learning_hook(state)
