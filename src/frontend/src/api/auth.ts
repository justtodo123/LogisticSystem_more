import request from './request'
import { getToken } from '@/utils/auth-storage'
import type { LoginPayload, LoginResult, UserInfo, UserRole } from '@/types/auth'

const MOCK_PASSWORD = '123456'

const MOCK_USERS: Record<
  string,
  { role: UserRole; display_name: string }
> = {
  dispatcher: { role: 'dispatcher', display_name: '调度员' },
  manager: { role: 'manager', display_name: '物流管理者' },
}

function useMockAuth(): boolean {
  return import.meta.env.VITE_USE_MOCK_AUTH === 'true'
}

function parseMockToken(token: string): UserRole | null {
  if (!token.startsWith('mock-token-')) return null
  const role = token.slice('mock-token-'.length) as UserRole
  if (role === 'dispatcher' || role === 'manager') return role
  return null
}

export async function login(payload: LoginPayload): Promise<LoginResult> {
  if (useMockAuth()) {
    if (payload.password !== MOCK_PASSWORD) {
      throw new Error('用户名或密码错误')
    }
    const user = MOCK_USERS[payload.username]
    if (!user) {
      throw new Error('用户名或密码错误')
    }
    return {
      access_token: `mock-token-${user.role}`,
      token_type: 'bearer',
      expires_in: 86400,
      role: user.role,
      display_name: user.display_name,
    }
  }
  const { data } = await request.post<LoginResult>('/auth/login', payload)
  return data
}

export async function getMe(): Promise<UserInfo> {
  if (useMockAuth()) {
    const token = getToken()
    if (!token) {
      throw new Error('未登录')
    }
    const role = parseMockToken(token)
    if (!role) {
      throw new Error('Token 无效')
    }
    const username = role === 'dispatcher' ? 'dispatcher' : 'manager'
    return {
      username,
      role,
      display_name: MOCK_USERS[username].display_name,
    }
  }
  const { data } = await request.get<UserInfo>('/auth/me')
  return data
}
