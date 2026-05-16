export type HistoryItem = {
  thread_id: string
  user_prompt: string
  generated_sql: string | null
  approval_status: string | null
  created_at: string
  risk_level: string | null
  execution_status?: string | null
  execution_result?: {
    success?: boolean
    error?: string | null
    rows_returned?: number
    rows_affected?: number
    execution_time_ms?: number
  } | null
  validation_result?: {
    errors?: string[]
    warnings?: string[]
  } | null
  errors?: string[] | null
}
