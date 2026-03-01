#!/usr/bin/env python3
"""
重建知识库 - 从wiki_cache加载正确的wikilink Wikipedia内容
替换错误的FRAMES问题数据

用法：
  python scripts/rebuild_knowledge_base.py
"""

import sys
import asyncio
import json
from pathlib import Path
import shutil
from datetime import datetime

# 确保能够导入 src 下的模块
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.memory.enhanced_faiss_memory import EnhancedFAISSMemory
from src.knowledge.vector_database import get_vector_knowledge_base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def rebuild_faiss_memory():
    """重建FAISS Memory知识库"""
    print("\n🔧 开始重建FAISS Memory知识库...")
    
    # 1. 备份旧数据
    faiss_dir = Path("data/faiss_memory")
    if faiss_dir.exists():
        backup_dir = faiss_dir.parent / f"faiss_memory_backup_{int(datetime.now().timestamp())}"
        print(f"📦 备份旧数据到: {backup_dir}")
        shutil.copytree(faiss_dir, backup_dir)
        print("✅ 备份完成")
    
    # 2. 删除旧数据
    knowledge_file = faiss_dir / "knowledge_entries.json"
    index_file = faiss_dir / "faiss_index.bin"
    metadata_file = faiss_dir / "index_metadata.json"
    
    files_to_remove = [knowledge_file, index_file, metadata_file]
    for file in files_to_remove:
        if file.exists():
            file.unlink()
            print(f"🗑️  已删除: {file.name}")
    
    # 3. 创建新的FAISS Memory实例并触发重建
    print("\n🔄 创建新的FAISS Memory实例并触发重建...")
    faiss_memory = EnhancedFAISSMemory()
    
    # 强制标记需要重建
    faiss_memory._index_needs_rebuild = True
    
    # 等待重建完成
    print("⏳ 等待知识库重建（从wiki_cache加载wikilink内容）...")
    await faiss_memory._rebuild_index_smart()
    
    # 验证重建结果
    await faiss_memory._load_knowledge_entries_async()
    print(f"\n✅ FAISS Memory重建完成，包含 {len(faiss_memory.knowledge_entries)} 条知识条目")
    
    # 验证内容质量
    if faiss_memory.knowledge_entries:
        print("\n📊 验证重建后的知识内容质量:")
        valid_count = 0
        question_count = 0
        
        for entry in faiss_memory.knowledge_entries[:50]:  # 检查前50条
            content = entry.get('content', '') or entry.get('text', '')
            if content:
                if faiss_memory._is_content_likely_question(content):
                    question_count += 1
                else:
                    valid_count += 1
        
        print(f"  有效知识: {valid_count}条")
        print(f"  问题内容: {question_count}条")
        print(f"  质量比例: {valid_count/(valid_count+question_count)*100:.1f}% 是有效知识" if (valid_count+question_count) > 0 else "无法判断")
        
        # 显示前3条有效知识示例
        print("\n📝 前3条有效知识示例:")
        count = 0
        for entry in faiss_memory.knowledge_entries:
            if count >= 3:
                break
            content = entry.get('content', '') or entry.get('text', '')
            if content and not faiss_memory._is_content_likely_question(content):
                print(f"  {count+1}. {content[:150]}...")
                print(f"     来源: {entry.get('source', 'unknown')}")
                count += 1
    
    return faiss_memory


async def rebuild_vector_kb():
    """重建向量知识库（VectorKnowledgeBase）"""
    print("\n🔧 开始重建向量知识库...")
    
    # 1. 检查wiki_cache
    wiki_cache_dir = Path("data/wiki_cache")
    if not wiki_cache_dir.exists():
        print("⚠️ wiki_cache目录不存在，无法重建向量知识库")
        return None
    
    cache_files = list(wiki_cache_dir.glob("*.json"))
    if not cache_files:
        print("⚠️ wiki_cache中没有文件，无法重建向量知识库")
        return None
    
    print(f"📚 发现 {len(cache_files)} 个wikilink Wikipedia页面文件")
    
    # 2. 获取向量知识库实例
    vector_kb = get_vector_knowledge_base()
    
    # 3. 清空现有内容
    print("🗑️  清空现有向量知识库...")
    vector_kb.clear()
    
    # 4. 从wiki_cache加载内容
    print("📥 从wiki_cache加载wikilink内容...")
    added_count = 0
    skipped_count = 0
    
    for i, cache_file in enumerate(cache_files):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            title = data.get('title', '')
            content = data.get('content', '') or data.get('extract', '')
            
            if content and len(content) > 50:
                # 验证不是问题
                if '?' in content[:100] and any(word in content.lower()[:50] 
                                               for word in ['how many', 'what', 'who', 'when', 'if ', 'imagine']):
                    skipped_count += 1
                    continue
                
                # 添加到向量知识库
                vector_kb.add_knowledge(
                    content[:2000],  # 限制长度
                    metadata={
                        'title': title,
                        'source': 'frames_wikilink',
                        'wikilink_url': data.get('url', ''),
                        'file': cache_file.name
                    }
                )
                added_count += 1
                
                if (added_count + skipped_count) % 100 == 0:
                    print(f"  已处理 {added_count + skipped_count}/{len(cache_files)} 个文件，已添加 {added_count} 条知识")
        
        except Exception as e:
            logger.debug(f"处理文件 {cache_file.name} 失败: {e}")
            skipped_count += 1
            continue
    
    # 5. 保存向量知识库
    print("💾 保存向量知识库...")
    vector_kb.save()
    
    print(f"\n✅ 向量知识库重建完成:")
    print(f"  总文件数: {len(cache_files)}")
    print(f"  成功添加: {added_count}条知识")
    print(f"  跳过: {skipped_count}条（问题或无效内容）")
    print(f"  最终大小: {vector_kb.size()}条")
    
    return vector_kb


async def main():
    """主函数"""
    print("=" * 60)
    print("🔧 知识库重建工具")
    print("=" * 60)
    print("\n此工具将：")
    print("1. 备份旧的FAISS Memory数据")
    print("2. 删除错误的问题数据")
    print("3. 从wiki_cache重建FAISS Memory（使用正确的Wikipedia内容）")
    print("4. 重建向量知识库（VectorKnowledgeBase）")
    print()
    
    try:
        # 重建FAISS Memory
        faiss_memory = await rebuild_faiss_memory()
        
        # 重建向量知识库
        vector_kb = await rebuild_vector_kb()
        
        print("\n" + "=" * 60)
        print("✅ 知识库重建完成！")
        print("=" * 60)
        print("\n💡 提示：下次运行核心系统时，将使用正确的wikilink Wikipedia内容")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 重建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

