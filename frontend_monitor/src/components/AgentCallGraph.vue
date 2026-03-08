<template>
  <div class="agent-call-graph">
    <el-card v-if="!props.agentCalls || !Array.isArray(props.agentCalls) || props.agentCalls.length === 0" class="empty-state">
      <el-empty description="暂无智能体调用数据，请先运行核心系统" />
    </el-card>
    
    <div v-else class="graph-container">
      <div class="graph-controls">
        <div class="controls-left">
          <el-button-group>
            <el-button @click="layoutType = 'flowchart'" :type="layoutType === 'flowchart' ? 'primary' : ''">
              📊 流程图
            </el-button>
            <el-button @click="layoutType = 'hierarchical'" :type="layoutType === 'hierarchical' ? 'primary' : ''">
              🔗 层次图
            </el-button>
            <el-button @click="layoutType = 'force'" :type="layoutType === 'force' ? 'primary' : ''">
              🌐 力导向图
            </el-button>
          </el-button-group>
          <el-button @click="resetView">重置视图</el-button>
        </div>
        <div class="controls-right">
          <el-input
            v-model="sampleSelector"
            placeholder="选择样本 (如: 1, 1-5, 1,3,5)"
            clearable
            style="width: 250px; margin-right: 12px;"
            @input="handleSampleSelectorChange"
            @clear="handleSampleSelectorClear"
          />
          <el-tag type="info">共 {{ filteredAgentCalls.length }} 条调用记录</el-tag>
        </div>
      </div>
      
      <div ref="chartContainer" class="chart-container"></div>
      
      <el-card class="call-list">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>调用详情 (共 {{ filteredAgentCalls.length }} 条)</span>
            <el-tag v-if="displayedSampleIds.length > 0" type="info" size="small">
              当前显示样本: {{ displayedSampleIds.join(', ') }}
            </el-tag>
          </div>
        </template>
        <el-table 
          :data="filteredAgentCalls" 
          stripe
          style="width: 100%"
          :max-height="400"
        >
          <el-table-column prop="sample_id" label="样本ID" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="primary">{{ row.sample_id || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="from" label="调用方" width="120" show-overflow-tooltip />
          <el-table-column prop="to" label="被调用方" width="150" show-overflow-tooltip />
          <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ getAgentDescription(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.duration !== null && row.duration !== undefined && row.duration > 0">
                {{ formatDuration(row.duration) }}
              </span>
              <el-tag v-else size="small" type="info">未记录</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sample_id" label="样本ID" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="primary">{{ row.sample_id || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="success" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                {{ row.success ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="purpose" label="查询内容" min-width="300" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tooltip
                v-if="(row.query || row.purpose) && (row.query || row.purpose).length > 50"
                :content="row.query || row.purpose || '-'"
                placement="top"
                effect="dark"
              >
                <span>{{ (row.query || row.purpose || '-').substring(0, 50) }}...</span>
              </el-tooltip>
              <span v-else>{{ row.query || row.purpose || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="结果摘要" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.result || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  agentCalls: {
    type: Array,
    default: () => []
  },
  autoRefresh: {
    type: Boolean,
    default: false
  }
})


const chartContainer = ref(null)
const layoutType = ref('flowchart')  // 默认使用流程图
const sampleSelector = ref('')  // 样本选择器字符串
let chartInstance = null

// 计算可用的样本ID列表
const availableSampleIds = computed(() => {
  const sampleIds = new Set()
  props.agentCalls.forEach(call => {
    if (call.sample_id) {
      sampleIds.add(call.sample_id)
    }
  })
  return Array.from(sampleIds).sort((a, b) => a - b)
})

// 解析样本选择器字符串，支持格式如 "1", "1-5", "1,3,5", "1-3,5,7-10", "1,2"
const parseSampleSelector = (selector) => {
  if (!selector || !selector.trim()) {
    return null  // 返回 null 表示显示所有
  }
  
  const selectedIds = new Set()
  // 🚀 修复：支持中文逗号和英文逗号
  const parts = selector.split(/[,，]/).map(p => p.trim()).filter(p => p)
  
  for (const part of parts) {
    if (part.includes('-')) {
      // 范围选择，如 "1-5"
      const [start, end] = part.split('-').map(s => parseInt(s.trim()))
      if (!isNaN(start) && !isNaN(end)) {
        const min = Math.min(start, end)
        const max = Math.max(start, end)
        for (let i = min; i <= max; i++) {
          selectedIds.add(i)
        }
      }
    } else {
      // 单个样本，如 "1" 或 "1,2"
      const id = parseInt(part)
      if (!isNaN(id)) {
        selectedIds.add(id)
      }
    }
  }
  
  return selectedIds.size > 0 ? selectedIds : null
}

// 根据样本选择器过滤调用记录（默认显示第一个样本）
const filteredAgentCalls = computed(() => {
  if (props.agentCalls.length === 0) {
    return []
  }
  
  // 如果没有选择器，默认显示第一个样本的调用
  if (!sampleSelector.value || !sampleSelector.value.trim()) {
    const firstSampleId = availableSampleIds.value[0]
    if (firstSampleId) {
      return props.agentCalls.filter(call => call.sample_id === firstSampleId)
    }
    return []
  }
  
  // 解析选择器
  const selectedIds = parseSampleSelector(sampleSelector.value)
  if (!selectedIds) {
    // 解析失败，默认显示第一个样本
    const firstSampleId = availableSampleIds.value[0]
    if (firstSampleId) {
      return props.agentCalls.filter(call => call.sample_id === firstSampleId)
    }
    return []
  }
  
  // 根据选择的ID过滤
  return props.agentCalls.filter(call => {
    if (!call.sample_id) return false
    return selectedIds.has(call.sample_id)
  })
})

// 处理样本选择器变化
const handleSampleSelectorChange = () => {
  // 🚀 调试：输出样本选择器变化
  const selectedIds = parseSampleSelector(sampleSelector.value)
  const filtered = filteredAgentCalls.value
  const sampleIdsInFiltered = new Set(filtered.map(c => c.sample_id).filter(id => id !== null && id !== undefined))
  console.log(`[AgentCallGraph] 样本选择器变化: "${sampleSelector.value}"`, {
    '解析结果': selectedIds ? Array.from(selectedIds).sort((a, b) => a - b) : null,
    '过滤后调用数': filtered.length,
    '过滤后包含的样本ID': Array.from(sampleIdsInFiltered).sort((a, b) => a - b),
    '所有调用记录的样本ID': availableSampleIds.value
  })
  nextTick(() => {
    renderChart()
  })
}

// 处理样本选择器清空
const handleSampleSelectorClear = () => {
  // 清空时，默认选择第一个样本
  if (availableSampleIds.value.length > 0) {
    sampleSelector.value = String(availableSampleIds.value[0])
  }
  nextTick(() => {
    renderChart()
  })
}

// 计算当前显示的样本ID列表
const displayedSampleIds = computed(() => {
  const sampleIds = new Set()
  filteredAgentCalls.value.forEach(call => {
    if (call.sample_id) {
      sampleIds.add(call.sample_id)
    }
  })
  return Array.from(sampleIds).sort((a, b) => a - b)
})

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

const formatDuration = (durationMs) => {
  if (durationMs === null || durationMs === undefined || durationMs <= 0) return '-'
  if (durationMs < 1000) {
    return `${durationMs}ms`
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(2)}s`
  } else {
    const minutes = Math.floor(durationMs / 60000)
    const seconds = ((durationMs % 60000) / 1000).toFixed(2)
    return `${minutes}m ${seconds}s`
  }
}

// 获取智能体描述（合并 role 和 purpose）
const getAgentDescription = (row) => {
  if (row.purpose) {
    return row.purpose
  }
  if (row.role) {
    return row.role
  }
  return '-'
}

const buildGraphData = () => {
  const nodes = new Map()
  const links = []
  
  // 🚀 修复：使用过滤后的调用记录，并添加调试日志
  const filtered = filteredAgentCalls.value
  const sampleIdsInFiltered = new Set(filtered.map(c => c.sample_id).filter(id => id !== null && id !== undefined))
  console.log(`[AgentCallGraph] buildGraphData: 过滤后调用数=${filtered.length}, 包含样本ID=${Array.from(sampleIdsInFiltered).sort((a, b) => a - b).join(',')}`)
  
  filtered.forEach(call => {
    // 添加节点（不区分样本，因为图表显示的是整体调用关系）
    if (!nodes.has(call.from)) {
      nodes.set(call.from, {
        id: call.from,
        name: call.from,
        value: 0,
        category: getAgentCategory(call.from)
      })
    }
    if (!nodes.has(call.to)) {
      nodes.set(call.to, {
        id: call.to,
        name: call.to,
        value: 0,
        category: getAgentCategory(call.to)
      })
    }
    
    // 增加节点权重
    nodes.get(call.from).value++
    nodes.get(call.to).value++
    
    // 添加边（包含样本ID信息）
    links.push({
      source: call.from,
      target: call.to,
      value: call.duration || 1,
      success: call.success,
      sampleId: call.sample_id  // 保存样本ID，用于tooltip显示
    })
  })
  
  return {
    nodes: Array.from(nodes.values()),
    links: links
  }
}

const getAgentCategory = (agentName) => {
  const name = agentName.toLowerCase()
  if (name.includes('knowledge') || name.includes('检索')) return 0
  if (name.includes('reasoning') || name.includes('推理')) return 1
  if (name.includes('answer') || name.includes('答案') || name.includes('generation')) return 2
  if (name.includes('citation') || name.includes('引用')) return 3
  if (name.includes('analysis') || name.includes('分析')) return 4
  if (name.includes('verification') || name.includes('验证') || name.includes('fact')) return 5
  if (name.includes('strategy') || name.includes('策略')) return 6
  if (name.includes('coordinator') || name.includes('协调')) return 7
  if (name.includes('system') || name === 'system') return 8
  return 9  // 其他
}

const renderChart = () => {
  if (!chartContainer.value) return
  
  // 检查DOM元素是否有尺寸
  const rect = chartContainer.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    // 如果还没有尺寸，延迟重试
    setTimeout(() => {
      renderChart()
    }, 100)
    return
  }
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
  }
  
  const graphData = buildGraphData()
  
  const option = {
    title: {
      text: '智能体调用关系图',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `${params.data.name}<br/>调用次数: ${params.data.value}`
        } else {
          return `${params.data.source} → ${params.data.target}<br/>耗时: ${params.data.value}ms`
        }
      }
    },
    legend: {
      data: ['知识检索', '推理引擎', '答案生成', '引用生成', '分析', '验证', '策略', '协调', '系统', '其他'],
      bottom: 0,
      type: 'scroll',
      orient: 'horizontal'
    },
    series: [{
      type: 'graph',
      layout: layoutType.value === 'hierarchical' ? 'none' : 'force',
      data: graphData.nodes,
      links: graphData.links,
      categories: [
        { name: '知识检索', itemStyle: { color: '#409eff' } },
        { name: '推理引擎', itemStyle: { color: '#67c23a' } },
        { name: '答案生成', itemStyle: { color: '#e6a23c' } },
        { name: '引用生成', itemStyle: { color: '#f56c6c' } },
        { name: '分析', itemStyle: { color: '#9c27b0' } },
        { name: '验证', itemStyle: { color: '#ff9800' } },
        { name: '策略', itemStyle: { color: '#00bcd4' } },
        { name: '协调', itemStyle: { color: '#4caf50' } },
        { name: '系统', itemStyle: { color: '#607d8b' } },
        { name: '其他', itemStyle: { color: '#909399' } }
      ],
      roam: true,
      label: {
        show: true,
        position: layoutType.value === 'flowchart' ? 'inside' : 'right',
        fontSize: layoutType.value === 'flowchart' ? 12 : 10,
        formatter: (params) => {
          if (params.data.id === 'start') return '开始'
          if (params.data.id === 'end') return '结束'
          return params.data.name
        }
      },
      labelLayout: {
        hideOverlap: true
      },
      lineStyle: {
        color: 'source',
        curveness: layoutType.value === 'flowchart' ? 0.1 : 0.3,
        width: 2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: {
        repulsion: layoutType.value === 'flowchart' ? 400 : 1000,
        gravity: layoutType.value === 'flowchart' ? 0.2 : 0.1,
        edgeLength: layoutType.value === 'flowchart' ? 120 : 200,
        layoutAnimation: true
      }
    }]
  }
  
  chartInstance.setOption(option)
}

const resetView = () => {
  if (chartInstance) {
    chartInstance.dispatchAction({
      type: 'restore'
    })
  }
}

// 监听调用记录变化
watch(() => props.agentCalls, () => {
  // 如果样本选择器为空，默认选择第一个样本
  if ((!sampleSelector.value || !sampleSelector.value.trim()) && availableSampleIds.value.length > 0) {
    sampleSelector.value = String(availableSampleIds.value[0])
  }
  nextTick(() => {
    if (props.agentCalls && Array.isArray(props.agentCalls) && props.agentCalls.length > 0) {
      renderChart()
    }
  })
}, { deep: true, immediate: true })

// 监听过滤后的调用记录变化
watch(filteredAgentCalls, () => {
  nextTick(() => {
    renderChart()
  })
}, { deep: true })

watch(layoutType, () => {
  renderChart()
})

onMounted(() => {
  nextTick(() => {
    renderChart()
  })
  
  // 响应式调整
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})
</script>

<style scoped>
.agent-call-graph {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.graph-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.graph-controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-container {
  flex: 1;
  min-height: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-bottom: 16px;
}

.call-list {
  margin-top: 16px;
}

.call-list :deep(.el-card__body) {
  padding: 0;
}
</style>

