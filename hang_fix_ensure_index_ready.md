# 卡住问题修复 - ensure_index_ready

## 问题定位

从终端输出看，系统在知识库管理系统初始化完成后卡住。问题可能出在：

1. **`ensure_index_ready()` 调用卡住**
   - 位置：`_initialize_traditional_agents()` 中
   - 原因：`ensure_index_ready()` 可能调用 `_async_initialize()`，而这个方法可能会阻塞

## 已实施的修复

### 1. 添加超时保护
- `ensure_index_ready()` 调用：30秒超时
- 如果超时，记录警告但继续执行

### 2. 添加初始化阶段日志
- 记录每个初始化阶段的开始和完成
- 帮助定位卡在哪个阶段

## 代码修改

```python
# 在 _initialize_traditional_agents() 中
if hasattr(service.faiss_service, 'ensure_index_ready'):
    try:
        result = await asyncio.wait_for(
            service.faiss_service.ensure_index_ready(),
            timeout=30.0  # 30秒超时
        )
        if result:
            logger.info("✅ 统一FAISS服务初始化完成")
        else:
            logger.warning("⚠️ 统一FAISS服务初始化失败，但继续执行")
    except asyncio.TimeoutError:
        logger.warning("⚠️ 统一FAISS服务初始化超时（30秒），但继续执行")
```

## 下一步

1. **重新运行测试**，查看新的诊断日志
2. **如果仍然卡住**，检查：
   - 是否卡在其他初始化阶段
   - 是否有其他阻塞操作
   - 日志是否正常刷新

## 建议

如果问题持续，可以考虑：
1. 暂时跳过 `ensure_index_ready()` 调用（知识库管理系统已经初始化完成）
2. 将 `ensure_index_ready()` 改为非阻塞检查
3. 使用后台任务异步初始化，不阻塞主流程

