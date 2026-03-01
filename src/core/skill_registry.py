#!/usr/bin/env python3
"""
技能注册表模块 - 让SOP可被发现/调用
对齐pc-agent-loop的"每任务即技能"理念
"""
import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """技能类别"""
    COMMUNICATION = "communication"      # 通讯类 (微信/邮件)
    DATA_ANALYSIS = "data_analysis"      # 数据分析 (股票/Excel)
    FILE_OPERATIONS = "file_operations"  # 文件操作
    WEB_AUTOMATION = "web_automation"   # 网页自动化
    DEVELOPMENT = "development"         # 开发运维 (Git/Docker)
    SYSTEM = "system"                    # 系统操作
    CUSTOM = "custom"                   # 自定义


class SkillStatus(str, Enum):
    """技能状态"""
    LEARNING = "learning"     # 学习中
    READY = "ready"          # 就绪
    TESTING = "testing"      # 测试中
    DEPRECATED = "deprecated" # 已废弃


@dataclass
class Skill:
    """技能定义
    
    每个SOP可以注册为一个技能，
    支持按场景召回和调用
    """
    skill_id: str
    name: str
    description: str
    category: SkillCategory
    
    # 来源
    source_sop_id: Optional[str] = None  # 来源SOP
    source_type: str = "manual"         # 来源类型: manual, template, learned
    
    # 能力
    keywords: List[str] = field(default_factory=list)  # 关键词
    triggers: List[str] = field(default_factory=list)  # 触发词
    examples: List[str] = field(default_factory=list) # 使用示例
    
    # 状态
    status: SkillStatus = SkillStatus.READY
    usage_count: int = 0                # 使用次数
    success_rate: float = 1.0           # 成功率
    avg_execution_time: float = 0.0    # 平均执行时间
    
    # 时间
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 依赖
    dependencies: List[str] = field(default_factory=list)  # 依赖技能
    
    def __post_init__(self):
        if not self.skill_id:
            content = f"{self.name}_{self.category.value}_{time.time()}"
            self.skill_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "source_sop_id": self.source_sop_id,
            "source_type": self.source_type,
            "keywords": self.keywords,
            "triggers": self.triggers,
            "examples": self.examples,
            "status": self.status.value,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_execution_time": self.avg_execution_time,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "updated_at": self.updated_at,
            "dependencies": self.dependencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        data = data.copy()
        data["category"] = SkillCategory(data.get("category", "custom"))
        data["status"] = SkillStatus(data.get("status", "ready"))
        return cls(**data)


