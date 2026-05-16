export type AppUser = {
  id: number
  email: string
  tenant_id: string
  role: string
}

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user: AppUser
}

export type RegisterRequest = {
  tenant_id: string
  email: string
  password: string
  full_name: string
  role: 'analyst' | 'developer' | 'admin'
}

export type RegisterResponse = {
  message?: string
  user_id?: number
  email?: string
}
