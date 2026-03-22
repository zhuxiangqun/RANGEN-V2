#!/usr/bin/env python3
"""
Fix import paths in src/access/api/ directory
All files in this directory should use relative imports for local modules
"""
import os
import re
from pathlib import Path

# Files in src/access/api/ that need import fixes
# These files reference modules that exist in the same directory but use src.api.xxx path

files_to_fix = [
    # From src.api.models_agent -> .models_agent
    ("src/access/api/agents.py", [
        ("from src.api.models_agent", "from .models_agent"),
    ]),
    # From src.api.auth_service -> .auth_service
    ("src/access/api/auth.py", [
        ("from src.api.auth_service", "from .auth_service"),
    ]),
    # From src.api.models_skill -> .models_skill
    ("src/access/api/skills.py", [
        ("from src.api.models_skill", "from .models_skill"),
    ]),
    # From src.api.auth -> .auth
    ("src/access/api/smart_handler_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    ("src/access/api/skill_factory_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    ("src/access/api/routing_monitor_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    ("src/access/api/ops_diagnosis_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    ("src/access/api/conversation_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    ("src/access/api/mcp_routes.py", [
        ("from src.api.auth import", "from .auth import"),
    ]),
    # server.py - multiple imports to fix
    ("src/access/api/server.py", [
        ("from src.api.design_routes import", "from .design_routes import"),
        ("from src.api.auth import", "from .auth import"),
        ("from src.api.team_routes import", "from .team_routes import"),
        ("from src.api.routes.platform import", "from .routes.platform import"),
        ("from src.api.unified_create_routes import", "from .unified_create_routes import"),
    ]),
    # server_di.py
    ("src/access/api/server_di.py", [
        ("from src.api.models import", "from .models import"),
        ("from src.api.auth import", "from .auth import"),
    ]),
    # auth_service.py
    ("src/access/api/auth_service.py", [
        ("from src.api.models_auth import", "from .models_auth import"),
        ("from src.api.auth import", "from .auth import"),
    ]),
]

def fix_file(filepath: str, replacements: list):
    """Apply replacements to a file"""
    full_path = Path(filepath)
    if not full_path.exists():
        print(f"⚠️  File not found: {filepath}")
        return False
    
    content = full_path.read_text(encoding='utf-8')
    original = content
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original:
        full_path.write_text(content, encoding='utf-8')
        print(f"✅ Fixed: {filepath}")
        return True
    else:
        print(f"⚠️  No changes: {filepath}")
        return False

def main():
    print("🔧 Fixing import paths in src/access/api/...")
    print("=" * 60)
    
    fixed_count = 0
    for filepath, replacements in files_to_fix:
        if fix_file(filepath, replacements):
            fixed_count += 1
    
    print("=" * 60)
    print(f"✅ Fixed {fixed_count} files")
    
    # Verify server.py can be imported
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
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)

if __name__ == "__main__":
    main()
