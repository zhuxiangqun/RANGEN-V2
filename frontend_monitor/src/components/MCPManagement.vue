<template>
  <div class="mcp-management">
    <el-alert 
      v-if="error" 
      :title="error" 
      type="error" 
      show-icon 
      @close="error = ''"
      style="margin-bottom: 20px;"
    />
    
    <!-- MCP系统状态 -->
    <el-card class="mcp-status-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">📡 MCP系统状态</span>
          <div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh" 
              @click="refreshStatus"
              :loading="loading.status"
            >
              刷新状态
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="status" class="status-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="系统状态">
            <el-tag :type="status.enabled ? 'success' : 'danger'">
              {{ status.enabled ? '已启用' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="服务器数量">
            <el-tag type="info">{{ status.server_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="运行中服务器">
            <el-tag :type="status.running_server_count > 0 ? 'success' : 'warning'">
              {{ status.running_server_count }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="配置加载">
            <el-tag :type="status.config_loaded ? 'success' : 'warning'">
              {{ status.config_loaded ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 健康检查 -->
        <div class="health-check" style="margin-top: 20px;">
          <el-button 
            type="info" 
            size="small" 
            @click="checkHealth"
            :loading="loading.health"
          >
            健康检查
          </el-button>
          <span v-if="health" style="margin-left: 10px;">
            状态: 
            <el-tag :type="health.status === 'healthy' ? 'success' : 'danger'">
              {{ health.status }}
            </el-tag>
            <span v-if="health.issues" style="color: #f56c6c; margin-left: 10px;">
              问题: {{ health.issues.join(', ') }}
            </span>
          </span>
        </div>
      </div>
      <div v-else>
        <el-skeleton :rows="3" animated />
      </div>
    </el-card>
    
    <!-- MCP服务器列表 -->
    <el-card class="servers-card" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">🖥️ MCP服务器管理</span>
          <div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh" 
              @click="refreshServers"
              :loading="loading.servers"
            >
              刷新服务器列表
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="servers.length > 0">
        <el-table :data="servers" style="width: 100%">
          <el-table-column prop="name" label="服务器名称" width="180">
            <template #default="scope">
              <strong>{{ scope.row.name }}</strong>
              <div class="server-description">{{ scope.row.description }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag 
                :type="getStatusTagType(scope.row.status)"
                size="small"
              >
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="transport" label="传输方式" width="120">
            <template #default="scope">
              <el-tag type="info" size="small">{{ scope.row.transport }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="pid" label="进程ID" width="100">
            <template #default="scope">
              <span v-if="scope.row.pid">{{ scope.row.pid }}</span>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="http_endpoint" label="HTTP端点">
            <template #default="scope">
              <span v-if="scope.row.http_endpoint">
                <el-link type="primary" :href="scope.row.http_endpoint" target="_blank">
                  {{ scope.row.http_endpoint }}
                </el-link>
              </span>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240">
            <template #default="scope">
              <div class="server-actions">
                <el-button 
                  v-if="scope.row.status !== 'running'"
                  type="success" 
                  size="small" 
                  @click="startServer(scope.row.name)"
                  :loading="loading.serverActions[scope.row.name] === 'start'"
                >
                  启动
                </el-button>
                <el-button 
                  v-if="scope.row.status === 'running'"
                  type="warning" 
                  size="small" 
                  @click="stopServer(scope.row.name)"
                  :loading="loading.serverActions[scope.row.name] === 'stop'"
                >
                  停止
                </el-button>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="restartServer(scope.row.name)"
                  :loading="loading.serverActions[scope.row.name] === 'restart'"
                >
                  重启
                </el-button>
                <el-button 
                  type="info" 
                  size="small" 
                  @click="showServerDetails(scope.row)"
                >
                  详情
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 服务器统计 -->
        <div class="server-stats" style="margin-top: 20px;">
          <el-descriptions :column="4" border>
            <el-descriptions-item label="总计">{{ servers.length }}</el-descriptions-item>
            <el-descriptions-item label="运行中">
              {{ runningServersCount }}
            </el-descriptions-item>
            <el-descriptions-item label="停止">
              {{ stoppedServersCount }}
            </el-descriptions-item>
            <el-descriptions-item label="错误">
              {{ errorServersCount }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      <div v-else>
        <el-empty description="暂无MCP服务器" />
      </div>
    </el-card>
    
    <!-- MCP配置 -->
    <el-card class="config-card" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">⚙️ MCP配置</span>
          <div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh" 
              @click="refreshConfig"
              :loading="loading.config"
            >
              刷新配置
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="config">
        <el-collapse v-model="activeConfigPanel">
          <el-collapse-item title="基础配置" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="启用状态">
                <el-tag :type="config.enabled ? 'success' : 'danger'">
                  {{ config.enabled ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="日志级别">
                <el-tag>{{ config.log_level }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-collapse-item>
          <el-collapse-item title="集成配置" name="integration">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="自动启动服务器">
                <el-tag :type="config.integration?.auto_start_servers ? 'success' : 'warning'">
                  {{ config.integration?.auto_start_servers ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="自动注册工具">
                <el-tag :type="config.integration?.auto_register_tools ? 'success' : 'warning'">
                  {{ config.integration?.auto_register_tools ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-collapse-item>
        </el-collapse>
      </div>
      <div v-else>
        <el-skeleton :rows="2" animated />
      </div>
    </el-card>
    
    <!-- 服务器详情对话框 -->
    <el-dialog
      v-model="showServerDetailDialog"
      :title="`服务器详情: ${selectedServer?.name}`"
      width="600px"
    >
      <div v-if="selectedServer">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ selectedServer.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedServer.description }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedServer.status)">
              {{ selectedServer.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="传输方式">
            {{ selectedServer.transport }}
          </el-descriptions-item>
          <el-descriptions-item label="启用状态">
            <el-tag :type="selectedServer.enabled ? 'success' : 'danger'">
              {{ selectedServer.enabled ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进程ID">
            {{ selectedServer.pid || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="启动时间">
            {{ selectedServer.start_time ? formatDate(selectedServer.start_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="HTTP端点">
            {{ selectedServer.http_endpoint || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求计数">
            {{ selectedServer.request_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="错误计数">
            {{ selectedServer.error_count || 0 }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showServerDetailDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '../services/api'

// 响应式数据
const status = ref(null)
const servers = ref([])
const config = ref(null)
const health = ref(null)
const error = ref('')
const loading = ref({
  status: false,
  servers: false,
  config: false,
  health: false,
  serverActions: {}
})

const showServerDetailDialog = ref(false)
const selectedServer = ref(null)
const activeConfigPanel = ref(['basic', 'integration'])

// 计算属性
const runningServersCount = computed(() => {
  return servers.value.filter(s => s.status === 'running').length
})

const stoppedServersCount = computed(() => {
  return servers.value.filter(s => s.status === 'stopped').length
})

const errorServersCount = computed(() => {
  return servers.value.filter(s => s.status === 'error').length
})

// 方法
const getStatusTagType = (status) => {
  switch (status) {
    case 'running': return 'success'
    case 'stopped': return 'info'
    case 'error': return 'danger'
    case 'starting': return 'warning'
    default: return 'info'
  }
}

const formatDate = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp * 1000).toLocaleString()
}

// API调用
const refreshStatus = async () => {
  try {
    loading.value.status = true
    const data = await apiService.getMCPStatus()
    status.value = data
    error.value = ''
  } catch (err) {
    error.value = `获取MCP状态失败: ${err.message}`
    console.error('获取MCP状态失败:', err)
  } finally {
    loading.value.status = false
  }
}

const refreshServers = async () => {
  try {
    loading.value.servers = true
    const data = await apiService.getMCPServers()
    servers.value = data
    error.value = ''
  } catch (err) {
    error.value = `获取服务器列表失败: ${err.message}`
    console.error('获取服务器列表失败:', err)
  } finally {
    loading.value.servers = false
  }
}

const refreshConfig = async () => {
  try {
    loading.value.config = true
    const data = await apiService.getMCPConfig()
    config.value = data
    error.value = ''
  } catch (err) {
    error.value = `获取配置失败: ${err.message}`
    console.error('获取配置失败:', err)
  } finally {
    loading.value.config = false
  }
}

const checkHealth = async () => {
  try {
    loading.value.health = true
    const data = await apiService.getMCPHealth()
    health.value = data
    error.value = ''
  } catch (err) {
    error.value = `健康检查失败: ${err.message}`
    console.error('健康检查失败:', err)
  } finally {
    loading.value.health = false
  }
}

const startServer = async (serverName) => {
  try {
    loading.value.serverActions[serverName] = 'start'
    const data = await apiService.startMCPServer(serverName)
    
    if (data.success) {
      ElMessage.success(data.message)
      // 刷新服务器列表
      await refreshServers()
      await refreshStatus()
    } else {
      ElMessage.error(`启动失败: ${data.message}`)
    }
  } catch (err) {
    ElMessage.error(`启动服务器失败: ${err.message}`)
  } finally {
    loading.value.serverActions[serverName] = false
  }
}

const stopServer = async (serverName) => {
  try {
    loading.value.serverActions[serverName] = 'stop'
    const data = await apiService.stopMCPServer(serverName)
    
    if (data.success) {
      ElMessage.success(data.message)
      // 刷新服务器列表
      await refreshServers()
      await refreshStatus()
    } else {
      ElMessage.error(`停止失败: ${data.message}`)
    }
  } catch (err) {
    ElMessage.error(`停止服务器失败: ${err.message}`)
  } finally {
    loading.value.serverActions[serverName] = false
  }
}

const restartServer = async (serverName) => {
  try {
    loading.value.serverActions[serverName] = 'restart'
    const data = await apiService.restartMCPServer(serverName)
    
    if (data.success) {
      ElMessage.success(data.message)
      // 刷新服务器列表
      await refreshServers()
      await refreshStatus()
    } else {
      ElMessage.error(`重启失败: ${data.message}`)
    }
  } catch (err) {
    ElMessage.error(`重启服务器失败: ${err.message}`)
  } finally {
    loading.value.serverActions[serverName] = false
  }
}

const showServerDetails = (server) => {
  selectedServer.value = server
  showServerDetailDialog.value = true
}

// 初始化加载数据
const loadAllData = async () => {
  await Promise.all([
    refreshStatus(),
    refreshServers(),
    refreshConfig()
  ])
}

// 生命周期
onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.mcp-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: bold;
  font-size: 16px;
}

.server-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.server-actions {
  display: flex;
  gap: 8px;
}

.status-content {
  padding: 10px;
}

.health-check {
  display: flex;
  align-items: center;
  margin-top: 15px;
}
</style>