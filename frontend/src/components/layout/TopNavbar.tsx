import { useNavigate } from 'react-router-dom'

import type { AppUser } from '../../types/auth'
import { logout } from '../../utils/auth'
import { getRoleBadgeClass, getRoleLabel } from '../../utils/roles'

type TopNavbarProps = {
  subtitle?: string
  title: string
  user: AppUser | null
}

function TopNavbar({ subtitle, title, user }: TopNavbarProps) {
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="flex flex-col gap-3 border-b border-slate-800 bg-slate-950/95 px-5 py-4 sm:flex-row sm:items-center sm:justify-between lg:px-8">
      <div>
        <p className="text-sm font-semibold text-white">{title}</p>
        <p className="text-xs text-slate-500">{subtitle || 'Enterprise AI SQL workspace.'}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-md border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-200">
          Tenant: {user?.tenant_id || 'unknown'}
        </span>
        <span className={`rounded-md border px-3 py-1.5 text-xs font-medium ${getRoleBadgeClass(user)}`}>
          Role: {getRoleLabel(user)}
        </span>
        <button
          className="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-red-400/50 hover:bg-red-500/10 hover:text-red-100"
          onClick={handleLogout}
          type="button"
        >
          Logout
        </button>
      </div>
    </header>
  )
}

export default TopNavbar
