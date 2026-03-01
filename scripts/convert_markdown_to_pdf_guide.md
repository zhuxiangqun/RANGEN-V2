# Markdown转PDF指南

## 已生成的文件

✅ **Markdown文件**: `docs/AI面试官系统技术架构设计文档.md`  
✅ **HTML文件**: `docs/AI面试官系统技术架构设计文档.html`（如果生成成功）

## 转换为PDF的方法

### 方法1: 使用浏览器打印（推荐，最简单）

1. 打开生成的HTML文件：
   ```bash
   open docs/AI面试官系统技术架构设计文档.html
   ```

2. 在浏览器中按 `Cmd+P` (Mac) 或 `Ctrl+P` (Windows/Linux)

3. 选择"另存为PDF"或"保存为PDF"

4. 在打印设置中：
   - 选择"更多设置"
   - 勾选"背景图形"（保留样式）
   - 选择"边距"为"默认"或"最小"
   - 点击"保存"

### 方法2: 使用Typora（如果已安装）

1. 打开 `docs/AI面试官系统技术架构设计文档.md`
2. 菜单：文件 → 导出 → PDF
3. 调整样式和设置后导出

### 方法3: 使用VS Code插件

1. 安装插件：`Markdown PDF` 或 `vscode-pdf`
2. 打开Markdown文件
3. 右键选择"Markdown PDF: Export (pdf)"

### 方法4: 在线工具

1. 访问 https://www.markdowntopdf.com/
2. 上传Markdown文件
3. 下载生成的PDF

### 方法5: 安装LaTeX后使用pandoc（最佳质量）

```bash
# macOS
brew install --cask mactex

# 然后运行
pandoc docs/AI面试官系统技术架构设计文档.md \
  -o docs/AI面试官系统技术架构设计文档.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=2.5cm \
  -V CJKmainfont="PingFang SC" \
  --toc \
  --toc-depth=3
```

## 推荐方案

**最简单**: 方法1（浏览器打印）  
**最佳质量**: 方法5（pandoc + LaTeX）  
**最方便**: 方法2（Typora）
