import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { isAuthenticated } from '../../utils/auth'

type ProtectedRouteProps = {
  children: ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate replace to="/login" />
  }

  return children
}

export default ProtectedRoute
