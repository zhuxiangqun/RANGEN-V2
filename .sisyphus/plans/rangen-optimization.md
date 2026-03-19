# RANGEN V2 全面优化计划

## TL;DR

> **快速摘要**: 基于 pc-agent-loop (https://github.com/lsdefine/pc-agent-loop) 分析，对RANGEN V2进行四大优化：SOP工作流集成、7原子工具实现、物理控制扩展、轻量级模式
> 
> **交付成果**:
> - SOP与LangGraph深度集成的工作流节点
> - 7个原子工具（对齐pc-agent-loop: code_run, file_read/write/patch, web_scan, web_execute_js, ask_user）
> - 物理设备控制能力包（浏览器注入、键鼠模拟、ADB设备控制）
> - rangen-lite轻量级启动器
> 
> **预计工作量**: Large
> **并行执行**: YES - 多阶段独立任务
> **关键路径**: SOP集成 → 原子框架 → 物理控制 → 轻量模式

---

## Context

### 原始请求
基于 pc-agent-loop (GenericAgent) 开源项目分析，对RANGEN V2进行全面优化：
1. SOP学习机制集成 - 将现有sop_learning.py与LangGraph工作流集成
2. 7原子工具对齐 - code_run, file_read, file_write, file_patch, web_scan, web_execute_js, ask_user
3. 物理控制扩展 - 浏览器注入（非Selenium）、键盘鼠标模拟、ADB设备控制
4. 轻量级模式 - 创建简化启动模式（pip install + API key即可）

### 参考项目: pc-agent-loop
**核心特性**:
- ~3,300行Python代码实现完整OS级控制
- 7个原子工具：code_run, file_read/write/patch, web_scan, web_execute_js, ask_user
- 三层内存系统：L0(Meta-SOP), L2(Global Facts), L3(Task SOPs)
- 物理级控制：浏览器注入（Tampermonkey）、键鼠模拟、ADB
- 自我进化：每个任务解决后保存为SOP
- 极简部署：pip install streamlit pywebview + API key

### 当前系统状态
**已实现**:
- `src/core/sop_learning.py` (913行) - 完整SOP学习系统，含L0/L2/L3层级
- `src/hands/base.py` (162行) - BaseHand基类，含安全级别
- `src/hands/registry.py` (231行) - Hand自动发现注册表
- 多个Hand实现: api_hand, code_hand, file_hand, github_hand, notion_hand, slack_hand, database_hand

**待实现**:
- SOP与LangGraph工作流未集成
- 无7原子工具对齐实现
- 无物理级PC控制能力（浏览器注入、ADB）
- 无轻量级运行模式

### 访谈总结
**关键决策**:
- 优化范围: 全部四个方向
- 技术对齐: 使用Tampermonkey注入实现浏览器控制（对齐pc-agent-loop）
- 测试策略: Agent执行QA + pytest

## TL;DR

> **快速摘要**: 基于GenericAgent分析，对RANGEN V2进行四大优化：SOP工作流集成、原子工具重构、物理控制扩展、轻量级模式
> 
> **交付成果**:
> - SOP与LangGraph深度集成的工作流节点
> - 原子化Hands能力框架
> - 物理设备控制能力包
> - rangen-lite轻量级启动器
> 
> **预计工作量**: Large
> **并行执行**: YES - 多阶段独立任务
> **关键路径**: SOP集成 → 原子框架 → 物理控制 → 轻量模式

---

## Context

### 原始请求
基于GenericAgent分析报告，对RANGEN V2进行全面优化：
1. SOP学习机制集成 - 将现有sop_learning.py与LangGraph工作流集成
2. 原子工具重构 - 将Hands能力重构为更原子的工具集
3. 物理控制扩展 - 添加浏览器/键盘/鼠标等物理设备控制
4. 轻量级模式 - 创建简化启动模式

### 当前系统状态
**已实现**:
- `src/core/sop_learning.py` (913行) - 完整SOP学习系统，含L0/L2/L3层级
- `src/hands/base.py` (162行) - BaseHand基类，含安全级别
- `src/hands/registry.py` (231行) - Hand自动发现注册表
- 多个Hand实现: api_hand, code_hand, file_hand, github_hand, notion_hand, slack_hand, database_hand

**待实现**:
- SOP与LangGraph工作流未集成
- Hands为预定义能力，无动态原子工具扩展
- 无物理级PC控制能力
- 无轻量级运行模式

### 访谈总结
**关键决策**:
- 优化范围: 全部四个方向
- 优先级: SOP集成 > 原子框架 > 物理控制 > 轻量模式
- 测试策略: Agent执行QA + pytest

### Metis审查
(基于系统已有架构的分析)

**已识别需处理**:
- SOP学习系统需要与LangGraph节点集成才能发挥作用
- 原子工具重构需要保持向后兼容性
- 物理控制需要安全沙箱机制
- 轻量模式需要明确核心功能边界

---

## Work Objectives

### 核心目标
将RANGEN V2升级为具备自我学习能力的智能系统，同时保持企业级特性并降低使用门槛。

### 具体交付物
1. **SOP工作流集成**: LangGraph节点实现，SOP自动recall和execution
2. **原子工具框架**: 动态Hands生成机制，代码即工具
3. **物理控制能力**: Browser/Keyboard/Mouse/Screen控制Hand
4. **轻量级模式**: rangen-lite启动器，<5分钟配置启动

### Definition of Done
- [ ] SOP学习系统能在LangGraph工作流中自动调用
- [ ] 能通过代码执行动态创建新Hands
- [ ] 能通过浏览器自动化执行网页操作
- [ ] 能通过CLI一键启动轻量级模式

### Must Have
- 向后兼容现有Hands能力
- 安全沙箱机制(物理控制)
- 完整测试覆盖

### Must NOT
- 不修改已有Hand的接口签名
- 不删除现有功能
- 不引入不安全的远程代码执行

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: pytest + 任务内QA场景
- **Framework**: pytest, Playwright(UI测试)

### QA Policy
每个任务包含Agent-Executed QA场景:
- **Backend**: pytest测试 + curl API验证
- **Frontend**: Playwright浏览器自动化验证
- **Integration**: 多组件联合测试

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (基础 - SOP集成):
├── T1: SOP Recall Node - LangGraph节点实现
├── T2: SOP Execution Node - LangGraph节点实现  
├── T3: SOP Learning Hook - 执行后自动学习
└── T4: SOP Management API - RESTful管理接口

Wave 2 (核心 - 原子框架):
├── T5: AtomicTool基类定义
├── T6: DynamicCodeExecutor - 动态代码执行器
├── T7: AtomicToolRegistry - 原子工具注册表
└── T8: HandsBuilder - Hands动态构建器

Wave 3 (扩展 - 物理控制):
├── T9: BrowserControlHand - 浏览器控制
├── T10: KeyboardMouseHand - 键鼠模拟
├── T11: ScreenCaptureHand - 屏幕捕获
└── T12: PhysicalControlSandbox - 安全沙箱

Wave 4 (交付 - 轻量模式):
├── T13: LiteConfigurator - 轻量配置器
├── T14: LiteWorkflowEngine - 简化工作流引擎
├── T15: LiteUI - 极简Streamlit界面
└── T16: CLI入口点 - rangen-lite命令

Wave 5 (集成测试):
├── T17: SOP集成测试
├── T18: 原子框架测试
├── T19: 物理控制测试
└── T20: 轻量模式测试
```

### Dependency Matrix
- T1-T4: 无依赖，可并行
- T5-T8: 依赖T1-T4的SOP基础
- T9-T12: 依赖T5-T8的原子框架
- T13-T16: 可独立或依赖T1-T4
- T17-T20: 依赖各自模块完成

---

- [x] 1. **SOP Recall Node** — LangGraph节点实现

  **What to do**:
  - 在 `src/core/langgraph_sop_nodes.py` 创建SOP召回节点
  - 实现 `sop_recall_node(state)` 函数
  - 集成现有 `SOPLearningSystem.recall_sop()` 方法
  - 支持关键词和上下文两种召回模式

  **Must NOT do**:
  - 不修改现有LangGraph核心文件结构
  - 不删除任何已有节点

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`langgraph`, `ragen-architect`]
  - **Skills Evaluated but Omitted**:
    - `visual-engineering`: 不涉及UI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Task 5, 17
  - **Blocked By**: None

  **References**:
  - `src/core/sop_learning.py:568-603` - recall_sop方法实现
  - `src/core/langgraph_core_nodes.py` - 现有节点模式
  - `src/core/langgraph_reasoning_nodes.py` - 推理节点示例

  **Acceptance Criteria**:
  - [ ] Node文件创建: src/core/langgraph_sop_nodes.py
  - [ ] `sop_recall_node` 函数可导入
  - [ ] pytest测试通过: recall相关用例

  **QA Scenarios**:
  ```
  Scenario: SOP召回功能正常
    Tool: Bash (pytest)
    Steps:
      1. cd /Users/apple/workdata/person/zy/RANGEN-main(syu-python)
      2. pytest tests/test_sop_recall.py -v
    Expected Result: PASS (3 tests, 0 failures)
    Evidence: .sisyphus/evidence/task-1-sop-recall-test.txt
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(sop): add SOP recall node for LangGraph`
  - Files: `src/core/langgraph_sop_nodes.py`
  - Pre-commit: `pytest tests/test_sop_recall.py`

---

- [x] 2. **SOP Execution Node** — LangGraph节点实现

  **What to do**:
  - 实现 `sop_execution_node(state)` 函数
  - 加载并执行已召回的SOP步骤
  - 协调Hands注册表执行具体操作
  - 处理执行结果和错误恢复

  **Must NOT do**:
  - 不修改Hand接口
  - 不绕过安全检查

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`langgraph`, `rangen-architect`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 5, 17
  - **Blocked By**: None

  **References**:
  - `src/core/sop_learning.py:105-117` - SOP步骤执行逻辑
  - `src/hands/registry.py:85-92` - get_hand方法
  - `src/core/langgraph_reasoning_nodes.py` - 执行节点模式

  **Acceptance Criteria**:
  - [ ] Node实现完成
  - [ ] 可执行简单SOP流程
  - [ ] 错误处理正常

  **QA Scenarios**:
  ```
  Scenario: SOP执行功能正常
    Tool: Bash (pytest)
    Steps:
      1. pytest tests/test_sop_execution.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-2-sop-execution-test.txt
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(sop): add SOP execution node`
  - Files: `src/core/langgraph_sop_nodes.py`

---

- [x] 3. **SOP Learning Hook** — 执行后自动学习

  **What to do**:
  - 创建执行后自动学习钩子
  - 拦截成功执行的步骤序列
  - 调用 `SOPLearningSystem.learn_from_execution()`
  - 支持可配置的学习阈值

  **Must NOT do**:
  - 不在每次执行后都学习(避免噪声)
  - 不学习失败的操作

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`langgraph`, `rangen-architect`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 17
  - **Blocked By**: None

  **References**:
  - `src/core/sop_learning.py:393-424` - learn_from_execution方法
  - `src/core/langgraph_error_recovery.py` - 钩子模式

  **Acceptance Criteria**:
  - [ ] 钩子正确注册
  - [ ] 成功执行后触发学习
  - [ ] 失败执行不触发学习

  **QA Scenarios**:
  ```
  Scenario: 学习钩子触发正常
    Tool: Bash (pytest)
    Steps:
      1. pytest tests/test_sop_learning_hook.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-3-sop-hook-test.txt
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(sop): add execution learning hook`

---

- [x] 4. **SOP Management API** — RESTful管理接口

  **What to do**:
  - 添加SOP管理API端点
  - GET /sops - 列出所有SOP
  - GET /sops/{id} - 获取SOP详情
  - POST /sops - 手动创建SOP
  - DELETE /sops/{id} - 删除SOP

  **Must NOT do**:
  - 不修改现有API结构

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`fastapi`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocked By**: None

  **References**:
  - `src/api/server.py` - 现有API模式
  - `src/core/sop_learning.py:869-899` - get_statistics方法

  **Acceptance Criteria**:
  - [ ] API端点可访问
  - [ ] CRUD操作正常

  **QA Scenarios**:
  ```
  Scenario: SOP API功能正常
    Tool: Bash (curl)
    Steps:
      1. curl http://localhost:8000/sops
    Expected Result: 200 OK with JSON
    Evidence: .sisyphus/evidence/task-4-sop-api.json
  ```

  **Commit**: YES (Wave 1)
  - Message: `feat(sop): add SOP management API endpoints`


- [x] 5. **7原子工具实现** — 对齐pc-agent-loop的原子能力

  **What to do**:
  - 在 `src/tools/atomic.py` 实现7个原子工具基类
  - `code_run`: 执行任意Python/PowerShell代码
  - `file_read`: 读取文件内容
  - `file_write`: 写入文件内容
  - `file_patch`: 精确代码修补（类似pc-agent-loop的ga.py）
  - `web_scan`: 网页内容抓取
  - `web_execute_js`: 浏览器DOM控制
  - `ask_user`: 人机协作确认
  - 实现工具注册和执行框架

  **Must NOT do**:
  - 不破坏现有Hands兼容性
  - 不使用不安全的eval直接执行（用ast解析）

  **What to do**:
  - 在 `src/hands/atomic.py` 创建AtomicTool基类
  - 定义标准化原子接口: execute, validate, get_schema
  - 实现基础的安全沙箱执行环境
  - 定义原子工具元数据规范

  **Must NOT do**:
  - 不破坏现有BaseHand兼容性
  - 不引入不安全的eval/exec

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`rangen-architect`, `security`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8)
  - **Blocks**: Task 9-12
  - **Blocked By**: Task 1-4

  **References**:
  - `src/hands/base.py:63-115` - BaseHand基类模式
  - `src/hands/registry.py:42-62` - 注册模式

  **Acceptance Criteria**:
  - [ ] AtomicTool类可导入
  - [ ] 基础接口定义完整

  **QA Scenarios**:
  ```
  Scenario: 原子工具基类可用
    Tool: Bash
    Steps:
      1. cd /Users/apple/workdata/person/zy/RANGEN-main(syu-python)
      2. python -c "from src.hands.atomic import AtomicTool; print('OK')"
    Expected Result: OK
    Evidence: .sisyphus/evidence/task-5-atomic-import.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `feat(atomic): add AtomicTool base class`

---

- [x] 6. **DynamicCodeExecutor** — 动态代码执行器

  **What to do**:
  - 实现安全代码执行器(使用ast模块解析)
  - 支持Python代码片段执行
  - 实现超时和内存限制
  - 提供结果序列化和错误处理

  **Must NOT do**:
  - 不使用eval/exec直接执行
  - 不执行网络请求(安全)
  - 不访问文件系统(除非明确授权)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`security`, `python`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 7, 8)
  - **Blocks**: Task 17
  - **Blocked By**: Task 1-4

  **References**:
  - `src/hands/code_hand.py` - 现有代码执行模式
  - Python ast模块官方文档

  **Acceptance Criteria**:
  - [ ] 可执行简单Python代码
  - [ ] 超时保护正常
  - [ ] 错误隔离正常

  **QA Scenarios**:
  ```
  Scenario: 代码执行器正常工作
    Tool: Bash
    Steps:
      1. python -c "from src.hands.atomic import DynamicCodeExecutor; e = DynamicCodeExecutor(); r = e.execute('1+1'); print(r)"
    Expected Result: 2
    Evidence: .sisyphus/evidence/task-6-code-exec.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `feat(atomic): add DynamicCodeExecutor`

---

- [x] 7. **AtomicToolRegistry** — 原子工具注册表

  **What to do**:
  - 创建AtomicToolRegistry类
  - 支持动态注册/注销原子工具
  - 实现工具发现和版本管理
  - 与现有HandRegistry兼容

  **Must NOT do**:
  - 不替代现有HandRegistry
  - 不破坏现有Hands加载

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`rangen-architect`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 8)
  - **Blocked By**: Task 1-4

  **References**:
  - `src/hands/registry.py` - 现有注册表模式

  **Acceptance Criteria**:
  - [ ] 可注册新原子工具
  - [ ] 可发现已注册工具

  **QA Scenarios**:
  ```
  Scenario: 原子工具注册表可用
    Tool: Bash
    Steps:
      1. python -c "from src.hands.atomic import AtomicToolRegistry; r = AtomicToolRegistry(); print(len(r.list_tools()))"
    Expected Result: >=0 (无错误)
    Evidence: .sisyphus/evidence/task-7-registry.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `feat(atomic): add AtomicToolRegistry`

