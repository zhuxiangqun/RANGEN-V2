#!/usr/bin/env python3
"""
客户经理 (Customer Manager)
根据解决方案寻找目标客户
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base import JapanMarketAgent


@dataclass
class LeadScore:
    """潜在客户评分"""
    company_name: str
    score: float  # 0-100
    match_reasons: List[str]
    barriers: List[str]
    recommended_approach: str


@dataclass
class CustomerProfile:
    """客户画像"""
    company_name: str
    industry: str
    company_size: str  # 大企業/中堅/中小企业
    revenue: str
    location: str
    pain_points: List[str]
    current_solutions: List[str]
    decision_makers: List[Dict[str, str]]
    website: str = ""


class JapanCustomerManager(JapanMarketAgent):
    """日本客户经理"""
    
    def __init__(self):
        super().__init__(
            agent_id="japan_customer_manager",
            role_name="アカウントマネージャー",
            role_name_en="Customer Manager",
            domain_expertise="顧客開拓 / リード獲得 / B2B営業",
            expertise_jp="""
あなたの任务是、根据ソリューション，找到合适的目标客户并开展営業活動。

【具体的な業務】
1. ターゲット顧客の特定
2. 顧客プロファイルの作成
3. リードの創出と評価
4. アプローチ戦略の策定
5. 商談機会の創出

【日本のビジネス慣行】
- 稟議制度への対応
- 長時間関係構築
- 信頼関係の重視
- 期末商戦の把握

