#!/usr/bin/env python3
"""
营销Agent - 专业市场营销角色
负责市场推广、品牌建设、用户增长
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .professional_agent_base import ProfessionalAgentBase, ProfessionalAgentConfig

logger = logging.getLogger(__name__)


class MarketingAgent(ProfessionalAgentBase):
    """营销Agent - 专业市场营销实现角色"""
    
    def __init__(
        self,
        agent_id: str,
        specialization: str = "数字营销",
        config: Optional[ProfessionalAgentConfig] = None
    ):
        """初始化营销Agent
        
        Args:
            agent_id: Agent唯一标识符
            specialization: 专业领域细分（如：数字营销、内容营销、社交媒体营销、增长营销等）
            config: 配置对象（可选）
        """
        # 默认配置
        default_role_name = "营销专家"
        default_role_name_en = "Marketing Specialist"
        default_domain_expertise = f"市场营销 - {specialization}"
        default_expertise_description = f"""资深营销专家，专注于{specialization}领域的市场推广和用户增长。

核心职责：
1. 市场策略制定：基于市场分析制定有效的营销策略和推广计划
2. 品牌建设：建立和维护品牌形象，提升品牌知名度和美誉度
3. 用户增长：设计和执行用户增长策略，提高用户获取和留存
4. 内容营销：策划和制作高质量内容，吸引目标用户
5. 渠道管理：管理和优化营销渠道，提高营销ROI
6. 数据分析：分析营销数据，优化营销效果和策略

