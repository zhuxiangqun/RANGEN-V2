#!/usr/bin/env python3
"""
测试 google/frames-benchmark 构建解决方案
验证 torch/datasets 库是否能正常工作
"""

import sys
import os
from pathlib import Path

def test_torch_import():
    """测试torch导入"""
    print("🔧 测试torch导入...")
    try:
        import torch
        print(f"✅ torch导入成功: 版本 {torch.__version__}")

        # 测试基本功能
        x = torch.tensor([1, 2, 3])
        print(f"✅ torch张量创建成功: {x}")
        return True
    except Exception as e:
        print(f"❌ torch导入失败: {e}")
        return False

def test_datasets_import():
    """测试datasets导入"""
    print("\n🔧 测试datasets导入...")
    try:
        import datasets
        print(f"✅ datasets导入成功: 版本 {datasets.__version__}")

        # 测试基本功能
        from datasets import load_dataset
        print("✅ load_dataset函数可用")
        return True
    except Exception as e:
        print(f"❌ datasets导入失败: {e}")
        return False

def test_sentence_transformers_import():
    """测试sentence_transformers导入"""
    print("\n🔧 测试sentence_transformers导入...")
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer导入成功")

        # 测试模型加载（轻量级）
        print("🔄 尝试加载轻量级模型...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"✅ 模型加载成功: 维度 {model.get_sentence_embedding_dimension()}")
        return True
    except Exception as e:
        print(f"❌ sentence_transformers导入失败: {e}")
        return False

def test_knowledge_base_files():
    """测试知识库文件"""
    print("\n🔧 检查知识库文件...")

    kb_dir = Path("data/knowledge_management")

    files_to_check = [
        "frames_dataset_complete.json",
        "frames_embeddings_complete.npy",
        "frames_texts_complete.json",
        "metadata_complete.json"
    ]

    all_exist = True
    for file in files_to_check:
        file_path = kb_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: 文件不存在")
            all_exist = False

    return all_exist

def test_keras_patch_impact():
    """测试keras补丁的影响"""
    print("\n🔧 测试keras补丁影响...")

    # 备份原始modules
    original_modules = dict(sys.modules)

    try:
        # 应用keras补丁
        print("🔄 应用keras兼容性补丁...")
        exec(open('keras_compat_patch.py').read())

        # 测试torch是否还能正常工作
        import torch
        x = torch.tensor([1.0])
        print("✅ keras补丁后torch仍正常工作")

        return True

    except Exception as e:
        print(f"❌ keras补丁导致问题: {e}")
        return False
    finally:
        # 恢复原始modules（简化版）
        pass

def main():
    print("🚀 google/frames-benchmark 构建解决方案测试")
    print("=" * 60)

    results = {}

    # 测试各个组件
    results['torch'] = test_torch_import()
    results['datasets'] = test_datasets_import()
    results['sentence_transformers'] = test_sentence_transformers_import()
    results['keras_patch'] = test_keras_patch_impact()
    results['kb_files'] = test_knowledge_base_files()

    # 总结结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！沙箱环境问题已彻底解决")
        print("\n📋 可以使用以下命令构建完整的向量知识库:")
        print("  python build_frames_kb_full.py --batch-size 10")
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        print("\n🔧 可能的解决方案:")
        print("  1. 确保使用无沙箱限制的环境")
        print("  2. 检查虚拟环境是否正确激活")
        print("  3. 验证所有依赖是否正确安装")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
