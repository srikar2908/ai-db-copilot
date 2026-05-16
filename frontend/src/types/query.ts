export type QueryRequest = {
  thread_id: string
  connection_ref: string
  user_prompt: string
}

export type QueryResponse = {
  thread_id?: string
  generated_sql: string
  approval_required?: boolean
  risk_level?: string | null
  validation_result?: ValidationResult | null
}

export type ApprovalRequest = {
  thread_id: string
  approval_status: 'approved' | 'rejected'
  approved_sql?: string
}

export type ExecutionRow = Record<string, string | number | boolean | null>

export type ValidationResult = {
  passed?: boolean
  errors?: string[]
  warnings?: string[]
}

export type ExecutionResult = {
  success?: boolean
  rows_affected?: number
  rows_returned?: number
  data?: ExecutionRow[] | null
  execution_time_ms?: number
  error?: string | null
}

export type ApprovalResponse = {
  thread_id?: string
  approval_status?: string
  workflow_status?: string
  risk_level?: string | null
  validation_result?: ValidationResult | null
  execution_result?: ExecutionResult | null
}
