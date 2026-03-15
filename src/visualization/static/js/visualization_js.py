"""
可视化界面的 JavaScript 代码库

将 JavaScript 代码从 Python f-string 中提取出来，避免转义问题。
"""

# 主页 JavaScript
HOME_PAGE_JS = """
// 主页 JavaScript 代码
$(document).ready(function() {
    console.log('🏠 可视化主页加载完成');
    
    // 系统状态更新
    function updateSystemStatus() {
        $.ajax({
            url: '/api/system/status',
            method: 'GET',
            success: function(data) {
                if (data.success) {
                    $('#system-status').html(data.status);
                    $('#agent-count').text(data.agent_count);
                    $('#graph-count').text(data.graph_count);
                    $('#last-updated').text(new Date().toLocaleTimeString());
                }
            },
            error: function() {
                $('#system-status').html('<span style="color: #f44336;">状态获取失败</span>');
            }
        });
    }
    
    // 初始加载
    updateSystemStatus();
    
    // 每30秒更新一次状态
    setInterval(updateSystemStatus, 30000);
    
    // 快速操作按钮
    $('#btn-refresh-status').click(function() {
        updateSystemStatus();
        showToast('状态已刷新', 'success');
    });
    
    $('#btn-clear-cache').click(function() {
        if (confirm('确定要清除所有缓存吗？')) {
            $.ajax({
                url: '/api/system/clear-cache',
                method: 'POST',
                success: function() {
                    showToast('缓存已清除', 'success');
                },
                error: function() {
                    showToast('缓存清除失败', 'error');
                }
            });
        }
    });
});
"""

# 图页面 JavaScript
GRAPH_PAGE_JS = """
// 图可视化页面 JavaScript 代码
$(document).ready(function() {
    console.log('📊 图可视化页面加载完成');
    
    // 初始化图可视化
    var graphContainer = document.getElementById('graph-container');
    var graphData = null;
    
    // 加载图数据
    function loadGraphData(graphId) {
        $.ajax({
            url: '/api/graph/' + graphId,
            method: 'GET',
            success: function(data) {
                if (data.success) {
                    graphData = data.graph;
                    renderGraph(graphData);
                    updateGraphInfo(data.graph);
                } else {
                    showToast('图数据加载失败: ' + (data.error || '未知错误'), 'error');
                }
            },
            error: function(xhr) {
                showToast('图数据加载失败: ' + xhr.status + ' ' + xhr.statusText, 'error');
            }
        });
    }
    
    // 渲染图
    function renderGraph(graph) {
        if (!graph || !graph.nodes || !graph.edges) {
            graphContainer.innerHTML = '<div class="alert alert-warning">图数据格式错误</div>';
            return;
        }
        
        // 使用 cytoscape.js 或其他图可视化库
        // 这里简化为显示基本信息
        var nodeCount = graph.nodes.length;
        var edgeCount = graph.edges.length;
        
        graphContainer.innerHTML = `
            <div class="graph-summary">
                <h4>图信息</h4>
                <p>节点数: ${nodeCount}</p>
                <p>边数: ${edgeCount}</p>
                <p>类型: ${graph.type || '未指定'}</p>
                <p>创建时间: ${graph.created_at || '未知'}</p>
            </div>
            <div class="graph-visualization">
                <canvas id="graph-canvas"></canvas>
            </div>
        `;
        
        // 初始化 canvas 绘制
        initCanvasGraph(graph);
    }
    
    // 更新图信息
    function updateGraphInfo(graph) {
        $('#graph-title').text(graph.name || '未命名图');
        $('#graph-id').text(graph.id || '未知ID');
        $('#graph-description').text(graph.description || '无描述');
    }
    
    // 从URL获取图ID
    function getGraphIdFromUrl() {
        var path = window.location.pathname;
        var match = path.match(/\/graph\/([^\/]+)/);
        return match ? match[1] : null;
    }
    
    // 页面加载时获取图数据
    var initialGraphId = getGraphIdFromUrl();
    if (initialGraphId) {
        loadGraphData(initialGraphId);
    }
    
    // 刷新按钮
    $('#btn-refresh-graph').click(function() {
        var graphId = getGraphIdFromUrl();
        if (graphId) {
            loadGraphData(graphId);
            showToast('图数据刷新中...', 'info');
        }
    });
});
"""

