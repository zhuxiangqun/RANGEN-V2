#!/usr/bin/env python3
import re
import sys

def check_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取template部分
    template_start = content.find('<template>')
    template_end = content.find('</template>')
    
    if template_start == -1 or template_end == -1:
        print("错误: 未找到template标签")
        return
    
    template = content[template_start:template_end + len('</template>')]
    print(f"模板长度: {len(template)} 字符")
    
    # 简化检查：查找所有标签
    # 正则表达式匹配标签名，忽略属性
    tag_pattern = r'</?([a-zA-Z][a-zA-Z0-9\-]*(?::[a-zA-Z][a-zA-Z0-9\-]*)?)\b'
    
    lines = template.split('\n')
    stack = []
    
    for i, line in enumerate(lines, 1):
        # 查找所有标签
        matches = re.findall(tag_pattern, line)
        for tag in matches:
            # 检查是开始标签还是结束标签
            if line.strip().startswith(f'</{tag}'):
                # 结束标签
                if not stack:
                    print(f"第{i}行: 多余的结束标签 '</{tag}>'")
                    continue
                if stack[-1] != tag:
                    print(f"第{i}行: 标签不匹配，期望 '</{stack[-1]}>'，实际 '</{tag}>'")
                    # 尝试从堆栈中弹出
                    if tag in stack:
                        idx = stack.index(tag)
                        print(f"  警告: 标签 '{tag}' 在堆栈位置 {idx}")
                else:
                    stack.pop()
            else:
                # 开始标签（检查是否为自闭合）
                # 检查标签是否自闭合
                tag_end_pattern = rf'<{tag}[^>]*/>'
                if re.search(tag_end_pattern, line):
                    # 自闭合标签，不入栈
                    continue
                # 检查是否为void元素
                void_elements = {'br', 'hr', 'img', 'input', 'link', 'meta', 'area', 'base', 'col', 'embed', 'param', 'source', 'track', 'wbr'}
                if tag.lower() in void_elements:
                    continue
                
                stack.append(tag)
    
    if stack:
        print(f"\n未闭合的标签: {stack}")
        # 打印未闭合标签的位置
        for tag in stack:
            for i, line in enumerate(lines, 1):
                if re.search(rf'<{tag}\b', line) and not re.search(rf'</{tag}>', line):
                    print(f"  标签 '<{tag}>' 在第{i}行开始")
    else:
        print("标签平衡检查通过")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        check_template(sys.argv[1])
    else:
        check_template('frontend_monitor/src/App.vue')