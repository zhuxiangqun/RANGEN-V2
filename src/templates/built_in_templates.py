#!/usr/bin/env python3
"""
内置模板模块 - 开箱即用的自动化场景
对齐pc-agent-loop的5个核心SOP
"""
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Template:
    """技能模板"""
    name: str
    description: str
    category: str
    triggers: List[str]
    keywords: List[str]
    steps: List[Dict[str, Any]]
    source: str = "built_in"


class BuiltInTemplates:
    """内置模板集合
    
    对齐pc-agent-loop的5个核心SOP:
    1. memory_management_sop - 记忆管理
    2. autonomous_operation_sop - 自主任务执行
    3. scheduled_task_sop - 定时任务
    4. web_setup_sop - 浏览器环境引导
    5. desktop_control_sop - 桌面控制
    """
    
    TEMPLATES = {
        # ===== 通讯类 =====
        "wechat_read_messages": {
            "name": "读取微信消息",
            "description": "读取微信未读消息",
            "category": "communication",
            "triggers": ["读取微信", "查看消息", "read wechat"],
            "keywords": ["wechat", "微信", "message", "消息", "unread"],
            "steps": [
                {"hand": "adb_hand", "action": "connect"},
                {"hand": "adb_hand", "action": "start_app", "package": "com.tencent.mm"},
                {"hand": "adb_hand", "action": "wait", "seconds": 3},
                {"hand": "adb_hand", "action": "screenshot"}
            ]
        },
        "email_send": {
            "name": "发送邮件",
            "description": "通过Gmail发送邮件",
            "category": "communication",
            "triggers": ["发邮件", "send email"],
            "keywords": ["email", "gmail", "mail", "send"],
            "steps": [
                {"hand": "browser_control", "action": "navigate", "url": "https://mail.google.com/mail/u/0/#inbox?compose=new"},
                {"hand": "browser_control", "action": "wait", "seconds": 3}
            ]
        },
        
        # ===== 数据分析类 =====
        "stock_monitor": {
            "name": "股票价格监控",
            "description": "监控股票价格并告警",
            "category": "data_analysis",
            "triggers": ["监控股票", "stock alert"],
            "keywords": ["stock", "股票", "price", "monitor", "alert"],
            "steps": [
                {"hand": "web_scan", "url": "https://quote.eastmoney.com/sh000001.html"},
                {"hand": "code_run", "language": "python", "code": "import json; print(json.dumps({'symbol': '000001', 'price': 3100}))"}
            ]
        },
        
        # ===== 开发运维类 =====
        "git_auto_commit": {
            "name": "自动Git提交",
            "description": "自动提交代码更改",
            "category": "development",
            "triggers": ["git提交", "commit code"],
            "keywords": ["git", "commit", "提交"],
            "steps": [
                {"hand": "code_run", "language": "bash", "code": "git status && git add -A && git commit -m 'Auto update'"}
            ]
        },
        "git_push": {
            "name": "Git推送",
            "description": "推送到远程仓库",
            "category": "development",
            "triggers": ["git推送", "git push"],
            "keywords": ["git", "push", "remote"],
            "steps": [
                {"hand": "code_run", "language": "bash", "code": "git push origin main"}
            ]
        },
        
        # ===== 系统操作类 =====
        "system_screenshot": {
            "name": "屏幕截图",
            "description": "截取当前屏幕",
            "category": "system",
            "triggers": ["截图", "screenshot"],
            "keywords": ["screenshot", "截图", "capture"],
            "steps": [
                {"hand": "keyboard_mouse", "operation": "hotkey", "keys": ["command", "shift", "4"]}
            ]
        },
        "open_application": {
            "name": "打开应用",
            "description": "通过Spotlight打开应用程序",
            "category": "system",
            "triggers": ["打开应用", "open app"],
            "keywords": ["app", "应用", "open"],
            "steps": [
                {"hand": "keyboard_mouse", "operation": "hotkey", "keys": ["command", "space"]},
                {"hand": "keyboard_mouse", "operation": "type", "text": "Safari"},
                {"hand": "keyboard_mouse", "operation": "press", "key": "return"}
            ]
        },
        
        # ===== 网页自动化类 =====
        "web_setup": {
            "name": "浏览器环境配置",
            "description": "配置浏览器扩展和环境",
            "category": "web_automation",
            "triggers": ["配置浏览器", "web setup"],
            "keywords": ["browser", "浏览器", "setup", "extension"],
            "steps": [
                {"hand": "browser_control", "action": "navigate", "url": "https://chrome://extensions"},
                {"hand": "browser_control", "action": "wait", "seconds": 2}
            ]
        },
        
        # ===== 定时任务类 =====
        "scheduled_task": {
            "name": "定时执行任务",
            "description": "设置定时执行的自动化任务",
            "category": "system",
            "triggers": ["定时任务", "scheduled task"],
            "keywords": ["schedule", "定时", "cron", "task"],
            "steps": [
                {"hand": "code_run", "language": "python", "code": "import schedule; schedule.every().day.at('10:00').do(lambda: print('task'))"}
            ]
        },
        
        # ===== 桌面控制类 =====
        "desktop_control": {
            "name": "桌面物理控制",
            "description": "键盘鼠标的物理级控制",
            "category": "system",
            "triggers": ["桌面控制", "desktop control"],
            "keywords": ["desktop", "keyboard", "mouse", "control"],
            "steps": [
                {"hand": "keyboard_mouse", "operation": "move", "x": 500, "y": 500},
                {"hand": "keyboard_mouse", "operation": "click"}
            ]
        }
    }
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载所有模板"""
        for template_id, template_data in self.TEMPLATES.items():
            self.templates[template_id] = Template(
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                triggers=template_data["triggers"],
                keywords=template_data["keywords"],
                steps=template_data["steps"],
                source="built_in"
            )
        
        logger.info(f"Loaded {len(self.templates)} built-in templates")
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """获取模板"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[Template]:
        """列出模板"""
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())
    
    def search_templates(self, query: str) -> List[Template]:
        """搜索模板"""
        query_words = set(query.lower().split())
        results = []
        
        for template in self.templates.values():
            # 检查触发词
            for trigger in template.triggers:
                if any(word in trigger.lower() for word in query_words):
                    results.append(template)
                    break
            
            # 检查关键词
            for keyword in template.keywords:
                if any(word in keyword.lower() for word in query_words):
                    if template not in results:
                        results.append(template)
                        break
        
        return results
    
    def get_template_as_sop(self, template_id: str):
        """将模板转换为SOP格式"""
        from src.core.sop_learning import StandardOperatingProcedure, SOPStep, SOPCategory
        
        template = self.get_template(template_id)
        if not template:
            return None
        
        # 映射类别
        category_map = {
            "communication": SOPCategory.API_INTEGRATION,
            "data_analysis": SOPCategory.DATA_PROCESSING,
            "development": SOPCategory.SYSTEM_OPERATION,
            "system": SOPCategory.SYSTEM_OPERATION,
            "web_automation": SOPCategory.API_INTEGRATION
        }
        
        # 转换步骤
        steps = []
        for i, step_data in enumerate(template.steps):
            step = SOPStep(
                step_id=f"step_{i+1}",
                hand_name=step_data.get("hand", ""),
                parameters={k: v for k, v in step_data.items() if k != "hand"},
                description=f"步骤{i+1}: {step_data.get('hand', '')}"
            )
            steps.append(step)
        
        # 创建SOP
        sop = StandardOperatingProcedure(
            sop_id=f"template_{template_id}",
            name=template.name,
            description=template.description,
            category=category_map.get(template.category, SOPCategory.CUSTOM),
            level="l3_task",
            steps=steps,
            tags=template.keywords,
            metadata={"source": "built_in_template", "template_id": template_id}
        )
        
        return sop
    
    def export_templates(self) -> str:
        """导出所有模板"""
        return json.dumps(
            {k: {
                "name": v.name,
                "description": v.description,
                "category": v.category,
                "triggers": v.triggers,
                "keywords": v.keywords,
                "steps": v.steps
            } for k, v in self.templates.items()},
            indent=2,
            ensure_ascii=False
        )


# 全局实例
_templates: Optional[BuiltInTemplates] = None


def get_built_in_templates() -> BuiltInTemplates:
    """获取内置模板单例"""
    global _templates
    if _templates is None:
        _templates = BuiltInTemplates()
    return _templates


def get_template(template_id: str) -> Optional[Template]:
    """获取指定模板"""
    return get_built_in_templates().get_template(template_id)


def list_templates(category: Optional[str] = None) -> List[Template]:
    """列出模板"""
    return get_built_in_templates().list_templates(category)


def search_templates(query: str) -> List[Template]:
    """搜索模板"""
    return get_built_in_templates().search_templates(query)


import json
