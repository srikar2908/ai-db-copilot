import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import { authApi, getApiErrorMessage } from '../services/api'
import { persistAuth } from '../utils/auth'

function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('admin@test.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    document.title = 'Login | AI SQL Copilot'
  }, [])

  useEffect(() => {
    const state = location.state as { message?: string } | null

    if (state?.message) {
      setSuccessMessage(state.message)
    }
  }, [location.state])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSuccessMessage('')
    setIsLoading(true)

    try {
      const data = await authApi.login({
        email,
        password,
      })

      persistAuth(data.access_token, data.user)
      navigate('/dashboard', { replace: true })
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          'Unable to sign in. Check your credentials and try again.',
        ),
      )
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
              Sign in to AI SQL Copilot
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Access tenant analytics, query intelligence, and approval workflows.
            </p>
          </div>

          {successMessage ? (
            <div className="mb-5 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              {successMessage}
            </div>
          ) : null}

          {error ? (
            <div className="mb-5 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="email">
                Email address
              </label>
              <input
                autoComplete="email"
                className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoading}
                id="email"
                name="email"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="admin@test.com"
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
                autoComplete="current-password"
                className="block w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoading}
                id="password"
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                required
                type="password"
                value={password}
              />
            </div>

            <Button className="w-full py-3" isLoading={isLoading} type="submit">
              Sign in
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            Don&apos;t have an account?{' '}
            <Link className="font-semibold text-cyan-300 transition hover:text-cyan-200" to="/register">
              Register
            </Link>
          </p>
        </section>
      </div>
    </main>
  )
}

export default Login