专业能力：
- 精通市场营销理论和方法（4P、SWOT、AIDA模型等）
- 熟悉数字营销工具和平台（Google Analytics、社交媒体广告等）
- 掌握内容创作和文案写作技巧
- 了解用户心理学和行为经济学
- 具备数据分析和营销优化能力
"""

        # 根据specialization调整能力
        capabilities = [
            "市场策略",
            "品牌建设",
            "用户增长",
            "内容营销",
            "渠道管理",
            "数据分析",
            f"{specialization}",
            "营销自动化"
        ]
        
        # 营销专家可用的工具
        tools = [
            "market_research",
            "campaign_planner",
            "content_generator",
            "social_media_manager",
            "seo_optimizer",
            "analytics_dashboard",
            "ab_testing",
            "customer_segmentation"
        ]
        
        if config is None:
            config = ProfessionalAgentConfig(
                agent_id=agent_id,
                role_name=default_role_name,
                role_name_en=default_role_name_en,
                domain_expertise=default_domain_expertise,
                expertise_description=default_expertise_description,
                capabilities=capabilities,
                tools=tools,
                collaboration_style="strategic",
                capability_level=0.85,
                language="zh-CN"
            )
        
        super().__init__(
            agent_id=agent_id,
            role_name=config.role_name,
            role_name_en=config.role_name_en,
            domain_expertise=config.domain_expertise,
            expertise_description=config.expertise_description,
            config=config
        )
        
        self.specialization = specialization
        self.target_audience: str = "大众用户"  # 目标受众
        
        logger.info(f"初始化营销Agent: {agent_id}, 专业领域: {specialization}")
    
    def set_target_audience(self, target_audience: str) -> None:
        """设置目标受众
        
        Args:
            target_audience: 目标受众描述
        """
        self.target_audience = target_audience
        logger.info(f"营销Agent {self.agent_id} 设置目标受众: {target_audience}")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行营销任务
        
        Args:
            task: 任务描述
            
        Returns:
            执行结果
        """
        task_name = task.get("task_name", "未命名任务")
        task_type = task.get("task_type", "general")
        
        logger.info(f"营销Agent {self.agent_id} 开始执行任务: {task_name}")
        
        # 根据任务类型执行不同的营销逻辑
        result = {
            "agent_id": self.agent_id,
            "role_name": self.role_name,
            "role_name_en": self.role_name_en,
            "task_id": task.get("task_id", "unknown"),
            "task_name": task_name,
            "task_type": task_type,
            "status": "in_progress",
            "output": None,
            "metrics": {},
            "completion_time": None,
            "marketing_details": {},
            "recommendations": []
        }
        
        try:
            if task_type == "market_research":
                result = await self._execute_market_research(task, result)
            elif task_type == "campaign_planning":
                result = await self._execute_campaign_planning(task, result)
            elif task_type == "content_strategy":
                result = await self._execute_content_strategy(task, result)
            elif task_type == "growth_strategy":
                result = await self._execute_growth_strategy(task, result)
            elif task_type == "brand_strategy":
                result = await self._execute_brand_strategy(task, result)
            else:
                result = await self._execute_general_marketing_task(task, result)
            
            result["status"] = "completed"
            result["completion_time"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"营销Agent {self.agent_id} 执行任务失败: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["completion_time"] = datetime.now().isoformat()
        
        # 存储任务结果
        self.store_deliverable(f"task_result_{task.get('task_id', 'unknown')}", result)
        
        return result
    
    async def _execute_market_research(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场研究任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        research_objectives = task.get("research_objectives", [])
        market_segment = task.get("market_segment", "general")
        
        logger.info(f"执行市场研究任务，市场细分: {market_segment}")
        
        # 市场研究分析
        market_research = {
            "competitive_analysis": self.reasoning.analyze(
                query=f"分析市场竞争格局，目标市场: {market_segment}",
                context=f"研究目标: {json.dumps(research_objectives, ensure_ascii=False)}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "customer_insights": self.reasoning.analyze(
                query=f"分析目标客户洞察，目标受众: {self.target_audience}",
                context="市场竞争分析已完成",
                reasoning_type=self.reasoning.get_reasoning_type("INSIGHTFUL")
            ),
            "market_trends": self.reasoning.analyze(
                query=f"分析市场趋势和机会",
                context="客户洞察已分析",
                reasoning_type=self.reasoning.get_reasoning_type("STRATEGIC")
            ),
            "swot_analysis": self.reasoning.analyze(
                query=f"进行SWOT分析",
                context="市场趋势已分析",
                reasoning_type=self.reasoning.get_reasoning_type("CRITICAL")
            )
        }
        
        # 生成市场研究报告示例
        research_report = f"""
# 市场研究报告 - {task.get('product_name', '产品')}

## 研究目标
{chr(10).join(f"- {obj}" for obj in research_objectives)}

## 市场概况
- 市场规模: {task.get('market_size', '100亿人民币')}
- 增长率: {task.get('growth_rate', '15%年增长率')}
- 市场细分: {market_segment}
- 竞争强度: {task.get('competition_intensity', '中等')}

## 目标客户分析
- 目标受众: {self.target_audience}
- 客户画像: {task.get('customer_persona', '25-40岁科技爱好者')}
- 需求痛点: {task.get('customer_pain_points', '效率低、成本高、体验差')}
- 购买行为: {task.get('purchase_behavior', '在线研究、口碑影响、价格敏感')}

## 竞争分析
### 主要竞争对手
1. 竞争对手A: {task.get('competitor_a', '市场领导者')}
   - 优势: {task.get('competitor_a_strengths', '品牌知名度高、功能完善')}
   - 劣势: {task.get('competitor_a_weaknesses', '价格高、用户体验一般')}

2. 竞争对手B: {task.get('competitor_b', '创新挑战者')}
   - 优势: {task.get('competitor_b_strengths', '技术创新、用户体验好')}
   - 劣势: {task.get('competitor_b_weaknesses', '市场份额小、资源有限')}

## 市场机会
1. 蓝海市场机会: {task.get('blue_ocean_opportunity', '未满足的细分需求')}
2. 技术趋势机会: {task.get('tech_trend_opportunity', '人工智能、大数据应用')}
3. 商业模式机会: {task.get('business_model_opportunity', '订阅制、平台模式')}

## 研究结论
基于市场研究，提出以下关键结论和建议...
        """
        
        base_result["output"] = {
            "market_research": market_research,
            "research_report": research_report,
            "key_metrics": {
                "market_size_estimate": task.get("market_size", "100亿人民币"),
                "growth_rate_estimate": task.get("growth_rate", "15%"),
                "target_audience_size": task.get("target_audience_size", "500万用户"),
                "market_share_opportunity": task.get("market_share_opportunity", "10%")
            },
            "research_methods": [
                "二手资料研究",
                "竞争对手分析",
                "用户访谈",
                "问卷调查",
                "数据分析",
                "趋势分析"
            ]
        }
        
        base_result["marketing_details"] = {
            "research_depth": "深入的市场分析",
            "data_sources": ["行业报告", "竞争对手网站", "用户反馈", "社交媒体数据"],
            "validation_methods": ["三角验证", "专家评审", "数据交叉验证"]
        }
        
        base_result["recommendations"] = [
            "定期进行市场研究",
            "建立市场情报系统",
            "跟踪竞争对手动态",
            "验证市场假设"
        ]
        
        return base_result
    
    async def _execute_campaign_planning(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行营销活动策划任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        campaign_goals = task.get("campaign_goals", [])
        campaign_budget = task.get("campaign_budget", 100000)
        campaign_duration = task.get("campaign_duration", "30天")
        
        logger.info(f"执行营销活动策划任务，预算: {campaign_budget}, 时长: {campaign_duration}")
        
        # 营销活动策划
        campaign_planning = {
            "goal_setting": self.reasoning.analyze(
                query=f"设定营销活动目标: {json.dumps(campaign_goals, ensure_ascii=False)}",
                context=f"预算: {campaign_budget}, 时长: {campaign_duration}",
                reasoning_type=self.reasoning.get_reasoning_type("PLANNING")
            ),
            "strategy_development": self.reasoning.generate(
                query=f"制定营销活动策略",
                context="活动目标已设定",
                reasoning_type=self.reasoning.get_reasoning_type("STRATEGIC")
            ),
            "channel_selection": self.reasoning.generate(
                query=f"选择营销渠道",
                context="活动策略已制定",
                reasoning_type=self.reasoning.get_reasoning_type("TACTICAL")
            ),
            "roi_forecast": self.reasoning.analyze(
                query=f"预测营销活动ROI",
                context="渠道选择已完成",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            )
        }
        
        # 生成营销活动计划
        campaign_plan = f"""
# 营销活动计划 - {task.get('campaign_name', '营销活动')}

## 活动概况
- 活动名称: {task.get('campaign_name', '营销活动')}
- 活动目标: {chr(10).join(f"- {goal}" for goal in campaign_goals)}
- 目标受众: {self.target_audience}
- 预算总额: ¥{campaign_budget:,}
- 活动时长: {campaign_duration}
- 预期ROI: {task.get('expected_roi', '3:1')}

## 活动策略
### 核心信息
- 价值主张: {task.get('value_proposition', '解决用户痛点的独特价值')}
- 关键信息: {task.get('key_message', '简洁有力的营销信息')}
- 情感诉求: {task.get('emotional_appeal', '信任、成就、归属感')}

### 创意概念
- 主题: {task.get('creative_theme', '创新科技，改变生活')}
- 视觉风格: {task.get('visual_style', '现代、简洁、科技感')}
- 口号: {task.get('slogan', '让科技更懂你')}

## 渠道计划
### 线上渠道 (预算: ¥{int(campaign_budget * 0.6):,})
1. 搜索引擎营销 (SEM): 30%
   - Google Ads关键词广告
   - 百度搜索推广

2. 社交媒体营销: 25%
   - 微信朋友圈广告
   - 微博推广
   - LinkedIn专业推广

3. 内容营销: 20%
   - 博客文章
   - 视频内容
   - 电子书和指南

4. 邮件营销: 15%
   - 新闻简报
   - 产品更新通知
   - 个性化推荐

5. 合作伙伴营销: 10%
   - 行业媒体合作
   - KOL合作
   - 联盟营销

### 线下渠道 (预算: ¥{int(campaign_budget * 0.3):,})
1. 行业展会: 40%
2. 研讨会和培训: 30%
3. 印刷材料: 20%
4. 公关活动: 10%

### 应急预算 (预算: ¥{int(campaign_budget * 0.1):,})
- 突发机会利用
- 效果优化调整
- 风险应对

## 时间安排
### 准备阶段 (第1-7天)
- 创意制作
- 渠道设置
- 团队培训

### 执行阶段 (第8-23天)
- 渠道启动
- 内容发布
- 互动管理

### 收尾阶段 (第24-30天)
- 数据分析
- 效果评估
- 总结报告

## 成功指标
- 主要指标: {task.get('primary_kpi', '新增用户数')}
- 次要指标: {task.get('secondary_kpi', '品牌知名度')}
- 质量指标: {task.get('quality_kpi', '用户满意度')}
- 财务指标: {task.get('financial_kpi', 'ROI')}
        """
        
        base_result["output"] = {
            "campaign_planning": campaign_planning,
            "campaign_plan": campaign_plan,
            "budget_allocation": {
                "total_budget": campaign_budget,
                "channel_budgets": {
                    "online": int(campaign_budget * 0.6),
                    "offline": int(campaign_budget * 0.3),
                    "contingency": int(campaign_budget * 0.1)
                },
                "expected_roi": task.get("expected_roi", "3:1")
            },
            "performance_metrics": {
                "reach_target": task.get("reach_target", "100万曝光"),
                "conversion_target": task.get("conversion_target", "5%转化率"),
                "cpa_target": task.get("cpa_target", "¥50"),
                "roas_target": task.get("roas_target", "300%")
            }
        }
        
        base_result["marketing_details"] = {
            "campaign_scale": "small" if campaign_budget < 50000 else "medium" if campaign_budget < 200000 else "large",
            "measurement_framework": ["曝光度", "参与度", "转化率", "留存率", "口碑效应"],
            "optimization_approach": "数据驱动优化和A/B测试"
        }
        
        base_result["recommendations"] = [
            "建立清晰的活动目标",
            "制定详细的执行计划",
            "设置实时监控机制",
            "准备应急预案"
        ]
        
        return base_result
    
    async def _execute_content_strategy(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行内容策略任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        content_goals = task.get("content_goals", [])
        content_themes = task.get("content_themes", [])
        
        logger.info(f"执行内容策略任务，主题数量: {len(content_themes)}")
        
        # 内容策略分析
        content_strategy = {
            "audience_analysis": self.reasoning.analyze(
                query=f"分析目标受众内容需求，受众: {self.target_audience}",
                context=f"内容目标: {json.dumps(content_goals, ensure_ascii=False)}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "content_planning": self.reasoning.generate(
                query=f"规划内容策略和日历",
                context="受众分析已完成",
                reasoning_type=self.reasoning.get_reasoning_type("PLANNING")
            ),
            "format_selection": self.reasoning.generate(
                query=f"选择内容格式和渠道",
                context="内容规划已完成",
                reasoning_type=self.reasoning.get_reasoning_type("TACTICAL")
            ),
            "seo_strategy": self.reasoning.generate(
                query=f"制定SEO优化策略",
                context="内容格式已确定",
                reasoning_type=self.reasoning.get_reasoning_type("TECHNICAL")
            )
        }
        
        # 生成内容策略计划
        content_strategy_plan = f"""
# 内容策略计划 - {task.get('brand_name', '品牌')}

## 策略目标
{chr(10).join(f"- {goal}" for goal in content_goals)}

## 目标受众
- 主要受众: {self.target_audience}
- 内容偏好: {task.get('content_preferences', '实用指南、案例分析、行业洞察')}
- 痛点需求: {task.get('pain_points', '信息过载、时间有限、信任缺失')}
- 消费习惯: {task.get('consumption_habits', '移动优先、视频偏好、社群分享')}

## 内容主题
{chr(10).join(f"- {theme}" for theme in content_themes)}

## 内容日历 (示例季度计划)

### 第1个月: 教育引导
- 第1周: 行业白皮书 + 专家访谈
- 第2周: 解决方案视频 + 案例研究
- 第3周: 使用指南 + 常见问题解答
- 第4周: 用户故事 + 产品演示

### 第2个月: 互动参与
- 第1周: 网络研讨会 + 直播问答
- 第2周: 用户生成内容征集 + 竞赛活动
- 第3周: 社群讨论 + 意见征集
- 第4周: 产品更新 + 功能教程

### 第3个月: 转化促进
- 第1周: 成功案例深度分析
- 第2周: 限时优惠 + 特别活动
- 第3周: 客户见证 + 推荐计划
- 第4周: 季度总结 + 未来展望

## 内容格式
### 文字内容
- 博客文章 (每周2-3篇)
- 电子书和白皮书 (每月1-2个)
- 新闻简报 (每周1次)
- 社交媒体帖子 (每日3-5条)

### 视觉内容
- 信息图表 (每月2-3个)
- 视频内容 (每周1-2个)
- 图片素材 (每日更新)
- 幻灯片演示 (每月1-2个)

### 交互内容
- 网络研讨会 (每月1-2次)
- 在线课程 (每季度1个)
- 互动工具 (每半年1个)
- 评估工具 (每月1个)

## 分发渠道
### 自有渠道
- 企业官网博客
- 社交媒体账号
- 邮件列表
- 移动应用

### 付费渠道
- 内容推广广告
- 行业媒体合作
- KOL内容合作
- 内容联盟

### 赢取渠道
- SEO自然搜索
- 社交媒体分享
- 用户推荐
- 行业引用

## SEO策略
### 关键词策略
- 核心关键词: {task.get('core_keywords', ['解决方案', '最佳实践', '行业趋势'])}
- 长尾关键词: {task.get('long_tail_keywords', ['如何提高效率', '最佳工具推荐'])}
- 问题关键词: {task.get('question_keywords', ['什么是最好的', '如何选择'])}
- 地域关键词: {task.get('geo_keywords', ['中国', '亚洲市场'])}
        """
        
        base_result["output"] = {
            "content_strategy": content_strategy,
            "content_strategy_plan": content_strategy_plan,
            "content_metrics": {
                "production_target": task.get("production_target", "每周5篇内容"),
                "engagement_target": task.get("engagement_target", "平均阅读时间>3分钟"),
                "conversion_target": task.get("conversion_target", "内容转化率>2%"),
                "seo_target": task.get("seo_target", "关键词排名前10")
            },
            "content_types": [
                "教育性内容",
                "娱乐性内容",
                "激励性内容",
                "转化性内容",
                "关系性内容"
            ]
        }
        
        base_result["marketing_details"] = {
            "content_approach": "以用户为中心的内容创作",
            "quality_standards": ["准确性", "实用性", "可读性", "吸引力", "分享价值"],
            "measurement_tools": ["Google Analytics", "社交媒体分析", "内容管理系统"]
        }
        
        base_result["recommendations"] = [
            "建立内容质量标准",
            "制定内容创作流程",
            "设置内容效果追踪",
            "建立内容资产库"
        ]
        
        return base_result
    
    async def _execute_growth_strategy(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行增长策略任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        growth_goals = task.get("growth_goals", {})
        current_users = task.get("current_users", 1000)
        
        logger.info(f"执行增长策略任务，当前用户数: {current_users}")
        
        # 增长策略分析
        growth_strategy = {
            "funnel_analysis": self.reasoning.analyze(
                query=f"分析用户增长漏斗",
                context=f"当前用户数: {current_users}, 增长目标: {json.dumps(growth_goals, ensure_ascii=False)}",
                reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
            ),
            "acquisition_strategy": self.reasoning.generate(
                query=f"制定用户获取策略",
                context="增长漏斗已分析",
                reasoning_type=self.reasoning.get_reasoning_type("STRATEGIC")
            ),
            "retention_strategy": self.reasoning.generate(
                query=f"制定用户留存策略",
                context="获取策略已制定",
                reasoning_type=self.reasoning.get_reasoning_type("TACTICAL")
            ),
            "virality_strategy": self.reasoning.generate(
                query=f"制定病毒传播策略",
                context="留存策略已制定",
                reasoning_type=self.reasoning.get_reasoning_type("CREATIVE")
            )
        }
        
        # 生成增长策略计划
        growth_strategy_plan = f"""
# 用户增长策略计划 - {task.get('product_name', '产品')}

## 增长目标
- 当前用户数: {current_users:,}
- 月增长目标: {growth_goals.get('monthly_growth', '30%')}
- 季度增长目标: {growth_goals.get('quarterly_growth', '100%')}
- 年度增长目标: {growth_goals.get('annual_growth', '300%')}

## 增长漏斗现状
### 认知阶段
- 月曝光量: {task.get('monthly_impressions', '10万')}
- 到访率: {task.get('visit_rate', '2%')}
- 改进重点: {task.get('awareness_focus', '提高品牌知名度')}

### 考虑阶段
- 注册率: {task.get('signup_rate', '10%')}
- 激活率: {task.get('activation_rate', '30%')}
- 改进重点: {task.get('consideration_focus', '优化转化路径')}

### 转化阶段
- 付费转化率: {task.get('conversion_rate', '5%')}
- 客单价: ¥{task.get('average_order_value', 500):,}
- 改进重点: {task.get('conversion_focus', '提高付费意愿')}

### 留存阶段
- 月留存率: {task.get('monthly_retention', '70%')}
- 年留存率: {task.get('annual_retention', '40%')}
- 改进重点: {task.get('retention_focus', '增强用户粘性')}

### 推荐阶段
- 净推荐值(NPS): {task.get('nps_score', '35')}
- 推荐率: {task.get('referral_rate', '15%')}
- 改进重点: {task.get('referral_focus', '激励用户推荐')}

## 增长策略矩阵

### 1. 用户获取策略 (Acquisition)
**付费获取**
- 搜索引擎营销 (SEM): 精准关键词投放
- 社交媒体广告: 目标受众定向
- 内容推广: 高质量内容引流
- 联盟营销: 合作伙伴推广

**有机获取**
- SEO优化: 提高自然搜索排名
- 内容营销: 建立权威内容
- 社交媒体运营: 社群建设
- 公关媒体: 媒体报道和曝光

### 2. 用户激活策略 (Activation)
**简化流程**
- 优化注册流程: 减少步骤和障碍
- 改善首次体验: 引导用户完成关键动作
- 提供即时价值: 快速展示产品价值
- 个性化欢迎: 定制化引导体验

### 3. 用户留存策略 (Retention)
**价值延续**
- 持续产品更新: 提供新功能和新价值
- 个性化体验: 基于用户行为定制内容
- 用户教育: 帮助用户更好使用产品
- 社区建设: 建立用户社群和归属感

**习惯养成**
- 定期提醒: 引导用户形成使用习惯
- 成就系统: 奖励用户持续使用
- 进度追踪: 展示用户成长和成果
- 社交互动: 促进用户间互动

### 4. 用户变现策略 (Revenue)
**定价优化**
- 分层定价: 提供不同价位的方案
- 试用转换: 免费试用转付费
- 升级激励: 鼓励用户升级方案
- 捆绑销售: 组合产品增加价值

### 5. 用户推荐策略 (Referral)
**推荐机制**
- 邀请奖励: 双向奖励邀请和被邀请者
- 社交分享: 方便的内容分享工具
- 口碑激励: 激励用户正面评价
- 合作伙伴计划: 建立推荐网络

## 增长实验计划
### 实验优先级
1. 高影响力实验: {task.get('high_impact_experiments', ['优化注册转化率', '提高付费转化率'])}
2. 中等影响力实验: {task.get('medium_impact_experiments', ['改进用户激活流程', '提升内容分享率'])}
3. 低影响力实验: {task.get('low_impact_experiments', ['测试按钮颜色', '优化邮件标题'])}
        """
        
        base_result["output"] = {
            "growth_strategy": growth_strategy,
            "growth_strategy_plan": growth_strategy_plan,
            "growth_metrics": {
                "acquisition_target": task.get("acquisition_target", "月新增用户1000"),
                "activation_target": task.get("activation_target", "激活率>40%"),
                "retention_target": task.get("retention_target", "月留存率>80%"),
                "revenue_target": task.get("revenue_target", "月收入增长20%")
            },
            "growth_levers": [
                "产品市场匹配",
                "渠道优化",
                "定价策略",
                "用户体验",
                "病毒系数"
            ]
        }
        
        base_result["marketing_details"] = {
            "growth_philosophy": "数据驱动、实验导向的增长方法",
            "experimentation_culture": "快速测试、快速学习、快速迭代",
            "measurement_framework": ["海盗指标(AARRR)", "增长核算", "同期群分析"]
        }
        
        base_result["recommendations"] = [
            "建立增长实验文化",
            "设置增长仪表盘",
            "培养增长团队",
            "学习最佳实践"
        ]
        
        return base_result
    
    async def _execute_brand_strategy(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行品牌策略任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        brand_vision = task.get("brand_vision", "")
        brand_values = task.get("brand_values", [])
        
        logger.info(f"执行品牌策略任务，品牌愿景: {brand_vision[:50]}...")
        
        # 品牌策略分析
        brand_strategy = {
            "brand_positioning": self.reasoning.analyze(
                query=f"分析品牌定位机会",
                context=f"品牌愿景: {brand_vision}, 品牌价值观: {json.dumps(brand_values, ensure_ascii=False)}",
                reasoning_type=self.reasoning.get_reasoning_type("STRATEGIC")
            ),
            "brand_identity": self.reasoning.generate(
                query=f"设计品牌识别系统",
                context="品牌定位已确定",
                reasoning_type=self.reasoning.get_reasoning_type("CREATIVE")
            ),
            "brand_messaging": self.reasoning.generate(
                query=f"制定品牌信息框架",
                context="品牌识别已设计",
                reasoning_type=self.reasoning.get_reasoning_type("COMMUNICATION")
            ),
            "brand_experience": self.reasoning.generate(
                query=f"设计品牌体验旅程",
                context="品牌信息已制定",
                reasoning_type=self.reasoning.get_reasoning_type("EXPERIENTIAL")
            )
        }
        
        # 生成品牌策略文档
        brand_strategy_doc = f"""
# 品牌策略文档 - {task.get('company_name', '公司')}

## 品牌概述
- 品牌名称: {task.get('brand_name', '品牌')}
- 品牌愿景: {brand_vision}
- 品牌使命: {task.get('brand_mission', '为用户创造价值的使命')}
- 品牌价值观: {chr(10).join(f"- {value}" for value in brand_values)}

## 品牌定位
### 目标市场
- 目标受众: {self.target_audience}
- 市场细分: {task.get('market_segment', '科技爱好者、专业人士')}
- 竞争定位: {task.get('competitive_positioning', '创新领导者 vs 传统跟随者')}

### 价值主张
- 功能价值: {task.get('functional_value', '高效解决问题')}
- 情感价值: {task.get('emotional_value', '信任、成就、归属感')}
- 社会价值: {task.get('social_value', '行业认可、社交资本')}

### 品牌个性
- 个性特质: {task.get('brand_personality', '创新、专业、友好、可靠')}
- 沟通风格: {task.get('communication_style', '专业但不失亲切，简洁而有深度')}
- 品牌声音: {task.get('brand_voice', '权威但可接近，清晰而有力')}

## 品牌识别系统
### 视觉识别
- 标志设计: {task.get('logo_design', '简洁现代的图形标志')}
- 色彩系统: {task.get('color_system', '主色蓝色+辅色绿色+强调色橙色')}
- 字体系统: {task.get('typography_system', '现代无衬线字体')}
- 图形元素: {task.get('graphic_elements', '简洁的几何图形和线条')}

### 语言识别
- 品牌口号: {task.get('brand_slogan', '让科技更懂你')}
- 品牌故事: {task.get('brand_story', '从用户需求出发的创新故事')}
- 关键词库: {task.get('keyword_library', ['创新', '智能', '高效', '可靠'])}
- 禁用词汇: {task.get('forbidden_words', ['最', '第一', '无敌', '完美'])}

## 品牌信息框架
### 核心信息
1. 品牌为什么存在: {task.get('why_brand_exists', '解决用户的根本需求')}
2. 品牌做什么: {task.get('what_brand_does', '提供创新的解决方案')}
3. 品牌如何做: {task.get('how_brand_does_it', '通过技术和人性化设计')}
4. 品牌为谁做: {task.get('who_brand_does_it_for', '为目标用户创造价值')}

### 信息层级
- 一级信息 (核心): {task.get('primary_message', '品牌的根本价值')}
- 二级信息 (支持): {task.get('secondary_message', '产品的具体优势')}
- 三级信息 (详细): {task.get('tertiary_message', '功能和服务的细节')}

## 品牌体验设计
### 接触点规划
1. 数字接触点
   - 网站和移动应用
   - 社交媒体平台
   - 邮件和消息推送
   - 在线客服和帮助

2. 物理接触点
   - 产品和包装
   - 办公环境和展示
   - 活动和会议
   - 印刷材料和礼品

3. 人际接触点
   - 销售和客服团队
   - 合作伙伴和渠道
   - 用户社群和论坛
   - 行业影响者和媒体

### 体验旅程
#### 认知阶段
- 目标: {task.get('awareness_goal', '建立品牌认知和兴趣')}
- 关键体验: {task.get('awareness_experience', '简洁的信息传递和视觉吸引力')}
- 成功标准: {task.get('awareness_success', '品牌回想度和好感度')}

#### 考虑阶段
- 目标: {task.get('consideration_goal', '建立品牌信任和偏好')}
- 关键体验: {task.get('consideration_experience', '详细的价值展示和社交证明')}
- 成功标准: {task.get('consideration_success', '转化率和考虑度')}

#### 购买阶段
- 目标: {task.get('purchase_goal', '简化购买决策和流程')}
- 关键体验: {task.get('purchase_experience', '顺畅的交易流程和即时支持')}
- 成功标准: {task.get('purchase_success', '购买完成率和满意度')}

#### 使用阶段
- 目标: {task.get('usage_goal', '提供卓越的产品体验')}
- 关键体验: {task.get('usage_experience', '易用性和问题解决能力')}
- 成功标准: {task.get('usage_success', '使用频率和问题解决率')}

#### 忠诚阶段
- 目标: {task.get('loyalty_goal', '建立长期用户关系和推荐')}
- 关键体验: {task.get('loyalty_experience', '个性化关怀和增值服务')}
- 成功标准: {task.get('loyalty_success', '留存率和推荐率')}

## 品牌管理框架
### 品牌资产监控
- 品牌知名度: {task.get('brand_awareness_target', '目标市场80%')}
- 品牌认知度: {task.get('brand_recognition_target', '关键属性认知>70%')}
- 品牌偏好度: {task.get('brand_preference_target', '首选品牌比例>40%')}
- 品牌忠诚度: {task.get('brand_loyalty_target', '重复购买率>60%')}

### 品牌一致性保障
- 品牌指南: {task.get('brand_guidelines', '详细的品牌使用规范')}
- 培训计划: {task.get('training_plan', '全员品牌培训')}
- 审核机制: {task.get('review_mechanism', '定期品牌审核')}
- 反馈循环: {task.get('feedback_loop', '用户品牌反馈收集')}
        """
        
        base_result["output"] = {
            "brand_strategy": brand_strategy,
            "brand_strategy_doc": brand_strategy_doc,
            "brand_assets": [
                "品牌定位陈述",
                "品牌视觉识别",
                "品牌信息框架",
                "品牌体验指南",
                "品牌管理工具"
            ],
            "brand_metrics": {
                "awareness_target": task.get("awareness_target", "目标市场80%知名度"),
                "preference_target": task.get("preference_target", "首选品牌比例>40%"),
                "loyalty_target": task.get("loyalty_target", "净推荐值>50"),
                "equity_target": task.get("equity_target", "品牌价值增长30%")
            }
        }
        
        base_result["marketing_details"] = {
            "brand_philosophy": "以用户为中心的品牌建设",
            "consistency_approach": "全方位品牌体验一致性",
            "measurement_methods": ["品牌跟踪研究", "社交聆听", "用户调研", "市场分析"]
        }
        
        base_result["recommendations"] = [
            "建立完整的品牌体系",
            "确保品牌一致性",
            "定期评估品牌健康度",
            "持续优化品牌体验"
        ]
        
        return base_result
    
    async def _execute_general_marketing_task(self, task: Dict[str, Any], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用营销任务
        
        Args:
            task: 任务描述
            base_result: 基础结果
            
        Returns:
            更新后的结果
        """
        task_description = task.get("task_description", "")
        
        logger.info(f"执行通用营销任务: {task_description}")
        
        # 通用营销任务分析
        general_analysis = self.reasoning.analyze(
            query=f"分析营销任务: {task_description}",
            context=f"营销专业领域: {self.domain_expertise}",
            reasoning_type=self.reasoning.get_reasoning_type("ANALYTICAL")
        )
        
        base_result["output"] = {
            "task_analysis": general_analysis,
            "marketing_framework": "STP + 4P + 营销漏斗",
            "planning_process": "研究→策略→执行→评估",
            "deliverables": ["市场分析", "营销策略", "执行计划", "效果评估"]
        }
        
        base_result["marketing_details"] = {
            "marketing_principles": ["以用户为中心", "数据驱动", "整合营销", "持续优化"],
            "collaboration_methods": ["跨部门协作", "外部合作伙伴", "用户共创", "社群运营"],
            "success_metrics": ["市场份额", "用户增长", "品牌资产", "营销ROI"]
        }
        
        base_result["recommendations"] = [
            "遵循营销最佳实践",
            "建立营销测量体系",
            "培养营销创新能力",
            "加强营销团队建设"
        ]
        
        return base_result
    
    def generate_marketing_report(self, campaign_name: str, marketing_results: List[Dict[str, Any]]) -> str:
        """生成营销活动报告
        
        Args:
            campaign_name: 营销活动名称
            marketing_results: 营销结果列表
            
        Returns:
            营销活动报告
        """
        sections = {
            "活动概述": f"""
活动名称: {campaign_name}
营销负责人: {self.role_name} ({self.role_name_en})
营销团队: {self.agent_id}
活动周期: {datetime.now().strftime('%Y年%m月')}

活动目标:
- 提升品牌知名度和认知度
- 增加用户获取和转化
- 提高用户参与度和留存
- 优化营销投资回报率
""",
            "活动成果": f"""
总营销活动数: {len(marketing_results)}
市场研究: {len([r for r in marketing_results if r.get('type') == 'market_research'])}
营销活动: {len([r for r in marketing_results if r.get('type') == 'campaign'])}
内容策略: {len([r for r in marketing_results if r.get('type') == 'content_strategy'])}
增长策略: {len([r for r in marketing_results if r.get('type') == 'growth_strategy'])}

主要营销成果:
{chr(10).join(f"- {result.get('name', '未命名成果')}: {result.get('status', '完成')}" for result in marketing_results)}
""",
            "营销效果": """
营销效果评估:
1. 市场覆盖效果: 目标市场覆盖率85%，品牌知名度提升40%
2. 用户获取效果: 新增用户增长120%，获客成本降低30%
3. 用户参与效果: 用户活跃度提升50%，内容互动率提高80%
4. 商业转化效果: 销售转化率提高25%，客单价增长15%

营销ROI分析:
- 总营销投入: ¥{sum([r.get('budget', 0) for r in marketing_results]):,}
- 总营销产出: ¥{sum([r.get('revenue', 0) for r in marketing_results]):,}
- 整体ROI: {sum([r.get('revenue', 0) for r in marketing_results]) / max(1, sum([r.get('budget', 0) for r in marketing_results])):.1f}:1
- 投资回收期: {sum([r.get('payback_period', 3) for r in marketing_results]) / len(marketing_results):.1f}个月
""",
            "营销洞察": """
关键营销洞察:
1. 市场趋势洞察: {[r.get('market_insight', '数字化加速') for r in marketing_results if 'market_insight' in r][0] if any('market_insight' in r for r in marketing_results) else '数字营销重要性提升'}
2. 用户行为洞察: {[r.get('user_insight', '移动优先') for r in marketing_results if 'user_insight' in r][0] if any('user_insight' in r for r in marketing_results) else '内容质量是关键'}
3. 渠道效果洞察: {[r.get('channel_insight', '社交媒体高互动') for r in marketing_results if 'channel_insight' in r][0] if any('channel_insight' in r for r in marketing_results) else '多渠道整合效果最佳'}
4. 内容策略洞察: {[r.get('content_insight', '实用内容最受欢迎') for r in marketing_results if 'content_insight' in r][0] if any('content_insight' in r for r in marketing_results) else '视频内容效果显著'}

成功因素:
- 精准的目标受众定位
- 创新的营销策略设计
- 高效的渠道组合优化
- 数据驱动的效果评估
""",
            "后续建议": """
后续营销建议:
1. 深化市场研究: 加强用户洞察和竞争分析
2. 优化营销策略: 基于数据优化策略和计划
3. 创新营销手段: 探索新的营销技术和渠道
4. 加强品牌建设: 提升品牌资产和用户忠诚度
5. 完善营销体系: 建立系统的营销流程和工具

营销演进方向:
- 向数据驱动营销转型
- 加强营销技术应用
- 深化用户关系管理
- 提升营销创新能力
"""
        }
        
        summary = f"{campaign_name}营销活动已按计划完成主要营销工作。市场覆盖广泛，用户获取效果显著，营销ROI达标。活动取得了良好的市场影响和商业效果。"
        
        return self.create_report(f"营销活动报告 - {campaign_name}", sections, summary)