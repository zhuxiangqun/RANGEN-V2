<template>
  <div class="reasoning-process">

    <!-- 🚀 改进：添加加载状态的骨架屏动画 -->
    <div v-if="props.samples && Array.isArray(props.samples) && props.samples.length === 0 && props.taskStatus === 'running'" class="loading-skeleton">
      <el-card v-for="n in 3" :key="n" class="skeleton-card">
        <template #header>
          <div class="skeleton-header">
            <div class="skeleton-tag"></div>
            <div class="skeleton-text"></div>
            <div class="skeleton-text short"></div>
          </div>
        </template>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </el-card>
    </div>
    
    <!-- 空状态 -->
    <el-card v-if="shouldShowEmptyState" class="empty-state">
      <el-empty :description="!props.samples || (Array.isArray(props.samples) && props.samples.length === 0) ? '暂无推理数据，请先运行核心系统' : '没有匹配的样本'" />
    </el-card>
    
    <!-- 样本列表 -->
    <div v-if="displayedSamples && Array.isArray(displayedSamples) && displayedSamples.length > 0" class="samples-container">
      <el-card
        v-for="sample in displayedSamples"
        :key="sample.id"
        class="sample-card"
        :class="{ 
          'sample-active': sample.is_running, 
          'sample-completed': sample.completed,
          'sample-error': sample.status === 'error'
        }"
        shadow="hover"
      >
        <template #header>
          <div class="sample-header" @click="toggleExpand(sample.id)">
            <div class="sample-info">
              <el-tag :type="getStatusType(sample.status)" size="large">
                {{ getStatusText(sample.status) }}
              </el-tag>
              <span class="sample-id">样本 #{{ sample.id }}</span>
              <span class="sample-time">{{ formatTime(sample.start_time) }}</span>
            </div>
            <div class="sample-metrics">
              <el-tag size="small" type="warning" v-if="sample.duration">
                ⏱️ {{ formatDuration(sample.duration) }}
              </el-tag>
              <el-tag size="small" type="success" v-if="sample.confidence">
                🎯 {{ (sample.confidence * 100).toFixed(1) }}%
              </el-tag>
              <el-tag size="small" type="info" v-if="sample.reasoning_steps_count > 0">
                📊 {{ sample.reasoning_steps_count }} 步
              </el-tag>
              <el-icon class="expand-icon" :class="{ 'expanded': isExpanded(sample.id) }">
                <ArrowDown />
              </el-icon>
            </div>
          </div>
        </template>
        
        <div v-show="isExpanded(sample.id)" class="sample-content">
          <!-- 查询部分 -->
          <div class="query-section">
            <div class="section-header">
              <h4><span>📝</span> 查询内容</h4>
            </div>
            <div class="query-content">
              <div class="query-text" v-html="formatQuery(sample.query)"></div>
            </div>
          </div>
          
          <!-- 期望答案 -->
          <div class="expected-answer-section" v-if="sample.expected_answer">
            <div class="section-header">
              <h4><span>✅</span> 期望答案</h4>
            </div>
            <div class="expected-answer-content">
              {{ sample.expected_answer }}
            </div>
          </div>
          
          <!-- 推理步骤 - 🚀 改进：TensorBoard风格可视化 -->
          <div class="steps-section" v-if="sample.steps && sample.steps.length > 0">
            <div class="section-header">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4><span>🧠</span> 推理步骤 ({{ sample.steps.length }})</h4>
                <div class="view-controls">
                  <el-radio-group v-model="viewMode" size="small">
                    <el-radio-button label="tensorboard">TensorBoard</el-radio-button>
                    <el-radio-button label="timeline">时间线</el-radio-button>
                    <el-radio-button label="graph">计算图</el-radio-button>
                    <el-radio-button label="flow">流程图</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
            </div>
            
            <!-- TensorBoard嵌入视图 -->
            <div v-if="viewMode === 'tensorboard'" class="tensorboard-embedded-view">
              <div class="tensorboard-container">
                <iframe 
                  :src="tensorboardUrl" 
                  class="tensorboard-iframe"
                  frameborder="0"
                  allowfullscreen
                ></iframe>
              </div>
              <div class="tensorboard-controls">
                <el-button @click="generateTensorBoardLogs" type="primary" :loading="generatingLogs">
                  {{ generatingLogs ? '正在生成日志...' : '生成 TensorBoard 日志' }}
                </el-button>
                <el-button @click="refreshTensorBoard" :disabled="!tensorboardUrl">
                  刷新 TensorBoard
                </el-button>
                <el-alert
                  v-if="tensorboardStatus"
                  :title="tensorboardStatus"
                  :type="tensorboardStatusType"
                  :closable="false"
                  style="margin-top: 12px;"
                />
              </div>
            </div>
            
            <!-- TensorBoard风格时间线视图 -->
            <div v-if="viewMode === 'timeline'" class="tensorboard-timeline-view">
              <div class="timeline-container" ref="timelineContainer">
                <div class="timeline-header">
                  <div class="timeline-ruler" ref="timelineRuler"></div>
                </div>
                <div class="timeline-content">
                  <div 
                    v-for="(step, index) in sample.steps" 
                    :key="index"
                    class="timeline-step"
                    :style="getTimelineStepStyle(step, index, sample.steps)"
                    @click="selectStep(index)"
                    :class="{ 'selected': selectedStepIndex === index }"
                  >
                    <div class="timeline-step-bar" :class="`step-type-${step.type}`">
                      <div class="timeline-step-label">
                        <span class="step-number">{{ index + 1 }}</span>
                        <span class="step-type-name">{{ getStepTypeLabel(step.type) }}</span>
                      </div>
                      <div class="timeline-step-duration" v-if="step.duration">
                        {{ formatDuration(step.duration) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 详细信息面板 -->
              <div v-if="selectedStepIndex !== null" class="timeline-detail-panel">
                <div class="detail-panel-header">
                  <h5>步骤 {{ selectedStepIndex + 1 }} 详细信息</h5>
                  <el-button text @click="selectedStepIndex = null">关闭</el-button>
                </div>
                <div class="detail-panel-content" v-if="sample.steps[selectedStepIndex]">
                  <div class="detail-section">
                    <strong>类型：</strong>{{ getStepTypeLabel(sample.steps[selectedStepIndex].type) }}
                  </div>
                  <div class="detail-section" v-if="sample.steps[selectedStepIndex].description">
                    <strong>描述：</strong>
                    <div class="detail-description">{{ sample.steps[selectedStepIndex].description }}</div>
                  </div>
                  <div class="detail-section" v-if="sample.steps[selectedStepIndex].timestamp">
                    <strong>时间戳：</strong>{{ formatStepTime(sample.steps[selectedStepIndex].timestamp) }}
                  </div>
                  <div class="detail-section" v-if="sample.steps[selectedStepIndex].confidence">
                    <strong>置信度：</strong>{{ (sample.steps[selectedStepIndex].confidence * 100).toFixed(1) }}%
                  </div>
                </div>
              </div>
            </div>
            
            <!-- TensorBoard风格计算图视图 -->
            <div v-if="viewMode === 'graph'" class="tensorboard-graph-view">
              <div class="graph-container" ref="graphContainer"></div>
            </div>
            
            <!-- 🚀 改进：流程图式推理过程展示 -->
            <div v-if="viewMode === 'flow'" class="reasoning-flow-animated">
              <!-- 流程开始标记 -->
              <div class="flow-start">
                <div class="flow-start-node">
                  <div class="flow-start-icon">🚀</div>
                  <div class="flow-start-text">开始推理</div>
                </div>
                <div class="flow-connector-line" v-if="sample.steps && sample.steps.length > 0"></div>
              </div>
              
              <div
                v-for="(step, index) in sample.steps"
                :key="`${sample.id}-${index}-${stepAnimationKeys.get(`${sample.id}-${index}`) || 0}`"
                class="reasoning-step-wrapper-animated"
                :class="{ 'step-newly-added': !animatedSteps.get(`${sample.id}-${index}`) }"
                :style="{ animationDelay: getStepAnimationDelay(sample.id, index) }"
              >
                <!-- 🚀 改进：根据依赖关系显示箭头 -->
                <!-- 只有非根步骤（有依赖的步骤）才显示连接线和箭头 -->
                <div 
                  v-if="shouldShowConnector(step, index, sample.steps)" 
                  class="step-connector-wrapper"
                  :class="{ 'connector-newly-added': !animatedSteps.get(`${sample.id}-${index}`) }"
                  :key="`connector-${sample.id}-${index}-${stepAnimationKeys.get(`${sample.id}-${index}`) || 0}`"
                  @click.stop
                >
                  <div class="step-connector-line"></div>
                  <div class="step-connector-arrow">
                    <svg width="20" height="20" viewBox="0 0 20 20">
                      <path d="M 5 5 L 15 10 L 5 15 Z" fill="#409eff" />
                    </svg>
                  </div>
                </div>
                
                <!-- 步骤卡片 -->
                <div 
                  class="reasoning-step-card" 
                  :class="`step-type-${step.type}`"
                  @click="toggleStepExpand(sample.id, index)"
                  :style="{ cursor: 'pointer' }"
                >
                  <!-- 步骤头部 -->
                  <div class="step-header-enhanced">
                    <div class="step-number-badge">
                      <span class="step-icon">{{ getStepIcon(step.type) }}</span>
                      <span class="step-num">{{ step.number || index + 1 }}</span>
                    </div>
                    <div class="step-header-content">
                      <div class="step-title-row">
                        <el-tag size="small" :type="getStepTagType(step.type)" class="step-type-tag">
                          {{ getStepTypeLabel(step.type) }}
                        </el-tag>
                        <span class="step-time">{{ formatStepTime(step.timestamp) }}</span>
                        <!-- 🚀 新增：展开/折叠图标 -->
                        <el-icon class="step-expand-icon" :class="{ 'expanded': isStepExpanded(sample.id, index) }">
                          <ArrowDown />
                        </el-icon>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 步骤内容 - 🚀 改进：结构化显示推理逻辑 -->
                  <div 
                    v-show="isStepExpanded(sample.id, index)" 
                    class="step-content-enhanced"
                  >
                    <!-- 前提/输入（根据什么） -->
                    <div class="step-premise" v-if="extractPremise(step, index, sample.steps)">
                      <div class="step-label">
                        <span class="label-icon">📥</span>
                        <span>根据：</span>
                      </div>
                      <div 
                        class="premise-content"
                        :data-premise-id="`${sample.id}-${index}`"
                        :ref="el => setPremiseRef(sample.id, index, el)"
                      ></div>
                    </div>
                    
                    <!-- 推理过程（如何推理） -->
                    <div class="step-process">
                      <div class="step-label">
                        <span class="label-icon">🔍</span>
                        <span>推理：</span>
                      </div>
                      <div 
                        class="step-description-enhanced" 
                        :data-step-id="`${sample.id}-${index}`"
                        :ref="el => setStepDescriptionRef(sample.id, index, el)"
                      ></div>
                    </div>
                    
                    <!-- 结论/输出（得出什么） -->
                    <div class="step-conclusion" v-if="extractConclusion(step.description)">
                      <div class="step-label">
                        <span class="label-icon">💡</span>
                        <span>得出：</span>
                      </div>
                      <div 
                        class="conclusion-content"
                        :data-conclusion-id="`${sample.id}-${index}`"
                        :ref="el => setConclusionRef(sample.id, index, el)"
                      ></div>
                    </div>
                    
                    <!-- 步骤输出标记 -->
                    <div class="step-output-indicator" v-if="extractConclusion(step.description)">
                      <div class="output-line"></div>
                      <div class="output-label">输出</div>
                    </div>
                    
                    <!-- 步骤详情（可折叠） -->
                    <div v-if="step.details" class="step-details-enhanced">
                      <el-collapse>
                        <el-collapse-item title="📋 查看详细数据" :name="`step-${sample.id}-${index}`">
                          <pre class="step-details-pre">{{ formatStepDetails(step.details) }}</pre>
                        </el-collapse-item>
                      </el-collapse>
                    </div>
                    
                    <!-- 步骤元信息 -->
                    <div v-if="step.confidence" class="step-meta">
                      <el-tag size="small" type="info" class="confidence-tag">
                        <span class="meta-icon">🎯</span>
                        置信度: {{ (step.confidence * 100).toFixed(1) }}%
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 流程结束标记 -->
              <div class="flow-end" v-if="sample.steps && sample.steps.length > 0">
                <div class="flow-connector-line"></div>
                <div class="flow-end-node">
                  <div class="flow-end-icon">✅</div>
                  <div class="flow-end-text">推理完成</div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 答案部分 -->
          <div class="answer-section" v-if="sample.answer">
            <div class="section-header">
              <h4><span>💡</span> 最终答案</h4>
            </div>
            <el-alert 
              :title="sample.answer" 
              type="success" 
              :closable="false"
              show-icon
            />
            <div v-if="sample.expected_answer" class="answer-comparison">
              <div class="comparison-item">
                <strong>系统答案:</strong> {{ sample.answer }}
              </div>
              <div class="comparison-item">
                <strong>期望答案:</strong> {{ sample.expected_answer }}
              </div>
              <div class="comparison-result" :class="{ 'match': sample.answer === sample.expected_answer }">
                {{ sample.answer === sample.expected_answer ? '✅ 答案匹配' : '❌ 答案不匹配' }}
              </div>
            </div>
          </div>
          
          <!-- 错误信息 -->
          <div class="error-section" v-if="sample.error">
            <div class="section-header">
              <h4><span>❌</span> 错误信息</h4>
            </div>
            <el-alert 
              :title="sample.error" 
              type="error" 
              :closable="false"
              show-icon
            />
          </div>
          
          <!-- 统计信息 -->
          <div class="metrics-section">
            <div class="section-header">
              <h4><span>📊</span> 统计信息</h4>
            </div>
            <div class="metrics-grid">
              <div class="metric-item">
                <span class="metric-label">推理步骤数:</span>
                <span class="metric-value">{{ sample.reasoning_steps_count || 0 }}</span>
              </div>
              <div class="metric-item" v-if="sample.duration">
                <span class="metric-label">总耗时:</span>
                <span class="metric-value">{{ formatDuration(sample.duration) }}</span>
              </div>
              <div class="metric-item" v-if="sample.confidence">
                <span class="metric-label">置信度:</span>
                <span class="metric-value">{{ (sample.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric-item" v-if="sample.start_time">
                <span class="metric-label">开始时间:</span>
                <span class="metric-value">{{ formatTime(sample.start_time) }}</span>
              </div>
              <div class="metric-item" v-if="sample.end_time">
                <span class="metric-label">结束时间:</span>
                <span class="metric-value">{{ formatTime(sample.end_time) }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const props = defineProps({
  samples: {
    type: Array,
    default: () => []
  },
  autoRefresh: {
    type: Boolean,
    default: false
  },
  totalSamples: {
    type: Number,
    default: 0
  },
  currentProgress: {
    type: Number,
    default: 0
  },
  taskStatus: {
    type: String,
    default: 'idle'
  },
  autoExpand: {
    type: Boolean,
    default: false
  }
})

// 组件初始化

// 🚀 修复：使用数组而不是Set，确保Vue响应式正常工作
// 🚀 修改：初始化为空数组，确保默认所有样本都是折叠的
const expandedSamples = ref([])

// 🚀 新增：打字机效果相关状态
const typingSteps = ref(new Map()) // 正在打字机效果的步骤
const stepDescriptionRefs = ref(new Map()) // 步骤描述元素引用
const conclusionRefs = ref(new Map()) // 结论元素引用
const premiseRefs = ref(new Map()) // 前提元素引用

// 🚀 新增：TensorBoard风格视图相关状态
const viewMode = ref('flow') // 视图模式：tensorboard, timeline, graph, flow
const selectedStepIndex = ref(null) // 选中的步骤索引
const timelineContainer = ref(null) // 时间线容器引用
const timelineRuler = ref(null) // 时间线标尺引用
const graphContainer = ref(null) // 计算图容器引用
const graphChart = ref(null) // ECharts图表实例

// 🚀 新增：TensorBoard相关状态
const tensorboardUrl = ref('') // TensorBoard URL
const generatingLogs = ref(false) // 是否正在生成日志
const tensorboardStatus = ref('') // TensorBoard状态信息
const tensorboardStatusType = ref('info') // 状态类型：success, warning, error, info

// 🚀 新增：实时推进动画相关状态
const animatedSteps = ref(new Map()) // 已播放动画的步骤 { sampleId-stepIndex: true }
const stepAnimationKeys = ref(new Map()) // 步骤动画key，用于强制重新播放动画 { sampleId-stepIndex: key }

// 🚀 新增：步骤展开/折叠状态
const expandedSteps = ref(new Map()) // 已展开的步骤 { sampleId-stepIndex: true }

// 🚀 简化：过滤后的样本（只做基本的数据处理，移除搜索、筛选、排序功能）
const filteredSamples = computed(() => {
  // 确保props.samples是数组
  if (!props.samples) {
    return []
  }
  
  // 如果不是数组，尝试转换
  let samplesArray = props.samples
  if (!Array.isArray(samplesArray)) {
    if (typeof samplesArray === 'object' && samplesArray !== null) {
      samplesArray = Object.values(samplesArray)
    } else {
      return []
    }
  }
  
  if (samplesArray.length === 0) {
    return []
  }
  
  // 按ID排序
  return [...samplesArray].sort((a, b) => a.id - b.id)
})

// 🚀 修复：监听props变化（在filteredSamples定义之后）
watch(() => props.samples, (newSamples, oldSamples) => {
  // 数据变化时自动更新
  // 🚀 修复：使用 nextTick 确保 filteredSamples 已经初始化
  nextTick(() => {
    // 🚀 新增：如果autoExpand为true，自动展开所有样本
    if (props.autoExpand && filteredSamples.value && filteredSamples.value.length > 0) {
      filteredSamples.value.forEach(sample => {
        if (!expandedSamples.value.includes(sample.id)) {
          expandedSamples.value.push(sample.id)
        }
      })
    }
    
  })
}, { immediate: true, deep: true })

// 🚀 新增：监听autoExpand属性变化
watch(() => props.autoExpand, (newVal) => {
  // 🚀 修复：使用 nextTick 确保 filteredSamples 已经初始化
  nextTick(() => {
    if (newVal && filteredSamples.value && filteredSamples.value.length > 0) {
      filteredSamples.value.forEach(sample => {
        if (!expandedSamples.value.includes(sample.id)) {
          expandedSamples.value.push(sample.id)
        }
      })
    } else if (!newVal) {
      // 如果autoExpand变为false，折叠所有样本
      expandedSamples.value = []
    }
  })
})

// 🚀 新增：监听步骤数组变化，检测新添加的步骤并触发动画
watch(() => props.samples, (newSamples, oldSamples) => {
  if (!newSamples || !Array.isArray(newSamples)) return
  
  nextTick(() => {
    newSamples.forEach(sample => {
      if (!sample.steps || !Array.isArray(sample.steps)) return
      
      // 检查样本是否已展开
      if (!isExpanded(sample.id)) return
      
      // 获取之前的步骤数量
      const oldSample = oldSamples?.find(s => s.id === sample.id)
      const oldStepCount = oldSample?.steps?.length || 0
      const newStepCount = sample.steps.length
      
      // 如果有新步骤添加
      if (newStepCount > oldStepCount) {
        // 为新步骤触发动画
        for (let i = oldStepCount; i < newStepCount; i++) {
          const stepKey = `${sample.id}-${i}`
          
          // 新添加的步骤，更新动画key，强制重新播放动画
          // 使用时间戳确保key唯一，触发Vue重新渲染
          stepAnimationKeys.value.set(stepKey, Date.now())
          
          // 标记步骤已存在（延迟标记，确保动画能触发）
          setTimeout(() => {
            animatedSteps.value.set(stepKey, true)
          }, 1000) // 延迟1秒，确保动画播放完成
        }
      }
    })
  })
}, { deep: true })

// 检查样本是否展开
const isExpanded = (sampleId) => {
  return expandedSamples.value.includes(sampleId)
}

// 🚀 新增：设置步骤描述元素引用
const setStepDescriptionRef = (sampleId, stepIndex, el) => {
  if (el) {
    const key = `${sampleId}-${stepIndex}`
    stepDescriptionRefs.value.set(key, el)
    // 如果样本已展开，立即开始打字机效果
    if (isExpanded(sampleId)) {
      nextTick(() => {
        startTypewriterForStep(sampleId, stepIndex)
      })
    }
  }
}

// 🚀 新增：设置结论元素引用
const setConclusionRef = (sampleId, stepIndex, el) => {
  if (el) {
    const key = `${sampleId}-${stepIndex}`
    conclusionRefs.value.set(key, el)
    // 如果样本已展开，立即开始打字机效果
    if (isExpanded(sampleId)) {
      nextTick(() => {
        startTypewriterForConclusion(sampleId, stepIndex)
      })
    }
  }
}

// 🚀 新增：设置前提元素引用
const setPremiseRef = (sampleId, stepIndex, el) => {
  if (el) {
    const key = `${sampleId}-${stepIndex}`
    premiseRefs.value.set(key, el)
    // 如果样本已展开，立即开始打字机效果
    if (isExpanded(sampleId)) {
      nextTick(() => {
        startTypewriterForPremise(sampleId, stepIndex)
      })
    }
  }
}

// 🚀 新增：打字机效果函数
const typewriterEffect = (element, text, speed = 30) => {
  return new Promise((resolve) => {
    if (!element || !text) {
      resolve()
      return
    }
    
    // 清理HTML标签，只保留纯文本用于打字机效果
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = text
    const plainText = tempDiv.textContent || tempDiv.innerText || ''
    
    let index = 0
    element.innerHTML = ''
    
    // 如果原文本包含HTML，我们需要保留HTML结构
    const hasHTML = text !== plainText
    
    if (hasHTML) {
      // 对于包含HTML的文本，我们使用更复杂的方式
      // 先显示HTML结构，然后逐步显示文本内容
      element.innerHTML = text
      const textNodes = getTextNodes(element)
      let currentTextNodeIndex = 0
      let currentCharIndex = 0
      
      const timer = setInterval(() => {
        if (currentTextNodeIndex < textNodes.length) {
          const textNode = textNodes[currentTextNodeIndex]
          const nodeText = textNode.textContent
          
          if (currentCharIndex < nodeText.length) {
            textNode.textContent = nodeText.substring(0, currentCharIndex + 1)
            currentCharIndex++
          } else {
            currentTextNodeIndex++
            currentCharIndex = 0
          }
        } else {
          clearInterval(timer)
          resolve()
        }
      }, speed)
    } else {
      // 纯文本，直接逐字显示
      const timer = setInterval(() => {
        if (index < plainText.length) {
          element.textContent = plainText.substring(0, index + 1)
          index++
        } else {
          clearInterval(timer)
          resolve()
        }
      }, speed)
    }
  })
}

// 🚀 新增：获取元素中的所有文本节点
const getTextNodes = (element) => {
  const textNodes = []
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null,
    false
  )
  
  let node
  while (node = walker.nextNode()) {
    textNodes.push(node)
  }
  
  return textNodes
}

// 🚀 新增：为前提启动打字机效果
const startTypewriterForPremise = async (sampleId, stepIndex) => {
  const key = `premise-${sampleId}-${stepIndex}`
  
  // 如果已经在打字，跳过
  if (typingSteps.value.has(key)) {
    return
  }
  
  // 找到对应的样本和步骤
  const sample = filteredSamples.value.find(s => s.id === sampleId)
  if (!sample || !sample.steps || !sample.steps[stepIndex]) {
    return
  }
  
  const step = sample.steps[stepIndex]
  const premise = extractPremise(step, stepIndex, sample.steps)
  
  if (!premise) {
    return
  }
  
  const element = premiseRefs.value.get(`${sampleId}-${stepIndex}`)
  if (!element) {
    return
  }
  
  // 标记为正在打字
  typingSteps.value.set(key, true)
  
  // 等待步骤卡片动画完成（延迟基于步骤索引，前提最先显示）
  await new Promise(resolve => setTimeout(resolve, stepIndex * 300 + 600))
  
  // 格式化前提文本
  const formattedText = formatPremise(premise)
  
  // 开始打字机效果
  await typewriterEffect(element, formattedText, 25)
  
  // 标记为完成
  typingSteps.value.delete(key)
}

// 🚀 新增：为步骤描述启动打字机效果
const startTypewriterForStep = async (sampleId, stepIndex) => {
  const key = `${sampleId}-${stepIndex}`
  
  // 如果已经在打字，跳过
  if (typingSteps.value.has(key)) {
    return
  }
  
  // 找到对应的样本和步骤
  const sample = filteredSamples.value.find(s => s.id === sampleId)
  if (!sample || !sample.steps || !sample.steps[stepIndex]) {
    return
  }
  
  const step = sample.steps[stepIndex]
  const element = stepDescriptionRefs.value.get(key)
  
  if (!element || !step.description) {
    return
  }
  
  // 标记为正在打字
  typingSteps.value.set(key, true)
  
  // 等待前提打字完成（延迟更久）
  await new Promise(resolve => setTimeout(resolve, stepIndex * 300 + 1000))
  
  // 格式化描述文本（只显示推理过程部分）
  const formattedText = formatStepDescription(step.description)
  
  // 开始打字机效果
  await typewriterEffect(element, formattedText, 20)
  
  // 标记为完成
  typingSteps.value.delete(key)
}

// 🚀 新增：为结论启动打字机效果
const startTypewriterForConclusion = async (sampleId, stepIndex) => {
  const key = `${sampleId}-${stepIndex}`
  
  // 如果已经在打字，跳过
  if (typingSteps.value.has(`conclusion-${key}`)) {
    return
  }
  
  // 找到对应的样本和步骤
  const sample = filteredSamples.value.find(s => s.id === sampleId)
  if (!sample || !sample.steps || !sample.steps[stepIndex]) {
    return
  }
  
  const step = sample.steps[stepIndex]
  const conclusion = extractConclusion(step.description)
  
  if (!conclusion) {
    return
  }
  
  const element = conclusionRefs.value.get(key)
  if (!element) {
    return
  }
  
  // 标记为正在打字
  typingSteps.value.set(`conclusion-${key}`, true)
  
  // 等待步骤描述打字完成（延迟更久）
  await new Promise(resolve => setTimeout(resolve, stepIndex * 300 + 1000))
  
  // 格式化结论文本
  const formattedText = formatConclusion(conclusion)
  
  // 开始打字机效果
  await typewriterEffect(element, formattedText, 20)
  
  // 标记为完成
  typingSteps.value.delete(`conclusion-${key}`)
}

// 🚀 新增：监听样本展开状态，触发打字机效果
watch(expandedSamples, (newExpanded, oldExpanded) => {
  nextTick(() => {
    // 找出新展开的样本
    const newlyExpanded = newExpanded.filter(id => !oldExpanded.includes(id))
    
    newlyExpanded.forEach(sampleId => {
      const sample = filteredSamples.value.find(s => s.id === sampleId)
      if (sample && sample.steps) {
        // 🚀 新增：初始化步骤动画状态
        initializeStepAnimations(sampleId, sample.steps)
        
        // 为每个步骤启动打字机效果（按顺序：前提→推理→结论）
        sample.steps.forEach((step, index) => {
          if (extractPremise(step, index, sample.steps)) {
            startTypewriterForPremise(sampleId, index)
          }
          startTypewriterForStep(sampleId, index)
          if (extractConclusion(step.description)) {
            startTypewriterForConclusion(sampleId, index)
          }
        })
      }
    })
  })
}, { deep: true })

// 根据样本选择器过滤后的显示样本（默认显示第一个）
// 🚀 简化：直接使用 filteredSamples
const displayedSamples = computed(() => filteredSamples.value)

// 计算是否显示空状态
const shouldShowEmptyState = computed(() => {
  const hasSamples = filteredSamples.value && Array.isArray(filteredSamples.value) && filteredSamples.value.length > 0
  return !hasSamples
})

// 计算是否显示样本列表
const shouldShowSamples = computed(() => {
  const hasSamples = filteredSamples.value && Array.isArray(filteredSamples.value) && filteredSamples.value.length > 0
  return hasSamples
})

const toggleExpand = (sampleId) => {
  const index = expandedSamples.value.indexOf(sampleId)
  if (index > -1) {
    expandedSamples.value.splice(index, 1)
  } else {
    expandedSamples.value.push(sampleId)
  }
}

// 🚀 新增：切换步骤展开/折叠状态
const toggleStepExpand = (sampleId, stepIndex) => {
  const stepKey = `${sampleId}-${stepIndex}`
  const isExpanded = expandedSteps.value.get(stepKey)
  
  if (isExpanded) {
    expandedSteps.value.delete(stepKey)
  } else {
    expandedSteps.value.set(stepKey, true)
  }
}

// 🚀 新增：检查步骤是否展开
const isStepExpanded = (sampleId, stepIndex) => {
  const stepKey = `${sampleId}-${stepIndex}`
  return expandedSteps.value.get(stepKey) || false
}

const getStatusType = (status) => {
  const statusMap = {
    'running': 'warning',
    'completed': 'success',
    'error': 'danger',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'running': '运行中',
    'completed': '已完成',
    'error': '错误',
    'pending': '等待中'
  }
  return statusMap[status] || status
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  // 如果timestamp是秒级时间戳，需要乘以1000
  const ts = timestamp > 1000000000000 ? timestamp : timestamp * 1000
  const date = new Date(ts)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '0s'
  if (seconds < 60) {
    return `${seconds.toFixed(2)}s`
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60)
    const secs = (seconds % 60).toFixed(2)
    return `${mins}m ${secs}s`
  } else {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = (seconds % 60).toFixed(2)
    return `${hours}h ${mins}m ${secs}s`
  }
}

const formatStepTime = (timestamp) => {
  if (!timestamp) return '-'
  // 如果timestamp是秒级时间戳，需要乘以1000
  const ts = timestamp > 1000000000000 ? timestamp : timestamp * 1000
  const date = new Date(ts)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })
}

const getStepIcon = (type) => {
  const iconMap = {
    'evidence': '🔍',
    'reasoning': '🧠',
    'answer': '💡',
    'validation': '✅'
  }
  return iconMap[type] || '📝'
}

const getStepColor = (type) => {
  const colorMap = {
    'evidence': '#409eff',
    'reasoning': '#67c23a',
    'answer': '#e6a23c',
    'validation': '#f56c6c',
    // 🚀 新增：支持更多步骤类型
    'query_analysis': '#67c23a',  // 查询分析 - 绿色（推理分析类）
    'evidence_gathering': '#409eff',  // 证据收集 - 蓝色
    'logical_deduction': '#67c23a',  // 逻辑推理 - 绿色
    'answer_synthesis': '#e6a23c',  // 答案综合 - 橙色
    'verification': '#f56c6c',  // 结果验证 - 红色
    'fact_checking': '#f56c6c',  // 事实核查 - 红色
    'pattern_recognition': '#67c23a',  // 模式识别 - 绿色
    'causal_reasoning': '#67c23a',  // 因果推理 - 绿色
    'analogical_reasoning': '#67c23a',  // 类比推理 - 绿色
    'mathematical_reasoning': '#67c23a',  // 数学推理 - 绿色
    'pattern_analysis': '#67c23a'  // 模式分析 - 绿色
  }
  return colorMap[type] || '#909399'
}

const getStepTagType = (type) => {
  const typeMap = {
    'evidence': 'primary',
    'reasoning': 'success',
    'answer': 'warning',
    'validation': 'danger'
  }
  return typeMap[type] || 'info'
}

// 格式化查询内容
const formatQuery = (query) => {
  if (!query) return '<span class="text-muted">暂无查询内容</span>'
  
  let queryStr = String(query)
  
  // 如果是字典格式，尝试提取并格式化
  if (queryStr.startsWith('{') || queryStr.startsWith("'")) {
    // 尝试提取Prompt字段
    const promptMatch = queryStr.match(/'Prompt'[：:]\s*['"]([^'"]+)['"]/)
    if (promptMatch) {
      return `<div class="query-prompt"><strong>问题：</strong>${escapeHtml(promptMatch[1])}</div>`
    }
    
    // 尝试解析为JSON
    try {
      const parsed = JSON.parse(queryStr.replace(/'/g, '"'))
      if (parsed.Prompt) {
        return `<div class="query-prompt"><strong>问题：</strong>${escapeHtml(parsed.Prompt)}</div>`
      }
    } catch (e) {
      // 解析失败，继续处理
    }
    
    // 如果包含Prompt字段但格式不标准，尝试提取
    const promptMatch2 = queryStr.match(/Prompt['"][：:]\s*['"]([^'"]+)['"]/)
    if (promptMatch2) {
      return `<div class="query-prompt"><strong>问题：</strong>${escapeHtml(promptMatch2[1])}</div>`
    }
  }
  
  // 普通文本，直接显示但限制长度
  if (queryStr.length > 500) {
    return `<div class="query-text-full">${escapeHtml(queryStr.substring(0, 500))}...</div>`
  }
  
  return `<div class="query-text-full">${escapeHtml(queryStr)}</div>`
}

// 转义HTML
const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 🚀 新增：提取前提（根据什么）
const extractPremise = (step, stepIndex, allSteps) => {
  if (!step || !step.description) return null
  
  let desc = String(step.description)
  
  // 模式1: 从描述中提取前提部分（如"根据..."、"基于..."、"从..."）
  const premiseMatch1 = desc.match(/(?:根据|基于|从|依据|参考|利用)[：:，,。.]\s*(.+?)(?:\n|$|，|。|；|推理|分析)/i)
  if (premiseMatch1 && premiseMatch1[1].trim()) {
    return premiseMatch1[1].trim()
  }
  
  // 模式2: 如果这是第一步，前提可能是查询或初始信息
  if (stepIndex === 0) {
    // 提取描述开头的关键信息作为前提
    const firstSentence = desc.split(/[。！？\n]/)[0]
    if (firstSentence && firstSentence.length < 200) {
      return firstSentence.trim()
    }
  }
  
  // 模式3: 从前一步的结论中提取前提
  if (stepIndex > 0 && allSteps && allSteps[stepIndex - 1]) {
    const prevStep = allSteps[stepIndex - 1]
    const prevConclusion = extractConclusion(prevStep.description)
    if (prevConclusion) {
      return prevConclusion
    }
    // 如果没有明确的结论，使用前一步的描述作为前提
    if (prevStep.description) {
      const prevDesc = String(prevStep.description)
      // 提取前一步的关键信息
      const sentences = prevDesc.split(/[。！？\n]/).filter(s => s.trim().length > 0)
      if (sentences.length > 0) {
        return sentences[sentences.length - 1].trim()
      }
    }
  }
  
  return null
}

// 🚀 新增：格式化前提
const formatPremise = (premise) => {
  if (!premise) return ''
  
  let prem = String(premise)
  prem = escapeHtml(prem)
  
  // 高亮关键信息
  const keywords = ['证据', '信息', '数据', '结果', '结论', '事实']
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    prem = prem.replace(regex, '<strong class="premise-keyword">$1</strong>')
  })
  
  return prem
}

// 格式化推理步骤描述（只显示推理过程部分）
const formatStepDescription = (description) => {
  if (!description) return ''
  
  let desc = String(description)
  
  // 🚀 修复：移除前提部分
  desc = desc.replace(/(?:根据|基于|从|依据|参考|利用)[：:，,。.]\s*.+?(?=\n|$|，|。|；|推理|分析)/i, '').trim()
  
  // 🚀 修复：如果描述中包含结论，先移除结论部分
  const conclusion = extractConclusion(desc)
  if (conclusion) {
    // 移除结论部分（包括"结论："等关键词）
    desc = desc.replace(/结论[：:]\s*.+$/i, '').trim()
    desc = desc.replace(/(?:因此|所以|得出|结论是|结果是)[：:，,。.]\s*.+$/i, '').trim()
  }
  
  // 如果移除后为空，返回提示
  if (!desc || desc.trim().length === 0) {
    return '<span class="text-muted">进行推理分析...</span>'
  }
  
  // 如果描述很长，添加换行和格式化
  desc = escapeHtml(desc)
  
  // 将换行符转换为<br>
  desc = desc.replace(/\n/g, '<br>')
  
  // 高亮关键词（但不包括"结论"，因为已经移除了）
  const keywords = ['推理', '分析', '验证', '计算', '比较', '判断', '推导']
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    desc = desc.replace(regex, '<strong class="keyword-highlight">$1</strong>')
  })
  
  return desc
}

// 格式化推理步骤详情
const formatStepDetails = (details) => {
  if (!details) return ''
  
  let detailStr = String(details)
  
  // 如果是JSON格式，尝试格式化
  if (detailStr.startsWith('{') || detailStr.startsWith('[')) {
    try {
      const parsed = JSON.parse(detailStr)
      return JSON.stringify(parsed, null, 2)
    } catch (e) {
      // 解析失败，返回原文本
    }
  }
  
  return detailStr
}

// 提取步骤结论
const extractConclusion = (description) => {
  if (!description) return null
  
  let desc = String(description)
  
  // 尝试提取结论（多种模式）
  // 模式1: "结论："或"结论:"后面的内容（优先匹配）
  const conclusionMatch1 = desc.match(/结论[：:]\s*(.+?)(?:\n|$|，|。|；)/i)
  if (conclusionMatch1 && conclusionMatch1[1].trim()) {
    return conclusionMatch1[1].trim()
  }
  
  // 模式2: "因此"、"所以"、"得出"等关键词后的内容
  const conclusionMatch2 = desc.match(/(?:因此|所以|得出|结论是|结果是)[：:，,。.]\s*(.+?)(?:\n|$|，|。|；)/i)
  if (conclusionMatch2 && conclusionMatch2[1].trim()) {
    return conclusionMatch2[1].trim()
  }
  
  // 模式3: 提取最后一句作为结论（如果描述包含多个句子）
  const sentences = desc.split(/[。！？\n]/).filter(s => s.trim().length > 0)
  if (sentences.length > 1) {
    // 如果有多个句子，取最后一句作为结论
    const lastSentence = sentences[sentences.length - 1].trim()
    // 检查最后一句是否包含结论关键词
    if (lastSentence.match(/(?:因此|所以|得出|结论|结果|是|为)/i) && 
        lastSentence.length > 10 && lastSentence.length < 200) {
      return lastSentence
    }
  }
  
  // 如果描述很短且不包含推理过程关键词，可能是结论
  if (desc.length < 150 && 
      !desc.match(/(?:分析|推理|搜索|查找|验证|检查|比较)/i) &&
      (desc.match(/(?:是|为|有|包含|属于|等于)/i) || desc.length < 50)) {
    return desc
  }
  
  return null
}

// 格式化结论
// 🚀 新增：判断是否应该显示连接线和箭头
const shouldShowConnector = (step, stepIndex, allSteps) => {
  // 第一个步骤（索引0）不显示箭头，因为它前面没有步骤
  if (stepIndex === 0) {
    return false
  }
  
  // 检查步骤是否有依赖关系
  const dependsOn = step.depends_on || step.dependsOn || []
  
  // 如果有明确的依赖关系，显示箭头
  if (dependsOn.length > 0) {
    return true
  }
  
  // 如果没有依赖关系，但也不是第一个步骤
  // 为了保持向后兼容和视觉连续性，默认显示箭头（顺序执行的情况）
  // 这样即使没有明确的depends_on字段，也能正常显示流程
  return true
}

// 🚀 新增：获取步骤动画延迟时间
const getStepAnimationDelay = (sampleId, stepIndex) => {
  const stepKey = `${sampleId}-${stepIndex}`
  const animationKey = stepAnimationKeys.value.get(stepKey)
  
  // 如果有动画key，说明这是新添加的步骤，应该立即显示（延迟0）
  // 如果没有动画key，说明这是首次显示，使用原来的延迟逻辑
  if (animationKey) {
    // 新添加的步骤立即显示
    return '0s'
  } else {
    // 首次显示时，使用原来的延迟逻辑
    return `${stepIndex * 0.3}s`
  }
}

// 🚀 新增：初始化样本的步骤动画状态（当样本首次展开时）
const initializeStepAnimations = (sampleId, steps) => {
  if (!steps || !Array.isArray(steps)) return
  
  steps.forEach((step, index) => {
    const stepKey = `${sampleId}-${index}`
    // 如果步骤已经存在（不是新添加的），标记为已播放动画
    // 这样新添加的步骤才能正确触发动画
    if (!animatedSteps.value.has(stepKey)) {
      animatedSteps.value.set(stepKey, true)
    }
  })
}

const formatConclusion = (conclusion) => {
  if (!conclusion) return ''
  
  let concl = String(conclusion)
  concl = escapeHtml(concl)
  
  // 高亮关键词
  const keywords = ['是', '为', '有', '包含', '属于', '等于', '大于', '小于']
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'g')
    concl = concl.replace(regex, '<strong class="conclusion-keyword">$1</strong>')
  })
  
  return concl
}

