# 知识库内容质量问题解决方案

**创建时间**: 2025-11-13  
**问题**: 知识库内容格式混乱、不完整、包含HTML标签和引用标记

---

## 🔍 问题分析

### 当前问题

1. **HTML标签残留**：
   - 证据中包含HTML标签：`"}},"i":0}}]}' id="mwBXM">`
   - 说明HTML清理不彻底

2. **引用标记未清理**：
   - 包含引用标记：`[ 82 ]  [ 83 ]`
   - 影响LLM理解

3. **内容可能被截断**：
   - `max_length = 50000`字符限制
   - 可能导致关键信息丢失

4. **内容格式混乱**：
   - 空白字符过多
   - 段落结构不清晰

---

## 💡 解决方案

### 方案1: 改进HTML清理逻辑（优先级：高）

**位置**: `knowledge_management_system/utils/wikipedia_fetcher.py` 的 `_extract_text_from_html` 方法

**改进内容**：
1. 使用更强大的HTML解析库（BeautifulSoup）
2. 彻底清理HTML标签和属性
3. 清理引用标记（`[数字]`）
4. 清理其他格式标记
5. 改进段落格式化

### 方案2: 改进内容格式化（优先级：中）

**位置**: `knowledge_management_system/scripts/import_wikipedia_from_frames.py` 的内容合并逻辑

**改进内容**：
1. 在合并前清理每个页面的内容
2. 统一格式化
3. 确保内容完整性

### 方案3: 增加内容验证（优先级：中）

**位置**: 知识条目导入前

**改进内容**：
1. 验证内容质量
2. 检查内容完整性
3. 过滤低质量内容

---

## 🔧 实施步骤

### 步骤1: 安装依赖

```bash
pip install beautifulsoup4 lxml
```

### 步骤2: 改进HTML清理逻辑

修改 `_extract_text_from_html` 方法，使用BeautifulSoup进行更彻底的清理。

### 步骤3: 添加内容清理函数

创建统一的内容清理函数，在导入前清理所有内容。

### 步骤4: 测试和验证

使用实际数据测试改进后的清理效果。

---

## 📝 详细实现

### 实现1: 改进的HTML清理方法

```python
def _extract_text_from_html(self, html: str) -> str:
    """
    从 HTML 中提取文本内容（改进版：使用BeautifulSoup）
    
    Args:
        html: HTML 内容
        
    Returns:
        提取的文本内容
    """
    try:
        from bs4 import BeautifulSoup
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # 移除脚本和样式
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # 移除引用标记（如 [1], [2]）
        for sup in soup.find_all("sup"):
            sup.decompose()
        
        # 移除注释
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # 提取文本
        text = soup.get_text(separator='\n')
        
        # 清理引用标记（如 [ 82 ], [ 83 ]）
        text = re.sub(r'\[\s*\d+\s*\]', '', text)
        
        # 清理多余的空白字符
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # 移除空行
        text = '\n'.join(lines)
        
        # 清理多余的空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 限制长度（避免过长的内容）
        max_length = 100000  # 增加到100000字符
        if len(text) > max_length:
            # 智能截断：保留开头和关键部分
            first_part = text[:max_length // 2]
            last_part = text[-max_length // 2:]
            text = first_part + "\n\n[... 内容已截断 ...]\n\n" + last_part
        
        return text.strip()
        
    except ImportError:
        # 回退到原来的方法
        logger.warning("BeautifulSoup未安装，使用简单清理方法")
        return self._extract_text_from_html_simple(html)
    except Exception as e:
        logger.debug(f"HTML 文本提取失败: {e}")
        return ""
```

### 实现2: 内容清理函数

```python
def clean_wikipedia_content(content: str) -> str:
    """
    清理Wikipedia内容
    
    Args:
        content: 原始内容
        
    Returns:
        清理后的内容
    """
    if not content:
        return ""
    
    # 1. 清理引用标记
    content = re.sub(r'\[\s*\d+\s*\]', '', content)
    
    # 2. 清理HTML实体
    import html
    content = html.unescape(content)
    
    # 3. 清理多余的空白字符
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # 4. 清理行首行尾空白
    lines = [line.strip() for line in content.split('\n')]
    lines = [line for line in lines if line]  # 移除空行
    content = '\n'.join(lines)
    
    return content.strip()
```

### 实现3: 在导入时应用清理

在 `import_wikipedia_from_frames.py` 中，在合并内容前清理每个页面的内容：

```python
for page in wikipedia_pages:
    title = page.get('title', '')
    content = page.get('content', '') or page.get('summary', '')
    url = page.get('url', '')
    
    if content and content.strip():
        # 🚀 改进：清理内容
        content = clean_wikipedia_content(content)
        
        if title:
            merged_content_parts.append(f"## {title}\n\n{content.strip()}")
            wikipedia_titles.append(title)
        else:
            merged_content_parts.append(content.strip())
```

---

## ✅ 预期效果

1. **HTML标签完全清理**：不再有HTML标签残留
2. **引用标记清理**：不再有`[数字]`标记
3. **内容格式清晰**：段落结构清晰，空白字符合理
4. **内容完整性提升**：减少截断，保留更多关键信息

---

## 🚀 实施优先级

1. **优先级1（立即实施）**：改进HTML清理逻辑
2. **优先级2（本周内）**：添加内容清理函数
3. **优先级3（下周）**：增加内容验证

---

*创建时间: 2025-11-13*

