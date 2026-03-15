# ReAct模式改进计划

**创建时间**: 2026-03-03  
**基于参考**: ReAct模式 vs Plan-and-Solve模式分析

---

## 背景

当前ReAct实现已有:
- max_iterations限制 (防止死循环)
- 动态迭代次数 (根据查询复杂度调整)

需要改进:
- 动态重规划机制
- 快慢双链路路由
- Human-in-loop确认

---

## 改进任务

### Phase 1: 动态重规划机制

- [ ] 1. 添加错误计数跟踪
- [ ] 2. 实现重试阈值配置
- [ ] 3. 创建Planner重新生成DAG的逻辑
- [ ] 4. 集成到ReAct循环中

### Phase 2: 快慢双链路

- [ ] 5. 实现查询复杂度判断
- [ ] 6. 创建路由逻辑
- [ ] 7. 简单请求→ReAct快速路径
- [ ] 8. 复杂请求→Plan模式

### Phase 3: Human-in-loop

- [ ] 9. 添加执行前确认机制
- [ ] 10. 实现暂停/继续功能
- [ ] 11. 添加超时处理

---

## 实施顺序

1. 先实现Phase 1 (动态重规划) - 最高优先级，解决死循环问题
2. 再实现Phase 2 (快慢双链路) - 优化性能
3. 最后实现Phase 3 (Human-in-loop) - 可选功能

---

## 关键文件

- `src/agents/react_agent.py` - 主要修改
- `src/core/langgraph_unified_workflow.py` - Plan模式相关
