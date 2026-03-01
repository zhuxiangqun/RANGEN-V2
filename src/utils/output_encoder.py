"""
输出编码和安全防护模块
提供企业级输出编码，防止XSS、注入和各种输出相关攻击
"""

import html
import json
import urllib.parse
import re
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

from src.services.logging_service import get_logger

logger = get_logger("output_encoder")


class EncodingType(Enum):
    """编码类型"""
    HTML = "html"          # HTML实体编码
    HTML_ATTR = "html_attr" # HTML属性编码
    URL = "url"            # URL编码
    JS = "js"              # JavaScript编码
    CSS = "css"            # CSS编码
    JSON = "json"          # JSON编码（安全序列化）
    XML = "xml"            # XML编码


class ContextType(Enum):
    """输出上下文类型"""
    HTML_BODY = "html_body"        # HTML正文（<div>内容</div>）
    HTML_ATTRIBUTE = "html_attribute"  # HTML属性（href="..."）
    HTML_STYLE = "html_style"      # HTML样式（style="..."）
    SCRIPT = "script"              # JavaScript代码
    SCRIPT_ATTRIBUTE = "script_attribute"  # JavaScript属性
    CSS = "css"                    # CSS代码
    URL = "url"                    # URL上下文
    JSON = "json"                  # JSON数据
    XML = "xml"                    # XML数据