// 获取步骤类型的中文标签
const getStepTypeLabel = (type) => {
  const labelMap = {
    'evidence': '证据收集',
    'reasoning': '推理分析',
    'answer': '答案生成',
    'validation': '结果验证',
    'search': '信息搜索',
    'analysis': '数据分析',
    // 🚀 新增：支持更多步骤类型
    'query_analysis': '查询分析',
    'evidence_gathering': '证据收集',
    'logical_deduction': '逻辑推理',
    'answer_synthesis': '答案综合',
    'verification': '结果验证',
    'fact_checking': '事实核查',
    'pattern_recognition': '模式识别',
    'causal_reasoning': '因果推理',
    'analogical_reasoning': '类比推理',
    'mathematical_reasoning': '数学推理',
    'pattern_analysis': '模式分析'
  }
  return labelMap[type] || type
}

// 🚀 新增：获取时间线步骤样式
const getTimelineStepStyle = (step, index, allSteps) => {
  if (!step || !allSteps) return {}
  
  // 计算时间范围
  const startTime = step.timestamp || 0
  const duration = step.duration || 1000 // 默认1秒
  const endTime = startTime + duration
  
  // 计算总时间范围
  const times = allSteps.map(s => s.timestamp || 0)
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times.map((t, i) => t + (allSteps[i].duration || 1000)))
  const totalDuration = maxTime - minTime
  
  // 计算位置和宽度（百分比）
  const left = totalDuration > 0 ? ((startTime - minTime) / totalDuration) * 100 : 0
  const width = totalDuration > 0 ? (duration / totalDuration) * 100 : 10
  
  return {
    left: `${left}%`,
    width: `${Math.max(width, 2)}%` // 最小宽度2%
  }
}

