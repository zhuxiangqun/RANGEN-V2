#!/bin/bash
# 查看知识图谱构建进度脚本

# 获取脚本实际路径（支持符号链接）
SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT" || exit 1

# 进度文件路径
GRAPH_PROGRESS_FILE="data/knowledge_management/graph_progress.json"
ENTITIES_FILE="data/knowledge_management/graph/entities.json"
LOG_FILE="logs/knowledge_management.log"

echo "======================================================================"
echo "📊 知识图谱构建进度检查"
echo "======================================================================"
echo ""

# 检查知识图谱文件是否存在
if [ ! -f "$ENTITIES_FILE" ]; then
    echo "⚠️  知识图谱文件不存在: $ENTITIES_FILE"
    echo "   💡 提示: 知识图谱可能尚未构建或已被清理"
    echo ""
fi

# 检查进度文件
if [ ! -f "$GRAPH_PROGRESS_FILE" ]; then
    echo "⚠️  未找到进度文件: $GRAPH_PROGRESS_FILE"
    echo "   💡 提示: 知识图谱构建可能尚未开始"
    echo ""
    
    # 🚀 修复：如果知识图谱文件不存在，说明已经清除了，不应该显示历史日志中的进度
    if [ ! -f "$ENTITIES_FILE" ] || [ ! -s "$ENTITIES_FILE" ]; then
        echo "   ✅ 知识图谱文件不存在或为空，说明已清除或尚未构建"
        echo "   💡 提示: 可以运行 ./build_knowledge_graph.sh 开始构建"
        echo ""
        exit 0
    fi
    
    # 🚀 修复：检查知识图谱文件是否真的为空（实体数量为0）
    # 如果实体数量为0，说明已清除，不应该显示历史日志中的进度
    ENTITY_COUNT=$(python3 << 'PYTHON_CHECK'
import json
from pathlib import Path
try:
    entities_file = Path("data/knowledge_management/graph/entities.json")
    if entities_file.exists():
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                count = len(data)
            elif isinstance(data, list):
                count = len(data)
            else:
                count = 0
            print(count)
        exit(0)
    else:
        print(0)
        exit(0)
except Exception as e:
    print(0)
    exit(0)
PYTHON_CHECK
)
    
    # 🚀 修复：清理ENTITY_COUNT中的换行符和空格
    ENTITY_COUNT=$(echo "$ENTITY_COUNT" | tr -d '\n' | tr -d ' ')
    
    if [ "$ENTITY_COUNT" = "0" ] || [ -z "$ENTITY_COUNT" ]; then
        echo "   ✅ 知识图谱为空（实体数量: 0），说明已清除或尚未构建"
        echo "   💡 提示: 可以运行 ./build_knowledge_graph.sh 开始构建"
        echo ""
        exit 0
    fi
    
    # 尝试从日志中提取进度（仅在知识图谱文件存在且有数据时）
    if [ -f "$LOG_FILE" ]; then
        echo "📋 尝试从日志中提取进度信息..."
        echo "   ℹ️  当前知识图谱实体数量: $ENTITY_COUNT"
        echo ""
        
        # 提取最近的进度信息（只提取最近24小时内的日志）
        python3 << 'PYTHON_SCRIPT'
import re
import json
from pathlib import Path
from datetime import datetime, timedelta

log_file = Path("logs/knowledge_management.log")
if not log_file.exists():
    print("   ⚠️  日志文件不存在")
    exit(0)

# 读取日志文件，只提取最近24小时内的日志
try:
    now = datetime.now()
    recent_lines = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 从后往前读取，找到最近24小时内的日志
        for line in reversed(lines[-5000:]):  # 只检查最后5000行
            # 尝试提取时间戳（格式：2025-11-16 01:26:19）
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if time_match:
                try:
                    log_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                    if (now - log_time).total_seconds() <= 24 * 3600:  # 24小时内
                        recent_lines.insert(0, line)
                    else:
                        break  # 超过24小时，停止
                except:
                    pass
            else:
                # 如果没有时间戳，假设是最近的（在最后2000行内）
                if len(recent_lines) < 2000:
                    recent_lines.insert(0, line)
    
    log_content = ''.join(recent_lines[-2000:])  # 最多2000行
