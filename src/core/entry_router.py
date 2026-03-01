#!/usr/bin/env python3
"""
入口路由器 - 轻量级快速决策
按照架构文档实现独立的路由组件
"""

import logging
import time
import sys
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EntryRouter:
    """入口路由器 - 轻量级快速决策
    
    职责：
    1. 快速复杂度分析（基于规则/轻量模型）
    2. 系统状态检查
    3. 快速路由决策（不涉及复杂推理）
    
    特点：
    - 轻量级：基于规则 + 轻量模型，毫秒级响应
    - 不阻塞：简单任务不走复杂路径
    - 可扩展：可逐步加入ML优化
    """
    
    def __init__(self, complexity_predictor=None, resource_checker=None, use_langgraph=False, use_unified_workflow=False):
        """初始化入口路由器
        
        Args:
            complexity_predictor: 可选的ML复杂度预测器（已废弃，使用统一服务）
            resource_checker: 可选的资源检查器（用于检查MAS等资源是否可用）
            use_langgraph: 是否启用 LangGraph（如果启用，优先使用 react_agent 路径）
            use_unified_workflow: 是否启用统一工作流（如果启用，优先使用统一工作流）
        """
        # 🚀 改进：使用统一复杂度判断服务（支持LLM判断）
        self._complexity_service = None
        try:
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            self._complexity_service = get_unified_complexity_model_service()
            self.logger = logging.getLogger(__name__)
            self.logger.info("✅ Entry Router: 统一复杂度判断服务已初始化（支持LLM判断）")
        except Exception as e:
            self.logger.warning(f"⚠️ Entry Router: 统一复杂度判断服务初始化失败: {e}，将使用fallback")
            self._complexity_service = None
        
        # 保留resource_checker用于资源检查
        self.resource_checker = resource_checker  # 用于检查资源可用性的回调函数
        self.logger = logging.getLogger(__name__)
        
        # 🚀 新增：LangGraph 支持
        self.use_langgraph = use_langgraph
        if self.use_langgraph:
            self.logger.info("✅ Entry Router: LangGraph 已启用，将优先使用 react_agent 路径")
        
        # 🌐 新增：统一工作流支持
        self.use_unified_workflow = use_unified_workflow
        if self.use_unified_workflow:
            self.logger.info("✅ Entry Router: 统一工作流已启用，将优先使用统一工作流路径")
        
        # 路由决策统计
        self._routing_stats = {
            'total_routes': 0,
            'standard_loop_routes': 0,
            'mas_routes': 0,
            'react_routes': 0,
            'traditional_routes': 0
        }
    
    async def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """路由决策 - 毫秒级响应
        
        根据架构文档，路由决策逻辑：
        1. 快速复杂度分析
        2. 系统状态检查
        3. 快速决策（不涉及复杂推理）
        
        Args:
            query: 用户查询
            context: 上下文信息（可选）
            
        Returns:
            路由路径：'standard_loop', 'mas', 'react_agent', 'traditional'
        """
        start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info("🚦 [Entry Router] 开始路由决策")
        self.logger.info(f"📝 [Entry Router] 查询: {query[:100]}...")
        sys.stdout.write(f"🚦 [DEBUG] [Entry Router] 开始路由决策: {query[:50]}...\n")
        sys.stdout.flush()
        
        # 1. 快速复杂度分析（使用统一服务，支持LLM判断）
        complexity_result = None
        complexity = "medium"  # 默认值
        needs_reasoning_chain = False
        
        if self._complexity_service and not self.use_unified_workflow:
            try:
                import asyncio
                self.logger.info("🔍 [Entry Router] 开始复杂度分析...")
                sys.stdout.write("🔍 [DEBUG] [Entry Router] 开始复杂度分析...\n")
                sys.stdout.flush()
                complexity_timeout = 30.0
                complexity_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._complexity_service.assess_complexity,
                        query=query,
                        query_type=None,
                        evidence_count=0,
                        use_cache=True
                    ),
                    timeout=complexity_timeout
                )
                complexity = complexity_result.level.value
                needs_reasoning_chain = complexity_result.needs_reasoning_chain
                self.logger.info(f"📊 [Entry Router] 复杂度分析结果: {complexity} (需要推理链: {needs_reasoning_chain})")
                sys.stdout.write(f"📊 [DEBUG] [Entry Router] 复杂度分析结果: {complexity}\n")
                sys.stdout.flush()
            except asyncio.TimeoutError:
                self.logger.warning("⚠️ [Entry Router] 复杂度判断超时，使用fallback")
                sys.stdout.write("⚠️ [DEBUG] [Entry Router] 复杂度判断超时，使用fallback\n")
                sys.stdout.flush()
                complexity = self._quick_analyze(query)  # Fallback
            except Exception as e:
                self.logger.warning(f"⚠️ [Entry Router] 复杂度判断失败: {e}，使用fallback")
                sys.stdout.write(f"⚠️ [DEBUG] [Entry Router] 复杂度判断失败: {e}，使用fallback\n")
                sys.stdout.flush()
                complexity = self._quick_analyze(query)  # Fallback
        else:
            self.logger.info("🔍 [Entry Router] 复杂度服务不可用，使用快速分析")
            sys.stdout.write("🔍 [DEBUG] [Entry Router] 复杂度服务不可用，使用快速分析\n")
            sys.stdout.flush()
            complexity = self._quick_analyze(query)  # Fallback
        
        # 2. 系统状态检查
        system_state = self._check_system_state()
        load = system_state.get("load", 0)
        mas_healthy = system_state.get("mas_healthy", False)
        self.logger.info(f"💻 [Entry Router] 系统状态: load={load:.1f}%, mas_healthy={mas_healthy}")
        
        # 3. 快速决策（不涉及复杂推理）
        route_path = None
        
        # 🌐 新增：如果启用了统一工作流，优先使用统一工作流路径
        if self.use_unified_workflow:
            route_path = "react_agent"  # 使用统一工作流（通过 react_agent 路径）
            self.logger.info(f"✅ [Entry Router] 路由决策: 统一工作流 (MVP)")
            self.logger.info(f"   📌 决策理由: 统一工作流已启用，使用统一工作流执行")
        # 🚀 新增：如果启用了 LangGraph，优先使用 react_agent 路径
        elif self.use_langgraph:
            route_path = "react_agent"  # 使用 LangGraph ReAct Agent
            self.logger.info(f"✅ [Entry Router] 路由决策: ReAct Agent (LangGraph)")
            self.logger.info(f"   📌 决策理由: LangGraph 已启用，使用 LangGraph ReAct Agent")
        elif complexity == "simple" or load > 80:
            route_path = "standard_loop"  # 快速路径
            self.logger.info(f"✅ [Entry Router] 路由决策: Standard Loop (快速路径)")
            self.logger.info(f"   📌 决策理由: 简单任务（复杂度={complexity}）或系统负载高（{load:.1f}%）")
        elif needs_reasoning_chain or complexity == "complex":
            # 🚀 改进：如果需要推理链或复杂度是complex，优先考虑ReAct Agent
            # 但如果MAS可用且任务可并行化，也可以使用MAS
            if mas_healthy and complexity == "complex" and not needs_reasoning_chain:
                # 复杂但不需要深度推理链的任务，可以使用MAS并行处理
                route_path = "mas"  # 并行处理
                self.logger.info(f"✅ [Entry Router] 路由决策: MAS (并行处理)")
                self.logger.info(f"   📌 决策理由: 复杂任务（复杂度={complexity}）且MAS可用，可并行处理")
            else:
                # 需要深度推理链的任务，使用ReAct Agent
                route_path = "react_agent"  # 深度推理
                self.logger.info(f"✅ [Entry Router] 路由决策: ReAct Agent (深度推理)")
                self.logger.info(f"   📌 决策理由: 需要推理链（needs_reasoning_chain={needs_reasoning_chain}）或复杂度={complexity}")
        elif complexity == "medium" and mas_healthy:
            route_path = "mas"  # 并行处理
            self.logger.info(f"✅ [Entry Router] 路由决策: MAS (并行处理)")
            self.logger.info(f"   📌 决策理由: 中等复杂度（复杂度={complexity}）且MAS可用")
        else:
            route_path = "traditional"  # 保守选择
            self.logger.info(f"✅ [Entry Router] 路由决策: Traditional Flow (保守路径)")
            self.logger.info(f"   📌 决策理由: 默认保守方案，确保稳定性")
        
        routing_time = time.time() - start_time
        self.logger.info(f"⏱️ [Entry Router] 路由决策完成，耗时: {routing_time:.3f}秒")
        self.logger.info("=" * 60)
        
        # 更新统计
        self._routing_stats['total_routes'] += 1
        if route_path == "standard_loop":
            self._routing_stats['standard_loop_routes'] += 1
        elif route_path == "mas":
            self._routing_stats['mas_routes'] += 1
        elif route_path == "react_agent":
            self._routing_stats['react_routes'] += 1
        elif route_path == "traditional":
            self._routing_stats['traditional_routes'] += 1
        
        return route_path
    
    def _quick_analyze(self, query: str) -> str:
        """快速复杂度分析
        
        🚀 改进：使用统一复杂度判断服务（优先LLM判断），避免重复实现
        
        Args:
            query: 用户查询
            
        Returns:
            复杂度级别：'simple', 'medium', 'complex'
        """
        # 🚀 优先使用统一复杂度判断服务（支持LLM判断）
        if self._complexity_service:
            try:
                start_time = time.time()
                complexity_result = self._complexity_service.assess_complexity(
                    query=query,
                    query_type=None,
                    evidence_count=0,
                    use_cache=True
                )
                execution_time = time.time() - start_time
                
                complexity = complexity_result.level.value
                score = complexity_result.score
                llm_judgment = complexity_result.llm_judgment
                
                if llm_judgment:
                    self.logger.info(f"✅ [Entry Router] LLM复杂度判断: {complexity} (评分: {score:.2f}, 耗时: {execution_time:.3f}秒)")
                    self.logger.debug(f"   LLM判断详情: {llm_judgment[:100]}")
                else:
                    self.logger.info(f"✅ [Entry Router] 规则复杂度判断: {complexity} (评分: {score:.2f}, 耗时: {execution_time:.3f}秒)")
                
                return complexity
            except Exception as e:
                self.logger.warning(f"⚠️ [Entry Router] 统一复杂度判断服务失败: {e}，使用fallback")
        
        # Fallback: 简单规则判断（仅在统一服务不可用时使用）
        return self._analyze_complexity_fallback(query)
    
    def _analyze_complexity_fallback(self, query: str) -> str:
        """Fallback复杂度判断（仅在统一服务不可用时使用）
        
        简单的规则判断，作为统一服务的fallback
        
        Args:
            query: 用户查询
            
        Returns:
            复杂度级别：'simple', 'medium', 'complex'
        """
        query_lower = query.lower()
        words = query.split()
        word_count = len(words)
        char_count = len(query)
        
        # 特征提取（参考ComplexityPredictor的特征提取逻辑）
        features = {
            # 基础特征
            'word_count': word_count,
            'char_count': char_count,
            'possessive_count': query.count("'s "),  # 所有格数量（多跳关系）
            'question_marks': query.count("?"),
            
            # 结构特征
            'conjunction_count': query.count(" and ") + query.count(" or ") + query.count(" but "),
            'conditional_count': query.count(" if ") + query.count(" when ") + query.count(" whether "),
            'comparison_count': query.count(" than ") + query.count(" compared ") + query.count(" vs "),
            
            # 关系特征（多跳查询）
            'relation_indicators': sum(1 for word in ['mother', 'father', 'wife', 'husband', 'son', 'daughter', 
                                                      'brother', 'sister', 'parent', 'child', 'spouse'] 
                                      if word in query_lower),
            'nested_relations': query.count("'s ") + query.count(" of "),
            
            # 查询类型特征
            'wh_questions': sum(1 for word in ['who', 'what', 'when', 'where', 'why', 'how'] 
                               if word in query_lower),
            'multiple_questions': query.count("?") > 1,
            
            # 🚀 简化：移除复杂操作特征检测（统一服务已能判断）
            # 这些特征检测方法仍然保留作为fallback，但不再在fallback复杂度判断中使用
        }
        
        # 复杂度评分
        complexity_score = 0
        
        # 简单任务特征（低分）
        if word_count < 8 and features['possessive_count'] == 0 and features['conjunction_count'] == 0:
            complexity_score += 1
        if features['wh_questions'] == 1 and features['relation_indicators'] == 0:
            complexity_score += 1
        
        # 中等复杂度特征（中分）
        if 8 <= word_count <= 25:
            complexity_score += 2
        if features['possessive_count'] == 1 or features['relation_indicators'] == 1:
            complexity_score += 2
        if features['conjunction_count'] == 1:
            complexity_score += 2
        
        # 复杂任务特征（高分）
        if word_count > 25:
            complexity_score += 4
        if features['possessive_count'] >= 2:  # 多跳关系
            complexity_score += 4
        if features['nested_relations'] >= 3:  # 深度嵌套
            complexity_score += 4
        if features['conjunction_count'] >= 2:  # 多个子任务
            complexity_score += 4
        if features['multiple_questions']:  # 多个问题
            complexity_score += 3
        # 🚀 移除：不再使用复杂操作特征检测（统一服务已能判断）
        # 这些方法（_detect_analysis_pattern等）已不再需要
        
        # 根据评分判断复杂度
        if complexity_score <= 2:
            return "simple"
        elif complexity_score <= 6:
            return "medium"
        else:
            return "complex"
    
    # 🚀 移除：_detect_analysis_pattern、_detect_comparison_pattern、_detect_synthesis_pattern 这些方法已不再需要
    # 
    # 原因：
    # 1. 统一复杂度判断服务已经能够判断查询是否需要分析、比较或综合
    # 2. 这些方法使用大量硬编码关键词，不符合通用性原则
    # 3. 统一服务使用LLM判断，比关键词列表更准确、更通用
    # 4. 这些方法原本用于fallback复杂度判断，但现在统一服务优先使用，fallback很少触发
    # 
    # 如果将来需要，应该：
    # - 使用LLM进行模式检测，而非硬编码关键词
    # - 或者完全依赖统一服务的判断结果
    
    def _check_system_state(self) -> Dict[str, Any]:
        """检查系统状态
        
        Returns:
            系统状态字典，包含：
            - load: 系统负载（0-100）
            - mas_healthy: MAS是否健康
            - tools_available: 工具是否可用
            - standard_loop_available: 标准循环是否可用
            - traditional_available: 传统流程是否可用
        """
        # 使用resource_checker检查资源可用性（如果提供）
        mas_healthy = True
        if self.resource_checker:
            try:
                mas_healthy = self.resource_checker('mas')
            except Exception as e:
                self.logger.debug(f"⚠️ [Entry Router] 资源检查失败: {e}，使用默认值")
        
        return {
            "load": self._get_system_load(),
            "mas_healthy": mas_healthy,
            "tools_available": True,  # 默认假设工具可用
            "standard_loop_available": True,  # 默认假设标准循环可用
            "traditional_available": True  # 默认假设传统流程可用
        }
    
    def _get_system_load(self) -> float:
        """获取系统负载
        
        Returns:
            系统负载（0-100）
        """
        try:
            import psutil
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 综合负载（取CPU和内存的最大值）
            load = max(cpu_percent, memory_percent)
            return load
        except Exception as e:
            self.logger.warning(f"⚠️ [Entry Router] 获取系统负载失败: {e}")
            return 50.0  # 默认中等负载
    
    # 🚀 移除：不再需要深度推理判断方法
    # 统一复杂度判断服务已经能够判断needs_reasoning_chain，不需要单独的方法
    # 路由决策直接使用complexity_result.needs_reasoning_chain即可
    # 
    # 原因：
    # 1. 统一服务使用LLM判断，比关键词列表更准确、更通用
    # 2. 避免重复实现，减少维护成本
    # 3. 统一服务已经能够区分simple/medium/complex，并判断是否需要推理链
    # 4. 如果统一服务不可用，fallback的复杂度判断已经足够
    
    def update_system_state(self, state: Dict[str, Any]):
        """更新系统状态（供外部调用）
        
        Args:
            state: 系统状态字典
        """
        # 可以用于更新系统状态，例如MAS健康状态
        pass
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息
        
        Returns:
            路由统计字典
        """
        return self._routing_stats.copy()
