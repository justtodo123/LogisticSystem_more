import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { clearAuthStorage, getToken } from '@/utils/auth-storage'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

interface ApiBody {
  code?: number
  message?: string
  data?: unknown
}

function shouldSkipUnauthorizedRedirect(config?: InternalAxiosRequestConfig): boolean {
  const url = config?.url ?? ''
  if (url.includes('/auth/login')) return true
  return window.location.pathname.startsWith('/login')
}

function clearAuthAndRedirectLogin(): void {
  clearAuthStorage()
  if (!window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

function unwrapResponseData(response: AxiosResponse): AxiosResponse {
  const body = response.data as ApiBody | unknown

  if (body && typeof body === 'object' && 'code' in body) {
    const apiBody = body as ApiBody

    if (apiBody.code === 40100 || apiBody.code === 40101) {
      if (!shouldSkipUnauthorizedRedirect(response.config)) {
        clearAuthAndRedirectLogin()
      }
      throw new Error(apiBody.message || '未授权')
    }

    if (apiBody.code !== 0) {
      throw new Error(apiBody.message || '请求失败')
    }

    return { ...response, data: apiBody.data }
  }

  return response
}

request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => unwrapResponseData(response),
  (error: AxiosError<ApiBody>) => {
    const status = error.response?.status
    const code = error.response?.data?.code

    if (
      (status === 401 || code === 40100 || code === 40101) &&
      !shouldSkipUnauthorizedRedirect(error.config)
    ) {
      clearAuthAndRedirectLogin()
    }

    const message =
      error.response?.data?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  },
)

export default request
