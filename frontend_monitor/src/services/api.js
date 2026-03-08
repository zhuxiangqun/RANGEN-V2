import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const apiService = {
  // 获取日志数据
  async getLogs() {
    try {
      const response = await api.get('/logs')
      return response.data
    } catch (error) {
      console.error('API调用失败:', error)
      throw error
    }
  },
  
  // 创建实时日志流（SSE）
  createLogStream(onMessage, onError) {
    const eventSource = new EventSource('/api/logs/stream')
    
    // 🚀 新增：连接打开时的处理
    eventSource.onopen = () => {
      console.log('📡 SSE连接已建立')
      // 清除重连定时器
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
      // 重置手动关闭标志（如果连接重新建立）
      isManuallyClosed = false
    }
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('解析日志流数据失败:', error)
        if (onError) onError(error)
      }
    }
    
    // 🚀 改进：跟踪手动关闭状态
    let isManuallyClosed = false
    let reconnectTimer = null
    
    // 重写 close 方法以标记手动关闭
    const originalClose = eventSource.close.bind(eventSource)
    eventSource.close = () => {
      isManuallyClosed = true
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
      originalClose()
    }
    
    eventSource.onerror = (error) => {
      // 🚀 改进：更智能的错误处理
      const readyState = eventSource.readyState
      
      // 如果用户手动关闭，不处理错误
      if (isManuallyClosed) {
        return
      }
      
      if (readyState === EventSource.CONNECTING) {
        // 正在重连，这是正常的，不记录错误
        console.log('📡 SSE正在重连...')
        return
      } else if (readyState === EventSource.OPEN) {
        // 连接已打开，但收到错误（可能是网络波动）
        // 不记录为错误，因为连接仍然有效
        return
      } else if (readyState === EventSource.CLOSED) {
        // 连接已关闭
        console.log('📡 SSE连接已关闭')
        
        // 只有在非手动关闭的情况下才尝试重连
        if (!isManuallyClosed && onError) {
          // 清除之前的定时器
          if (reconnectTimer) {
            clearTimeout(reconnectTimer)
          }
          // 延迟调用，避免频繁重连
          reconnectTimer = setTimeout(() => {
            // 再次检查连接状态和手动关闭标志
            if (eventSource.readyState === EventSource.CLOSED && !isManuallyClosed) {
              console.log('📡 SSE连接异常关闭，尝试重连...')
              onError(error)
            }
          }, 2000)
        }
      }
    }
    
    return eventSource
  },
  
  // 🚀 改进：运行核心系统（返回任务ID）
  async runCoreSystem(sampleCount = 10) {
    const response = await api.post('/core-system/run', {
      sample_count: sampleCount
    })
    return response.data
  },
  
  // 🚀 改进：运行评测（返回任务ID）
  async runEvaluation() {
    try {
      const response = await api.post('/evaluation/run', {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      // 提供更详细的错误信息
      if (error.response) {
        // 服务器返回了错误响应
        throw new Error(`评测失败: ${error.response.status} - ${error.response.data?.error || error.response.statusText}`)
      } else if (error.request) {
        // 请求已发送但没有收到响应
        throw new Error('评测失败: 无法连接到服务器')
      } else {
        // 其他错误
        throw new Error(`评测失败: ${error.message}`)
      }
    }
  },
  
  // 🚀 新增：获取任务状态
  async getTaskStatus(taskId) {
    const response = await api.get(`/tasks/${taskId}`)
    return response.data
  },
  
  // 🚀 新增：取消任务
  async cancelTask(taskId) {
    const response = await api.post(`/tasks/${taskId}/cancel`)
    return response.data
  },
  
  // 获取评测结果（兼容旧接口）
  async getEvaluationResult() {
    const response = await api.get('/evaluation/result')
    return response.data
  },

  // 获取内部工具列表
  async getInternalTools() {
    try {
      const response = await api.get('/tools/internal')
      return response.data
    } catch (error) {
      console.error('获取内部工具失败:', error)
      throw error
    }
  },

  // 获取数据库工具列表（支持分页）
  async getTools(page = 1, pageSize = 10) {
    try {
      const response = await api.get('/tools', {
        params: {
          page,
          page_size: pageSize
        }
      })
      return response.data
    } catch (error) {
      console.error('获取工具列表失败:', error)
      throw error
    }
  },

  // 获取工具详情
  async getToolDetail(toolId) {
    try {
      const response = await api.get(`/tools/${toolId}`)
      return response.data
    } catch (error) {
      console.error('获取工具详情失败:', error)
      throw error
    }
  },

  // ==================== 外部集成API ====================

  // 获取所有外部集成
  async getExternalIntegrations() {
    try {
      const response = await api.get('/external/integrations')
      return response.data
    } catch (error) {
      console.error('获取外部集成失败:', error)
      throw error
    }
  },

  // 添加外部MCP端点
  async addExternalMCPEndpoint(data) {
    try {
      const response = await api.post('/external/mcp/add', data)
      return response.data
    } catch (error) {
      console.error('添加外部MCP端点失败:', error)
      throw error
    }
  },

  // 连接外部MCP端点
  async connectExternalMCP(name) {
    try {
      const response = await api.post(`/external/mcp/connect/${name}`)
      return response.data
    } catch (error) {
      console.error('连接外部MCP端点失败:', error)
      throw error
    }
  },

  // 列出外部MCP服务器工具
  async listExternalMCPTools(endpointName) {
    try {
      const response = await api.get(`/external/mcp/tools/${endpointName}`)
      return response.data
    } catch (error) {
      console.error('列出MCP工具失败:', error)
      throw error
    }
  },

  // 导入OpenAI GPTs Agent
  async importOpenAIAgent(data) {
    try {
      const response = await api.post('/external/openai/import', data)
      return response.data
    } catch (error) {
      console.error('导入OpenAI Agent失败:', error)
      throw error
    }
  },

  // 导入GitHub Copilot Agent
  async importGitHubCopilot(data) {
    try {
      const response = await api.post('/external/github/import', data)
      return response.data
    } catch (error) {
      console.error('导入GitHub Copilot失败:', error)
      throw error
    }
  },

  // 添加自定义API
  async addCustomAPI(data) {
    try {
      const response = await api.post('/external/custom-api/add', data)
      return response.data
    } catch (error) {
      console.error('添加自定义API失败:', error)
      throw error
    }
  },

  // 从YAML文件导入配置
  async importYAML(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post('/external/import/yaml', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('导入YAML配置失败:', error)
      throw error
    }
  },

  // 从JSON文件导入配置
  async importJSON(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post('/external/import/json', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('导入JSON配置失败:', error)
      throw error
    }
  },

  // 移除外部集成
  async removeExternalIntegration(integrationId) {
    try {
      const response = await api.delete(`/external/integrations/${integrationId}`)
      return response.data
    } catch (error) {
      console.error('移除外部集成失败:', error)
      throw error
    }
  },

  // ==================== Skill API ====================

  // 获取Skill列表
  async getSkills(status = null) {
    try {
      const params = status ? { status } : {}
      const response = await api.get('/skills', { params })
      return response.data
    } catch (error) {
      console.error('获取Skill列表失败:', error)
      throw error
    }
  },

  // 创建Skill
  async createSkill(data) {
    try {
      const response = await api.post('/skills', data)
      return response.data
    } catch (error) {
      console.error('创建Skill失败:', error)
      throw error
    }
  },

  // 从工具组合Skill
  async combineToolsToSkill(name, description, toolIds) {
    try {
      const response = await api.post('/skills/combine', {
        name,
        description,
        tool_ids: toolIds
      })
      return response.data
    } catch (error) {
      console.error('组合Skill失败:', error)
      throw error
    }
  },

  // 检查工具是否存在
  async checkToolExists(toolId) {
    try {
      await api.get(`/tools/${toolId}`)
      return true
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return false
      }
      throw error
    }
  },

  // 创建MCP工具
  async createMCPTool(serverName, toolName, description, source = 'mcp') {
    try {
      const toolId = `mcp_${serverName}_${toolName}`
      const response = await api.post('/tools', {
        name: toolId,
        description: description || `MCP工具: ${toolName} (来自 ${serverName})`,
        type: 'mcp',
        source: source
      })
      return response.data
    } catch (error) {
      console.error('创建MCP工具失败:', error)
      throw error
    }
  },

  // ==================== 路由监控API ====================

  // 获取路由统计信息
  async getRoutingStatistics() {
    try {
      const response = await api.get('/routing/statistics')
      return response.data
    } catch (error) {
      console.error('获取路由统计失败:', error)
      throw error
    }
  },

  // 获取最近路由决策
  async getRecentRoutingDecisions(limit = 20, offset = 0) {
    try {
      const response = await api.get('/routing/decisions/recent', {
        params: { limit, offset }
      })
      return response.data
    } catch (error) {
      console.error('获取最近路由决策失败:', error)
      throw error
    }
  },

  // 获取网络健康状态
  async getNetworkHealth() {
    try {
      const response = await api.get('/routing/network/health')
      return response.data
    } catch (error) {
      console.error('获取网络健康状态失败:', error)
      throw error
    }
  },

  // 清除路由决策
  async clearRoutingDecisions() {
    try {
      const response = await api.post('/routing/decisions/clear')
      return response.data
    } catch (error) {
      console.error('清除路由决策失败:', error)
      throw error
    }
  }
}

export default apiService;

