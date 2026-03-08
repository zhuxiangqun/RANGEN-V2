<template>
  <div class="evaluation-results">
    <el-card v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </el-card>
    
    <el-card v-else-if="!evaluationResult" class="empty-state">
      <el-empty description="暂无评测结果，请点击运行评测按钮开始评测" />
    </el-card>
    
    <div v-else class="results-container">
      <!-- 评测摘要 -->
      <el-card class="summary-card">
        <template #header>
          <div class="card-header">
            <span>📊 评测摘要</span>
            <el-tag :type="getOverallStatusType()" size="large">
              {{ getOverallStatus() }}
            </el-tag>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <el-statistic 
              title="准确率" 
              :value="evaluationResult.accuracy || 0" 
              :precision="2" 
              suffix="%"
            >
              <template #prefix>
                <el-icon style="color: #409eff;"><Trophy /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-statistic 
              title="样本成功率" 
              :value="evaluationResult.success_rate || 0" 
              :precision="2" 
              suffix="%"
            >
              <template #prefix>
                <el-icon style="color: #67c23a;"><SuccessFilled /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-statistic 
              title="平均耗时" 
              :value="evaluationResult.avg_time || 0" 
              :precision="2" 
              suffix="秒"
            >
              <template #prefix>
                <el-icon style="color: #e6a23c;"><Timer /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-statistic 
              title="样本数量" 
              :value="evaluationResult.sample_count || 0"
            >
              <template #prefix>
                <el-icon style="color: #909399;"><Document /></el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <!-- 分析报告 -->
      <el-card v-if="evaluationResult.analysis" class="analysis-card">
        <template #header>
          <div class="card-header">
            <span>📈 分析报告</span>
            <div>
              <el-button size="small" @click="copyReport" v-if="evaluationResult.report">
                <el-icon><DocumentCopy /></el-icon>
                复制完整报告
              </el-button>
              <el-button size="small" @click="downloadReport" v-if="evaluationResult.report">
                <el-icon><Download /></el-icon>
                下载完整报告
              </el-button>
            </div>
          </div>
        </template>
        <el-tabs v-model="activeAnalysisTab" type="border-card">
          <!-- 系统智能化程度 -->
          <el-tab-pane label="系统智能化" name="intelligence">
            <div class="analysis-content">
              <div ref="intelligenceChart" class="chart-container"></div>
              <!-- 🚀 新增：显示对应的详细报告内容 -->
              <div v-if="evaluationResult.report" class="report-section">
                <h3>详细分析</h3>
                <div class="markdown-content" v-html="getReportSection('intelligence')"></div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 性能指标 -->
          <el-tab-pane label="性能指标" name="performance">
            <div class="analysis-content">
              <div ref="performanceChart" class="chart-container"></div>
              <!-- 🚀 新增：显示对应的详细报告内容 -->
              <div v-if="evaluationResult.report" class="report-section">
                <h3>详细分析</h3>
                <div class="markdown-content" v-html="getReportSection('performance')"></div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 学习能力 -->
          <el-tab-pane label="学习能力" name="learning">
            <div class="analysis-content">
              <div ref="learningChart" class="chart-container"></div>
              <!-- 🚀 新增：显示对应的详细报告内容 -->
              <div v-if="evaluationResult.report" class="report-section">
                <h3>详细分析</h3>
                <div class="markdown-content" v-html="getReportSection('learning')"></div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- FRAMES指标 -->
          <el-tab-pane label="FRAMES指标" name="frames">
            <div class="analysis-content">
              <div ref="framesChart" class="chart-container"></div>
              <!-- 🚀 新增：显示对应的详细报告内容 -->
              <div v-if="evaluationResult.report" class="report-section">
                <h3>详细分析</h3>
                <div class="markdown-content" v-html="getReportSection('frames')"></div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
      
      <!-- 完整报告（可折叠） -->
      <el-card class="details-card">
        <template #header>
          <div class="card-header">
            <span>📄 完整报告</span>
            <el-button size="small" @click="showFullReport = !showFullReport">
              {{ showFullReport ? '收起' : '展开' }}
            </el-button>
          </div>
        </template>
        <div v-show="showFullReport" class="report-content">
          <div v-if="evaluationResult.report" class="markdown-content" v-html="renderedReport"></div>
          <div v-else-if="evaluationResult.html_report" class="report-html" v-html="evaluationResult.html_report"></div>
          <el-empty v-else description="报告内容为空" />
        </div>
      </el-card>
      
      <!-- 执行输出 -->
      <el-card v-if="evaluationResult.stdout || evaluationResult.stderr" class="output-card">
        <template #header>
          <span>📋 执行输出</span>
        </template>
        <el-alert
          v-if="evaluationResult.success === false"
          title="评测执行失败"
          type="error"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <div class="output-content">
          <div v-if="evaluationResult.stdout" class="stdout">
            <h4>标准输出:</h4>
            <pre>{{ evaluationResult.stdout }}</pre>
          </div>
          <div v-if="evaluationResult.stderr" class="stderr">
            <h4>错误输出:</h4>
            <pre>{{ evaluationResult.stderr }}</pre>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Download, Trophy, SuccessFilled, Timer, Document } from '@element-plus/icons-vue'
