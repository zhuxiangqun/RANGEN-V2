#!/usr/bin/env python3
"""
ADR Documentation Exporter

自动将 ADR 注册表导出为 Markdown 文档
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.core.adr_registry import ADRRegistry, ADRStatus
from src.core.adr_examples import initialize_sample_adrs


def get_status_icon(status: ADRStatus) -> str:
    """获取状态图标"""
    icons = {
        ADRStatus.PROPOSED: "🔶",
        ADRStatus.ACCEPTED: "✅",
        ADRStatus.DEPRECATED: "❌",
        ADRStatus.SUPERSEDED: "📦"
    }
    return icons.get(status, "❓")


def adr_to_markdown(adr) -> str:
    """单个 ADR 转 Markdown"""
    lines = []
    
    # 标题
    lines.append(f"## {adr.adr_id}: {adr.title} {get_status_icon(adr.status)}\n")
    
    # 元数据
    lines.append(f"**日期**: {adr.date_created}")
    lines.append(f"**作者**: {adr.author}")
    lines.append(f"**状态**: {adr.status.value}\n")
    
    # 背景
    lines.append("### 背景")
    lines.append(adr.background.strip() + "\n")
    
    # 决策
    lines.append("### 决策")
    lines.append(adr.decision.strip() + "\n")
    
    # 后果
    lines.append("### 后果")
    lines.append(adr.consequences.strip() + "\n")
    
    # 替代方案
    if adr.alternatives_considered:
        lines.append("### 考虑的替代方案")
        for alt in adr.alternatives_considered:
            lines.append(f"- {alt}")
        lines.append("")
    
    # 标签
    if adr.tags:
        lines.append(f"**标签**: {', '.join(adr.tags)}\n")
    
    # 关联
    if adr.supersedes:
        lines.append(f"**取代**: {adr.supersedes}\n")
    if adr.superseded_by:
        lines.append(f"**被取代**: {adr.superseded_by}\n")
    
    lines.append("---\n")
    
    return "\n".join(lines)


def export_adrs_to_markdown(
    output_dir: str = "docs/architecture/adr",
    filename: str = "INDEX.md"
) -> str:
    """
    导出 ADR 文档
    
    Args:
        output_dir: 输出目录
        filename: 索引文件名
    
    Returns:
        导出的文件路径
    """
    # 初始化 ADR
    initialize_sample_adrs()
    registry = ADRRegistry()
    
    # 获取所有 ADR
    all_adrs = sorted(registry.get_all(), key=lambda x: x.adr_id)
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成索引内容
    index_lines = [
        "# ADR (Architecture Decision Records)",
        "",
        "> 本文档自动从代码生成。",
        "",
        "## 目录",
        ""
    ]
    
    # 添加目录项
    for adr in all_adrs:
        index_lines.append(f"- [{adr.adr_id}](#{adr.adr_id.lower()})")
    
    index_lines.append("")
    index_lines.append("---\n")
    
    # 添加每个 ADR
    for adr in all_adrs:
        index_lines.append(adr_to_markdown(adr))
    
    # 写入索引文件
    index_content = "\n".join(index_lines)
    index_file = output_path / filename
    index_file.write_text(index_content, encoding='utf-8')
    
    print(f"✅ ADR 文档已导出到: {index_file}")
    
    # 同时导出每个 ADR 为单独文件
    for adr in all_adrs:
        adr_file = output_path / f"{adr.adr_id.lower()}.md"
        adr_file.write_text(adr_to_markdown(adr), encoding='utf-8')
        print(f"   📄 {adr.adr_id}.md")
    
    return str(index_file)


def export_summary() -> str:
    """导出 ADR 摘要"""
    initialize_sample_adrs()
    registry = ADRRegistry()
    
    lines = ["# ADR 摘要\n"]
    
    # 统计
    all_adrs = registry.get_all()
    active_adrs = registry.get_active()
    
    lines.append(f"**总数**: {len(all_adrs)}")
    lines.append(f"**活跃**: {len(active_adrs)}\n")
    
    # 按状态分组
    lines.append("### 按状态")
    for status in ADRStatus:
        count = len(registry.get_by_status(status))
        if count > 0:
            lines.append(f"- {get_status_icon(status)} {status.value}: {count}")
    
    # 按标签分组
    tag_counts = {}
    for adr in all_adrs:
        for tag in adr.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    if tag_counts:
        lines.append("\n### 按标签")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {tag}: {count}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 导出所有 ADR
    export_adrs_to_markdown()
    
    # 导出摘要
    print("\n" + "="*50)
    print(export_summary())