# 监控页面 JavaScript
MONITOR_PAGE_JS = """
// 系统监控页面 JavaScript 代码
$(document).ready(function() {
    console.log('📈 监控页面加载完成');
    
    // 初始化监控图表
    var cpuChart = null;
    var memoryChart = null;
    var requestChart = null;
    
    // 加载监控数据
    function loadMonitorData() {
        $.ajax({
            url: '/api/monitor/metrics',
            method: 'GET',
            success: function(data) {
                if (data.success) {
                    updateCharts(data.metrics);
                    updateStats(data.stats);
                }
            },
            error: function() {
                showToast('监控数据加载失败', 'error');
            }
        });
    }
    
    // 更新图表
    function updateCharts(metrics) {
        // 更新 CPU 使用率图表
        if (cpuChart) {
            cpuChart.data.datasets[0].data = metrics.cpu_history;
            cpuChart.update('none');
        }
        
        // 更新内存使用率图表
        if (memoryChart) {
            memoryChart.data.datasets[0].data = metrics.memory_history;
            memoryChart.update('none');
        }
        
        // 更新请求频率图表
        if (requestChart) {
            requestChart.data.datasets[0].data = metrics.request_history;
            requestChart.update('none');
        }
    }
    
    // 更新统计信息
    function updateStats(stats) {
        $('#cpu-usage').text(stats.cpu_usage + '%');
        $('#memory-usage').text(stats.memory_usage + '%');
        $('#request-rate').text(stats.request_rate + '/分钟');
        $('#error-rate').text(stats.error_rate + '%');
        $('#avg-response-time').text(stats.avg_response_time + 'ms');
        
        // 更新健康状态
        var healthStatus = $('#health-status');
        healthStatus.removeClass('healthy warning critical');
        
        if (stats.health_status === 'healthy') {
            healthStatus.addClass('healthy').text('健康');
        } else if (stats.health_status === 'warning') {
            healthStatus.addClass('warning').text('警告');
        } else {
            healthStatus.addClass('critical').text('异常');
        }
    }
    
    // 初始化图表
    function initCharts() {
        var ctxCpu = document.getElementById('cpu-chart').getContext('2d');
        cpuChart = new Chart(ctxCpu, {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => (i + 1) + '秒前'),
                datasets: [{
                    label: 'CPU 使用率 (%)',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        var ctxMemory = document.getElementById('memory-chart').getContext('2d');
        memoryChart = new Chart(ctxMemory, {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => (i + 1) + '秒前'),
                datasets: [{
                    label: '内存使用率 (%)',
                    data: [],
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        var ctxRequest = document.getElementById('request-chart').getContext('2d');
        requestChart = new Chart(ctxRequest, {
            type: 'bar',
            data: {
                labels: Array.from({length: 10}, (_, i) => (i + 1) + '分钟前'),
                datasets: [{
                    label: '请求频率 (次/分钟)',
                    data: [],
                    backgroundColor: '#FF9800',
                    borderColor: '#F57C00'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // 初始化页面
    initCharts();
    loadMonitorData();
    
    // 每10秒更新一次监控数据
    setInterval(loadMonitorData, 10000);
    
    // 导出监控数据
    $('#btn-export-metrics').click(function() {
        $.ajax({
            url: '/api/monitor/export',
            method: 'GET',
            success: function(data) {
                if (data.success) {
                    var blob = new Blob([JSON.stringify(data.metrics, null, 2)], {type: 'application/json'});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = 'monitor_metrics_' + new Date().toISOString().split('T')[0] + '.json';
                    a.click();
                    URL.revokeObjectURL(url);
                    showToast('监控数据导出成功', 'success');
                }
            },
            error: function() {
                showToast('监控数据导出失败', 'error');
            }
        });
    });
});
"""

# 通用工具函数
COMMON_JS = """
// 通用 JavaScript 工具函数

// 显示 Toast 通知
function showToast(message, type = 'info', duration = 3000) {
    // 移除现有的 Toast
    $('.toast-container').remove();
    
    // 创建 Toast 容器
    var toastContainer = $('<div class="toast-container"></div>');
    
    // 设置 Toast 样式
    var toastClass = 'toast-' + type;
    var toast = $(`
        <div class="toast ${toastClass}">
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close">&times;</button>
            </div>
        </div>
    `);
    
    // 添加到页面
    toastContainer.append(toast);
    $('body').append(toastContainer);
    
    // 自动消失
    var timeout = setTimeout(function() {
        toast.fadeOut(300, function() {
            $(this).remove();
            if ($('.toast-container').children().length === 0) {
                $('.toast-container').remove();
            }
        });
    }, duration);
    
    // 点击关闭
    toast.find('.toast-close').click(function() {
        clearTimeout(timeout);
        toast.fadeOut(300, function() {
            $(this).remove();
            if ($('.toast-container').children().length === 0) {
                $('.toast-container').remove();
            }
        });
    });
    
    // 显示 Toast
    toast.hide().fadeIn(300);
}

// 显示加载进度
function showLoadingProgress(show = true, message = '加载中...', progress = 0) {
    var loadingEl = $('#loading-progress');
    
    if (show) {
        if (loadingEl.length === 0) {
            loadingEl = $(`
                <div id="loading-progress" class="loading-overlay">
                    <div class="loading-content">
                        <div class="loading-spinner"></div>
                        <div class="loading-message">${message}</div>
                        <div class="loading-bar">
                            <div class="loading-progress" style="width: ${progress}%"></div>
                        </div>
                    </div>
                </div>
            `);
            $('body').append(loadingEl);
        } else {
            loadingEl.find('.loading-message').text(message);
            loadingEl.find('.loading-progress').css('width', progress + '%');
        }
        
        loadingEl.show();
    } else {
        if (loadingEl.length > 0) {
            loadingEl.fadeOut(300, function() {
                $(this).remove();
            });
        }
    }
}

// 格式化时间
function formatTime(timestamp) {
    if (!timestamp) return '未知时间';
    
    var date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化字节大小
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    var k = 1024;
    var dm = decimals < 0 ? 0 : decimals;
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// 防抖函数
function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this;
        var args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}
"""