import { marked } from 'marked'
import * as echarts from 'echarts'

const props = defineProps({
  evaluationResult: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const activeAnalysisTab = ref('intelligence')
const showFullReport = ref(false)
const intelligenceChart = ref(null)
const performanceChart = ref(null)
const learningChart = ref(null)
const framesChart = ref(null)

// 🚀 修复：使用对象包装，以便在函数中修改
const intelligenceChartInstance = { value: null }
const performanceChartInstance = { value: null }
const learningChartInstance = { value: null }
const framesChartInstance = { value: null }

// 渲染Markdown报告
const renderedReport = computed(() => {
  if (!props.evaluationResult?.report) return ''
  try {
    return marked.parse(props.evaluationResult.report)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return `<pre>${props.evaluationResult.report}</pre>`
  }
})

// 🚀 新增：获取报告中的特定部分
const getReportSection = (section) => {
  if (!props.evaluationResult?.report) return ''
  
  const report = props.evaluationResult.report
  let sectionContent = ''
  
  try {
    // 根据标签页名称提取对应的报告部分
    switch (section) {
      case 'intelligence':
        // 提取"系统智能化程度"部分
        const intelligenceMatch = report.match(/##\s*2\.\s*系统智能化程度[\s\S]*?(?=##|$)/)
        if (intelligenceMatch) {
          sectionContent = intelligenceMatch[0]
        }
        break
      case 'performance':
        // 提取"系统性能"部分
        const performanceMatch = report.match(/##\s*5\.\s*系统性能[\s\S]*?(?=##|$)/)
        if (performanceMatch) {
          sectionContent = performanceMatch[0]
        }
        break
      case 'learning':
        // 提取"系统自我学习程度"部分
        const learningMatch = report.match(/##\s*4\.\s*系统自我学习程度[\s\S]*?(?=##|$)/)
        if (learningMatch) {
          sectionContent = learningMatch[0]
        }
        break
      case 'frames':
        // 提取"FRAMES评测基准指标"部分
        const framesMatch = report.match(/##\s*1\.\s*FRAMES评测基准指标[\s\S]*?(?=##|$)/)
        if (framesMatch) {
          sectionContent = framesMatch[0]
        }
        break
    }
    
    if (sectionContent) {
      return marked.parse(sectionContent)
    }
  } catch (error) {
    console.error('解析报告部分失败:', error)
  }
  
  return sectionContent ? `<pre>${sectionContent}</pre>` : '<p>暂无相关内容</p>'
}

// 获取整体状态
const getOverallStatus = () => {
  const accuracy = props.evaluationResult?.accuracy || 0
  if (accuracy >= 90) return '优秀'
  if (accuracy >= 70) return '良好'
  if (accuracy >= 50) return '一般'
  return '需改进'
}

const getOverallStatusType = () => {
  const accuracy = props.evaluationResult?.accuracy || 0
  if (accuracy >= 90) return 'success'
  if (accuracy >= 70) return 'warning'
  return 'danger'
}

// 复制报告
const copyReport = () => {
  if (props.evaluationResult?.report) {
    navigator.clipboard.writeText(props.evaluationResult.report).then(() => {
      ElMessage.success('报告已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}

// 下载报告
const downloadReport = () => {
  if (!props.evaluationResult?.report) return
  
  const blob = new Blob([props.evaluationResult.report], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `evaluation_report_${new Date().getTime()}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('报告下载成功')
}

// 初始化图表
// 🚀 修复：检查DOM元素是否准备好且有尺寸，并且可见
const checkElementReady = (element) => {
  if (!element) return false
  const rect = element.getBoundingClientRect()
  const style = window.getComputedStyle(element)
  // 检查元素是否有尺寸、是否可见（display不为none，visibility不为hidden）
  return rect.width > 0 && rect.height > 0 && 
         style.display !== 'none' && 
         style.visibility !== 'hidden' &&
         style.opacity !== '0'
}

// 🚀 修复：为每个图表单独初始化，支持重试
const initSingleChart = async (chartRef, chartInstanceRef, initFn, chartName, maxRetries = 10) => {
  if (!chartRef.value) return false
  
  let retryCount = 0
  const tryInit = async () => {
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100)) // 等待标签页切换动画完成
    
    // 🚀 修复：检查 chartRef 是否仍然存在（可能在重试过程中被销毁）
    if (!chartRef.value) return false
    
    if (!checkElementReady(chartRef.value)) {
      retryCount++
      if (retryCount < maxRetries) {
        setTimeout(tryInit, 200)
        return false
      }
      // 超过重试次数，跳过这个图表（但不输出警告，因为可能是标签页未激活）
      return false
    }
    
    // DOM已准备好，初始化图表
    // 🚀 修复：chartInstanceRef 是一个对象引用，直接修改其属性
    if (chartInstanceRef.value) {
      chartInstanceRef.value.dispose()
    }
    chartInstanceRef.value = echarts.init(chartRef.value)
    initFn(chartInstanceRef.value)
    return true
  }
  
  return await tryInit()
}

const initCharts = async () => {
  await nextTick()
  
  if (!props.evaluationResult?.analysis) return
  
  const analysis = props.evaluationResult.analysis
  
  // 🚀 修复：根据当前激活的标签页，只初始化对应的图表
  const currentTab = activeAnalysisTab.value
  
  // 系统智能化程度图表
  if (currentTab === 'intelligence' && intelligenceChart.value && analysis.intelligence) {
    await initSingleChart(
      intelligenceChart,
      intelligenceChartInstance,
      (instance) => {
        const intelligenceData = analysis.intelligence
        const option = {
          title: {
            text: '系统智能化程度',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' }
          },
          radar: {
            indicator: [
              { name: '整体智能', max: 1 },
              { name: 'AI算法', max: 1 },
              { name: '学习能力', max: 1 },
              { name: '推理能力', max: 1 }
            ],
            center: ['50%', '60%'],
            radius: '70%'
          },
          series: [{
            type: 'radar',
            data: [{
              value: [
                intelligenceData.overall || 0,
                intelligenceData.ai_algorithm || 0,
                intelligenceData.learning || 0,
                intelligenceData.reasoning || 0
              ],
              name: '智能化程度',
              areaStyle: {
                color: 'rgba(64, 158, 255, 0.3)'
              }
            }]
          }]
        }
        instance.setOption(option)
      },
      '智能化程度'
    )
  }
  
  // 性能指标图表
  if (currentTab === 'performance' && performanceChart.value && analysis.performance) {
    await initSingleChart(
      performanceChart,
      performanceChartInstance,
      (instance) => {
        const perfData = analysis.performance
        const option = {
          title: {
            text: '系统性能指标',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis'
          },
          xAxis: {
            type: 'category',
            data: ['平均时间', '最大时间', '最小时间', '缓存命中率']
          },
          yAxis: {
            type: 'value'
          },
          series: [{
            data: [
              perfData.avg_time || 0,
              perfData.max_time || 0,
              perfData.min_time || 0,
              perfData.cache_hit_rate || 0
            ],
            type: 'bar',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }]
        }
        instance.setOption(option)
      },
      '性能指标'
    )
  }
  
  // 学习能力图表
  if (currentTab === 'learning' && learningChart.value && analysis.learning) {
    await initSingleChart(
      learningChart,
      learningChartInstance,
      (instance) => {
        const learningData = analysis.learning
        const option = {
          title: {
            text: '系统学习能力',
            left: 'center'
          },
          tooltip: {
            trigger: 'item'
          },
          series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: true,
              formatter: '{b}: {c} ({d}%)'
            },
            data: [
              { value: learningData.ml_score || 0, name: 'ML学习' },
              { value: learningData.rl_score || 0, name: 'RL学习' },
              { value: learningData.self_learning_score || 0, name: '自我学习' }
            ]
          }]
        }
        instance.setOption(option)
      },
      '学习能力'
    )
  }
  
  // FRAMES指标图表
  if (currentTab === 'frames' && framesChart.value && analysis.frames) {
    await initSingleChart(
      framesChart,
      framesChartInstance,
      (instance) => {
        const framesData = analysis.frames
        const option = {
          title: {
            text: 'FRAMES评测指标',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis'
          },
          xAxis: {
            type: 'category',
            data: ['平均准确率', '平均推理步骤', '创新性分数']
          },
          yAxis: {
            type: 'value'
          },
          series: [{
            data: [
              framesData.average_accuracy || 0,
              framesData.average_steps || 0,
              (framesData.innovation_score || 0) * 100
            ],
            type: 'line',
            smooth: true,
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
                { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
              ])
            },
            itemStyle: {
              color: '#67c23a'
            }
          }]
        }
        instance.setOption(option)
      },
      'FRAMES指标'
    )
  }
}

// 监听数据变化，重新渲染图表
watch(() => props.evaluationResult, () => {
  if (props.evaluationResult?.analysis) {
    initCharts()
  }
}, { deep: true })

// 监听标签页切换，重新渲染图表
watch(activeAnalysisTab, () => {
  // 🚀 修复：等待标签页切换动画完成后再初始化图表
  nextTick(() => {
    setTimeout(() => {
      initCharts()
    }, 150) // 等待 el-tabs 的切换动画完成
  })
})

onMounted(() => {
  if (props.evaluationResult?.analysis) {
    initCharts()
  }
  
  // 窗口大小改变时重新调整图表
  window.addEventListener('resize', () => {
    intelligenceChartInstance.value?.resize()
    performanceChartInstance.value?.resize()
    learningChartInstance.value?.resize()
    framesChartInstance.value?.resize()
  })
})
</script>

<style scoped>
.evaluation-results {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-card,
.analysis-card,
.details-card,
.output-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.markdown-content {
  background: white;
  padding: 24px;
  border-radius: 4px;
  line-height: 1.8;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}

.markdown-content :deep(h1) {
  font-size: 24px;
  border-bottom: 2px solid #e4e7ed;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 20px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 6px;
}

.markdown-content :deep(h3) {
  font-size: 16px;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 12px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 6px 0;
}

.markdown-content :deep(code) {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.report-html {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.analysis-content {
  padding: 16px;
}

.chart-container {
  width: 100%;
  height: 400px;
  min-height: 400px;
  margin-bottom: 24px;
}

.report-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.report-section h3 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.output-content {
  margin-top: 16px;
}

.output-content h4 {
  margin: 12px 0 8px 0;
  color: #606266;
  font-size: 14px;
  font-weight: 600;
}

.stdout pre,
.stderr pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.stderr pre {
  background: #fef0f0;
  color: #f56c6c;
}
</style>
