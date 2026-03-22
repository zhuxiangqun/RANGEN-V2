#!/usr/bin/env python3
"""
Fix remaining import paths - agents in specialized subdirectory
"""
from pathlib import Path

files_to_fix = {
    "src/access/api/smart_handler_routes.py": [
        ("from src.agents.requirement_analyzer_agent import", "from src.agents.specialized.requirement_analyzer_agent import"),
        ("from src.agents.ops_diagnosis_agent import", "from src.agents.specialized.ops_diagnosis_agent import"),
    ],
    "src/access/api/conversation_routes.py": [
        ("from src.agents.smart_conversation_agent import", "from src.agents.smart_conversation_agent import"),
    ],
    "src/access/api/ops_diagnosis_routes.py": [
        ("from src.agents.ops_diagnosis_agent import", "from src.agents.specialized.ops_diagnosis_agent import"),
    ],
}

def fix_file(filepath: str, replacements: list):
    """Apply replacements to a file"""
    full_path = Path(filepath)
    if not full_path.exists():
        print(f"⚠️  File not found: {filepath}")
        return False
    
    content = full_path.read_text(encoding='utf-8')
    original = content
    
    for old, new in replacements:
        if old != new:  # Skip if same
            content = content.replace(old, new)
    
    if content != original:
        full_path.write_text(content, encoding='utf-8')
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"⚠️  No changes: {filepath}")
        return False

def main():
    print("🔧 Fixing remaining import paths...")
    for filepath, replacements in files_to_fix.items():
        fix_file(filepath, replacements)
    
    # Verify
    print("\n🔍 Verifying imports...")
    import subprocess
    result = subprocess.run(
        ["python3", "-c", "from src.access.api.server import app; print('✅ API server import OK')"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"❌ Import still failing:")
        print(result.stderr[-800:] if len(result.stderr) > 800 else result.stderr)

if __name__ == "__main__":
    main()
