#!/usr/bin/env python3
"""
使用pandoc生成PDF（需要LaTeX）
如果LaTeX未安装，会生成HTML供浏览器打印
"""

import sys
import subprocess
from pathlib import Path

def check_command(cmd):
    """检查命令是否可用"""
    try:
        result = subprocess.run(['which', cmd], capture_output=True)
        return result.returncode == 0
    except:
        return False

def generate_pdf_pandoc(markdown_file: str, output_file: str = None):
    """使用pandoc生成PDF"""
    md_path = Path(markdown_file)
    if not md_path.exists():
        print(f"❌ Markdown文件不存在: {markdown_file}")
        return False
    
    if output_file is None:
        output_file = md_path.with_suffix('.pdf')
    else:
        output_file = Path(output_file)
    
    # 检查pandoc
    if not check_command('pandoc'):
        print("❌ pandoc未安装")
        return False
    
    # 尝试使用xelatex（支持中文最好）
    if check_command('xelatex'):
        print("🔄 使用xelatex生成PDF（最佳中文支持）...")
        cmd = [
            'pandoc', str(md_path),
            '-o', str(output_file),
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=2.5cm',
            '-V', 'CJKmainfont=PingFang SC',
            '-V', 'CJKoptions=BoldFont=*,ItalicFont=*',
            '--toc',
            '--toc-depth=3',
            '-V', 'colorlinks=true',
            '-V', 'linkcolor=blue',
            '-V', 'urlcolor=blue'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PDF生成成功: {output_file}")
            print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")
            return True
        else:
            print(f"⚠️  xelatex生成失败: {result.stderr[:200]}")
    
    # 尝试使用pdflatex
    if check_command('pdflatex'):
        print("🔄 使用pdflatex生成PDF...")
        cmd = [
            'pandoc', str(md_path),
            '-o', str(output_file),
            '--pdf-engine=pdflatex',
            '-V', 'geometry:margin=2.5cm',
            '--toc',
            '--toc-depth=3'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PDF生成成功: {output_file}")
            print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")
            print("⚠️  注意: pdflatex对中文支持有限，建议安装xelatex")
            return True
    
    # 如果LaTeX都不可用，生成HTML供浏览器打印
    print("⚠️  LaTeX未安装，生成HTML文件供浏览器打印...")
    html_file = md_path.with_suffix('.html')
    cmd = [
        'pandoc', str(md_path),
        '-o', str(html_file),
        '--standalone',
        '--toc',
        '--toc-depth=3',
        '--css=https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css',
        '-V', 'lang=zh-CN'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ HTML生成成功: {html_file}")
        print("\n💡 请使用浏览器打开HTML文件，然后按 Cmd+P 打印为PDF")
        print(f"   打开命令: open {html_file}")
        return True
    else:
        print(f"❌ HTML生成失败: {result.stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_pdf_with_pandoc.py <markdown_file> [output_file]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = generate_pdf_pandoc(md_file, output)
    sys.exit(0 if success else 1)
