#!/usr/bin/env python3
"""
数据模板配置 - 替代硬编码数据
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random


@dataclass
class DataTemplate:
    """数据模板"""
    name: str
    template_type: str
    config: Dict[str, Any]
    description: str
    created_at: float
    updated_at: float


class DataTemplateManager:
    """数据模板管理器 - 替代硬编码数据"""
    
    def __init__(self, config_dir: str = "config/data_templates"):
        self.config_dir = config_dir
        self.templates: Dict[str, DataTemplate] = {}
        self.logger = self._get_logger()
        self._ensure_config_dir()
        self._load_templates()
    
    def _get_logger(self):
        """获取日志记录器"""
        import logging
        return logging.getLogger(__name__)
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _load_templates(self):
        """加载数据模板"""
        try:
            if not os.path.exists(self.config_dir):
                self.logger.info("配置目录不存在，创建默认模板")
                self._create_default_templates()
                return
            
            template_files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
            
            for template_file in template_files:
                template_path = os.path.join(self.config_dir, template_file)
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template = DataTemplate(
                    name=template_data['name'],
                    template_type=template_data['template_type'],
                    config=template_data['config'],
                    description=template_data['description'],
                    created_at=template_data['created_at'],
                    updated_at=template_data['updated_at']
                )
                
                self.templates[template.name] = template
            
            # 如果没有加载到任何模板，创建默认模板
            if len(self.templates) == 0:
                self.logger.info("未找到模板文件，创建默认模板")
                self._create_default_templates()
            else:
                self.logger.info(f"加载了 {len(self.templates)} 个数据模板")
            
        except Exception as e:
            self.logger.error(f"加载数据模板失败: {e}")
            self._create_default_templates()
    
    def _create_default_templates(self):
        """创建默认数据模板"""
        default_templates = [
            {
                "name": "historical_metrics",
                "template_type": "metrics",
                "description": "历史指标数据模板",
                "config": {
                    "base_score": 0.7,
                    "trend_factor": 0.01,
                    "noise_range": 0.1,
                    "days_count": 30,
                    "metrics": [
                        "overall_score", "code_quality", "architecture_score",
                        "maintainability", "performance", "security",
                        "test_coverage", "documentation", "complexity", "technical_debt"
                    ]
                }
            },
            {
                "name": "sample_data_generator",
                "template_type": "data_generator",
                "description": "数据生成器模板",
                "config": {
                    "sample_count": 100,
                    "data_types": ["string", "number", "boolean", "array", "object"],
                    "string_length_range": [5, 50],
                    "number_range": [0, 1000],
                    "array_length_range": [1, 10]
                }
            },
            {
                "name": "agent_configuration_data",
                "template_type": "agent_config",
                "description": "智能体配置数据模板",
                "config": {
                    "agent_types": ["knowledge", "reasoning", "answer", "citation"],
                    "capabilities": ["search", "analyze", "generate", "validate"],
                    "performance_metrics": ["accuracy", "speed", "reliability"]
                }
            },
            {
                "name": "training_samples",
                "template_type": "ml_training",
                "description": "机器学习训练样本模板",
                "config": {
                    "feature_count": 10,
                    "sample_count": 1000,
                    "target_classes": 5,
                    "noise_level": 0.1,
                    "validation_split": 0.2
                }
            }
        ]
        
        for template_data in default_templates:
            template = DataTemplate(
                name=template_data["name"],
                template_type=template_data["template_type"],
                config=template_data["config"],
                description=template_data["description"],
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp()
            )
            
            self.templates[template.name] = template
            self._save_template(template)
    
    def _save_template(self, template: DataTemplate):
        """保存模板到文件"""
        try:
            template_path = os.path.join(self.config_dir, f"{template.name}.json")
            template_data = {
                "name": template.name,
                "template_type": template.template_type,
                "config": template.config,
                "description": template.description,
                "created_at": template.created_at,
                "updated_at": template.updated_at
            }
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存模板失败 {template.name}: {e}")
    
    def get_template(self, name: str) -> Optional[DataTemplate]:
        """获取数据模板"""
        return self.templates.get(name)
    
    def generate_data(self, template_name: str, **kwargs) -> Any:
        """根据模板生成数据"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        if template.template_type == "metrics":
            return self._generate_metrics_data(template, **kwargs)
        elif template.template_type == "test_data":
            return self._generate_test_data(template, **kwargs)
        elif template.template_type == "agent":
            return self._generate_agent_data(template, **kwargs)
        elif template.template_type == "ml_training":
            return self._generate_ml_training_data(template, **kwargs)
        else:
            raise ValueError(f"未知的模板类型: {template.template_type}")
    
    def _generate_metrics_data(self, template: DataTemplate, **kwargs) -> List[Dict[str, Any]]:
        """生成指标数据"""
        config = template.config
        days_count = kwargs.get('days_count', config['days_count'])
        base_score = kwargs.get('base_score', config['base_score'])
        trend_factor = kwargs.get('trend_factor', config['trend_factor'])
        noise_range = kwargs.get('noise_range', config['noise_range'])
        
        current_time = datetime.now().timestamp()
        historical_data = []
        
        for i in range(days_count):
            timestamp = current_time - (i * 24 * 3600)
            
            # 模拟质量指标的变化趋势
            score = base_score + (i * trend_factor)
            noise = random.uniform(-noise_range, noise_range)
            
            metrics = {
                'timestamp': timestamp,
                'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
                'metrics_count': random.randint(8, 15),
                'issues_found': random.randint(0, 5),
                'improvements_made': random.randint(1, 8)
            }
            
            # 为每个指标生成数据
            for metric in config['metrics']:
                if metric == 'complexity':
                    metrics[metric] = max(0.0, min(1.0, 0.3 + noise))
                elif metric == 'technical_debt':
                    metrics[metric] = max(0.0, min(1.0, 0.2 + noise))
                else:
                    metrics[metric] = max(0.0, min(1.0, score + noise + random.uniform(-0.05, 0.05)))
            
            historical_data.append(metrics)
        
        return historical_data
    
    def _generate_test_data(self, template: DataTemplate, **kwargs) -> List[Dict[str, Any]]:
        """生成测试数据"""
        config = template.config
        sample_count = kwargs.get('sample_count', config['sample_count'])
        
        test_data = []
        for i in range(sample_count):
            sample = {
                'id': f"test_{i}",
                'string_value': self._generate_string_value(config),
                'number_value': self._generate_number_value(config),
                'boolean_value': random.choice([True, False]),
                'array_value': self._generate_array_value(config),
                'object_value': self._generate_object_value(config)
            }
            test_data.append(sample)
        
        return test_data
    
    def _generate_agent_data(self, template: DataTemplate, **kwargs) -> Dict[str, Any]:
        """生成智能体数据"""
        config = template.config
        
        return {
            'agent_type': random.choice(config['agent_types']),
            'capabilities': random.sample(config['capabilities'], random.randint(1, 3)),
            'performance': {
                metric: random.uniform(0.7, 1.0) 
                for metric in config['performance_metrics']
            },
            'created_at': datetime.now().timestamp(),
            'status': 'active'
        }
    
    def _generate_ml_training_data(self, template: DataTemplate, **kwargs) -> Dict[str, Any]:
        """生成机器学习训练数据"""
        config = template.config
        feature_count = kwargs.get('feature_count', config['feature_count'])
        sample_count = kwargs.get('sample_count', config['sample_count'])
        
        # 生成特征数据
        features = []
        for i in range(sample_count):
            sample = [random.uniform(0, 1) for _ in range(feature_count)]
            features.append(sample)
        
        # 生成目标变量
        targets = [random.randint(0, config['target_classes'] - 1) for _ in range(sample_count)]
        
        return {
            'features': features,
            'targets': targets,
            'feature_names': [f"feature_{i}" for i in range(feature_count)],
            'target_names': [f"class_{i}" for i in range(config['target_classes'])],
            'sample_count': sample_count,
            'feature_count': feature_count
        }
    
    def _generate_string_value(self, config: Dict[str, Any]) -> str:
        """生成字符串值"""
        length_range = config['string_length_range']
        length = random.randint(length_range[0], length_range[1])
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))
    
    def _generate_number_value(self, config: Dict[str, Any]) -> float:
        """生成数值"""
        number_range = config['number_range']
        return random.uniform(number_range[0], number_range[1])
    
    def _generate_array_value(self, config: Dict[str, Any]) -> List[Any]:
        """生成数组值"""
        length_range = config['array_length_range']
        length = random.randint(length_range[0], length_range[1])
        return [random.randint(1, 100) for _ in range(length)]
    
    def _generate_object_value(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """生成对象值"""
        return {
            'key1': random.randint(1, 100),
            'key2': random.choice(['A', 'B', 'C']),
            'key3': random.uniform(0, 1)
        }
    
    def create_template(self, name: str, template_type: str, config: Dict[str, Any], description: str = "") -> DataTemplate:
        """创建新模板"""
        template = DataTemplate(
            name=name,
            template_type=template_type,
            config=config,
            description=description,
            created_at=datetime.now().timestamp(),
            updated_at=datetime.now().timestamp()
        )
        
        self.templates[name] = template
        self._save_template(template)
        
        return template
    
    def update_template(self, name: str, config: Dict[str, Any], description: str = None) -> bool:
        """更新模板"""
        if name not in self.templates:
            return False
        
        template = self.templates[name]
        template.config = config
        if description:
            template.description = description
        template.updated_at = datetime.now().timestamp()
        
        self._save_template(template)
        return True
    
    def delete_template(self, name: str) -> bool:
        """删除模板"""
        if name not in self.templates:
            return False
        
        try:
            template_path = os.path.join(self.config_dir, f"{name}.json")
            if os.path.exists(template_path):
                os.remove(template_path)
            
            del self.templates[name]
            return True
            
        except Exception as e:
            self.logger.error(f"删除模板失败 {name}: {e}")
            return False


# 全局实例
_data_template_manager = None

def get_data_template_manager() -> DataTemplateManager:
    """获取数据模板管理器实例"""
    global _data_template_manager
    if _data_template_manager is None:
        _data_template_manager = DataTemplateManager()
    return _data_template_manager