# Agent 创建相关 JavaScript
AGENT_CREATION_JS = """
// Agent 创建相关 JavaScript 代码

// 显示 Agent 创建进度
function showAgentCreationProgress(show, progress, message, type = 'info') {
    var progressEl = $('#agent-creation-progress');
    
    if (show) {
        if (progressEl.length === 0) {
            progressEl = $(`
                <div id="agent-creation-progress" class="agent-creation-overlay">
                    <div class="agent-creation-content">
                        <h4>Agent 创建进度</h4>
                        <div class="agent-creation-message ${type}">${message}</div>
                        <div class="agent-creation-bar">
                            <div class="agent-creation-progress" style="width: ${progress}%"></div>
                        </div>
                        <div class="agent-creation-percentage">${progress}%</div>
                    </div>
                </div>
            `);
            $('body').append(progressEl);
        } else {
            progressEl.find('.agent-creation-message').text(message).removeClass('info success warning error').addClass(type);
            progressEl.find('.agent-creation-progress').css('width', progress + '%');
            progressEl.find('.agent-creation-percentage').text(progress + '%');
        }
        
        progressEl.show();
    } else {
        if (progressEl.length > 0) {
            progressEl.fadeOut(300, function() {
                $(this).remove();
            });
        }
    }
}

// 提交 Agent 创建表单
function submitAgentCreationForm(formData) {
    showAgentCreationProgress(true, 0, '正在提交 Agent 创建请求...', 'info');
    
    $.ajax({
        url: '/api/agents/create',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            if (response.success) {
                showAgentCreationProgress(true, 100, 'Agent 创建成功！ID: ' + (response.data.agent_id || '未知'), 'success');
                
                // 延迟跳转到 Agent 详情页
                setTimeout(function() {
                    window.location.href = '/agents/' + response.data.agent_id;
                }, 1500);
            } else {
                showAgentCreationProgress(true, 0, '创建失败: ' + (response.error || '未知错误'), 'error');
            }
        },
        error: function(xhr) {
            showAgentCreationProgress(true, 0, '请求失败: ' + xhr.status + ' ' + xhr.statusText, 'error');
        }
    });
}

// 验证 Agent 配置
function validateAgentConfig(config) {
    if (!config.name || config.name.trim() === '') {
        return {valid: false, error: 'Agent 名称不能为空'};
    }
    
    if (!config.capabilities || config.capabilities.length === 0) {
        return {valid: false, error: '至少需要选择一个能力'};
    }
    
    if (config.max_concurrent && config.max_concurrent < 1) {
        return {valid: false, error: '最大并发数必须大于0'};
    }
    
    return {valid: true};
}

// 加载 Agent 模板
function loadAgentTemplates() {
    $.ajax({
        url: '/api/agents/templates',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                var templateSelect = $('#agent-template');
                templateSelect.empty();
                templateSelect.append('<option value="">选择模板...</option>');
                
                response.data.templates.forEach(function(template) {
                    templateSelect.append('<option value="' + template.id + '">' + template.name + '</option>');
                });
                
                // 模板选择事件
                templateSelect.change(function() {
                    var templateId = $(this).val();
                    if (templateId) {
                        applyAgentTemplate(templateId);
                    }
                });
            }
        }
    });
}

// 应用 Agent 模板
function applyAgentTemplate(templateId) {
    $.ajax({
        url: '/api/agents/templates/' + templateId,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                var template = response.data.template;
                
                // 填充表单
                $('#agent-name').val(template.name || '');
                $('#agent-description').val(template.description || '');
                
                // 设置能力复选框
                if (template.capabilities) {
                    $('input[name="capabilities"]').prop('checked', false);
                    template.capabilities.forEach(function(capability) {
                        $('#capability-' + capability).prop('checked', true);
                    });
                }
                
                showToast('已应用模板: ' + template.name, 'success');
            }
        }
    });
}
"""

# 所有 JavaScript 代码的映射
JS_LIBRARY = {
    "home": HOME_PAGE_JS,
    "graph": GRAPH_PAGE_JS,
    "monitor": MONITOR_PAGE_JS,
    "common": COMMON_JS,
    "agent_creation": AGENT_CREATION_JS
}

def get_js_code(module_name):
    """
    获取指定模块的 JavaScript 代码
    
    Args:
        module_name: 模块名称 (home, graph, monitor, common, agent_creation)
    
    Returns:
        JavaScript 代码字符串
    """
    return JS_LIBRARY.get(module_name, "")

def get_all_js_code():
    """
    获取所有 JavaScript 代码
    
    Returns:
        合并后的 JavaScript 代码字符串
    """
    return "\n".join(JS_LIBRARY.values())