【輸出要件】
- 具体的な企業リスト
- 顧客プロファイル
- アプローチ計画
- 商談スクリプト
"""
        )
        
        self.available_tools = [
            "web_search",
            "knowledge_retrieval",
            "crm_integration",
            "email_composition"
        ]
        
        # 目标客户列表
        self.leads: List[LeadScore] = []
        self.customer_profiles: List[CustomerProfile] = []
    
    async def find_target_customers(
        self,
        solution_design: Dict[str, Any],
        technical_solution: Optional[Dict[str, Any]] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        寻找目标客户
        
        Args:
            solution_design: 解决方案设计
            technical_solution: 技术解决方案
            criteria: 筛选条件
        """
        criteria = criteria or {}
        
        # 1. 定义理想客户画像
        ideal_profile = await self._define_ideal_customer(solution_design)
        
        # 2. 搜索潜在客户
        potential_customers = await self._search_potential_customers(
            ideal_profile, criteria
        )
        
        # 3. 评估和评分
        scored_leads = await self._score_leads(
            potential_customers, solution_design
        )
        
        # 4. 创建客户画像
        profiles = await self._create_customer_profiles(scored_leads)
        
        # 5. 制定接触策略
        approach_plans = await self._design_approach_strategy(profiles)
        
        # 6. 生成客户列表报告
        report = self._generate_lead_report(
            leads=scored_leads,
            profiles=profiles,
            approach_plans=approach_plans
        )
        
        # 存储成果
        self.store_deliverable("customer_targeting", {
            "ideal_profile": ideal_profile,
            "leads": scored_leads,
            "profiles": profiles,
            "approach_plans": approach_plans,
            "report": report
        })
        
        return {
            "status": "completed",
            "ideal_profile": ideal_profile,
            "total_leads": len(scored_leads),
            "top_leads": scored_leads[:10],
            "profiles": profiles,
            "approach_plans": approach_plans,
            "report": report
        }
    
    async def _define_ideal_customer(
        self,
        solution_design: Dict
    ) -> Dict[str, Any]:
        """定义理想客户画像"""
        solution = solution_design.get("solution", {})
        
        return {
            "company_size": ["中堅企業", "大企業"],
            "industry": [
                "製造業",
                "小売業",
                "サービス業",
                "金融業"
            ],
            "annual_revenue": "1億円〜100億円",
            "region": ["東京都", "大阪府", "愛知県"],
            "characteristics": [
                "DX推進への関心が高い",
                "既存システムの老朽化",
                "業務効率化ニーズあり",
                "予算確保可能"
            ],
            "pain_points": [
                "手作業が多い",
                "システム連携の課題",
                "データ活用が進んでいない",
                "人材不足"
            ],
            "tech_readiness": ["中〜高"]
        }
    
    async def _search_potential_customers(
        self,
        ideal_profile: Dict,
        criteria: Dict
    ) -> List[Dict[str, Any]]:
        """搜索潜在客户"""
        # 这里应该调用web_search搜索真实数据
        # 简化版本返回模拟数据
        return [
            {
                "company_name": "山田製作所",
                "industry": "製造業",
                "company_size": "中堅企業",
                "revenue": "50億円",
                "location": "東京都",
                "employee_count": "300名",
                "website": "https://yamada.co.jp"
            },
            {
                "company_name": "佐藤商店",
                "industry": "小売業",
                "company_size": "中堅企業",
                "revenue": "80億円",
                "location": "大阪府",
                "employee_count": "500名",
                "website": "https://sato.co.jp"
            },
            {
                "company_name": "鈴木重工",
                "industry": "製造業",
                "company_size": "大企業",
                "revenue": "500億円",
                "location": "愛知県",
                "employee_count": "2000名",
                "website": "https://suzuki-heavy.co.jp"
            },
            {
                "company_name": "田中電機",
                "industry": "製造業",
                "company_size": "大企業",
                "revenue": "1000億円",
                "location": "東京都",
                "employee_count": "5000名",
                "website": "https://tanaka-denki.co.jp"
            },
            {
                "company_name": "高橋物産",
                "industry": "卸売業",
                "company_size": "中堅企業",
                "revenue": "30億円",
                "location": "大阪府",
                "employee_count": "150名",
                "website": "https://takahashi.co.jp"
            },
            {
                "company_name": "伊藤五金",
                "industry": "小売業",
                "company_size": "中小企业",
                "revenue": "5億円",
                "location": "愛知県",
                "employee_count": "50名",
                "website": "https://ito.co.jp"
            },
            {
                "company_name": "渡辺建設",
                "industry": "建設業",
                "company_size": "中堅企業",
                "revenue": "60億円",
                "location": "東京都",
                "employee_count": "400名",
                "website": "https://watanabe.co.jp"
            },
            {
                "company_name": "中村化工",
                "industry": "化学",
                "company_size": "大企業",
                "revenue": "800億円",
                "location": "大阪府",
                "employee_count": "3000名",
                "website": "https://nakamura-kagaku.co.jp"
            },
            {
                "company_name": "小林精密",
                "industry": "製造業",
                "company_size": "中堅企業",
                "revenue": "25億円",
                "location": "愛知県",
                "employee_count": "200名",
                "website": "https://kobayashi-seiko.co.jp"
            },
            {
                "company_name": "加藤商事",
                "industry": "サービス業",
                "company_size": "中堅企業",
                "revenue": "40億円",
                "location": "東京都",
                "employee_count": "350名",
                "website": "https://kato.co.jp"
            }
        ]
    
    async def _score_leads(
        self,
        potential_customers: List[Dict],
        solution_design: Dict
    ) -> List[LeadScore]:
        """评分潜在客户"""
        scored = []
        
        for customer in potential_customers:
            score = 50  # 基础分数
            match_reasons = []
            barriers = []
            
            # 企业规模匹配
            if customer["company_size"] in ["中堅企業", "大企業"]:
                score += 20
                match_reasons.append("適切な企業規模")
            else:
                barriers.append("企業規模が小さい")
            
            # 行业匹配
            if customer["industry"] in ["製造業", "小売業"]:
                score += 15
                match_reasons.append("対象業界")
            
            # 地区匹配
            if customer["location"] in ["東京都", "大阪府", "愛知県"]:
                score += 10
                match_reasons.append("主要三大都市圏")
            
            # 收入规模
            revenue = customer.get("revenue", "0億円")
            if "億円" in revenue:
                try:
                    amount = float(revenue.replace("億円", ""))
                    if amount >= 20:
                        score += 5
                except:
                    pass
            
            scored.append(LeadScore(
                company_name=customer["company_name"],
                score=min(100, score),
                match_reasons=match_reasons,
                barriers=barriers,
                recommended_approach=self._determine_approach(score)
            ))
        
        # 按分数排序
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
    
    def _determine_approach(self, score: float) -> str:
        """确定接触方式"""
        if score >= 80:
            return "高優先度 - 直接訪問 + 経営層紹介"
        elif score >= 60:
            return "優先ターゲット - Webinar招待 + 資料送付"
        else:
            return "ナーチャリング対象 - メール配信 + ニュースレター"
    
    async def _create_customer_profiles(
        self,
        leads: List[LeadScore]
    ) -> List[CustomerProfile]:
        """创建客户画像"""
        profiles = []
        
        for lead in leads[:10]:  # Top 10
            profiles.append(CustomerProfile(
                company_name=lead.company_name,
                industry="製造業",  # 简化
                company_size="中堅企業",  # 简化
                revenue="50億円",  # 简化
                location="東京都",  # 简化
                pain_points=[
                    "業務効率化したい",
                    "システム連携の課題",
                    "データ活用を進たい"
                ],
                current_solutions=[
                    "Excel中心の運用",
                    "古い基幹システム"
                ],
                decision_makers=[
                    {"name": "田中 太郎", "position": "情報部長", "role": "決裁者"},
                    {"name": "鈴木 花子", "position": "DX推進室長", "role": "影響者"}
                ]
            ))
        
        return profiles
    
    async def _design_approach_strategy(
        self,
        profiles: List[CustomerProfile]
    ) -> List[Dict[str, Any]]:
        """制定接触策略"""
        strategies = []
        
        for profile in profiles:
            strategy = {
                "company": profile.company_name,
                "priority": "HIGH" if len(profile.decision_makers) > 0 else "MEDIUM",
                "channels": [
                    {
                        "type": "紹介",
                        "description": "共通の知人からの紹介",
                        "timing": "1-2週間以内"
                    },
                    {
                        "type": "メール",
                        "description": "社長・経営層への直接メール",
                        "timing": "1週間以内"
                    },
                    {
                        "type": "イベント",
                        "description": "業界のセミナー・展示会への参加",
                        "timing": "1ヶ月以内"
                    }
                ],
                "script": self._generate_outreach_script(profile),
                "next_steps": [
                    "第一步：LinkedInでconnection建立",
                    "第二周：会社概要资料的发送",
                    "第三周：オンライン座谈会的邀请"
                ]
            }
            strategies.append(strategy)
        
        return strategies
    
    def _generate_outreach_script(self, profile: CustomerProfile) -> Dict[str, str]:
        """生成接触脚本"""
        return {
            "subject": f"{profile.company_name}様のDX推進について",
            "opening": f"お世話になっております。{profile.company_name}様のDX推進を担当されているとご要望いただき联系いたしました。",
            "body": f"""
{profile.company_name}様においては、{'、'.join(profile.pain_points[:2])}の課題をお持ちと存じます。

当我们社は、当該課題の解决に有効なソリューション为您提供できます。
是非、30分程度のお時間をいただければ、介绍一下给您提供できる价值。
""",
            "cta": "お忙しい中恐れ入りますが、ご都合のよろしい日時を教えていただければ调整いたします。",
            "closing": "どうぞよろしくお願い申し上げます。"
        }
    
    def _generate_lead_report(
        self,
        leads: List[LeadScore],
        profiles: List[CustomerProfile],
        approach_plans: List[Dict]
    ) -> str:
        """生成客户列表报告"""
        
        # 创建排名表格
        lead_table = "\n".join([
            f"| {i+1} | {lead.company_name} | {lead.score}点 | {', '.join(lead.match_reasons[:2])} |"
            for i, lead in enumerate(leads[:10])
        ])
        
        sections = {
            "1. サマリー": f"""
総リード数: {len(leads)}件
高優先度（HOT）: {len([l for l in leads if l.score >= 80])}件
優先度（ウォーム）: {len([l for l in leads if 60 <= l.score < 80])}件
ナーチャリング: {len([l for l in leads if l.score < 60])}件
""",
            "2. トップ10リーディングリスト": f"""
| 順位 | 企業名 | スコア | マッチング理由 |
|------|--------|--------|---------------|
{lead_table}
""",
            "3. アプローチ戦略": f"""
{chr(10).join([f"**{plan['company']}**\n- 優先度: {plan['priority']}\n- チャネル: {', '.join([c['type'] for c in plan['channels']])}" for plan in approach_plans[:5]])}
"""
        }
        
        return self.create_report("ターゲット顧客リスト", sections)
    
    async def generate_sales_materials(
        self,
        customer: CustomerProfile,
        solution_summary: Dict[str, Any]
    ) -> Dict[str, str]:
        """生成销售材料"""
        return {
            "presentation": self._create_presentation(customer, solution_summary),
            "proposal": self._create_proposal(customer, solution_summary),
            "case_study": self._create_case_study(customer.industry)
        }
    
    def _create_presentation(
        self,
        customer: CustomerProfile,
        solution_summary: Dict
    ) -> str:
        """创建演示文稿大纲"""
        return f"""
タイトル: {customer.company_name}様向けDX推進プレゼンテーション

構成:
1. 現状の課題分析
2. 解决方案のご提案
3. 導入効果試算
4. 事例紹介
5. 次のステップ
"""
    
    def _create_proposal(self, customer: CustomerProfile, solution: Dict) -> str:
        """创建提案书"""
        return f"""
{customer.company_name}様へ

提案書ver1.0

1. ご課題
{chr(10).join(['- ' + p for p in customer.pain_points])}

2. 当社の解决方案
[詳細を记载]

3. 導入効果
[数值目标を记载]

4. お見積もり
[価格を记载]

5. スケジュール
[導入予定期間を记载]
"""
    
    def _create_case_study(self, industry: str) -> str:
        """创建案例研究"""
        return f"""
【{industry}業界】導入事例

客户: A社（{industry}）
課題: 業務効率化、データ活用
導入効果: 
- 作業時間 30%削減
- データ抽出時間 80%削減
- 意思決定速度 2倍向上
"""
