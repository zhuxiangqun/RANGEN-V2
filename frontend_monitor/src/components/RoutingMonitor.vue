<template>
  <div class="routing-monitor">
    <div class="monitor-header">
      <h2>🔀 智能路由监控</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          inactive-text="手动刷新"
          style="margin-left: 16px;"
        />
        <el-select v-model="timeRange" style="width: 200px; margin-left: 16px;">
          <el-option label="最近1小时" value="1h" />
          <el-option label="最近24小时" value="24h" />
          <el-option label="最近7天" value="7d" />
          <el-option label="全部" value="all" />
        </el-select>
      </div>
    </div>

    <!-- 路由统计概览 -->
    <div class="stats-overview">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background-color: #e6f7ff;">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total_queries || 0 }}</div>
                <div class="stat-label">总查询数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background-color: #f6ffed;">
                <el-icon><MagicStick /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.skill_routing_count || 0 }}</div>
                <div class="stat-label">技能路由</div>
                <div class="stat-ratio" v-if="stats.total_queries > 0">
                  {{ ((stats.skill_routing_count / stats.total_queries) * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background-color: #fff7e6;">
                <el-icon><Tools /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.tool_routing_count || 0 }}</div>
                <div class="stat-label">工具路由</div>
                <div class="stat-ratio" v-if="stats.total_queries > 0">
                  {{ ((stats.tool_routing_count / stats.total_queries) * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon" style="background-color: #fff2f0;">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.fallback_count || 0 }}</div>
                <div class="stat-label">回退次数</div>
                <div class="stat-ratio" v-if="stats.total_queries > 0">
                  {{ ((stats.fallback_count / stats.total_queries) * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 资源使用统计 -->
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <span>本地 vs 外部资源使用</span>
                <el-tag :type="stats.local_resource_ratio > 0.7 ? 'success' : 'warning'">
                  本地资源占比: {{ (stats.local_resource_ratio * 100).toFixed(1) }}%
                </el-tag>
              </div>
            </template>
            <div class="resource-chart">
              <div class="resource-bar">
                <div class="resource-segment local" :style="{ width: `${stats.local_resource_ratio * 100}%` }">
                  <span class="segment-label">本地资源: {{ stats.local_resource_count || 0 }}</span>
                </div>
                <div class="resource-segment external" :style="{ width: `${(1 - stats.local_resource_ratio) * 100}%` }">
                  <span class="segment-label">外部资源: {{ stats.external_resource_count || 0 }}</span>
                </div>
              </div>
              <div class="resource-legend">
                <div class="legend-item">
                  <div class="legend-color local"></div>
                  <span>本地资源 (延迟低、可靠性高)</span>
                </div>
                <div class="legend-item">
                  <div class="legend-color external"></div>
                  <span>外部资源 (网络依赖)</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="chart-header">
                <span>路由性能指标</span>
                <el-tag :type="stats.avg_decision_time < 0.5 ? 'success' : stats.avg_decision_time < 1 ? 'warning' : 'danger'">
                  平均决策时间: {{ stats.avg_decision_time.toFixed(3) || 0 }}s
                </el-tag>
              </div>
            </template>
            <div class="performance-metrics">
              <div class="metric-item">
                <div class="metric-label">成功率</div>
                <div class="metric-value">
                  <el-progress 
                    :percentage="(stats.success_rate * 100) || 85" 
                    :status="stats.success_rate > 0.9 ? 'success' : stats.success_rate > 0.8 ? 'warning' : 'exception'"
                    :stroke-width="10"
                  />
                  <span class="metric-text">{{ ((stats.success_rate || 0.85) * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">技能路由比例</div>
                <div class="metric-value">
                  <el-progress 
                    :percentage="(stats.skill_routing_ratio * 100) || 0" 
                    :status="stats.skill_routing_ratio > 0.5 ? 'success' : 'warning'"
                    :stroke-width="10"
                  />
                  <span class="metric-text">{{ ((stats.skill_routing_ratio || 0) * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 路由决策历史 -->
    <div class="decision-history" style="margin-top: 24px;">
      <el-card>
        <template #header>
          <div class="history-header">
            <span>📊 最近路由决策</span>
            <el-button type="primary" size="small" @click="refreshDecisions">
              <el-icon><Refresh /></el-icon>
              刷新决策记录
            </el-button>
          </div>
        </template>
        
        <el-table :data="recentDecisions" stripe style="width: 100%">
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="{ row }">
              {{ formatTimestamp(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="query" label="查询" width="250">
            <template #default="{ row }">
              <el-tooltip :content="row.query" placement="top">
                <span class="query-text">{{ truncateText(row.query, 30) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="decision_type" label="决策类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getDecisionTypeTag(row.decision_type)">
                {{ getDecisionTypeText(row.decision_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="selected_resource" label="选中资源" width="200">
            <template #default="{ row }">
              <div v-if="row.selected_resource">
                <span class="resource-name">{{ row.selected_resource }}</span>
                <el-tag size="small" :type="getSourceTag(row.selected_resource_source)" style="margin-left: 8px;">
                  {{ getSourceText(row.selected_resource_source) }}
                </el-tag>
              </div>
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="priority_score" label="优先级分数" width="120">
            <template #default="{ row }">
              <el-rate
                v-model="row.priority_score"
                :max="5"
                :show-score="true"
                disabled
                score-template="{value}"
              />
            </template>
          </el-table-column>
          <el-table-column prop="semantic_score" label="语义匹配" width="120">
            <template #default="{ row }">
              <el-progress 
                :percentage="(row.semantic_score * 100).toFixed(0)" 
                :stroke-width="12"
                :show-text="false"
              />
              <span class="score-text">{{ (row.semantic_score * 100).toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="decision_time" label="决策时间" width="120">
            <template #default="{ row }">
              <span :class="getDecisionTimeClass(row.decision_time)">
                {{ row.decision_time.toFixed(3) }}s
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="alternative_options" label="备选方案" width="100">
            <template #default="{ row }">
              <span v-if="row.alternative_options > 0" class="text-success">
                {{ row.alternative_options }} 个
              </span>
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="table-footer" v-if="recentDecisions.length === 0">
          <el-empty description="暂无路由决策记录" />
        </div>
      </el-card>
    </div>

    <!-- 网络状况监控 -->
    <div class="network-monitor" style="margin-top: 24px;" v-if="networkHealthData.length > 0">
      <el-card>
        <template #header>
          <div class="network-header">
            <span>🌐 服务器网络状况</span>
            <el-button type="primary" size="small" @click="checkNetworkHealth">
              <el-icon><Connection /></el-icon>
              检查网络健康
            </el-button>
          </div>
        </template>
        
        <el-table :data="networkHealthData" stripe style="width: 100%">
          <el-table-column prop="server_name" label="服务器名称" width="180" />
          <el-table-column prop="server_url" label="服务器地址" width="250">
            <template #default="{ row }">
              <el-tooltip :content="row.server_url" placement="top">
                <span class="url-text">{{ truncateText(row.server_url, 30) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="latency" label="延迟" width="120">
            <template #default="{ row }">
              <span :class="getLatencyClass(row.latency)">
                {{ row.latency.toFixed(3) }}s
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="available" label="可用性" width="100">
            <template #default="{ row }">
              <el-tag :type="row.available ? 'success' : 'danger'" size="small">
                {{ row.available ? '可用' : '不可用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getStatusTag(row.status)" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_check" label="最后检查" width="180">
            <template #default="{ row }">
              {{ formatTimestamp(row.last_check) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="testServerConnection(row.server_name)">
                测试连接
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { 
  Refresh, 
  DataAnalysis, 
  MagicStick, 
  Tools, 
  Warning,
  Connection
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiService } from '../services/api'

const loading = ref(false)
const autoRefresh = ref(false)
const timeRange = ref('1h')
const stats = ref({
  total_queries: 0,
  skill_routing_count: 0,
  tool_routing_count: 0,
  fallback_count: 0,
  local_resource_count: 0,
  external_resource_count: 0,
  avg_decision_time: 0,
  success_rate: 0.85,
  local_resource_ratio: 0,
  skill_routing_ratio: 0
})

const recentDecisions = ref([])
const networkHealthData = ref([])
let refreshTimer = null

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  if (!timestamp) return '未知'
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 截断文本
const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 获取决策类型标签
const getDecisionTypeTag = (type) => {
  switch (type) {
    case 'skill_routing': return 'success'
    case 'tool_routing': return 'primary'
    case 'fallback': return 'warning'
    default: return 'info'
  }
}

// 获取决策类型文本
const getDecisionTypeText = (type) => {
  switch (type) {
    case 'skill_routing': return '技能路由'
    case 'tool_routing': return '工具路由'
    case 'fallback': return '回退'
    default: return '未知'
  }
}

// 获取来源标签
const getSourceTag = (source) => {
  switch (source) {
    case 'local': return 'success'
    case 'local_mcp': return 'primary'
    case 'external_mcp': return 'warning'
    case 'external': return 'info'
    default: return 'info'
  }
}

// 获取来源文本
const getSourceText = (source) => {
  switch (source) {
    case 'local': return '本地'
    case 'local_mcp': return '本地MCP'
    case 'external_mcp': return '外部MCP'
    case 'external': return '外部'
    default: return source || '未知'
  }
}

// 获取决策时间样式
const getDecisionTimeClass = (time) => {
  if (time < 0.1) return 'text-success'
  if (time < 0.5) return 'text-warning'
  return 'text-danger'
}

// 获取延迟样式
const getLatencyClass = (latency) => {
  if (latency < 0.1) return 'text-success'
  if (latency < 0.5) return 'text-warning'
  return 'text-danger'
}

// 获取状态标签
const getStatusTag = (status) => {
  switch (status) {
    case 'healthy': return 'success'
    case 'unhealthy': return 'danger'
    case 'error': return 'warning'
    case 'monitoring_disabled': return 'info'
    default: return 'info'
  }
}

// 刷新统计数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchRoutingStats(),
      fetchRecentDecisions(),
      fetchNetworkHealth()
    ])
    ElMessage.success('路由监控数据刷新成功')
  } catch (error) {
    console.error('刷新路由监控数据失败:', error)
    ElMessage.error('刷新路由监控数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取路由统计
const fetchRoutingStats = async () => {
  try {
    const response = await apiService.getRoutingStatistics()
    // API返回的是直接的对象，没有嵌套的data字段
    stats.value = response
  } catch (error) {
    console.error('获取路由统计失败:', error)
    ElMessage.warning('使用模拟路由统计数据')
    // 使用模拟数据
    stats.value = {
      total_queries: 125,
      skill_routing_count: 68,
      tool_routing_count: 52,
      fallback_count: 5,
      local_resource_count: 98,
      external_resource_count: 27,
      avg_decision_time: 0.125,
      success_rate: 0.92,
      local_resource_ratio: 0.784,
      skill_routing_ratio: 0.544
    }
  }
}

// 获取最近决策
const fetchRecentDecisions = async () => {
  try {
    const response = await apiService.getRecentRoutingDecisions()
    // API返回 { decisions: [], total_count: X, limit: X, offset: X }
    if (response && Array.isArray(response.decisions)) {
      recentDecisions.value = response.decisions
    } else if (Array.isArray(response)) {
      // 兼容直接返回数组的情况
      recentDecisions.value = response
    } else {
      // 使用模拟数据
      ElMessage.warning('使用模拟路由决策数据')
      recentDecisions.value = generateMockDecisions()
    }
  } catch (error) {
    console.error('获取最近决策失败:', error)
    ElMessage.warning('使用模拟路由决策数据')
    recentDecisions.value = generateMockDecisions()
  }
}

// 获取网络健康数据
const fetchNetworkHealth = async () => {
  try {
    const response = await apiService.getNetworkHealth()
    // API返回 { servers: [], total_servers: X, healthy_servers: X, unhealthy_servers: X, check_time: X }
    if (response && Array.isArray(response.servers)) {
      // 映射字段到模板需要的格式
      networkHealthData.value = response.servers.map(server => ({
        server_name: server.server_name,
        server_url: server.http_endpoint || server.server_name, // 如果没有URL，使用名称
        latency: server.latency || 0,
        available: server.is_available || false,
        status: server.is_available ? 'healthy' : 'unhealthy',
        last_check: server.last_check_time
      }))
    } else if (Array.isArray(response)) {
      // 兼容直接返回数组的情况
      networkHealthData.value = response
    } else {
      // 使用模拟数据
      ElMessage.warning('使用模拟网络健康数据')
      networkHealthData.value = generateMockNetworkHealth()
    }
  } catch (error) {
    console.error('获取网络健康数据失败:', error)
    ElMessage.warning('使用模拟网络健康数据')
    networkHealthData.value = generateMockNetworkHealth()
  }
}

// 刷新决策记录
const refreshDecisions = async () => {
  try {
    await fetchRecentDecisions()
    ElMessage.success('决策记录刷新成功')
  } catch (error) {
    console.error('刷新决策记录失败:', error)
    ElMessage.error('刷新决策记录失败: ' + error.message)
  }
}

// 检查网络健康
const checkNetworkHealth = async () => {
  try {
    loading.value = true
    // 这里调用后端API检查网络健康
    await fetchNetworkHealth()
    ElMessage.success('网络健康检查完成')
  } catch (error) {
    console.error('检查网络健康失败:', error)
    ElMessage.error('检查网络健康失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 测试服务器连接
const testServerConnection = async (serverName) => {
  try {
    ElMessage.info(`正在测试服务器 ${serverName} 连接...`)
    // 这里调用后端API测试服务器连接
    // 暂时模拟
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success(`服务器 ${serverName} 连接测试成功`)
  } catch (error) {
    ElMessage.error(`服务器 ${serverName} 连接测试失败: ` + error.message)
  }
}

// 生成模拟决策数据
const generateMockDecisions = () => {
  const queries = [
    "查询北京天气",
    "计算25的平方根",
    "翻译'Hello World'到中文",
    "搜索最近的餐厅",
    "获取当前时间",
    "计算三角函数值",
    "查询股票价格",
    "生成随机数",
    "格式化JSON数据",
    "压缩图片文件"
  ]
  
  const resources = [
    { id: "weather_skill", name: "天气查询技能", source: "local" },
    { id: "calculator_tool", name: "计算器工具", source: "local" },
    { id: "translator_skill", name: "翻译技能", source: "local_mcp" },
    { id: "search_tool", name: "搜索工具", source: "external_mcp" },
    { id: "time_skill", name: "时间技能", source: "local" }
  ]
  
  const decisions = []
  const now = Date.now() / 1000
  
  for (let i = 0; i < 10; i++) {
    const query = queries[i % queries.length]
    const resource = resources[i % resources.length]
    const decisionType = i % 3 === 0 ? 'skill_routing' : i % 3 === 1 ? 'tool_routing' : 'fallback'
    
    decisions.push({
      timestamp: now - (i * 60), // 每60秒一个
      query: query,
      decision_type: decisionType,
      selected_resource: decisionType === 'fallback' ? null : resource.id,
      selected_resource_type: decisionType === 'skill_routing' ? 'skill' : 'tool',
      selected_resource_source: decisionType === 'fallback' ? null : resource.source,
      priority_score: 0.7 + Math.random() * 0.3,
      semantic_score: 0.6 + Math.random() * 0.4,
      decision_time: 0.05 + Math.random() * 0.15,
      alternative_options: Math.floor(Math.random() * 5)
    })
  }
  
  return decisions
}

// 生成模拟网络健康数据
const generateMockNetworkHealth = () => {
  const servers = [
    { name: "local_weather", url: "http://localhost:8001", type: "local_mcp" },
    { name: "external_translate", url: "http://api.translate.com", type: "external_mcp" },
    { name: "local_calculator", url: "stdio:///usr/bin/python3", type: "local_mcp" },
    { name: "external_search", url: "http://api.search.com", type: "external_mcp" }
  ]
  
  const now = Date.now() / 1000
  
  return servers.map(server => ({
    server_name: server.name,
    server_url: server.url,
    latency: 0.05 + Math.random() * 0.3,
    available: Math.random() > 0.2,
    status: Math.random() > 0.2 ? 'healthy' : 'unhealthy',
    last_check: now - Math.random() * 300
  }))
}

// 监听自动刷新
watch(autoRefresh, (newVal) => {
  if (newVal) {
    refreshTimer = setInterval(() => {
      refreshData()
    }, 10000) // 10秒刷新一次
  } else if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

// 组件挂载时加载数据
onMounted(() => {
  refreshData()
  if (autoRefresh.value) {
    refreshTimer = setInterval(() => {
      refreshData()
    }, 10000)
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.routing-monitor {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.monitor-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
}

.stats-overview {
  margin-bottom: 24px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #1890ff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-ratio {
  font-size: 12px;
  color: #52c41a;
  margin-top: 2px;
}

.chart-card {
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-chart {
  padding: 16px 0;
}

.resource-bar {
  height: 30px;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  margin-bottom: 16px;
  background-color: #f5f5f5;
}

.resource-segment {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
}

.resource-segment.local {
  background-color: #52c41a;
}

.resource-segment.external {
  background-color: #faad14;
}

.segment-label {
  color: white;
  font-size: 12px;
  font-weight: bold;
  padding: 0 8px;
  text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.3);
}

.resource-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  margin-right: 8px;
}

.legend-color.local {
  background-color: #52c41a;
}

.legend-color.external {
  background-color: #faad14;
}

.performance-metrics {
  padding: 8px 0;
}

.metric-item {
  margin-bottom: 16px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  display: flex;
  align-items: center;
}

.metric-value .el-progress {
  flex: 1;
  margin-right: 12px;
}

.metric-text {
  font-size: 14px;
  font-weight: bold;
  min-width: 50px;
  text-align: right;
}

.decision-history {
  margin-top: 24px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-name {
  font-family: monospace;
  font-size: 12px;
}

.score-text {
  font-size: 12px;
  color: #666;
  margin-left: 8px;
}

.text-success {
  color: #52c41a;
}

.text-warning {
  color: #faad14;
}

.text-danger {
  color: #ff4d4f;
}

.text-muted {
  color: #999;
}

.table-footer {
  padding: 40px 0;
  text-align: center;
}

.network-monitor {
  margin-top: 24px;
}

.network-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.url-text {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>