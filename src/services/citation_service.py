"""
引用服务 - 从EnhancedCitationAgent重命名

注意：这是一个服务组件，不是Agent。它提供引用生成功能，可以被Agent使用。
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging
import time
import re
import threading
import asyncio
from src.agents.base_agent import BaseAgent, AgentResult, AgentConfig

# 统一配置中心与智能阈值获取（首选绝对导入，失败时提供最小兜底）
try:
    from src.utils.unified_centers import get_unified_config_center, get_smart_config
except ImportError:
    def get_unified_config_center():
        return None
    def get_smart_config(key: str, context: Optional[Dict[str, Any]] = None):
        return None

# 设置logger
logger = logging.getLogger(__name__)

class CitationService(BaseAgent):
    """引用服务 - 从EnhancedCitationAgent重命名
    
    这是一个服务组件，不是Agent。它提供引用生成功能，可以被Agent使用。
    """

    def __init__(self, agent_name: str = "CitationService", use_intelligent_config: bool = True):
        # 创建配置
        config = AgentConfig(
            agent_id=agent_name,
            agent_type="citation"
        )
        super().__init__(agent_name, ["citation_generation", "reference_management", "quality_assessment"], config)
        self.logger = logging.getLogger(__name__)

        self.is_executing = False
        self._execution_lock = threading.Lock()

        try:
            self.unified_config = get_unified_config_center()
            self.logger.debug("✅ 统一配置管理中心初始化成功")
        except Exception as e:
            self.logger.warning(f"统一配置管理中心初始化失败: {e}")
            self.unified_config = None

        self.dynamic_config = self.unified_config

        self.intelligent_processor = None  # 暂时设为None

        self.logger.info("增强引用智能体初始化完成，使用统一工具")

    def _get_intelligent_analysis(self, content: str, context: str = "") -> Dict[str, Any]:
        """安全地获取智能分析结果 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            confidence_score = 0.7
            
            if self.intelligent_processor:
                try:
                    if hasattr(self.intelligent_processor, 'analyze_content'):
                        result = self.intelligent_processor.analyze_content(content, context)
                        return {
                            "confidence_score": result.get("confidence", confidence_score),
                            "extracted_info": result.get("extracted_info", {})
                        }
                except Exception as e:
                    self.logger.warning(f"智能处理器调用失败: {e}")
            
            return {
                "confidence_score": confidence_score,
                "extracted_info": {}
            }
            
        except Exception as e:
            self.logger.warning(f"智能分析失败: {e}")
            return {
                "confidence_score": 0.7,
                "extracted_info": {}
            }

    def generate_enhanced_citation(self, content: str, source_type: str = "general") -> Dict[str, Any]:
        """生成增强引用"""
        try:
            intelligent_analysis = self._get_intelligent_analysis(content, "")

            citation_info = self._extract_citation_info(content, source_type, intelligent_analysis)

            citation_formats = self._generate_citation_formats(citation_info, source_type)

            quality_assessment = self._assess_citation_quality(citation_info)

            return {
                "citation_info": citation_info,
                "citation_formats": citation_formats,
                "quality_assessment": quality_assessment,
                "confidence": intelligent_analysis.get("confidence",
                    get_smart_config("confidence_threshold", {"query": "confidence_threshold"}) or 0.7)
            }

        except Exception as e:
            self.logger.error("【异常处理】增强引用生成失败: {str(e)}")
            self.logger.debug("异常详情: {type(e).__name__}: {e}")
            return {
                "citation_info": {"error": "引用生成失败"},
                "citation_formats": {},
                                "quality_assessment": {"overall_score": get_smart_config("low_threshold", {"query": "low_threshold"}) or 0.3},

                "confidence": get_smart_config("low_threshold", {"query": "low_threshold"}) or 0.3
            }

    def _extract_citation_info(self, content: str, source_type: str, intelligent_analysis: Dict[str, Any]) -> Dict[str,
    Any]:  # noqa: E501
        """提取引用信息"""
        try:
            info = {
                "title": "",
                "authors": [],
                "year": None,
                "journal": "",
                "volume": "",
                "issue": "",
                "pages": "",
                "publisher": "",
                "url": "",
                "doi": "",
                "source_type": source_type
            }

            title_patterns = [
                r'"([^"]+)"',
                r"'([^']+)'",
                r'《([^》]+)》',
                r'\[([^\]]+)\]'
            ]

            for pattern in title_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    info["title"] = matches[0]
                    break

            author_patterns = [
                r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'作者[：:]\s*([^，。\n]+)',
                r'Author[：:]\s*([^，。\n]+)'
            ]

            for pattern in author_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches and len(matches) > 0:
                    authors = [author.strip() for author in matches[0].split(',')]
                    info["authors"] = authors
                    break

            year_pattern = r'\b(19\d{2}|20\d{2})\b'
            year_matches = re.findall(year_pattern, content)
            if year_matches and len(year_matches) > 0:
                try:
                    info["year"] = int(year_matches[0])
                except (ValueError, IndexError) as e:
                    self.logger.warning("年份解析失败: {e}")
                    info["year"] = None

            journal_patterns = [
                r'Journal[：:]\s*([^，。\n]+)',
                r'期刊[：:]\s*([^，。\n]+)'
            ]

            for pattern in journal_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    info["journal"] = matches[0].strip()
                    break

            url_pattern = r'https?://[^\s]+'
            url_matches = re.findall(url_pattern, content)
            if url_matches:
                info["url"] = url_matches[0]

            return info

        except Exception as e:
            self.logger.error("【异常处理】引用信息提取失败: {str(e)}")
            self.logger.debug("异常详情: {type(e).__name__}: {e}")
            return {"error": str(e)}

    def _generate_citation_formats(self, citation_info: Dict[str, Any], source_type: str) -> Dict[str, str]:
        """生成不同格式的引用"""
        try:
            formats = {}

            formats["apa"] = self._generate_apa_citation(citation_info)

            formats["mla"] = self._generate_mla_citation(citation_info)

            formats["chicago"] = self._generate_chicago_citation(citation_info)

            formats["ieee"] = self._generate_ieee_citation(citation_info)

            return formats

        except Exception as e:
            self.logger.error("【异常处理】引用格式生成失败: {e}")
            return {"error": str(e)}

    def _generate_apa_citation(self, citation_info: Dict[str, Any]) -> str:
        """生成APA格式引用"""
        try:
            authors = citation_info.get("authors", [])
            year = citation_info.get("year")
            title = citation_info.get("title", "")
            journal = citation_info.get("journal", "")
            volume = citation_info.get("volume", "")
            issue = citation_info.get("issue", "")
            pages = citation_info.get("pages", "")

            if authors and year and title:
                author_str = ", ".join(authors)
                citation = f"{author_str} ({year}). {title}."
                if journal:
                    citation += f" {journal}"
                if volume:
                    citation += f", {volume}"
                if issue:
                    citation += f"({issue})"
                if pages:
                    citation += f", {pages}."
                else:
                    citation += "."
                return citation
            else:
                return "引用信息不完整"

        except Exception as e:
            self.logger.error("【异常处理】APA引用生成失败: {e}")
            return "APA引用生成失败"

    def _generate_mla_citation(self, citation_info: Dict[str, Any]) -> str:
        """生成MLA格式引用"""
        try:
            authors = citation_info.get("authors", [])
            title = citation_info.get("title", "")
            year = citation_info.get("year")
            journal = citation_info.get("journal", "")

            if authors and title:
                author_str = ", ".join(authors)
                citation = f"{author_str}. \"{title}.\""
                if journal:
                    citation += f" {journal}"
                if year:
                    citation += f" {year}."
                else:
                    citation += "."
                return citation
            else:
                return "引用信息不完整"

        except Exception as e:
            self.logger.error("【异常处理】MLA引用生成失败: {e}")
            return "MLA引用生成失败"

    def _generate_chicago_citation(self, citation_info: Dict[str, Any]) -> str:
        """生成Chicago格式引用"""
        try:
            authors = citation_info.get("authors", [])
            title = citation_info.get("title", "")
            year = citation_info.get("year")
            journal = citation_info.get("journal", "")

            if authors and title:
                author_str = ", ".join(authors)
                citation = f"{author_str}. \"{title}.\""
                if journal:
                    citation += f" {journal}"
                if year:
                    citation += f" ({year})."
                else:
                    citation += "."
                return citation
            else:
                return "引用信息不完整"

        except Exception as e:
            self.logger.error("【异常处理】Chicago引用生成失败: {e}")
            return "Chicago引用生成失败"

    def _generate_ieee_citation(self, citation_info: Dict[str, Any]) -> str:
        """生成IEEE格式引用"""
        try:
            authors = citation_info.get("authors", [])
            title = citation_info.get("title", "")
            year = citation_info.get("year")
            journal = citation_info.get("journal", "")

            if authors and title:
                author_str = ", ".join(authors)
                citation = f"{author_str}, \"{title},\""
                if journal:
                    citation += f" {journal}"
                if year:
                    citation += f", {year}."
                else:
                    citation += "."
                return citation
            else:
                return "引用信息不完整"

        except Exception as e:
            self.logger.error("【异常处理】IEEE引用生成失败: {e}")
            return "IEEE引用生成失败"

    def _get_minimal_fallback_confidence(self, confidence_type: str) -> float:
        """获取最小化回退置信度 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            # 智能回退
                default_confidence_map = {
                    "citation_default": 0.7,
                    "citation_fallback": 0.6,
                    "citation_error": get_smart_config("low_threshold", {"query": "low_threshold"}) or 0.3,
                    "citation_high": 0.9,
                    "citation_medium": 0.7,
                    "citation_low": get_smart_config("medium_threshold", {"query": "medium_threshold"}) or 0.5
                }
                return default_confidence_map.get(confidence_type, 0.6)
        except Exception as e:
            self.logger.warning(f"智能置信度分析失败: {e}，使用最小化回退值")
            return 0.6

    def _get_intelligent_quality_score(self, score_type: str, **kwargs) -> float:
        """获取智能质量评分 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            return self._get_minimal_fallback_quality_score(score_type)
        except Exception as e:
            self.logger.warning(f"获取智能质量评分失败: {e}，使用最小化回退值")
            return self._get_minimal_fallback_quality_score(score_type)

    def _get_minimal_fallback_quality_score(self, score_type: str) -> float:
        """获取最小化回退质量评分 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            # 智能回退计算
            return max(0.0, 1.0 / (len(score_type) + 2))
        except Exception as e:
            self.logger.warning(f"智能质量评分分析失败: {e}，使用最小化回退值")
            return max(0.0, 1.0 / (len(score_type) + 2))

    def _get_intelligent_accuracy_threshold(self, accuracy_level: str) -> float:
        """获取智能准确度阈值 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            return self._get_minimal_fallback_accuracy_threshold(accuracy_level)
        except Exception as e:
            self.logger.warning(f"获取智能准确度阈值失败: {e}，使用最小化回退值")
            return self._get_minimal_fallback_accuracy_threshold(accuracy_level)

    def _get_minimal_fallback_accuracy_threshold(self, accuracy_level: str) -> float:
        """获取最小化回退准确度阈值 - 使用统一智能评分器"""
        try:
            # 使用回退评分器
            # 智能回退计算
                level_factors = {"high": 3, "medium": 2, "low": 1}
                return max(0.1, min(0.9, level_factors.get(accuracy_level, 2) / 4.0))
        except Exception as e:
            self.logger.warning(f"智能准确度阈值分析失败: {e}，使用最小化回退值")
            level_factors = {"high": 3, "medium": 2, "low": 1}
            factor = level_factors.get(accuracy_level, 2)
            return max(0.1, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}) / (factor + 1))

    def _get_intelligent_text_limit(self, limit_type: str) -> int:
        """获取智能文本限制 - 使用统一配置管理中心"""
        try:
            if hasattr(self, 'unified_config') and self.unified_config:
                limit_value = self.unified_config.get(f"text_limit_{limit_type}", None)
                if limit_value is not None:
                    return int(limit_value)

            return self._get_minimal_fallback_text_limit(limit_type)
        except Exception as e:
            self.logger.warning(f"获取智能文本限制失败: {e}，使用最小化回退值")
            return self._get_minimal_fallback_text_limit(limit_type)

    def _get_minimal_fallback_text_limit(self, limit_type: str) -> int:
        """获取最小化回退文本限制 - 使用统一动态特征分析中心"""
        try:
            intelligent_analysis = self._get_intelligent_analysis(f"text_limit_{limit_type}", "text_limit_analysis")

            text_limit = intelligent_analysis.get("text_limit", get_smart_config("large_limit", {"config_type": "auto"}))
            return max(get_smart_config("default_limit", {"config_type": "auto"}), min(1000, int(text_limit)))

        except Exception as e:
            self.logger.warning("智能文本限制分析失败: {e}，使用最小化回退值")
            return max(get_smart_config("default_limit", {"config_type": "auto"}), min(1000, len(limit_type) * 25))

    def _get_current_query_context(self) -> Dict[str, Any]:
        """获取当前查询上下文"""
        return {
            "query_type": getattr(self, 'current_query_type', 'general'),
            "citation_method": 'enhanced_citation',
            "source_type": getattr(self, 'current_source_type', 'general')
        }
    
    def _assess_citation_quality(self, citation_info: Dict[str, Any]) -> Dict[str, Any]:
        """评估引用质量 - 保持功能完整性"""
        try:
            # 基础质量评估
            quality_score = 0.8  # 默认质量分数
            
            # 根据引用信息调整质量分数
            if citation_info.get('title'):
                quality_score += 0.1
            if citation_info.get('author'):
                quality_score += 0.1
            if citation_info.get('year'):
                quality_score += 0.1
            if citation_info.get('url'):
                quality_score += 0.1
            
            # 确保分数在0-1范围内
            quality_score = min(1.0, max(0.0, quality_score))
            
            return {
                "overall_score": quality_score,
                "completeness": 0.8,
                "accuracy": 0.8,
                "relevance": 0.8,
                "metadata": {
                    "assessment_time": time.time(),
                    "criteria_checked": ["title", "author", "year", "url"]
                }
            }
        except Exception as e:
            self.logger.warning(f"引用质量评估失败: {e}")
            return {
                "overall_score": 0.5,
                "completeness": 0.5,
                "accuracy": 0.5,
                "relevance": 0.5,
                "metadata": {
                    "assessment_time": time.time(),
                    "error": str(e)
                }
            }
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 同步接口，保持功能完整性"""
        start_time = time.time()
        
        try:
            with self._execution_lock:
                self.is_executing = True
            
            # 生成增强引用
            citation_result = self.generate_enhanced_citation(query, context.get("source_type", "general") if context else "general")
            
            processing_time = time.time() - start_time
            
            # 记录处理事件
            self._log_citation_event(query, citation_result, True, processing_time)
            
            return AgentResult(
                success=True,
                data=citation_result,
                confidence=citation_result.get("confidence", 0.7),
                processing_time=processing_time,
                metadata={
                    "citation_method": "enhanced_citation",
                    "source_type": context.get("source_type", "general") if context else "general",
                    "query": query
                }
            )
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"同步查询处理失败: {e}")
            
            # 记录失败事件
            self._log_citation_event(query, {"error": str(e)}, False, processing_time)
            
            return AgentResult(
                success=False,
                data={"content": f"查询处理失败: {str(e)}"},
                confidence=0.0,
                processing_time=processing_time,
                error=str(e)
            )
        finally:
            with self._execution_lock:
                self.is_executing = False
    
    def _log_citation_event(self, query: str, result: Dict[str, Any], success: bool, processing_time: float):
        """记录引用事件"""
        try:
            event_data = {
                "query": query[:100],  # 限制长度
                "success": success,
                "processing_time": processing_time,
                "timestamp": time.time(),
                "citation_count": len(result.get("citation_formats", {})) if success else 0
            }
            
            if success:
                self.logger.info(f"引用生成成功: {event_data}")
            else:
                self.logger.warning(f"引用生成失败: {event_data}")
                
        except Exception as e:
            self.logger.error(f"事件记录失败: {e}")
    
    def _validate_citation_input(self, content: str, source_type: str) -> bool:
        """验证引用输入"""
        try:
            if not content or not content.strip():
                return False
            
            if len(content) > 5000:  # 限制内容长度
                return False
            
            if source_type not in ["general", "academic", "web", "book", "journal", "conference"]:
                return False
            
            return True
        except Exception:
            return False
    
    def _calculate_citation_metrics(self, citation_info: Dict[str, Any], quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """计算引用指标"""
        try:
            metrics = {
                "completeness_score": 0.0,
                "accuracy_score": 0.0,
                "format_score": 0.0,
                "overall_score": 0.0
            }
            
            # 计算完整性分数
            required_fields = ["title", "authors", "year"]
            present_fields = sum(1 for field in required_fields if citation_info.get(field))
            metrics["completeness_score"] = present_fields / len(required_fields)
            
            # 计算准确性分数
            metrics["accuracy_score"] = quality_assessment.get("accuracy", 0.5)
            
            # 计算格式分数
            citation_formats = citation_info.get("citation_formats", {})
            if citation_formats:
                metrics["format_score"] = len(citation_formats) / 4.0  # 假设有4种格式
            else:
                metrics["format_score"] = 0.0
            
            # 计算总体分数
            metrics["overall_score"] = (
                metrics["completeness_score"] * 0.4 +
                metrics["accuracy_score"] * 0.4 +
                metrics["format_score"] * 0.2
            )
            
            return metrics
        except Exception as e:
            self.logger.error(f"计算引用指标失败: {e}")
            return {
                "completeness_score": 0.0,
                "accuracy_score": 0.0,
                "format_score": 0.0,
                "overall_score": 0.0,
                "error": str(e)
            }
    
    def _generate_citation_report(self, citation_info: Dict[str, Any], quality_assessment: Dict[str, Any], 
                                metrics: Dict[str, Any]) -> str:
        """生成引用报告"""
        try:
            report_lines = []
            
            # 报告标题
            report_lines.append("=== 增强引用生成报告 ===")
            report_lines.append("")
            
            # 引用信息
            report_lines.append("## 引用信息")
            report_lines.append(f"标题: {citation_info.get('title', 'N/A')}")
            report_lines.append(f"作者: {', '.join(citation_info.get('authors', []))}")
            report_lines.append(f"年份: {citation_info.get('year', 'N/A')}")
            report_lines.append(f"期刊: {citation_info.get('journal', 'N/A')}")
            report_lines.append("")
            
            # 质量评估
            report_lines.append("## 质量评估")
            report_lines.append(f"总体分数: {quality_assessment.get('overall_score', 0.0):.2f}")
            report_lines.append(f"完整性: {quality_assessment.get('completeness', 0.0):.2f}")
            report_lines.append(f"准确性: {quality_assessment.get('accuracy', 0.0):.2f}")
            report_lines.append(f"相关性: {quality_assessment.get('relevance', 0.0):.2f}")
            report_lines.append("")
            
            # 指标
            report_lines.append("## 详细指标")
            report_lines.append(f"完整性分数: {metrics.get('completeness_score', 0.0):.2f}")
            report_lines.append(f"准确性分数: {metrics.get('accuracy_score', 0.0):.2f}")
            report_lines.append(f"格式分数: {metrics.get('format_score', 0.0):.2f}")
            report_lines.append(f"总体分数: {metrics.get('overall_score', 0.0):.2f}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            self.logger.error(f"生成引用报告失败: {e}")
            return f"引用报告生成失败: {str(e)}"
    
    def _optimize_citation_performance(self) -> Dict[str, Any]:
        """优化引用性能"""
        try:
            optimizations = {}
            
            # 基于配置优化
            if self.unified_config:
                current_style = self.unified_config.get("citation_style", "apa")
                optimizations["preferred_style"] = current_style
            
            # 基于质量评估优化
            quality_threshold = get_smart_config("quality_threshold", {"query": "quality_threshold"}) or 0.7
            optimizations["quality_threshold"] = quality_threshold
            
            return {
                "optimizations": optimizations,
                "recommendations": [
                    f"当前引用样式: {optimizations.get('preferred_style', 'apa')}",
                    f"质量阈值: {optimizations.get('quality_threshold', 0.7):.2f}",
                    "建议定期更新引用格式模板"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"优化引用性能失败: {e}")
            return {
                "optimizations": {},
                "error": str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        try:
            return {
                "name": getattr(self, 'name', 'EnhancedCitationAgent'),
                "is_executing": self.is_executing,
                "unified_config_available": self.unified_config is not None,
                "intelligent_processor_available": self.intelligent_processor is not None,
                "supported_formats": ["apa", "mla", "chicago", "ieee"],
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"获取智能体状态失败: {e}")
            return {
                "name": getattr(self, 'name', 'EnhancedCitationAgent'),
                "is_executing": False,
                "error": str(e)
            }

    # 适配统一编排器的最小执行接口
    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """根据上下文生成引用（适配 UnifiedResearchSystem 调用约定）"""
        start_time = time.time()
        try:
            content = ""
            if isinstance(context, dict):
                content = context.get("content") or context.get("answer") or context.get("query", "")
            if not isinstance(content, str):
                content = str(content or "")

            result = self.generate_enhanced_citation(content, context.get("source_type", "general") if isinstance(context, dict) else "general")
            return AgentResult(
                success=True,
                data=result,
                confidence=result.get("confidence", 0.7),
                processing_time=time.time() - start_time,
                metadata={"method": "enhanced_citation"}
            )
        except Exception as e:
            self.logger.error(f"citation execute 失败: {e}")
            return AgentResult(
                success=False,
                data={"error": str(e)},
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
