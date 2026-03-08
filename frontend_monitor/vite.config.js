import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { readFileSync } from 'fs'

// 🚀 修复：从 .env 文件读取配置（如果存在）
function getApiUrl() {
  try {
    const envFile = resolve(__dirname, '.env')
    const envContent = readFileSync(envFile, 'utf-8')
    const match = envContent.match(/VITE_API_URL=(.+)/)
    if (match) {
      return match[1].trim()
    }
  } catch (e) {
    // .env 文件不存在，使用默认值
  }
  // 优先使用环境变量，如果没有则默认使用5001（避免AirPlay冲突）
  return process.env.VITE_API_URL || 'http://localhost:8000'
}

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // 🚀 修复：从 .env 文件或环境变量读取，默认使用5001（避免AirPlay冲突）
        // 注意：由于 macOS AirPlay 占用 5000 端口，默认使用 5001
        target: getApiUrl(),
        changeOrigin: true,
        // 🚀 新增：添加错误处理
        onError: (err, req, res) => {
          console.error('🚨 Vite代理错误:', err.message)
          if (err.code === 'ECONNREFUSED') {
            console.error('❌ 无法连接到后端服务器，请检查：')
            console.error('   1. 后端服务是否正在运行')
            console.error('   2. 后端端口是否正确（5000 或 5001）')
            console.error('   3. 环境变量 VITE_API_URL 是否设置正确')
          }
        },
        // 支持SSE流式传输
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.url.includes('/logs/stream')) {
              // 禁用缓冲以支持SSE
              proxyReq.setHeader('Cache-Control', 'no-cache')
              proxyReq.setHeader('Connection', 'keep-alive')
              proxyReq.setHeader('X-Accel-Buffering', 'no')
            }
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            if (req.url.includes('/logs/stream')) {
              // 确保SSE响应头正确设置
              proxyRes.headers['Cache-Control'] = 'no-cache'
              proxyRes.headers['Connection'] = 'keep-alive'
              proxyRes.headers['X-Accel-Buffering'] = 'no'
            }
          })
        },
        // 🚀 新增：SSE需要特殊配置
        ws: false, // 禁用WebSocket，使用SSE
        timeout: 0 // 禁用超时，保持长连接
      }
    }
  }
})

