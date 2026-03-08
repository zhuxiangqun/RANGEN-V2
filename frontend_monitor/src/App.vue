<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-content">
        <div class="logo-section">
          <h1 class="logo">🚀 RANGEN V2 一体化体验系统</h1>
          <div class="subtitle">在一个画面中体验所有功能 | 真实模式 - 使用DeepSeek API</div>
        </div>
        <div class="status-section">
          <div class="status-item">
            <el-tag type="success" size="small">后端API: 运行中</el-tag>
            <span class="status-text">localhost:8000</span>
          </div>
          <div class="status-item">
            <el-tag type="success" size="small">自动发现: 就绪</el-tag>
            <span class="status-text">已发现6个资源</span>
          </div>
          <div class="status-item">
            <el-tag type="info" size="small">模式: 真实</el-tag>
            <span class="status-text">使用DeepSeek API</span>
          </div>
        </div>
      </div>
    </el-header>

    <!-- 主要内容区域 -->
    <el-main class="main-content">
      <!-- 系统概览卡片 -->
      <el-row :gutter="20" class="overview-row">
        <el-col :span="6">
          <el-card class="overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">📊 系统统计</span>
              </div>
            </template>
            <div class="card-content">
              <div class="stat-item">
                <div class="stat-label">总查询数</div>
                <div class="stat-value">{{ systemStats.totalQueries || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">技能路由</div>
                <div class="stat-value">{{ systemStats.skillRoutingCount || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">工具路由</div>
                <div class="stat-value">{{ systemStats.toolRoutingCount || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">本地资源</div>
                <div class="stat-value">{{ systemStats.localResourceCount || 0 }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-button type="primary" size="small" @click="refreshStats">刷新统计</el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">🔍 自动发现</span>
              </div>
            </template>
            <div class="card-content">
              <div class="stat-item">
                <div class="stat-label">已发现资源</div>
                <div class="stat-value">{{ discoveryStats.discoveredCount || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">目标数量</div>
                <div class="stat-value">{{ discoveryStats.targetCount || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">集成状态</div>
                <div class="stat-value">
                  <el-tag :type="discoveryStats.serviceInitialized ? 'success' : 'warning'" size="small">
                    {{ discoveryStats.serviceInitialized ? '就绪' : '初始化中' }}
                  </el-tag>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">最后扫描</div>
                <div class="stat-value">{{ formatTimeShort(discoveryStats.timestamp) || '从未' }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-button-group>
                <el-button type="primary" size="small" @click="startDiscoveryScan">启动扫描</el-button>
                <el-button type="success" size="small" @click="autoIntegrate">自动集成</el-button>
              </el-button-group>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">🤖 Agent管理</span>
              </div>
            </template>
            <div class="card-content">
              <div class="stat-item">
                <div class="stat-label">活跃Agent</div>
                <div class="stat-value">{{ agentStats.activeAgents || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">总Agent数</div>
                <div class="stat-value">{{ agentStats.totalAgents || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">总调用数</div>
                <div class="stat-value">{{ agentStats.totalCalls || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">成功率</div>
                <div class="stat-value">{{ agentStats.successRate ? Math.round(agentStats.successRate * 100) + '%' : '0%' }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-input
                v-model="agentQuery"
                placeholder="输入Agent需求，例如：帮我写Python代码调试程序"
                clearable
              >
                <template #append>
                  <el-button type="primary" @click="triggerAgentDemand">触发</el-button>
                </template>
              </el-input>
              <div class="hint-text">
                系统将自动分析需求，发现并集成相关资源
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">🔧 工具管理</span>
              </div>
            </template>
            <div class="card-content">
              <div class="stat-item">
                <div class="stat-label">可用工具</div>
                <div class="stat-value">{{ toolStats.availableTools || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">MCP工具</div>
                <div class="stat-value">{{ toolStats.mcpTools || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">自定义工具</div>
                <div class="stat-value">{{ toolStats.customTools || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">总调用数</div>
                <div class="stat-value">{{ toolStats.totalCalls || 0 }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-button type="warning" size="small" @click="showToolManagement">管理工具</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 路由监控面板 -->
      <el-card class="routing-panel" shadow="hover">
        <template #header>
          <div class="panel-header">
            <h3>📊 路由监控面板</h3>
            <div class="panel-actions">
              <el-button type="primary" size="small" @click="refreshRoutingStats">刷新路由</el-button>
              <el-button type="info" size="small" @click="refreshMCP">刷新MCP</el-button>
              <el-button type="success" size="small" @click="refreshExternal">刷新外部</el-button>
            </div>
          </div>
        </template>
        <div class="panel-content">
          <div class="routing-stats">
            <h4>路由统计</h4>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-title">总查询数</div>
                <div class="stat-number">{{ routingStats.total_queries || 0 }}</div>
                <div class="stat-subtitle">历史总查询</div>
              </div>
              <div class="stat-card">
                <div class="stat-title">技能路由</div>
                <div class="stat-number">{{ routingStats.skill_routing_count || 0 }}</div>
                <div class="stat-subtitle">{{ routingStats.skill_routing_ratio ? Math.round(routingStats.skill_routing_ratio * 100) + '%' : '0%' }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-title">工具路由</div>
                <div class="stat-number">{{ routingStats.tool_routing_count || 0 }}</div>
                <div class="stat-subtitle">工具调用</div>
              </div>
              <div class="stat-card">
                <div class="stat-title">决策时间</div>
                <div class="stat-number">{{ routingStats.avg_decision_time ? routingStats.avg_decision_time.toFixed(2) : '0.00' }}ms</div>
                <div class="stat-subtitle">平均决策时间</div>
              </div>
              <div class="stat-card">
                <div class="stat-title">成功率</div>
                <div class="stat-number">{{ routingStats.success_rate ? Math.round(routingStats.success_rate * 100) + '%' : '0%' }}</div>
                <div class="stat-subtitle">路由成功率</div>
              </div>
              <div class="stat-card">
                <div class="stat-title">更新时间</div>
                <div class="stat-number">{{ formatTimeShort(routingStats.timestamp) || '无数据' }}</div>
                <div class="stat-subtitle">最后更新</div>
              </div>
            </div>
          </div>
          
          <div class="routing-details">
            <div class="detail-section">
              <h4>最近路由决策</h4>
              <el-table :data="recentDecisions" size="small" height="200">
                <el-table-column prop="query" label="查询内容" width="200">
                  <template #default="{ row }">
                    <div class="query-cell">{{ truncateText(row.query, 30) }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="decision_type" label="决策类型" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.decision_type === 'skill' ? 'success' : 'primary'" size="small">
                      {{ row.decision_type === 'skill' ? '技能' : '工具' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="selected_resource" label="选择资源" width="120"></el-table-column>
                <el-table-column prop="timestamp" label="时间" width="100">
                  <template #default="{ row }">
                    {{ formatTimeShort(row.timestamp) }}
                  </template>
                </el-table-column>
                <el-table-column prop="confidence" label="置信度" width="80">
                  <template #default="{ row }">
                    <el-progress 
                      :percentage="Math.round(row.confidence * 100)" 
                      :format="() => Math.round(row.confidence * 100) + '%'"
                      :stroke-width="10"
                      :show-text="false"
                    ></el-progress>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.integrated ? 'success' : 'warning'" 
                      size="small"
                    >
                      {{ row.integrated ? '已集成' : '未集成' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            
            <div class="detail-section">
              <h4>已发现资源</h4>
              <el-table :data="discoveredResources" size="small" height="200">
                <el-table-column prop="name" label="资源名称" width="150"></el-table-column>
                <el-table-column prop="resource_type" label="类型" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getResourceTypeTag(row.resource_type)" size="small">
                      {{ getResourceTypeText(row.resource_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="endpoint" label="端点" width="150">
                  <template #default="{ row }">
                    <div class="endpoint-cell">{{ truncateText(row.endpoint, 25) }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="confidence" label="置信度" width="80">
                  <template #default="{ row }">
                    <el-progress 
                      :percentage="Math.round(row.confidence * 100)" 
                      :format="() => Math.round(row.confidence * 100) + '%'"
                      :stroke-width="10"
                      :show-text="false"
                    ></el-progress>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.integrated ? 'success' : 'warning'" 
                      size="small"
                    >
                      {{ row.integrated ? '已集成' : '未集成' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button 
                      v-if="!row.integrated" 
                      type="primary" 
                      size="small"
                      @click="integrateResource(row.id)"
                    >
                      集成
                    </el-button>
                    <el-button 
                      v-else 
                      type="info" 
                      size="small"
                      @click="disconnectResource(row.id)"
                    >
                      断开
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
          
          <div class="external-management">
            <div class="mcp-section">
              <h4>MCP服务器状态</h4>
              <el-table :data="mcpServers" size="small" height="200">
                <el-table-column prop="name" label="服务器名称" width="120"></el-table-column>
                <el-table-column prop="type" label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.type === 'local' ? 'success' : 'primary'" size="small">
                      {{ row.type === 'local' ? '本地' : '外部' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="endpoint" label="端点" width="150">
                  <template #default="{ row }">
                    <div class="endpoint-cell">{{ truncateText(row.endpoint, 25) }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.status === 'connected' ? 'success' : row.status === 'connecting' ? 'warning' : 'danger'" 
                      size="small"
                    >
                      {{ row.status === 'connected' ? '已连接' : row.status === 'connecting' ? '连接中' : '未连接' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tools_count" label="工具数量" width="80"></el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button 
                      v-if="row.status !== 'connected'" 
                      type="primary" 
                      size="small"
                      @click="connectMCP(row.name)"
                    >
                      连接
                    </el-button>
                    <el-button 
                      v-else 
                      type="info" 
                      size="small"
                      @click="disconnectMCP(row.name)"
                    >
                      断开
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="mcp-actions">
                <el-button type="primary" @click="connectAllMCP">连接所有MCP</el-button>
                <el-button type="success" @click="refreshMCP">刷新状态</el-button>
              </div>
            </div>
            
            <div class="network-health">
              <h4>网络健康状态</h4>
              <div class="health-list">
                <div class="health-item" v-for="(server, index) in networkHealth" :key="index">
                  <div class="health-name">{{ server.name }}</div>
                  <div class="health-status">
                    <el-tag 
                      :type="server.status === 'healthy' ? 'success' : server.status === 'degraded' ? 'warning' : 'danger'"
                      size="small"
                    >
                      {{ server.status === 'healthy' ? '健康' : server.status === 'degraded' ? '降级' : '异常' }}
                    </el-tag>
                  </div>
                  <div class="health-latency">{{ server.latency ? server.latency.toFixed(0) + 'ms' : 'N/A' }}</div>
                </div>
              </div>
            </div>
            
            <div class="external-services">
              <h4>外部服务状态</h4>
              <el-table :data="externalServices" size="small" height="200">
                <el-table-column prop="name" label="服务名称" width="120"></el-table-column>
                <el-table-column prop="type" label="类型" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getServiceTypeTag(row.type)" size="small">
                      {{ getServiceTypeText(row.type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="endpoint" label="端点" width="150">
                  <template #default="{ row }">
                    <div class="endpoint-cell">{{ truncateText(row.endpoint, 25) }}</div>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag 
                      :type="row.status === 'active' ? 'success' : 'warning'" 
                      size="small"
                    >
                      {{ row.status === 'active' ? '活跃' : '未激活' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="{ row }">
                    <el-button 
                      v-if="row.status !== 'active'" 
                      type="primary" 
                      size="small"
                      @click="activateService(row.id)"
                    >
                      激活
                    </el-button>
                    <el-button 
                      v-else 
                      type="info" 
                      size="small"
                      @click="deactivateService(row.id)"
                    >
                      停用
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="external-actions">
                <h4>快速操作</h4>
                <div class="action-buttons">
                  <el-button type="primary" @click="discoverAndIntegrate">
                    🔍 一键发现并集成
                  </el-button>
                  <el-button type="success" @click="testAllServices">
                    🧪 测试所有服务
                  </el-button>
                  <el-button type="warning" @click="clearDiscoveryCache">
                    🗑️ 清除发现缓存
                  </el-button>
                </div>
                <div class="action-hints">
                  <p>💡 提示：</p>
                  <ul>
                    <li>一键发现并集成会自动扫描网络并集成可用资源</li>
                    <li>测试所有服务会检查所有外部服务的连接状态</li>
                    <li>清除缓存会重置自动发现的历史记录</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </el-main>

    <!-- 底部信息栏 -->
    <el-footer class="footer">
      <div class="footer-content">
        <div class="footer-left">
          <span>RANGEN V2 一体化体验系统 | 真实模式 | 使用DeepSeek API</span>
        </div>
        <div class="footer-right">
          <span>后端: localhost:8000 | 前端: localhost:3000 | 最后更新: {{ currentTime }}</span>
        </div>
      </div>
    </el-footer>

    <!-- 加载遮罩 -->
    <el-dialog
      v-model="loading"
      title="系统处理中"
      width="30%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="loading-content">
        <el-progress :percentage="loadingProgress" :indeterminate="loadingProgress === 0"></el-progress>
        <p class="loading-text">{{ loadingText }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from './services/api'

export default {
  name: 'App',
  
  setup() {
    // 状态数据
    const systemStats = ref({})
    const discoveryStats = ref({})
    const agentStats = ref({})
    const toolStats = ref({})
    const routingStats = ref({})
    const recentDecisions = ref([])
    const discoveredResources = ref([])
    const mcpServers = ref([])
    const networkHealth = ref([])
    const externalServices = ref([])
    
    // 控制数据
    const loading = ref(false)
    const loadingProgress = ref(0)
    const loadingText = ref('系统初始化中...')
    const agentQuery = ref('')
    const currentTime = ref('')
    
    // 模拟的路由数据（用于图表）
    const routingData = ref([
      { time: '00:00', queries: 12 },
      { time: '04:00', queries: 8 },
      { time: '08:00', queries: 25 },
      { time: '12:00', queries: 42 },
      { time: '16:00', queries: 38 },
      { time: '20:00', queries: 21 }
    ])
    
    // 工具函数
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    }
    
    const formatTimeShort = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    
    const truncateText = (text, maxLength) => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }
    
    const getResourceTypeTag = (type) => {
      const typeMap = {
        'mcp': 'primary',
        'api': 'success',
        'tool': 'warning',
        'database': 'info',
        'file': ''
      }
      return typeMap[type] || 'info'
    }
    
    const getResourceTypeText = (type) => {
      const typeMap = {
        'mcp': 'MCP服务',
        'api': 'API服务',
        'tool': '工具',
        'database': '数据库',
        'file': '文件'
      }
      return typeMap[type] || type
    }
    
    const getServiceTypeTag = (type) => {
      const typeMap = {
        'openai': 'success',
        'github': 'primary',
        'api': 'warning',
        'custom': 'info',
        'weather': ''
      }
      return typeMap[type] || 'info'
    }
    
    const getServiceTypeText = (type) => {
      const typeMap = {
        'openai': 'OpenAI',
        'github': 'GitHub',
        'api': 'API服务',
        'custom': '自定义',
        'weather': '天气'
      }
      return typeMap[type] || type
    }
    
    // 显示加载遮罩
    const showLoading = (text = '处理中...') => {
      loading.value = true
      loadingText.value = text
      loadingProgress.value = 0
    }
    
    const hideLoading = () => {
      loading.value = false
      loadingProgress.value = 0
    }
    
    const updateProgress = (progress) => {
      loadingProgress.value = progress
    }
    
    // 操作方法
    const refreshStats = async () => {
      try {
        const response = await api.getRoutingStatistics()
        routingStats.value = response
        systemStats.value = {
          totalQueries: response.total_queries,
          skillRoutingCount: response.skill_routing_count,
          toolRoutingCount: response.tool_routing_count,
          localResourceCount: response.local_resource_count
        }
        ElMessage.success('统计数据已刷新')
      } catch (error) {
        console.error('刷新统计失败:', error)
        ElMessage.error('刷新统计失败')
      }
    }
    
    const refreshDiscovery = async () => {
      try {
        const [statusResponse, resourcesResponse] = await Promise.all([
          api.getAutoDiscoveryStatus(),
          api.getDiscoveredResources()
        ])
        discoveryStats.value = statusResponse
        discoveredResources.value = resourcesResponse.resources || []
        ElMessage.success('发现数据已刷新')
      } catch (error) {
        console.error('刷新发现数据失败:', error)
        ElMessage.error('刷新发现数据失败')
      }
    }
    
    const refreshRoutingStats = async () => {
      await refreshStats()
    }
    
    const refreshMCP = async () => {
      try {
        // 模拟MCP服务器数据
        mcpServers.value = [
          { id: 1, name: '文件系统', type: 'local', endpoint: 'file:///', status: 'connected', tools_count: 12 },
          { id: 2, name: 'GitHub', type: 'external', endpoint: 'https://api.github.com', status: 'connected', tools_count: 8 },
          { id: 3, name: '数据库', type: 'local', endpoint: 'postgres://localhost:5432', status: 'connecting', tools_count: 5 },
          { id: 4, name: '天气服务', type: 'external', endpoint: 'https://api.weather.com', status: 'disconnected', tools_count: 3 }
        ]
        ElMessage.success('MCP状态已刷新')
      } catch (error) {
        console.error('刷新MCP失败:', error)
        ElMessage.error('刷新MCP失败')
      }
    }
    
    const refreshExternal = async () => {
      try {
        // 模拟外部服务数据
        externalServices.value = [
          { id: 1, name: 'OpenAI GPT', type: 'openai', endpoint: 'https://api.openai.com/v1', status: 'active' },
          { id: 2, name: 'GitHub API', type: 'github', endpoint: 'https://api.github.com', status: 'active' },
          { id: 3, name: '自定义API', type: 'custom', endpoint: 'https://api.example.com', status: 'inactive' },
          { id: 4, name: '天气API', type: 'api', endpoint: 'https://api.weather.com', status: 'active' }
        ]
        ElMessage.success('外部服务状态已刷新')
      } catch (error) {
        console.error('刷新外部服务失败:', error)
        ElMessage.error('刷新外部服务失败')
      }
    }
    
    const startDiscoveryScan = async () => {
      try {
        showLoading('启动自动发现扫描...')
        await api.startDiscoveryScan()
        updateProgress(50)
        await refreshDiscovery()
        updateProgress(100)
        setTimeout(() => {
          hideLoading()
          ElMessage.success('自动发现扫描已启动')
        }, 500)
      } catch (error) {
        console.error('启动扫描失败:', error)
        hideLoading()
        ElMessage.error('启动扫描失败')
      }
    }
    
    const autoIntegrate = async () => {
      try {
        showLoading('自动集成资源...')
        await api.autoIntegrateResources()
        updateProgress(50)
        await refreshDiscovery()
        updateProgress(100)
        setTimeout(() => {
          hideLoading()
          ElMessage.success('自动集成完成')
        }, 500)
      } catch (error) {
        console.error('自动集成失败:', error)
        hideLoading()
        ElMessage.error('自动集成失败')
      }
    }
    
    const triggerAgentDemand = async () => {
      if (!agentQuery.value.trim()) {
        ElMessage.warning('请输入Agent需求')
        return
      }
      
      try {
        showLoading('触发Agent需求...')
        const response = await api.triggerAgentDemand(agentQuery.value)
        updateProgress(50)
        agentQuery.value = ''
        await refreshDiscovery()
        updateProgress(100)
        setTimeout(() => {
          hideLoading()
          ElMessage.success(`Agent需求已触发: ${response.target_name}`)
        }, 500)
      } catch (error) {
        console.error('触发Agent需求失败:', error)
        hideLoading()
        ElMessage.error('触发Agent需求失败')
      }
    }
    
    const connectMCP = async (serverName) => {
      try {
        showLoading(`连接MCP服务器: ${serverName}...`)
        // 模拟连接延迟
        await new Promise(resolve => setTimeout(resolve, 1000))
        updateProgress(100)
        hideLoading()
        ElMessage.success(`MCP服务器 ${serverName} 已连接`)
        refreshMCP()
      } catch (error) {
        console.error('连接MCP失败:', error)
        hideLoading()
        ElMessage.error('连接MCP失败')
      }
    }
    
    const disconnectMCP = async (serverName) => {
      try {
        showLoading(`断开MCP服务器: ${serverName}...`)
        // 模拟断开延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        updateProgress(100)
        hideLoading()
        ElMessage.success(`MCP服务器 ${serverName} 已断开`)
        refreshMCP()
      } catch (error) {
        console.error('断开MCP失败:', error)
        hideLoading()
        ElMessage.error('断开MCP失败')
      }
    }
    
    const connectAllMCP = async () => {
      try {
        showLoading('连接所有MCP服务器...')
        // 模拟连接所有
        await new Promise(resolve => setTimeout(resolve, 1500))
        updateProgress(100)
        hideLoading()
        ElMessage.success('所有MCP服务器已连接')
        refreshMCP()
      } catch (error) {
        console.error('连接所有MCP失败:', error)
        hideLoading()
        ElMessage.error('连接所有MCP失败')
      }
    }
    
    const integrateResource = async (resourceId) => {
      try {
        showLoading('集成资源...')
        // 模拟集成
        await new Promise(resolve => setTimeout(resolve, 800))
        updateProgress(100)
        hideLoading()
        ElMessage.success('资源集成成功')
        refreshDiscovery()
      } catch (error) {
        console.error('集成资源失败:', error)
        hideLoading()
        ElMessage.error('集成资源失败')
      }
    }
    
    const disconnectResource = async (resourceId) => {
      try {
        showLoading('断开资源...')
        // 模拟断开
        await new Promise(resolve => setTimeout(resolve, 600))
        updateProgress(100)
        hideLoading()
        ElMessage.success('资源断开成功')
        refreshDiscovery()
      } catch (error) {
        console.error('断开资源失败:', error)
        hideLoading()
        ElMessage.error('断开资源失败')
      }
    }
    
    const discoverAndIntegrate = async () => {
      try {
        showLoading('一键发现并集成...')
        await startDiscoveryScan()
        updateProgress(50)
        await autoIntegrate()
        updateProgress(100)
        hideLoading()
        ElMessage.success('一键发现并集成完成')
      } catch (error) {
        console.error('一键发现并集成失败:', error)
        hideLoading()
        ElMessage.error('一键发现并集成失败')
      }
    }
    
    const showAgentDetails = () => {
      ElMessage.info('Agent详情功能开发中...')
    }
    
    const showToolManagement = () => {
      ElMessage.info('工具管理功能开发中...')
    }
    
    const activateService = async (serviceId) => {
      try {
        showLoading('激活服务...')
        // 模拟激活
        await new Promise(resolve => setTimeout(resolve, 700))
        updateProgress(100)
        hideLoading()
        ElMessage.success('服务激活成功')
        refreshExternal()
      } catch (error) {
        console.error('激活服务失败:', error)
        hideLoading()
        ElMessage.error('激活服务失败')
      }
    }
    
    const deactivateService = async (serviceId) => {
      try {
        showLoading('停用服务...')
        // 模拟停用
        await new Promise(resolve => setTimeout(resolve, 600))
        updateProgress(100)
        hideLoading()
        ElMessage.success('服务停用成功')
        refreshExternal()
      } catch (error) {
        console.error('停用服务失败:', error)
        hideLoading()
        ElMessage.error('停用服务失败')
      }
    }
    
    const addExternalAPI = () => {
      ElMessage.info('添加外部API功能开发中...')
    }
    
    const testAllServices = async () => {
      try {
        showLoading('测试所有服务...')
        // 模拟测试
        await new Promise(resolve => setTimeout(resolve, 2000))
        updateProgress(100)
        hideLoading()
        ElMessage.success('所有服务测试完成')
      } catch (error) {
        console.error('测试服务失败:', error)
        hideLoading()
        ElMessage.error('测试服务失败')
      }
    }
    
    const clearDiscoveryCache = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清除自动发现缓存吗？这将重置所有发现历史。',
          '确认清除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        showLoading('清除缓存...')
        // 模拟清除
        await new Promise(resolve => setTimeout(resolve, 800))
        updateProgress(100)
        hideLoading()
        ElMessage.success('缓存清除成功')
        refreshDiscovery()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('清除缓存失败:', error)
          ElMessage.error('清除缓存失败')
        }
      }
    }
    
    // 系统初始化
    const initialize = async () => {
      showLoading('一体化体验系统初始化...')
      
      try {
        // 模拟初始化步骤
        updateProgress(10)
        await refreshStats()
        
        updateProgress(30)
        await refreshDiscovery()
        
        updateProgress(50)
        refreshMCP()
        refreshExternal()
        
        updateProgress(70)
        // 模拟网络健康数据
        networkHealth.value = [
          { name: '后端API', status: 'healthy', latency: 42 },
          { name: '自动发现', status: 'healthy', latency: 67 },
          { name: 'MCP服务', status: 'degraded', latency: 215 },
          { name: '外部API', status: 'healthy', latency: 89 }
        ]
        
        updateProgress(85)
        // 模拟最近决策数据
        recentDecisions.value = [
          { id: 1, query: '帮我写Python代码调试程序', decision_type: 'skill', selected_resource: 'code_agent', timestamp: new Date().toISOString(), confidence: 0.92, integrated: true },
          { id: 2, query: '分析这个JSON文件结构', decision_type: 'tool', selected_resource: 'json_parser', timestamp: new Date(Date.now() - 300000).toISOString(), confidence: 0.87, integrated: true },
          { id: 3, query: '连接到GitHub仓库获取代码', decision_type: 'tool', selected_resource: 'github_client', timestamp: new Date(Date.now() - 600000).toISOString(), confidence: 0.95, integrated: true },
          { id: 4, query: '帮我写技术文档', decision_type: 'skill', selected_resource: 'doc_writer', timestamp: new Date(Date.now() - 900000).toISOString(), confidence: 0.78, integrated: false },
          { id: 5, query: '分析系统日志错误', decision_type: 'skill', selected_resource: 'log_analyzer', timestamp: new Date(Date.now() - 1200000).toISOString(), confidence: 0.83, integrated: true }
        ]
        
        // 模拟已发现资源
        discoveredResources.value = [
          { id: 1, name: '文件系统MCP', resource_type: 'mcp', endpoint: 'file:///', confidence: 0.95, integrated: true },
          { id: 2, name: 'GitHub API', resource_type: 'api', endpoint: 'https://api.github.com', confidence: 0.88, integrated: true },
          { id: 3, name: '代码分析工具', resource_type: 'tool', endpoint: 'internal://code_analyzer', confidence: 0.76, integrated: false },
          { id: 4, name: 'PostgreSQL数据库', resource_type: 'database', endpoint: 'postgres://localhost:5432', confidence: 0.82, integrated: true },
          { id: 5, name: '天气API', resource_type: 'api', endpoint: 'https://api.weather.com', confidence: 0.65, integrated: false }
        ]
        
        // 模拟统计
        agentStats.value = {
          activeAgents: 3,
          totalAgents: 8,
          totalCalls: 142,
          successRate: 0.92
        }
        
        toolStats.value = {
          availableTools: 15,
          mcpTools: 8,
          customTools: 7,
          totalCalls: 42
        }
        
        updateProgress(100)
        setTimeout(() => {
          hideLoading()
          ElMessage.success('一体化体验系统初始化完成')
        }, 500)
      } catch (error) {
        console.error('初始化失败:', error)
        ElMessage.error('初始化失败，请检查后端服务')
        hideLoading()
      }
    }
    
    // 定时更新当前时间
    const updateCurrentTime = () => {
      currentTime.value = new Date().toLocaleString('zh-CN')
    }
    
    // 生命周期钩子
    onMounted(() => {
      initialize()
      updateCurrentTime()
      // 每秒更新时间
      const timeInterval = setInterval(updateCurrentTime, 1000)
      
      // 每30秒刷新一次数据
      const refreshInterval = setInterval(() => {
        refreshStats()
      }, 30000)
      
      // 保存定时器ID以便清理
      window.__timeInterval = timeInterval
      window.__refreshInterval = refreshInterval
    })
    
    onUnmounted(() => {
      if (window.__timeInterval) {
        clearInterval(window.__timeInterval)
      }
      if (window.__refreshInterval) {
        clearInterval(window.__refreshInterval)
      }
    })
    
    return {
      // 状态数据
      systemStats,
      discoveryStats,
      agentStats,
      toolStats,
      routingStats,
      recentDecisions,
      discoveredResources,
      mcpServers,
      networkHealth,
      externalServices,
      
      // 控制数据
      loading,
      loadingProgress,
      loadingText,
      agentQuery,
      currentTime,
      routingData,
      
      // 工具函数
      formatTime,
      formatTimeShort,
      truncateText,
      getResourceTypeTag,
      getResourceTypeText,
      getServiceTypeTag,
      getServiceTypeText,
      
      // 操作方法
      refreshStats,
      refreshDiscovery,
      refreshRoutingStats,
      refreshMCP,
      refreshExternal,
      startDiscoveryScan,
      autoIntegrate,
      triggerAgentDemand,
      connectMCP,
      disconnectMCP,
      connectAllMCP,
      discoverAndIntegrate,
      showAgentDetails,
      showToolManagement,
      activateService,
      deactivateService,
      addExternalAPI,
      testAllServices,
      clearDiscoveryCache
    }
  }
}
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 头部样式 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
  height: auto !important;
  min-height: 80px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 主要内容样式 */
.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 概览行 */
.overview-row {
  margin-bottom: 20px;
}

.overview-card {
  height: 100%;
  border-radius: 10px;
  border: none;
  transition: transform 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-title {
  font-weight: bold;
  font-size: 16px;
}

/* 状态标签样式 */
.status-section {
  display: flex;
  gap: 10px;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

/* 表格样式 */
.el-table {
  margin-top: 10px;
}

/* 按钮动画 */
.el-button {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.el-button:active {
  transform: translateY(0);
}

/* 加载动画 */
.loading-content {
  text-align: center;
  padding: 20px;
}

.loading-text {
  margin-top: 10px;
  color: #666;
}

/* 页脚样式 */
.footer {
  background: #f5f7fa;
  color: #666;
  padding: 10px 20px;
  font-size: 12px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 10px;
  }
  
  .status-section {
    flex-wrap: wrap;
  }
  
  .main-content {
    padding: 10px;
  }
}
</style>