@dataclass
class EncodingResult:
    """编码结果"""
    encoded_value: Any
    encoding_applied: List[EncodingType]
    was_modified: bool = False
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class OutputEncoder:
    """输出编码器主类"""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化危险模式"""
        # JavaScript危险模式
        self.js_dangerous_patterns = [
            r'(?i)(eval\(|setTimeout\(|setInterval\()',
            r'(?i)(document\.write|document\.writeln)',
            r'(?i)(innerHTML|outerHTML|insertAdjacentHTML)',
            r'(?i)(location\.|window\.|document\.)',
            r'(?i)(<script|<iframe|<object|<embed)',
            r'(?i)(javascript:|vbscript:|data:|mocha:)',
            r'(?i)(onload|onerror|onclick|onmouseover)',
        ]
        
        # CSS危险模式
        self.css_dangerous_patterns = [
            r'(?i)(expression\(|url\(|@import)',
            r'(?i)(javascript:|vbscript:|data:)',
            r'(?i)(behavior:|binding:|-moz-binding:)',
        ]
        
        # URL危险模式
        self.url_dangerous_patterns = [
            r'(?i)(javascript:|vbscript:|data:|mocha:)',
            r'(?i)(%0a|%0d|%00)',  # 换行符、回车符、空字符
            r'(?i)(\.\./|\.\.\\)',  # 路径遍历
        ]
    
    def _needs_encoding(self, value: Any) -> bool:
        """检查值是否需要编码"""
        if isinstance(value, (int, float, bool)):
            return False
        elif isinstance(value, str):
            return True
        elif value is None:
            return False
        else:
            # 列表、字典等需要递归处理
            return True
    
    def encode_html(self, value: str) -> str:
        """HTML实体编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # 标准HTML转义
        encoded = html.escape(value, quote=False)
        
        # 额外处理单引号和双引号
        encoded = encoded.replace("'", "&#x27;")
        encoded = encoded.replace('"', "&quot;")
        
        # 处理斜杠（防御闭合标签）
        encoded = encoded.replace("/", "&#x2F;")
        
        return encoded
    
    def encode_html_attribute(self, value: str) -> str:
        """HTML属性编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # HTML属性需要额外的引号编码
        encoded = html.escape(value)
        
        # 确保引号被编码
        encoded = encoded.replace("'", "&#x27;")
        encoded = encoded.replace('"', "&quot;")
        
        # 处理空格和特殊字符
        encoded = encoded.replace("\t", "&#x09;")
        encoded = encoded.replace("\n", "&#x0A;")
        encoded = encoded.replace("\r", "&#x0D;")
        
        return encoded
    
    def encode_url(self, value: str) -> str:
        """URL编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # URL编码
        encoded = urllib.parse.quote(value, safe='')
        
        # 检查危险模式
        for pattern in self.url_dangerous_patterns:
            if re.search(pattern, encoded, re.IGNORECASE):
                logger.warning(f"URL编码后仍检测到危险模式: {pattern}")
                # 双重编码
                encoded = urllib.parse.quote(encoded, safe='')
                break
        
        return encoded
    
    def encode_javascript(self, value: str) -> str:
        """JavaScript编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # 处理特殊字符
        encoded = value
        
        # 转义反斜杠
        encoded = encoded.replace('\\', '\\\\')
        
        # 转义引号
        encoded = encoded.replace("'", "\\'")
        encoded = encoded.replace('"', '\\"')
        
        # 转义换行符
        encoded = encoded.replace('\n', '\\n')
        encoded = encoded.replace('\r', '\\r')
        encoded = encoded.replace('\t', '\\t')
        
        # 转义Unicode控制字符
        encoded = re.sub(r'[\x00-\x1F\x7F]', lambda m: f'\\x{m.group(0).encode().hex():02x}', encoded)
        
        # 检查危险模式
        for pattern in self.js_dangerous_patterns:
            if re.search(pattern, encoded, re.IGNORECASE):
                logger.warning(f"JavaScript编码后仍检测到危险模式: {pattern}")
                # 添加额外转义
                encoded = encoded.replace('<', '\\x3c')
                encoded = encoded.replace('>', '\\x3e')
                break
        
        return encoded
    
    def encode_css(self, value: str) -> str:
        """CSS编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # CSS编码
        encoded = value
        
        # 转义特殊字符
        encoded = re.sub(r'[^\w\s-]', lambda m: f'\\{m.group(0)}', encoded)
        
        # 检查危险模式
        for pattern in self.css_dangerous_patterns:
            if re.search(pattern, encoded, re.IGNORECASE):
                logger.warning(f"CSS编码后仍检测到危险模式: {pattern}")
                # 添加额外防护
                encoded = f"/*{encoded}*/"
                break
        
        return encoded
    
    def encode_json(self, value: Any) -> str:
        """安全JSON编码（序列化）"""
        # 使用json.dumps进行安全序列化
        try:
            # 清理值中的危险内容
            safe_value = self._make_json_safe(value)
            encoded = json.dumps(safe_value, ensure_ascii=False)
            return encoded
        except (TypeError, ValueError) as e:
            logger.error(f"JSON编码失败: {e}")
            # 返回安全错误消息
            return json.dumps({"error": "数据编码失败"})
    
    def _make_json_safe(self, value: Any) -> Any:
        """使值对JSON安全"""
        if isinstance(value, str):
            # 字符串：检查并清理危险内容
            return self.encode_html(value)  # 先进行HTML编码作为防御层
        elif isinstance(value, dict):
            # 字典：递归处理所有值
            return {k: self._make_json_safe(v) for k, v in value.items()}
        elif isinstance(value, list):
            # 列表：递归处理所有元素
            return [self._make_json_safe(item) for item in value]
        elif isinstance(value, (int, float, bool)):
            # 基本类型：安全
            return value
        elif value is None:
            return None
        else:
            # 其他类型：转换为字符串并清理
            return self.encode_html(str(value))
    
    def encode_xml(self, value: str) -> str:
        """XML编码"""
        if not isinstance(value, str):
            value = str(value)
        
        # XML实体编码
        encoded = value
        
        # 转义XML特殊字符
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;',
        }
        
        for char, entity in replacements.items():
            encoded = encoded.replace(char, entity)
        
        # 处理控制字符
        encoded = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', encoded)
        
        return encoded
    
    def encode_for_context(self, value: Any, context: ContextType) -> EncodingResult:
        """根据上下文进行编码"""
        if not self._needs_encoding(value):
            return EncodingResult(
                encoded_value=value,
                encoding_applied=[],
                was_modified=False
            )
        
        encoding_applied = []
        encoded_value = value
        
        if context == ContextType.HTML_BODY:
            # HTML正文：HTML实体编码
            encoded_value = self.encode_html(str(value))
            encoding_applied.append(EncodingType.HTML)
            
        elif context == ContextType.HTML_ATTRIBUTE:
            # HTML属性：HTML属性编码
            encoded_value = self.encode_html_attribute(str(value))
            encoding_applied.append(EncodingType.HTML_ATTR)
            
        elif context == ContextType.HTML_STYLE:
            # HTML样式：CSS编码
            encoded_value = self.encode_css(str(value))
            encoding_applied.append(EncodingType.CSS)
            
        elif context == ContextType.SCRIPT:
            # JavaScript代码：JavaScript编码
            encoded_value = self.encode_javascript(str(value))
            encoding_applied.append(EncodingType.JS)
            
        elif context == ContextType.SCRIPT_ATTRIBUTE:
            # JavaScript属性：双重编码
            # 先HTML属性编码，再JavaScript编码
            html_encoded = self.encode_html_attribute(str(value))
            encoded_value = self.encode_javascript(html_encoded)
            encoding_applied.extend([EncodingType.HTML_ATTR, EncodingType.JS])
            
        elif context == ContextType.CSS:
            # CSS代码：CSS编码
            encoded_value = self.encode_css(str(value))
            encoding_applied.append(EncodingType.CSS)
            
        elif context == ContextType.URL:
            # URL：URL编码
            encoded_value = self.encode_url(str(value))
            encoding_applied.append(EncodingType.URL)
            
        elif context == ContextType.JSON:
            # JSON：安全序列化
            encoded_value = self.encode_json(value)
            encoding_applied.append(EncodingType.JSON)
            
        elif context == ContextType.XML:
            # XML：XML编码
            encoded_value = self.encode_xml(str(value))
            encoding_applied.append(EncodingType.XML)
            
        else:
            # 默认：HTML编码
            encoded_value = self.encode_html(str(value))
            encoding_applied.append(EncodingType.HTML)
        
        return EncodingResult(
            encoded_value=encoded_value,
            encoding_applied=encoding_applied,
            was_modified=True
        )
    
    def encode_response(self, data: Any, response_type: str = "json") -> Any:
        """编码API响应"""
        if response_type == "json":
            return self.encode_json(data)
        elif response_type == "html":
            # HTML响应：递归编码所有字符串
            return self._encode_html_response(data)
        elif response_type == "xml":
            # XML响应
            if isinstance(data, str):
                return self.encode_xml(data)
            else:
                # 转换为字符串再编码
                return self.encode_xml(json.dumps(data))
        else:
            # 默认：JSON
            return self.encode_json(data)
    
    def _encode_html_response(self, data: Any) -> Any:
        """递归编码HTML响应中的所有字符串"""
        if isinstance(data, str):
            return self.encode_html(data)
        elif isinstance(data, dict):
            return {k: self._encode_html_response(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._encode_html_response(item) for item in data]
        else:
            return data
    
    def sanitize_output(self, value: Any, allowed_html_tags: List[str] = None) -> str:
        """清理输出，允许安全的HTML标签"""
        if not isinstance(value, str):
            value = str(value)
        
        if allowed_html_tags is None:
            allowed_html_tags = ["b", "i", "u", "em", "strong", "code", "pre", "br", "p", "div", "span"]
        
        # 安全的HTML标签模式
        safe_tags_pattern = "|".join(allowed_html_tags)
        
        # 允许的标签及其属性
        allowed_attributes = {
            "a": ["href", "title", "target"],
            "img": ["src", "alt", "title", "width", "height"],
            "span": ["class", "style"],
            "div": ["class", "style"],
            "p": ["class", "style"],
        }
        
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(value, "html.parser")
            
            # 处理所有标签
            for tag in soup.find_all(True):
                # 删除不允许的标签
                if tag.name not in allowed_html_tags:
                    tag.unwrap()  # 移除标签但保留内容
                    continue
                
                # 清理属性
                if tag.name in allowed_attributes:
                    allowed_attrs = allowed_attributes[tag.name]
                    attrs = dict(tag.attrs)
                    for attr_name in list(attrs.keys()):
                        if attr_name not in allowed_attrs:
                            del tag[attr_name]
                        elif attr_name == "href" or attr_name == "src":
                            # 验证URL
                            url = attrs[attr_name]
                            if not self._is_safe_url(url):
                                del tag[attr_name]
                        elif attr_name == "style":
                            # 清理样式
                            tag[attr_name] = self._sanitize_style(attrs[attr_name])
                else:
                    # 不允许任何属性
                    tag.attrs = {}
            
            # 获取清理后的HTML
            sanitized = str(soup)
            
            # 最后进行HTML编码（但保留允许的标签）
            # 这是复杂的过程，这里简化处理
            return sanitized
            
        except ImportError:
            logger.warning("BeautifulSoup不可用，回退到基本HTML编码")
            return self.encode_html(value)
        except Exception as e:
            logger.error(f"HTML清理失败: {e}")
            return self.encode_html(value)
    
    def _is_safe_url(self, url: str) -> bool:
        """检查URL是否安全"""
        if not url:
            return False
        
        # 检查危险协议
        dangerous_protocols = ["javascript:", "vbscript:", "data:", "file:", "ftp:"]
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return False
        
        # 检查路径遍历
        if re.search(r'(\.\./|\.\.\\)', url):
            return False
        
        # 检查可疑字符
        if re.search(r'[\x00-\x1F\x7F]', url):
            return False
        
        return True
    
    def _sanitize_style(self, style: str) -> str:
        """清理CSS样式"""
        # 移除危险属性
        dangerous_properties = ["expression", "behavior", "binding", "javascript", "vbscript"]
        
        styles = style.split(';')
        safe_styles = []
        
        for style_part in styles:
            if not style_part.strip():
                continue
            
            # 分割属性和值
            if ':' in style_part:
                prop, value = style_part.split(':', 1)
                prop = prop.strip().lower()
                value = value.strip()
                
                # 检查是否危险
                is_dangerous = False
                for dangerous in dangerous_properties:
                    if dangerous in prop or dangerous in value:
                        is_dangerous = True
                        break
                
                if not is_dangerous:
                    safe_styles.append(f"{prop}: {value}")
        
        return '; '.join(safe_styles)


# 全局编码器实例
_default_encoder = None

def get_output_encoder() -> OutputEncoder:
    """获取全局输出编码器实例"""
    global _default_encoder
    if _default_encoder is None:
        _default_encoder = OutputEncoder()
    return _default_encoder


# 便捷函数
def encode_html(value: str) -> str:
    """HTML编码便捷函数"""
    encoder = get_output_encoder()
    return encoder.encode_html(value)


def encode_url(value: str) -> str:
    """URL编码便捷函数"""
    encoder = get_output_encoder()
    return encoder.encode_url(value)


def encode_json(value: Any) -> str:
    """JSON编码便捷函数"""
    encoder = get_output_encoder()
    return encoder.encode_json(value)


def encode_for_context(value: Any, context: ContextType) -> EncodingResult:
    """上下文编码便捷函数"""
    encoder = get_output_encoder()
    return encoder.encode_for_context(value, context)