// 🚀 新增：渲染计算图（带重试机制）
let renderGraphViewRetryCount = 0
const MAX_RETRY_COUNT = 10

const renderGraphView = () => {
  if (!graphContainer.value) {
    // 容器不存在，延迟重试（最多重试10次）
    if (renderGraphViewRetryCount < MAX_RETRY_COUNT) {
      renderGraphViewRetryCount++
      setTimeout(() => {
        renderGraphView()
      }, 200)
    } else {
      console.warn('图表容器未准备好，已达到最大重试次数')
      renderGraphViewRetryCount = 0
    }
    return
  }
  
  // 重置重试计数
  renderGraphViewRetryCount = 0
  
  // 如果图表已存在，先销毁
  if (graphChart.value) {
    graphChart.value.dispose()
    graphChart.value = null
  }
  
  // 找到当前显示的样本
  const sample = displayedSamples.value.find(s => isExpanded(s.id))
  if (!sample || !sample.steps || sample.steps.length === 0) return
  
  // 确保容器元素已准备好且有尺寸
  const container = graphContainer.value
  if (!container) {
    if (renderGraphViewRetryCount < MAX_RETRY_COUNT) {
      renderGraphViewRetryCount++
      setTimeout(() => {
        renderGraphView()
      }, 200)
    } else {
      console.warn('图表容器未准备好，已达到最大重试次数')
      renderGraphViewRetryCount = 0
    }
    return
  }
  
  // 检查是否是有效的 DOM 元素
  if (typeof container.getBoundingClientRect !== 'function') {
    if (renderGraphViewRetryCount < MAX_RETRY_COUNT) {
      renderGraphViewRetryCount++
      setTimeout(() => {
        renderGraphView()
      }, 200)
    } else {
      console.warn('图表容器不是有效的 DOM 元素，已达到最大重试次数')
      renderGraphViewRetryCount = 0
    }
    return
  }
  
  // 检查容器是否有尺寸
  const rect = container.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    // 如果还没有尺寸，延迟重试
    if (renderGraphViewRetryCount < MAX_RETRY_COUNT) {
      renderGraphViewRetryCount++
      setTimeout(() => {
        renderGraphView()
      }, 200)
    } else {
      console.warn('图表容器没有尺寸，已达到最大重试次数')
      renderGraphViewRetryCount = 0
    }
    return
  }
  
  // 创建图表实例
  const chart = echarts.init(container)
  graphChart.value = chart
  
  // 构建节点和边
  const nodes = []
  const links = []
  
  // 添加开始节点
  nodes.push({
    id: 'start',
    name: '开始',
    category: 0,
    symbolSize: 50,
    itemStyle: { color: '#67c23a' }
  })
  
  // 🚀 改进：使用依赖关系构建节点图
  // 首先创建所有节点
  sample.steps.forEach((step, index) => {
    const nodeId = `step-${index}`
    const stepType = (step.type || 'unknown').toLowerCase()
    const stepLabel = getStepTypeLabel(stepType)
    
    // 根据步骤类型确定类别
    let category = 1
    if (stepType === 'evidence' || stepType === 'search' || stepType === 'evidence_gathering' || stepType === 'knowledge_query') {
      category = 1
    } else if (stepType === 'reasoning' || stepType === 'analysis' || stepType === 'logical_deduction' || stepType === 'logical_induction' || stepType === 'logical_abduction') {
      category = 2
    } else if (stepType === 'answer' || stepType === 'answer_synthesis' || stepType === 'synthesis') {
      category = 3
    } else if (stepType === 'validation' || stepType === 'verification') {
      category = 4
    }
    
    // 获取并行组信息
    const parallelGroup = step.parallel_group || step.parallelGroup
    
    // 🚀 新增：检查步骤是否展开，展开的节点显示不同样式
    const stepKey = `${sample.id}-${index}`
    const isStepExpandedInGraph = expandedSteps.value.get(stepKey) || false
    
    nodes.push({
      id: nodeId,
      name: `${index + 1}. ${stepLabel}${parallelGroup ? ` [${parallelGroup}]` : ''}`, // 在名称中包含并行组信息
      category: category,
      symbolSize: parallelGroup ? 70 : 60, // 并行组节点稍大
      stepIndex: index,
      stepData: step,
      parallelGroup: parallelGroup,
      // 🚀 新增：展开的节点使用不同颜色
      itemStyle: {
        color: isStepExpandedInGraph ? '#67c23a' : undefined, // 展开的节点显示为绿色
        borderColor: isStepExpandedInGraph ? '#67c23a' : '#fff',
        borderWidth: isStepExpandedInGraph ? 3 : 2
      }
    })
  })
  
  // 🚀 改进：根据 depends_on 构建依赖关系
  const rootSteps = [] // 没有依赖的步骤（根节点）
  
  sample.steps.forEach((step, index) => {
    const nodeId = `step-${index}`
    const dependsOn = step.depends_on || step.dependsOn || []
    
    if (dependsOn.length === 0) {
      // 没有依赖的步骤，连接到开始节点
      rootSteps.push(index)
      links.push({ source: 'start', target: nodeId })
    } else {
      // 有依赖的步骤，连接到依赖的步骤
      dependsOn.forEach((dep) => {
        let depIndex = -1
        
        // 处理不同的依赖格式
        if (typeof dep === 'string') {
          // 格式可能是 "step_1", "step-1", "1" 等
          const match = dep.match(/(\d+)/)
          if (match) {
            depIndex = parseInt(match[1]) - 1 // step_1 -> index 0
          }
        } else if (typeof dep === 'number') {
          depIndex = dep - 1 // 如果dep是1-based，转换为0-based
        }
        
        // 验证依赖索引是否有效
        if (depIndex >= 0 && depIndex < sample.steps.length && depIndex !== index) {
          const depNodeId = `step-${depIndex}`
          links.push({ 
            source: depNodeId, 
            target: nodeId,
            // 如果是并行组，使用不同的样式
            lineStyle: {
              curveness: step.parallel_group || step.parallelGroup ? 0.3 : 0.2
            }
          })
        }
      })
    }
  })
  
  // 添加结束节点
  // 找到所有没有后续步骤的节点（叶子节点）
  const leafSteps = []
  sample.steps.forEach((step, index) => {
    // 检查是否有其他步骤依赖此步骤
    const hasDependent = sample.steps.some((otherStep, otherIndex) => {
      if (otherIndex === index) return false
      const otherDependsOn = otherStep.depends_on || otherStep.dependsOn || []
      return otherDependsOn.some((dep) => {
        let depIndex = -1
        if (typeof dep === 'string') {
          const match = dep.match(/(\d+)/)
          if (match) {
            depIndex = parseInt(match[1]) - 1
          }
        } else if (typeof dep === 'number') {
          depIndex = dep - 1
        }
        return depIndex === index
      })
    })
    
    if (!hasDependent) {
      leafSteps.push(index)
    }
  })
  
  nodes.push({
    id: 'end',
    name: '结束',
    category: 0,
    symbolSize: 50,
    itemStyle: { color: '#909399' }
  })
  
  // 将所有叶子节点连接到结束节点
  if (leafSteps.length > 0) {
    leafSteps.forEach((leafIndex) => {
      links.push({ source: `step-${leafIndex}`, target: 'end' })
    })
  } else if (sample.steps.length > 0) {
    // 如果没有找到叶子节点，连接最后一个步骤（回退方案）
    links.push({ source: `step-${sample.steps.length - 1}`, target: 'end' })
  }
  
  // 配置图表
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          if (params.data.id === 'start' || params.data.id === 'end') {
            return params.data.name
          }
          
          if (params.data.stepData) {
            const step = params.data.stepData
            const stepIndex = params.data.stepIndex
            let tooltip = `<b>步骤 ${stepIndex + 1}: ${params.data.name}</b><br/>`
            
            // 显示子查询
            if (step.sub_query) {
              tooltip += `<br/><b>子查询:</b> ${step.sub_query.substring(0, 150)}${step.sub_query.length > 150 ? '...' : ''}<br/>`
            }
            
            // 显示描述
            if (step.description) {
              tooltip += `<br/><b>描述:</b> ${step.description.substring(0, 150)}${step.description.length > 150 ? '...' : ''}<br/>`
            }
            
            // 显示依赖关系
            const dependsOn = step.depends_on || step.dependsOn || []
            if (dependsOn.length > 0) {
              tooltip += `<br/><b>依赖步骤:</b> ${dependsOn.join(', ')}<br/>`
            } else {
              tooltip += `<br/><b>依赖:</b> 无（根步骤）<br/>`
            }
            
            // 显示并行组
            const parallelGroup = step.parallel_group || step.parallelGroup
            if (parallelGroup) {
              tooltip += `<br/><b>并行组:</b> ${parallelGroup}<br/>`
            }
            
            // 显示答案（如果有）
            if (step.answer) {
              tooltip += `<br/><b>答案:</b> ${step.answer.substring(0, 100)}${step.answer.length > 100 ? '...' : ''}<br/>`
            }
            
            return tooltip
          }
        }
        return params.data.name
      }
    },
    legend: {
      data: ['开始/结束', '证据收集', '推理分析', '答案生成', '结果验证'],
      bottom: 10
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      categories: [
        { name: '开始/结束', itemStyle: { color: '#909399' } },
        { name: '证据收集', itemStyle: { color: '#409eff' } },
        { name: '推理分析', itemStyle: { color: '#67c23a' } },
        { name: '答案生成', itemStyle: { color: '#e6a23c' } },
        { name: '结果验证', itemStyle: { color: '#f56c6c' } }
      ],
      roam: true,
      label: {
        show: true,
        position: 'inside',
        fontSize: 12
      },
      lineStyle: {
        color: 'source',
        curveness: 0.2,
        width: 2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 }
      },
      force: {
        repulsion: 600, // 增加排斥力，使节点间距更大
        gravity: 0.2, // 减少重力，使布局更分散
        edgeLength: 200, // 增加边的理想长度
        layoutAnimation: true,
        // 🚀 改进：根据并行组调整布局
        initLayout: 'circular' // 初始布局使用圆形，然后由力导向算法优化
      },
      // 🚀 改进：为并行组使用不同的节点样式
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2
      },
      // 🚀 改进：根据并行组设置不同的节点形状
      symbol: 'circle'
    }]
  }
  
  chart.setOption(option)
  
  // 🚀 新增：添加节点点击事件，展开/折叠步骤详情
  chart.off('click') // 先移除之前的点击事件监听器
  chart.on('click', (params) => {
    if (params.dataType === 'node' && params.data.stepData) {
      const stepIndex = params.data.stepIndex
      const sample = displayedSamples.value.find(s => isExpanded(s.id))
      if (sample) {
        toggleStepExpand(sample.id, stepIndex)
        // 更新视图以反映展开/折叠状态
        nextTick(() => {
          renderGraphView()
        })
      }
    }
  })
  
  // 响应式调整
  const resizeHandler = () => {
    if (chart && !chart.isDisposed()) {
      chart.resize()
    }
  }
  window.addEventListener('resize', resizeHandler)
  chart._resizeHandler = resizeHandler
}

