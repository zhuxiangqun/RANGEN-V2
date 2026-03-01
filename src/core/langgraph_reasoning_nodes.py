"""
推理节点模块 - 阶段3.1
将推理引擎集成到 LangGraph 工作流中
"""
import logging
import time
import re
from typing import Dict, Any, Optional, List
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class ReasoningNodes:
    """推理节点集合 - 集成 RealReasoningEngine 到 LangGraph 工作流"""
    
    def __init__(self, system=None):
        """初始化推理节点
        
        Args:
            system: UnifiedResearchSystem 实例（可选）
        """
        self.system = system
        self.reasoning_engine = None
        self._initialize_reasoning_engine()
    
    def _initialize_reasoning_engine(self):
        """初始化推理引擎"""
        try:
            from src.core.reasoning.engine import RealReasoningEngine
            self.reasoning_engine = RealReasoningEngine()
            logger.info("✅ 推理引擎初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 推理引擎初始化失败: {e}")
            self.reasoning_engine = None
    
    async def generate_steps_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """生成推理步骤节点
        
        从查询生成推理步骤列表
        """
        logger.info("📝 [Generate Steps] 开始生成推理步骤")
        start_time = time.time()
        
        try:
            query = state.get('query', '')
            if not query:
                state['error'] = "查询为空，无法生成推理步骤"
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append({
                    'node': 'generate_steps',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                return state
            
            # 使用推理引擎生成步骤
            if self.reasoning_engine:
                # 优先使用推理引擎已有的 step_generator
                if hasattr(self.reasoning_engine, 'step_generator') and self.reasoning_engine.step_generator:
                    step_generator = self.reasoning_engine.step_generator
                    logger.debug("✅ [Generate Steps] 使用推理引擎已有的 step_generator")
                else:
                    # 降级：创建新的 StepGenerator（使用正确的参数）
                    from src.core.reasoning.step_generator import StepGenerator
                    step_generator = StepGenerator(
                        llm_integration=self.reasoning_engine.llm_integration,
                        fast_llm_integration=self.reasoning_engine.fast_llm_integration,
                        prompt_generator=getattr(self.reasoning_engine, 'prompt_generator', None),
                        context_manager=getattr(self.reasoning_engine, 'context_manager', None),
                        subquery_processor=getattr(self.reasoning_engine, 'subquery_processor', None),
                        evidence_processor=getattr(self.reasoning_engine, 'evidence_processor', None),
                        learning_manager=getattr(self.reasoning_engine, 'learning_manager', None),
                        config_center=getattr(self.reasoning_engine, 'config_center', None),
                        cache_manager=getattr(self.reasoning_engine, 'cache_manager', None)
                    )
                    logger.debug("✅ [Generate Steps] 创建新的 step_generator")
                
                # 生成推理步骤（注意：generate_reasoning_steps 是同步方法，不是协程）
                reasoning_steps = step_generator.generate_reasoning_steps(
                    query=query,
                    context=state.get('context', {})
                )
                
                # 🚀 修复：确保返回的是列表格式
                if not isinstance(reasoning_steps, list):
                    logger.warning(f"⚠️ [Generate Steps] 返回的不是列表格式: {type(reasoning_steps)}, 值: {reasoning_steps}")
                    if reasoning_steps is None:
                        reasoning_steps = []
                    else:
                        # 尝试转换
                        try:
                            reasoning_steps = list(reasoning_steps) if hasattr(reasoning_steps, '__iter__') else [reasoning_steps]
                        except Exception as e:
                            logger.error(f"❌ [Generate Steps] 无法转换推理步骤: {e}")
                            reasoning_steps = []
                
                # 更新状态
                state['reasoning_steps'] = reasoning_steps
                state['current_step_index'] = 0
                state['step_answers'] = []
                
                # 🚀 修复：确保 metadata 存在并初始化
                if 'metadata' not in state:
                    state['metadata'] = {}
                
                # 记录执行时间
                execution_time = time.time() - start_time
                # 🚀 修复：确保 node_execution_times 和 node_times 存在
                if 'node_execution_times' not in state:
                    state['node_execution_times'] = {}
                if 'node_times' not in state:
                    state['node_times'] = {}
                state['node_execution_times']['generate_steps'] = execution_time
                state['node_times']['generate_steps'] = execution_time
                
                logger.info(f"✅ [Generate Steps] 生成了 {len(reasoning_steps)} 个推理步骤 (耗时: {execution_time:.2f}s)")
                logger.debug(f"🔍 [Generate Steps] 推理步骤详情: {[step.get('sub_query', '')[:50] for step in reasoning_steps[:3]]}")
                logger.debug(f"🔍 [Generate Steps] 状态更新: reasoning_steps={len(reasoning_steps)}, current_step_index={state.get('current_step_index')}, step_answers={len(state.get('step_answers', []))}")
            else:
                # 降级：创建简单步骤
                state['reasoning_steps'] = [{
                    'sub_query': query,
                    'type': 'evidence_gathering',
                    'description': f'检索查询相关信息: {query}',
                    'depends_on': []
                }]
                state['current_step_index'] = 0
                state['step_answers'] = []
                
                logger.warning("⚠️ [Generate Steps] 推理引擎不可用，使用降级方案")
        
        except Exception as e:
            error_msg = f"生成推理步骤失败: {str(e)}"
            logger.error(f"❌ [Generate Steps] {error_msg}", exc_info=True)
            state['error'] = error_msg
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'generate_steps',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：创建简单步骤
            state['reasoning_steps'] = [{
                'sub_query': query,
                'type': 'evidence_gathering',
                'description': f'检索查询相关信息: {query}',
                'depends_on': []
            }]
            state['current_step_index'] = 0
            state['step_answers'] = []
        
        return state
    
    async def execute_step_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """执行单个推理步骤节点
        
        执行当前步骤，准备收集证据
        """
        logger.info("🔧 [Execute Step] 开始执行推理步骤")
        start_time = time.time()
        
        try:
            # 🚀 修复：确保 metadata 存在
            if 'metadata' not in state:
                state['metadata'] = {}
            
            reasoning_steps = state.get('reasoning_steps', [])
            current_step_index = state.get('current_step_index', 0)
            
            # 🚀 修复：详细日志诊断状态传递问题
            logger.debug(f"🔍 [Execute Step] 推理步骤数: {len(reasoning_steps)}, 当前步骤索引: {current_step_index}")
            logger.debug(f"🔍 [Execute Step] 状态键: {list(state.keys())}")
            logger.debug(f"🔍 [Execute Step] reasoning_steps 类型: {type(reasoning_steps)}")
            if reasoning_steps:
                logger.debug(f"🔍 [Execute Step] 第一个步骤: {reasoning_steps[0] if isinstance(reasoning_steps, list) else 'N/A'}")
            
            if not reasoning_steps:
                error_msg = "没有推理步骤"
                logger.warning(f"⚠️ [Execute Step] {error_msg}")
                logger.debug(f"🔍 [Execute Step] 状态详情: state.keys()={list(state.keys())}, reasoning_steps={reasoning_steps}")
                # 🚀 修复：尝试从其他位置恢复推理步骤
                if 'metadata' in state and 'reasoning_steps' in state.get('metadata', {}):
                    reasoning_steps = state['metadata']['reasoning_steps']
                    state['reasoning_steps'] = reasoning_steps
                    logger.info(f"✅ [Execute Step] 从 metadata 恢复推理步骤: {len(reasoning_steps)} 个步骤")
                else:
                    if 'errors' not in state:
                        state['errors'] = []
                    state['errors'].append({
                        'node': 'execute_step',
                        'error': error_msg,
                        'timestamp': time.time(),
                        'severity': 'warning'
                    })
                    return state
            
            if current_step_index >= len(reasoning_steps):
                error_msg = f"当前步骤索引 ({current_step_index}) 超出范围 (0-{len(reasoning_steps)-1})"
                logger.warning(f"⚠️ [Execute Step] {error_msg}")
                # 🚀 修复：如果索引超出范围，说明所有步骤已完成，应该进入合成阶段
                # 不设置错误，而是标记为完成
                logger.info(f"✅ [Execute Step] 所有步骤已完成，应该进入合成阶段")
                return state
            
            current_step = reasoning_steps[current_step_index]
            
            # 检查步骤依赖
            depends_on = current_step.get('depends_on', [])
            step_query = current_step.get('sub_query', '') or ''
            has_placeholder = (
                ('[步骤' in step_query) or
                ('[step' in step_query.lower()) or
                bool(re.search(r'\[result\s+from\s+step\s+\d+\]|\[result\s+from\s+previous\s+step\]|\[previous\s+step\s+result\]', step_query, re.IGNORECASE))
            )

            if has_placeholder and not depends_on:
                dep_index = None
                explicit_step_patterns = [
                    r'\[Result\s+from\s+Step\s+(\d+)\]',
                    r'\[result\s+from\s+step\s+(\d+)\]',
                    r'\[step\s+(\d+)\s+result\]',
                    r'\[步骤(\d+)的结果\]',
                ]
                for pattern in explicit_step_patterns:
                    match = re.search(pattern, step_query, re.IGNORECASE)
                    if match:
                        dep_index = int(match.group(1)) - 1
                        break

                if dep_index is None and re.search(r'\[result\s+from\s+previous\s+step\]|\[previous\s+step\s+result\]', step_query, re.IGNORECASE):
                    dep_index = current_step_index - 1

                if dep_index is None and current_step_index > 0:
                    dep_index = current_step_index - 1

                if dep_index is not None and dep_index >= 0:
                    current_step['depends_on'] = [f"step_{dep_index + 1}"]
                    depends_on = current_step['depends_on']

            if depends_on:
                for dep in depends_on:
                    dep_index = int(dep.replace('step_', '')) - 1 if isinstance(dep, str) and dep.startswith('step_') else dep - 1
                    if dep_index >= 0 and dep_index < len(state.get('step_answers', [])):
                        prev_answer = state['step_answers'][dep_index]
                        if has_placeholder and prev_answer:
                            step_query = current_step.get('sub_query', '') or ''
                            step_query = step_query.replace(f'[步骤{dep_index + 1}的结果]', prev_answer)
                            step_query = step_query.replace(f'[step {dep_index + 1} result]', prev_answer)
                            step_query = re.sub(r'\[Result\s+from\s+Step\s+' + str(dep_index + 1) + r'\]', prev_answer, step_query, flags=re.IGNORECASE)
                            step_query = re.sub(r'\[result\s+from\s+step\s+' + str(dep_index + 1) + r'\]', prev_answer, step_query, flags=re.IGNORECASE)
                            step_query = re.sub(r'\[step\s+' + str(dep_index + 1) + r'\s+result\]', prev_answer, step_query, flags=re.IGNORECASE)
                            step_query = re.sub(r'\[result\s+from\s+previous\s+step\]|\[previous\s+step\s+result\]', prev_answer, step_query, flags=re.IGNORECASE)
                            current_step['sub_query'] = step_query
            
            # 🚀 修复：确保 metadata 存在
            if 'metadata' not in state:
                state['metadata'] = {}
            
            # 更新当前步骤信息
            state['metadata']['current_step'] = current_step
            state['metadata']['current_step_index'] = current_step_index
            
            logger.debug(f"🔍 [Execute Step] 已设置 current_step: {current_step.get('sub_query', '')[:50]}...")
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['execute_step'] = execution_time
            state['node_times']['execute_step'] = execution_time
            
            logger.info(f"✅ [Execute Step] 步骤 {current_step_index + 1}/{len(reasoning_steps)} 准备就绪")
        
        except Exception as e:
            error_msg = f"执行推理步骤失败: {str(e)}"
            logger.error(f"❌ [Execute Step] {error_msg}", exc_info=True)
            state['error'] = error_msg
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'execute_step',
                'error': error_msg,
                'timestamp': time.time()
            })
        
        return state
    
    async def gather_evidence_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """收集证据节点
        
        为当前步骤收集相关证据
        """
        logger.info("🔍 [Gather Evidence] 开始收集证据")
        start_time = time.time()
        
        try:
            # 🚀 修复：确保 metadata 存在
            if 'metadata' not in state:
                state['metadata'] = {}
            
            current_step = state.get('metadata', {}).get('current_step')
            if not current_step:
                error_msg = "没有当前步骤信息"
                logger.warning(f"⚠️ [Gather Evidence] {error_msg}")
                logger.debug(f"🔍 [Gather Evidence] state keys: {list(state.keys())}")
                logger.debug(f"🔍 [Gather Evidence] metadata keys: {list(state.get('metadata', {}).keys())}")
                
                # 🚀 修复：尝试从 reasoning_steps 中恢复当前步骤
                reasoning_steps = state.get('reasoning_steps', [])
                current_step_index = state.get('current_step_index', 0)
                
                if reasoning_steps and 0 <= current_step_index < len(reasoning_steps):
                    current_step = reasoning_steps[current_step_index]
                    state['metadata']['current_step'] = current_step
                    logger.info(f"✅ [Gather Evidence] 从 reasoning_steps 恢复当前步骤")
                else:
                    # 如果无法恢复，记录错误但不阻止继续执行
                    if 'errors' not in state:
                        state['errors'] = []
                    state['errors'].append({
                        'node': 'gather_evidence',
                        'error': error_msg,
                        'timestamp': time.time(),
                        'severity': 'warning'  # 标记为警告级别
                    })
                    # 设置空证据，允许继续执行
                    state['metadata']['current_evidence'] = []
                    return state
            
            sub_query = current_step.get('sub_query', '')
            step_type = current_step.get('type', 'evidence_gathering')
            
            # 检查是否是答案合成步骤（不需要收集证据）
            if 'answer_synthesis' in step_type or 'synthesis' in step_type:
                logger.info("ℹ️ [Gather Evidence] 答案合成步骤，跳过证据收集")
                state['metadata']['current_evidence'] = []
                return state
            
            # 使用推理引擎收集证据
            if self.reasoning_engine and self.reasoning_engine.evidence_preprocessor:
                # 使用统一证据处理框架
                query_analysis = state.get('metadata', {}).get('query_analysis', {})
                context = state.get('context', {})
                
                evidence_result = await self.reasoning_engine.evidence_preprocessor.process_evidence_for_step(
                    sub_query=sub_query,
                    step=current_step,
                    context=context,
                    query_analysis=query_analysis,
                    previous_evidence=state.get('evidence', []),
                    format_type="structured"
                )
                
                evidence = evidence_result.evidence if evidence_result else []
                state['metadata']['current_evidence'] = evidence
                
                # 更新总证据列表
                if 'evidence' not in state:
                    state['evidence'] = []
                state['evidence'].extend(evidence)
            else:
                # 降级：使用系统知识检索
                if self.system:
                    try:
                        # 🚀 修复：execute_research 需要 ResearchRequest 对象，不是字符串
                        from src.unified_research_system import ResearchRequest
                        request = ResearchRequest(
                            query=sub_query,
                            context=state.get('context', {})
                        )
                        knowledge_result = await self.system.execute_research(request)
                        
                        # 提取证据（ResearchResult 对象）
                        if hasattr(knowledge_result, 'knowledge'):
                            evidence = knowledge_result.knowledge or []
                        elif isinstance(knowledge_result, dict):
                            evidence = knowledge_result.get('knowledge', [])
                        else:
                            evidence = []
                        
                        # 转换为统一的证据格式
                        formatted_evidence = []
                        for ev in evidence:
                            if isinstance(ev, dict):
                                formatted_evidence.append(ev)
                            else:
                                formatted_evidence.append({
                                    'content': str(ev) if ev else '',
                                    'source': getattr(ev, 'source', '') if hasattr(ev, 'source') else ''
                                })
                        
                        state['metadata']['current_evidence'] = formatted_evidence
                        if 'evidence' not in state:
                            state['evidence'] = []
                        state['evidence'].extend(formatted_evidence)
                        logger.info(f"✅ [Gather Evidence] 通过系统检索到 {len(formatted_evidence)} 条证据")
                    except Exception as e:
                        logger.warning(f"⚠️ [Gather Evidence] 系统知识检索失败: {e}", exc_info=True)
                        state['metadata']['current_evidence'] = []
                else:
                    logger.warning("⚠️ [Gather Evidence] 系统不可用，无法检索证据")
                    state['metadata']['current_evidence'] = []
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['gather_evidence'] = execution_time
            state['node_times']['gather_evidence'] = execution_time
            
            logger.info(f"✅ [Gather Evidence] 收集了 {len(state.get('metadata', {}).get('current_evidence', []))} 条证据 (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"收集证据失败: {str(e)}"
            logger.error(f"❌ [Gather Evidence] {error_msg}", exc_info=True)
            logger.debug(f"🔍 [Gather Evidence] 异常详情: {type(e).__name__}: {str(e)}")
            
            # 🚀 修复：确保 metadata 存在
            if 'metadata' not in state:
                state['metadata'] = {}
            
            # 🚀 修复：不要因为收集证据失败就设置全局错误，而是记录为警告
            # 可以尝试使用已有证据或跳过证据收集
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'gather_evidence',
                'error': error_msg,
                'timestamp': time.time(),
                'severity': 'warning'  # 标记为警告级别，不阻止继续执行
            })
            state['metadata']['current_evidence'] = []
            
            # 🚀 修复：只有在严重错误时才设置全局错误状态
            # 收集证据失败不应该阻止整个推理流程
            # 不设置 state['error']，允许继续执行
        
        return state
    
    async def extract_step_answer_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """提取步骤答案节点
        
        从证据中提取当前步骤的答案
        """
        logger.info("📤 [Extract Step Answer] 开始提取步骤答案")
        start_time = time.time()
        
        try:
            # 🚀 修复：确保 metadata 存在
            if 'metadata' not in state:
                state['metadata'] = {}
            
            current_step = state.get('metadata', {}).get('current_step')
            current_evidence = state.get('metadata', {}).get('current_evidence', [])
            
            if not current_step:
                error_msg = "没有当前步骤信息"
                logger.warning(f"⚠️ [Extract Step Answer] {error_msg}")
                logger.debug(f"🔍 [Extract Step Answer] state keys: {list(state.keys())}")
                logger.debug(f"🔍 [Extract Step Answer] metadata keys: {list(state.get('metadata', {}).keys())}")
                logger.debug(f"🔍 [Extract Step Answer] current_step_index: {state.get('current_step_index', 'N/A')}")
                logger.debug(f"🔍 [Extract Step Answer] reasoning_steps count: {len(state.get('reasoning_steps', []))}")
                
                # 🚀 修复：不要因为缺少步骤信息就设置全局错误，而是尝试从 reasoning_steps 中获取
                reasoning_steps = state.get('reasoning_steps', [])
                current_step_index = state.get('current_step_index', 0)
                
                if reasoning_steps and 0 <= current_step_index < len(reasoning_steps):
                    # 尝试从 reasoning_steps 中恢复当前步骤
                    current_step = reasoning_steps[current_step_index]
                    state['metadata']['current_step'] = current_step
                    logger.info(f"✅ [Extract Step Answer] 从 reasoning_steps 恢复当前步骤")
                else:
                    # 如果无法恢复，才设置错误（但不阻止继续执行）
                    if 'errors' not in state:
                        state['errors'] = []
                    state['errors'].append({
                        'node': 'extract_step_answer',
                        'error': error_msg,
                        'timestamp': time.time(),
                        'severity': 'warning'  # 标记为警告级别
                    })
                    # 🚀 修复：即使没有当前步骤，也尝试使用已有步骤答案
                    step_answers = state.get('step_answers', [])
                    if step_answers:
                        logger.info(f"ℹ️ [Extract Step Answer] 使用已有步骤答案作为降级方案")
                        return state
                    else:
                        return state
            
            sub_query = current_step.get('sub_query', '')
            step_type = current_step.get('type', 'evidence_gathering')
            
            # 检查是否是答案合成步骤
            if 'answer_synthesis' in step_type or 'synthesis' in step_type:
                # 合成前面步骤的答案
                step_answers = state.get('step_answers', [])
                depends_on = current_step.get('depends_on', [])
                
                if depends_on and step_answers:
                    # 收集依赖步骤的答案
                    dependent_answers = []
                    for dep in depends_on:
                        dep_index = int(dep.replace('step_', '')) - 1 if isinstance(dep, str) and dep.startswith('step_') else dep - 1
                        if 0 <= dep_index < len(step_answers):
                            dependent_answers.append(step_answers[dep_index])
                    
                    # 使用推理引擎合成答案
                    if self.reasoning_engine and self.reasoning_engine.answer_extractor:
                        answer_extractor = self.reasoning_engine.answer_extractor
                        
                        # 构建步骤信息（包含答案）
                        steps_with_answers = []
                        for i, ans in enumerate(dependent_answers):
                            dep_index = int(depends_on[i].replace('step_', '')) - 1 if isinstance(depends_on[i], str) and depends_on[i].startswith('step_') else depends_on[i] - 1
                            if 0 <= dep_index < len(state.get('reasoning_steps', [])):
                                step_info = state['reasoning_steps'][dep_index].copy()
                                step_info['answer'] = ans
                                steps_with_answers.append(step_info)
                        
                        # 使用 _synthesize_answer_from_steps 方法合成答案
                        synthesized_answer = answer_extractor._synthesize_answer_from_steps(
                            query=state.get('query', ''),
                            steps=steps_with_answers
                        )
                        
                        step_answer = synthesized_answer if synthesized_answer else "无法合成答案"
                    else:
                        # 降级：简单拼接
                        step_answer = " | ".join(dependent_answers) if dependent_answers else "无法合成答案"
                else:
                    step_answer = "无法合成答案（缺少依赖步骤答案）"
            else:
                # 从证据中提取答案
                if current_evidence and self.reasoning_engine and self.reasoning_engine.answer_extractor:
                    # 获取上一步答案
                    step_answers = state.get('step_answers', [])
                    previous_step_result = step_answers[-1] if step_answers else None
                    
                    # 提取答案
                    step_answer = self.reasoning_engine.answer_extractor.extract_step_result(
                        step_evidence=current_evidence,
                        step=current_step,
                        previous_step_result=previous_step_result,
                        original_query=state.get('query', ''),
                        sub_query=sub_query
                    )
                    
                    if not step_answer:
                        # 🚀 修复：如果提取失败，尝试从证据中直接提取内容
                        if current_evidence:
                            # 尝试从证据中提取内容
                            for ev in current_evidence:
                                if isinstance(ev, dict):
                                    content = ev.get('content', '')
                                    if content and content.strip():
                                        step_answer = content[:200]  # 限制长度
                                        logger.info(f"ℹ️ [Extract Step Answer] 从证据内容中提取答案: {step_answer[:100]}...")
                                        break
                                elif ev and str(ev).strip():
                                    step_answer = str(ev)[:200]
                                    logger.info(f"ℹ️ [Extract Step Answer] 从证据中提取答案: {step_answer[:100]}...")
                                    break
                        
                        if not step_answer:
                            step_answer = "无法从证据中提取答案"
                else:
                    # 降级：使用证据的第一条
                    if current_evidence:
                        first_evidence = current_evidence[0]
                        if isinstance(first_evidence, dict):
                            content = first_evidence.get('content', '')
                            if content and content.strip():
                                step_answer = content[:200]  # 限制长度
                            else:
                                step_answer = str(first_evidence)[:200]
                        else:
                            step_answer = str(first_evidence)[:200] if first_evidence else "无法从证据中提取答案"
                    else:
                        # 🚀 修复：如果没有证据，不设置占位符，而是返回 None，让后续节点处理
                        logger.warning(f"⚠️ [Extract Step Answer] 步骤 {current_step.get('sub_query', '')[:50]}... 没有可用证据")
                        step_answer = None  # 不设置占位符，让后续节点决定如何处理
            
            # 保存步骤答案（只保存有效答案，跳过 None）
            if 'step_answers' not in state:
                state['step_answers'] = []
            
            # 🚀 修复：如果 step_answer 是 None，不添加到 step_answers 中
            # 这样可以避免占位符污染步骤答案列表
            if step_answer is not None:
                state['step_answers'].append(step_answer)
            else:
                # 如果答案为空，记录警告但不阻止流程继续
                logger.warning(f"⚠️ [Extract Step Answer] 步骤答案为空，跳过添加到 step_answers")
            
            # 更新当前步骤索引
            current_step_index = state.get('current_step_index', 0)
            state['current_step_index'] = current_step_index + 1
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['extract_step_answer'] = execution_time
            state['node_times']['extract_step_answer'] = execution_time
            
            logger.info(f"✅ [Extract Step Answer] 提取答案: {step_answer[:100]}... (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"提取步骤答案失败: {str(e)}"
            logger.error(f"❌ [Extract Step Answer] {error_msg}", exc_info=True)
            logger.debug(f"🔍 [Extract Step Answer] 异常详情: {type(e).__name__}: {str(e)}")
            
            # 🚀 修复：不要因为提取答案失败就设置全局错误，而是记录为警告
            # 这样可以允许系统继续执行，尝试从其他步骤中获取答案
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'extract_step_answer',
                'error': error_msg,
                'timestamp': time.time(),
                'severity': 'warning'  # 标记为警告级别，不阻止继续执行
            })
            
            # 添加空答案以保持索引一致
            if 'step_answers' not in state:
                state['step_answers'] = []
            state['step_answers'].append("提取答案失败")
            state['current_step_index'] = state.get('current_step_index', 0) + 1
            
            # 🚀 修复：只有在严重错误时才设置全局错误状态
            # 提取答案失败不应该阻止整个推理流程
            # 不设置 state['error']，允许继续执行
        
        return state
    
    async def synthesize_answer_node(self, state: ResearchSystemState) -> ResearchSystemState:
        """合成最终答案节点
        
        将所有步骤答案合成为最终答案
        """
        logger.info("🎯 [Synthesize Answer] 开始合成最终答案")
        start_time = time.time()
        
        try:
            step_answers = state.get('step_answers', [])
            reasoning_steps = state.get('reasoning_steps', [])
            evidence = state.get('evidence', [])
            query = state.get('query', '')
            
            # 🚀 修复：检查 step_answers 是否为空或只包含占位符
            if not step_answers:
                # 尝试从 evidence 中提取答案
                logger.warning(f"⚠️ [Synthesize Answer] step_answers 为空，尝试从证据中提取答案")
                if evidence and self.reasoning_engine and self.reasoning_engine.answer_extractor:
                    try:
                        answer_extractor = self.reasoning_engine.answer_extractor
                        final_answer = await answer_extractor.derive_final_answer_with_ml(
                            query=query,
                            evidence=evidence,
                            steps=None
                        )
                        if final_answer:
                            state['final_answer'] = final_answer
                            state['answer'] = final_answer
                            logger.info(f"✅ [Synthesize Answer] 从证据中提取到最终答案")
                            return state
                    except Exception as e:
                        logger.warning(f"⚠️ [Synthesize Answer] 从证据提取答案失败: {e}")
                
                # 如果都失败，设置错误
                state['error'] = "没有步骤答案可合成，且无法从证据中提取答案"
                if 'errors' not in state:
                    state['errors'] = []
                state['errors'].append({
                    'node': 'synthesize_answer',
                    'error': state['error'],
                    'timestamp': time.time()
                })
                state['final_answer'] = "无法生成最终答案（没有步骤答案且无法从证据中提取）"
                return state
            
            # 🚀 修复：过滤无效的步骤答案（占位符）
            valid_step_answers = []
            valid_steps_with_answers = []
            invalid_markers = [
                "没有可用证据", "无法从证据中提取答案", "提取答案失败", 
                "无法合成答案", "无法生成最终答案", "No answer available from evidence"
            ]
            
            for i, step_answer in enumerate(step_answers):
                # 🚀 修复：将 ProcessedEvidence 对象转换为字符串
                if hasattr(step_answer, 'content'):
                    # 如果是 ProcessedEvidence 对象，提取 content
                    step_answer = str(step_answer.content) if step_answer.content else str(step_answer)
                elif not isinstance(step_answer, str):
                    # 如果是其他对象，转换为字符串
                    step_answer = str(step_answer)
                
                # 检查是否是有效答案（不是占位符）
                is_valid = (
                    step_answer and 
                    step_answer.strip() and 
                    not any(marker in step_answer for marker in invalid_markers)
                )
                
                if is_valid:
                    valid_step_answers.append(step_answer)
                    if i < len(reasoning_steps):
                        step_info = reasoning_steps[i].copy()
                        step_info['answer'] = step_answer
                        valid_steps_with_answers.append(step_info)
            
            # 🚀 修复：如果没有有效步骤答案，记录警告并尝试其他方法
            if not valid_step_answers:
                logger.warning(f"⚠️ [Synthesize Answer] 所有步骤答案都是占位符，尝试从证据中提取")
                # 尝试从证据中提取答案
                if evidence and self.reasoning_engine and self.reasoning_engine.answer_extractor:
                    try:
                        answer_extractor = self.reasoning_engine.answer_extractor
                        final_answer = await answer_extractor.derive_final_answer_with_ml(
                            query=query,
                            evidence=evidence,
                            steps=None  # 步骤答案无效，不使用步骤
                        )
                        if final_answer and final_answer not in invalid_markers:
                            state['final_answer'] = final_answer
                            state['answer'] = final_answer
                            logger.info(f"✅ [Synthesize Answer] 从证据中提取到最终答案")
                            return state
                    except Exception as e:
                        logger.warning(f"⚠️ [Synthesize Answer] 从证据提取答案失败: {e}")
                
                # 如果都失败，使用最后一个步骤答案（即使可能是占位符）
                final_answer = step_answers[-1] if step_answers else "无法生成最终答案"
                logger.warning(f"⚠️ [Synthesize Answer] 使用最后一个步骤答案（可能是占位符）: {final_answer}")
            else:
                # 使用推理引擎合成答案
                if self.reasoning_engine and self.reasoning_engine.answer_extractor:
                    answer_extractor = self.reasoning_engine.answer_extractor
                    
                    # 使用有效的步骤信息合成答案
                    final_answer = answer_extractor._synthesize_answer_from_steps(
                        query=query,
                        steps=valid_steps_with_answers
                    )
                    
                    if not final_answer:
                        # 降级：使用 derive_final_answer_with_ml 方法
                        try:
                            final_answer = await answer_extractor.derive_final_answer_with_ml(
                                query=query,
                                evidence=evidence,
                                steps=valid_steps_with_answers
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ [Synthesize Answer] derive_final_answer_with_ml 失败: {e}")
                            # 最终降级：使用最后一个有效步骤答案
                            final_answer = valid_step_answers[-1] if valid_step_answers else "无法生成最终答案"
                else:
                    # 降级：使用最后一个有效步骤答案或拼接所有有效答案
                    if len(valid_step_answers) == 1:
                        final_answer = valid_step_answers[0]
                    else:
                        final_answer = "\n".join([f"步骤{i+1}: {ans}" for i, ans in enumerate(valid_step_answers)])
            
            state['final_answer'] = final_answer
            state['answer'] = final_answer
            
            # 记录执行时间
            execution_time = time.time() - start_time
            # 🚀 修复：确保 node_execution_times 和 node_times 存在
            if 'node_execution_times' not in state:
                state['node_execution_times'] = {}
            if 'node_times' not in state:
                state['node_times'] = {}
            state['node_execution_times']['synthesize_answer'] = execution_time
            state['node_times']['synthesize_answer'] = execution_time
            
            logger.info(f"✅ [Synthesize Answer] 最终答案已生成 (耗时: {execution_time:.2f}s)")
        
        except Exception as e:
            error_msg = f"合成最终答案失败: {str(e)}"
            logger.error(f"❌ [Synthesize Answer] {error_msg}", exc_info=True)
            state['error'] = error_msg
            if 'errors' not in state:
                state['errors'] = []
            state['errors'].append({
                'node': 'synthesize_answer',
                'error': error_msg,
                'timestamp': time.time()
            })
            # 降级：使用最后一个步骤答案
            step_answers = state.get('step_answers', [])
            state['final_answer'] = step_answers[-1] if step_answers else "无法生成最终答案"
            state['answer'] = state['final_answer']
        
        return state
