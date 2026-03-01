#!/usr/bin/env python3
"""
简单的Markdown转PDF工具
使用markdown + weasyprint（如果可用）
"""

import sys
from pathlib import Path

def generate_pdf_simple(markdown_file: str, output_file: str = None):
    """使用Python库生成PDF"""
    md_path = Path(markdown_file)
    if not md_path.exists():
        print(f"❌ Markdown文件不存在: {markdown_file}")
        return False
    
    if output_file is None:
        output_file = md_path.with_suffix('.pdf')
    else:
        output_file = Path(output_file)
    
    # 读取Markdown内容
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 尝试使用weasyprint
    try:
        import markdown
        from markdown.extensions import tables, fenced_code, toc
        from weasyprint import HTML
        from weasyprint.text.fonts import FontConfiguration
        
        # 转换Markdown为HTML，使用扩展支持表格、代码块和目录
        md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'toc',
            'codehilite',
            'nl2br'
        ])
        html_content = md.convert(md_content)
        
        # 添加样式，确保中文字体正确显示
        html_with_style = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
        }}
        @font-face {{
            font-family: "PingFang SC";
            src: local("PingFang SC"), local("PingFangSC-Regular");
        }}
        @font-face {{
            font-family: "Hiragino Sans GB";
            src: local("Hiragino Sans GB"), local("STHeiti");
        }}
        * {{
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif !important;
        }}
        body {{
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
            font-size: 12pt;
            line-height: 1.8;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
            color: #1a1a1a;
            page-break-after: avoid;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }}
        h1 {{
            font-size: 24pt;
            border-bottom: 2px solid #333;
            padding-bottom: 0.3em;
        }}
        h2 {{
            font-size: 20pt;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.2em;
        }}
        h3 {{
            font-size: 16pt;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        code {{
            font-family: "Monaco", "Menlo", "Consolas", "Courier New", monospace;
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        pre {{
            font-family: "Monaco", "Menlo", "Consolas", "Courier New", monospace;
            background-color: #f4f4f4;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #ddd;
        }}
        p {{
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
            margin: 0.8em 0;
        }}
        li {{
            font-family: "PingFang SC", "Hiragino Sans GB", "STHeiti", "Microsoft YaHei", "SimSun", sans-serif;
            margin: 0.4em 0;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        # 生成PDF，确保使用UTF-8编码
        font_config = FontConfiguration()
        HTML(
            string=html_with_style.encode('utf-8').decode('utf-8'),
            base_url=str(md_path.parent)
        ).write_pdf(
            str(output_file),
            font_config=font_config
        )
        
        print(f"✅ PDF生成成功: {output_file}")
        print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")
        return True
        
    except ImportError as e:
        print(f"❌ 缺少必要的库: {e}")
        print("\n💡 安装方法:")
        print("   pip install markdown weasyprint")
        print("\n   或者使用浏览器打印HTML文件（最简单）:")
        print(f"   open {md_path.with_suffix('.html')}")
        return False
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_pdf_simple.py <markdown_file> [output_file]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = generate_pdf_simple(md_file, output)
    sys.exit(0 if success else 1)
