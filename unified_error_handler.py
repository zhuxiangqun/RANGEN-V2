
# 统一错误处理系统
class UnifiedErrorHandler:
    """统一处理推理过程中的各种错误"""
    
    # 错误类型定义
    ERROR_TYPES = {
        'schema_validation': 'Schema验证失败',
        'llm_call': 'LLM调用失败',
        'parsing': '响应解析失败',
        'orchestrator': '推理编排器失败',
        'compatibility': '兼容性转换失败',
        'validation': '步骤验证失败',
        'timeout': '处理超时',
        'unknown': '未知错误'
    }
    
    # 错误严重程度
    ERROR_SEVERITY = {
        'low': 1,      # 可以重试
        'medium': 2,   # 需要降级处理
        'high': 3,     # 严重错误，需要回退
        'critical': 4  # 系统错误，需要停止
    }
    
    def __init__(self):
        self.error_history = []
        self.recovery_strategies = {
            'schema_validation': self._recover_schema_validation,
            'llm_call': self._recover_llm_call,
            'parsing': self._recover_parsing,
            'orchestrator': self._recover_orchestrator,
            'compatibility': self._recover_compatibility,
            'validation': self._recover_validation,
            'timeout': self._recover_timeout,
            'unknown': self._recover_unknown
        }
    
    def handle_error(self, error_type: str, error_details: dict, context: dict) -> dict:
        """处理错误并返回恢复策略"""
        error_info = {
            'type': error_type,
            'severity': self._classify_severity(error_type, error_details),
            'details': error_details,
            'context': context,
            'timestamp': self._get_timestamp(),
            'recovery_strategy': None,
            'should_retry': False,
            'should_fallback': False,
            'diagnostic_info': self._generate_diagnostic_info(error_type, error_details)
        }
        
        # 记录错误历史
        self.error_history.append(error_info)
        
        # 应用恢复策略
        if error_type in self.recovery_strategies:
            recovery_result = self.recovery_strategies[error_type](error_details, context)
            error_info.update(recovery_result)
        
        return error_info
    
    def _classify_severity(self, error_type: str, error_details: dict) -> str:
        """根据错误类型和详情分类严重程度"""
        if error_type in ['llm_call', 'timeout']:
            # LLM调用失败可能是临时的
            return 'medium'
        elif error_type in ['schema_validation', 'parsing']:
            # 格式问题通常可以重试或修复
            return 'low'
        elif error_type in ['orchestrator', 'compatibility']:
            # 系统架构问题，需要降级
            return 'high'
        elif error_type == 'validation':
            # 验证失败取决于具体情况
            if 'required field' in str(error_details):
                return 'low'
            else:
                return 'medium'
        else:
            return 'high'
    
    def _recover_schema_validation(self, error_details: dict, context: dict) -> dict:
        """恢复Schema验证失败"""
        return {
            'recovery_strategy': 'fix_schema',
            'should_retry': True,
            'max_retries': 2,
            'fallback_action': 'use_legacy_schema'
        }
    
    def _recover_llm_call(self, error_details: dict, context: dict) -> dict:
        """恢复LLM调用失败"""
        return {
            'recovery_strategy': 'switch_model',
            'should_retry': True,
            'max_retries': 3,
            'fallback_action': 'use_mock_response'
        }
    
    def _recover_parsing(self, error_details: dict, context: dict) -> dict:
        """恢复解析失败"""
        return {
            'recovery_strategy': 'robust_parsing',
            'should_retry': True,
            'max_retries': 2,
            'fallback_action': 'generate_fallback_steps'
        }
    
    def _recover_orchestrator(self, error_details: dict, context: dict) -> dict:
        """恢复推理编排器失败"""
        return {
            'recovery_strategy': 'disable_orchestrator',
            'should_fallback': True,
            'fallback_action': 'use_legacy_generation'
        }
    
    def _recover_compatibility(self, error_details: dict, context: dict) -> dict:
        """恢复兼容性转换失败"""
        return {
            'recovery_strategy': 'use_legacy_types',
            'should_fallback': True,
            'fallback_action': 'convert_to_legacy_format'
        }
    
    def _recover_validation(self, error_details: dict, context: dict) -> dict:
        """恢复验证失败"""
        if 'sub_query' in str(error_details):
            return {
                'recovery_strategy': 'add_missing_fields',
                'should_retry': True,
                'fallback_action': 'generate_minimal_steps'
            }
        else:
            return {
                'recovery_strategy': 'relax_validation',
                'should_fallback': True,
                'fallback_action': 'use_legacy_validation'
            }
    
    def _recover_timeout(self, error_details: dict, context: dict) -> dict:
        """恢复超时错误"""
        return {
            'recovery_strategy': 'reduce_complexity',
            'should_fallback': True,
            'fallback_action': 'generate_simple_steps'
        }
    
    def _recover_unknown(self, error_details: dict, context: dict) -> dict:
        """恢复未知错误"""
        return {
            'recovery_strategy': 'safe_fallback',
            'should_fallback': True,
            'fallback_action': 'use_most_basic_mode'
        }
    
    def _generate_diagnostic_info(self, error_type: str, error_details: dict) -> dict:
        """生成诊断信息"""
        return {
            'error_category': self.ERROR_TYPES.get(error_type, '未知错误'),
            'possible_causes': self._identify_possible_causes(error_type, error_details),
            'recommended_actions': self._suggest_actions(error_type, error_details),
            'error_pattern': self._detect_error_pattern(error_type)
        }
    
    def _identify_possible_causes(self, error_type: str, error_details: dict) -> list:
        """识别可能的错误原因"""
        causes = {
            'schema_validation': ['LLM输出格式不符合Schema', 'Schema定义过严', '类型枚举不匹配'],
            'llm_call': ['API密钥问题', '网络连接失败', '模型服务不可用', '请求频率限制'],
            'parsing': ['LLM输出格式异常', 'JSON格式错误', '响应截断'],
            'orchestrator': ['组件初始化失败', '配置问题', '依赖缺失'],
            'compatibility': ['类型映射错误', '数据格式不兼容', '版本不匹配'],
            'validation': ['必需字段缺失', '数据类型错误', '业务规则违反'],
            'timeout': ['处理时间过长', '死锁', '资源耗尽'],
            'unknown': ['未预期的异常', '系统内部错误']
        }
        return causes.get(error_type, ['未知原因'])
    
    def _suggest_actions(self, error_type: str, error_details: dict) -> list:
        """建议的处理动作"""
        actions = {
            'schema_validation': ['检查Schema定义', '更新类型枚举', '放松验证规则'],
            'llm_call': ['检查API配置', '重试请求', '切换备用模型'],
            'parsing': ['改进解析逻辑', '添加错误容忍', '使用备用解析器'],
            'orchestrator': ['检查组件状态', '重新初始化', '降级到基础模式'],
            'compatibility': ['更新类型映射', '添加兼容性检查', '使用旧版接口'],
            'validation': ['补充缺失字段', '修复数据格式', '调整验证规则'],
            'timeout': ['增加超时时间', '优化处理逻辑', '减少并发'],
            'unknown': ['记录详细信息', '联系技术支持', '使用安全模式']
        }
        return actions.get(error_type, ['记录错误日志'])
    
    def _detect_error_pattern(self, error_type: str) -> str:
        """检测错误模式"""
        recent_errors = [e for e in self.error_history[-10:] if e['type'] == error_type]
        if len(recent_errors) >= 3:
            return 'recurring'
        elif len(recent_errors) >= 1:
            return 'occasional'
        else:
            return 'isolated'
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_error_summary(self) -> dict:
        """获取错误摘要"""
        total_errors = len(self.error_history)
        if total_errors == 0:
            return {'total_errors': 0, 'error_rate': 0.0}
        
        error_counts = {}
        for error in self.error_history:
            error_type = error['type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        most_common_error = max(error_counts.items(), key=lambda x: x[1])
        
        return {
            'total_errors': total_errors,
            'error_rate': total_errors / max(1, len(set(e['context'].get('query', '') for e in self.error_history))),
            'most_common_error': most_common_error,
            'error_distribution': error_counts
        }
