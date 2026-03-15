#!/usr/bin/env python3
"""
Skill内容填充器

根据技能类型和需求，自动填充真实的:
- description: 技能描述
- tools: 工具定义
- triggers: 触发关键词
- prompt_template: 完整提示词模板
- examples: 使用示例
- 错误处理

使用方式:
    filler = SkillContentFiller()
    filled_skill = filler.fill_skill(skill_name, skill_type, requirements)
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class SkillContentFiller:
    """Skill内容填充器"""
    
    # 预定义的技能模板库
    SKILL_TEMPLATES = {
        "calculator-skill": {
            "description": "数学计算工具，执行精确的数学运算。支持基本算术（加、减、乘、除）、幂运算、三角函数、对数等高级数学运算。适用于数据分析、科学计算、Financial建模等场景。",
            "triggers": ["计算", "运算", "数学", "calculator", "calculate", "算一下", "等于多少"],
            "tools": [
                {
                    "name": "calculate",
                    "description": "执行数学表达式计算",
                    "parameters": {
                        "expression": {"type": "string", "description": "数学表达式，如 '10 + 20 * 3'"},
                        "precision": {"type": "integer", "description": "小数精度，默认4"}
                    },
                    "returns": "计算结果"
                }
            ],
            "prompt_template": """## 技能说明

### 功能描述
你是一个专业的数学计算助手，擅长执行各种数学运算。

### 使用方式
当用户提出计算需求时：
1. 解析用户的数学表达式
2. 使用calculate工具执行计算
3. 返回清晰的结果

### 支持的运算
- 基本运算: +, -, *, /, %
- 幂运算: **, pow
- 三角函数: sin, cos, tan (需要弧度)
- 对数: log, log10, log2
- 其他: sqrt, abs, round

### 注意事项
- 表达式中不能包含未定义的变量
- 除数不能为0
- 超大数计算可能需要设置精度""",
            "examples": [
                {
                    "user": "计算 100 * 5 + 50",
                    "expected": "550"
                },
                {
                    "user": "帮我算一下 sqrt(16) + pow(2, 3)",
                    "expected": "12.0"
                }
            ],
            "error_handling": {
                "除数为零": "返回错误提示：'除数不能为零，请检查表达式'",
                "无效表达式": "返回错误提示：'无效的数学表达式，请重新输入'",
                "不支持的操作": "返回错误提示：'暂不支持该运算，请尝试其他方式'"
            }
        },
        
        "multimodal-skill": {
            "description": "多模态内容处理工具，支持图像识别、视频分析、音频处理、OCR文字识别等功能。适用于内容审核、文档数字化、媒体分析等场景。",
            "triggers": ["图像", "图片", "照片", "识别", "OCR", "视频", "音频", "image", "video", "audio", "multimodal"],
            "tools": [
                {
                    "name": "image_recognition",
                    "description": "识别图像中的物体和内容",
                    "parameters": {
                        "image_path": {"type": "string", "description": "图像文件路径或URL"},
                        "mode": {"type": "string", "description": "识别模式: general(通用), object(物体), text(文字)"}
                    },
                    "returns": "识别结果"
                },
                {
                    "name": "ocr",
                    "description": "光学字符识别，提取图像中的文字",
                    "parameters": {
                        "image_path": {"type": "string", "description": "图像文件路径"}
                    },
                    "returns": "识别的文字内容"
                },
                {
                    "name": "video_analysis",
                    "description": "分析视频内容",
                    "parameters": {
                        "video_path": {"type": "string", "description": "视频文件路径"},
                        "timestamp": {"type": "integer", "description": "分析的时间点(秒)"}
                    },
                    "returns": "视频分析结果"
                }
            ],
            "prompt_template": """## 技能说明

### 功能描述
你是一个多模态内容处理助手，能够处理图像、视频、音频等多种媒体格式。

### 使用方式
1. 图像处理：识别图片内容、提取文字(OCR)
2. 视频分析：分析视频关键帧、提取音频
3. 音频处理：转写语音、分析音频特征

### 支持的功能
- 图像物体识别
- 场景理解
- 文字识别(OCR)
- 人脸检测
- 视频关键帧提取
- 音频转文字

