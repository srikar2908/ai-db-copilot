import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { isAuthenticated } from '../../utils/auth'

type PublicRouteProps = {
  children: ReactNode
}

function PublicRoute({ children }: PublicRouteProps) {
  if (isAuthenticated()) {
    return <Navigate replace to="/dashboard" />
  }

  return children
}

export default PublicRoute

