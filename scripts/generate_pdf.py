"""
Generate PDF from Markdown
"""
import markdown
import sys
import os
from weasyprint import HTML

def generate_pdf(input_path, output_path):
    # Read Markdown
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Convert to HTML
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code'])

    # Add some basic styling
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; margin: 40px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            code {{ background-color: #f8f9fa; padding: 2px 4px; border-radius: 4px; font-family: monospace; }}
            pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .mermaid {{ background-color: #eeffee; border: 1px solid #ccffcc; padding: 10px; font-family: monospace; white-space: pre; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    print(f"Generating PDF from {input_path} to {output_path}...")
    HTML(string=styled_html).write_pdf(output_path)
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    
    generate_pdf(sys.argv[1], sys.argv[2])
