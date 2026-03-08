<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-content">
        <div class="logo-section">
          <h1 class="logo">🚀 RANGEN V2 一体化体验系统</h1>
          <div class="subtitle">在一个画面中体验所有功能 | Mock模式 - 无API费用</div>
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
            <el-tag type="info" size="small">模式: Mock</el-tag>
            <span class="status-text">无API费用</span>
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
                <div class="stat-label">成功率</div>
                <div class="stat-value">{{ systemStats.successRate || '0%' }}</div>
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
                <div class="stat-label">最后发现</div>
                <div class="stat-value">{{ formatTime(discoveryStats.lastDiscovery) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">集成资源</div>
                <div class="stat-value">{{ discoveryStats.integratedCount || 0 }}</div>
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
                <div class="stat-value">{{ agentStats.activeAgents || 3 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">推理Agent</div>
                <div class="stat-value">{{ agentStats.reasoningAgent || 1 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">验证Agent</div>
                <div class="stat-value">{{ agentStats.validationAgent || 1 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">引用Agent</div>
                <div class="stat-value">{{ agentStats.citationAgent || 1 }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-button type="info" size="small" @click="showAgentDetails">查看详情</el-button>
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
                <div class="stat-value">{{ toolStats.availableTools || 15 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">MCP工具</div>
                <div class="stat-value">{{ toolStats.mcpTools || 8 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">自定义工具</div>
                <div class="stat-value">{{ toolStats.customTools || 7 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">调用次数</div>
                <div class="stat-value">{{ toolStats.totalCalls || 0 }}</div>
              </div>
            </div>
            <div class="card-footer">
              <el-button type="warning" size="small" @click="showToolManagement">管理工具</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 主要功能区域 -->
      <el-row :gutter="20" class="main-row">
        <!-- 左侧：路由监控和自动发现 -->
        <el-col :span="12">
          <el-card class="feature-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">📈 路由监控</span>
                <el-button type="primary" size="small" @click="refreshRoutingStats">刷新</el-button>
              </div>
            </template>
            <div class="feature-content">
              <div class="routing-stats">
                <div class="chart-container">
                  <div v-if="routingData.labels && routingData.labels.length > 0" class="chart-placeholder">
                    <!-- 这里可以放置ECharts图表 -->
                    <div class="chart-description">
                      <h4>路由决策分布</h4>
                      <p>技能路由: {{ routingStats.skillRoutingCount || 0 }} 次</p>
                      <p>工具路由: {{ routingStats.toolRoutingCount || 0 }} 次</p>
                      <p>本地资源: {{ routingStats.localResourceCount || 0 }} 个</p>
                      <p>外部资源: {{ routingStats.externalResourceCount || 0 }} 个</p>
                    </div>
                  </div>
                  <div v-else class="no-data">
                    暂无路由数据，等待Agent查询...
                  </div>
                </div>
                <div class="recent-decisions">
                  <h4>最近决策记录</h4>
                  <el-table :data="recentDecisions" size="small" height="200">
                    <el-table-column prop="query" label="查询内容" width="180">
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
                    <el-table-column prop="selected_resource" label="选择资源" width="120" />
                    <el-table-column prop="timestamp" label="时间" width="100">
                      <template #default="{ row }">
                        {{ formatTimeShort(row.timestamp) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="feature-card" shadow="hover" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span class="card-title">🔍 自动发现控制台</span>
                <el-button-group>
                  <el-button type="primary" size="small" @click="startDiscoveryScan">扫描</el-button>
                  <el-button type="success" size="small" @click="autoIntegrate">集成</el-button>
                  <el-button type="info" size="small" @click="refreshDiscovery">刷新</el-button>
                </el-button-group>
              </div>
            </template>
            <div class="feature-content">
              <div class="discovery-controls">
                <div class="control-section">
                  <h4>Agent需求触发</h4>
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
                
                <div class="control-section">
                  <h4>已发现资源</h4>
                  <el-table :data="discoveredResources" size="small" height="200">
                    <el-table-column prop="name" label="资源名称" width="150" />
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
                        />
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
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：MCP管理和外部集成 -->
        <el-col :span="12">
          <el-card class="feature-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">🌐 MCP服务器管理</span>
                <el-button-group>
                  <el-button type="primary" size="small" @click="refreshMCP">刷新</el-button>
                  <el-button type="success" size="small" @click="connectAllMCP">连接全部</el-button>
                </el-button-group>
              </div>
            </template>
            <div class="feature-content">
              <div class="mcp-management">
                <div class="mcp-status">
                  <h4>MCP服务器状态</h4>
                  <el-table :data="mcpServers" size="small" height="200">
                    <el-table-column prop="name" label="服务器名称" width="120" />
                    <el-table-column prop="type" label="类型" width="80">
                      <template #default="{ row }">
                        <el-tag :type="row.type === 'local' ? 'success' : 'primary'" size="small">
                          {{ row.type === 'local' ? '本地' : '外部' }}
                        </el-tag>
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
                    <el-table-column prop="tools_count" label="工具数量" width="80" />
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
                </div>
                
                <div class="mcp-health">
                  <h4>网络健康监控</h4>
                  <div class="health-grid">
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
                      <div class="health-latency">
                        延迟: {{ server.latency || '--' }}ms
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="feature-card" shadow="hover" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <span class="card-title">🔄 外部集成管理</span>
                <el-button-group>
                  <el-button type="primary" size="small" @click="refreshExternal">刷新</el-button>
                  <el-button type="success" size="small" @click="addExternalAPI">添加API</el-button>
                </el-button-group>
              </div>
            </template>
            <div class="feature-content">
              <div class="external-integration">
                <div class="external-status">
                  <h4>外部服务状态</h4>
                  <el-table :data="externalServices" size="small" height="200">
                    <el-table-column prop="name" label="服务名称" width="120" />
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
                </div>
                
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
          </el-card>
        </el-col>
      </el-row>

      <!-- 底部信息栏 -->
      <el-footer class="footer">
        <div class="footer-content">
          <div class="footer-left">
            <span>RANGEN V2 一体化体验系统 | Mock模式 | 无API费用</span>
          </div>
          <div class="footer-right">
            <span>后端: localhost:8000 | 前端: localhost:3000 | 最后更新: {{ currentTime }}</span>
          </div>
        </div>
      </el-footer>
    </el-main>

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
        <el-progress :percentage="loadingProgress" :indeterminate="loadingProgress === 0" />
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
    const loadingText = ref('')
    const agentQuery = ref('')
    const currentTime = ref('')
    
    // 模拟数据
    const routingData = ref({
      labels: ['技能路由', '工具路由', '本地资源', '外部资源'],
      datasets: [
        {
          data: [25, 15, 8, 5],
          backgroundColor: ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C']
        }
      ]
    })

    // 工具函数
    const formatTime = (timestamp) => {
      if (!timestamp) return '--'
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    }
    
    const formatTimeShort = (timestamp) => {
      if (!timestamp) return '--'
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
        'mcp_server': 'primary',
        'openai_agent': 'success',
        'github_agent': 'info',
        'custom_api': 'warning'
      }
      return typeMap[type] || 'default'
    }
    
    const getResourceTypeText = (type) => {
      const typeMap = {
        'mcp_server': 'MCP服务器',
        'openai_agent': 'OpenAI Agent',
        'github_agent': 'GitHub Agent',
        'custom_api': '自定义API'
      }
      return typeMap[type] || type
    }
    
    const getServiceTypeTag = (type) => {
      const typeMap = {
        'openai': 'success',
        'github': 'info',
        'custom': 'warning',
        'api': 'primary'
      }
      return typeMap[type] || 'default'
    }
    
    const getServiceTypeText = (type) => {
      const typeMap = {
        'openai': 'OpenAI',
        'github': 'GitHub',
        'custom': '自定义',
        'api': 'API服务'
      }
      return typeMap[type] || type
    }

    // API调用函数
    const showLoading = (text) => {
      loading.value = true
      loadingText.value = text
      loadingProgress.value = 0
    }
    
    const hideLoading = () => {
      loading.value = false
      loadingText.value = ''
      loadingProgress.value = 0
    }
    
    const updateProgress = (progress) => {
      loadingProgress.value = progress
    }

    const refreshStats = async () => {
      try {
        showLoading('正在获取系统统计...')
        const response = await api.getRoutingStatistics()
        systemStats.value = response.data
        updateProgress(100)
        ElMessage.success('系统统计已更新')
      } catch (error) {
        console.error('获取系统统计失败:', error)
        ElMessage.error('获取系统统计失败')
      } finally {
        hideLoading()
      }
    }
    
    const refreshDiscovery = async () => {
      try {
        showLoading('正在获取自动发现状态...')
        const [statusRes, resourcesRes] = await Promise.all([
          api.getAutoDiscoveryStatus(),
          api.getDiscoveredResources()
        ])
        discoveryStats.value = statusRes.data
        discoveredResources.value = resourcesRes.data.map(resource => ({
          ...resource,
          integrated: resource.confidence > 0.5 // 模拟集成状态
        }))
        updateProgress(100)
        ElMessage.success('自动发现信息已更新')
      } catch (error) {
        console.error('获取自动发现信息失败:', error)
        ElMessage.error('获取自动发现信息失败')
      } finally {
        hideLoading()
      }
    }
    
    const refreshRoutingStats = async () => {
      try {
        showLoading('正在获取路由监控数据...')
        const response = await api.getRoutingStatistics()
        routingStats.value = response.data
        
        // 模拟最近决策数据
        recentDecisions.value = [
          { query: '帮我写Python代码调试程序', decision_type: 'skill', selected_resource: 'coding_assistant', timestamp: new Date().toISOString() },
          { query: '研究人工智能最新进展', decision_type: 'skill', selected_resource: 'research_assistant', timestamp: new Date(Date.now() - 300000).toISOString() },
          { query: '翻译英文文档', decision_type: 'tool', selected_resource: 'translation_tool', timestamp: new Date(Date.now() - 600000).toISOString() },
          { query: '搜索GitHub项目', decision_type: 'tool', selected_resource: 'github_search', timestamp: new Date(Date.now() - 900000).toISOString() },
          { query: '计算数学公式', decision_type: 'skill', selected_resource: 'math_assistant', timestamp: new Date(Date.now() - 1200000).toISOString() }
        ]
        
        updateProgress(100)
        ElMessage.success('路由监控数据已更新')
      } catch (error) {
        console.error('获取路由监控数据失败:', error)
        ElMessage.error('获取路由监控数据失败')
      } finally {
        hideLoading()
      }
    }
    
    const refreshMCP = async () => {
      try {
        showLoading('正在获取MCP服务器信息...')
        // 模拟MCP服务器数据
        mcpServers.value = [
          { name: '本地MCP服务器', type: 'local', status: 'connected', tools_count: 8 },
          { name: '外部MCP服务', type: 'external', status: 'disconnected', tools_count: 5 },
          { name: '工具集成服务', type: 'local', status: 'connected', tools_count: 12 },
          { name: 'API网关', type: 'external', status: 'connecting', tools_count: 3 }
        ]
        
        // 模拟网络健康数据
        networkHealth.value = [
          { name: '本地MCP', status: 'healthy', latency: 12 },
          { name: '外部API', status: 'healthy', latency: 45 },
          { name: 'GitHub', status: 'degraded', latency: 120 },
          { name: 'OpenAI', status: 'healthy', latency: 80 }
        ]
        
        updateProgress(100)
        ElMessage.success('MCP信息已更新')
      } catch (error) {
        console.error('获取MCP信息失败:', error)
        ElMessage.error('获取MCP信息失败')
      } finally {
        hideLoading()
      }
    }
    
    const refreshExternal = async () => {
      try {
        showLoading('正在获取外部服务信息...')
        // 模拟外部服务数据
        externalServices.value = [
          { id: 1, name: 'OpenAI GPT', type: 'openai', endpoint: 'https://api.openai.com/v1', status: 'active' },
          { id: 2, name: 'GitHub API', type: 'github', endpoint: 'https://api.github.com', status: 'active' },
          { id: 3, name: '自定义API', type: 'custom', endpoint: 'https://api.example.com', status: 'inactive' },
          { id: 4, name: '天气API', type: 'api', endpoint: 'https://api.weather.com', status: 'active' }
        ]
        
        updateProgress(100)
        ElMessage.success('外部服务信息已更新')
      } catch (error) {
        console.error('获取外部服务信息失败:', error)
        ElMessage.error('获取外部服务信息失败')
      } finally {
        hideLoading()
      }
    }
    
    const startDiscoveryScan = async () => {
      try {
        showLoading('正在启动自动发现扫描...')
        await api.startDiscoveryScan()
        updateProgress(50)
        
        // 模拟扫描进度
        const interval = setInterval(() => {
          if (loadingProgress.value < 90) {
            updateProgress(loadingProgress.value + 10)
          }
        }, 500)
        
        // 等待扫描完成
        setTimeout(() => {
          clearInterval(interval)
          updateProgress(100)
          hideLoading()
          ElMessage.success('自动发现扫描已启动，正在后台运行')
          refreshDiscovery()
        }, 3000)
      } catch (error) {
        console.error('启动自动发现扫描失败:', error)
        ElMessage.error('启动自动发现扫描失败')
        hideLoading()
      }
    }
    
    const autoIntegrate = async () => {
      try {
        showLoading('正在自动集成资源...')
        await api.autoIntegrateResources()
        updateProgress(50)
        
        // 模拟集成进度
        const interval = setInterval(() => {
          if (loadingProgress.value < 90) {
            updateProgress(loadingProgress.value + 10)
          }
        }, 300)
        
        // 等待集成完成
        setTimeout(() => {
          clearInterval(interval)
          updateProgress(100)
          hideLoading()
          ElMessage.success('资源自动集成完成')
          refreshDiscovery()
        }, 2000)
      } catch (error) {
        console.error('自动集成资源失败:', error)
        ElMessage.error('自动集成资源失败')
        hideLoading()
      }
    }
    
    const triggerAgentDemand = async () => {
      if (!agentQuery.value.trim()) {
        ElMessage.warning('请输入Agent需求')
        return
      }
      
      try {
        showLoading('正在分析Agent需求并触发自动发现...')
        await api.triggerAgentDemandIntegration(agentQuery.value)
        updateProgress(50)
        
        // 模拟处理进度
        const interval = setInterval(() => {
          if (loadingProgress.value < 90) {
            updateProgress(loadingProgress.value + 10)
          }
        }, 400)
        
        // 等待处理完成
        setTimeout(() => {
          clearInterval(interval)
          updateProgress(100)
          hideLoading()
          ElMessage.success(`Agent需求已触发: "${agentQuery.value}"`)
          agentQuery.value = ''
          refreshDiscovery()
        }, 2500)
      } catch (error) {
        console.error('触发Agent需求失败:', error)
        ElMessage.error('触发Agent需求失败')
        hideLoading()
      }
    }
    
    const connectMCP = async (serverName) => {
      try {
        showLoading(`正在连接MCP服务器: ${serverName}...`)
        // 模拟连接过程
        setTimeout(() => {
          const server = mcpServers.value.find(s => s.name === serverName)
          if (server) {
            server.status = 'connected'
          }
          hideLoading()
          ElMessage.success(`MCP服务器 ${serverName} 连接成功`)
        }, 1500)
      } catch (error) {
        console.error('连接MCP服务器失败:', error)
        ElMessage.error('连接MCP服务器失败')
        hideLoading()
      }
    }
    
    const disconnectMCP = async (serverName) => {
      try {
        showLoading(`正在断开MCP服务器: ${serverName}...`)
        // 模拟断开过程
        setTimeout(() => {
          const server = mcpServers.value.find(s => s.name === serverName)
          if (server) {
            server.status = 'disconnected'
          }
          hideLoading()
          ElMessage.success(`MCP服务器 ${serverName} 已断开`)
        }, 1000)
      } catch (error) {
        console.error('断开MCP服务器失败:', error)
        ElMessage.error('断开MCP服务器失败')
        hideLoading()
      }
    }
    
    const connectAllMCP = async () => {
      try {
        showLoading('正在连接所有MCP服务器...')
        // 模拟连接所有服务器
        setTimeout(() => {
          mcpServers.value.forEach(server => {
            server.status = 'connected'
          })
          hideLoading()
          ElMessage.success('所有MCP服务器连接成功')
        }, 2000)
      } catch (error) {
        console.error('连接所有MCP服务器失败:', error)
        ElMessage.error('连接所有MCP服务器失败')
        hideLoading()
      }
    }
    
    const discoverAndIntegrate = async () => {
      try {
        showLoading('正在一键发现并集成所有资源...')
        await api.discoverAndIntegrate()
        updateProgress(30)
        
        // 模拟处理进度
        const interval = setInterval(() => {
          if (loadingProgress.value < 90) {
            updateProgress(loadingProgress.value + 15)
          }
        }, 500)
        
        // 等待处理完成
        setTimeout(() => {
          clearInterval(interval)
          updateProgress(100)
          hideLoading()
          ElMessage.success('一键发现并集成完成')
          refreshDiscovery()
          refreshMCP()
          refreshExternal()
        }, 4000)
      } catch (error) {
        console.error('一键发现并集成失败:', error)
        ElMessage.error('一键发现并集成失败')
        hideLoading()
      }
    }

    // 模拟函数
    const showAgentDetails = () => {
      ElMessage.info('Agent详情功能 - 模拟演示')
    }
    
    const showToolManagement = () => {
      ElMessage.info('工具管理功能 - 模拟演示')
    }
    
    const activateService = (id) => {
      const service = externalServices.value.find(s => s.id === id)
      if (service) {
        service.status = 'active'
        ElMessage.success(`服务 ${service.name} 已激活`)
      }
    }
    
    const deactivateService = (id) => {
      const service = externalServices.value.find(s => s.id === id)
      if (service) {
        service.status = 'inactive'
        ElMessage.success(`服务 ${service.name} 已停用`)
      }
    }
    
    const addExternalAPI = () => {
      ElMessage.info('添加外部API功能 - 模拟演示')
    }
    
    const testAllServices = () => {
      showLoading('正在测试所有外部服务...')
      setTimeout(() => {
        hideLoading()
        ElMessage.success('所有外部服务测试完成')
      }, 2000)
    }
    
    const clearDiscoveryCache = () => {
      ElMessageBox.confirm(
        '确定要清除自动发现缓存吗？这将重置所有发现历史记录。',
        '清除缓存确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        showLoading('正在清除自动发现缓存...')
        setTimeout(() => {
          hideLoading()
          discoveryStats.value = {}
          discoveredResources.value = []
          ElMessage.success('自动发现缓存已清除')
        }, 1500)
      }).catch(() => {
        // 用户取消
      })
    }

    // 初始化
    const initialize = async () => {
      try {
        showLoading('正在初始化一体化体验系统...')
        
        // 并行加载所有数据
        await Promise.all([
          refreshStats(),
          refreshDiscovery(),
          refreshRoutingStats(),
          refreshMCP(),
          refreshExternal()
        ])
        
        // 模拟Agent和工具统计
        agentStats.value = {
          activeAgents: 3,
          reasoningAgent: 1,
          validationAgent: 1,
          citationAgent: 1
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
