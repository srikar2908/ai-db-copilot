import type { AppUser } from '../types/auth'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user'
const ACTIVE_CONNECTION_KEY = 'active_connection_ref'

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function isAuthenticated() {
  return Boolean(getAuthToken())
}

export function persistAuth(token: string, user: AppUser) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getStoredUser(): AppUser | null {
  const user = localStorage.getItem(USER_KEY)

  if (!user) {
    return null
  }

  try {
    return JSON.parse(user) as AppUser
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(ACTIVE_CONNECTION_KEY)
}
