import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import MetricCard from '../components/MetricCard'
import AppLayout from '../components/layout/AppLayout'
import DataTable from '../components/table/DataTable'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import { connectionApi, getApiErrorMessage, historyApi, queryApi, schemaApi } from '../services/api'
import type { DatabaseConnection } from '../types/connection'
import type { HistoryItem } from '../types/history'
import type { ExecutionResult, ExecutionRow, ValidationResult } from '../types/query'
import { getStoredUser } from '../utils/auth'
import { getActiveConnectionRef, setActiveConnectionRef } from '../utils/connections'

import {
  canApproveQueries,
  canEditSql,
  canGenerateQueries,
  canUseAdminActions,
  getRoleLabel,
} from '../utils/roles'

import SchemaExplorer from '../components/schema/SchemaExplorer'
import type { SchemaResponse } from '../types/schema'


function generateThreadId() {
  return `thread_${Date.now()}`
}

function isWriteSql(sql: string) {
  return /\b(insert|update|delete|drop|alter|truncate|create|merge|replace)\b/i.test(sql)
}

function Dashboard() {
  const user = useMemo(() => getStoredUser(), [])
  const canGenerate = canGenerateQueries(user)
  const canEdit = canEditSql(user)
  const canApprove = canApproveQueries(user)
  const isAdmin = canUseAdminActions(user)

  const [prompt, setPrompt] = useState('show employee names')
  const [threadId, setThreadId] = useState('')
  const [generatedSql, setGeneratedSql] = useState('')
  const [editableSql, setEditableSql] = useState('')
  const [isEditingSql, setIsEditingSql] = useState(false)
  const [approvalRequired, setApprovalRequired] = useState(false)
  const [results, setResults] = useState<ExecutionRow[]>([])
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'success' | 'failed'>('idle')
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [riskLevel, setRiskLevel] = useState<string | null>(null)
  const [connections, setConnections] = useState<DatabaseConnection[]>([])
  const [schema, setSchema] =
    useState<SchemaResponse | null>(null)

  const [isLoadingSchema, setIsLoadingSchema] =
    useState(false)

  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeConnectionRef, setActiveConnectionRefState] = useState(
    getActiveConnectionRef() || `${user?.tenant_id || 'tenant_001'}:supabase_prod`,
  )
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)
  const [isLoadingMeta, setIsLoadingMeta] = useState(true)

  useEffect(() => {
    document.title = 'Dashboard | AI SQL Copilot'
  }, [])

  useEffect(() => {
    async function loadDashboardMeta() {
      try {
        const [connectionData, historyData] = await Promise.all([
          connectionApi.listConnections(),
          historyApi.listHistory(),
        ])

        setConnections(connectionData)
        setHistory(historyData)

        const storedConnection = getActiveConnectionRef()
        const nextConnection =
          storedConnection ||
          connectionData[0]?.connection_ref ||
          `${user?.tenant_id || 'tenant_001'}:supabase_prod`

        setActiveConnectionRefState(nextConnection)
        setActiveConnectionRef(nextConnection)
      } catch (requestError) {
        setError(getApiErrorMessage(requestError, 'Unable to load dashboard metadata.'))
      } finally {
        setIsLoadingMeta(false)
      }
    }

    void loadDashboardMeta()
  }, [user?.tenant_id])


  useEffect(() => {

    async function loadSchema() {

      if (!activeConnectionRef) {
        return
      }

      try {

        setIsLoadingSchema(true)

        const schemaData =
          await schemaApi.getSchema(
            activeConnectionRef
          )

        setSchema(schemaData)

      } catch {

        setSchema(null)

      } finally {

        setIsLoadingSchema(false)
      }
    }

    void loadSchema()

  }, [activeConnectionRef])

  const executedCount = history.filter((item) => item.approval_status === 'approved').length
  const pendingCount = history.filter((item) => item.approval_status === 'pending').length
  const successRate = history.length ? Math.round((executedCount / history.length) * 100) : 0
  const sqlIsWrite = isWriteSql(editableSql)

  const roleMessage =
    user?.role === 'admin'
      ? 'Admin access: full workflow visibility and connection management.'
      : user?.role === 'developer'
        ? 'Developer access: generate, edit, and approve reviewed SQL workflows.'
        : 'Analyst access: read-only dashboard visibility; approval controls stay hidden.'

  const handleGenerateSql = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    setError('')
    setToast('')
    setGeneratedSql('')
    setEditableSql('')
    setIsEditingSql(false)
    setApprovalRequired(false)
    setResults([])
    setExecutionResult(null)
    setExecutionStatus('idle')
    setValidationResult(null)
    setRiskLevel(null)
    setIsGenerating(true)

    const newThreadId = generateThreadId()
    setThreadId(newThreadId)

    try {
      const response = await queryApi.generateSql({
        thread_id: newThreadId,
        connection_ref: activeConnectionRef,
        user_prompt: prompt,
      })

      setGeneratedSql(response.generated_sql)
      setEditableSql(response.generated_sql)
      setApprovalRequired(response.approval_required ?? true)
      setValidationResult(response.validation_result || null)
      setRiskLevel(response.risk_level || null)
      setToast('SQL generated. Review or edit before approval.')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to generate SQL. Please try again.'))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleApproval = async (approvalStatus: 'approved' | 'rejected') => {
    setError('')
    setToast('')
    setIsApproving(approvalStatus === 'approved')
    setIsRejecting(approvalStatus === 'rejected')

    try {
      const approvedSql =
        approvalStatus === 'approved' &&
        (editableSql.trim() !== generatedSql.trim() || executionStatus === 'failed')
          ? editableSql
          : undefined

      const response = await queryApi.approveQuery({
        thread_id: threadId,
        approval_status: approvalStatus,
        approved_sql: approvedSql,
      })

      if (approvalStatus === 'approved') {
        const nextExecutionResult = response.execution_result || null

        setExecutionResult(nextExecutionResult)
        setValidationResult(response.validation_result || validationResult)
        setRiskLevel(response.risk_level || riskLevel)
        setGeneratedSql(editableSql)
        setIsEditingSql(false)

        if (nextExecutionResult?.success === false) {
          setResults([])
          setExecutionStatus('failed')
          setApprovalRequired(true)
          setToast('')
          setError('')
        } else {
          setResults(nextExecutionResult?.data || [])
          setExecutionStatus('success')
          setApprovalRequired(false)
          setToast('Query approved and executed successfully.')
        }
      } else {
        setResults([])
        setExecutionResult(null)
        setExecutionStatus('idle')
        setApprovalRequired(false)
        setGeneratedSql('')
        setEditableSql('')
        setIsEditingSql(false)
        setToast('Query rejected. No SQL was executed.')
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to submit approval decision.'))
    } finally {
      setIsApproving(false)
      setIsRejecting(false)
    }
  }

  const handleConnectionChange = (connectionRef: string) => {
    setActiveConnectionRefState(connectionRef)
    setActiveConnectionRef(connectionRef)
    setToast(`Active connection set to ${connectionRef}.`)
  }

  const handleCopySql = async () => {
    if (!editableSql) {
      return
    }

    await navigator.clipboard.writeText(editableSql)
    setToast('SQL copied to clipboard.')
  }

  const handleInsertSchemaText = (
    value: string,
  ) => {

    setPrompt((prev) => {

      if (!prev.trim()) {
        return value
      }

      return `${prev} ${value}`
    })
  }

  return (
    <AppLayout
      subtitle="Ask, edit, approve, and execute tenant-scoped database queries."
      title="Dashboard"
      user={user}
    >
      <div className="mx-auto max-w-7xl space-y-5">
        {error ? (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        {toast ? (
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {toast}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard helper="Approved workflow runs" label="Queries Executed" value={executedCount} />
          <MetricCard helper="Tenant database targets" label="Active Connections" value={connections.length} />
          <MetricCard helper="Waiting for review" label="Pending Approvals" value={pendingCount} />
          <MetricCard helper="Approved vs total runs" label="Success Rate" value={`${successRate}%`} />
        </div>

        <Card>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Role testing summary</h2>
              <p className="mt-1 text-sm text-slate-400">{roleMessage}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone={user?.role === 'admin' ? 'success' : user?.role === 'developer' ? 'info' : 'warning'}>
                {getRoleLabel(user)} role
              </Badge>
              {sqlIsWrite ? (
                <Badge tone={isAdmin ? 'success' : 'warning'}>
                  {isAdmin ? 'Write SQL allowed visually' : 'Write SQL needs elevated review'}
                </Badge>
              ) : (
                <Badge tone="neutral">Read query workflow</Badge>
              )}
            </div>
          </div>
        </Card>

        <Card>
          <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h1 className="text-xl font-semibold text-white">AI Query Input</h1>
              <p className="mt-1 text-sm text-slate-400">
                Active connection: <span className="font-medium text-slate-300">{activeConnectionRef}</span>
              </p>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <select
                className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
                disabled={isLoadingMeta || isGenerating}
                onChange={(event) => handleConnectionChange(event.target.value)}
                value={activeConnectionRef}
              >
                {connections.length ? (
                  connections.map((connection) => (
                    <option key={connection.connection_ref} value={connection.connection_ref}>
                      {connection.connection_ref}
                    </option>
                  ))
                ) : (
                  <option value={activeConnectionRef}>{activeConnectionRef}</option>
                )}
              </select>

              <span className="w-fit rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-400">
                Thread: {threadId || 'Not generated'}
              </span>
            </div>
          </div>

          {user?.role === 'analyst' ? (
              <div className="mb-4 rounded-md border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
                Analyst access supports safe SELECT query generation and execution.
                SQL editing and approval actions are restricted.
              </div>
            ) : null}

            {isLoadingSchema ? (
              <div className="mt-4 rounded-md border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
                Loading database schema...
              </div>
            ) : schema ? (
              <div className="mt-5">
                <SchemaExplorer
                  onInsert={handleInsertSchemaText}
                  tables={schema.tables}
                />
              </div>
            ) : (
              <div className="mt-4 rounded-md border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                Unable to load schema for this connection.
              </div>
            )}
          <form className="space-y-4" onSubmit={handleGenerateSql}>
            <textarea
              className="min-h-36 w-full resize-y rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20"
              disabled={!canGenerate || isGenerating || isApproving || isRejecting}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask AI about your database..."
              required
              value={prompt}
            />

            {canGenerate  ? (
              <div className="flex justify-end">
                <Button disabled={!prompt.trim()} isLoading={isGenerating} type="submit">
                  Generate SQL
                </Button>
              </div>
            ) : null}
          </form>

        </Card>

        <Card>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Generated SQL</h2>
              <p className="mt-1 text-sm text-slate-400">Review and edit the generated query before approval.</p>
            </div>

            <div className="flex flex-wrap gap-2">
              {approvalRequired ? <Badge tone="warning">Approval required</Badge> : null}
              {riskLevel ? <Badge tone={riskLevel === 'high' || riskLevel === 'blocked' ? 'danger' : riskLevel === 'medium' ? 'warning' : 'info'}>{riskLevel} risk</Badge> : null}

              {generatedSql && !isEditingSql ? (
                <>
                  <Button className="px-3 py-1.5 text-xs" onClick={handleCopySql} type="button" variant="secondary">
                    Copy SQL
                  </Button>
                  <Button className="px-3 py-1.5 text-xs" onClick={() => setIsEditingSql(true)} type="button" variant="secondary">
                    Edit SQL
                  </Button>
                </>
              ) : null}

              {isEditingSql ? (
                <>
                  <Button
                    className="px-3 py-1.5 text-xs"
                    onClick={() => {

                      // -----------------------------------
                      // ANALYST WRITE SQL PROTECTION
                      // -----------------------------------

                      if (
                        user?.role === 'analyst' &&
                        isWriteSql(editableSql)
                      ) {

                        setError(
                          'Analyst role can only save SELECT queries.'
                        )

                        return
                      }

                      setGeneratedSql(editableSql)

                      setIsEditingSql(false)

                      setToast(
                        'SQL changes saved locally for approval.'
                      )
                    }}
                    type="button"
                    variant="success"
                  >
                    Save Changes
                  </Button>
                  <Button
                    className="px-3 py-1.5 text-xs"
                    onClick={() => {
                      setEditableSql(generatedSql)
                      setIsEditingSql(false)
                    }}
                    type="button"
                    variant="secondary"
                  >
                    Cancel Edit
                  </Button>
                </>
              ) : null}
            </div>
          </div>

          <textarea
            className="min-h-52 w-full resize-y rounded-md border border-slate-800 bg-slate-950 p-4 font-mono text-sm leading-6 text-cyan-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 disabled:text-slate-400"
            disabled={!isEditingSql}
            onChange={(event) => setEditableSql(event.target.value)}
            placeholder="-- Generated SQL will appear here after you ask AI about your database."
            value={editableSql}
          />

          {validationResult?.warnings?.length ? (
            <div className="mt-4 rounded-md border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
              <p className="font-semibold">Validation warnings</p>
              <ul className="mt-2 list-inside list-disc space-y-1">
                {validationResult.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {validationResult?.errors?.length ? (
            <div className="mt-4 rounded-md border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-100">
              <p className="font-semibold">Validation errors</p>
              <ul className="mt-2 list-inside list-disc space-y-1">
                {validationResult.errors.map((validationError) => (
                  <li key={validationError}>{validationError}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>

        {executionStatus === 'success' ? (
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            Execution completed successfully.
          </div>
        ) : null}

        {executionStatus !== 'success' ? (
        <Card>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Approval</h2>
            <p className="mt-1 text-sm text-slate-400">
              {executionStatus === 'failed'
                ? 'Edit the SQL if needed, then retry execution without refreshing the page.'
                : 'Approve to execute the reviewed SQL, or reject to discard this request.'}
            </p>
          </div>

          {(canApprove || user?.role === 'analyst') ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                disabled={!generatedSql || !approvalRequired || isEditingSql || isRejecting || (
                      user?.role === 'analyst' &&
                      isWriteSql(editableSql)
                    )
        }
                isLoading={isApproving}
                onClick={() => void handleApproval('approved')}
                type="button"
                variant="success"
              >
                {executionStatus === 'failed' ? 'Retry Query' : 'Approve'}
              </Button>

              <Button
                disabled={!generatedSql || !approvalRequired || isApproving}
                isLoading={isRejecting}
                onClick={() => void handleApproval('rejected')}
                type="button"
                variant="danger"
              >
                Reject
              </Button>
            </div>
          ) : (
            <div className="rounded-md border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-400">
              This workflow requires elevated privileges.
            </div>
          )}
        </Card>
        ) : null}

        <Card>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Query Results</h2>
            <p className="mt-1 text-sm text-slate-400">
              Approved query execution results render dynamically from backend rows.
            </p>
          </div>

          {executionStatus === 'success' ? (
            <div className="mb-4 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
              Query returned {executionResult?.rows_returned ?? results.length} rows in{' '}
              {Math.round(executionResult?.execution_time_ms || 0)} ms.
            </div>
          ) : null}

          {executionStatus === 'failed' ? (
            <div className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              <p className="font-semibold">Query execution failed</p>
              <pre className="mt-3 max-h-40 overflow-auto rounded-md border border-red-400/20 bg-slate-950 p-3 font-mono text-xs leading-5 text-red-100">
                {executionResult?.error || 'The database returned an execution error.'}
              </pre>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  disabled={isEditingSql || isRejecting  ||
    (
      user?.role === 'analyst' &&
      isWriteSql(editableSql)
    )}
                  isLoading={isApproving}
                  onClick={() => void handleApproval('approved')}
                  type="button"
                  variant="danger"
                >
                  Retry Query
                </Button>
                {generatedSql  ? (
                      <Button
                        onClick={() => setIsEditingSql(true)}
                        type="button"
                        variant="secondary"
                      >
                        Edit SQL
                      </Button>
                    ) : null}
              </div>
            </div>
          ) : null}

          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Rows returned</p>
              <p className="mt-2 text-sm font-semibold text-slate-100">
                {executionResult?.rows_returned ?? results.length}
              </p>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Execution time</p>
              <p className="mt-2 text-sm font-semibold text-slate-100">
                {executionResult ? `${Math.round(executionResult.execution_time_ms || 0)} ms` : 'Not run'}
              </p>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Workflow status</p>
              <p className="mt-2 text-sm font-semibold capitalize text-slate-100">{executionStatus}</p>
            </div>
          </div>

          <DataTable rows={results} />
        </Card>
      </div>
    </AppLayout>
  )
}

export default Dashboard
