#!/usr/bin/env python3
"""
Agent迁移状态同步脚本

自动同步Agent迁移状态到相关文档：
- SYSTEM_AGENTS_OVERVIEW.md
- docs/migration_implementation_log.md

使用方法:
python scripts/sync_migration_status.py --agent AgentName --status "新状态" --description "状态描述"
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

class MigrationStatusSyncer:
    """迁移状态同步器"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.overview_file = self.project_root / "SYSTEM_AGENTS_OVERVIEW.md"
        self.log_file = self.project_root / "docs" / "migration_implementation_log.md"

    def update_agent_status(self, agent_name: str, new_status: str, description: str):
        """更新Agent状态到两个文档"""

        print(f"🔄 同步Agent状态: {agent_name}")
        print(f"   新状态: {new_status}")
        print(f"   描述: {description}")

        # 更新SYSTEM_AGENTS_OVERVIEW.md
        self._update_overview_status(agent_name, new_status, description)

        # 更新docs/migration_implementation_log.md
        self._update_migration_log_status(agent_name, new_status, description)

        # 添加更新日志
        self._add_update_log_entry(agent_name, new_status, description)

        print("✅ 状态同步完成")

    def _update_overview_status(self, agent_name: str, new_status: str, description: str):
        """更新SYSTEM_AGENTS_OVERVIEW.md中的状态"""

        with open(self.overview_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找Agent状态行
        pattern = rf'\| \*\*{re.escape(agent_name)}\*\* \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|'
        match = re.search(pattern, content, re.MULTILINE)

        if match:
            old_target = match.group(1).strip()
            old_status = match.group(2).strip()
            old_priority = match.group(3).strip()
            old_description = match.group(4).strip()

            # 构造新行，保持原有格式
            new_line = f'| **{agent_name}** | {old_target} | {new_status} | {old_priority} | {description} |'

            # 替换整行
            old_line = f'| **{agent_name}** | {old_target} | {old_status} | {old_priority} | {old_description} |'
            content = content.replace(old_line, new_line)

            with open(self.overview_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"   ✅ SYSTEM_AGENTS_OVERVIEW.md 已更新")
        else:
            print(f"   ⚠️ 在SYSTEM_AGENTS_OVERVIEW.md中未找到Agent: {agent_name}")

    def _update_migration_log_status(self, agent_name: str, new_status: str, description: str):
        """更新docs/migration_implementation_log.md中的状态"""

        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 在Agent迁移状态总览表格中查找并更新
        lines = content.split('\n')
        updated = False

        for i, line in enumerate(lines):
            if f'{agent_name} |' in line and ('|' in line):
                # 这是表格行，更新状态
                parts = line.split('|')
                if len(parts) >= 6:
                    # 保持其他字段不变，只更新状态和备注
                    parts[4] = f' {new_status} '  # 状态列
                    parts[5] = f' {description} '  # 备注列
                    lines[i] = '|'.join(parts)
                    updated = True
                    break

        if updated:
            new_content = '\n'.join(lines)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"   ✅ migration_implementation_log.md 已更新")
        else:
            print(f"   ⚠️ 在migration_implementation_log.md中未找到Agent: {agent_name}")

    def _add_update_log_entry(self, agent_name: str, new_status: str, description: str):
        """添加更新日志条目"""

        today = datetime.now().strftime('%Y-%m-%d')
        log_entry = f"- ✅ {agent_name}: {description}"

        # 更新SYSTEM_AGENTS_OVERVIEW.md的更新日志
        self._add_to_update_log(self.overview_file, today, log_entry)

        # 更新docs/migration_implementation_log.md的更新日志（如果有的话）
        self._add_to_update_log(self.log_file, today, log_entry)

    def _add_to_update_log(self, file_path: Path, date: str, entry: str):
        """添加条目到文档的更新日志部分"""

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找更新日志部分
        log_pattern = r'## 📝 更新日志'
        log_match = re.search(log_pattern, content)

        if log_match:
            # 查找今天的日期条目
            today_pattern = f'### {date}'
            today_match = re.search(today_pattern, content)

            if today_match:
                # 今天已经有条目，在该日期下添加新条目
                insert_pos = today_match.end()
                # 找到下一日期或下一章节的位置
                next_section = re.search(r'\n### \d{4}-\d{2}-\d{2}', content[insert_pos:])
                if next_section:
                    insert_pos += next_section.start()
                else:
                    # 找到下一章节
                    next_chapter = re.search(r'\n## ', content[insert_pos:])
                    if next_chapter:
                        insert_pos += next_chapter.start()

                content = content[:insert_pos] + f'\n{entry}' + content[insert_pos:]
            else:
                # 今天没有条目，创建新的日期条目
                insert_pos = log_match.end()
                new_entry = f'\n### {date} - Agent迁移状态更新\n{entry}'
                content = content[:insert_pos] + new_entry + content[insert_pos:]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def verify_consistency(self, agent_name: str):
        """验证两个文档的状态一致性"""

        print(f"🔍 验证文档一致性: {agent_name}")

        # 从两个文档中读取状态
        overview_status = self._get_agent_status_from_file(self.overview_file, agent_name)
        log_status = self._get_agent_status_from_file(self.log_file, agent_name)

        if overview_status and log_status:
            if overview_status == log_status:
                print("   ✅ 文档状态一致")
                return True
            else:
                print(f"   ❌ 文档状态不一致:")
                print(f"      SYSTEM_AGENTS_OVERVIEW.md: {overview_status}")
                print(f"      migration_implementation_log.md: {log_status}")
                return False
        else:
            print("   ⚠️ 无法读取状态信息")
            return False

    def _get_agent_status_from_file(self, file_path: Path, agent_name: str):
        """从文件中获取Agent状态"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # SYSTEM_AGENTS_OVERVIEW.md的模式
            if 'SYSTEM_AGENTS_OVERVIEW.md' in str(file_path):
                pattern = rf'\| \*\*{re.escape(agent_name)}\*\* \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|'
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    return match.group(2).strip()  # 状态列

            # docs/migration_implementation_log.md的模式
            else:
                lines = content.split('\n')
                for line in lines:
                    if f'{agent_name} |' in line and ('|' in line):
                        parts = line.split('|')
                        if len(parts) >= 5:
                            return parts[4].strip()  # 状态列

        except Exception as e:
            print(f"   读取文件失败 {file_path}: {e}")

        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="同步Agent迁移状态到文档")
    parser.add_argument('--agent', required=True, help='Agent名称')
    parser.add_argument('--status', required=True, help='新状态 (如: ✅ 完全迁移, 🟢 逐步替换已启用)')
    parser.add_argument('--description', required=True, help='状态描述')

    args = parser.parse_args()

    syncer = MigrationStatusSyncer()
    syncer.update_agent_status(args.agent, args.status, args.description)

    # 验证一致性
    if syncer.verify_consistency(args.agent):
        print("🎉 状态同步成功！")
    else:
        print("⚠️ 状态同步完成，但存在一致性问题，请手动检查。")

if __name__ == "__main__":
    main()
