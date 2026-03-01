#!/bin/bash
# 禁用 Cursor 中的 Gemini 扩展脚本

echo "🔍 检查 Gemini 扩展..."

CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"
CURSOR_EXTENSIONS="$HOME/.cursor/extensions"

# 检查扩展是否存在
if [ -d "$CURSOR_EXTENSIONS/google.geminicodeassist-"* ]; then
    echo "✅ 找到: Google Gemini Code Assist"
    GEMINI_FOUND=true
fi

if [ -d "$CURSOR_EXTENSIONS/printfn.gemini-improved-"* ]; then
    echo "✅ 找到: Gemini Improved"
    GEMINI_FOUND=true
fi

if [ "$GEMINI_FOUND" != "true" ]; then
    echo "ℹ️  未找到 Gemini 扩展"
    exit 0
fi

echo ""
echo "📝 更新 Cursor 设置..."

# 备份设置文件
if [ -f "$CURSOR_SETTINGS" ]; then
    cp "$CURSOR_SETTINGS" "$CURSOR_SETTINGS.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份设置文件"
fi

# 使用 Python 来更新 JSON 文件（更安全）
python3 << 'PYTHON_SCRIPT'
import json
import os
from pathlib import Path

settings_path = Path.home() / "Library/Application Support/Cursor/User/settings.json"

# 读取现有设置
if settings_path.exists():
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
else:
    settings = {}

# 添加禁用 Gemini 的设置
settings["geminicodeassist.enabled"] = False
settings["google.geminicodeassist.enabled"] = False
settings["printfn.gemini-improved.enabled"] = False

# 保存设置
with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=4, ensure_ascii=False)

print("✅ 已更新 Cursor 设置文件")
PYTHON_SCRIPT

echo ""
echo "🎯 解决方案："
echo "   1. 在 Cursor 中按 Cmd+Shift+X 打开扩展面板"
echo "   2. 搜索 'gemini'"
echo "   3. 找到以下扩展并点击 'Disable' 或 'Uninstall':"
echo "      - Google Gemini Code Assist"
echo "      - Gemini Improved"
echo "   4. 重启 Cursor"
echo ""
echo "💡 或者，您可以手动禁用扩展："
echo "   - 扩展目录: $CURSOR_EXTENSIONS"
echo "   - 可以重命名扩展目录以禁用它们"

