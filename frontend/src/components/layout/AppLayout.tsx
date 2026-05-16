import type { ReactNode } from 'react'

import type { AppUser } from '../../types/auth'
import Sidebar from './Sidebar'
import TopNavbar from './TopNavbar'

type AppLayoutProps = {
  children: ReactNode
  subtitle?: string
  title: string
  user: AppUser | null
}

function AppLayout({ children, subtitle, title, user }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="grid min-h-screen lg:grid-cols-[18rem_1fr]">
        <div className="hidden lg:block">
          <Sidebar user={user} />
        </div>

        <div className="flex min-w-0 flex-col">
          <TopNavbar subtitle={subtitle} title={title} user={user} />
          <div className="border-b border-slate-800 bg-slate-950 px-5 py-4 lg:hidden">
            <Sidebar user={user} />
          </div>
          <main className="flex-1 px-5 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
