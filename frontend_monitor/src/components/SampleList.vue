<template>
  <div class="sample-list">
    <el-table
      :data="displayedSamples"
      stripe
      border
      style="width: 100%"
      :row-class-name="getRowClassName"
    >
      <el-table-column type="index" label="序号" width="80" align="center">
        <template #default="{ $index }">
          <el-button
            type="primary"
            link
            class="sample-id-button"
            @click.stop="handleSampleClick(displayedSamples[$index].id)"
          >
            {{ displayedSamples[$index].id }}
          </el-button>
        </template>
      </el-table-column>
      
      <el-table-column prop="query" label="问题" min-width="300" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="query-cell">{{ formatQuery(row.query) }}</div>
        </template>
      </el-table-column>
      
      <el-table-column prop="expected_answer" label="期望答案" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="answer-cell">{{ row.expected_answer || '暂无' }}</div>
        </template>
      </el-table-column>
      
      <el-table-column prop="answer" label="系统答案" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="answer-cell" :class="{ 'answer-match': row.answer === row.expected_answer }">
            {{ row.answer || (row.is_running ? '处理中...' : '暂无') }}
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="default">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="duration" label="耗时" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.duration">{{ formatDuration(row.duration) }}</span>
          <span v-else-if="row.is_running" class="processing">处理中</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="confidence" label="置信度" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.confidence || (row.answer && row.expected_answer)">
            {{ getDisplayConfidence(row) }}%
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  samples: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['sample-click'])

// 显示的样本列表（按ID排序）
const displayedSamples = computed(() => {
  if (!props.samples || !Array.isArray(props.samples)) {
    return []
  }
  return [...props.samples].sort((a, b) => (a.id || 0) - (b.id || 0))
})

// 获取状态类型
const getStatusType = (status) => {
  if (!status) return 'info'
  const statusMap = {
    'running': 'warning',
    'completed': 'success',
    'error': 'danger',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  if (!status) return '未知'
  const statusMap = {
    'running': '运行中',
    'completed': '已完成',
    'error': '错误',
    'pending': '等待中'
  }
  return statusMap[status] || '未知'
}

// 格式化耗时
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const secs = (seconds % 60).toFixed(1)
    return `${minutes}分${secs}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分`
  }
}

// 获取行样式类名
const getRowClassName = ({ row }) => {
  if (row.status === 'error') {
    return 'error-row'
  } else if (row.is_running) {
    return 'running-row'
  } else if (row.completed) {
    return 'completed-row'
  }
  return ''
}

// 处理样本点击（仅通过序号按钮触发）
const handleSampleClick = (sampleId) => {
  emit('sample-click', sampleId)
}

// 🚀 新增：获取显示的置信度（如果答案完全匹配期望答案，显示100%）
const getDisplayConfidence = (row) => {
  // 如果答案和期望答案完全匹配，返回100%
  if (row.answer && row.expected_answer) {
    const answerNormalized = String(row.answer).trim().toLowerCase()
    const expectedNormalized = String(row.expected_answer).trim().toLowerCase()
    
    if (answerNormalized === expectedNormalized) {
      return '100.0'
    }
  }
  
  // 否则返回原始置信度
  if (row.confidence !== null && row.confidence !== undefined) {
    return (row.confidence * 100).toFixed(1)
  }
  
  return '-'
}

