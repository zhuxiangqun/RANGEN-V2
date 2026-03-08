# Linter 警告修复指南

## 当前状态

✅ **已完成**：
- `node_modules` 目录已创建
- Vue 3.5.24 已安装
- TypeScript 已安装
- `.volar` 目录已创建
- `vue-global.d.ts` 文件已创建
- `jsconfig.json` 已配置 `globalTypesPath`

## 剩余警告

如果 VS Code 中仍然显示 Vue 语言服务器警告，这是因为 **Vue 语言服务器需要手动重启**才能识别新配置。

## 解决步骤

### 方法1：重启 Vue 语言服务器（推荐）

1. 在 VS Code 中按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Windows/Linux)
2. 输入：`Vue: Restart Vue server`
3. 选择并执行该命令
4. 等待几秒钟让服务器重新初始化

### 方法2：重新加载窗口

1. 在 VS Code 中按 `Cmd+Shift+P` (Mac) 或 `Ctrl+Shift+P` (Windows/Linux)
2. 输入：`Developer: Reload Window`
3. 选择并执行该命令

### 方法3：完全重启 VS Code

关闭并重新打开 VS Code

## 验证修复

重启后，警告应该消失。如果仍然存在，请检查：

1. ✅ `node_modules/vue` 目录是否存在
2. ✅ `node_modules/typescript` 目录是否存在
3. ✅ `.volar/vue-global.d.ts` 文件是否存在
4. ✅ `jsconfig.json` 中是否包含 `globalTypesPath` 配置

## 重要说明

- ⚠️ **这个警告不影响代码运行**，只是开发体验的问题
- ✅ 所有必要的配置和文件都已就绪
- ✅ 重启 Vue 语言服务器后，警告应该会消失
- ✅ 重启后可以获得完整的开发体验（代码补全、类型检查等）

## 如果问题仍然存在

如果重启后警告仍然存在，可能是 VS Code 的 Vue 扩展问题。请：

1. 确保已安装 **Volar** 扩展（Vue 官方推荐）
2. 禁用其他 Vue 相关扩展（如 Vetur），避免冲突
3. 检查 VS Code 输出面板中的 Vue 语言服务器日志