// 🚀 新增：生成 TensorBoard 日志
const generateTensorBoardLogs = async () => {
  generatingLogs.value = true
  tensorboardStatus.value = '正在生成 TensorBoard 日志...'
  tensorboardStatusType.value = 'info'
  
  try {
    // 找到当前显示的样本
    const sample = displayedSamples.value.find(s => isExpanded(s.id))
    if (!sample || !sample.steps || sample.steps.length === 0) {
      tensorboardStatus.value = '请先展开一个包含推理步骤的样本'
      tensorboardStatusType.value = 'warning'
      generatingLogs.value = false
      return
    }
    
    // 调用后端API生成 TensorBoard 日志
    const response = await fetch('/api/generate_tensorboard_logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sample_id: sample.id,
        steps: sample.steps
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      tensorboardStatus.value = 'TensorBoard 日志生成成功！'
      tensorboardStatusType.value = 'success'
      // 设置 TensorBoard URL
      tensorboardUrl.value = data.tensorboard_url || 'http://localhost:6006'
    } else {
      tensorboardStatus.value = data.error || '生成 TensorBoard 日志失败'
      tensorboardStatusType.value = 'error'
    }
  } catch (error) {
    tensorboardStatus.value = `生成 TensorBoard 日志时出错: ${error.message}`
    tensorboardStatusType.value = 'error'
  } finally {
    generatingLogs.value = false
  }
}

