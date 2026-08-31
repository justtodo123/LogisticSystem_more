import request from './request'
import { getToken } from '@/utils/auth-storage'
import { MOCK_ROLE_PERMISSIONS } from '@/constants/permissions'
import type { LoginPayload, LoginResult, Permission, UserInfo, UserRole } from '@/types/auth'

const MOCK_PASSWORD = '123456'

const MOCK_USERS: Record<string, { role: UserRole; display_name: string }> = {
  admin: { role: 'admin', display_name: 'Admin' },
  dispatcher: { role: 'dispatcher', display_name: 'Dispatcher' },
  manager: { role: 'manager', display_name: 'Manager' },
  viewer: { role: 'viewer', display_name: 'Viewer' },
  warehouse_operator: { role: 'warehouse_operator', display_name: 'Warehouse' },
}

function useMockAuth(): boolean {
  return import.meta.env.VITE_USE_MOCK_AUTH === 'true'
}

function isUserRole(role: string): role is UserRole {
  return role in MOCK_ROLE_PERMISSIONS
}

function parseMockToken(token: string): UserRole | null {
  if (!token.startsWith('mock-token-')) return null
  const role = token.slice('mock-token-'.length)
  return isUserRole(role) ? role : null
}

function permissionsFor(role: UserRole): Permission[] {
  return [...MOCK_ROLE_PERMISSIONS[role]]
}

export async function login(payload: LoginPayload): Promise<LoginResult> {
  if (useMockAuth()) {
    if (payload.password !== MOCK_PASSWORD) {
      throw new Error('invalid username or password')
    }
    const user = MOCK_USERS[payload.username]
    if (!user) {
      throw new Error('invalid username or password')
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
      throw new Error('not logged in')
    }
    const role = parseMockToken(token)
    if (!role) {
      throw new Error('invalid token')
    }
    const username = Object.keys(MOCK_USERS).find((name) => MOCK_USERS[name].role === role) ?? role
    return {
      username,
      role,
      display_name: MOCK_USERS[username]?.display_name ?? role,
      is_active: true,
      permissions: permissionsFor(role),
    }
  }
  const { data } = await request.get<UserInfo>('/auth/me')
  return {
    ...data,
    permissions: Array.isArray(data.permissions) ? data.permissions : [],
  }
}

export async function logout(): Promise<void> {
  if (useMockAuth()) return
  await request.post('/auth/logout')
}
