export type UserRole =
  | 'admin'
  | 'dispatcher'
  | 'viewer'
  | 'manager'
  | 'warehouse_operator'

export type Permission = string

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
  is_active?: boolean
  permissions: Permission[]
}

export interface StoredUser {
  username: string
  role: UserRole
  displayName: string
  permissions: Permission[]
}
