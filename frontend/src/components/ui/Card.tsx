import type { ReactNode } from 'react'

type CardProps = {
  children: ReactNode
  className?: string
}

function Card({ children, className = '' }: CardProps) {
  return (
    <section className={`rounded-lg border border-slate-800 bg-slate-900 p-5 ${className}`}>
      {children}
    </section>
  )
}

export default Card