// 格式化查询内容，提取Prompt字段的值
const formatQuery = (query) => {
  if (!query) return '暂无'
  
  let queryStr = String(query).trim()
  
  // 🚀 改进：更强大的Prompt字段提取逻辑
  // 方法1: 尝试解析为JSON对象（处理单引号和双引号混合的情况）
  if (queryStr.startsWith('{') || queryStr.startsWith("'")) {
    try {
      // 先尝试直接解析（如果是标准JSON）
      let parsed = null
      try {
        parsed = JSON.parse(queryStr)
      } catch (e1) {
        // 如果不是标准JSON，尝试将单引号替换为双引号
        try {
          // 处理Python字典格式：将单引号替换为双引号
          let jsonStr = queryStr
            .replace(/'/g, '"')  // 先全部替换
            .replace(/None/g, 'null')
            .replace(/True/g, 'true')
            .replace(/False/g, 'false')
          
          parsed = JSON.parse(jsonStr)
        } catch (e2) {
          // JSON解析失败，继续尝试正则表达式提取
        }
      }
      
      if (parsed && parsed.Prompt) {
        return String(parsed.Prompt).trim()
      }
    } catch (e) {
      // 解析失败，继续尝试其他方法
    }
    
    // 方法2: 使用正则表达式提取Prompt字段（处理各种引号组合和多行情况）
    // 🚀 修复：改进正则表达式，支持多行和长文本
    
    // 尝试匹配 'Prompt': '...' 格式（单引号键，单引号值，支持多行）
    // 使用非贪婪匹配，匹配到下一个 ', ' 或 '}' 或字符串结束
    let promptMatch = queryStr.match(/'Prompt'\s*[：:]\s*'((?:[^']|'(?!\s*[,}]))*)'/)
    if (promptMatch && promptMatch[1]) {
      return promptMatch[1].trim()
    }
    
    // 尝试匹配 "Prompt": "..." 格式（双引号键，双引号值，支持多行）
    promptMatch = queryStr.match(/"Prompt"\s*[：:]\s*"((?:[^"]|"(?!\s*[,}]))*)"/)
    if (promptMatch && promptMatch[1]) {
      return promptMatch[1].trim()
    }
    
    // 尝试匹配 'Prompt': "..." 格式（单引号键，双引号值）
    promptMatch = queryStr.match(/'Prompt'\s*[：:]\s*"((?:[^"]|"(?!\s*[,}]))*)"/)
    if (promptMatch && promptMatch[1]) {
      return promptMatch[1].trim()
    }
    
    // 尝试匹配 "Prompt": '...' 格式（双引号键，单引号值）
    promptMatch = queryStr.match(/"Prompt"\s*[：:]\s*'((?:[^']|'(?!\s*[,}]))*)'/)
    if (promptMatch && promptMatch[1]) {
      return promptMatch[1].trim()
    }
    
    // 方法3: 🚀 修复：更智能的提取 - 处理Prompt值被截断的情况
    // 查找 'Prompt': '...' 或 "Prompt": "..." 格式，支持被截断的字符串
    if (queryStr.includes("'Prompt'") || queryStr.includes('"Prompt"')) {
      // 查找Prompt关键字的位置
      const promptKeyPattern = /['"]Prompt['"]\s*[：:]\s*/
      const keyMatch = queryStr.match(promptKeyPattern)
      
      if (keyMatch) {
        const afterKey = queryStr.substring(keyMatch.index + keyMatch[0].length)
        
        // 检查第一个字符是否是引号
        if (afterKey.startsWith("'") || afterKey.startsWith('"')) {
          const quoteChar = afterKey[0]
          const valueStart = 1
          
          // 查找结束引号的位置（后面跟着 ', ' 或 '}' 或字符串结束）
          let endPos = -1
          
          // 尝试找到结束引号（后面跟着 ', ' 或 '}'）
          const endPattern1 = new RegExp(`${quoteChar}\\s*,\\s*['"]`, 'g')
          const endPattern2 = new RegExp(`${quoteChar}\\s*\\}`, 'g')
          
          let match1 = endPattern1.exec(afterKey)
          let match2 = endPattern2.exec(afterKey)
          
          if (match1 && match1.index > 0) {
            endPos = match1.index
          }
          if (match2 && match2.index > 0) {
            if (endPos < 0 || match2.index < endPos) {
              endPos = match2.index
            }
          }
          
          // 如果找到了结束位置，提取值
          if (endPos > valueStart) {
            const promptValue = afterKey.substring(valueStart, endPos).trim()
            if (promptValue) {
              return promptValue
            }
          } else {
            // 如果没有找到结束引号，说明被截断了，提取到字符串结束
            const promptValue = afterKey.substring(valueStart).trim()
            if (promptValue) {
              return promptValue
            }
          }
        }
      }
    }
    
    // 方法4: 🚀 修复：更宽松的匹配 - 直接查找 Prompt 关键字后的内容
    if (queryStr.includes('Prompt')) {
      const promptIndex = queryStr.indexOf('Prompt')
      const afterPrompt = queryStr.substring(promptIndex + 6) // 'Prompt' 的长度
      
      // 查找冒号
      const colonIndex = afterPrompt.indexOf(':')
      if (colonIndex >= 0) {
        const afterColon = afterPrompt.substring(colonIndex + 1).trim()
        
        // 检查是否以引号开始
        if (afterColon.startsWith("'") || afterColon.startsWith('"')) {
          const quoteChar = afterColon[0]
          const valueStart = 1
          
          // 查找结束引号（后面跟着 ', ' 或 '}'）
          let endPos = afterColon.length
          const nextComma = afterColon.indexOf(`${quoteChar}, `, valueStart)
          const nextBrace = afterColon.indexOf(`${quoteChar}}`, valueStart)
          
          if (nextComma > 0) endPos = Math.min(endPos, nextComma)
          if (nextBrace > 0) endPos = Math.min(endPos, nextBrace)
          
          // 提取Prompt值（如果没有找到结束引号，提取到字符串结束）
          const extracted = afterColon.substring(valueStart, endPos).trim()
          if (extracted) {
            return extracted
          }
        }
      }
    }
  }
  
  // 如果都不匹配，检查是否已经是纯文本（不包含字典格式）
  // 如果包含字典格式的标记但没有成功提取，尝试清理后返回
  if (queryStr.includes('Prompt') && (queryStr.includes('{') || queryStr.includes("'"))) {
    // 移除常见的标记
    let cleaned = queryStr
      .replace(/样本ID=\d+[，,]?\s*/g, '')
      .replace(/RANGEN查询处理流程开始[，,]?\s*/g, '')
      .trim()
    
    // 如果清理后仍然很长，可能是包含完整字典，返回提示
    if (cleaned.length > 200) {
      // 尝试提取第一个句子或前200字符
      const firstSentence = cleaned.match(/^[^。！？\n]+[。！？\n]?/)
      if (firstSentence && firstSentence[0].length < 200) {
        return firstSentence[0].trim()
      }
      return cleaned.substring(0, 200) + '...'
    }
    
    return cleaned
  }
  
  // 普通文本，直接返回（限制长度）
  if (queryStr.length > 200) {
    return queryStr.substring(0, 200) + '...'
  }
  
  return queryStr
}
</script>

