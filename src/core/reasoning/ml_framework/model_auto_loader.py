"""
模型自动加载工具

为所有ML组件提供统一的模型自动加载功能。
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def auto_load_model(component, model_name: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """自动加载模型
    
    Args:
        component: ML组件实例（BaseMLComponent子类）
        model_name: 模型名称
        config: 配置字典（可选）
        
    Returns:
        是否成功加载模型
    """
    try:
        # 1. 优先从配置中获取模型路径
        if config and config.get('model_path'):
            model_path = config['model_path']
            if Path(model_path).exists():
                if component.load_model(model_path):
                    logger.info(f"✅ [{model_name}] 从配置路径加载模型: {model_path}")
                    return True
                else:
                    logger.warning(f"⚠️ [{model_name}] 配置路径模型加载失败: {model_path}")
        
        # 2. 尝试从默认路径加载
        default_model_path = Path("data/ml_models") / f"{model_name}.pkl"
        if default_model_path.exists():
            if component.load_model(str(default_model_path)):
                logger.info(f"✅ [{model_name}] 从默认路径加载模型: {default_model_path}")
                return True
            else:
                logger.warning(f"⚠️ [{model_name}] 默认路径模型加载失败: {default_model_path}")
        
        # 3. 模型不存在，使用规则版本
        logger.debug(f"ℹ️ [{model_name}] 模型文件不存在，使用规则版本")
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ [{model_name}] 自动加载模型失败: {e}")
        return False