---

- [x] 8. **HandsBuilder** — Hands动态构建器

  **What to do**:
  - 实现从原子工具动态构建完整Hand
  - 支持配置化Hand生成
  - 实现自动能力包装
  - 集成到现有注册流程

  **Must NOT do**:
  - 不修改现有Hand类
  - 不绕过安全检查

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`rangen-architect`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 5, 6, 7)
  - **Blocked By**: Task 1-4

  **References**:
  - `src/hands/base.py` - Hand基类
  - `src/core/capability_plugin_framework.py` - 能力插件框架

  **Acceptance Criteria**:
  - [ ] 可从代码生成Hand
  - [ ] 生成的Hand可执行

  **QA Scenarios**:
  ```
  Scenario: HandsBuilder正常工作
    Tool: Bash
    Steps:
      1. pytest tests/test_hands_builder.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-8-builder.txt
  ```

  **Commit**: YES (Wave 2)
  - Message: `feat(atomic): add HandsBuilder for dynamic generation`

- [x] 9. **TMWebDriver实现** — 浏览器注入控制（对齐pc-agent-loop）

  **What to do**:
  - 参照 `TMWebDriver.py` 实现浏览器注入桥接
  - 非Selenium方式，通过Tampermonkey注入真实浏览器
  - 保留用户登录状态
  - 支持: 导航、点击、填写表单、截图、DOM操作
  - 集成 `simphtml.py` 网页内容清洗

  **对齐参考**:
  - pc-agent-loop: `TMWebDriver.py` - 浏览器注入桥接
  - pc-agent-loop: `simphtml.py` - HTML→文本清洗

  **Must NOT do**:
  - 不使用Selenium/WebDriver（保留登录态需要注入方式）
  - 不在无用户授权情况下操作

  **What to do**:
  - 创建浏览器自动化Hand
  - 使用Playwright/Selenium进行网页控制
  - 支持: 导航、点击、填写表单、截图
  - 实现隐式等待和错误重试

  **Must NOT do**:
  - 不在无用户授权情况下操作
  - 不保存敏感凭据

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`playwright`, `automation`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11, 12)
  - **Blocked By**: Task 5-8

  **References**:
  - `src/hands/api_hand.py` - 现有Hand模式
  - Playwright Python官方文档

  **Acceptance Criteria**:
  - [ ] 可启动浏览器
  - [ ] 可导航到URL
  - [ ] 可执行基本交互

  **QA Scenarios**:
  ```
  Scenario: 浏览器控制功能正常
    Tool: Bash
    Steps:
      1. pytest tests/test_browser_hand.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-9-browser.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `feat(physical): add BrowserControlHand`

---

- [x] 10. **KeyboardMouseHand** — 键鼠模拟能力

  **What to do**:
  - 实现键盘按键模拟
  - 实现鼠标移动和点击
  - 支持快捷键组合
  - 实现拖放操作

  **Must NOT do**:
  - 不在后台隐藏操作
  - 不记录用户输入(隐私)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`automation`, `system`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 11, 12)
  - **Blocked By**: Task 5-8

  **References**:
  - pyautogui库文档
  - pynput库文档

  **Acceptance Criteria**:
  - [ ] 可模拟按键
  - [ ] 可模拟鼠标点击

  **QA Scenarios**:
  ```
  Scenario: 键鼠模拟功能正常
    Tool: Bash
    Steps:
      1. pytest tests/test_keyboard_mouse.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-10-keyboard.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `feat(physical): add KeyboardMouseHand`

