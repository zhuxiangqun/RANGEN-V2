<template>
  <div class="external-mcp-management">
    <!-- 错误提示 -->
    <el-alert 
      v-if="error" 
      :title="error" 
      type="error" 
      show-icon 
      @close="error = ''"
      style="margin-bottom: 20px;"
    />
    
    <!-- 成功提示 -->
    <el-alert 
      v-if="successMessage" 
      :title="successMessage" 
      type="success" 
      show-icon 
      @close="successMessage = ''"
      style="margin-bottom: 20px;"
    />
    
    <!-- 外部集成概览 -->
    <el-card class="overview-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">🌐 外部集成概览</span>
          <div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh" 
              @click="refreshOverview"
              :loading="loading.overview"
            >
              刷新概览
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              :icon="Plus" 
              @click="showAddServerDialog = true"
              style="margin-left: 10px;"
            >
              添加外部服务器
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="overview" class="overview-content">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-value">{{ overview.mcp_servers || 0 }}</div>
                <div class="stat-label">MCP服务器</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-value">{{ overview.external_tools || 0 }}</div>
                <div class="stat-label">外部工具</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-value">{{ overview.mcp_skills || 0 }}</div>
                <div class="stat-label">MCP技能</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-value">{{ overview.total_integrations || 0 }}</div>
                <div class="stat-label">总集成数</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      <div v-else>
        <el-skeleton :rows="2" animated />
      </div>
    </el-card>
    
    <!-- 外部MCP服务器列表 -->
    <el-card class="mcp-servers-card" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">🖥️ 外部MCP服务器管理</span>
          <div>
            <el-button 
              type="primary" 
              size="small" 
              :icon="Refresh" 
              @click="refreshMCPIntegrations"
              :loading="loading.integrations"
            >
              刷新服务器列表
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              :icon="Upload" 
              @click="showImportDialog = true"
              style="margin-left: 10px;"
            >
              导入配置
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="mcpIntegrations.length > 0">
        <el-table :data="mcpIntegrations" style="width: 100%" stripe>
          <el-table-column prop="name" label="服务器名称" width="180" />
          <el-table-column prop="url" label="地址/命令" width="250">
            <template #default="{ row }">
              <span v-if="row.url">{{ row.url }}</span>
              <span v-else-if="row.command">{{ row.command.join(' ') }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="transport" label="传输协议" width="120">
            <template #default="{ row }">
              <el-tag :type="row.transport === 'http' ? 'primary' : 'success'" size="small">
                {{ row.transport || 'stdio' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="server_type" label="服务器类型" width="120">
            <template #default="{ row }">
              <el-tag :type="row.server_type === 'local' ? 'success' : 'warning'" size="small">
                {{ row.server_type === 'local' ? '本地' : '外部' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'warning'" size="small">
                {{ row.enabled ? '已启用' : '已禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="tools_count" label="工具数量" width="100">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ row.tools_count || 0 }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="connected" label="连接状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.connected ? 'success' : 'danger'" size="small">
                {{ row.connected ? '已连接' : '未连接' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="320">
            <template #default="{ row }">
              <el-button-group>
                <el-button 
                  size="small" 
                  @click="connectToMCP(row.name)"
                  :disabled="row.connected"
                  :loading="loading.connections[row.name]"
                >
                  连接
                </el-button>
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="showToolsForServer(row)"
                  :loading="loading.tools[row.name]"
                >
                  查看工具
                </el-button>
                <el-button 
                  size="small" 
                  type="info" 
                  @click="removeIntegration(row.id)"
                  :loading="loading.removals[row.id]"
                >
                  移除
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else>
        <el-empty description="暂无外部MCP服务器">
          <el-button type="primary" @click="showAddServerDialog = true">
            添加第一个服务器
          </el-button>
        </el-empty>
      </div>
    </el-card>
    
    <!-- MCP工具注册面板 -->
    <el-card v-if="selectedServer" class="tools-panel" shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span class="card-title">🔧 MCP工具管理 - {{ selectedServer.name }}</span>
          <div>
            <el-button 
              size="small" 
              :icon="Back" 
              @click="selectedServer = null"
            >
              返回服务器列表
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              :icon="Refresh" 
              @click="refreshServerTools"
              :loading="loading.serverTools"
              style="margin-left: 10px;"
            >
              刷新工具列表
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="serverTools.length > 0">
        <el-alert
          title="工具注册说明"
          type="info"
          description="选择需要注册到系统的工具，系统将自动创建工具记录并可选地创建对应的Skill"
          show-icon
          style="margin-bottom: 20px;"
        />
        
        <el-table 
          :data="serverTools" 
          style="width: 100%" 
          stripe
          @selection-change="handleToolSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="工具名称" width="200" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="input_schema" label="输入参数" width="150">
            <template #default="{ row }">
              <el-tag v-if="row.input_schema" type="info" size="small">
                {{ Object.keys(row.input_schema || {}).length }} 个参数
              </el-tag>
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>
          <el-table-column prop="registered" label="注册状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.registered" type="success" size="small">
                已注册
              </el-tag>
              <el-tag v-else type="warning" size="small">
                未注册
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="tool-actions" style="margin-top: 20px; text-align: right;">
          <el-checkbox v-model="autoCreateSkill" label="自动创建Skill" />
          <el-checkbox v-model="autoMapToExistingSkill" label="映射到现有Skill" style="margin-left: 20px;" />
          <el-button 
            type="primary" 
            :icon="Check" 
            @click="registerSelectedTools"
            :disabled="selectedTools.length === 0"
            :loading="loading.toolRegistration"
            style="margin-left: 20px;"
          >
            注册所选工具 ({{ selectedTools.length }})
          </el-button>
        </div>
      </div>
      <div v-else-if="loading.serverTools">
        <el-skeleton :rows="4" animated />
      </div>
      <div v-else>
        <el-empty description="该服务器没有可用的工具或未连接">
          <el-button type="primary" @click="connectToMCP(selectedServer.name)">
            连接服务器
          </el-button>
        </el-empty>
      </div>
    </el-card>
    
    <!-- 添加外部MCP服务器对话框 -->
    <el-dialog
      v-model="showAddServerDialog"
      title="添加外部MCP服务器"
      width="600px"
      :before-close="handleAddServerDialogClose"
    >
      <el-form 
        ref="addServerFormRef" 
        :model="addServerForm" 
        :rules="addServerRules" 
        label-width="120px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="addServerForm.name" placeholder="例如: weather-service" />
        </el-form-item>
        
        <el-form-item label="传输协议" prop="transport">
          <el-radio-group v-model="addServerForm.transport">
            <el-radio label="http">HTTP/HTTPS</el-radio>
            <el-radio label="stdio">STDIO (命令行)</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="addServerForm.transport === 'http'" label="服务器地址" prop="url">
          <el-input v-model="addServerForm.url" placeholder="例如: http://localhost:3000" />
        </el-form-item>
        
        <el-form-item v-else-if="addServerForm.transport === 'stdio'" label="命令" prop="command">
          <el-input v-model="addServerForm.command" placeholder="例如: python /path/to/server.py" />
          <div class="form-hint">多个参数用空格分隔，会自动解析为数组</div>
        </el-form-item>
        
        <el-form-item label="服务器类型" prop="server_type">
          <el-radio-group v-model="addServerForm.server_type">
            <el-radio label="local">本地MCP服务器</el-radio>
            <el-radio label="external">外部MCP服务器</el-radio>
          </el-radio-group>
          <div class="form-hint">本地服务器部署在相同网络环境，外部服务器通过公网访问</div>
        </el-form-item>
        
        <el-form-item label="自动连接" prop="auto_connect">
          <el-switch v-model="addServerForm.auto_connect" />
          <div class="form-hint">添加后自动连接到服务器</div>
        </el-form-item>
        
        <el-form-item label="自动注册工具" prop="auto_register_tools">
          <el-switch v-model="addServerForm.auto_register_tools" />
          <div class="form-hint">连接后自动注册所有工具</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddServerDialog = false">取消</el-button>
        <el-button type="primary" @click="addMCPIntegration" :loading="loading.addServer">
          添加服务器
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 导入配置对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入外部集成配置"
      width="500px"
    >
      <el-tabs v-model="activeImportTab">
        <el-tab-pane label="YAML文件" name="yaml">
          <div class="import-tab-content">
            <el-upload
              class="upload-demo"
              drag
              :action="importYAMLAction"
              :headers="uploadHeaders"
              :on-success="handleYAMLImportSuccess"
              :on-error="handleImportError"
              :before-upload="beforeYAMLUpload"
              accept=".yaml,.yml"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将YAML文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持YAML格式的MCP服务器配置
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>
        <el-tab-pane label="JSON文件" name="json">
          <div class="import-tab-content">
            <el-upload
              class="upload-demo"
              drag
              :action="importJSONAction"
              :headers="uploadHeaders"
              :on-success="handleJSONImportSuccess"
              :on-error="handleImportError"
              :before-upload="beforeJSONUpload"
              accept=".json"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将JSON文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持JSON格式的MCP服务器配置
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>
        <el-tab-pane label="OpenAI GPTs" name="openai">
          <div class="import-tab-content">
            <el-form :model="openaiImportForm" label-width="120px">
              <el-form-item label="GPTs ID" prop="gpts_id">
                <el-input v-model="openaiImportForm.gpts_id" placeholder="例如: gpt-xxxxxx" />
              </el-form-item>
              <el-form-item label="API Key" prop="api_key">
                <el-input v-model="openaiImportForm.api_key" type="password" placeholder="输入OpenAI API Key" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="importOpenAIAgent" :loading="loading.openaiImport">
                  导入GPTs
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Plus,
  Upload,
  Back,
  Check,
  UploadFilled
} from '@element-plus/icons-vue'
import { apiService } from '../services/api'

// 响应式数据
const error = ref('')
const successMessage = ref('')
const loading = reactive({
  overview: false,
  integrations: false,
  addServer: false,
  serverTools: false,
  toolRegistration: false,
  connections: {},
  tools: {},
  removals: {},
  openaiImport: false
})

const overview = ref(null)
const mcpIntegrations = ref([])
const selectedServer = ref(null)
const serverTools = ref([])
const selectedTools = ref([])
const autoCreateSkill = ref(true)
const autoMapToExistingSkill = ref(true)

// 对话框控制
const showAddServerDialog = ref(false)
const showImportDialog = ref(false)
const activeImportTab = ref('yaml')

// 表单数据
const addServerForm = reactive({
  name: '',
  transport: 'http',
  url: '',
  command: '',
  server_type: 'local',
  auto_connect: true,
  auto_register_tools: true
})

const addServerFormRef = ref()
const addServerRules = {
  name: [
    { required: true, message: '请输入服务器名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在2到50个字符', trigger: 'blur' }
  ],
  transport: [
    { required: true, message: '请选择传输协议', trigger: 'change' }
  ],
  url: [
    { 
      required: true, 
      message: '请输入服务器地址',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (addServerForm.transport === 'http' && !value) {
          callback(new Error('HTTP协议需要服务器地址'))
        } else {
          callback()
        }
      }
    }
  ]
}

const openaiImportForm = reactive({
  gpts_id: '',
  api_key: ''
})

// 计算属性
const importYAMLAction = computed(() => {
  return '/api/external/import/yaml'
})

const importJSONAction = computed(() => {
  return '/api/external/import/json'
})

const uploadHeaders = computed(() => {
  return {
    'Accept': 'application/json'
  }
})

// 方法
const refreshOverview = async () => {
  loading.overview = true
  try {
    // 获取外部集成列表
    const integrations = await apiService.getExternalIntegrations()
    
    // 计算概览数据
    const mcpServers = Array.isArray(integrations) ? integrations.length : 0
    
    overview.value = {
      mcp_servers: mcpServers,
      external_tools: 0, // 需要从服务器获取工具数量，这里暂时设为0
      mcp_skills: 0, // 需要查询数据库中的Skill数量，这里暂时设为0
      total_integrations: mcpServers
    }
  } catch (err) {
    console.error('刷新概览失败:', err)
    error.value = `刷新概览失败: ${err.message || err}`
    // 使用默认数据
    overview.value = {
      mcp_servers: 0,
      external_tools: 0,
      mcp_skills: 0,
      total_integrations: 0
    }
  } finally {
    loading.overview = false
  }
}

const refreshMCPIntegrations = async () => {
  loading.integrations = true
  try {
    const integrations = await apiService.getExternalIntegrations()
    
    // 转换API响应到组件期望的格式
    mcpIntegrations.value = Array.isArray(integrations) ? integrations.map(integration => ({
      id: integration.id || integration.name,
      name: integration.name,
      url: integration.url || '',
      command: integration.command || [],
      transport: integration.transport || 'http',
      server_type: integration.server_type || 'external', // 默认为外部服务器
      enabled: integration.enabled !== false, // 默认为启用
      tools_count: integration.tools_count || 0,
      connected: integration.connected || false
    })) : []
  } catch (err) {
    console.error('刷新MCP集成失败:', err)
    error.value = `刷新MCP集成失败: ${err.message || err}`
    mcpIntegrations.value = []
  } finally {
    loading.integrations = false
  }
}

const connectToMCP = async (serverName) => {
  loading.connections[serverName] = true
  try {
    const response = await apiService.connectExternalMCP(serverName)
    ElMessage.success(`成功连接到MCP服务器: ${serverName}`)
    
    // 刷新服务器列表
    await refreshMCPIntegrations()
    
    // 如果当前选中了该服务器，刷新工具列表
    if (selectedServer.value && selectedServer.value.name === serverName) {
      await refreshServerTools()
    }
  } catch (err) {
    console.error('连接MCP服务器失败:', err)
    ElMessage.error(`连接失败: ${err.message || err}`)
  } finally {
    loading.connections[serverName] = false
  }
}

const showToolsForServer = async (server) => {
  selectedServer.value = server
  await refreshServerTools()
}

const refreshServerTools = async () => {
  if (!selectedServer.value) return
  
  loading.serverTools = true
  try {
    const response = await apiService.listExternalMCPTools(selectedServer.value.name)
    serverTools.value = response.tools || []
    
    // 标记已注册的工具
    for (const tool of serverTools.value) {
      // 检查工具是否已在系统中注册
      const toolId = `mcp_${selectedServer.value.name}_${tool.name}`
      const exists = await apiService.checkToolExists(toolId)
      tool.registered = exists
    }
  } catch (err) {
    console.error('获取工具列表失败:', err)
    error.value = `获取工具列表失败: ${err.message || err}`
    serverTools.value = []
  } finally {
    loading.serverTools = false
  }
}

const handleToolSelectionChange = (selection) => {
  selectedTools.value = selection
}

const registerSelectedTools = async () => {
  if (selectedTools.value.length === 0) return
  
  loading.toolRegistration = true
  try {
    const registrations = []
    
    for (const tool of selectedTools.value) {
      // 创建MCP工具记录
      const serverType = selectedServer.value.server_type || 'external'
      const source = serverType === 'local' ? 'local_mcp' : 'external_mcp'
      const result = await apiService.createMCPTool(
        selectedServer.value.name,
        tool.name,
        tool.description,
        source
      )
      registrations.push(result)
      
      // 可选：自动创建Skill
      if (autoCreateSkill.value) {
        const skillName = `mcp-${selectedServer.value.name}-${tool.name}`
        const skillDescription = `MCP工具技能: ${tool.description}`
        
        try {
          await apiService.createSkill({
            name: skillName,
            description: skillDescription,
            tools: [result.tool_id]
          })
          console.log(`已创建Skill: ${skillName}`)
        } catch (skillErr) {
          console.warn(`创建Skill失败: ${skillErr.message}`)
          // 继续注册其他工具
        }
      }
    }
    
    ElMessage.success(`成功注册 ${registrations.length} 个工具`)
    
    // 刷新工具列表，更新注册状态
    await refreshServerTools()
    
    // 清空选择
    selectedTools.value = []
    
  } catch (err) {
    console.error('注册工具失败:', err)
    ElMessage.error(`注册工具失败: ${err.message || err}`)
  } finally {
    loading.toolRegistration = false
  }
}

const removeIntegration = async (integrationId) => {
  try {
    await ElMessageBox.confirm(
      '确定要移除这个集成吗？移除后需要重新添加才能使用。',
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.removals[integrationId] = true
    await apiService.removeExternalIntegration(integrationId)
    ElMessage.success('集成已移除')
    
    // 刷新列表
    await refreshMCPIntegrations()
    
  } catch (err) {
    if (err !== 'cancel') {
      console.error('移除集成失败:', err)
      ElMessage.error(`移除失败: ${err.message || err}`)
    }
  } finally {
    loading.removals[integrationId] = false
  }
}

const addMCPIntegration = async () => {
  if (!addServerFormRef.value) return
  
  await addServerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.addServer = true
    try {
      // 准备数据
      const data = {
        name: addServerForm.name,
        transport: addServerForm.transport,
        server_type: addServerForm.server_type
      }
      
      if (addServerForm.transport === 'http') {
        data.url = addServerForm.url
      } else if (addServerForm.transport === 'stdio') {
        data.command = addServerForm.command.split(' ').filter(cmd => cmd.trim())
      }
      
      // 添加MCP端点
      const response = await apiService.addExternalMCPEndpoint(data)
      ElMessage.success(`成功添加MCP服务器: ${addServerForm.name}`)
      
      // 关闭对话框
      showAddServerDialog.value = false
      
      // 如果设置了自动连接，连接服务器
      if (addServerForm.auto_connect) {
        setTimeout(() => {
          connectToMCP(addServerForm.name)
        }, 500)
      }
      
      // 刷新列表
      await refreshMCPIntegrations()
      
    } catch (err) {
      console.error('添加MCP服务器失败:', err)
      error.value = `添加失败: ${err.message || err}`
    } finally {
      loading.addServer = false
    }
  })
}

const handleAddServerDialogClose = (done) => {
  // 重置表单
  addServerForm.name = ''
  addServerForm.transport = 'http'
  addServerForm.url = ''
  addServerForm.command = ''
  addServerForm.server_type = 'local'
  addServerForm.auto_connect = true
  addServerForm.auto_register_tools = true
  
  if (addServerFormRef.value) {
    addServerFormRef.value.resetFields()
  }
  
  done()
}

const beforeYAMLUpload = (file) => {
  const isYAML = file.name.endsWith('.yaml') || file.name.endsWith('.yml')
  if (!isYAML) {
    ElMessage.error('只能上传YAML格式的文件!')
    return false
  }
  return true
}

const beforeJSONUpload = (file) => {
  const isJSON = file.name.endsWith('.json')
  if (!isJSON) {
    ElMessage.error('只能上传JSON格式的文件!')
    return false
  }
  return true
}

const handleYAMLImportSuccess = (response) => {
  ElMessage.success('YAML配置导入成功')
  showImportDialog.value = false
  refreshMCPIntegrations()
}

const handleJSONImportSuccess = (response) => {
  ElMessage.success('JSON配置导入成功')
  showImportDialog.value = false
  refreshMCPIntegrations()
}

const handleImportError = (err) => {
  console.error('导入失败:', err)
  ElMessage.error(`导入失败: ${err.message || '未知错误'}`)
}

const importOpenAIAgent = async () => {
  if (!openaiImportForm.gpts_id || !openaiImportForm.api_key) {
    ElMessage.error('请填写GPTs ID和API Key')
    return
  }
  
  loading.openaiImport = true
  try {
    await apiService.importOpenAIAgent({
      gpts_id: openaiImportForm.gpts_id,
      api_key: openaiImportForm.api_key
    })
    
    ElMessage.success('OpenAI GPTs导入成功')
    showImportDialog.value = false
    openaiImportForm.gpts_id = ''
    openaiImportForm.api_key = ''
    
    // 刷新集成列表
    await refreshMCPIntegrations()
    
  } catch (err) {
    console.error('导入OpenAI GPTs失败:', err)
    ElMessage.error(`导入失败: ${err.message || err}`)
  } finally {
    loading.openaiImport = false
  }
}

// 初始化
onMounted(() => {
  refreshOverview()
  refreshMCPIntegrations()
})
</script>

<style scoped>
.external-mcp-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
}

.card-title::before {
  margin-right: 8px;
  font-size: 20px;
}

.stat-card {
  border-radius: 8px;
  transition: all 0.3s;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  text-align: center;
  padding: 24px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.text-muted {
  color: #c0c4cc;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.import-tab-content {
  padding: 10px;
}

.upload-demo {
  width: 100%;
}

.tool-actions {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.mcp-servers-card {
  margin-top: 20px;
}

.tools-panel {
  margin-top: 20px;
}
</style>