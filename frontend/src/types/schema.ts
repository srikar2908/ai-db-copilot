export type SchemaTableMap = Record<string, string[]>

export type SchemaResponse = {
  tables: SchemaTableMap
  relevant_tables: string[]
  schema_version: string
  extracted_at: string
}