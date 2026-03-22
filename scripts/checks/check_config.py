#!/usr/bin/env python3
"""检查配置是否生效"""

import os
from pathlib import Path
import sys

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

print("🔧 检查优化配置是否生效")
print("=" * 50)

# 检查环境变量
dedup_window = os.getenv('DEDUPLICATION_WINDOW')
max_tokens_env = os.getenv('MAX_TOKENS')
strict_validation = os.getenv('STRICT_ANSWER_VALIDATION')

print(f"1. DEDUPLICATION_WINDOW: {dedup_window} (预期: 60)")
print(f"2. MAX_TOKENS: {max_tokens_env} (预期: 8192)")
print(f"3. STRICT_ANSWER_VALIDATION: {strict_validation}")

# 检查代码修改
print(f"\n📝 检查代码修改:")
llm_integration_path = project_root / "src" / "core" / "llm_integration.py"
if llm_integration_path.exists():
    with open(llm_integration_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 检查推理模型基础tokens
        if 'base_tokens = 8192 if "reasoner"' in content:
            print("✅ llm_integration.py: 推理模型基础tokens已修改为8192")
        else:
            print("❌ llm_integration.py: 推理模型基础tokens未修改")
            
        # 检查去重窗口注释
        if 'DEDUPLICATION_WINDOW' in content:
            print("✅ llm_integration.py: 包含DEDUPLICATION_WINDOW配置")
        else:
            print("⚠️ llm_integration.py: 未找到DEDUPLICATION_WINDOW引用")
else:
    print("❌ llm_integration.py文件不存在")

# 检查.env文件修改
print(f"\n📁 检查.env文件修改:")
env_path = project_root / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
        if 'DEDUPLICATION_WINDOW=60' in env_content:
            print("✅ .env: DEDUPLICATION_WINDOW=60 已设置")
        else:
            print("❌ .env: DEDUPLICATION_WINDOW未设置为60")
            
        if 'MAX_TOKENS=8192' in env_content:
            print("✅ .env: MAX_TOKENS=8192 已设置")
        else:
            print("❌ .env: MAX_TOKENS未设置为8192")
            
        if '🚀 优化' in env_content:
            print("✅ .env: 包含优化注释")
else:
    print("❌ .env文件不存在")

print(f"\n🎯 优化总结:")
if dedup_window == '60' and '8192' in content:
    print("✅ 两项优化均已成功实施:")
    print("   - 推理任务max_tokens提高到8192")
    print("   - 请求去重窗口缩短到60秒")
else:
    print("⚠️ 部分优化可能未完全生效")

print(f"\n📊 下一步建议:")
print("1. 运行STRICT_ANSWER_VALIDATION=true python test_chief_agent_migration.py")
print("2. 比较优化前后的性能指标")
print("3. 检查API调用是否受益于更大的max_tokens")