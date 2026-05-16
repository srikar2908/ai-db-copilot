import type { AppUser } from '../types/auth'

export function getRoleLabel(user: AppUser | null) {
  return user?.role || 'analyst'
}

export function canUseQueryActions(user: AppUser | null) {
  return user?.role === 'developer' || user?.role === 'admin'
}

export function canUseAdminActions(user: AppUser | null) {
  return user?.role === 'admin'
}

export function getRoleBadgeClass(user: AppUser | null) {
  if (user?.role === 'admin') {
    return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200'
  }

  if (user?.role === 'developer') {
    return 'border-cyan-400/20 bg-cyan-400/10 text-cyan-200'
  }

  return 'border-amber-400/20 bg-amber-400/10 text-amber-200'
}

