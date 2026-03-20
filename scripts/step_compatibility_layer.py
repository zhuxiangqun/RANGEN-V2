
# 数据模型兼容性层 - 统一新旧系统的数据格式
class StepTypeCompatibilityLayer:
    """处理新旧系统之间的步骤类型转换"""
    
    # 新旧系统步骤类型映射
    TYPE_MAPPING = {
        # 新系统 -> 旧系统（向下兼容）
        'information_retrieval': 'evidence_gathering',
        'data_processing': 'evidence_gathering', 
        'logical_reasoning': 'evidence_gathering',
        'answer_synthesis': 'answer_synthesis',
        'evidence_gathering': 'evidence_gathering',
        
        # 旧系统 -> 新系统（向上兼容）
        'evidence_gathering': 'information_retrieval',  # 默认转换
        'answer_synthesis': 'answer_synthesis',
    }
    
    @staticmethod
    def normalize_step_type(step_type: str, target_system: str = 'new') -> str:
        """标准化步骤类型
        
        Args:
            step_type: 原始步骤类型
            target_system: 目标系统 ('new' 或 'old')
            
        Returns:
            标准化后的步骤类型
        """
        if target_system == 'new':
            # 转换为新系统类型
            return StepTypeCompatibilityLayer.TYPE_MAPPING.get(step_type, step_type)
        else:
            # 转换为旧系统类型（反向映射）
            reverse_mapping = {v: k for k, v in StepTypeCompatibilityLayer.TYPE_MAPPING.items()}
            return reverse_mapping.get(step_type, step_type)
    
    @staticmethod
    def validate_step_data(step_data: dict, standards: dict) -> dict:
        """根据标准验证步骤数据
        
        Args:
            step_data: 步骤数据字典
            standards: 步骤类型标准
            
        Returns:
            验证和修复后的步骤数据
        """
        step_type = step_data.get('type', '')
        
        # 检查类型是否在标准中
        if step_type not in standards:
            # 尝试兼容性转换
            normalized_type = StepTypeCompatibilityLayer.normalize_step_type(step_type, 'new')
            if normalized_type in standards:
                step_data['type'] = normalized_type
                step_type = normalized_type
        
        # 检查必需字段
        if step_type in standards:
            type_config = standards[step_type]
            if type_config.get('sub_query_required', False):
                if 'sub_query' not in step_data or not step_data['sub_query']:
                    # 为需要sub_query的类型添加默认值
                    step_data['sub_query'] = step_data.get('description', 'Please provide a specific question')
        
        return step_data
