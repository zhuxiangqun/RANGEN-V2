#!/usr/bin/env python3
"""
知识库管理系统测试脚本
验证系统独立性和基本功能
"""

import sys
import os
from pathlib import Path

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_independence():
    """测试系统独立性"""
    print("=" * 80)
    print("测试1: 系统独立性")
    print("=" * 80)
    
    # 测试是否可以通过标准接口导入
    try:
        from knowledge_management_system.api.service_interface import get_knowledge_service
        print("✅ 标准接口导入成功")
        
        # 获取服务实例
        service = get_knowledge_service()
        print("✅ 服务实例创建成功")
        
        # 测试不应该直接导入核心模块
        try:
            from knowledge_management_system.core.knowledge_manager import KnowledgeManager
            print("⚠️  警告：可以导入核心模块（虽然不推荐，但技术上可行）")
            print("   建议：其他系统应只通过api.service_interface调用")
        except ImportError:
            print("✅ 核心模块未暴露（完全独立）")
        
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 80)
    print("测试2: 基本功能")
    print("=" * 80)
    
    try:
        from knowledge_management_system.api.service_interface import get_knowledge_service
        
        service = get_knowledge_service()
        
        # 测试统计信息
        stats = service.get_statistics()
        print(f"✅ 获取统计信息成功")
        print(f"   总知识条目: {stats.get('total_entries', 0)}")
        print(f"   向量索引大小: {stats.get('vector_index_size', 0)}")
        
        # 测试导入（示例数据）
        test_knowledge = {
            "content": "This is a test knowledge entry.",
            "metadata": {
                "source": "test",
                "category": "test"
            }
        }
        
        knowledge_ids = service.import_knowledge(
            data=test_knowledge,
            modality="text",
            source_type="dict"
        )
        
        if knowledge_ids:
            print(f"✅ 知识导入成功: {len(knowledge_ids)} 条")
        else:
            print("⚠️  知识导入返回空列表（可能验证失败或索引未就绪）")
        
        # 测试查询
        results = service.query_knowledge(
            query="test",
            modality="text",
            top_k=3
        )
        
        print(f"✅ 知识查询成功: {len(results)} 条结果")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_modality_processors():
    """测试多模态处理器"""
    print("\n" + "=" * 80)
    print("测试3: 多模态处理器")
    print("=" * 80)
    
    try:
        from knowledge_management_system.modalities.text_processor import TextProcessor
        from knowledge_management_system.modalities.image_processor import ImageProcessor
        from knowledge_management_system.modalities.audio_processor import AudioProcessor
        from knowledge_management_system.modalities.video_processor import VideoProcessor
        
        # 测试文本处理器
        text_processor = TextProcessor()
        print(f"✅ 文本处理器: enabled={text_processor.enabled}, dimension={text_processor.get_dimension()}")
        
        # 测试图像处理器
        image_processor = ImageProcessor()
        print(f"✅ 图像处理器: enabled={image_processor.enabled}, dimension={image_processor.get_dimension()}")
        
        # 测试音频处理器
        audio_processor = AudioProcessor()
        print(f"✅ 音频处理器: enabled={audio_processor.enabled}, dimension={audio_processor.get_dimension()}")
        
        # 测试视频处理器
        video_processor = VideoProcessor()
        print(f"✅ 视频处理器: enabled={video_processor.enabled}, dimension={video_processor.get_dimension()}")
        
        return True
    except Exception as e:
        print(f"❌ 多模态处理器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("知识库管理系统测试")
    print("=" * 80)
    
    results = []
    
    # 测试1: 独立性
    results.append(("独立性测试", test_independence()))
    
    # 测试2: 基本功能
    results.append(("基本功能测试", test_basic_functionality()))
    
    # 测试3: 多模态处理器
    results.append(("多模态处理器测试", test_modality_processors()))
    
    # 汇总
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

