import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/auth/ProtectedRoute'
import PublicRoute from './components/auth/PublicRoute'
import Connections from './pages/Connections'
import Dashboard from './pages/Dashboard'
import QueryHistory from './pages/QueryHistory'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  )
}

export default App
