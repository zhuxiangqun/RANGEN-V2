# Tampermonkey 浏览器控制配置指南

## 概述

RANGEN 支持通过 Tampermonkey 用户脚本实现真实的浏览器控制，与 pc-agent-loop 对齐。

## 安装步骤

### 1. 安装 Tampermonkey 扩展

- **Chrome**: https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo
- **Edge**: https://microsoftedge.microsoft.com/addons/detail/tampermonkey/igbgpehnbmhgdgejabcpmejjgjhonmpm
- **Firefox**: https://addons.mozilla.org/firefox/addon/tampermonkey/

### 2. 安装 RANGEN 用户脚本

1. 打开 Tampermonkey 管理面板
2. 点击 "+" 新建脚本
3. 复制 `src/hands/tampermonkey_script.js` 的内容
4. 保存脚本

### 3. 配置 RANGEN API 服务器

启动 RANGEN 时需要启用浏览器控制 API：

```bash
# 确保环境变量配置
export RANGEN_BROWSER_API_ENABLED=true
export RANGEN_BROWSER_API_PORT=8080

# 启动
python -m src.api.server
```

## 使用方法

### Python 端

```python
from src.hands.tmwebdriver import TMWebDriver

# 创建浏览器控制实例
browser = TMWebDriver(browser_type="chrome")

# 连接到浏览器（需要在浏览器中启用脚本）
result = await browser.connect()

# 执行操作
result = await browser.navigate("https://example.com")
result = await browser.click(selector="#submit-button")
result = await browser.type_text(selector="#input", text="hello")

# 获取页面内容
content = await browser.get_page_content()

# 断开连接
await browser.disconnect()
```

### 支持的操作

| 操作 | 说明 | 参数 |
|------|------|------|
| `navigate` | 导航到 URL | `url` |
| `click` | 点击元素 | `selector` |
| `type` | 输入文本 | `selector`, `value` |
| `get_text` | 获取文本 | `selector` |
| `get_html` | 获取 HTML | `selector` |
| `screenshot` | 截图 | - |
| `execute_script` | 执行 JS | `script` |

## 安全说明

⚠️ **重要**：

1. **只在受信任的网站上使用** - 脚本会与页面内容交互
2. **保持登录状态** - 与 Selenium 不同，脚本保留用户登录状态
3. **授权确认** - 建议在执行敏感操作前添加确认步骤

## 故障排除

### 脚本未激活

- 检查 Tampermonkey 图标是否显示脚本数量
- 刷新页面或重新加载脚本

### 无法连接到 RANGEN

- 检查 API 服务器是否运行在端口 8080
- 检查 `RANGEN_BROWSER_API_ENABLED=true`

### 操作失败

- 检查页面元素选择器是否正确
- 尝试使用更具体的选择器

## 与 Playwright 对比

| 特性 | Tampermonkey | Playwright |
|------|---------------|------------|
| 登录状态 | ✅ 保留 | ❌ 需重新登录 |
| 安装复杂度 | 中 | 低 |
| 跨域限制 | 无 | 有 |
| 截图 | 受限 | ✅ 完全支持 |
| 运行环境 | 真实浏览器 | 自动化浏览器 |
