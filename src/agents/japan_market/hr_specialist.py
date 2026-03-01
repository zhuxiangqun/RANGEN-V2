#!/usr/bin/env python3
"""
日本人力资源专家
专注于日本雇佣法规、人才招聘、组织发展和员工关系管理
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import JapanMarketAgent, JapanAgentConfig, JapanAgentFactory


class JapanHRSpecialist(JapanMarketAgent):
    """日本人力资源专家"""
    
    def __init__(self, config: Optional[JapanAgentConfig] = None):
        if config is None:
            config = JapanAgentConfig(
                agent_id="japan_hr_specialist_001",
                role_name="日本人材・労務専門家",
                role_name_en="Japan HR Specialist",
                domain_expertise="日本労務管理・人材採用・組織開発",
                expertise_jp="日本の労働法、雇用慣行、人材採用、給与計算、社会保険、組織文化の専門知識を持ち、日本市場でのビジネス展開における人的資源の最適化と法的コンプライアンスを支援します。",
                capabilities=["人材採用", "労務管理", "給与計算", "社会保険手続き", "組織開発", "従業員関係"],
                tools=["採用プラットフォーム", "給与計算ソフト", "労務管理システム"]
            )
        
        super().__init__(
            agent_id=config.agent_id,
            role_name=config.role_name,
            role_name_en=config.role_name_en,
            domain_expertise=config.domain_expertise,
            expertise_jp=config.expertise_jp,
            config=config
        )
        
        # 人力资源特定字段
        self.hr_expertise_areas = [
            "日本労働法・雇用契約",
            "採用活動・人材紹介",
            "給与計算・賞与制度",
            "社会保険・労働保険手続き",
            "従業員評価・昇進制度",
            "研修・能力開発",
            "ダイバーシティ・インクルージョン",
            "労使関係・紛争解決"
        ]
        
        # 更新系统提示
        self._enhance_system_prompt()
    
    def _enhance_system_prompt(self):
        """增强人力资源专家系统提示"""
        hr_expertise = "\n".join([f"• {area}" for area in self.hr_expertise_areas])
        
        enhanced_prompt = f"""
{self.system_prompt}

【人事・労務専門分野】
{hr_expertise}

【日本の主要労働法規】
1. 労働基準法（Labor Standards Act） - 労働条件の最低基準
2. 労働契約法（Labor Contract Act） - 雇用契約の基本ルール
3. 労働者派遣法（Worker Dispatch Act） - 派遣労働の規制
4. 男女雇用機会均等法（Equal Employment Opportunity Act） - 差別禁止
5. 育児・介護休業法（Childcare and Family Care Leave Act） - 休業制度
6. 最低賃金法（Minimum Wage Act） - 賃金の最低基準
7. 社会保険関連法（Social Insurance Acts） - 健康保険、厚生年金、雇用保険

【日本の雇用慣行の特徴】
• 終身雇用制度：長期雇用を前提とした慣行（徐々に変化中）
• 年功序列：年齢や勤続年数に基づく昇進・昇給
• 春季闘争（春闘）：年に一度の賃金交渉
• 転勤制度：会社都合による全国転勤
• 退職金制度：退職時に支払われる一時金
• ボーナス：夏季・冬季の賞与（基本給の数ヶ月分）

【人事管理の原則】
• 法令遵守の徹底：日本の労働法規は厳格に遵守
• 文化的配慮：日本的雇用慣行を理解した対応
• 文書化の重要性：すべての契約・合意を文書化
• 継続的コミュニケーション：定期的な面談・フィードバック
• 福利厚生の充実：社会保険・追加福利による従業員満足度向上

【具体的な支援内容】
• 日本での従業員採用計画と実行
• 雇用契約書の作成と労務管理
• 給与計算・賞与制度の設計
• 社会保険・労働保険の加入手続き
• 研修プログラムの開発と実施
• 従業員評価制度の構築
• 労使関係の構築と紛争予防
"""
        self.system_prompt = enhanced_prompt
    
    async def create_hiring_plan(self, company_size: int, business_type: str, growth_stage: str) -> Dict[str, Any]:
        """创建招聘计划"""
        task = f"""
