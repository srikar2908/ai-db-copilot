import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import StatusBadge from '../components/StatusBadge'
import AppLayout from '../components/layout/AppLayout'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { connectionApi, getApiErrorMessage } from '../services/api'
import type { DatabaseConnection } from '../types/connection'
import { getStoredUser } from '../utils/auth'
import { getActiveConnectionRef, setActiveConnectionRef } from '../utils/connections'
import { canUseAdminActions } from '../utils/roles'

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function Connections() {
  const user = useMemo(() => getStoredUser(), [])
  const isAdmin = canUseAdminActions(user)
  const [connections, setConnections] = useState<DatabaseConnection[]>([])
  const [activeConnection, setActiveConnection] = useState(getActiveConnectionRef())
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [connectionRef, setConnectionRef] = useState(`${user?.tenant_id || 'tenant_001'}:supabase_prod`)
  const [databaseType, setDatabaseType] = useState('postgresql')
  const [databaseUrl, setDatabaseUrl] = useState('')

  useEffect(() => {
    document.title = 'Connections | AI SQL Copilot'
  }, [])

  async function loadConnections() {
    setIsLoading(true)

    try {
      const data = await connectionApi.listConnections()
      setConnections(data)

      const nextActive = getActiveConnectionRef() || data[0]?.connection_ref || ''
      setActiveConnection(nextActive)

      if (nextActive) {
        setActiveConnectionRef(nextActive)
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to load connections.'))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadConnections()
  }, [])

  const handleSelectConnection = (connectionRefValue: string) => {
    setActiveConnection(connectionRefValue)
    setActiveConnectionRef(connectionRefValue)
    setSuccess(`${connectionRefValue} is now the active dashboard connection.`)
  }

  const handleCreateConnection = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setIsCreating(true)

    try {
      await connectionApi.createConnection({
        connection_ref: connectionRef,
        database_type: databaseType,
        database_url: databaseUrl,
      })

      setIsModalOpen(false)
      setDatabaseUrl('')
      await loadConnections()
      handleSelectConnection(connectionRef)
      setSuccess('Connection created successfully.')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to create connection.'))
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <AppLayout
      subtitle="Manage tenant database targets for AI SQL workflows."
      title="Connections"
      user={user}
    >
      <div className="mx-auto max-w-7xl space-y-5">
        {error ? (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {success}
          </div>
        ) : null}

        <Card>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-xl font-semibold text-white">Database Connections</h1>
              <p className="mt-1 text-sm text-slate-400">
                Select which connection the dashboard should use for query generation.
              </p>
            </div>

            {isAdmin ? (
              <Button className="w-fit" onClick={() => setIsModalOpen(true)} type="button">
                Create Connection
              </Button>
            ) : (
              <Badge tone="neutral">Connection creation is admin-only</Badge>
            )}
          </div>

          {!isAdmin ? (
            <div className="mb-5 rounded-md border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
              Your role can view and select existing tenant connections. Admin users manage new connection setup.
            </div>
          ) : null}

          {isLoading ? (
            <LoadingSpinner label="Loading connections..." />
          ) : connections.length ? (
            <div className="grid gap-4 lg:grid-cols-2">
              {connections.map((connection) => {
                const isActive = activeConnection === connection.connection_ref

                return (
                  <article
                    className={`rounded-lg border p-5 transition ${
                      isActive
                        ? 'border-cyan-400/40 bg-cyan-400/5'
                        : 'border-slate-800 bg-slate-950 hover:border-slate-700'
                    }`}
                    key={connection.connection_ref}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h2 className="break-all text-base font-semibold text-white">
                          {connection.connection_ref}
                        </h2>
                        <p className="mt-2 text-sm text-slate-400">
                          Created {formatDate(connection.created_at)}
                        </p>
                      </div>
                      <StatusBadge value={connection.database_type} />
                    </div>

                    <div className="mt-5 flex items-center justify-between gap-3">
                      <Badge tone={isActive ? 'info' : 'neutral'}>
                        {isActive ? 'Active connection' : 'Available'}
                      </Badge>
                      <Button
                        className="px-3 py-1.5 text-xs"
                        disabled={isActive}
                        onClick={() => handleSelectConnection(connection.connection_ref)}
                        type="button"
                        variant="secondary"
                      >
                        {isActive ? 'Selected' : 'Select'}
                      </Button>
                    </div>
                  </article>
                )
              })}
            </div>
          ) : (
            <EmptyState
              description={
                isAdmin
                  ? 'Create a tenant database connection to start running AI SQL workflows.'
                  : 'Ask an admin to add a tenant database connection before running workflows.'
              }
              title="No connections found"
            />
          )}
        </Card>

        {isModalOpen ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-5 py-8">
            <section className="w-full max-w-lg rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-slate-950">
              <div className="mb-5">
                <h2 className="text-lg font-semibold text-white">Create Connection</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Add a tenant database URL using the existing backend connection endpoint.
                </p>
              </div>

              <form className="space-y-4" onSubmit={handleCreateConnection}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="connection_ref">
                    Connection ref
                  </label>
                  <input
                    className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                    id="connection_ref"
                    onChange={(event) => setConnectionRef(event.target.value)}
                    required
                    value={connectionRef}
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="database_type">
                    Database type
                  </label>
                  <select
                    className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                    id="database_type"
                    onChange={(event) => setDatabaseType(event.target.value)}
                    value={databaseType}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="supabase">Supabase</option>
                    <option value="sqlite">SQLite</option>
                  </select>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="database_url">
                    Database URL
                  </label>
                  <textarea
                    className="min-h-24 w-full resize-y rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm text-slate-100 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                    id="database_url"
                    onChange={(event) => setDatabaseUrl(event.target.value)}
                    placeholder="postgresql+asyncpg://user:password@host:5432/database"
                    required
                    value={databaseUrl}
                  />
                </div>

                <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                  <Button onClick={() => setIsModalOpen(false)} type="button" variant="secondary">
                    Cancel
                  </Button>
                  <Button isLoading={isCreating} type="submit">
                    Create Connection
                  </Button>
                </div>
              </form>
            </section>
          </div>
        ) : null}
      </div>
    </AppLayout>
  )
}

export default Connections
