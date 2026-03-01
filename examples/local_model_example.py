"""
本地模型使用示例
演示如何在开发环境中使用 DistilBERT 等本地模型
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"✅ 已加载环境变量: {env_path}")
except ImportError:
    print("⚠️ python-dotenv 未安装，无法加载 .env 文件")

# 设置使用本地模型（不设置 GOOGLE_API_KEY）
os.environ.pop('GOOGLE_API_KEY', None)  # 确保不使用 Google API
os.environ['USE_LOCAL_MODEL'] = 'true'

from src.services.local_model_extract_service import HybridExtractService, LocalModelExtractService


async def example_1_basic_usage():
    """示例1：基本使用"""
    print("\n" + "="*60)
    print("示例1：基本使用（命名实体识别）")
    print("="*60)
    
    try:
        # 初始化本地模型服务
        service = LocalModelExtractService(
            model_name="distilbert-base-uncased",
            task="ner"  # 命名实体识别
        )
        
        # 准备证据
        evidence = [
            {
                "content": "Barack Obama was the 44th President of the United States. He was born in Hawaii.",
                "source": "wikipedia"
            },
            {
                "content": "The White House is located in Washington, D.C.",
                "source": "geography_book"
            }
        ]
        
        # 提取结构化信息
        print("\n📝 正在提取实体...")
        result = await service.extract_from_evidence(
            evidence=evidence,
            schema={"type": "object", "properties": {}},
            query="Who was the 44th President?"
        )
        
        print(f"\n✅ 提取完成！")
        print(f"   找到 {len(result['entities'])} 个实体：")
        for entity in result["entities"]:
            print(f"   - {entity['text']} ({entity['type']}) - 置信度: {entity.get('confidence', 0.0):.2f}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


async def example_2_hybrid_mode():
    """示例2：混合模式（自动选择）"""
    print("\n" + "="*60)
    print("示例2：混合模式（自动选择本地模型或 LangExtract）")
    print("="*60)
    
    try:
        # 自动选择：如果没有 GOOGLE_API_KEY，使用本地模型
        service = HybridExtractService()
        
        evidence = [
            {
                "content": "The capital of France is Paris. Paris is also known as the City of Light.",
                "source": "geography_book"
            }
        ]
        
        print("\n📝 正在提取答案...")
        result = await service.extract_answer_with_source(
            query="What is the capital of France?",
            evidence=evidence
        )
        
        print(f"\n✅ 提取完成！")
        print(f"   答案: {result['answer']}")
        print(f"   置信度: {result['confidence']:.2f}")
        print(f"   来源: {result['sources']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


async def example_3_entity_extraction():
    """示例3：实体提取（带位置信息）"""
    print("\n" + "="*60)
    print("示例3：实体提取（带位置信息）")
    print("="*60)
    
    try:
        service = LocalModelExtractService(
            model_name="distilbert-base-uncased",
            task="ner"
        )
        
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California in 1976."
        
        print(f"\n📝 文本: {text}")
        print("\n📝 正在提取实体...")
        entities = await service.extract_entities_with_locations(text)
        
        print(f"\n✅ 提取完成！找到 {len(entities)} 个实体：")
        for entity in entities:
            print(f"   - '{entity['text']}' ({entity['type']})")
            print(f"     位置: [{entity['start']}:{entity['end']}]")
            print(f"     置信度: {entity.get('confidence', 0.0):.2f}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("="*60)
    print("本地模型使用示例")
    print("="*60)
    print("\n这个示例演示如何在开发环境中使用本地模型（DistilBERT）")
    print("进行信息提取，无需 Google API Key。")
    print("\n注意：首次运行会下载模型，可能需要一些时间。")
    
    # 检查依赖
    try:
        import transformers
        import torch
        print(f"\n✅ 依赖检查通过:")
        print(f"   - transformers: {transformers.__version__}")
        print(f"   - torch: {torch.__version__}")
    except ImportError as e:
        print(f"\n❌ 缺少依赖: {e}")
        print("   请安装: pip install transformers torch")
        return
    
    # 运行示例
    await example_1_basic_usage()
    await example_2_hybrid_mode()
    await example_3_entity_extraction()
    
    print("\n" + "="*60)
    print("✅ 所有示例运行完成！")
    print("="*60)
    print("\n💡 提示:")
    print("   - 开发环境：使用本地模型（零成本、快速）")
    print("   - 生产环境：使用 LangExtract + Google Gemini（高准确度）")
    print("   - 查看文档: docs/usage/local_model_development_guide.md")


if __name__ == "__main__":
    asyncio.run(main())

