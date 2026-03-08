<template>
  <div class="tool-management">
    <div class="header">
      <h2>🔧 工具管理</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Refresh" @click="refreshTools">
          刷新工具列表
        </el-button>
        <el-switch
          v-model="showInternalTools"
          active-text="内部工具"
          inactive-text="数据库工具"
          @change="handleViewChange"
        />
        <el-input
          v-model="searchQuery"
          placeholder="搜索工具名称或描述..."
          clearable
          style="width: 300px; margin-left: 16px;"
          @input="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 内部工具视图 -->
    <div v-if="showInternalTools" class="internal-tools-view">
      <div class="stats">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ filteredTools.length }}</div>
                <div class="stat-label">工具总数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ categoryCount.retrieval || 0 }}</div>
                <div class="stat-label">检索类工具</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ categoryCount.reasoning || 0 }}</div>
                <div class="stat-label">推理类工具</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-value">{{ categoryCount.utility || 0 }}</div>
                <div class="stat-label">实用类工具</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <el-table
        :data="filteredTools"
        style="width: 100%; margin-top: 20px;"
        :loading="loading"
        stripe
      >
        <el-table-column prop="name" label="工具名称" width="200">
          <template #default="{ row }">
            <div class="tool-name">
              <el-tag type="primary" size="small">{{ getCategoryTag(row.category) }}</el-tag>
              <span style="margin-left: 8px;">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryTagType(row.category)" effect="plain">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewToolDetail(row)">详情</el-button>
            <el-button size="small" type="info" @click="testTool(row)" :disabled="!row.name">测试</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 工具详情对话框 -->
      <el-dialog
        v-model="detailDialogVisible"
        title="工具详情"
        width="600px"
      >
        <div v-if="currentTool" class="tool-detail">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="工具名称">
              <el-tag type="primary" size="small">{{ currentTool.name }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="描述">
              {{ currentTool.description }}
            </el-descriptions-item>
            <el-descriptions-item label="分类">
              <el-tag :type="getCategoryTagType(currentTool.category)" effect="plain">
                {{ getCategoryLabel(currentTool.category) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="技能映射" v-if="skillMappings[currentTool.name]">
              <div class="skill-mappings">
                <el-tag
                  v-for="skill in skillMappings[currentTool.name]"
                  :key="skill"
                  type="success"
                  size="small"
                  style="margin-right: 8px; margin-bottom: 4px;"
                >
                  {{ skill }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <template #footer>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="testTool(currentTool)" v-if="currentTool">测试工具</el-button>
        </template>
      </el-dialog>
    </div>

    <!-- 数据库工具视图 -->
    <div v-else class="database-tools-view">
      <el-alert
        title="数据库工具管理"
        type="info"
        description="这里显示从数据库管理的工具，可以查看工具状态、创建时间等信息"
        show-icon
        style="margin-bottom: 20px;"
      />
      
      <el-table
        :data="dbTools"
        style="width: 100%;"
        :loading="dbLoading"
        stripe
      >
        <el-table-column prop="id" label="ID" width="180" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'warning'" size="small">
              {{ row.status === 'active' ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" style="margin-top: 20px; text-align: right;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalTools"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '../services/api'

// 响应式数据
const showInternalTools = ref(true)
const searchQuery = ref('')
const loading = ref(false)
const dbLoading = ref(false)
const internalTools = ref([])
const dbTools = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalTools = ref(0)
const detailDialogVisible = ref(false)
const currentTool = ref(null)

// 技能映射数据（从工具技能映射系统中获取）
const skillMappings = ref({
  'rag_tool': ['知识检索', '问答生成'],
  'knowledge_retrieval': ['知识检索', '信息查询'],
  'search': ['搜索', '信息查询'],
  'web_search': ['网页搜索', '信息查询'],
  'real_search': ['真实搜索', '信息查询'],
  'reasoning': ['推理', '逻辑分析'],
  'answer_generation': ['答案生成', '文本生成'],
  'citation': ['引用生成', '文本生成'],
  'calculator': ['计算', '数学运算'],
  'multimodal': ['多模态处理', '图像分析'],
  'browser': ['浏览器自动化', '网页操作'],
  'file_read': ['文件读取', '文档处理']
})

// 计算属性
const filteredTools = computed(() => {
  if (!searchQuery.value.trim()) {
    return internalTools.value
  }
  
  const query = searchQuery.value.toLowerCase().trim()
  return internalTools.value.filter(tool => 
    tool.name.toLowerCase().includes(query) ||
    tool.description.toLowerCase().includes(query) ||
    tool.category.toLowerCase().includes(query)
  )
})

const categoryCount = computed(() => {
  const counts = {}
  internalTools.value.forEach(tool => {
    counts[tool.category] = (counts[tool.category] || 0) + 1
  })
  return counts
})

// 方法
const refreshTools = async () => {
  if (showInternalTools.value) {
    await loadInternalTools()
  } else {
    await loadDatabaseTools()
  }
}

const loadInternalTools = async () => {
  loading.value = true
  try {
    const response = await apiService.getInternalTools()
    internalTools.value = response.tools || []
    ElMessage.success(`已加载 ${internalTools.value.length} 个内部工具`)
  } catch (error) {
    console.error('加载内部工具失败:', error)
    ElMessage.error('加载内部工具失败: ' + (error.message || error))
    // 如果API失败，使用默认数据
    internalTools.value = getDefaultTools()
  } finally {
    loading.value = false
  }
}

const loadDatabaseTools = async () => {
  dbLoading.value = true
  try {
    const response = await apiService.getTools(currentPage.value, pageSize.value)
    dbTools.value = response.tools || []
    totalTools.value = response.total || 0
    ElMessage.success(`已加载 ${dbTools.value.length} 个数据库工具`)
  } catch (error) {
    console.error('加载数据库工具失败:', error)
    ElMessage.error('加载数据库工具失败: ' + (error.message || error))
    dbTools.value = []
  } finally {
    dbLoading.value = false
  }
}

const handleViewChange = (value) => {
  if (value) {
    loadInternalTools()
  } else {
    loadDatabaseTools()
  }
}

const handleSearch = () => {
  // 搜索功能通过计算属性自动处理
}

const getCategoryTag = (category) => {
  const categoryMap = {
    'retrieval': '🔍',
    'reasoning': '🧠',
    'generation': '📝',
    'utility': '🛠️'
  }
  return categoryMap[category] || '📌'
}

const getCategoryLabel = (category) => {
  const labelMap = {
    'retrieval': '检索类',
    'reasoning': '推理类',
    'generation': '生成类',
    'utility': '实用类'
  }
  return labelMap[category] || category
}

const getCategoryTagType = (category) => {
  const typeMap = {
    'retrieval': 'primary',
    'reasoning': 'success',
    'generation': 'warning',
    'utility': 'info'
  }
  return typeMap[category] || 'default'
}

const viewToolDetail = (tool) => {
  currentTool.value = tool
  detailDialogVisible.value = true
}

const testTool = (tool) => {
  ElMessage.info(`测试工具 "${tool.name}" - 功能待实现`)
  // TODO: 实现工具测试功能
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  } catch (e) {
    return dateString
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  loadDatabaseTools()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadDatabaseTools()
}

// 默认工具数据（当API不可用时使用）
const getDefaultTools = () => {
  return [
    {"name": "rag_tool", "description": "检索增强生成工具", "category": "retrieval"},
    {"name": "knowledge_retrieval", "description": "知识检索工具", "category": "retrieval"},
    {"name": "search", "description": "搜索工具", "category": "retrieval"},
    {"name": "web_search", "description": "网页搜索工具", "category": "retrieval"},
    {"name": "real_search", "description": "真实网络搜索工具", "category": "retrieval"},
    {"name": "reasoning", "description": "推理工具", "category": "reasoning"},
    {"name": "answer_generation", "description": "答案生成工具", "category": "generation"},
    {"name": "citation", "description": "引用工具", "category": "generation"},
    {"name": "calculator", "description": "计算器工具", "category": "utility"},
    {"name": "multimodal", "description": "多模态处理工具", "category": "utility"},
    {"name": "browser", "description": "浏览器自动化工具", "category": "utility"},
    {"name": "file_read", "description": "文件读取工具", "category": "utility"}
  ]
}

// 生命周期钩子
onMounted(() => {
  loadInternalTools()
})
</script>

<style scoped>
.tool-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  text-align: center;
  padding: 20px 0;
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

.tool-name {
  display: flex;
  align-items: center;
}

.skill-mappings {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tool-detail {
  padding: 10px 0;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>