### 注意事项
- 支持的图像格式: JPG, PNG, BMP, WebP
- 支持的视频格式: MP4, AVI, MOV
- OCR对手写体识别率较低""",
            "examples": [
                {
                    "user": "识别这张图片中的物体",
                    "expected": "[物体列表和置信度]"
                },
                {
                    "user": "提取图片中的文字",
                    "expected": "[识别的文字内容]"
                }
            ],
            "error_handling": {
                "文件不存在": "返回错误提示：'文件不存在，请检查路径'",
                "不支持的格式": "返回错误提示：'不支持的文件格式'",
                "处理失败": "返回错误提示：'处理失败，请稍后重试'"
            }
        },
        
        "browser-skill": {
            "description": "浏览器自动化工具，模拟用户在浏览器中的操作。支持网页浏览、表单填写、截图、元素提取等功能。适用于自动化测试、数据抓取、网页操作等场景。",
            "triggers": ["浏览器", "网页", "截图", "自动化", "browser", "navigate", "click", "screenshot"],
            "tools": [
                {
                    "name": "navigate",
                    "description": "导航到指定URL",
                    "parameters": {
                        "url": {"type": "string", "description": "目标网页URL"}
                    },
                    "returns": "页面内容"
                },
                {
                    "name": "click",
                    "description": "点击页面元素",
                    "parameters": {
                        "selector": {"type": "string", "description": "CSS选择器或元素路径"}
                    },
                    "returns": "操作结果"
                },
                {
                    "name": "fill_form",
                    "description": "填写表单",
                    "parameters": {
                        "form_data": {"type": "object", "description": "表单数据字典"}
                    },
                    "returns": "提交结果"
                },
                {
                    "name": "screenshot",
                    "description": "截图",
                    "parameters": {
                        "selector": {"type": "string", "description": "截图区域选择器(可选)"}
                    },
                    "returns": "截图文件路径"
                }
            ],
            "prompt_template": """## 技能说明

### 功能描述
你是一个浏览器自动化助手，能够模拟用户操作浏览器。

### 使用方式
1. 导航：打开指定网页
2. 交互：点击、输入、选择
3. 提取：获取页面内容、截图
4. 自动化：执行预定义的浏览器操作序列

### 支持的操作
- 打开网页 (navigate)
- 点击元素 (click)
- 填写表单 (fill_form)
- 获取元素文本 (get_text)
- 截图 (screenshot)
- 执行JavaScript (execute_js)

### 注意事项
- 需要配置浏览器驱动
- 部分网站有反爬虫机制
- 截图可能包含敏感信息""",
            "examples": [
                {
                    "user": "打开Google首页",
                    "expected": "[页面内容]"
                },
                {
                    "user": "截取网页截图",
                    "expected": "[截图保存路径]"
                }
            ],
            "error_handling": {
                "页面加载失败": "返回错误提示：'页面加载超时，请检查网络'",
                "元素未找到": "返回错误提示：'未找到指定元素，请检查选择器'",
                "截图失败": "返回错误提示：'截图失败，请重试'"
            }
        },
        
        "file-read-skill": {
            "description": "文件读取工具，支持读取各种格式的文本文件。支持TXT、JSON、YAML、CSV、Markdown等格式。适用于数据导入、配置读取、文档处理等场景。",
            "triggers": ["读取", "打开", "文件", "内容", "file", "read", "加载"],
            "tools": [
                {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "file_path": {"type": "string", "description": "文件路径"},
                        "encoding": {"type": "string", "description": "文件编码，默认utf-8"},
                        "max_lines": {"type": "integer", "description": "最大读取行数(可选)"}
                    },
                    "returns": "文件内容"
                },
                {
                    "name": "read_json",
                    "description": "读取并解析JSON文件",
                    "parameters": {
                        "file_path": {"type": "string", "description": "JSON文件路径"}
                    },
                    "returns": "解析后的JSON对象"
                },
                {
                    "name": "read_csv",
                    "description": "读取CSV文件",
                    "parameters": {
                        "file_path": {"type": "string", "description": "CSV文件路径"},
                        "has_header": {"type": "boolean", "description": "是否有表头，默认True"}
                    },
                    "returns": "CSV数据列表"
                }
            ],
            "prompt_template": """## 技能说明

### 功能描述
你是一个文件读取助手，能够读取各种格式的文件内容。

### 使用方式
1. 文本文件：直接读取内容
2. JSON：解析为对象/数组
3. CSV：解析为表格数据
4. YAML：解析为配置对象

### 支持的格式
- 文本: TXT, MD, HTML
- 数据: JSON, YAML, CSV, XML
- 配置: INI, TOML, ENV

