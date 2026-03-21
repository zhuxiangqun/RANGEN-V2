"""
提示词管理器
管理各种提示词模板，支持动态渲染和版本控制
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from jinja2 import Template, TemplateError
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("jinja2不可用，将使用基础模板功能")

logger = logging.getLogger(__name__)


class PromptTemplate:
    """提示词模板类"""

    def __init__(self, name: str, template_str: str, version: str = "1.0"):
        self.name = name
        self.template_str = template_str
        self.version = version
        self.created_at = datetime.now()

        # 预编译模板
        if JINJA2_AVAILABLE:
            try:
                self._compiled_template = Template(template_str)
            except TemplateError as e:
                logger.error(f"模板编译失败 {name}: {e}")
                self._compiled_template = None
        else:
            self._compiled_template = None

    def render(self, **kwargs) -> str:
        """渲染模板"""
        if self._compiled_template:
            try:
                return self._compiled_template.render(**kwargs)
            except Exception as e:
                logger.error(f"模板渲染失败 {self.name}: {e}")
                return self._fallback_render(**kwargs)
        else:
            return self._fallback_render(**kwargs)

    def _fallback_render(self, **kwargs) -> str:
        """基础模板渲染（不支持复杂语法）"""
        result = self.template_str
        for key, value in kwargs.items():
            placeholder = "{{" + key + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result

    def get_metadata(self) -> Dict[str, Any]:
        """获取模板元数据"""
        return {
            'name': self.name,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'template_length': len(self.template_str),
            'has_jinja': self._compiled_template is not None
        }


class PromptManager:
    """提示词管理器"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.template_stats = {
            'total_templates': 0,
            'render_calls': 0,
            'successful_renders': 0,
            'failed_renders': 0
        }

        # 预加载内置模板
        self._load_builtin_templates()

        logger.info(f"✅ 提示词管理器初始化完成，支持{len(self.templates)}个模板")

    def register_template(self, name: str, template_str: str, version: str = "1.0") -> bool:
        """注册新模板"""
        try:
            template = PromptTemplate(name, template_str, version)
            self.templates[name] = template
            self.template_stats['total_templates'] = len(self.templates)
            logger.info(f"✅ 模板已注册: {name} v{version}")
            return True
        except Exception as e:
            logger.error(f"注册模板失败 {name}: {e}")
            return False

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)

    def render(self, template_name: str, **kwargs) -> Optional[str]:
        """渲染模板"""
        self.template_stats['render_calls'] += 1

        template = self.get_template(template_name)
        if not template:
            logger.error(f"模板不存在: {template_name}")
            self.template_stats['failed_renders'] += 1
            return None

        try:
            result = template.render(**kwargs)
            self.template_stats['successful_renders'] += 1
            return result
        except Exception as e:
            logger.error(f"模板渲染失败 {template_name}: {e}")
            self.template_stats['failed_renders'] += 1
            return None

    def update_template(self, name: str, new_template_str: str, new_version: Optional[str] = None) -> bool:
        """更新模板"""
        if name not in self.templates:
            logger.error(f"模板不存在: {name}")
            return False

        try:
            current_version = self.templates[name].version
            new_version = new_version or self._increment_version(current_version)

            new_template = PromptTemplate(name, new_template_str, new_version)
            self.templates[name] = new_template

            logger.info(f"✅ 模板已更新: {name} {current_version} -> {new_version}")
            return True
        except Exception as e:
            logger.error(f"更新模板失败 {name}: {e}")
            return False

    def remove_template(self, name: str) -> bool:
        """移除模板"""
        if name in self.templates:
            del self.templates[name]
            self.template_stats['total_templates'] = len(self.templates)
            logger.info(f"✅ 模板已移除: {name}")
            return True
        else:
            logger.warning(f"模板不存在: {name}")
            return False

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """列出所有模板"""
        return {
            name: template.get_metadata()
            for name, template in self.templates.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.template_stats.copy()
        total_renders = stats['render_calls']
        if total_renders > 0:
            stats['success_rate'] = stats['successful_renders'] / total_renders * 100
        else:
            stats['success_rate'] = 0.0
        return stats

    def _load_builtin_templates(self):
        """加载内置模板"""
        builtin_templates = {
            'step_generation': self._get_step_generation_template(),
            'step_validation': self._get_step_validation_template(),
            'complexity_analysis': self._get_complexity_analysis_template(),
        }

        for name, template_str in builtin_templates.items():
            self.register_template(name, template_str, "1.0")

    def _get_step_generation_template(self) -> str:
        """获取步骤生成模板"""
        return """
# 推理步骤生成任务

你是一个专业的推理规划专家，需要为用户查询生成清晰的推理步骤。

## 查询内容
{{ query }}

## 上下文信息
时间: {{ current_time }}
查询类型: {{ query_type }}
复杂度级别: {{ complexity_level }}

## 生成要求

请生成解决此查询所需的推理步骤：

### 步骤格式要求
每个步骤必须包含：
- **type**: 步骤类型 (information_gathering/analysis/comparison/synthesis)
- **description**: 清晰的步骤描述
- **sub_query**: 可执行的子查询（可选）

### 推理链要求
- 步骤间要有逻辑关系
- 后一步应该依赖前一步的结果
- 最终步骤应该是答案合成

## 输出格式
返回JSON格式的步骤数组：
```json
[
  {
    "type": "information_gathering",
    "description": "步骤描述",
    "sub_query": "具体查询"
  }
]
```

## 现在开始生成

为查询生成推理步骤：
{{ query }}
"""

    def _get_step_validation_template(self) -> str:
        """获取步骤验证模板"""
        return """
# 推理步骤验证任务

你需要验证给定的推理步骤是否正确和完整。

## 原始查询
{{ query }}

## 当前步骤
{{ steps }}

## 验证标准

1. **相关性**: 步骤是否与查询相关
2. **逻辑性**: 步骤间是否有逻辑关系
3. **完整性**: 是否覆盖了解决查询所需的所有方面
4. **可执行性**: 每个步骤是否可执行

## 输出格式
返回JSON格式的验证结果：
```json
{
  "is_valid": true/false,
  "reason": "验证结果说明",
  "quality_score": 0.0-1.0,
  "suggestions": ["改进建议"]
}
```

## 验证结果
"""

    def _get_complexity_analysis_template(self) -> str:
        """获取复杂度分析模板"""
        return """
# 查询复杂度分析任务

分析查询的复杂度并推荐处理策略。

## 查询内容
{{ query }}

## 分析维度

1. **推理深度**: 需要多少步推理
2. **领域广度**: 涉及多少个知识领域
3. **数据需求**: 需要什么类型的数据
4. **计算复杂度**: 是否涉及复杂计算

## 输出格式
```json
{
  "complexity": "simple/medium/complex",
  "reasoning_steps": 1-10,
  "domains": ["领域1", "领域2"],
  "recommended_approach": "fast/reasoning/with_thinking"
}
```

## 分析结果
"""

    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        try:
            parts = version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return f"{major}.{minor + 1}"
        except:
            return "1.1"

    def export_templates(self, file_path: str) -> bool:
        """导出所有模板到文件"""
        try:
            import json
            export_data = {
                'templates': {
                    name: {
                        'template_str': template.template_str,
                        'version': template.version,
                        'metadata': template.get_metadata()
                    }
                    for name, template in self.templates.items()
                },
                'stats': self.get_stats(),
                'exported_at': datetime.now().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 模板已导出到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return False

    def import_templates(self, file_path: str) -> bool:
        """从文件导入模板"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0
            for name, template_data in data.get('templates', {}).items():
                self.register_template(
                    name,
                    template_data['template_str'],
                    template_data.get('version', '1.0')
                )
                imported_count += 1

            logger.info(f"✅ 已导入 {imported_count} 个模板")
            return True
        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return False
