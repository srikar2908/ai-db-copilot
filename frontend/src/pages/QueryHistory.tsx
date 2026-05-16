import { useEffect, useMemo, useState } from 'react'

import StatusBadge from '../components/StatusBadge'
import AppLayout from '../components/layout/AppLayout'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { getApiErrorMessage, historyApi } from '../services/api'
import type { HistoryItem } from '../types/history'
import { getStoredUser } from '../utils/auth'

function formatDate(value?: string | null) {
  if (!value) {
    return 'Unknown date'
  }

  const parsedDate = new Date(value)

  if (Number.isNaN(parsedDate.getTime())) {
    return 'Invalid date'
  }

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(parsedDate)
}

function formatRelativeTime(value?: string | null) {
  if (!value) {
    return 'Unknown'
  }

  const parsedDate = new Date(value)

  if (Number.isNaN(parsedDate.getTime())) {
    return 'Unknown'
  }

  const diffMs = Date.now() - parsedDate.getTime()

  const diffMinutes = Math.max(1, Math.round(diffMs / 60000))

  if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? 'min' : 'mins'} ago`
  }

  const diffHours = Math.round(diffMinutes / 60)

  if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`
  }

  const diffDays = Math.round(diffHours / 24)

  return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`
}

function getDisplayStatus(item: HistoryItem) {
  if (
    item.execution_status === 'failed' ||
    item.execution_result?.success === false
  ) {
    return 'failed'
  }

  if (item.approval_status === 'pending') {
    return 'pending review'
  }

  return item.approval_status || 'unknown'
}

function QueryHistory() {
  const user = useMemo(() => getStoredUser(), [])

  const [history, setHistory] = useState<HistoryItem[]>([])
  const [expandedThreadId, setExpandedThreadId] = useState<string | null>(null)
  const [modalSql, setModalSql] = useState<string | null>(null)

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    document.title = 'Query History | AI SQL Copilot'
  }, [])

  useEffect(() => {
    async function loadHistory() {
      try {
        setIsLoading(true)

        const data = await historyApi.listHistory()

        console.log('HISTORY DATA:', data)

        setHistory(Array.isArray(data) ? data : [])
      } catch (requestError) {
        console.error(requestError)

        setError(
          getApiErrorMessage(
            requestError,
            'Unable to load query history.',
          ),
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadHistory()
  }, [])

  const filteredHistory = history.filter((item) => {
    const query = searchTerm.toLowerCase()

    const matchesSearch =
      (item.thread_id || '')
        .toLowerCase()
        .includes(query) ||
      (item.user_prompt || '')
        .toLowerCase()
        .includes(query) ||
      (item.generated_sql || '')
        .toLowerCase()
        .includes(query)

    const displayStatus = getDisplayStatus(item)

    const matchesStatus =
      statusFilter === 'all' ||
      displayStatus === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <AppLayout
      subtitle="Review recent tenant workflow runs and generated SQL."
      title="Query History"
      user={user}
    >
      <div className="mx-auto max-w-7xl space-y-5">

        {error ? (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        <Card>

          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-xl font-semibold text-white">
                Workflow Runs
              </h1>

              <p className="mt-1 text-sm text-slate-400">
                Latest tenant-isolated SQL generation and approval activity.
              </p>
            </div>

            <span className="w-fit rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-400">
              {filteredHistory.length} of {history.length} runs
            </span>
          </div>

          <div className="mb-5 grid gap-3 md:grid-cols-[1fr_12rem]">

            <input
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search prompt, SQL, or thread ID..."
              value={searchTerm}
            />

            <select
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
              onChange={(event) => setStatusFilter(event.target.value)}
              value={statusFilter}
            >
              <option value="all">All statuses</option>
              <option value="pending review">Pending review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="failed">Failed</option>
            </select>

          </div>

          {isLoading ? (
            <LoadingSpinner label="Loading query history..." />
          ) : filteredHistory.length ? (

            <div className="overflow-hidden rounded-md border border-slate-800">

              <div className="overflow-x-auto">

                <table className="min-w-full divide-y divide-slate-800 text-left text-sm">

                  <thead className="bg-slate-950">

                    <tr>

                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        Prompt
                      </th>

                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        Status
                      </th>

                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        Risk
                      </th>

                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        Created
                      </th>

                      <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        SQL
                      </th>

                    </tr>

                  </thead>

                  <tbody className="divide-y divide-slate-800 bg-slate-900">

                    {filteredHistory.map((item) => {

                      const isExpanded =
                        expandedThreadId === item.thread_id

                      const displayStatus =
                        getDisplayStatus(item)

                      const executionError =
                        item.execution_result?.error ||
                        item.errors?.[0] ||
                        null

                      return (

                        <tr
                          className={`align-top transition hover:bg-slate-950/70 ${
                            displayStatus === 'failed'
                              ? 'bg-red-950/10'
                              : ''
                          }`}
                          key={item.thread_id}
                        >

                          <td className="max-w-sm px-4 py-4 text-slate-200">

                            <p className="font-medium">
                              {displayStatus === 'failed'
                                ? 'Failed: '
                                : ''}
                              {item.user_prompt}
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                              {item.thread_id}
                            </p>

                          </td>

                          <td className="px-4 py-4">
                            <StatusBadge value={displayStatus} />
                          </td>

                          <td className="px-4 py-4">
                            <StatusBadge
                              value={item.risk_level || 'unknown'}
                            />
                          </td>

                          <td className="whitespace-nowrap px-4 py-4 text-slate-400">

                            <p>
                              {formatRelativeTime(item.created_at)}
                            </p>

                            <p className="mt-1 text-xs text-slate-600">
                              {formatDate(item.created_at)}
                            </p>

                          </td>

                          <td className="min-w-80 px-4 py-4">

                            <Button
                              className="mb-3 px-3 py-1.5 text-xs"
                              onClick={() =>
                                setExpandedThreadId(
                                  isExpanded
                                    ? null
                                    : item.thread_id,
                                )
                              }
                              type="button"
                              variant="secondary"
                            >
                              {isExpanded
                                ? 'Hide SQL'
                                : 'Preview SQL'}
                            </Button>

                            {isExpanded ? (

                              <div className="space-y-3">

                                <pre className="max-h-64 overflow-auto rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs leading-5 text-cyan-100">
                                  {item.generated_sql ||
                                    '-- No SQL captured for this run.'}
                                </pre>

                                {executionError ? (
                                  <pre className="max-h-48 overflow-auto rounded-md border border-red-400/20 bg-red-500/10 p-3 font-mono text-xs leading-5 text-red-100">
                                    {executionError}
                                  </pre>
                                ) : null}

                                <Button
                                  className="px-3 py-1.5 text-xs"
                                  onClick={() =>
                                    setModalSql(
                                      item.generated_sql ||
                                        '-- No SQL captured for this run.',
                                    )
                                  }
                                  type="button"
                                  variant="secondary"
                                >
                                  Open SQL Preview
                                </Button>

                              </div>

                            ) : null}

                          </td>

                        </tr>
                      )
                    })}

                  </tbody>

                </table>

              </div>

            </div>

          ) : (

            <EmptyState
              description="Try clearing filters, or generate and approve a query from the dashboard."
              title="No workflow history found"
            />

          )}

        </Card>

        {modalSql ? (

          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-5 py-8">

            <section className="w-full max-w-4xl rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-2xl shadow-slate-950">

              <div className="mb-4 flex items-center justify-between gap-3">

                <div>
                  <h2 className="text-lg font-semibold text-white">
                    SQL Preview
                  </h2>

                  <p className="mt-1 text-sm text-slate-400">
                    Scrollable generated SQL from workflow history.
                  </p>
                </div>

                <Button
                  onClick={() => setModalSql(null)}
                  type="button"
                  variant="secondary"
                >
                  Close
                </Button>

              </div>

              <pre className="max-h-[70vh] overflow-auto rounded-md border border-slate-800 bg-slate-950 p-4 font-mono text-sm leading-6 text-cyan-100">
                {modalSql}
              </pre>

            </section>

          </div>

        ) : null}

      </div>
    </AppLayout>
  )
}

export default QueryHistory