#!/usr/bin/env python3
"""
日本财务专家
专注于日本财务规划、税务策略、资金管理和投资分析
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import JapanMarketAgent, JapanAgentConfig, JapanAgentFactory


class JapanFinancialExpert(JapanMarketAgent):
    """日本财务专家"""
    
    def __init__(self, config: Optional[JapanAgentConfig] = None):
        if config is None:
            config = JapanAgentConfig(
                agent_id="japan_financial_expert_001",
                role_name="日本財務・税務専門家",
                role_name_en="Japan Financial Expert",
                domain_expertise="日本財務・税務計画・資金調達",
                expertise_jp="日本の会計基準、税制、財務計画、資金調達、投資分析の専門知識を持ち、日本市場でのビジネス展開における財務最適化と税務効率化を支援します。",
                capabilities=["財務計画", "税務戦略", "資金調達", "投資分析", "予算管理"],
                tools=["財務モデル", "税務計算ツール", "投資分析フレームワーク"]
            )
        
        super().__init__(
            agent_id=config.agent_id,
            role_name=config.role_name,
            role_name_en=config.role_name_en,
            domain_expertise=config.domain_expertise,
            expertise_jp=config.expertise_jp,
            config=config
        )
        
        # 财务特定字段
        self.financial_expertise_areas = [
            "日本会計基準（JGAAP）",
            "国際会計基準（IFRS）対応",
            "法人税・消費税計画",
            "資金調達戦略（銀行融資、VC、公的支援）",
            "予算管理・コスト最適化",
            "投資リターン分析",
            "為替リスク管理",
            "連結決算対応"
        ]
        
        # 更新系统提示
        self._enhance_system_prompt()
    
    def _enhance_system_prompt(self):
        """增强财务专家系统提示"""
        financial_expertise = "\n".join([f"• {area}" for area in self.financial_expertise_areas])
        
        enhanced_prompt = f"""
{self.system_prompt}

【財務専門分野】
{financial_expertise}

【日本の主要税制】
1. 法人税（Corporate Tax） - 23.2%（基準税率）
2. 消費税（Consumption Tax） - 10%（標準税率）、8%（軽減税率）
3. 住民税（Inhabitant Tax） - 法人住民税、法人事業税
4. 源泉徴収税（Withholding Tax） - 給与、配当、利子
5. 固定資産税（Fixed Asset Tax） - 不動産・設備

【財務計画の原則】
• 保守的見積もり：日本のビジネス環境に適した保守的な計画
• 段階的投資：リスク分散のための段階的資金投入
• 現地通貨対応：円建てでのキャッシュフロー管理
• 税務効率化：合法的な税務最適化戦略
• レポート対応：日本の会計・税務報告要件への対応

【具体的な支援内容】
• 日本での会社設立時の資金計画
• 日本の税制を考慮したビジネスモデル設計
• 資金調達オプションの比較分析（銀行、VC、政府支援）
• 予算管理とコスト最適化戦略
• 投資案件の財務的評価
• 為替リスクヘッジ戦略
• 月次・四半期財務レビュー
"""
        self.system_prompt = enhanced_prompt
    
    async def create_financial_plan(self, business_model: str, investment_amount: float, timeframe_years: int = 3) -> Dict[str, Any]:
        """创建财务计划"""
        task = f"""
以下のビジネスモデルに基づき、{timeframe_years}年間の財務計画を作成してください：
- ビジネスモデル：{business_model}
- 初期投資額：¥{investment_amount:,.0f}
- 計画期間：{timeframe_years}年

日本の税制、会計基準、市場条件を考慮してください。
"""
        
        result = await self.process_task(task)
        
        # 添加财务特定分析
        financial_projections = await self._generate_financial_projections(business_model, investment_amount, timeframe_years)
        
        result["financial_projections"] = financial_projections
        result["plan_type"] = "financial_plan"
        result["timeframe_years"] = timeframe_years
        
        return result
    
    async def analyze_tax_strategy(self, business_structure: str, revenue_projections: Dict[str, float]) -> Dict[str, Any]:
        """分析税务策略"""
        revenue_summary = "\n".join([f"- {year}: ¥{amount:,.0f}" for year, amount in revenue_projections.items()])
        
        task = f"""
以下の条件に基づき、最適な税務戦略を分析してください：
- 事業形態：{business_structure}
- 収益見込み：
{revenue_summary}

日本の税制を考慮し、合法的な税務最適化策を提案してください。
"""
        
        result = await self.process_task(task)
        
        # 添加税务特定分析
        tax_analysis = await self._perform_tax_analysis(business_structure, revenue_projections)
        
        result["tax_analysis"] = tax_analysis
        result["business_structure"] = business_structure
        
        return result
    
    async def evaluate_funding_options(self, funding_needs: float, business_stage: str) -> Dict[str, Any]:
        """评估融资选项"""
        task = f"""
資金調達ニーズ：¥{funding_needs:,.0f}
ビジネスステージ：{business_stage}

