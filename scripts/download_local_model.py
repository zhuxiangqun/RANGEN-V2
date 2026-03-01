#!/usr/bin/env python3
"""
下载本地Embedding模型脚本
支持使用镜像源和重试机制
"""

import os
import sys
from pathlib import Path

def download_model_with_mirror(model_name: str = "all-mpnet-base-v2", use_mirror: bool = True):
    """下载模型，支持使用镜像源"""
    
    # 设置镜像源（如果需要）
    if use_mirror:
        # 尝试多个镜像源
        mirrors = [
            'https://hf-mirror.com',
            'https://huggingface.co',  # 官方源
        ]
        
        for mirror in mirrors:
            try:
                os.environ['HF_ENDPOINT'] = mirror
                print(f"🔄 尝试使用镜像源: {mirror}")
                break
            except:
                continue
    
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔄 开始下载模型: {model_name}...")
        print("   这可能需要几分钟时间，请耐心等待...")
        print()
        
        # 下载模型
        model = SentenceTransformer(model_name)
        
        print()
        print("=" * 70)
        print("✅ 模型下载成功！")
        print("=" * 70)
        print(f"模型名称: {model_name}")
        print(f"向量维度: {model.get_sentence_embedding_dimension()}")
        
        # 测试模型
        test_text = "Hello world"
        embedding = model.encode(test_text)
        print(f"测试向量化: 成功 (维度: {embedding.shape[0]})")
        
        print()
        print("💡 提示: 模型已缓存到本地，后续使用无需重新下载")
        print(f"缓存位置: ~/.cache/huggingface/hub/")
        
        return True
        
    except ImportError:
        print("❌ sentence-transformers 未安装")
        print("💡 请先安装: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print()
        print("可能的原因:")
        print("  1. 网络连接问题")
        print("  2. HuggingFace服务器访问受限")
        print("  3. SSL证书问题")
        print()
        print("💡 建议:")
        print("  1. 检查网络连接")
        print("  2. 尝试使用VPN或代理")
        print("  3. 稍后重试")
        print("  4. 手动下载模型文件（见文档）")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="下载本地Embedding模型")
    parser.add_argument(
        "--model",
        type=str,
        default="all-mpnet-base-v2",
        help="模型名称（默认: all-mpnet-base-v2）"
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="不使用镜像源（使用官方源）"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("📥 本地Embedding模型下载工具")
    print("=" * 70)
    print()
    
    success = download_model_with_mirror(
        model_name=args.model,
        use_mirror=not args.no_mirror
    )
    
    if success:
        print()
        print("=" * 70)
        print("✅ 下载完成！")
        print("=" * 70)
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("❌ 下载失败")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()