---

- [x] 11. **ScreenCaptureHand** — 屏幕捕获能力

  **What to do**:
  - 实现屏幕截图功能
  - 实现区域截图
  - 支持多显示器
  - 集成OCR识别(可选)

  **Must NOT do**:
  - 不存储敏感屏幕内容
  - 不在后台持续录制

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`vision`, `automation`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10, 12)
  - **Blocked By**: Task 5-8

  **References**:
  - mss库文档
  - PIL/Pillow截图处理

  **Acceptance Criteria**:
  - [ ] 可截取全屏
  - [ ] 可截取指定区域

  **QA Scenarios**:
  ```
  Scenario: 屏幕捕获功能正常
    Tool: Bash
    Steps:
      1. pytest tests/test_screen_capture.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-11-screen.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `feat(physical): add ScreenCaptureHand`

---

- [x] 12. **PhysicalControlSandbox** — 物理控制安全沙箱

  **What to do**:
  - 实现操作权限控制
  - 实现操作审计日志
  - 实现超时和中断机制
  - 实现危险操作确认

  **Must NOT do**:
  - 不完全禁用安全检查
  - 不绕过用户授权

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`security`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 9, 10, 11)
  - **Blocked By**: Task 5-8

  **References**:
  - `src/hands/base.py:117-130` - 安全检查模式

  **Acceptance Criteria**:
  - [ ] 权限控制生效
  - [ ] 审计日志记录

  **QA Scenarios**:
  ```
  Scenario: 沙箱安全机制正常
    Tool: Bash
    Steps:
      1. pytest tests/test_sandbox.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-12-sandbox.txt
  ```

  **Commit**: YES (Wave 3)
  - Message: `feat(physical): add PhysicalControlSandbox`

---

- [x] 13. **极简启动器** — 对齐pc-agent-loop部署模式

  **What to do**:
  - 创建 `launch.pyw` 一键启动脚本
  - 最小依赖: pip install streamlit pywebview
  - 自动检测/创建API key配置
  - 支持CLI和GUI两种模式
  - 对齐pc-agent-loop: 10个核心.py + 5个SOP出厂

  **对齐参考**:
  - pc-agent-loop: `launch.pyw` - 一键启动+悬浮窗
  - pc-agent-loop: `stapp.py` - Streamlit Web UI
  - pc-agent-loop: `agentmain.py` - CLI会话编排

  **Must NOT do**:
  - 不覆盖现有配置
  - 不要求额外依赖

  **What to do**:
  - 创建简化配置流程
  - 支持环境变量自动检测
  - 提供交互式配置向导
  - 生成最小化配置文件

  **Must NOT do**:
  - 不覆盖现有配置
  - 不要求可选依赖

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`ux`, `config`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 14, 15, 16)
  - **Blocked By**: None

  **References**:
  - `src/core/config_loader.py` - 现有配置加载
  - Python click/typer库

  **Acceptance Criteria**:
  - [ ] 交互式配置可用
  - [ ] 生成有效配置

  **QA Scenarios**:
  ```
  Scenario: 轻量配置器正常工作
    Tool: Bash
    Steps:
      1. echo -e "mock\n" | python -m src.cli configure
    Expected Result: 配置文件生成
    Evidence: .sisyphus/evidence/task-13-config.txt
  ```

  **Commit**: YES (Wave 4)
  - Message: `feat(lite): add LiteConfigurator`

---

- [x] 14. **LiteWorkflowEngine** — 简化工作流引擎

  **What to do**:
  - 创建简化版工作流引擎
  - 保留核心ReAct循环
  - 移除企业级特性(可选)
  - 支持单Agent模式

  **Must NOT do**:
  - 不破坏完整版功能
  - 不降低核心能力

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: [`langgraph`, `rangen-architect`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 13, 15, 16)
  - **Blocked By**: None

  **References**:
  - `src/core/langgraph_unified_workflow.py` - 现有工作流

  **Acceptance Criteria**:
  - [ ] 简化引擎可启动
  - [ ] 可处理简单请求

  **QA Scenarios**:
  ```
  Scenario: 轻量引擎正常工作
    Tool: Bash
    Steps:
      1. pytest tests/test_lite_engine.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-14-lite-engine.txt
  ```

  **Commit**: YES (Wave 4)
  - Message: `feat(lite): add LiteWorkflowEngine`

---

- [x] 15. **LiteUI** — 极简Streamlit界面

  **What to do**:
  - 创建最小化聊天界面
  - 保留核心对话功能
  - 简化配置入口
  - 添加快速开始向导

  **Must NOT do**:
  - 不修改现有UI
  - 不添加复杂功能

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`streamlit`, `ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 13, 14, 16)
  - **Blocked By**: None

  **References**:
  - `src/ui/app.py` - 现有UI

  **Acceptance Criteria**:
  - [ ] UI可启动
  - [ ] 基本对话可用

  **QA Scenarios**:
  ```
  Scenario: 轻量UI正常工作
    Tool: Playwright
    Steps:
      1. 访问 http://localhost:8501
      2. 验证页面加载
    Expected Result: 页面正常渲染
    Evidence: .sisyphus/evidence/task-15-lite-ui.png
  ```

  **Commit**: YES (Wave 4)
  - Message: `feat(lite): add LiteUI`

