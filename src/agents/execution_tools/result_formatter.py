#!/usr/bin/env python3
"""
结果格式化器 - 格式化处理结果的核心工具
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OutputFormat(Enum):
    """输出格式枚举"""
    JSON = "json"
    XML = "xml"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    CSV = "csv"

class FormatStyle(Enum):
    """格式样式枚举"""
    COMPACT = "compact"
    PRETTY = "pretty"
    DETAILED = "detailed"
    SUMMARY = "summary"

@dataclass
class FormattingOptions:
    """格式化选项数据类"""
    output_format: OutputFormat
    style: FormatStyle
    include_metadata: bool = True
    include_timestamp: bool = True
    max_length: Optional[int] = None
    custom_template: Optional[str] = None

@dataclass
class FormattedResult:
    """格式化结果数据类"""
    original_result: Any
    formatted_content: str
    format_type: OutputFormat
    formatting_time: float
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def result(self) -> Any:
        """获取结果"""
        return self.original_result
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ResultFormatter:
    """结果格式化器"""
    
    def __init__(self):
        """初始化结果格式化器"""
        self.formatting_history = []
        self.performance_metrics = {
            "total_formats": 0,
            "successful_formats": 0,
            "failed_formats": 0,
            "average_formatting_time": 0.0,
            "format_distribution": {}
        }
        self.templates = self._load_default_templates()
        self.initialized = True
        logger.info("结果格式化器初始化完成")
    
    def format_result(self, result: Any, options: FormattingOptions) -> FormattedResult:
        """格式化结果"""
        try:
            # 验证输入
            if not self._validate_formatting_input(result, options):
                return self._create_error_result("Invalid formatting input")
            
            start_time = time.time()
            
            # 执行格式化
            formatted_result = self._execute_formatting(result, options)
            
            # 记录性能指标
            self._update_performance_metrics(start_time)
            
            # 记录格式化历史
            self._record_formatting_history(result, options, formatted_result)
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"结果格式化失败: {e}")
            return self._create_error_result(f"Formatting failed: {e}")
    
    def _validate_formatting_input(self, result: Any, options: FormattingOptions) -> bool:
        """验证格式化输入"""
        if result is None:
            return False
        
        if not isinstance(options, FormattingOptions):
            return False
        
        return True
    
    def _execute_formatting(self, result: Any, options: FormattingOptions) -> FormattedResult:
        """执行格式化"""
        try:
            # 根据格式类型进行格式化
            if options.format_type == "json":
                formatted_data = self._format_as_json(result, options)
            elif options.format_type == "xml":
                formatted_data = self._format_as_xml(result, options)
            elif options.format_type == "csv":
                formatted_data = self._format_as_csv(result, options)
            else:
                formatted_data = self._format_as_text(result, options)
            
            return FormattedResult(
                original_result=result,
                formatted_data=formatted_data,
                format_type=options.format_type,
                metadata={
                    'formatted_at': time.time(),
                    'format_options': options.to_dict() if hasattr(options, 'to_dict') else {}
                }
            )
            
        except Exception as e:
            logger.error(f"格式化执行失败: {e}")
            raise e
    
    def _format_as_json(self, result: Any, options: FormattingOptions) -> str:
        """格式化为JSON"""
        try:
            import json
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"JSON格式化失败: {e}")
            return str(result)
    
    def _format_as_xml(self, result: Any, options: FormattingOptions) -> str:
        """格式化为XML"""
        try:
            # 简化的XML格式化
            if isinstance(result, dict):
                xml_lines = ['<root>']
                for key, value in result.items():
                    xml_lines.append(f'  <{key}>{value}</{key}>')
                xml_lines.append('</root>')
                return '\n'.join(xml_lines)
            else:
                return f'<root>{result}</root>'
        except Exception as e:
            logger.warning(f"XML格式化失败: {e}")
            return str(result)
    
    def _format_as_csv(self, result: Any, options: FormattingOptions) -> str:
        """格式化为CSV"""
        try:
            import csv
            import io
            
            if isinstance(result, list) and result and isinstance(result[0], dict):
                # 字典列表
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)
                return output.getvalue()
            else:
                # 简单列表
                return ','.join(str(item) for item in result) if isinstance(result, list) else str(result)
        except Exception as e:
            logger.warning(f"CSV格式化失败: {e}")
            return str(result)
    
    def _format_as_text(self, result: Any, options: FormattingOptions) -> str:
        """格式化为文本"""
        return str(result)
    
    def _update_performance_metrics(self, start_time: float):
        """更新性能指标"""
        end_time = time.time()
        formatting_time = end_time - start_time
        
        self.performance_metrics["total_formats"] += 1
        self.performance_metrics["successful_formats"] += 1
        
        # 更新平均格式化时间
        total = self.performance_metrics["total_formats"]
        current_avg = self.performance_metrics["average_formatting_time"]
        self.performance_metrics["average_formatting_time"] = (
            (current_avg * (total - 1) + formatting_time) / total
        )
    
    def _record_formatting_history(self, result: Any, options: FormattingOptions, formatted_result: FormattedResult):
        """记录格式化历史"""
        self.formatting_history.append({
            'timestamp': time.time(),
            'result_type': type(result).__name__,
            'format_type': options.format_type,
            'success': True
        })
        
        # 保持历史记录在合理范围内
        if len(self.formatting_history) > 1000:
            self.formatting_history = self.formatting_history[-1000:]
    
    def _create_error_result(self, error_message: str) -> FormattedResult:
        """创建错误结果"""
        return FormattedResult(
            original_result=None,
            formatted_data=f"Error: {error_message}",
            format_type="error",
            metadata={'error': True, 'message': error_message, 'timestamp': time.time()}
        )
        
        try:
            # 选择格式化方法
            formatter = self._get_formatter(options.output_format)
            
            if formatter is None:
                return FormattedResult(
                    content=f"Unsupported format: {options.output_format}",
                    format_type=options.output_format,
                    metadata={"error": "unsupported_format"}
                )
            
            # 执行格式化
            formatted_content = formatter(result, options)
            
            # 应用样式
            if options.style != FormatStyle.COMPACT:
                formatted_content = self._apply_style(formatted_content, options)
            
            # 应用长度限制
            if options.max_length:
                formatted_content = self._apply_length_limit(formatted_content, options.max_length)
            
            formatting_time = time.time() - start_time
            
            # 创建格式化结果
            formatted_result = FormattedResult(
                original_result=result,
                formatted_content=formatted_content,
                format_type=options.output_format,
                formatting_time=formatting_time,
                metadata={
                    "style": options.style.value,
                    "include_metadata": options.include_metadata,
                    "include_timestamp": options.include_timestamp,
                    "max_length": options.max_length
                }
            )
            
            # 更新性能指标
            self._update_metrics(formatted_result)
            
            # 记录格式化历史
            self.formatting_history.append(formatted_result)
            
            logger.info(f"结果格式化成功: {options.output_format.value}")
            return formatted_result
            
        except Exception as e:
            formatting_time = time.time() - start_time
            logger.error(f"结果格式化失败: {e}")
            
            formatted_result = FormattedResult(
                original_result=result,
                formatted_content=f"格式化错误: {str(e)}",
                format_type=options.output_format,
                formatting_time=formatting_time,
                metadata={"error": str(e)}
            )
            
            self._update_metrics(formatted_result)
            return formatted_result
    
    def _get_formatter(self, output_format: OutputFormat) -> Optional[Callable]:
        """获取格式化器"""
        formatters = self._get_formatters()
        return formatters.get(output_format)
    
    def _get_formatters(self) -> Dict[OutputFormat, Callable]:
        """获取格式化器"""
        formatters = {
            OutputFormat.JSON: self._format_json,
            OutputFormat.XML: self._format_xml,
            OutputFormat.HTML: self._format_html,
            OutputFormat.MARKDOWN: self._format_markdown,
            OutputFormat.TEXT: self._format_text,
            OutputFormat.CSV: self._format_csv
        }
        return formatters
    
    def _format_json(self, result: Any, options: FormattingOptions) -> str:
        """JSON格式化"""
        if options.style == FormatStyle.PRETTY:
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return json.dumps(result, ensure_ascii=False)
    
    def _format_xml(self, result: Any, options: FormattingOptions) -> str:
        """XML格式化"""
        if isinstance(result, dict):
            xml_content = self._dict_to_xml(result, "result")
        else:
            xml_content = f"<result>{str(result)}</result>"
        
        if options.style == FormatStyle.PRETTY:
            return self._prettify_xml(xml_content)
        else:
            return xml_content
    
    def _format_html(self, result: Any, options: FormattingOptions) -> str:
        """HTML格式化"""
        if isinstance(result, dict):
            html_content = self._dict_to_html(result)
        else:
            html_content = f"<p>{str(result)}</p>"
        
        if options.style == FormatStyle.PRETTY:
            return self._prettify_html(html_content)
        else:
            return html_content
    
    def _format_markdown(self, result: Any, options: FormattingOptions) -> str:
        """Markdown格式化"""
        if isinstance(result, dict):
            return self._dict_to_markdown(result)
        else:
            return str(result)
    
    def _format_text(self, result: Any, options: FormattingOptions) -> str:
        """文本格式化"""
        if isinstance(result, dict):
            return self._dict_to_text(result)
        else:
            return str(result)
    
    def _format_csv(self, result: Any, options: FormattingOptions) -> str:
        """CSV格式化"""
        if isinstance(result, list) and all(isinstance(item, dict) for item in result):
            return self._list_to_csv(result)
        else:
            return str(result)
    
    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = "root") -> str:
        """字典转XML"""
        xml_parts = [f"<{root_name}>"]
        
        for key, value in data.items():
            if isinstance(value, dict):
                xml_parts.append(self._dict_to_xml(value, key))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        xml_parts.append(self._dict_to_xml(item, key))
                    else:
                        xml_parts.append(f"<{key}>{item}</{key}>")
            else:
                xml_parts.append(f"<{key}>{value}</{key}>")
        
        xml_parts.append(f"</{root_name}>")
        return "".join(xml_parts)
    
    def _dict_to_html(self, data: Dict[str, Any]) -> str:
        """字典转HTML"""
        html_parts = ["<div class='result'>"]
        
        for key, value in data.items():
            html_parts.append(f"<div class='field'>")
            html_parts.append(f"<strong>{key}:</strong> ")
            
            if isinstance(value, dict):
                html_parts.append(self._dict_to_html(value))
            elif isinstance(value, list):
                html_parts.append("<ul>")
                for item in value:
                    html_parts.append(f"<li>{item}</li>")
                html_parts.append("</ul>")
            else:
                html_parts.append(f"<span>{value}</span>")
            
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        return "".join(html_parts)
    
    def _dict_to_markdown(self, data: Dict[str, Any]) -> str:
        """字典转Markdown"""
        md_parts = []
        
        for key, value in data.items():
            md_parts.append(f"## {key}")
            
            if isinstance(value, dict):
                md_parts.append(self._dict_to_markdown(value))
            elif isinstance(value, list):
                for item in value:
                    md_parts.append(f"- {item}")
            else:
                md_parts.append(f"{value}")
            
            md_parts.append("")
        
        return "\n".join(md_parts)
    
    def _dict_to_text(self, data: Dict[str, Any]) -> str:
        """字典转文本"""
        text_parts = []
        
        for key, value in data.items():
            if isinstance(value, dict):
                text_parts.append(f"{key}:")
                text_parts.append(self._dict_to_text(value))
            elif isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(map(str, value))}")
            else:
                text_parts.append(f"{key}: {value}")
        
        return "\n".join(text_parts)
    
    def _list_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """列表转CSV"""
        if not data:
            return ""
        
        # 获取所有键
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        # 创建CSV头部
        csv_parts = [",".join(all_keys)]
        
        # 创建CSV数据行
        for item in data:
            row = []
            for key in all_keys:
                value = item.get(key, "")
                # 转义CSV特殊字符
                if isinstance(value, str) and ("," in value or '"' in value or "\n" in value):
                    value = f'"{value.replace('"', '""')}"'
                row.append(str(value))
            csv_parts.append(",".join(row))
        
        return "\n".join(csv_parts)
    
    def _prettify_xml(self, xml_content: str) -> str:
        """美化XML"""
        # 简单的XML美化
        import re
        xml_content = re.sub(r", ", '>\n<', xml_content)
        return xml_content
    
    def _prettify_html(self, html_content: str) -> str:
        """美化HTML"""
        # 简单的HTML美化
        import re
        html_content = re.sub(r", ", '>\n<', html_content)
        return html_content
    
    def _apply_style(self, content: str, options: FormattingOptions) -> str:
        """应用样式"""
        if options.style == FormatStyle.DETAILED:
            return self._apply_detailed_style(content)
        elif options.style == FormatStyle.SUMMARY:
            return self._apply_summary_style(content)
        else:
            return content
    
    def _apply_detailed_style(self, content: str) -> str:
        """应用详细样式"""
        return f"=== 详细结果 ===\n{content}\n=== 结束 ==="
    
    def _apply_summary_style(self, content: str) -> str:
        """应用摘要样式"""
        lines = content.split('\n')
        return '\n'.join(lines[:3]) + '\n... (更多内容)'
    
    def _apply_length_limit(self, content: str, max_length: int) -> str:
        """应用长度限制"""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."
    
    def _load_default_templates(self) -> Dict[str, str]:
        """加载默认模板"""
        return {
            "json": "{{result}}",
            "xml": "<result>{{result}}</result>",
            "html": "<div class='result'>{{result}}</div>",
            "markdown": "# 结果\n{{result}}",
            "text": "结果: {{result}}"
        }
    
    def _update_metrics(self, formatted_result: FormattedResult):
        """更新性能指标"""
        self.performance_metrics["total_formats"] += 1
        
        if "error" not in formatted_result.result:
            self.performance_metrics["successful_formats"] += 1
        else:
            self.performance_metrics["failed_formats"] += 1
        
        # 更新平均格式化时间
        total_formats = self.performance_metrics["total_formats"]
        current_avg = self.performance_metrics["average_formatting_time"]
        self.performance_metrics["average_formatting_time"] = (
            (current_avg * (total_formats - 1) + formatted_result.formatting_time) / total_formats
        )
        
        # 更新格式分布
        format_type = formatted_result.format_type.value
        if format_type not in self.performance_metrics["format_distribution"]:
            self.performance_metrics["format_distribution"][format_type] = 0
        self.performance_metrics["format_distribution"][format_type] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = self.performance_metrics.copy()
        
        # 计算成功率
        if metrics["total_formats"] > 0:
            metrics["success_rate"] = metrics["successful_formats"] / metrics["total_formats"]
        else:
            metrics["success_rate"] = 0
        return metrics
    
    def process_data(self, data: Any) -> Any:
        """处理数据（兼容接口）"""
        if isinstance(data, dict) and "result" in data:
            options = FormattingOptions(
                output_format=OutputFormat(data.get("type", "json")),
                style=FormatStyle(data.get("type", "compact")),
                include_metadata=data.get("type", True),
                include_timestamp=data.get("type", True),
                max_length=data.get("type"),
                custom_template=data.get("type")
            )
            return self.format_result(data["result"], options)
        else:
            return {"error", "Invalid data format for result formatting"}
    
    def validate(self, data: Any) -> bool:
        """验证数据（兼容接口）"""
        return data is not None and isinstance(data, dict) and "result" in data

# 全局实例
result_formatter = ResultFormatter()

def get_result_formatter():
    """获取结果格式化器实例"""
    return result_formatter