// 🚀 新增：刷新 TensorBoard
const refreshTensorBoard = () => {
  if (tensorboardUrl.value) {
    // 重新加载 iframe
    const iframe = document.querySelector('.tensorboard-iframe')
    if (iframe) {
      iframe.src = tensorboardUrl.value
    }
  }
}

// 🚀 新增：监听视图模式变化
watch(viewMode, (newMode) => {
  if (newMode === 'graph') {
    // 等待 DOM 渲染完成，增加延迟确保容器元素已准备好
    nextTick(() => {
      setTimeout(() => {
        renderGraphView()
      }, 200)
    })
  } else if (newMode === 'tensorboard') {
    // 检查是否已有 TensorBoard URL
    if (!tensorboardUrl.value) {
      tensorboardStatus.value = '请先点击"生成 TensorBoard 日志"按钮'
      tensorboardStatusType.value = 'info'
    }
  }
})

// 🚀 新增：监听样本展开状态，更新计算图
watch(expandedSamples, () => {
  if (viewMode.value === 'graph') {
    // 等待 DOM 渲染完成
    nextTick(() => {
      setTimeout(() => {
        renderGraphView()
      }, 200)
    })
  }
}, { deep: true })

// 🚀 新增：组件挂载时确保所有样本都是折叠的
onMounted(() => {
  // 🚀 修复：如果autoExpand为false，默认折叠所有样本
  if (!props.autoExpand) {
    expandedSamples.value = []
  } else {
    // 如果autoExpand为true，自动展开所有样本
    if (filteredSamples.value.length > 0) {
      filteredSamples.value.forEach(sample => {
        if (!expandedSamples.value.includes(sample.id)) {
          expandedSamples.value.push(sample.id)
        }
      })
    }
  }
  
  // 初始化计算图
  if (viewMode.value === 'graph') {
    nextTick(() => {
      setTimeout(() => {
        renderGraphView()
      }, 300)
    })
  }
})