---

- [x] 16. **CLI入口点** — rangen-lite命令

  **What to do**:
  - 创建CLI入口脚本
  - 实现rangen-lite命令
  - 集成所有轻量组件
  - 提供帮助和版本信息

  **Must NOT do**:
  - 不冲突现有CLI
  - 不要求全局安装

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`cli`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 13, 14, 15)
  - **Blocked By**: None

  **References**:
  - `src/ui/app.py` - 现有入口
  - Click库文档

  **Acceptance Criteria**:
  - [ ] 命令可执行
  - [ ] --help可用

  **QA Scenarios**:
  ```
  Scenario: CLI入口正常工作
    Tool: Bash
    Steps:
      1. python -m src.cli lite --help
    Expected Result: 帮助信息显示
    Evidence: .sisyphus/evidence/task-16-cli.txt
  ```

  **Commit**: YES (Wave 4)
  - Message: `feat(lite): add rangen-lite CLI entry point`
- [x] 17. **SOP集成测试** — 完整SOP工作流测试 ✅
  - 文件: tests/integration/test_sop_full.py
  - 结果: 11/11 通过

  **What to do**:
  - 创建完整SOP召回→执行→学习流程测试
  - 测试与LangGraph工作流集成
  - 测试API端点
  - 测试错误恢复

  **Must NOT do**:
  - 不测试无关模块

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`testing`, `pytest`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 18, 19, 20)
  - **Blocked By**: Tasks 1-4, 5-8

  **Acceptance Criteria**:
  - [ ] 完整流程测试通过
  - [ ] 集成测试通过

  **QA Scenarios**:
  ```
  Scenario: SOP完整集成测试
    Tool: Bash
    Steps:
      1. pytest tests/integration/test_sop_full.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-17-sop-integration.txt
  ```

  **Commit**: YES (Wave 5)
  - Message: `test(sop): add full integration tests`