<style scoped>
.sample-list {
  padding: 20px;
}

.query-cell,
.answer-cell {
  word-break: break-word;
  word-wrap: break-word;
  white-space: normal;
  line-height: 1.5;
  max-width: 100%;
}

.answer-cell.answer-match {
  color: #67c23a;
  font-weight: 500;
}

.processing {
  color: #e6a23c;
  font-style: italic;
}

:deep(.el-table .error-row) {
  background-color: #fef0f0;
}

:deep(.el-table .running-row) {
  background-color: #fdf6ec;
}

:deep(.el-table .completed-row) {
  background-color: #f0f9ff;
}

/* 🚀 改进：参考 fogsight 的动画设计，添加更流畅的表格行动画 */

:deep(.el-table .el-table__row) {
  /* 🚀 修复：移除 cursor: pointer，因为只有序号按钮可点击 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInRow 0.4s ease-out;
  animation-fill-mode: both;
}

/* 行出现动画（错开时间） */
:deep(.el-table .el-table__row:nth-child(1)) {
  animation-delay: 0.05s;
}

:deep(.el-table .el-table__row:nth-child(2)) {
  animation-delay: 0.1s;
}

:deep(.el-table .el-table__row:nth-child(3)) {
  animation-delay: 0.15s;
}

:deep(.el-table .el-table__row:nth-child(4)) {
  animation-delay: 0.2s;
}

:deep(.el-table .el-table__row:nth-child(n+5)) {
  animation-delay: 0.25s;
}

@keyframes fadeInRow {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
  /* 🚀 修复：移除行的hover变换效果，因为行不再可点击 */
}

/* 状态行颜色过渡动画 */
:deep(.el-table .error-row) {
  animation: errorRowPulse 2s ease-in-out infinite;
}

@keyframes errorRowPulse {
  0%, 100% {
    background-color: #fef0f0;
  }
  50% {
    background-color: #fde2e2;
  }
}

:deep(.el-table .running-row) {
  animation: runningRowPulse 2s ease-in-out infinite;
}

@keyframes runningRowPulse {
  0%, 100% {
    background-color: #fdf6ec;
  }
  50% {
    background-color: #faecd8;
  }
}

:deep(.el-table .completed-row) {
  transition: background-color 0.5s ease;
}

/* 🚀 改进：序号按钮样式，使其更明显可点击 */
.sample-id-button {
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sample-id-button:hover {
  transform: scale(1.1);
  text-decoration: underline;
}
</style>