以下の条件に基づき、日本での採用計画を作成してください：
- 会社規模：{company_size}名
- 事業内容：{business_type}
- 成長ステージ：{growth_stage}

日本の労働市場、雇用慣行、法規制を考慮してください。
"""
        
        result = await self.process_task(task)
        
        # 添加人力资源特定分析
        hiring_analysis = await self._analyze_hiring_needs(company_size, business_type, growth_stage)
        
        result["hiring_analysis"] = hiring_analysis
        result["plan_type"] = "hiring_plan"
        
        return result
    
    async def design_compensation_plan(self, positions: List[str], experience_levels: List[str], location: str = "東京") -> Dict[str, Any]:
        """设计薪酬计划"""
        positions_str = "、".join(positions)
        experience_str = "、".join(experience_levels)
        
        task = f"""
以下の条件に基づき、日本の{location}での適切な給与体系を設計してください：
- 職種：{positions_str}
- 経験レベル：{experience_str}
- 地域：{location}

日本の給与相場、税制、社会保険料を考慮してください。
"""
        
        result = await self.process_task(task)
        
        # 添加薪酬特定分析
        compensation_analysis = await self._analyze_compensation_market(positions, experience_levels, location)
        
        result["compensation_analysis"] = compensation_analysis
        result["location"] = location
        
        return result
    
    async def setup_hr_compliance(self, employee_count: int, business_operations: List[str]) -> Dict[str, Any]:
        """设置人力资源合规"""
        operations_str = "、".join(business_operations)
        
        task = f"""
以下の条件に基づき、日本での人事労務コンプライアンス計画を作成してください：
- 従業員数：{employee_count}名
- 事業運営：{operations_str}

