import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import { ROUTE_PERMISSIONS } from '@/constants/permissions'
import {
  clearAuthStorage,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
} from '@/utils/auth-storage'
import type { Permission, UserRole } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const role = ref<UserRole | null>(null)
  const displayName = ref('')
  const username = ref('')
  const permissions = ref<Permission[]>([])
  const isReady = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isDispatcher = computed(() => role.value === 'dispatcher' || role.value === 'admin')

  function can(permission: Permission): boolean {
    return permissions.value.includes(permission)
  }

  function firstAllowedPath(): string {
    const ordered = [
      '/dashboard',
      '/orders',
      '/goods',
      '/packages',
      '/vehicles',
      '/drivers',
      '/nodes/storage',
      '/exceptions',
      '/reports',
      '/notifications',
    ]
    for (const path of ordered) {
      const required = ROUTE_PERMISSIONS[path]
      if (!required || can(required)) return path
    }
    return '/login'
  }

  function clearSession(): void {
    token.value = null
    role.value = null
    displayName.value = ''
    username.value = ''
    permissions.value = []
    clearAuthStorage()
  }

  function persistSession(): void {
    if (!token.value || !role.value) return
    setToken(token.value)
    setStoredUser({
      username: username.value,
      role: role.value,
      displayName: displayName.value,
      permissions: permissions.value,
    })
  }

  async function login(loginUsername: string, password: string): Promise<void> {
    const result = await authApi.login({
      username: loginUsername,
      password,
    })
    token.value = result.access_token
    role.value = result.role
    displayName.value = result.display_name
    username.value = loginUsername
    persistSession()
    const me = await authApi.getMe()
    username.value = me.username
    role.value = me.role
    displayName.value = me.display_name
    permissions.value = me.permissions
    persistSession()
  }

  async function restore(): Promise<void> {
    if (isReady.value) return

    const savedToken = getToken()
    const savedUser = getStoredUser()

    if (!savedToken) {
      isReady.value = true
      return
    }

    token.value = savedToken
    if (savedUser) {
      role.value = savedUser.role
      displayName.value = savedUser.displayName
      username.value = savedUser.username
      permissions.value = savedUser.permissions ?? []
    }

    try {
      const me = await authApi.getMe()
      username.value = me.username
      role.value = me.role
      displayName.value = me.display_name
      permissions.value = me.permissions
      persistSession()
    } catch {
      clearSession()
    } finally {
      isReady.value = true
    }
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // Local session still needs to be cleared after revocation or network errors.
    }
    clearSession()
    window.location.href = '/login'
  }

  return {
    token,
    role,
    displayName,
    username,
    permissions,
    isReady,
    isLoggedIn,
    isDispatcher,
    can,
    firstAllowedPath,
    login,
    restore,
    logout,
    clearSession,
  }
})
