# RANGEN 内置技能模板
# 对标 pc-agent-loop 的开箱即用场景

## 📱 微信自动化 (WeChat Automation)

### 读取微信消息 (Read WeChat Messages)
```yaml
name: wechat_read_messages
description: 读取微信未读消息
category: communication
triggers:
  - 读取微信
  - 查看消息
  - read wechat
keywords:
  - wechat
  - 微信
  - message
  - 消息
  - unread
steps:
  - hand: adb_hand
    action: connect
  - hand: adb_hand
    action: start_app
    package: com.tencent.mm
  - hand: adb_hand
    action: wait
    seconds: 3
  - hand: adb_hand
    action: screenshot
```

### 发送微信消息 (Send WeChat Message)
```yaml
name: wechat_send_message
description: 发送微信消息给指定联系人
category: communication
triggers:
  - 发微信
  - send wechat
keywords:
  - wechat
  - 微信
  - send
  - 发送
steps:
  - hand: adb_hand
    action: connect
  - hand: adb_hand
    action: start_app
    package: com.tencent.mm
  - hand: adb_hand
    action: tap
    x: 100
    y: 200
```

---

## 📈 股票监控 (Stock Monitoring)

### 股票价格监控 (Stock Price Monitor)
```yaml
name: stock_price_monitor
description: 监控指定股票价格并提醒
category: data_analysis
triggers:
  - 监控股票
  - stock alert
keywords:
  - stock
  - 股票
  - price
  - 价格
  - monitor
  - 监控
  - alert
  - 提醒
steps:
  - hand: web_scan
    url: https://quote.eastmoney.com/sh000001.html
  - hand: code_run
    language: python
    code: |
      # 解析股票价格
      import re
      # 返回告警格式
      {"symbol": "000001", "price": 3100, "change": 0.5}
```

### 选股策略执行 (Stock Screening)
```yaml
name: stock_screen_golden_cross
description: 筛选金叉股票
category: data_analysis
triggers:
  - 选股
  - 金叉
keywords:
  - stock
  - 股票
  - screen
  - 选股
  - golden
  - cross
steps:
  - hand: code_run
    language: python
    code: |
      # 使用mootdx进行选股
      # 筛选条件: EXPMA金叉 放量
      pass
```

---

## 📧 邮件自动化 (Email Automation)

### 发送邮件 (Send Email)
```yaml
name: email_send_gmail
description: 通过Gmail发送邮件
category: communication
triggers:
  - 发邮件
  - send email
keywords:
  - email
  - gmail
  - mail
  - 邮件
  - send
  - 发送
steps:
  - hand: browser_control
    action: navigate
    url: https://mail.google.com/mail/u/0/#inbox?compose=new
  - hand: browser_control
    action: wait
    seconds: 3
  - hand: browser_control
    action: type
    selector: "input[type=email]"
    text: recipient@example.com
```

### 读取未读邮件 (Read Unread Emails)
```yaml
name: email_read_unread
description: 读取Gmail未读邮件
category: communication
triggers:
  - 读邮件
  - read email
keywords:
  - email
  - gmail
  - unread
  - 未读
steps:
  - hand: browser_control
    action: navigate
    url: https://mail.google.com/mail/u/0/#inbox
  - hand: browser_control
    action: execute_script
    script: |
      // 获取未读邮件列表
      document.querySelectorAll('.zE').length
```

---

## 🔧 Git自动化 (Git Automation)

### 自动提交 (Auto Commit)
```yaml
name: git_auto_commit
description: 自动提交代码更改
category: development
triggers:
  - git提交
  - commit code
keywords:
  - git
  - commit
  - 提交
  - code
  - 代码
steps:
  - hand: code_run
    language: bash
    code: |
      git status
      git add -A
      git commit -m "Auto update"
  - hand: file_read
    path: .git/COMMIT_EDITMSG
```

### Git推送 (Git Push)
```yaml
name: git_push
description: 推送到远程仓库
category: development
triggers:
  - git推送
  - git push
keywords:
  - git
  - push
  - 推送
  - remote
steps:
  - hand: code_run
    language: bash
    code: |
      git push origin main
```

---

## 🖥️ 系统操作 (System Operations)

### 截图 (Screenshot)
```yaml
name: system_screenshot
description: 截取屏幕截图
category: system
triggers:
  - 截图
  - screenshot
keywords:
  - screenshot
  - 截图
  - capture
  - 屏幕
steps:
  - hand: keyboard_mouse
    operation: press
    key: command
  - hand: keyboard_mouse
    operation: press
    key: shift
  - hand: keyboard_mouse
    operation: press
    key: 4
```

### 打开应用 (Open Application)
```yaml
name: system_open_app
description: 打开指定应用程序
category: system
triggers:
  - 打开应用
  - open app
keywords:
  - app
  - 应用
  - open
  - 打开
  - launch
steps:
  - hand: keyboard_mouse
    operation: hotkey
    keys: ["command", "space"]
  - hand: keyboard_mouse
    operation: type
    text: "Safari"
  - hand: keyboard_mouse
    operation: press
    key: return
```

---

## 📝 使用方式

### 导入模板
```python
from src.templates.built_in_templates import get_template, list_templates

# 列出所有模板
templates = list_templates()

# 获取指定模板
template = get_template("wechat_read_messages")

# 注册为技能
from src.core.skill_registry import get_skill_registry
registry = get_skill_registry()
registry.register_from_sop(template.sop, relevance=1.0)
```

### 执行模板
```python
from src.templates.built_in_templates import execute_template

# 执行模板
result = await execute_template("wechat_read_messages", context={})
```