except Exception as e:
    print(f"   ⚠️  读取日志文件失败: {e}")
    exit(0)

# 查找知识图谱构建相关的日志
graph_patterns = [
    r'已处理.*?(\d+).*?条',
    r'处理条目.*?(\d+).*?知识图谱',
    r'知识图谱.*?(\d+).*?条',
    r'processed_entry_ids.*?(\d+)',
]

processed_count = 0
failed_count = 0
total_count = 0

# 尝试提取已处理数量
for pattern in graph_patterns:
    matches = re.findall(pattern, log_content, re.IGNORECASE)
    if matches:
        try:
            processed_count = max([int(m) for m in matches])
            break
        except:
            pass

# 查找失败数量
failed_patterns = [
    r'失败.*?(\d+).*?条',
    r'failed_entry_ids.*?(\d+)',
]
for pattern in failed_patterns:
    matches = re.findall(pattern, log_content, re.IGNORECASE)
    if matches:
        try:
            failed_count = max([int(m) for m in matches])
            break
        except:
            pass

if processed_count > 0 or failed_count > 0:
    print(f"   📦 从日志提取的进度信息（最近24小时内）:")
    if processed_count > 0:
        print(f"      已处理: {processed_count} 条")
    if failed_count > 0:
        print(f"      失败: {failed_count} 条")
    if total_count > 0:
        pct = (processed_count / total_count * 100) if total_count > 0 else 0
        print(f"      进度: {pct:.1f}%")
    print("")
    print("   ⚠️  注意: 这是从日志中提取的估计值，可能不准确")
    print("   ⚠️  注意: 如果知识图谱已清除，这些是历史数据，不代表当前状态")
    print("   💡 建议: 查看详细日志: tail -f $LOG_FILE")
    print("   💡 提示: 如果已清除知识图谱，可以忽略此信息")
else:
    print("   ⚠️  未在最近24小时的日志中找到知识图谱构建进度信息")
PYTHON_SCRIPT
    fi
    
    exit 0
fi

# 解析进度文件
python3 << 'PYTHON_SCRIPT'
import json
import os
from pathlib import Path
from datetime import datetime

progress_file = Path("data/knowledge_management/graph_progress.json")

try:
    with open(progress_file, 'r', encoding='utf-8') as f:
        progress = json.load(f)
except Exception as e:
    print(f"❌ 读取进度文件失败: {e}")
    exit(1)

# 提取进度信息
processed_ids = progress.get('processed_entry_ids', [])
failed_ids = progress.get('failed_entry_ids', [])
total_entries = progress.get('total_entries', 0)
start_time = progress.get('start_time')
last_update = progress.get('last_update')

# 计算进度
processed_count = len(processed_ids) if isinstance(processed_ids, list) else 0
failed_count = len(failed_ids) if isinstance(failed_ids, list) else 0

# 如果没有total_entries，尝试从知识库获取
if total_entries == 0:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from knowledge_management_system.api.service_interface import get_knowledge_service
        service = get_knowledge_service()
        all_entries = service.knowledge_manager.list_knowledge(limit=100000)
        total_entries = len(all_entries)
        # 🎯 修复：如果成功获取total_entries，更新进度文件
        if total_entries > 0:
            progress['total_entries'] = total_entries
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # 🎯 修复：如果获取失败，至少显示已处理的数量
        pass

# 计算百分比
progress_pct = (processed_count / total_entries * 100) if total_entries > 0 else 0

