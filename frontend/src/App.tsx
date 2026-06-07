import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/auth/ProtectedRoute'
import PublicRoute from './components/auth/PublicRoute'
import LoadingSpinner from './components/ui/LoadingSpinner'

const Connections = lazy(() => import('./pages/Connections'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const QueryHistory = lazy(() => import('./pages/QueryHistory'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner label="Loading page..." />}>
        <Routes>
        <Route
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
          path="/login"
        />
        <Route
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
          path="/register"
        />
        <Route
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
          path="/dashboard"
        />
        <Route
          element={
            <ProtectedRoute>
              <Connections />
            </ProtectedRoute>
          }
          path="/connections"
        />
        <Route
          element={
            <ProtectedRoute>
              <QueryHistory />
            </ProtectedRoute>
          }
          path="/history"
        />
        <Route element={<Navigate replace to="/login" />} path="*" />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
