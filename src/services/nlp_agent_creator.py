"""
NLP Agent Creator Service - Create agents from natural language descriptions
MVP Version: Basic keyword matching and rule-based configuration
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from src.services.agent_service import AgentService
from src.services.capability_checker import CapabilityChecker, CheckResult
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class AgentCreationResult:
    """Agent创建结果"""
    success: bool
    agent: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggestions: Optional[List[Dict[str, Any]]] = None


@dataclass
class RequirementParseResult:
    """需求解析结果"""
    capabilities: List[str]
    agent_type: str
    confidence: float
    parsed_requirements: Dict[str, Any]


class NLPAgentCreator:
    """NLP Agent创建器 - 从自然语言描述创建Agent (MVP版本)"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.capability_checker = CapabilityChecker()
        
        # MVP: 简单关键词到Tool/Skill的映射
        self.keyword_to_tools = {
            # 数据分析类
            "数据分析": ["data_analysis_tool", "pandas_tool", "numpy_tool"],
            "数据可视化": ["matplotlib_tool", "plotly_tool", "chart_generation"],
            "数据处理": ["data_processing", "data_cleaning", "etl_tool"],
            
            # 文件处理类
            "文件处理": ["file_handler", "csv_processor", "excel_processor"],
            "PDF处理": ["pdf_parser", "pdf_extractor"],
            "图像处理": ["image_processor", "opencv_tool"],
            
            # 网络相关
            "网页抓取": ["web_scraper", "requests_tool"],
            "API调用": ["api_client", "rest_client"],
            "网络请求": ["http_client", "requests_tool"],
            
            # 文本处理
            "文本分析": ["text_analyzer", "nlp_tool"],
            "情感分析": ["sentiment_analyzer", "nlp_engine"],
            "文本摘要": ["text_summarizer", "summarization_tool"],
            
            # 数据库
            "数据库操作": ["database_client", "sql_executor"],
            "数据查询": ["query_executor", "sql_tool"],
            
            # 机器学习
            "机器学习": ["ml_predictor", "model_training"],
            "预测分析": ["prediction_engine", "forecasting_tool"],
            
            # 通用工具
            "计算": ["calculator", "math_tool"],
            "转换": ["converter", "format_transformer"],
            "验证": ["validator", "checker_tool"],
        }
        
        self.keyword_to_skills = {
            # 技能映射
            "数据分析": ["data_analysis_skill", "statistical_analysis"],
            "数据可视化": ["visualization_skill", "chart_creation"],
            "报告生成": ["report_generation", "document_creation"],
            "自动化": ["automation_skill", "workflow_automation"],
            "监控": ["monitoring_skill", "alert_system"],
            "优化": ["optimization_skill", "performance_tuning"],
            "集成": ["integration_skill", "api_integration"],
        }
        
        self.agent_type_keywords = {
            "数据分析": ["数据分析", "数据", "分析", "统计", "报表"],
            "数据处理": ["数据处理", "清洗", "转换", "整理"],
            "文件处理": ["文件", "文档", "PDF", "Excel", "CSV"],
            "网络爬虫": ["爬虫", "抓取", "采集", "网页", "网站"],
            "API服务": ["API", "接口", "服务", "调用"],
            "文本处理": ["文本", "文字", "文档", "NLP", "自然语言"],
            "机器学习": ["机器学习", "AI", "模型", "预测", "训练"],
            "自动化": ["自动化", "自动", "机器人", "流程"],
            "监控告警": ["监控", "告警", "警报", "监测"],
        }
    
    async def create_agent_from_natural_language(self, description: str) -> AgentCreationResult:
        """
        从自然语言描述创建Agent (主入口点)
        
        Args:
            description: 自然语言描述，如"创建一个能分析CSV文件并生成图表的Agent"
            
        Returns:
            AgentCreationResult: 创建结果
        """
        try:
            logger.info(f"开始从自然语言创建Agent: '{description}'")
            
            # 1. 解析需求
            parse_result = self._parse_requirements(description)
            logger.info(f"需求解析结果: {parse_result}")
            
            # 2. 匹配Tools和Skills
            matched_config = self._match_capabilities(parse_result)
            logger.info(f"能力匹配结果: {matched_config}")
            
            # 3. 生成Agent配置
            agent_config = self._generate_agent_config(description, matched_config)
            logger.info(f"Agent配置: {agent_config}")
            
            # 4. 验证可行性
            validation_result = self._validate_config(matched_config)
            if not validation_result[0]:
                return AgentCreationResult(
                    success=False,
                    error=f"配置验证失败: {validation_result[1]}",
                    preview=agent_config
                )
            
            # 5. 创建Agent
            agent = self.agent_service.create_agent(agent_config)
            logger.info(f"Agent创建成功: {agent['id']}")
            
            return AgentCreationResult(
                success=True,
                agent=agent,
                preview=agent_config
            )
            
        except Exception as e:
            logger.error(f"创建Agent失败: {str(e)}", exc_info=True)
            return AgentCreationResult(
                success=False,
                error=f"创建过程中发生错误: {str(e)}"
            )
    
    async def parse_requirements_only(self, description: str) -> Dict[str, Any]:
        """
        仅解析需求，返回配置预览 (用于前端预览)
        
        Args:
            description: 自然语言描述
            
        Returns:
            配置预览信息
        """
        try:
            logger.info(f"解析需求: '{description}'")
            
            # 1. 解析需求
            parse_result = self._parse_requirements(description)
            
            # 2. 匹配Tools和Skills
            matched_config = self._match_capabilities(parse_result)
            
            # 3. 生成Agent配置
            agent_config = self._generate_agent_config(description, matched_config)
            
            # 4. 验证可行性
            is_valid, message = self._validate_config(matched_config)
            
            return {
                "success": True,
                "preview": agent_config,
                "validation": {
                    "is_valid": is_valid,
                    "message": message
                },
                "parse_result": parse_result.__dict__,
                "matched_config": matched_config
            }
            
        except Exception as e:
            logger.error(f"解析需求失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "preview": None
            }
    
    def _parse_requirements(self, description: str) -> RequirementParseResult:
        """
        解析自然语言需求 (MVP: 简单关键词匹配)
        
        Args:
            description: 自然语言描述
            
        Returns:
            RequirementParseResult: 解析结果
        """
        description_lower = description.lower()
        
        # 提取关键词
        capabilities = []
        for keyword, tools in self.keyword_to_tools.items():
            if keyword.lower() in description_lower:
                capabilities.append(keyword)
        
        # 确定Agent类型
        agent_type = "general"
        max_matches = 0
        for type_name, keywords in self.agent_type_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in description_lower)
            if matches > max_matches:
                max_matches = matches
                agent_type = type_name
        
        # 计算置信度 (简单算法)
        total_keywords = len(self.keyword_to_tools)
        matched_keywords = len(capabilities)
        confidence = matched_keywords / max(total_keywords, 1) * 0.7 + 0.3 if matched_keywords > 0 else 0.1
        
        return RequirementParseResult(
            capabilities=capabilities,
            agent_type=agent_type,
            confidence=min(confidence, 1.0),
            parsed_requirements={
                "description": description,
                "keywords": capabilities,
                "agent_type": agent_type
            }
        )
    
    def _match_capabilities(self, parse_result: RequirementParseResult) -> Dict[str, Any]:
        """
        匹配Tools和Skills (MVP: 基于关键词映射)
        
        Args:
            parse_result: 解析结果
            
        Returns:
            匹配的配置
        """
        matched_tools = []
        matched_skills = []
        
        # 匹配Tools
        for capability in parse_result.capabilities:
            if capability in self.keyword_to_tools:
                matched_tools.extend(self.keyword_to_tools[capability])
        
        # 匹配Skills
        for capability in parse_result.capabilities:
            if capability in self.keyword_to_skills:
                matched_skills.extend(self.keyword_to_skills[capability])
        
        # 去重
        matched_tools = list(set(matched_tools))
        matched_skills = list(set(matched_skills))
        
        # 如果没有匹配到，添加默认Tools/Skills
        if not matched_tools and parse_result.capabilities:
            matched_tools = ["general_tool", "basic_processor"]
        
        if not matched_skills:
            matched_skills = ["basic_skill", "general_processing"]
        
        return {
            "tools": matched_tools,
            "skills": matched_skills,
            "agent_type": parse_result.agent_type,
            "confidence": parse_result.confidence
        }
    
    def _generate_agent_config(self, description: str, matched_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成Agent配置
        
        Args:
            description: 原始描述
            matched_config: 匹配的配置
            
        Returns:
            Agent配置
        """
        # 生成名称
        name = f"Auto-Agent-{self._generate_simple_name(description)}"
        
        return {
            "name": name,
            "type": matched_config["agent_type"],
            "description": description,
            "tools": matched_config["tools"],
            "skills": matched_config["skills"],
            "config": {
                "auto_created": True,
                "creation_method": "natural_language",
                "confidence": matched_config["confidence"],
                "version": "1.0"
            }
        }
    
    def _validate_config(self, matched_config: Dict[str, Any], strict: bool = False) -> Tuple[bool, str]:
        """
        验证配置可行性
        
        Args:
            matched_config: 匹配的配置
            strict: 是否严格模式 (默认False, 只警告不失败)
            
        Returns:
            (是否可行, 消息)
        """
        try:
            warnings = []
            
            # 检查Tools
            tool_result = self.capability_checker.check_tools(matched_config["tools"])
            
            # 检查Skills
            skill_result = self.capability_checker.check_skills(matched_config["skills"])
            
            if not tool_result.satisfied:
                msg = f"Tools不可用: {', '.join(tool_result.missing)}"
                if strict:
                    return False, msg
                warnings.append(msg)
            
            if not skill_result.satisfied:
                msg = f"Skills不可用: {', '.join(skill_result.missing)}"
                if strict:
                    return False, msg
                warnings.append(msg)
            
            if warnings:
                return True, "配置验证通过 (有警告: " + "; ".join(warnings) + ")"
            
            return True, "配置验证通过"
            
        except Exception as e:
            return False, f"验证过程中发生错误: {str(e)}"
    
    def _generate_simple_name(self, description: str) -> str:
        """
        从描述生成简单名称
        
        Args:
            description: 描述文本
            
        Returns:
            简单名称
        """
        # 提取前3个有意义的词
        words = re.findall(r'\b\w+\b', description)
        meaningful_words = [w for w in words if len(w) > 2][:3]
        
        if meaningful_words:
            return "-".join(meaningful_words).lower()
        else:
            return "custom-agent"
    
    def get_available_capabilities(self) -> Dict[str, Any]:
        """
        获取系统可用的能力列表 (用于前端展示)
        
        Returns:
            能力列表
        """
        try:
            # 获取所有Tools
            all_tools = self.capability_checker.db.get_all_tools(status='active')
            all_skills = self.capability_checker.db.get_all_skills(status='active')
            
            # 按类别分组
            tool_categories = {}
            for tool in all_tools:
                category = tool.get('category', 'general')
                if category not in tool_categories:
                    tool_categories[category] = []
                tool_categories[category].append({
                    "id": tool['id'],
                    "name": tool['name'],
                    "description": tool.get('description', '')
                })
            
            skill_categories = {}
            for skill in all_skills:
                category = skill.get('category', 'general')
                if category not in skill_categories:
                    skill_categories[category] = []
                skill_categories[category].append({
                    "id": skill['id'],
                    "name": skill['name'],
                    "description": skill.get('description', '')
                })
            
            return {
                "tools": tool_categories,
                "skills": skill_categories,
                "keyword_mappings": {
                    "tools": list(self.keyword_to_tools.keys()),
                    "skills": list(self.keyword_to_skills.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"获取能力列表失败: {str(e)}")
            return {"tools": {}, "skills": {}, "keyword_mappings": {"tools": [], "skills": []}}


# 创建全局实例
_nlp_agent_creator_instance = None

def get_nlp_agent_creator() -> NLPAgentCreator:
    """获取NLPAgentCreator实例 (单例模式)"""
    global _nlp_agent_creator_instance
    if _nlp_agent_creator_instance is None:
        _nlp_agent_creator_instance = NLPAgentCreator()
    return _nlp_agent_creator_instance