// 🚀 新增：组件卸载时清理
onBeforeUnmount(() => {
  if (graphChart.value) {
    if (graphChart.value._resizeHandler) {
      window.removeEventListener('resize', graphChart.value._resizeHandler)
    }
    graphChart.value.dispose()
    graphChart.value = null
  }
})
</script>

<style scoped>
.reasoning-process {
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 0;
}

.toolbar-card {
  margin-bottom: 16px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.samples-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sample-card {
  transition: all 0.3s;
  margin-bottom: 16px;
}

.sample-card.sample-active {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
  animation: pulse 2s infinite;
}

.sample-card.sample-completed {
  border-color: #67c23a;
}

.sample-card.sample-error {
  border-color: #f56c6c;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
  }
  50% {
    box-shadow: 0 2px 20px rgba(64, 158, 255, 0.5);
  }
}

.sample-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}

.sample-header:hover {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 4px 8px;
  margin: -4px -8px;
}

.sample-info {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.sample-id {
  font-weight: bold;
  color: #303133;
  font-size: 16px;
}

.sample-time {
  color: #909399;
  font-size: 12px;
}

.sample-metrics {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* 🚀 改进：参考 fogsight 的动画设计，添加更流畅的展开/收起动画 */

.expand-icon {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 18px;
  color: #909399;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.expand-icon:hover {
  color: #409eff;
  transform: scale(1.2);
}

.expand-icon.expanded:hover {
  transform: rotate(180deg) scale(1.2);
}

/* 样本卡片动画 */
.sample-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: cardFadeIn 0.5s ease-out;
  animation-fill-mode: both;
}

/* 卡片错开出现动画 */
.sample-card:nth-child(1) {
  animation-delay: 0.05s;
}

.sample-card:nth-child(2) {
  animation-delay: 0.1s;
}

.sample-card:nth-child(3) {
  animation-delay: 0.15s;
}

.sample-card:nth-child(4) {
  animation-delay: 0.2s;
}

.sample-card:nth-child(n+5) {
  animation-delay: 0.25s;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.sample-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.sample-card.sample-active {
  animation: activePulse 2s ease-in-out infinite;
  border: 2px solid #409eff;
}

@keyframes activePulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(64, 158, 255, 0);
  }
}