# 显示进度信息
print("📊 知识图谱构建进度:")
print(f"   ✅ 已处理: {processed_count}/{total_entries} ({progress_pct:.1f}%)")
if failed_count > 0:
    print(f"   ❌ 失败: {failed_count} 条")
else:
    print(f"   ❌ 失败: 0 条")

print("")

# 显示时间信息
if start_time:
    try:
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = datetime.fromtimestamp(start_time)
        print(f"   🕐 开始时间: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    except:
        print(f"   🕐 开始时间: {start_time}")

if last_update:
    try:
        if isinstance(last_update, str):
            last_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        else:
            last_dt = datetime.fromtimestamp(last_update)
        now = datetime.now()
        time_diff = now - last_dt
        hours = time_diff.total_seconds() / 3600
        
        print(f"   🕐 最后更新: {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        if hours < 1:
            print(f"      （{int(time_diff.total_seconds() / 60)} 分钟前）")
        elif hours < 24:
            print(f"      （{hours:.1f} 小时前）")
        else:
            print(f"      （{time_diff.days} 天前）")
    except:
        print(f"   🕐 最后更新: {last_update}")

print("")

# 检查是否完成
if total_entries > 0 and processed_count >= total_entries:
    print("   ✅ 知识图谱构建已完成！")
elif total_entries > 0:
    remaining = total_entries - processed_count
    print(f"   📋 剩余: {remaining} 条")
    
    # 估算剩余时间（如果可能）
    if start_time and last_update:
        try:
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = datetime.fromtimestamp(start_time)
            if isinstance(last_update, str):
                last_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            else:
                last_dt = datetime.fromtimestamp(last_update)
            
            elapsed = (last_dt - start_dt).total_seconds()
            if processed_count > 0 and elapsed > 0:
                avg_time_per_entry = elapsed / processed_count
                estimated_remaining = avg_time_per_entry * remaining
                hours = estimated_remaining / 3600
                if hours < 1:
                    print(f"   ⏱️  预计剩余时间: {int(estimated_remaining / 60)} 分钟")
                else:
                    print(f"   ⏱️  预计剩余时间: {hours:.1f} 小时")
        except:
            pass

print("")

# 检查知识图谱文件
entities_file = Path("data/knowledge_management/graph/entities.json")
relations_file = Path("data/knowledge_management/graph/relations.json")

if entities_file.exists():
    try:
        file_size = entities_file.stat().st_size
        if file_size > 10:
            # 读取实体和关系数量
            with open(entities_file, 'r', encoding='utf-8') as f:
                entities_data = json.load(f)
                if isinstance(entities_data, dict):
                    entity_count = len(entities_data)
                elif isinstance(entities_data, list):
                    entity_count = len(entities_data)
                else:
                    entity_count = 0
            
            relation_count = 0
            if relations_file.exists():
                try:
                    with open(relations_file, 'r', encoding='utf-8') as f:
                        relations_data = json.load(f)
                        if isinstance(relations_data, list):
                            relation_count = len(relations_data)
                        elif isinstance(relations_data, dict):
                            relation_count = len(relations_data)
                except:
                    pass
            
            print("   ✅ 知识图谱文件存在")
            print(f"      📁 文件大小: {file_size / 1024:.1f} KB")
            print(f"      📊 实体数量: {entity_count}")
            print(f"      🔗 关系数量: {relation_count}")
        else:
            print("   ⚠️  知识图谱文件存在但可能为空")
    except Exception as e:
        print(f"   ⚠️  读取知识图谱文件失败: {e}")
else:
    print("   ⚠️  知识图谱文件不存在")

print("")

# 检查进程是否在运行
print("💡 提示:")
print("   - 查看详细日志: tail -f logs/knowledge_management.log")
print("   - 如果构建已完成，可以开始使用知识图谱")
if failed_count > 0:
    print(f"   - 有 {failed_count} 个条目处理失败，可以使用 --retry-failed 重新处理")
PYTHON_SCRIPT

exit 0

