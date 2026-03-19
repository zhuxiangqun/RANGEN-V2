"""
RANGEN CLI - Command Line Interface

Usage:
    python -m src.cli skills list
    python -m src.cli skills search <query>
    python -m src.cli skills info <skill-name>
"""

import sys
import argparse
from typing import Optional

# Add project root to path
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.agents.skills.enhanced_registry import get_enhanced_skill_registry


def cmd_skills_list(args):
    """List all available skills"""
    registry = get_enhanced_skill_registry()
    skills = registry.list_skills()
    
    print(f"\n{'='*60}")
    print(f"Available Skills ({len(skills)})")
    print(f"{'='*60}\n")
    
    for s in skills:
        print(f"📦 {s.name}")
        print(f"   {s.description[:60]}...")
        if s.triggers:
            print(f"   🔑 triggers: {', '.join(s.triggers[:5])}")
        if s.tags:
            print(f"   🏷️  tags: {', '.join(s.tags[:3])}")
        print()


def cmd_skills_search(args):
    """Search skills by query"""
    registry = get_enhanced_skill_registry()
    results = registry.search_skills(args.query)
    
    print(f"\n{'='*60}")
    print(f"Search Results for '{args.query}' ({len(results)} found)")
    print(f"{'='*60}\n")
    
    for s in results:
        print(f"📦 {s.name}")
        print(f"   {s.description}")
        print()


def cmd_skills_info(args):
    """Show detailed info for a skill"""
    registry = get_enhanced_skill_registry()
    metadata = registry.get_metadata(args.skill_name)
    
    if not metadata:
        print(f"❌ Skill '{args.skill_name}' not found")
        return
    
    print(f"\n{'='*60}")
    print(f"Skill: {metadata.name}")
    print(f"{'='*60}\n")
    
    print(f"📝 Description: {metadata.description}")
    print(f"📌 Version: {metadata.version}")
    print(f"👤 Author: {metadata.author}")
    print(f"🏷️  Tags: {', '.join(metadata.tags)}")
    print(f"🔑 Triggers: {', '.join(metadata.triggers) if metadata.triggers else 'None'}")
    print()
    
    if metadata.tools:
        print("🔧 Available Tools:")
        for t in metadata.tools:
            print(f"   - {t.name}: {t.description}")
        print()
    
    # Show documentation
    docs = registry.get_skill_documentation(args.skill_name)
    if docs:
        print("📄 Documentation (first 1000 chars):")
        print("-" * 40)
        print(docs[:1000])
        if len(docs) > 1000:
            print(f"\n... (truncated, total {len(docs)} chars)")
    else:
        print("📄 Documentation: Not available")


def cmd_skills_trigger(args):
    """Find skills by trigger keyword"""
    registry = get_enhanced_skill_registry()
    results = registry.find_skills_by_trigger(args.keyword)
    
    print(f"\n{'='*60}")
    print(f"Skills triggered by '{args.keyword}' ({len(results)} found)")
    print(f"{'='*60}\n")
    
    for name in results:
        metadata = registry.get_metadata(name)
        print(f"📦 {name}")
        print(f"   {metadata.description if metadata else 'No description'}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="RANGEN CLI - Multi-Agent Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Skills commands
    skills_parser = subparsers.add_parser('skills', help='Skills management')
    skills_subparsers = skills_parser.add_subparsers(dest='subcommand')
    
    # skills list
    skills_subparsers.add_parser('list', help='List all skills')
    
    # skills search
    search_parser = skills_subparsers.add_parser('search', help='Search skills')
    search_parser.add_argument('query', type=str, help='Search query')
    
    # skills info
    info_parser = skills_subparsers.add_parser('info', help='Show skill details')
    info_parser.add_argument('skill_name', type=str, help='Skill name')
    
    # Lite commands
    lite_parser = subparsers.add_parser('lite', help='RANGEN Lite mode')
    lite_parser.add_argument('--interactive', action='store_true', help='Interactive configuration')
    lite_parser.add_argument('--port', type=str, default='8501', help='UI port')
    lite_parser.set_defaults(func=cmd_lite)
    
    # skills trigger
    trigger_parser = skills_subparsers.add_parser('trigger', help='Find skills by trigger')
    trigger_parser.add_argument('keyword', type=str, help='Trigger keyword')
    trigger_parser.set_defaults(func=cmd_skills_trigger)
    
    args = parser.parse_args()
    
    if args.command == 'skills':
        if args.subcommand == 'list':
            cmd_skills_list(args)
        elif args.subcommand == 'search':
            cmd_skills_search(args)
        elif args.subcommand == 'info':
            cmd_skills_info(args)
        elif args.subcommand == 'trigger':
            cmd_skills_trigger(args)
        else:
            skills_parser.print_help()
    elif args.command == 'lite':
        cmd_lite(args)
    else:
        parser.print_help()


def cmd_lite(args):
    """启动 RANGEN Lite 模式"""
    from src.core.lite_configurator import LiteConfigurator, quick_start, interactive_configure
    
    if args.interactive:
        interactive_configure()
    else:
        quick_start()


def cmd_lite_start(args):
    """直接启动 UI"""
    import subprocess
    print("🚀 启动 RANGEN Lite UI...")
    print("   访问 http://localhost:8501")
    subprocess.run(["streamlit", "run", "src/ui/app.py", "--server.port", args.port])


if __name__ == '__main__':
    main()
