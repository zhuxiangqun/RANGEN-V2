#!/usr/bin/env python3
"""
将Markdown文件转换为PDF
支持中文字体
"""

import sys
from pathlib import Path
import subprocess

def generate_pdf(markdown_file: str, output_file: str = None):
    """使用pandoc将Markdown转换为PDF"""
    md_path = Path(markdown_file)
    if not md_path.exists():
        print(f"❌ Markdown文件不存在: {markdown_file}")
        return False
    
    if output_file is None:
        output_file = md_path.with_suffix('.pdf')
    else:
        output_file = Path(output_file)
    
    # 检查pandoc
    try:
        result = subprocess.run(['which', 'pandoc'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ pandoc未安装，请先安装pandoc")
            return False
    except Exception:
        print("❌ 无法检查pandoc安装状态")
        return False
    
    # 尝试不同的PDF引擎
    engines = ['xelatex', 'pdflatex', 'wkhtmltopdf']
    
    for engine in engines:
        try:
            # 检查引擎是否可用
            check_cmd = ['which', engine] if engine != 'wkhtmltopdf' else ['which', 'wkhtmltopdf']
            check_result = subprocess.run(check_cmd, capture_output=True)
            
            if check_result.returncode == 0 or engine == 'pdflatex':
                print(f"🔄 尝试使用 {engine} 引擎...")
                
                cmd = [
                    'pandoc',
                    str(md_path),
                    '-o', str(output_file),
                    '--pdf-engine', engine,
                    '-V', 'geometry:margin=2.5cm',
                    '--toc',
                    '--toc-depth=3'
                ]
                
                # 如果是xelatex，添加中文字体支持
                if engine == 'xelatex':
                    cmd.extend(['-V', 'CJKmainfont=PingFang SC'])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ PDF生成成功: {output_file}")
                    print(f"   文件大小: {output_file.stat().st_size / 1024:.1f} KB")
                    return True
                else:
                    print(f"❌ {engine} 引擎失败: {result.stderr[:200]}")
                    continue
        except Exception as e:
            print(f"⚠️  {engine} 引擎检查失败: {e}")
            continue
    
    print("\n💡 建议:")
    print("   1. 安装LaTeX发行版（如MacTeX）以使用xelatex/pdflatex")
    print("   2. 或安装wkhtmltopdf")
    print("   3. 或使用在线工具（如 https://www.markdowntopdf.com/）")
    print("   4. 或使用Typora、VS Code插件等工具")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_pdf_from_markdown.py <markdown_file> [output_file]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = generate_pdf(md_file, output)
    sys.exit(0 if success else 1)
