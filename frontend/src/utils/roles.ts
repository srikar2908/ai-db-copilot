import type { AppUser } from '../types/auth'

export function getRoleLabel(user: AppUser | null) {
  return user?.role || 'analyst'
}

/*
---------------------------------------------------
ANALYST
---------------------------------------------------
Allowed:
- Generate SELECT queries
- Execute safe read workflows
- View schema/results/history

Blocked:
- SQL editing
- Approvals
- Write queries
*/

export function canGenerateQueries(user: AppUser | null) {
  return (
    user?.role === 'analyst' ||
    user?.role === 'developer' ||
    user?.role === 'admin'
  )
}

/*
---------------------------------------------------
EDIT SQL
---------------------------------------------------
Only developer/admin
*/

export function canEditSql(user: AppUser | null) {
  return (
    user?.role === 'developer' ||
    user?.role === 'admin'
  )
}

/*
---------------------------------------------------
APPROVAL ACTIONS
---------------------------------------------------
Only developer/admin
*/

export function canApproveQueries(user: AppUser | null) {
  return (
    user?.role === 'developer' ||
    user?.role === 'admin'
  )
}

/*
---------------------------------------------------
ADMIN ONLY
---------------------------------------------------
*/

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