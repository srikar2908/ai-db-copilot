import type { ReactNode } from 'react'

type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

type BadgeProps = {
  children: ReactNode
  className?: string
  tone?: BadgeTone
}

const toneClasses: Record<BadgeTone, string> = {
  neutral: 'border-slate-700 bg-slate-950 text-slate-300',
  info: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-200',
  success: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200',
  warning: 'border-amber-400/20 bg-amber-400/10 text-amber-200',
  danger: 'border-red-400/20 bg-red-400/10 text-red-200',
}

function Badge({ children, className = '', tone = 'neutral' }: BadgeProps) {
  return (
    <span className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-medium ${toneClasses[tone]} ${className}`}>
      {children}
    </span>
  )
}

export default Badge

