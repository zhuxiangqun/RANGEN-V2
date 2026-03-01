#!/usr/bin/env python3
"""
向量索引深度诊断脚本
用于检查FAISS索引状态、向量质量和维度一致性
"""

import sys
import os
import numpy as np
import faiss
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledge_management_system.utils.logger import get_logger
from knowledge_management_system.modalities.text_processor import get_text_processor

logger = get_logger()

def diagnose_vector_index(index_path: str = "data/knowledge_management/vector_index.bin"):
    print("=" * 70)
    print("🩺 向量索引深度诊断报告")
    print("=" * 70)
    
    # 1. 检查索引文件
    path_obj = Path(index_path)
    if not path_obj.exists():
        print(f"❌ 索引文件不存在: {index_path}")
        return
    
    file_size_mb = path_obj.stat().st_size / (1024 * 1024)
    print(f"📂 索引文件路径: {index_path}")
    print(f"📦 文件大小: {file_size_mb:.2f} MB")
    
    # 2. 加载FAISS索引
    try:
        index = faiss.read_index(str(index_path))
        print(f"✅ FAISS索引加载成功")
        print(f"📊 索引类型: {type(index).__name__}")
        print(f"🔢 向量维度 (d): {index.d}")
        print(f"📈 向量总数 (ntotal): {index.ntotal}")
        print(f"📏 是否已训练 (is_trained): {index.is_trained}")
        print(f"📐 距离度量 (metric_type): {index.metric_type} (0=INNER_PRODUCT, 1=L2)")
    except Exception as e:
        print(f"❌ FAISS索引加载失败: {e}")
        return

    # 3. 检查TextProcessor配置
    print("\n🔄 检查文本处理器配置...")
    try:
        processor = get_text_processor()
        test_text = "test query for dimension check"
        vector = processor.encode(test_text)
        
        if vector is None:
            print("❌ TextProcessor编码失败，返回None")
        else:
            model_dim = vector.shape[0]
            print(f"🧠 模型输出维度: {model_dim}")
            
            # 验证维度一致性
            if model_dim != index.d:
                print(f"❌ 严重错误: 模型维度 ({model_dim}) 与索引维度 ({index.d}) 不匹配!")
            else:
                print(f"✅ 维度一致性检查通过")
            
            # 检查模型输出向量是否归一化
            norm = np.linalg.norm(vector)
            print(f"📏 模型输出向量模长: {norm:.6f}")
            if abs(norm - 1.0) > 1e-4:
                print("⚠️ 警告: 模型输出向量未归一化 (IndexFlatIP需要归一化向量)")
            else:
                print("✅ 模型输出已归一化")

    except Exception as e:
        print(f"❌ TextProcessor检查失败: {e}")

    # 4. 索引向量抽样检查
    print("\n🔍 索引向量抽样检查 (前5个)...")
    if index.ntotal > 0:
        try:
            # 尝试重建向量（并非所有索引类型都支持reconstruct）
            for i in range(min(5, index.ntotal)):
                try:
                    vec = index.reconstruct(i)
                    vec_norm = np.linalg.norm(vec)
                    is_zero = np.allclose(vec, 0)
                    print(f"   Vector[{i}]: Norm={vec_norm:.6f}, IsZero={is_zero}, First5={vec[:5]}")
                    
                    if is_zero:
                        print(f"   ❌ 发现全零向量! Index: {i}")
                    if abs(vec_norm - 1.0) > 1e-4 and index.metric_type == faiss.METRIC_INNER_PRODUCT:
                         print(f"   ⚠️ 向量未归一化 (内积索引推荐归一化)")
                except Exception as e:
                    print(f"   ⚠️ 无法重建向量[{i}]: {e}")
                    break
        except Exception as e:
             print(f"❌ 抽样检查失败: {e}")
    else:
        print("⚠️ 索引为空，跳过抽样检查")

    print("\n" + "=" * 70)
    print("🏁 诊断完成")
    print("=" * 70)

if __name__ == "__main__":
    diagnose_vector_index()