日本での資金調達オプションを比較分析し、最適な選択肢を提案してください。
"""
        
        result = await self.process_task(task)
        
        # 添加融资特定分析
        funding_analysis = await self._analyze_funding_options(funding_needs, business_stage)
        
        result["funding_analysis"] = funding_analysis
        result["funding_needs"] = funding_needs
        result["business_stage"] = business_stage
        
        return result
    
    async def _generate_financial_projections(self, business_model: str, investment: float, years: int) -> Dict[str, Any]:
        """生成财务预测"""
        # 这里应该实现具体的财务预测逻辑
        # 为简化，返回示例预测
        return {
            "initial_investment": investment,
            "projection_period": f"{years} years",
            "revenue_growth_assumption": "保守的（年率15-25%）",
            "key_assumptions": [
                "日本の市場成長率を考慮",
                "段階的な市場参入",
                "保守的な顧客獲得コスト",
                "日本の人件費・オフィスコスト"
            ],
            "break_even_analysis": {
                "estimated_months_to_break_even": 18,
                "critical_factors": ["顧客獲得速度", "価格設定", "運営効率"]
            },
            "cash_flow_considerations": [
                "初期6ヶ月はキャッシュバーン率が高い",
                "12ヶ月目から安定化見込み",
                "為替リスク管理が必要"
            ]
        }
    
    async def _perform_tax_analysis(self, business_structure: str, revenues: Dict[str, float]) -> Dict[str, Any]:
        """执行税务分析"""
        # 基于业务结构和收入进行税务分析
        tax_rates = {
            "kk": {"corporate_tax": 0.232, "inhabitant_tax": 0.107},
            "gk": {"corporate_tax": 0.232, "inhabitant_tax": 0.107},
            "branch": {"corporate_tax": 0.232, "withholding_tax": 0.206}
        }
        
        rates = tax_rates.get(business_structure.lower(), tax_rates["kk"])
        
        # 简单税务计算示例
        first_year_revenue = list(revenues.values())[0] if revenues else 0
        estimated_tax = first_year_revenue * (rates["corporate_tax"] + rates.get("inhabitant_tax", 0))
        
        return {
            "business_structure": business_structure,
            "applicable_tax_rates": rates,
            "estimated_first_year_tax": estimated_tax,
            "tax_optimization_strategies": [
                "研究開発税額控除の活用",
                "設備投資の減価償却",
                "適切な会計年度設定"
            ],
            "compliance_requirements": [
                "年1回の法人税申告",
                "消費税課税事業者登録（売上高1000万円以上）",
                "源泉徴収税の納付"
            ]
        }
    
    async def _analyze_funding_options(self, needs: float, stage: str) -> List[Dict[str, Any]]:
        """分析融资选项"""
        # 基于业务阶段提供融资选项
        funding_options = []
        
        if stage == "startup":
            funding_options = [
                {
                    "type": "政府支援金",
                    "description": "JST、NEDOなどの研究開発補助金",
                    "amount_range": "¥1,000万 - ¥5,000万",
                    "pros": ["返済不要", "信用向上", "ネットワーク構築"],
                    "cons": ["申請競争率が高い", "用途制限", "報告義務"],
                    "suitability": "high"
                },
                {
                    "type": "ベンチャーキャピタル",
                    "description": "日本VCからの投資",
                    "amount_range": "¥5,000万 - ¥5億",
                    "pros": ["専門家ネットワーク", "経営支援", "追加資金調達の道"],
                    "cons": ["株式譲渡", "経営介入", "出口戦略のプレッシャー"],
                    "suitability": "medium"
                }
            ]
        elif stage == "growth":
            funding_options = [
                {
                    "type": "銀行融資",
                    "description": "メガバンク・地銀からの融資",
                    "amount_range": "¥1,000万 - ¥10億",
                    "pros": ["株式希薄化なし", "金利が比較的低い", "関係構築"],
                    "cons": ["担保・保証が必要", "審査が厳しい", "返済義務"],
                    "suitability": "high"
                },
                {
                    "type": "社債発行",
                    "description": "私募債・公募債の発行",
                    "amount_range": "¥1億以上",
                    "pros": ["長期資金調達", "金利固定", "財務構造の多様化"],
                    "cons": ["発行コスト", "信用格付け必要", "市場条件に依存"],
                    "suitability": "medium"
                }
            ]
        else:  # established
            funding_options = [
                {
                    "type": "株式公開（IPO）",
                    "description": "東証・名証への上場",
                    "amount_range": "¥10億以上",
                    "pros": ["大型資金調達", "ブランド価値向上", "流動性提供"],
                    "cons": ["高コスト", "情報開示義務", "短期業績圧力"],
                    "suitability": "high"
                },
                {
                    "type": "戦略的投資",
                    "description": "大企業からの出資",
                    "amount_range": "¥5億 - ¥50億",
                    "pros": ["事業連携", "市場アクセス", "技術支援"],
                    "cons": ["経営独立性の制限", "競合関係の懸念", "出口の複雑さ"],
                    "suitability": "medium"
                }
            ]
        
        # 根据资金需求筛选
        filtered_options = []
        for option in funding_options:
            # 简单匹配逻辑
            if needs > 50000000:  # 5000万円以上
                if option["type"] in ["ベンチャーキャピタル", "株式公開", "戦略的投資"]:
                    filtered_options.append(option)
            else:
                if option["type"] in ["政府支援金", "銀行融資"]:
                    filtered_options.append(option)
        
        return filtered_options if filtered_options else funding_options[:2]
    
    def get_financial_expertise_summary(self) -> Dict[str, Any]:
        """获取财务专业知识摘要"""
        return {
            "agent_role": self.role_name,
            "financial_areas": self.financial_expertise_areas,
            "language": self.language,
            "focus_markets": ["日本市場"],
            "tax_knowledge": ["法人税", "消費税", "源泉徴収税", "国際税務"],
            "deliverables_count": len(self.deliverables)
        }


# 工厂方法
def create_japan_financial_expert() -> JapanFinancialExpert:
    """创建日本财务专家"""
    return JapanFinancialExpert()