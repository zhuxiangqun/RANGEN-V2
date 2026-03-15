#!/usr/bin/env python3
"""测试循环导入修复"""

import os
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

print("测试LLMIntegration导入...")

try:
    from src.core.llm_integration import LLMIntegration
    print("✅ LLMIntegration导入成功")
    
    # 测试创建实例
    config = {
        'model': 'deepseek-reasoner',
        'llm_provider': 'deepseek'
    }
    
    llm = LLMIntegration(config)
    print("✅ LLMIntegration实例创建成功")
    print(f"   模型: {llm.model}")
    print(f"   去重窗口: {llm._dedup_window}秒")
    
    # 测试max_tokens计算
    max_tokens = llm._get_max_tokens('deepseek-reasoner', 'complex')
    print(f"✅ max_tokens计算: {max_tokens}")
    
    print("\n🎉 所有测试通过！循环导入问题已修复。")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)