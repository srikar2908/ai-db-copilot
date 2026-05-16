import { NavLink } from 'react-router-dom'

import type { AppUser } from '../../types/auth'
import { getRoleBadgeClass, getRoleLabel } from '../../utils/roles'

type SidebarProps = {
  user: AppUser | null
}

const navItems = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Connections', to: '/connections' },
  { label: 'Query History', to: '/history' },
]

function Sidebar({ user }: SidebarProps) {
  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800 bg-slate-950 px-4 py-5 lg:w-72">
      <div className="flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-md border border-cyan-400/30 bg-cyan-400/10 text-sm font-bold text-cyan-200">
          AI
        </div>
        <div>
          <p className="text-sm font-semibold text-white">AI SQL Copilot</p>
          <p className="text-xs text-slate-500">Enterprise workspace</p>
        </div>
      </div>

      <nav className="mt-8 space-y-1">
        {navItems.map((item) => {
          return (
            <NavLink
              className={({ isActive }) =>
                `flex w-full items-center rounded-md px-3 py-2.5 text-left text-sm font-medium transition ${
                  isActive
                  ? 'border border-cyan-400/20 bg-cyan-400/10 text-cyan-100'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100'
                }`
              }
              key={item.to}
              to={item.to}
            >
              {item.label}
            </NavLink>
          )
        })}
      </nav>

      <div className="mt-auto rounded-md border border-slate-800 bg-slate-900 p-4">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Signed in</p>
        <p className="mt-2 truncate text-sm font-medium text-slate-100">
          {user?.email || 'Unknown user'}
        </p>
        <p className="mt-1 text-xs text-slate-500">{user?.tenant_id || 'No tenant selected'}</p>
        <span className={`mt-3 inline-flex rounded-md border px-2.5 py-1 text-xs font-medium ${getRoleBadgeClass(user)}`}>
          {getRoleLabel(user)} access
        </span>
      </div>
    </aside>
  )
}

export default Sidebar
