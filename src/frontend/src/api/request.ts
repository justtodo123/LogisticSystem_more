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

const rawRequest = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

interface ApiBody {
  code?: number
  message?: string
  data?: unknown
}

export interface ApiBodyWithMeta extends ApiBody {
  meta?: {
    degraded?: boolean
    degraded_reason?: string | null
  }
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

function handleApiError(body: ApiBody | undefined, config?: InternalAxiosRequestConfig): void {
  if (body?.code === 40100 || body?.code === 40101) {
    if (!shouldSkipUnauthorizedRedirect(config)) {
      clearAuthAndRedirectLogin()
    }
    throw new Error(body.message || '未授权')
  }
  if (body?.code != null && body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
}

function unwrapResponseData(response: AxiosResponse): AxiosResponse {
  const body = response.data as ApiBody | unknown

  if (body && typeof body === 'object' && 'code' in body) {
    const apiBody = body as ApiBody
    handleApiError(apiBody, response.config)
    return { ...response, data: apiBody.data }
  }

  return response
}

function attachAuth(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

request.interceptors.request.use(attachAuth)
rawRequest.interceptors.request.use(attachAuth)

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

rawRequest.interceptors.response.use(
  (response) => response,
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

export interface BusinessCodeResult<T> {
  data: T | null
  meta: { degraded: boolean; degraded_reason: string | null }
  pending?: boolean
  message?: string
}

/** 保留 meta；50100 等业务占位码不 throw（用于 /ai/explain 等 P1 端点） */
export async function postWithBusinessCode<T>(
  url: string,
  body?: unknown,
  config?: { timeout?: number; pendingCodes?: number[] },
): Promise<BusinessCodeResult<T>> {
  const pendingCodes = config?.pendingCodes ?? [50100]
  const response = await rawRequest.post<ApiBodyWithMeta>(url, body, config)
  const apiBody = response.data

  if (apiBody.code === 40100 || apiBody.code === 40101) {
    handleApiError(apiBody, response.config)
  }

  const meta = {
    degraded: apiBody.meta?.degraded ?? false,
    degraded_reason: apiBody.meta?.degraded_reason ?? null,
  }

  if (apiBody.code != null && pendingCodes.includes(apiBody.code)) {
    return {
      data: null,
      meta,
      pending: true,
      message: apiBody.message,
    }
  }

  handleApiError(apiBody, response.config)

  return {
    data: apiBody.data as T,
    meta,
    message: apiBody.message,
  }
}

/** 保留 meta 字段（用于 /ai/parse 等需展示降级的接口） */
export async function postWithMeta<T>(
  url: string,
  body?: unknown,
  config?: { timeout?: number },
): Promise<{ data: T; meta: { degraded: boolean; degraded_reason: string | null } }> {
  const response = await rawRequest.post<ApiBodyWithMeta>(url, body, config)
  const apiBody = response.data
  handleApiError(apiBody, response.config)
  return {
    data: apiBody.data as T,
    meta: {
      degraded: apiBody.meta?.degraded ?? false,
      degraded_reason: apiBody.meta?.degraded_reason ?? null,
    },
  }
}

export default request
