export type UserRole = 'dispatcher' | 'manager'

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  expires_in: number
  role: UserRole
  display_name: string
}

export interface UserInfo {
  username: string
  role: UserRole
  display_name: string
}

export interface StoredUser {
  username: string
  role: UserRole
  displayName: string
}
