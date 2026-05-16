import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import { authApi, getApiErrorMessage } from '../services/api'
import type { RegisterRequest } from '../types/auth'

const roles: RegisterRequest['role'][] = ['analyst', 'developer', 'admin']

function Register() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenantId, setTenantId] = useState('tenant_001')
  const [role, setRole] = useState<RegisterRequest['role']>('analyst')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    document.title = 'Register | AI SQL Copilot'
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setIsLoading(true)

    try {
      await authApi.register({
        tenant_id: tenantId,
        email,
        password,
        full_name: fullName,
        role,
      })

      navigate('/login', {
        replace: true,
        state: { message: 'Registration successful. Sign in with your new account.' },
      })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to register this user.'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen items-center justify-center px-6 py-12">
        <section className="w-full max-w-md rounded-lg border border-slate-800 bg-slate-900 p-8 shadow-2xl shadow-slate-950">
          <div className="mb-8">
            <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-md border border-cyan-400/30 bg-cyan-400/10 text-sm font-semibold text-cyan-200">
              AI
            </div>
            <h1 className="text-2xl font-semibold tracking-normal text-white">
              Create AI SQL Copilot account
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Register a tenant user to test analyst, developer, and admin workflows.
            </p>
          </div>

          {error ? (
            <div className="mb-5 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="full_name">
                Full name
              </label>
              <input
                autoComplete="name"
                className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoading}
                id="full_name"
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Avery Morgan"
                required
                value={fullName}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="email">
                Email address
              </label>
              <input
                autoComplete="email"
                className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoading}
                id="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="analyst@test.com"
                required
                type="email"
                value={email}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="password">
                Password
              </label>
              <input
                autoComplete="new-password"
                className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoading}
                id="password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Minimum 6 characters"
                required
                type="password"
                value={password}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="tenant_id">
                  Tenant ID
                </label>
                <input
                  className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                  disabled={isLoading}
                  id="tenant_id"
                  onChange={(event) => setTenantId(event.target.value)}
                  placeholder="tenant_001"
                  required
                  value={tenantId}
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="role">
                  Role
                </label>
                <select
                  className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                  disabled={isLoading}
                  id="role"
                  onChange={(event) => setRole(event.target.value as RegisterRequest['role'])}
                  value={role}
                >
                  {roles.map((roleOption) => (
                    <option key={roleOption} value={roleOption}>
                      {roleOption}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <Button className="w-full py-3" isLoading={isLoading} type="submit">
              Create account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link className="font-semibold text-cyan-300 transition hover:text-cyan-200" to="/login">
              Login
            </Link>
          </p>
        </section>
      </div>
    </main>
  )
}

export default Register
