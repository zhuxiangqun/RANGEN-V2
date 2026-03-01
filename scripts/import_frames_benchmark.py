#!/usr/bin/env python3
"""
FRAMES-Benchmark 数据集导入脚本
用于将 FRAMES-Benchmark 数据集集成到 KMS 向量知识库
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knowledge_management_system.integrations.frames_benchmark_loader import FramesBenchmarkLoader
from knowledge_management_system.utils.logger import get_logger

logger = get_logger()


def main():
    """主函数"""
    logger.info("开始 FRAMES-Benchmark 数据集集成流程...")
    
    # 创建加载器
    loader = FramesBenchmarkLoader()
    
    # 加载并导入数据集
    success = loader.load_and_import(split="test", use_cache=True)
    
    if success:
        logger.info("✅ FRAMES-Benchmark 数据集集成成功")
        
        # 验证 "Jane Ballou" 数据
        logger.info("验证 'Jane Ballou' 相关数据...")
        jane_found = loader.verify_jane_ballou_integration()
        
        if jane_found:
            logger.info("✅ 'Jane Ballou' 数据验证成功 - 系统现在可以正确回答相关查询")
            print("\n🎉 集成完成！")
            print("系统现在可以正确检索关于 'Jane Ballou' 的信息")
            print("可以测试查询：'Jane Ballou' 或相关政治历史问题")
        else:
            logger.warning("⚠️ 'Jane Ballou' 数据验证失败 - 可能需要检查数据加载")
            print("\n⚠️ 集成部分完成，但 Jane Ballou 数据验证失败")
    else:
        logger.error("❌ FRAMES-Benchmark 数据集集成失败")
        print("\n❌ 数据集集成失败，请检查日志获取详细信息")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())