class SkillRegistry:
    """技能注册表
    
    管理所有技能的注册、发现和调用
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.name_index: Dict[str, List[str]] = {}  # 名称 -> skill_ids
        self.category_index: Dict[SkillCategory, List[str]] = {}  # 类别 -> skill_ids
        self.keyword_index: Dict[str, List[str]] = {}  # 关键词 -> skill_ids
        self.trigger_index: Dict[str, List[str]] = {}  # 触发词 -> skill_ids
        
        # 初始化索引
        for cat in SkillCategory:
            self.category_index[cat] = []
        
        logger.info("Skill Registry initialized")
    
    def register(self, skill: Skill) -> str:
        """注册技能
        
        Args:
            skill: 技能实例
            
        Returns:
            skill_id
        """
        # 检查是否已存在同名技能
        if skill.name in self.name_index:
            existing_id = self.name_index[skill.name][0]
            existing = self.skills[existing_id]
            
            # 如果已存在，更新而非重复注册
            logger.info(f"Skill '{skill.name}' already exists, updating...")
            existing.usage_count += skill.usage_count
            existing.updated_at = time.time()
            return existing.skill_id
        
        # 注册新技能
        self.skills[skill.skill_id] = skill
        
        # 更新索引
        self._update_indices(skill)
        
        logger.info(f"Registered skill: {skill.name} ({skill.category.value})")
        return skill.skill_id
    
    def register_from_sop(self, sop, relevance: float = 1.0) -> str:
        """从SOP注册技能
        
        Args:
            sop: StandardOperatingProcedure实例
            relevance: 相关性分数
            
        Returns:
            skill_id
        """
        # 推断类别
        category = self._infer_category(sop)
        
        # 提取关键词
        keywords = self._extract_keywords(sop)
        
        # 推断触发词
        triggers = self._extract_triggers(sop)
        
        skill = Skill(
            skill_id="",
            name=sop.name,
            description=sop.description,
            category=category,
            source_sop_id=sop.sop_id,
            source_type="learned",
            keywords=keywords,
            triggers=triggers,
            examples=sop.tags,
            success_rate=sop.success_rate,
            usage_count=sop.execution_count
        )
        
        return self.register(skill)
    
    def _infer_category(self, sop) -> SkillCategory:
        """推断SOP类别"""
        name_lower = sop.name.lower()
        desc_lower = sop.description.lower()
        tags = [t.lower() for t in sop.tags]
        
        text = " ".join([name_lower, desc_lower] + tags)
        
        if any(w in text for w in ["wechat", "微信", "mail", "邮件", "message", "消息"]):
            return SkillCategory.COMMUNICATION
        elif any(w in text for w in ["stock", "股票", "data", "分析", "excel"]):
            return SkillCategory.DATA_ANALYSIS
        elif any(w in text for w in ["file", "文件", "read", "write"]):
            return SkillCategory.FILE_OPERATIONS
        elif any(w in text for w in ["web", "browser", "网页", "自动化"]):
            return SkillCategory.WEB_AUTOMATION
        elif any(w in text for w in ["git", "docker", "deploy", "开发", "devops"]):
            return SkillCategory.DEVELOPMENT
        elif any(w in text for w in ["system", "系统", "process", "进程"]):
            return SkillCategory.SYSTEM
        else:
            return SkillCategory.CUSTOM
    
    def _extract_keywords(self, sop) -> List[str]:
        """提取关键词"""
        keywords = set()
        
        # 从名称提取
        words = sop.name.replace("_", " ").replace("-", " ").split()
        keywords.update(w.lower() for w in words if len(w) > 2)
        
        # 从描述提取
        words = sop.description.replace("_", " ").replace("-", " ").split()
        keywords.update(w.lower() for w in words if len(w) > 3)
        
        # 从标签提取
        keywords.update(t.lower() for t in sop.tags)
        
        return list(keywords)[:20]  # 最多20个
    
    def _extract_triggers(self, sop) -> List[str]:
        """提取触发词"""
        triggers = []
        
        # 基于类别添加默认触发词
        if sop.category.value in ["api_integration", "web_automation"]:
            triggers.extend(["执行", "运行", "do", "run"])
        
        if sop.category.value == "data_processing":
            triggers.extend(["分析", "处理", "analyze", "process"])
        
        # 从名称提取动作词
        name_words = sop.name.split("_")
        if name_words:
            triggers.append(name_words[0])
        
        return triggers[:10]  # 最多10个
    
    def _update_indices(self, skill: Skill):
        """更新索引"""
        # 名称索引
        if skill.name not in self.name_index:
            self.name_index[skill.name] = []
        self.name_index[skill.name].append(skill.skill_id)
        
        # 类别索引
        self.category_index[skill.category].append(skill.skill_id)
        
        # 关键词索引
        for kw in skill.keywords:
            if kw not in self.keyword_index:
                self.keyword_index[kw] = []
            self.keyword_index[kw].append(skill.skill_id)
        
        # 触发词索引
        for trigger in skill.triggers:
            if trigger not in self.trigger_index:
                self.trigger_index[trigger] = []
            self.trigger_index[trigger].append(skill.skill_id)
    
    def discover(self, query: str, category: Optional[SkillCategory] = None, 
                 limit: int = 10) -> List[Dict[str, Any]]:
        """发现技能
        
        按自然语言查询发现相关技能
        
        Args:
            query: 查询文本
            category: 可选类别过滤
            limit: 返回数量限制
            
        Returns:
            相关技能列表
        """
        query_words = set(query.lower().split())
        scores: Dict[str, float] = {}
        
        # 遍历所有技能
        for skill_id, skill in self.skills.items():
            # 类别过滤
            if category and skill.category != category:
                continue
            
            # 状态过滤
            if skill.status == SkillStatus.DEPRECATED:
                continue
            
            score = 0.0
            
            # 关键词匹配
            skill_keywords = set(skill.keywords)
            if skill_keywords:
                overlap = len(query_words.intersection(skill_keywords))
                score += overlap * 2.0
            
            # 触发词匹配
            skill_triggers = set(skill.triggers)
            if skill_triggers:
                overlap = len(query_words.intersection(skill_triggers))
                score += overlap * 1.5
            
            # 名称匹配
            name_words = set(skill.name.lower().split())
            if name_words:
                overlap = len(query_words.intersection(name_words))
                score += overlap * 3.0
            
            # 使用次数加权
            score += min(skill.usage_count / 10, 1.0)
            
            # 成功率加权
            score += skill.success_rate * 0.5
            
            if score > 0:
                scores[skill_id] = score
        
        # 排序
        sorted_skills = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 返回结果
        results = []
        for skill_id, score in sorted_skills[:limit]:
            skill = self.skills[skill_id]
            results.append({
                "skill": skill,
                "score": score,
                "skill_id": skill_id
            })
        
        return results
    
    def recall(self, context: str, max_results: int = 5) -> List[Skill]:
        """回忆技能
        
        按上下文自动召回相关技能
        
        Args:
            context: 上下文描述
            max_results: 最大返回数量
            
        Returns:
            技能列表
        """
        discoveries = self.discover(context, limit=max_results)
        return [d["skill"] for d in discoveries]
    
    def use_skill(self, skill_id: str, success: bool = True, 
                  execution_time: float = 0.0) -> bool:
        """记录技能使用
        
        Args:
            skill_id: 技能ID
            success: 是否成功
            execution_time: 执行时间
            
        Returns:
            是否成功
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill not found: {skill_id}")
            return False
        
        skill = self.skills[skill_id]
        
        # 更新统计
        skill.usage_count += 1
        skill.last_used = time.time()
        
        # 更新成功率
        if skill.usage_count > 1:
            skill.success_rate = (
                (skill.success_rate * (skill.usage_count - 1) + (1.0 if success else 0.0))
                / skill.usage_count
            )
        
        # 更新平均执行时间
        if execution_time > 0:
            if skill.avg_execution_time > 0:
                skill.avg_execution_time = (
                    (skill.avg_execution_time * (skill.usage_count - 1) + execution_time)
                    / skill.usage_count
                )
            else:
                skill.avg_execution_time = execution_time
        
        return True
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def list_skills(self, category: Optional[SkillCategory] = None,
                    status: Optional[SkillStatus] = None,
                    limit: int = 100) -> List[Skill]:
        """列出技能"""
        result = []
        
        for skill in self.skills.values():
            if category and skill.category != category:
                continue
            if status and skill.status != status:
                continue
            result.append(skill)
        
        # 按使用次数排序
        result.sort(key=lambda s: s.usage_count, reverse=True)
        
        return result[:limit]
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if skill_id not in self.skills:
            return False
        
        skill = self.skills.pop(skill_id)
        
        # 从索引中移除
        if skill.name in self.name_index:
            self.name_index[skill.name].remove(skill_id)
        
        if skill.skill_id in self.category_index[skill.category]:
            self.category_index[skill.category].remove(skill_id)
        
        for kw in skill.keywords:
            if skill_id in self.keyword_index.get(kw, []):
                self.keyword_index[kw].remove(skill_id)
        
        logger.info(f"Deleted skill: {skill.name}")
        return True
    
    def export_skills(self) -> str:
        """导出技能"""
        data = {
            "export_time": time.time(),
            "count": len(self.skills),
            "skills": [s.to_dict() for s in self.skills.values()]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def import_skills(self, json_data: str) -> Dict[str, int]:
        """导入技能"""
        data = json.loads(json_data)
        
        imported = 0
        skipped = 0
        
        for skill_data in data.get("skills", []):
            try:
                skill = Skill.from_dict(skill_data)
                self.register(skill)
                imported += 1
            except Exception as e:
                logger.warning(f"Failed to import skill: {e}")
                skipped += 1
        
        return {"imported": imported, "skipped": skipped, "total": len(self.skills)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        stats = {
            "total": len(self.skills),
            "by_category": {},
            "by_status": {},
            "total_usages": sum(s.usage_count for s in self.skills.values()),
            "avg_success_rate": 0.0
        }
        
        # 按类别统计
        for cat in SkillCategory:
            count = len(self.category_index[cat])
            if count > 0:
                stats["by_category"][cat.value] = count
        
        # 按状态统计
        for status in SkillStatus:
            count = sum(1 for s in self.skills.values() if s.status == status)
            if count > 0:
                stats["by_status"][status.value] = count
        
        # 平均成功率
        if self.skills:
            stats["avg_success_rate"] = sum(s.success_rate for s in self.skills.values()) / len(self.skills)
        
        return stats


# 全局实例
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取技能注册表单例"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
