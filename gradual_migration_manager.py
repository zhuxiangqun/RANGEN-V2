
# 渐进式迁移管理器
class GradualMigrationManager:
    """管理新旧系统间的渐进式迁移"""
    
    def __init__(self):
        self.migration_phase = "phase_2"  # 当前迁移阶段
        self.feature_flags = {
            'orchestrator_query_analysis': True,
            'dynamic_knowledge_retrieval': True,
            'smart_prompt_enhancement': True,
            'adaptive_quality_validation': True,
            'legacy_fallback_mode': True,  # 保持向后兼容
            'enhanced_error_handling': False,  # 下一阶段启用
            'performance_monitoring': False,  # 下一阶段启用
        }
        self.migration_metrics = {
            'total_requests': 0,
            'orchestrator_success_rate': 0.0,
            'fallback_usage_rate': 0.0,
            'error_rate': 0.0,
            'performance_improvement': 0.0
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """检查功能是否启用"""
        return self.feature_flags.get(feature_name, False)
    
    def should_use_orchestrator(self, query_complexity: str) -> bool:
        """决定是否使用推理编排器"""
        if not self.is_feature_enabled('orchestrator_query_analysis'):
            return False
        
        # 根据查询复杂度决定
        complex_queries = ['complex', 'high']
        return query_complexity in complex_queries
    
    def update_metrics(self, request_result: dict):
        """更新迁移指标"""
        self.migration_metrics['total_requests'] += 1
        
        if request_result.get('used_orchestrator', False):
            if request_result.get('orchestrator_success', False):
                self.migration_metrics['orchestrator_success_rate'] = (
                    (self.migration_metrics['orchestrator_success_rate'] * (self.migration_metrics['total_requests'] - 1)) + 1
                ) / self.migration_metrics['total_requests']
        
        if request_result.get('used_fallback', False):
            self.migration_metrics['fallback_usage_rate'] = (
                (self.migration_metrics['fallback_usage_rate'] * (self.migration_metrics['total_requests'] - 1)) + 1
            ) / self.migration_metrics['total_requests']
    
    def get_migration_status(self) -> dict:
        """获取迁移状态"""
        return {
            'current_phase': self.migration_phase,
            'feature_flags': self.feature_flags,
            'metrics': self.migration_metrics,
            'ready_for_next_phase': self._check_next_phase_readiness()
        }
    
    def _check_next_phase_readiness(self) -> bool:
        """检查是否准备好进入下一阶段"""
        if self.migration_phase == "phase_2":
            # Phase 2 -> Phase 3 的条件
            return (
                self.migration_metrics['orchestrator_success_rate'] > 0.95 and
                self.migration_metrics['fallback_usage_rate'] < 0.05 and
                self.migration_metrics['error_rate'] < 0.01
            )
        elif self.migration_phase == "phase_3":
            # Phase 3 -> Phase 4 的条件
            return (
                self.migration_metrics['performance_improvement'] > 0.20 and  # 性能提升20%
                self.migration_metrics['error_rate'] < 0.005  # 错误率低于0.5%
            )
        return False
    
    def can_rollback(self) -> bool:
        """检查是否可以回滚"""
        # 如果错误率突然上升，允许回滚
        return self.migration_metrics['error_rate'] > 0.10
