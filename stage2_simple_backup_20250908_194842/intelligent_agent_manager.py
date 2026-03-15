#!/usr/bin/env python3
"""智能体管理模块 - 从UnifiedIntelligentCenter中分离出来"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformance:
    """智能体性能记录"""
    total_calls: int = 0
    successful_calls: int = 0
    total_time: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    average_time: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
    success_rate: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))


class IntelligentAgentManager:
    """智能体管理器"""
    
    def __init__(self, config_center):
        self.config_center = config_center
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.agent_workflows: Dict[str, List[str]] = {}
    
    def record_agent_performance(self, agent_name: str, execution_time: float, success: bool):
        """记录智能体性能"""
        try:
            if agent_name not in self.agent_performance:
                self.agent_performance[agent_name] = AgentPerformance()

            perf = self.agent_performance[agent_name]
            perf.total_calls += 1
            perf.total_time += execution_time
            perf.average_time = perf.total_time / perf.total_calls

            if success:
                perf.successful_calls += 1

            perf.success_rate = perf.successful_calls / perf.total_calls
            
        except Exception as e:
            logger.warning("记录智能体性能失败: %s", e)
    
    def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformance]:
        """获取智能体性能"""
        return self.agent_performance.get(agent_name)
    
    def get_all_agent_performance(self) -> Dict[str, AgentPerformance]:
        """获取所有智能体性能"""
        return self.agent_performance.copy()
    
    def reset_agent_performance(self, agent_name: Optional[str] = None):
        """重置智能体性能"""
        try:
            if agent_name:
                if agent_name in self.agent_performance:
                    del self.agent_performance[agent_name]
            else:
                self.agent_performance.clear()
        except Exception as e:
            logger.warning("重置智能体性能失败: %s", e)
    
    def create_workflow(self, workflow_name: str, agent_sequence: List[str]) -> bool:
        """创建工作流"""
        try:
            self.agent_workflows[workflow_name] = agent_sequence.copy()
            return True
        except Exception as e:
            logger.warning("创建工作流失败: %s", e)
            return False
    
    def get_workflow(self, workflow_name: str) -> Optional[List[str]]:
        """获取工作流"""
        return self.agent_workflows.get(workflow_name)
    
    def execute_workflow(self, workflow_name: str, context: Dict[str, Any], 
                        integration_center) -> Dict[str, Any]:
        """执行工作流"""
        try:
            workflow = self.get_workflow(workflow_name)
            if not workflow:
                return {'success': False, 'error': f'工作流 {workflow_name} 不存在'}
            
            results = []
            for agent_name in workflow:
                agent = integration_center.get_agent(agent_name) if integration_center else None
                if agent:
                    start_time = time.time()
                    try:
                        # 执行智能体
                        if hasattr(agent, 'process_query'):
                            result = agent.process_query(context.get('query', ''), context)
                        elif hasattr(agent, 'execute'):
                            result = agent.execute(context)
                        else:
                            result = {'success': False, 'error': '智能体方法不支持'}
                        
                        execution_time = time.time() - start_time
                        self.record_agent_performance(agent_name, execution_time, result.get('success', False))
                        results.append({
                            'agent': agent_name,
                            'result': result,
                            'execution_time': execution_time
                        })
                    except Exception as e:
                        execution_time = time.time() - start_time
                        self.record_agent_performance(agent_name, execution_time, False)
                        results.append({
                            'agent': agent_name,
                            'result': {'success': False, 'error': str(e)},
                            'execution_time': execution_time
                        })
                else:
                    results.append({
                        'agent': agent_name,
                        'result': {'success': False, 'error': '智能体不存在'},
                        'execution_time': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
                    })
            
            return {
                'success': True,
                'workflow': workflow_name,
                'results': results,
                'total_agents': len(workflow),
                'successful_agents': sum(1 for r in results if r['result'].get('success', False))
            }
            
        except Exception as e:
            logger.error("执行工作流失败: %s", e)
            return {'success': False, 'error': str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            if not self.agent_performance:
                return {'total_agents': 0, 'summary': '无性能数据'}
            
            total_agents = len(self.agent_performance)
            total_calls = sum(perf.total_calls for perf in self.agent_performance.values())
            total_successful = sum(perf.successful_calls for perf in self.agent_performance.values())
            total_time = sum(perf.total_time for perf in self.agent_performance.values())
            
            overall_success_rate = total_successful / total_calls if total_calls > 0 else 0
            overall_avg_time = total_time / total_calls if total_calls > 0 else 0
            
            return {
                'total_agents': total_agents,
                'total_calls': total_calls,
                'total_successful_calls': total_successful,
                'overall_success_rate': overall_success_rate,
                'overall_average_time': overall_avg_time,
                'agent_details': {
                    name: {
                        'total_calls': perf.total_calls,
                        'success_rate': perf.success_rate,
                        'average_time': perf.average_time
                    } for name, perf in self.agent_performance.items()
                }
            }
            
        except Exception as e:
            logger.warning("获取性能摘要失败: %s", e)
            return {'error': str(e)}
    
    def optimize_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """优化工作流"""
        try:
            workflow = self.get_workflow(workflow_name)
            if not workflow:
                return {'success': False, 'error': f'工作流 {workflow_name} 不存在'}
            
            # 基于性能数据优化工作流顺序
            agent_performances = []
            for agent_name in workflow:
                perf = self.get_agent_performance(agent_name)
                if perf:
                    # 计算综合评分（成功率 * 速度）
                    score = perf.success_rate * (get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")) / max(perf.average_time, 0.001))
                    agent_performances.append((agent_name, score))
                else:
                    agent_performances.append((agent_name, 0.config.DEFAULT_TOP_K))
            
            # 按评分排序
            agent_performances.sort(key=lambda x: x[1], reverse=True)
            optimized_sequence = [name for name, _ in agent_performances]
            
            # 更新工作流
            self.agent_workflows[workflow_name] = optimized_sequence
            
            return {
                'success': True,
                'original_sequence': workflow,
                'optimized_sequence': optimized_sequence,
                'optimization_reason': '基于性能数据重新排序'
            }
            
        except Exception as e:
            logger.warning("优化工作流失败: %s", e)
            return {'success': False, 'error': str(e)}
