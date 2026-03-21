# 如何访问诊断端点查看执行记录

## 方法1: 使用 curl 命令

### 1. 获取所有执行记录

```bash
curl http://localhost:8080/api/executions | jq
```

### 2. 诊断特定的执行记录

从上面的结果中找到 `execution_id`，然后运行：

```bash
# 替换 {execution_id} 为实际的执行ID
curl http://localhost:8080/api/diagnose/execution/{execution_id} | jq
```

例如，从之前的日志中看到的 execution_id 是 `44db79ac-c791-4f59-aaec-e52f83ece7ff`：

```bash
curl http://localhost:8080/api/diagnose/execution/44db79ac-c791-4f59-aaec-e52f83ece7ff | jq
```

## 方法2: 在浏览器中访问

### 1. 获取所有执行记录

打开浏览器，访问：
```
http://localhost:8080/api/executions
```

### 2. 诊断特定的执行记录

访问：
```
http://localhost:8080/api/diagnose/execution/{execution_id}
```

例如：
```
http://localhost:8080/api/diagnose/execution/44db79ac-c791-4f59-aaec-e52f83ece7ff
```

## 方法3: 使用 Python 脚本

如果服务器正在运行，可以使用提供的脚本：

```bash
python3 scripts/check_execution_diagnosis.py
```

## 诊断端点返回的信息

诊断端点会返回以下信息：

1. **执行基本信息**
   - execution_id
   - status

2. **final_result 信息**
   - 是否存在
   - 是否有答案
   - 答案内容（前100字符）
   - 答案长度
   - 是否成功
   - 是否有错误

3. **节点信息**
   - 节点总数
   - 已完成节点数
   - 节点中是否有答案
   - 包含答案的节点列表

4. **state_history 信息**
   - 历史记录数
   - 历史中是否有答案
   - 包含答案的历史记录

5. **问题列表**
   - 发现的所有问题

6. **建议**
   - 修复建议

## 示例输出

```json
{
  "execution_id": "44db79ac-c791-4f59-aaec-e52f83ece7ff",
  "status": "completed",
  "has_final_result": false,
  "final_result_info": {
    "exists": false,
    "has_answer": false
  },
  "nodes_info": {
    "count": 0,
    "completed_count": 0,
    "has_answer_in_nodes": false
  },
  "issues": [
    "执行记录中缺少 final_result"
  ],
  "recommendations": [
    "执行记录中缺少 final_result，检查 _execute_unified_workflow 方法是否正确保存"
  ]
}
```