### 注意事项
- 文件路径需要是绝对路径或相对于当前目录
- 大文件可能需要分批读取
- 二进制文件不支持直接读取""",
            "examples": [
                {
                    "user": "读取 config.json 文件",
                    "expected": "[JSON内容]"
                },
                {
                    "user": "查看 data.csv 的前10行",
                    "expected": "[CSV数据列表]"
                }
            ],
            "error_handling": {
                "文件不存在": "返回错误提示：'文件不存在，请检查路径'",
                "编码错误": "返回错误提示：'文件编码不支持，请尝试其他编码'",
                "解析失败": "返回错误提示：'文件格式错误，无法解析'"
            }
        }
    }
    
    def __init__(self):
        self.logger = None
        try:
            import logging
            self.logger = logging.getLogger(__name__)
        except:
            pass
    
    def fill_skill(self, skill_name: str, skill_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        填充Skill内容
        
        Args:
            skill_name: 技能名称
            skill_type: 技能类型 (mcp_integration, expert, workflow等)
            requirements: 原始需求
            
        Returns:
            填充后的skill数据
        """
        # 查找匹配的模板
        template = self._find_template(skill_name, requirements)
        
        if template:
            filled = template.copy()
            self._log(f"找到匹配的模板: {skill_name}")
        else:
            # 使用通用模板
            filled = self._create_generic_template(skill_name, requirements)
            self._log(f"使用通用模板: {skill_name}")
        
        # 合并需求中的自定义内容
        if requirements.get("description"):
            filled["description"] = requirements["description"]
        
        return filled
    
    def _find_template(self, skill_name: str, requirements: Dict[str, Any]) -> Optional[Dict]:
        """查找匹配的模板"""
        # 1. 精确匹配
        if skill_name in self.SKILL_TEMPLATES:
            return self.SKILL_TEMPLATES[skill_name]
        
        # 2. 模糊匹配
        skill_name_lower = skill_name.lower()
        for key, template in self.SKILL_TEMPLATES.items():
            if any(kw in skill_name_lower for kw in key.lower().split("-")):
                return template
        
        # 3. 关键词匹配
        desc = requirements.get("description", "").lower()
        for key, template in self.SKILL_TEMPLATES.items():
            keywords = {
                "calculator": ["计算", "数学", "math", "运算"],
                "multimodal": ["图像", "图片", "视频", "audio", "video", "image", "OCR"],
                "browser": ["浏览器", "网页", "browser", "自动化"],
                "file-read": ["文件", "读取", "file", "read"]
            }
            if any(kw in desc for kw in keywords.get(key, [])):
                return template
        
        return None
    
    def _create_generic_template(self, skill_name: str, requirements: Dict[str, Any]) -> Dict:
        """创建通用模板"""
        description = requirements.get("description", f"{skill_name} - AI技能")
        
        return {
            "description": description,
            "triggers": [skill_name.lower(), skill_name.replace("-", "_")],
            "tools": [],
            "prompt_template": f"""## 技能说明

### 功能描述
{description}

### 使用方式
请描述如何使用这个技能

### 注意事项
请补充注意事项""",
            "examples": [],
            "error_handling": {}
        }
    
    def fill_skill_yaml(self, skill_dir: str, skill_name: str, skill_type: str, requirements: Dict[str, Any]) -> bool:
        """
        填充Skill YAML文件
        
        Args:
            skill_dir: Skill目录路径
            skill_name: 技能名称
            skill_type: 技能类型
            requirements: 原始需求
            
        Returns:
            是否成功
        """
        try:
            # 填充内容
            filled = self.fill_skill(skill_name, skill_type, requirements)
            
            # 读取现有文件
            yaml_path = os.path.join(skill_dir, "skill.yaml")
            if not os.path.exists(yaml_path):
                self._log(f"文件不存在: {yaml_path}")
                return False
            
            with open(yaml_path, 'r', encoding='utf-8') as f:
                skill_data = yaml.safe_load(f)
            
            # 更新字段
            if "description" in filled:
                skill_data["description"] = filled["description"]
            if "triggers" in filled:
                skill_data["triggers"] = filled["triggers"]
            if "tools" in filled:
                skill_data["tools"] = filled["tools"]
            if "prompt_template" in filled:
                skill_data["prompt_template"] = filled["prompt_template"]
            
            # 保存
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(skill_data, f, allow_unicode=True, default_flow_style=False)
            
            self._log(f"成功填充skill: {skill_name}")
            return True
            
        except Exception as e:
            self._log(f"填充失败: {e}")
            return False
    
    def _log(self, message: str):
        if self.logger:
            self.logger.info(f"[SkillContentFiller] {message}")
        else:
            print(f"[SkillContentFiller] {message}")


def get_skill_content_filler() -> SkillContentFiller:
    """获取内容填充器实例"""
    return SkillContentFiller()
