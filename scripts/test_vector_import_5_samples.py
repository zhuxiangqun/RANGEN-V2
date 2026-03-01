#!/usr/bin/env python3
"""
测试脚本：使用5条数据验证向量知识库导入修复
验证：
1. 元数据文件原子性写入是否生效
2. 进度文件是否正确更新
3. 导入过程是否正常
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knowledge_management_system.scripts.build_vector_knowledge_base import (
    build_vector_knowledge_base_from_list,
    build_vector_knowledge_base_from_frames
)

def main():
    print("=" * 70)
    print("🧪 向量知识库导入修复验证测试")
    print("=" * 70)
    
    # 1. 加载测试数据
    test_data_path = Path("data/test_5_samples.json")
    if not test_data_path.exists():
        # 如果测试数据不存在，从完整数据集提取5条
        dataset_path = Path("data/frames_dataset.json")
        if not dataset_path.exists():
            print(f"❌ 数据集文件不存在: {dataset_path}")
            return False
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        test_data = dataset[:5]
        with open(test_data_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已从完整数据集提取5条测试数据")
    else:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        print(f"✅ 已加载测试数据: {len(test_data)} 条")
    
    # 2. 检查元数据文件初始状态
    metadata_path = Path("data/knowledge_management/metadata.json")
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            initial_entry_count = len(metadata.get('entries', {}))
            print(f"✅ 元数据文件初始状态: {initial_entry_count} 条条目")
        except json.JSONDecodeError as e:
            print(f"❌ 元数据文件损坏: {e}")
            return False
    else:
        print("⚠️ 元数据文件不存在，将创建新文件")
        initial_entry_count = 0
    
    # 3. 检查进度文件初始状态
    progress_path = Path("data/knowledge_management/vector_import_progress.json")
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            initial_processed = len(progress.get('processed_item_indices', []))
            print(f"✅ 进度文件初始状态: {initial_processed} 条已处理")
        except json.JSONDecodeError as e:
            print(f"⚠️ 进度文件损坏，将重新创建: {e}")
            initial_processed = 0
    else:
        print("⚠️ 进度文件不存在，将创建新文件")
        initial_processed = 0
    
    print("\n" + "=" * 70)
    print("🚀 开始导入测试数据")
    print("=" * 70)
    
    # 4. 转换数据格式（FRAMES格式 -> 导入脚本期望的格式）
    print("\n🔄 转换数据格式...")
    converted_data = []
    for item in test_data:
        # 提取Prompt作为content
        content = item.get('Prompt', item.get('question', item.get('query', '')))
        if not content:
            continue
        
        # 构建metadata
        metadata = {
            'answer': item.get('Answer', ''),
            'dataset_source': 'frames_dataset.json',
            'item_index': item.get('Unnamed: 0', len(converted_data))
        }
        
        # 提取Wikipedia链接
        wikipedia_links = []
        for i in range(1, 12):  # wikipedia_link_1 到 wikipedia_link_11+
            link = item.get(f'wikipedia_link_{i}', '')
            if link:
                wikipedia_links.append(link)
        if wikipedia_links:
            metadata['wikipedia_links'] = wikipedia_links
        
        # 添加其他字段到metadata
        for key, value in item.items():
            if key not in ['Prompt', 'Answer', 'Unnamed: 0'] and not key.startswith('wikipedia_link_'):
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
        
        converted_data.append({
            'content': content,
            'metadata': metadata
        })
    
    print(f"✅ 已转换 {len(converted_data)} 条数据")
    
    # 5. 执行导入
    try:
        build_vector_knowledge_base_from_list(
            data=converted_data,
            batch_size=2,  # 小批次，便于观察
            resume=True,
            retry_failed=True
        )
        print("\n✅ 导入完成")
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 验证元数据文件
    print("\n" + "=" * 70)
    print("🔍 验证元数据文件")
    print("=" * 70)
    
    if not metadata_path.exists():
        print("❌ 元数据文件不存在")
        return False
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        final_entry_count = len(metadata.get('entries', {}))
        new_entries = final_entry_count - initial_entry_count
        
        print(f"✅ 元数据文件格式正确")
        print(f"   初始条目数: {initial_entry_count}")
        print(f"   最终条目数: {final_entry_count}")
        print(f"   新增条目数: {new_entries}")
        
        if new_entries > 0:
            print(f"   ✅ 成功导入 {new_entries} 条知识条目")
        else:
            print(f"   ⚠️ 未新增条目（可能已存在或导入失败）")
        
        # 检查是否有临时文件残留
        temp_file = metadata_path.with_suffix('.tmp')
        if temp_file.exists():
            print(f"   ⚠️ 发现临时文件残留: {temp_file}")
        else:
            print(f"   ✅ 无临时文件残留（原子性写入正常）")
            
    except json.JSONDecodeError as e:
        print(f"❌ 元数据文件损坏: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取元数据文件失败: {e}")
        return False
    
    # 7. 验证进度文件
    print("\n" + "=" * 70)
    print("🔍 验证进度文件")
    print("=" * 70)
    
    if not progress_path.exists():
        print("⚠️ 进度文件不存在（可能未保存）")
    else:
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            final_processed = len(progress.get('processed_item_indices', []))
            final_failed = len(progress.get('failed_item_indices', []))
            new_processed = final_processed - initial_processed
            
            print(f"✅ 进度文件格式正确")
            print(f"   初始已处理: {initial_processed}")
            print(f"   最终已处理: {final_processed}")
            print(f"   新增已处理: {new_processed}")
            print(f"   失败条目数: {final_failed}")
            
            if new_processed > 0:
                print(f"   ✅ 进度文件正确更新")
            else:
                print(f"   ⚠️ 进度文件未更新（可能所有条目都已处理过）")
            
            # 检查是否有临时文件残留
            temp_file = progress_path.with_suffix('.tmp')
            if temp_file.exists():
                print(f"   ⚠️ 发现临时文件残留: {temp_file}")
            else:
                print(f"   ✅ 无临时文件残留（原子性写入正常）")
                
        except json.JSONDecodeError as e:
            print(f"❌ 进度文件损坏: {e}")
            return False
        except Exception as e:
            print(f"❌ 读取进度文件失败: {e}")
            return False
    
    # 8. 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    all_passed = True
    
    # 检查元数据文件
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print("✅ 元数据文件: 格式正确，无损坏")
        except json.JSONDecodeError:
            print("❌ 元数据文件: 损坏")
            all_passed = False
    else:
        print("❌ 元数据文件: 不存在")
        all_passed = False
    
    # 检查进度文件
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print("✅ 进度文件: 格式正确，无损坏")
        except json.JSONDecodeError:
            print("❌ 进度文件: 损坏")
            all_passed = False
    
    # 检查临时文件
    temp_files = [
        metadata_path.with_suffix('.tmp'),
        progress_path.with_suffix('.tmp')
    ]
    temp_files_found = [f for f in temp_files if f.exists()]
    if temp_files_found:
        print(f"⚠️ 临时文件残留: {len(temp_files_found)} 个")
        all_passed = False
    else:
        print("✅ 临时文件: 无残留（原子性写入正常）")
    
    if all_passed:
        print("\n🎉 所有验证通过！修复生效。")
    else:
        print("\n⚠️ 部分验证未通过，请检查上述问题。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

