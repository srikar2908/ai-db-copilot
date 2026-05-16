import type { ExecutionRow } from '../../types/query'
import EmptyState from '../ui/EmptyState'

type DataTableProps = {
  rows: ExecutionRow[]
}

function formatCellValue(value: ExecutionRow[string]) {
  if (value === null) {
    return 'NULL'
  }

  return String(value)
}

function DataTable({ rows }: DataTableProps) {
  if (!rows.length) {
    return (
      <EmptyState
        description="Approved query execution results will render here when the backend returns rows."
        title="No query results yet"
      />
    )
  }

  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))))

  return (
    <div className="overflow-hidden rounded-md border border-slate-800">
      <div className="max-h-80 overflow-auto">
        <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
          <thead className="sticky top-0 bg-slate-900">
            <tr>
              {columns.map((column) => (
                <th
                  className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400"
                  key={column}
                  scope="col"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950">
            {rows.map((row, rowIndex) => (
              <tr className="hover:bg-slate-900/70" key={`${rowIndex}-${JSON.stringify(row)}`}>
                {columns.map((column) => (
                  <td className="whitespace-nowrap px-4 py-3 text-slate-200" key={column}>
                    {formatCellValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DataTable
