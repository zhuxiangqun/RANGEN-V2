#!/usr/bin/env python3
"""
工具到Skill的映射表

用于将旧系统的工具名称映射到新系统的Skill
"""

import os

# 旧工具名 -> 新Skill名 (使用已存在的Skill)
TOOL_TO_SKILL_MAP = {
    # 计算和推理
    "calculator": "calculator-skill",      # 需创建
    "reasoning": "reasoning-chain",        # 已存在
    
    # 搜索和检索
    "search": "web-search",                # 已存在
    "web_search": "web-search",            # 已存在
    "real_search": "web-search",           # 已存在 (可创建 real-time-search)
    "rag": "rag-retrieval",                # 已存在
    "knowledge_retrieval": "knowledge-graph",  # 已存在
    
    # 生成和回答
    "answer_generation": "answer-generation",  # 已存在
    "citation": "citation-generation",     # 已存在
    
    # 多模态
    "multimodal": "multimodal-skill",      # 需创建
    "browser": "browser-skill",            # 需创建
    "file_read": "file-read-skill",        # 需创建
}

# Skill配置目录
SKILL_BASE_PATH = "src/agents/skills/bundled"


def get_skill_name(tool_name: str) -> str:
    """获取工具对应的Skill名称"""
    return TOOL_TO_SKILL_MAP.get(tool_name, tool_name)


def get_skill_path(tool_name: str) -> str:
    """获取Skill目录路径"""
    skill_name = get_skill_name(tool_name)
    return f"{SKILL_BASE_PATH}/{skill_name}"


def is_skill_available(tool_name: str) -> bool:
    """检查Skill是否可用"""
    skill_path = get_skill_path(tool_name)
    return os.path.exists(skill_path)


def list_missing_skills():
    """列出缺失的Skills"""
    missing = []
    for tool_name in TOOL_TO_SKILL_MAP:
        if not is_skill_available(tool_name):
            missing.append((tool_name, get_skill_name(tool_name)))
    return missing


# 导出
__all__ = [
    "TOOL_TO_SKILL_MAP",
    "get_skill_name",
    "get_skill_path",
    "is_skill_available",
    "list_missing_skills",
]
