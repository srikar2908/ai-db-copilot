export type DatabaseConnection = {
  tenant_id: string
  connection_ref: string
  database_type: string
  created_at: string
  owner_user_id: number
}

export type CreateConnectionRequest = {
  connection_ref: string
  database_type: string
  database_url: string
}