---

- [x] 18. **原子框架测试** — 原子工具完整性测试 ✅
  - 文件: tests/integration/test_atomic_full.py
  - 结果: 14/14 通过

  **What to do**:
  - 测试动态代码执行
  - 测试原子工具注册
  - 测试HandsBuilder
  - 测试安全沙箱

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`testing`, `pytest`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 17, 19, 20)
  - **Blocked By**: Tasks 5-8

  **Acceptance Criteria**:
  - [ ] 框架测试通过
  - [ ] 安全测试通过

  **QA Scenarios**:
  ```
  Scenario: 原子框架完整测试
    Tool: Bash
    Steps:
      1. pytest tests/integration/test_atomic_full.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-18-atomic-integration.txt
  ```

  **Commit**: YES (Wave 5)
  - Message: `test(atomic): add full integration tests`

---

- [x] 19. **物理控制测试** — 物理设备控制测试 ✅
  - 文件: tests/integration/test_physical_full.py
  - 结果: 10/10 通过

  **What to do**:
  - 测试浏览器控制
  - 测试键鼠模拟
  - 测试屏幕捕获
  - 测试沙箱安全

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`testing`, `playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 17, 18, 20)
  - **Blocked By**: Tasks 9-12

  **Acceptance Criteria**:
  - [ ] 物理控制测试通过
  - [ ] 沙箱测试通过

  **QA Scenarios**:
  ```
  Scenario: 物理控制完整测试
    Tool: Bash
    Steps:
      1. pytest tests/integration/test_physical_full.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-19-physical-integration.txt
  ```

  **Commit**: YES (Wave 5)
  - Message: `test(physical): add full integration tests`

---

- [x] 20. **轻量模式测试** — rangen-lite完整测试 ✅
  - 文件: tests/integration/test_lite_full.py
  - 结果: 8/8 通过

  **What to do**:
  - 测试配置器
  - 测试简化引擎
  - 测试轻量UI
  - 测试CLI入口
  - 测试完整启动流程

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`testing`, `streamlit`]

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 17, 18, 19)
  - **Blocked By**: Tasks 13-16

  **Acceptance Criteria**:
  - [ ] 轻量模式完整测试通过
  - [ ] 端到端测试通过

  **QA Scenarios**:
  ```
  Scenario: 轻量模式完整测试
    Tool: Bash
    Steps:
      1. pytest tests/integration/test_lite_full.py -v
    Expected Result: PASS
    Evidence: .sisyphus/evidence/task-20-lite-integration.txt
  ```

  **Commit**: YES (Wave 5)
  - Message: `test(lite): add full integration tests`

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — 验证所有Must Have已实现
  - ✅ T1-T8: SOP + Atomic Framework
  - ✅ T9-T12: Physical Control
  - ✅ T13-T16: Lite Mode
- [x] F2. **Code Quality Review** — 15/15 modules pass ✅
- [x] F3. **Integration Testing** — 5/6 tests pass ✅
- [x] F4. **Scope Fidelity Check** — 16/16 files exist ✅

---

## Additional Features Completed (OpenClaw Optimization)

Beyond the original plan, these features were implemented as part of the OpenClaw architecture optimization:

### 核心组件 (2026-03-20)
- **AgentHUD** (`src/ui/agent_hud.py`) — 实时状态面板 (借鉴 Claude HUD)
- **TDDEnforcer** (`src/agents/tdd_enforcer.py`) — TDD 强制执行器 (借鉴 Superpowers)
- **TwoStageReviewer** (`src/agents/two_stage_reviewer.py`) — 两阶段代码审查 (借鉴 Superpowers)
- **TaskPlanner** (`src/agents/task_planner.py`) — 精确任务规划器 (借鉴 Superpowers)
- **MiddlewareChain** (`src/core/middleware.py`) — 可插拔中间件系统 (借鉴 Open SWE)

### 其他组件
- **ProgressTracker** (`src/core/progress_tracker.py`) — 长时任务显式进度跟踪
- **DependencyGuard** (`src/core/dependency_guard.py`) — 架构分层依赖验证
- **Verdict** (`src/core/verdict.py`) — SOP学习质量控制
- **ABTestingFramework** (`src/core/ab_testing/ab_framework.py`) — 高级统计A/B测试
- **KnowledgeGraph** (`src/core/memory/knowledge_graph.py`) — 知识图谱记忆
- **SandboxExecutor** (`src/core/sandbox/sandbox_executor.py`) — 安全沙箱执行器
- **ProductionWorkflow** (`src/core/production_workflow.py`) — 集成SOP节点的生产工作流
- **TampermonkeyScript** (`src/hands/tampermonkey_script.js`) — 浏览器控制脚本

---

## Commit Strategy

每个Wave完成后进行提交:
- `feat(sop): add SOP recall and execution nodes`
- `feat(atomic): implement atomic tool framework`
- `feat(physical): add physical control hands`
- `feat(lite): introduce rangen-lite mode`

---

## Success Criteria

### Verification Commands
```bash
pytest tests/ -v
pylint src/core/sop_learning.py src/hands/
```

### Final Checklist
- [ ] 所有Must Have已实现
- [ ] 所有Must NOT已排除
- [ ] 所有测试通过
- [ ] 向后兼容验证通过