.sample-card.sample-completed {
  border-left: 4px solid #67c23a;
  animation: completedGlow 0.5s ease-out;
}

@keyframes completedGlow {
  0% {
    box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.7);
  }
  100% {
    box-shadow: 0 0 0 10px rgba(103, 194, 58, 0);
  }
}

.sample-card.sample-error {
  border-left: 4px solid #f56c6c;
  animation: errorShake 0.5s ease-in-out;
}

.sample-content {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  animation: contentExpand 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

@keyframes contentExpand {
  from {
    max-height: 0;
    opacity: 0;
  }
  to {
    max-height: 2000px;
    opacity: 1;
  }
}

.section-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #ebeef5;
  animation: slideInLeft 0.4s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.section-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.query-section,
.expected-answer-section,
.steps-section,
.answer-section,
.error-section,
.metrics-section {
  margin-bottom: 24px;
}

.query-content {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.query-text {
  color: #303133;
  line-height: 1.8;
  margin: 0;
  font-size: 14px;
}

.query-prompt {
  font-size: 15px;
  line-height: 1.8;
}

.query-prompt strong {
  color: #409eff;
  margin-right: 8px;
}

.query-text-full {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.text-muted {
  color: #909399;
  font-style: italic;
}

.expected-answer-content {
  background: #f0f9ff;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
}

.step-card {
  margin-top: 8px;
  border: 1px solid #ebeef5;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-number {
  font-weight: bold;
  color: #409eff;
  font-size: 14px;
}

.step-description {
  color: #303133;
  line-height: 1.8;
  margin: 8px 0;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.keyword-highlight {
  color: #409eff;
  font-weight: 600;
}

.step-details-pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

.keyword-highlight {
  color: #409eff;
  font-weight: 600;
}

.step-details-pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
}

.step-details {
  margin-top: 12px;
}

.step-details pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
  margin: 0;
}

.step-confidence {
  margin-top: 8px;
}

.answer-comparison {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.comparison-item {
  margin-bottom: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.comparison-item strong {
  color: #606266;
  margin-right: 8px;
}

.comparison-result {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 4px;
  font-weight: bold;
  text-align: center;
}

.comparison-result.match {
  background: #f0f9ff;
  color: #67c23a;
  border: 1px solid #67c23a;
}

.comparison-result:not(.match) {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #f56c6c;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.metric-label {
  color: #606266;
  font-size: 14px;
}

.metric-value {
  color: #303133;
  font-weight: bold;
  font-size: 14px;
}

/* 流程图样式 */
.flowchart-container {
  margin: 16px 0;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  min-height: 500px;
}

.flowchart-chart {
  min-height: 500px;
  width: 100%;
  background: white;
  border-radius: 4px;
  display: block;
}

/* 推理步骤内容样式 */
.step-content-enhanced {
  padding: 12px;
}

.step-premise {
  margin-bottom: 12px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 6px;
  border-left: 4px solid #e6a23c;
}

.premise-content {
  color: #303133;
  line-height: 1.8;
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  word-wrap: break-word;
  font-size: 14px;
}

.premise-keyword {
  color: #e6a23c;
  font-weight: 600;
}

.step-process {
  margin-bottom: 12px;
}

.step-label {
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-icon {
  font-size: 16px;
}

.step-description-enhanced {
  color: #303133;
  line-height: 1.8;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  word-wrap: break-word;
  font-size: 14px;
}

.step-conclusion {
  margin-top: 12px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  border-left: 4px solid #67c23a;
}

.conclusion-content {
  color: #303133;
  line-height: 1.8;
  max-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  word-wrap: break-word;
  font-size: 14px;
}

.conclusion-keyword {
  color: #67c23a;
  font-weight: 600;
}

/* 步骤输出指示器 */
.step-output-indicator {
  margin-top: 16px;
  padding: 12px;
  background: linear-gradient(90deg, rgba(103, 194, 58, 0.1) 0%, rgba(103, 194, 58, 0.05) 100%);
  border-radius: 8px;
  border-left: 3px solid #67c23a;
  display: flex;
  align-items: center;
  gap: 12px;
}

.output-line {
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, #67c23a 0%, rgba(103, 194, 58, 0.3) 100%);
  position: relative;
}

.output-line::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 6px solid #67c23a;
}

.output-label {
  color: #67c23a;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
}

/* 🚀 改进：参考 fogsight 的动画设计，添加骨架屏加载动画 */
.loading-skeleton {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  animation: skeletonFadeIn 0.3s ease-out;
}

@keyframes skeletonFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.skeleton-tag {
  width: 60px;
  height: 24px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeletonShimmer 1.5s infinite;
}

.skeleton-text {
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeletonShimmer 1.5s infinite;
  flex: 1;
}

.skeleton-text.short {
  width: 100px;
  flex: none;
}

.skeleton-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: skeletonShimmer 1.5s infinite;
}

.skeleton-line:nth-child(1) {
  width: 100%;
  animation-delay: 0s;
}

.skeleton-line:nth-child(2) {
  width: 90%;
  animation-delay: 0.1s;
}

.skeleton-line:nth-child(3) {
  width: 80%;
  animation-delay: 0.2s;
}

.skeleton-line.short {
  width: 60%;
}

@keyframes skeletonShimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.step-details-enhanced {
  margin-top: 12px;
}

/* 🚀 改进：流程图式推理过程展示 */
.reasoning-flow-animated {
  position: relative;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 流程开始节点 */
.flow-start {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
  animation: fadeInDown 0.5s ease-out;
}

.flow-start-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 80px;
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  color: white;
  font-weight: bold;
}

.flow-start-icon {
  font-size: 32px;
  margin-bottom: 4px;
}

.flow-start-text {
  font-size: 14px;
}

/* 流程结束节点 */
.flow-end {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
  animation: fadeInUp 0.5s ease-out;
}

.flow-end-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 80px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  color: white;
  font-weight: bold;
}

.flow-end-icon {
  font-size: 32px;
  margin-bottom: 4px;
}

.flow-end-text {
  font-size: 14px;
}

/* 流程连接线 */
.flow-connector-line {
  width: 3px;
  height: 40px;
  background: linear-gradient(180deg, #67c23a 0%, #409eff 100%);
  margin: 10px 0;
  animation: lineGrow 0.6s ease-out;
  position: relative;
}

.flow-connector-line::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 8px solid #409eff;
}

@keyframes lineGrow {
  from {
    height: 0;
    opacity: 0;
  }
  to {
    height: 40px;
    opacity: 1;
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.reasoning-step-wrapper-animated {
  position: relative;
  width: 100%;
  max-width: 900px;
  opacity: 0;
  animation: stepFadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  margin-bottom: 30px;
}

/* 🚀 新增：新添加步骤的动画效果 */
.reasoning-step-wrapper-animated.step-newly-added {
  animation: stepFadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes stepFadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 步骤连接线和箭头 */
.step-connector-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 15px;
  position: relative;
}

.step-connector-line {
  width: 3px;
  height: 30px;
  background: linear-gradient(180deg, #409eff 0%, rgba(64, 158, 255, 0.5) 100%);
  animation: connectorGrow 0.5s ease-out forwards;
  position: relative;
}

.step-connector-arrow {
  margin-top: -2px;
  animation: arrowFadeIn 0.5s ease-out 0.3s forwards;
  opacity: 0;
}

/* 🚀 新增：新添加步骤的连接线和箭头动画 */
.step-connector-wrapper.connector-newly-added .step-connector-line {
  animation: connectorGrow 0.5s ease-out forwards;
}

.step-connector-wrapper.connector-newly-added .step-connector-arrow {
  animation: arrowFadeIn 0.5s ease-out 0.3s forwards;
}

@keyframes arrowFadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes connectorGrow {
  from {
    height: 0;
    opacity: 0;
  }
  to {
    height: 30px;
    opacity: 1;
  }
}

.reasoning-step-card {
  background: white;
  border-radius: 16px;
  border: 2px solid #e4e7ed;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  width: 100%;
}

.reasoning-step-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  background: #409eff;
  transition: width 0.3s ease;
}

.reasoning-step-card::after {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.reasoning-step-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: #409eff;
}

.reasoning-step-card:hover::before {
  width: 6px;
}

.reasoning-step-card:hover::after {
  opacity: 1;
}

.reasoning-step-card.step-type-reasoning::before {
  background: #409eff;
}

.reasoning-step-card.step-type-evidence::before {
  background: #67c23a;
}

.reasoning-step-card.step-type-search::before {
  background: #e6a23c;
}

.reasoning-step-card.step-type-conclusion::before {
  background: #f56c6c;
}

.step-header-enhanced {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-bottom: 1px solid #ebeef5;
}

/* 🚀 新增：步骤展开/折叠图标样式 */
.step-expand-icon {
  margin-left: auto;
  transition: transform 0.3s ease;
  cursor: pointer;
  font-size: 14px;
  color: #909399;
}

.step-expand-icon.expanded {
  transform: rotate(180deg);
}

.step-expand-icon:hover {
  color: #409eff;
}

/* step-title-row 样式已存在，不需要重复定义 */

.step-number-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  position: relative;
  flex-shrink: 0;
  animation: badgePop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
}

@keyframes badgePop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.step-icon {
  font-size: 20px;
  margin-right: 4px;
}

.step-num {
  font-size: 16px;
}

.step-header-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.step-type-tag {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.step-time {
  color: #909399;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .sample-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

/* 🚀 新增：TensorBoard 嵌入视图样式 */
.tensorboard-embedded-view {
  display: flex;
  flex-direction: column;
  height: 800px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.tensorboard-container {
  flex: 1;
  position: relative;
  min-height: 600px;
}

.tensorboard-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.tensorboard-controls {
  padding: 16px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.view-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>

