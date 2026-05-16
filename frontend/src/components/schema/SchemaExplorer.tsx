import { useMemo, useState } from 'react'

type SchemaExplorerProps = {
  tables: Record<string, string[]>
  onInsert: (value: string) => void
}

function SchemaExplorer({
  tables,
  onInsert,
}: SchemaExplorerProps) {

  const [expandedTables, setExpandedTables] =
    useState<Record<string, boolean>>({})

  const [search, setSearch] = useState('')

  const filteredTables = useMemo(() => {

    if (!search.trim()) {
      return tables
    }

    const next: Record<string, string[]> = {}

    Object.entries(tables).forEach(
      ([table, columns]) => {

        const tableMatch =
          table.toLowerCase().includes(
            search.toLowerCase()
          )

        const filteredColumns =
          columns.filter((column) =>
            column.toLowerCase().includes(
              search.toLowerCase()
            )
          )

        if (tableMatch || filteredColumns.length) {

          next[table] = tableMatch
            ? columns
            : filteredColumns
        }
      }
    )

    return next

  }, [tables, search])

  const toggleTable = (table: string) => {

    setExpandedTables((prev) => ({
      ...prev,
      [table]: !prev[table],
    }))
  }

  return (
    <div className="mt-6 rounded-md border border-slate-800 bg-slate-900">

      <div className="border-b border-slate-800 p-3">
        <h3 className="text-sm font-semibold text-white">
          Database Schema
        </h3>

        <p className="mt-1 text-xs text-slate-500">
          Click tables or columns to insert into prompts.
        </p>

        <input
          className="mt-3 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-100 outline-none focus:border-cyan-400"
          onChange={(event) =>
            setSearch(event.target.value)
          }
          placeholder="Search tables or columns..."
          value={search}
        />
      </div>

      <div className="max-h-[420px] overflow-auto p-2">

        {Object.keys(filteredTables).length === 0 ? (
          <div className="px-3 py-4 text-xs text-slate-500">
            No schema matches found.
          </div>
        ) : null}

        {Object.entries(filteredTables).map(
          ([table, columns]) => {

            const expanded =
              expandedTables[table]

            return (
              <div
                className="mb-2 rounded-md border border-slate-800"
                key={table}
              >

                <button
                  className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-slate-800"
                  onClick={() => toggleTable(table)}
                  type="button"
                >
                  <span
                    className="text-sm font-medium text-cyan-200"
                    onClick={(event) => {
                      event.stopPropagation()
                      onInsert(table)
                    }}
                  >
                    {table}
                  </span>

                  <span className="text-xs text-slate-500">
                    {expanded ? '−' : '+'}
                  </span>
                </button>

                {expanded ? (
                  <div className="border-t border-slate-800 bg-slate-950 p-2">

                    {columns.map((column) => (

                      <button
                        className="mb-1 mr-1 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-300 transition hover:border-cyan-400 hover:text-cyan-200"
                        key={column}
                        onClick={() =>
                          onInsert(column)
                        }
                        type="button"
                      >
                        {column}
                      </button>
                    ))}

                  </div>
                ) : null}

              </div>
            )
          }
        )}
      </div>
    </div>
  )
}

export default SchemaExplorer