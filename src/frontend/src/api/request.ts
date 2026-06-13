import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

// 阶段 1：在此添加 Authorization: Bearer {token}
request.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error),
)

// 阶段 1：在此处理 code !== 0 与 401 跳转登录
request.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error),
)

export default request
