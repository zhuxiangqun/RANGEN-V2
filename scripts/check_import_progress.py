#!/usr/bin/env python3
"""
检查知识库导入进度
支持检查Wikipedia导入进度和向量知识库构建进度
"""

import json
from pathlib import Path
from datetime import datetime

def check_progress_file(progress_file: Path, progress_type: str):
    """检查单个进度文件"""
    if not progress_file.exists():
        return False
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        
        # 知识图谱进度文件使用不同的格式（processed_entry_ids）
        if 'processed_entry_ids' in progress:
            processed = len(progress.get('processed_entry_ids', []))
            total = progress.get('total_entries', 0) or len(progress.get('processed_entry_ids', []))
            failed = len(progress.get('failed_entry_ids', []))
        else:
            # 向量知识库和Wikipedia导入使用 processed_item_indices
            processed = len(progress.get('processed_item_indices', []))
            total = progress.get('total_items', 0)
            failed = len(progress.get('failed_item_indices', []))
        
        print(f"\n📊 {progress_type}进度:")
        if total > 0:
            percentage = (processed / total) * 100
            remaining = total - processed
            print(f"   ✅ 已处理: {processed}/{total} ({percentage:.1f}%)")
            print(f"   ⏳ 剩余: {remaining} 条")
            if failed > 0:
                print(f"   ❌ 失败: {failed} 条")
        else:
            print(f"   ✅ 已处理: {processed} 条")
            if failed > 0:
                print(f"   ❌ 失败: {failed} 条")
        
        if progress.get('start_time'):
            try:
                start_time = datetime.fromisoformat(progress['start_time'])
                print(f"   🕐 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"   🕐 开始时间: {progress['start_time']}")
        
        if progress.get('last_update'):
            try:
                last_update = datetime.fromisoformat(progress['last_update'])
                print(f"   🕐 最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 计算运行时间
                if progress.get('start_time'):
                    try:
                        start_time = datetime.fromisoformat(progress['start_time'])
                        elapsed = last_update - start_time
                        hours = int(elapsed.total_seconds() // 3600)
                        minutes = int((elapsed.total_seconds() % 3600) // 60)
                        if hours > 0:
                            print(f"   ⏱️  运行时间: {hours}小时{minutes}分钟")
                        else:
                            print(f"   ⏱️  运行时间: {minutes}分钟")
                    except:
                        pass
            except:
                print(f"   🕐 最后更新: {progress['last_update']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 读取进度文件失败: {e}")
        return False

def check_import_progress():
    """检查所有导入进度"""
    print("=" * 70)
    print("📊 知识库导入进度检查")
    print("=" * 70)
    
    # 检查Wikipedia导入进度
    # 说明：这是第一阶段，从FRAMES数据集抓取Wikipedia页面内容
    wikipedia_progress_file = Path("data/knowledge_management/import_progress.json")
    found_wikipedia = check_progress_file(wikipedia_progress_file, "Wikipedia导入（第一阶段：抓取内容）")
    
    # 检查向量知识库构建进度
    # 说明：这是第二阶段，将抓取的内容向量化并构建索引
    # 注意：build_vector_knowledge_base.py 内部调用 import_wikipedia_from_frames.py
    # 所以实际上使用的是同一个进度文件 import_progress.json
    vector_progress_file = Path("data/knowledge_management/vector_import_progress.json")
    found_vector = check_progress_file(vector_progress_file, "向量知识库构建（第二阶段：向量化）")
    
    # 🚀 修复：如果进度文件存在，记录其内容，用于与日志进度对比
    # 进度文件是权威来源，应该优先使用进度文件的数据
    progress_file_data = None
    if wikipedia_progress_file.exists():
        try:
            with open(wikipedia_progress_file, 'r', encoding='utf-8') as f:
                progress_file_data = json.load(f)
        except:
            pass
    
    # 检查知识图谱构建进度
    graph_progress_file = Path("data/knowledge_management/graph_progress.json")
    found_graph = False
    
    # 先检查知识图谱文件是否已被清理
    entities_file = Path("data/knowledge_management/graph/entities.json")
    graph_cleared = False
    if not entities_file.exists():
        graph_cleared = True
    else:
        try:
            if entities_file.stat().st_size < 10:  # 文件很小，可能是空的
                graph_cleared = True
        except:
            pass
    
    # 如果知识图谱已被清理，但进度文件还存在，提示删除
    if graph_cleared and graph_progress_file.exists():
        print(f"\n⚠️  发现旧的知识图谱进度文件:")
        print(f"   📁 文件: {graph_progress_file}")
        try:
            import os
            from datetime import datetime as dt
            file_mtime = os.path.getmtime(graph_progress_file)
            file_time = dt.fromtimestamp(file_mtime)
            now = dt.now()
            days_old = (now - file_time).days
            print(f"   📅 创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')} ({days_old} 天前)")
        except Exception:
            pass
        print(f"   ✅ 知识图谱文件已被清理")
        print(f"   🔧 建议删除此旧进度文件:")
        print(f"      rm {graph_progress_file}")
    elif graph_progress_file.exists():
        # 知识图谱还存在，显示进度
        found_graph = check_progress_file(graph_progress_file, "知识图谱构建")
        
        # 如果知识图谱进度文件存在但时间很旧，添加说明
        if found_graph:
            try:
                import os
                from datetime import datetime as dt
                file_mtime = os.path.getmtime(graph_progress_file)
                file_time = dt.fromtimestamp(file_mtime)
                now = dt.now()
                days_old = (now - file_time).days
                
                if days_old > 1:
                    print(f"   ⚠️  注意: 此进度文件是 {days_old} 天前的旧文件")
                    print(f"   💡 提示: 这是知识图谱构建的进度，不是向量知识库构建的进度")
            except Exception:
                pass
    
    # 检查日志文件，提取向量知识库的实际进度
    # 🚀 修复：如果进度文件存在，优先使用进度文件的数据，日志仅作为补充信息
    log_file = Path("logs/knowledge_management.log")
    found_progress_in_log = False  # 🚀 修复：初始化标志变量
    
    # 如果进度文件存在，直接使用进度文件的数据，不需要从日志提取
    if progress_file_data and not found_wikipedia:
        # 进度文件存在但check_progress_file没有显示（可能因为格式问题），手动显示
        file_processed = len(progress_file_data.get('processed_item_indices', []))
        file_total = progress_file_data.get('total_items', 0)
        file_failed = len(progress_file_data.get('failed_item_indices', []))
        
        if file_total > 0:
            print(f"\n📊 Wikipedia导入进度（从进度文件）:")
            percentage = (file_processed / file_total) * 100
            remaining = file_total - file_processed
            print(f"   ✅ 已处理: {file_processed}/{file_total} ({percentage:.1f}%)")
            print(f"   ⏳ 剩余: {remaining} 条")
            if file_failed > 0:
                print(f"   ❌ 失败: {file_failed} 条")
            if progress_file_data.get('last_update'):
                try:
                    from datetime import datetime as dt
                    last_update = dt.fromisoformat(progress_file_data['last_update'])
                    print(f"   🕐 最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    print(f"   🕐 最后更新: {progress_file_data['last_update']}")
            found_wikipedia = True
    
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找数据集总数和实际进度
            import re
            dataset_total = None
            latest_progress = None
            latest_timestamp = None
            items_to_process_info = None
            
            # 查找数据集加载信息
            for line in lines:
                # 查找数据集加载完成信息
                if "数据集加载完成" in line or "✅ 数据集加载完成" in line or "📥 加载数据集" in line:
                    match = re.search(r'(\d+)\s*条数据', line)
                    if match:
                        dataset_total = int(match.group(1))
                
                # 查找"需要处理"信息（断点续传时会显示）
                if "需要处理" in line and "/" in line:
                    match = re.search(r'(\d+)/(\d+)\s*条数据项', line)
                    if match:
                        items_to_process_info = (int(match.group(1)), int(match.group(2)))
                        # 如果找到了需要处理的信息，总数就是第二个数字
                        if not dataset_total:
                            dataset_total = int(match.group(2))
            
            # 如果还没找到总数，尝试从数据集文件读取
            if not dataset_total:
                dataset_file = Path("data/frames_dataset.json")
                if dataset_file.exists():
                    try:
                        with open(dataset_file, 'r', encoding='utf-8') as f:
                            dataset_data = json.load(f)
                            if isinstance(dataset_data, list):
                                dataset_total = len(dataset_data)
                    except:
                        pass
            
            # 查找最新的导入进度信息
            # 🚀 修复：同时显示两种进度
            # 1. FRAMES数据项进度（"📊 总体进度: X/Y"）- 这是FRAMES数据集的进度
            # 2. 知识条目进度（"📊 导入进度: X/Y" 或 "处理条目 X/Y: Item N"）- 这是实际导入的知识条目进度
            
            # 🚀 修复：获取进度文件的开始时间，只提取该时间之后的日志进度
            progress_file_start_time = None
            if progress_file_data and progress_file_data.get('start_time'):
                try:
                    from datetime import datetime as dt
                    progress_file_start_time = dt.fromisoformat(progress_file_data['start_time'])
                except:
                    pass
            
            frames_progress = None  # FRAMES数据项进度
            knowledge_entry_progress = None  # 知识条目进度
            frames_timestamp = None
            knowledge_timestamp = None
            
            # 首先查找FRAMES数据项进度（"总体进度"）
            for line in reversed(lines[-2000:]):
                overall_progress_match = re.search(r'总体进度:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)', line)
                if overall_progress_match:
                    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if time_match:
                        timestamp = time_match.group(1)
                        # 🚀 修复：只提取进度文件开始时间之后的日志进度
                        if progress_file_start_time:
                            try:
                                from datetime import datetime as dt
                                log_time = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                if log_time < progress_file_start_time:
                                    continue  # 跳过旧日志
                            except:
                                pass
                        
                        processed = int(overall_progress_match.group(1))
                        actual_total = int(overall_progress_match.group(2))
                        percentage = overall_progress_match.group(3)
                        
                        if not frames_progress or (frames_timestamp is not None and timestamp > frames_timestamp) or frames_timestamp is None:
                            frames_progress = (processed, actual_total, percentage)
                            frames_timestamp = timestamp
                        break  # 找到最新的就停止
            
            # 查找知识条目进度（"导入进度"或"处理条目"）
            for line in reversed(lines[-2000:]):
                time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not time_match:
                    continue
                
                timestamp = time_match.group(1)
                # 🚀 修复：只提取进度文件开始时间之后的日志进度
                if progress_file_start_time:
                    try:
                        from datetime import datetime as dt
                        log_time = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        if log_time < progress_file_start_time:
                            continue  # 跳过旧日志
                    except:
                        pass
                
                # 查找"📊 导入进度"
                import_progress_match = re.search(r'📊 导入进度:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)', line)
                if import_progress_match:
                    processed = int(import_progress_match.group(1))
                    total = int(import_progress_match.group(2))
                    percentage = import_progress_match.group(3)
                    
                    if not knowledge_entry_progress or (knowledge_timestamp is not None and timestamp > knowledge_timestamp) or knowledge_timestamp is None:
                        knowledge_entry_progress = (processed, total, percentage)
                        knowledge_timestamp = timestamp
                    break  # 找到最新的就停止
                
                # 查找"处理条目 X/Y: Item N"（这是当前批次的进度）
                entry_progress_match = re.search(r'处理条目\s*(\d+)/(\d+)\s*\(([\d.]+)%\)', line)
                if entry_progress_match:
                    processed = int(entry_progress_match.group(1))
                    total = int(entry_progress_match.group(2))
                    percentage = entry_progress_match.group(3)
                    
                    if not knowledge_entry_progress or (knowledge_timestamp is not None and timestamp > knowledge_timestamp) or knowledge_timestamp is None:
                        knowledge_entry_progress = (processed, total, percentage)
                        knowledge_timestamp = timestamp
                    break  # 找到最新的就停止
            
            # 如果没有找到FRAMES数据项进度，尝试从Item编号推断
            if not frames_progress:
                max_item_index = -1
                latest_item_timestamp = None
                for line in reversed(lines[-2000:]):
                    entry_progress_match = re.search(r'处理条目\s*(\d+)/(\d+)\s*\(([\d.]+)%\):\s*Item\s*(\d+)', line)
                    if entry_progress_match:
                        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if time_match:
                            timestamp = time_match.group(1)
                            item_index = int(entry_progress_match.group(4))
                            if item_index > max_item_index or (item_index == max_item_index and (latest_item_timestamp is None or timestamp > latest_item_timestamp)):
                                max_item_index = item_index
                                latest_item_timestamp = timestamp
                
                # 如果找到了Item编号，并且有"需要处理"信息，可以推断FRAMES数据项进度
                if max_item_index >= 0 and items_to_process_info:
                    if max_item_index >= items_to_process_info[0]:
                        processed_count = max_item_index - items_to_process_info[0] + 1
                        actual_total = items_to_process_info[1]
                        percentage = (processed_count / actual_total * 100) if actual_total > 0 else 0
                        frames_progress = (processed_count, actual_total, f"{percentage:.1f}")
                        frames_timestamp = latest_item_timestamp
            
            # 组合两种进度
            if frames_progress or knowledge_entry_progress:
                # 使用最新的时间戳
                latest_timestamp = frames_timestamp if frames_timestamp else knowledge_timestamp
                if frames_timestamp and knowledge_timestamp:
                    latest_timestamp = frames_timestamp if frames_timestamp > knowledge_timestamp else knowledge_timestamp
                
                # 创建进度元组
                if frames_progress:
                    frames_processed, frames_total, frames_pct = frames_progress
                else:
                    frames_processed, frames_total, frames_pct = 0, dataset_total or 0, "0.0"
                
                if knowledge_entry_progress:
                    entry_processed, entry_total, entry_pct = knowledge_entry_progress
                else:
                    entry_processed, entry_total, entry_pct = 0, 0, "0.0"
                
                latest_progress = (frames_processed, frames_total, frames_pct, entry_processed, entry_total, entry_pct, latest_timestamp or "unknown")
            
            if latest_progress:
                found_progress_in_log = True  # 🚀 修复：标记已找到日志进度
                frames_processed, frames_total, frames_pct, entry_processed, entry_total, entry_pct, timestamp = latest_progress
                
                # 🚀 修复：如果进度文件存在，对比日志进度和进度文件进度，检查一致性
                # 如果不一致，说明代码有问题（要么是进度文件保存有问题，要么是日志输出有问题）
                if progress_file_data:
                    file_processed = len(progress_file_data.get('processed_item_indices', []))
                    file_total = progress_file_data.get('total_items', 0)
                    file_failed = len(progress_file_data.get('failed_item_indices', []))
                    
                    # 对比FRAMES数据项进度
                    if file_total > 0 and frames_total > 0:
                        if file_processed != frames_processed or file_total != frames_total:
                            print(f"\n❌ 进度不一致错误:")
                            print(f"   📁 进度文件: {file_processed}/{file_total} ({file_processed/file_total*100:.1f}%)")
                            print(f"   📝 日志进度: {frames_processed}/{frames_total} ({frames_pct}%)")
                            print(f"   ⚠️  警告: 进度文件与日志进度不一致，说明代码存在问题！")
                            print(f"   💡 可能的原因:")
                            print(f"      1. 进度文件保存失败或保存时机不对")
                            print(f"      2. 日志输出时机不对或格式错误")
                            print(f"      3. 进度文件被外部修改或损坏")
                            print(f"   🔧 建议: 检查 import_wikipedia_from_frames.py 中的进度保存和日志输出逻辑")
                            # 不强制使用进度文件的数据，而是报告问题
                        else:
                            print(f"\n✅ 进度一致性检查: 日志进度与进度文件一致")
                
                print(f"\n📊 向量知识库构建进度（从日志提取，包含向量化）:")
                print(f"   💡 说明: 这是完整的构建进度，包括Wikipedia内容抓取和向量化两个阶段")
                
                # 检查时间戳是否很旧
                try:
                    from datetime import datetime
                    if timestamp != "unknown":
                        log_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        minutes_ago = (now - log_time).total_seconds() / 60
                        
                        if minutes_ago > 30:
                            print(f"   ⚠️  注意: 日志中的进度信息是 {int(minutes_ago)} 分钟前的")
                            print(f"   💡 提示: 程序可能已完成或正在处理其他任务")
                except:
                    pass
                
                # 🚀 修复：同时显示FRAMES数据项进度和知识条目进度
                print(f"\n   📦 FRAMES数据项进度（数据集层面）:")
                if frames_total > 0:
                    frames_pct_float = float(frames_pct) if isinstance(frames_pct, str) else frames_pct
                    print(f"      ✅ 已处理: {frames_processed}/{frames_total} ({frames_pct_float:.1f}%)")
                    remaining_frames = frames_total - frames_processed
                    if remaining_frames > 0:
                        print(f"      ⏳ 剩余: {remaining_frames} 个FRAMES数据项")
                else:
                    print(f"      ⚠️  无法确定FRAMES数据项总数")
                
                print(f"\n   📚 知识条目进度（实际导入的知识条目）:")
                if entry_total > 0:
                    entry_pct_float = float(entry_pct) if isinstance(entry_pct, str) else entry_pct
                    print(f"      ✅ 已导入: {entry_processed}/{entry_total} ({entry_pct_float:.1f}%)")
                    remaining_entries = entry_total - entry_processed
                    if remaining_entries > 0:
                        print(f"      ⏳ 剩余: {remaining_entries} 个知识条目")
                    print(f"      💡 说明: 一个FRAMES数据项可能产生多个知识条目（多个Wikipedia链接或内容分块）")
                else:
                    print(f"      ⚠️  无法确定知识条目总数")
                
                print(f"\n   🕐 最后更新: {timestamp}")
                
                # 检查是否完成
                frames_pct_float = float(frames_pct) if isinstance(frames_pct, str) else frames_pct
                if frames_pct_float >= 100.0 and frames_processed >= frames_total:
                    print(f"   ✅ FRAMES数据项导入已完成！")
                    print(f"   💡 提示: 程序可能正在处理未向量化的条目或进行最终清理")
                elif entry_total > 0:
                    entry_pct_float = float(entry_pct) if isinstance(entry_pct, str) else entry_pct
                    if entry_pct_float >= 100.0:
                        print(f"   ⚠️  当前批次的知识条目已完成，但可能还有更多FRAMES数据项需要处理")
                        print(f"   💡 提示: 程序可能正在处理下一批次或进行其他操作")
                
                # 检查程序是否还在运行
                import subprocess
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "build_vector_knowledge_base"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"   🔄 程序正在运行中...")
                    else:
                        print(f"   ⚠️  程序可能已停止运行")
                except:
                    pass
        except Exception as e:
            print(f"   ⚠️  读取日志文件失败: {e}")
    
    # 如果没找到进度文件，显示提示
    # 🚀 修复：如果从日志中提取到了进度，说明程序正在运行，不显示"未找到进度文件"的警告
    
    if not found_wikipedia and not found_vector and not found_graph and not found_progress_in_log:
        print("\n⚠️  未找到任何进度文件")
        
        print("\n   可能的原因：")
        print("   1. 导入程序还未开始运行")
        print("   2. 导入程序已完成并清理了进度文件")
        print("   3. 使用了 --no-resume 参数从头开始")
        print("\n💡 提示：")
        print("   - Wikipedia导入进度: data/knowledge_management/import_progress.json")
        print("   - 向量知识库进度: data/knowledge_management/vector_import_progress.json")
        print("   - 知识图谱进度: data/knowledge_management/graph_progress.json")
        print("   - 查看日志: tail -f logs/knowledge_management.log")
    elif not found_wikipedia and not found_vector and not found_graph and found_progress_in_log:
        # 🚀 修复：如果从日志中提取到了进度，但进度文件不存在，说明程序正在运行但进度文件可能还未创建或已被清理
        print("\n💡 提示：")
        print("   - 进度信息从日志中提取，程序正在运行中")
        print("   - 进度文件可能还未创建或已被清理")
        print("   - 查看详细日志: tail -f logs/knowledge_management.log")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    check_import_progress()
