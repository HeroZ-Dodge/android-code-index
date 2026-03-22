import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.PROD ? '/' : '/api',
  timeout: 30000,
})

// 响应拦截：捕获网络错误，分发事件供顶部 Banner 处理
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      window.dispatchEvent(new CustomEvent('api:network-error', { detail: error }))
    }
    return Promise.reject(error)
  }
)

export default client
