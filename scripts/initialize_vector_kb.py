#!/usr/bin/env python3
"""
初始化向量知识库 - 添加初始知识
"""

import sys
from pathlib import Path

# 确保能够导入 src 下的模块
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.knowledge.vector_database import get_vector_knowledge_base

def initialize_base_knowledge():
    """初始化向量知识库 - 知识将从实际运行中自动积累"""
    kb = get_vector_knowledge_base()
    
    # 向量知识库会自动从知识检索Agent的结果中积累
    # 不需要添加固定的示例知识
    
    kb.save()
    print(f"✅ 向量知识库初始化完成（知识将从运行中自动积累）")

if __name__ == "__main__":
    try:
        initialize_base_knowledge()
        print("初始化成功！")
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