日本の労働法、社会保険、税務関連の要件をすべて網羅してください。
"""
        
        result = await self.process_task(task)
        
        # 添加合规特定分析
        compliance_checklist = await self._generate_hr_compliance_checklist(employee_count, business_operations)
        
        result["compliance_checklist"] = compliance_checklist
        result["employee_count"] = employee_count
        
        return result
    
    async def _analyze_hiring_needs(self, size: int, business_type: str, stage: str) -> Dict[str, Any]:
        """分析招聘需求"""
        # 基于公司规模、业务类型和成长阶段分析招聘需求
        position_templates = {
            "technology": [
                {"position": "ソフトウェアエンジニア", "level": "中途", "count": max(1, size // 5)},
                {"position": "プロダクトマネージャー", "level": "中途", "count": max(1, size // 10)},
                {"position": "UI/UXデザイナー", "level": "中途", "count": max(1, size // 15)}
            ],
            "ecommerce": [
                {"position": "EC担当", "level": "中途", "count": max(1, size // 6)},
                {"position": "マーケティング担当", "level": "中途", "count": max(1, size // 8)},
                {"position": "カスタマーサポート", "level": "新卒", "count": max(1, size // 4)}
            ],
            "consulting": [
                {"position": "コンサルタント", "level": "中途", "count": max(1, size // 3)},
                {"position": "アナリスト", "level": "新卒", "count": max(1, size // 4)},
                {"position": "プロジェクトマネージャー", "level": "中途", "count": max(1, size // 8)}
            ]
        }
        
        positions = position_templates.get(business_type.lower(), [
            {"position": "一般事務", "level": "新卒", "count": max(1, size // 3)},
            {"position": "営業担当", "level": "中途", "count": max(1, size // 4)}
        ])
        
        # 调整基于成长阶段
        if stage == "startup":
            # 初创期需要多面手
            for pos in positions:
                pos["count"] = max(1, pos["count"] // 2)
        elif stage == "growth":
            # 成长期需要更多专业人才
            for pos in positions:
                pos["count"] = pos["count"] * 2
        
        # 估算招聘成本和时间
        hiring_timeline = {
            "新卒": {"time_months": 6, "cost_per_hire": 500000},
            "中途": {"time_months": 3, "cost_per_hire": 1000000}
        }
        
        total_cost = 0
        total_time = 0
        for pos in positions:
            level_info = hiring_timeline.get(pos["level"], hiring_timeline["中途"])
            total_cost += level_info["cost_per_hire"] * pos["count"]
            total_time = max(total_time, level_info["time_months"])
        
        return {
            "recommended_positions": positions,
            "total_positions": sum(p["count"] for p in positions),
            "estimated_hiring_timeline_months": total_time,
            "estimated_total_cost": total_cost,
            "recruitment_channels": [
                "リクナビ・マイナビ（新卒）",
                "リクルートエージェント・doda（中途）",
                "Wantedly（スタートアップ向け）",
                "LinkedIn（グローバル人材）"
            ],
            "key_considerations": [
                "日本の就職活動サイクルに合わせる（新卒は4月入社）",
                "中途採用は通年可能だが、転職市場は3-4月、9-10月が活発",
                "外国人採用の場合はビザ手続きが必要"
            ]
        }
    
    async def _analyze_compensation_market(self, positions: List[str], experience_levels: List[str], location: str) -> Dict[str, Any]:
        """分析薪酬市场"""
        # 基于职位、经验级别和地区提供薪酬分析
        salary_data = {
            "東京": {
                "ソフトウェアエンジニア": {"entry": 4000000, "mid": 6000000, "senior": 9000000},
                "プロダクトマネージャー": {"entry": 5000000, "mid": 7500000, "senior": 11000000},
                "マーケティング担当": {"entry": 3500000, "mid": 5000000, "senior": 7500000},
                "営業担当": {"entry": 3800000, "mid": 5500000, "senior": 8000000},
                "一般事務": {"entry": 2800000, "mid": 3500000, "senior": 4500000}
            },
            "大阪": {
                "ソフトウェアエンジニア": {"entry": 3500000, "mid": 5000000, "senior": 7500000},
                "プロダクトマネージャー": {"entry": 4500000, "mid": 6500000, "senior": 9500000},
                "マーケティング担当": {"entry": 3000000, "mid": 4500000, "senior": 6500000},
                "営業担当": {"entry": 3300000, "mid": 4800000, "senior": 7000000},
                "一般事務": {"entry": 2500000, "mid": 3200000, "senior": 4000000}
            }
        }
        
        location_data = salary_data.get(location, salary_data["東京"])
        
        compensation_analysis = []
        for position in positions:
            position_data = location_data.get(position, location_data.get("一般事務", {"entry": 3000000, "mid": 4000000, "senior": 5000000}))
            
            for level in experience_levels:
                if level == "entry":
                    salary = position_data["entry"]
                elif level == "senior":
                    salary = position_data["senior"]
                else:  # mid
                    salary = position_data["mid"]
                
                # 估算总薪酬（基本工资+奖金）
                total_compensation = salary * 1.3  # 假设奖金为30%
                
                # 估算社会保险费用（公司负担部分）
                social_insurance = salary * 0.15  # 约15%
                
                compensation_analysis.append({
                    "position": position,
                    "experience_level": level,
                    "base_salary_per_year": salary,
                    "estimated_bonus_percentage": 30,
                    "total_compensation_per_year": total_compensation,
                    "employer_social_insurance_per_year": social_insurance,
                    "total_employer_cost_per_year": total_compensation + social_insurance,
                    "market_comparison": "competitive" if salary >= position_data["mid"] else "below_market"
                })
        
        return {
            "location": location,
            "salary_data_source": "日本の給与調査データ（2024年）",
            "positions_analyzed": compensation_analysis,
            "additional_benefits_recommendations": [
                "健康保険・厚生年金（法定）",
                "雇用保険（法定）",
                "退職金制度（任意）",
                "定期健康診断（法定）",
                "住宅手当・通勤手当（任意）",
                "社員旅行・レクリエーション（任意）"
            ],
            "compliance_requirements": [
                "最低賃金法の遵守（地域別最低賃金）",
                "時間外労働に対する割増賃金（25-50%）",
                "年次有給休暇の付与（法定）",
                "社会保険・労働保険の加入"
            ]
        }
    
    async def _generate_hr_compliance_checklist(self, employee_count: int, operations: List[str]) -> List[Dict[str, Any]]:
        """生成人力资源合规检查清单"""
        # 基于员工数量和业务类型生成合规检查清单
        compliance_items = []
        
        # 基本合规项目（所有公司）
        compliance_items.extend([
            {
                "item": "労働基準監督署への届出",
                "description": "事業所設置届、労災保険関係成立届",
                "deadline": "事業開始後10日以内",
                "priority": "high"
            },
            {
                "item": "社会保険・労働保険加入",
                "description": "健康保険、厚生年金、雇用保険、労災保険",
                "deadline": "従業員雇用時",
                "priority": "high"
            },
            {
                "item": "就業規則の作成・届出",
                "description": "常時10名以上の場合、労働基準監督署へ届出必要",
                "deadline": "10名到達後",
                "priority": employee_count >= 10 and "high" or "medium"
            }
        ])
        
        # 基于业务类型的特定合规
        if "manufacturing" in operations or "工場" in "".join(operations).lower():
            compliance_items.extend([
                {
                    "item": "労働安全衛生法対応",
                    "description": "安全管理者選任、安全衛生委員会設置",
                    "deadline": "従業員50名以上で必要",
                    "priority": employee_count >= 50 and "high" or "medium"
                },
                {
                    "item": "危険物取扱者資格",
                    "description": "特定の化学物質・機械を扱う場合",
                    "deadline": "事業開始前",
                    "priority": "high"
                }
            ])
        
        if "food" in operations or "飲食" in "".join(operations).lower():
            compliance_items.extend([
                {
                    "item": "食品衛生法対応",
                    "description": "営業許可、食品衛生責任者選任",
                    "deadline": "営業開始前",
                    "priority": "high"
                },
                {
                    "item": "HACCP対応",
                    "description": "食品の安全基準",
                    "deadline": "事業規模により異なる",
                    "priority": "medium"
                }
            ])
        
        if "information" in operations or "情報" in "".join(operations).lower():
            compliance_items.extend([
                {
                    "item": "個人情報保護法対応",
                    "description": "個人情報取扱事業者届出",
                    "deadline": "事業開始後速やかに",
                    "priority": "high"
                },
                {
                    "item": "情報セキュリティ対策",
                    "description": "サイバーセキュリティ基本法対応",
                    "deadline": "継続的",
                    "priority": "high"
                }
            ])
        
        # 基于员工数量的额外要求
        if employee_count >= 5:
            compliance_items.append({
                "item": "産業医の選任",
                "description": "常時50名未満の場合、産業医の選任努力義務",
                "deadline": "従業員雇用時",
                "priority": "medium"
            })
        
        if employee_count >= 10:
            compliance_items.append({
                "item": "衛生委員会の設置",
                "deadline": "従業員10名以上で必要",
                "priority": "high"
            })
        
        if employee_count >= 50:
            compliance_items.extend([
                {
                    "item": "労働時間等設定改善委員会",
                    "description": "時間外労働上限規制対応",
                    "deadline": "従業員50名以上で必要",
                    "priority": "high"
                },
                {
                    "item": "職業訓練実施",
                    "description": "キャリア形成促進助成金対象",
                    "deadline": "継続的",
                    "priority": "medium"
                }
            ])
        
        return compliance_items
    
    def get_hr_expertise_summary(self) -> Dict[str, Any]:
        """获取人力资源专业知识摘要"""
        return {
            "agent_role": self.role_name,
            "hr_areas": self.hr_expertise_areas,
            "language": self.language,
            "focus_markets": ["日本市場"],
            "legal_knowledge": ["労働基準法", "労働契約法", "社会保険関連法"],
            "deliverables_count": len(self.deliverables)
        }


# 工厂方法
def create_japan_hr_specialist() -> JapanHRSpecialist:
    """创建日本人力资源专家"""
    return JapanHRSpecialist()