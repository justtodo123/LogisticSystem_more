import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import {
  clearAuthStorage,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
} from '@/utils/auth-storage'
import type { UserRole } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const role = ref<UserRole | null>(null)
  const displayName = ref('')
  const username = ref('')
  const isReady = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isDispatcher = computed(() => role.value === 'dispatcher')

  function clearSession(): void {
    token.value = null
    role.value = null
    displayName.value = ''
    username.value = ''
    clearAuthStorage()
  }

  function persistSession(): void {
    if (!token.value || !role.value) return
    setToken(token.value)
    setStoredUser({
      username: username.value,
      role: role.value,
      displayName: displayName.value,
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
    }

    try {
      const me = await authApi.getMe()
      username.value = me.username
      role.value = me.role
      displayName.value = me.display_name
      persistSession()
    } catch {
      clearSession()
    } finally {
      isReady.value = true
    }
  }

  function logout(): void {
    clearSession()
    window.location.href = '/login'
  }

  return {
    token,
    role,
    displayName,
    username,
    isReady,
    isLoggedIn,
    isDispatcher,
    login,
    restore,
    logout,
    clearSession,
  }
})
