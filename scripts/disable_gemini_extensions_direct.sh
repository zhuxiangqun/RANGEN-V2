#!/bin/bash
# 直接禁用 Gemini 扩展（通过重命名扩展目录）

echo "🔍 正在禁用 Gemini 扩展..."

CURSOR_EXTENSIONS="$HOME/.cursor/extensions"
BACKUP_DIR="$HOME/.cursor/extensions_disabled_$(date +%Y%m%d_%H%M%S)"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 禁用 Google Gemini Code Assist
if [ -d "$CURSOR_EXTENSIONS/google.geminicodeassist-"* ]; then
    GEMINI_DIR=$(ls -d "$CURSOR_EXTENSIONS/google.geminicodeassist-"* 2>/dev/null | head -1)
    if [ -n "$GEMINI_DIR" ]; then
        echo "📦 禁用: Google Gemini Code Assist"
        mv "$GEMINI_DIR" "$BACKUP_DIR/" 2>/dev/null && echo "   ✅ 已移动到: $BACKUP_DIR" || echo "   ⚠️  移动失败（可能已被禁用）"
    fi
fi

# 禁用 Gemini Improved
if [ -d "$CURSOR_EXTENSIONS/printfn.gemini-improved-"* ]; then
    GEMINI_DIR=$(ls -d "$CURSOR_EXTENSIONS/printfn.gemini-improved-"* 2>/dev/null | head -1)
    if [ -n "$GEMINI_DIR" ]; then
        echo "📦 禁用: Gemini Improved"
        mv "$GEMINI_DIR" "$BACKUP_DIR/" 2>/dev/null && echo "   ✅ 已移动到: $BACKUP_DIR" || echo "   ⚠️  移动失败（可能已被禁用）"
    fi
fi

echo ""
echo "✅ 完成！"
echo ""
echo "📝 扩展已被移动到: $BACKUP_DIR"
echo "💡 如果需要恢复，可以运行："
echo "   mv $BACKUP_DIR/* ~/.cursor/extensions/"
echo ""
echo "🔄 请重启 Cursor 以使更改生效"

