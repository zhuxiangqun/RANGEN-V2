"""
引用智能体演示
演示引用智能体的各种功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agents.enhanced_citation_agent import CitationAgent

async def demo_citation_generation():
    """演示引用生成功能"""
    print("=== 引用生成演示 ===")
    citation_agent = CitationAgent()
    # 示例来源数据
    sources = [
        {
            "url": "https://openai.com/research/ai-safety",
            "title": "AI Safety Research at OpenAI",
            "snippet": "Research on artificial intelligence safety measures and alignment",
            "author": "OpenAI Research Team",
            "publication_date": "2024"
        },
        {
            "url": "https://arxiv.org/abs/2024.12345",
            "title": "Deep Learning for Natural Language Processing",
            "snippet": "A comprehensive study on neural network architectures for NLP",
            "author": "Smith, J. and Johnson, A.",
            "publication_date": "2024"
        }
    ]
    
    # 生成不同格式的引用
    formats = ["apa", "mla", "chicago"]
    for fmt in formats:
        print(f"\n--- {fmt.upper()} 格式引用 ---")
        task = {
            "type": "citation_generation",
            "sources": sources,
            "format": fmt
        }
        try:
            result = await citation_agent.execute(task)
            if result.success:
                print(f"生成了 {len(result.data.get('citations', []))} 个引用")
                for i, citation in enumerate(result.data.get('citations', [])[:2]):
                    print(f"\n引用 {i+1}:")
                    print(f"  标题: {citation.get('source_title', 'N/A')}")
                    print(f"  引用文本: {citation.get('citation_text', 'N/A')}")
            else:
                print(f"生成失败: {result.error_message}")
        except Exception as e:
            print(f"执行出错: {e}")

async def demo_source_validation():
    """演示来源验证功能"""
    print("\n=== 来源验证演示 ===")
    citation_agent = CitationAgent()
    # 混合来源数据
    sources = [
        {
            "url": "https://harvard.edu/research/ai-safety",
            "title": "Academic Research on AI Safety",
            "snippet": "This is a peer-reviewed research study on artificial intelligence safety"
        },
        {
            "url": "https://blog.example.com/my-thoughts-on-ai",
            "title": "My Personal Thoughts on AI",
            "snippet": "Personal opinions about artificial intelligence"
        }
    ]
    
    task = {
        "type": "source_validation",
        "sources": sources
    }
    try:
        result = await citation_agent.execute(task)
        if result.success:
            print(f"总来源数: {result.data.get('total_sources', 0)}")
            print(f"有效来源数: {result.data.get('valid_sources', 0)}")
        else:
            print(f"验证失败: {result.error_message}")
    except Exception as e:
        print(f"执行出错: {e}")

async def main():
    """主函数"""
    print("🔍 引用智能体功能演示")
    print("=" * 50)
    
    try:
        await demo_citation_generation()
        await demo_source_validation()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
    
    print("\n✅ 演示完成!")

if __name__ == "__main__":
    asyncio.run(main())
