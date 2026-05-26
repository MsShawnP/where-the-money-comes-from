/**
 * Visually hidden data table for screen reader accessibility.
 *
 * Renders with .sr-only class — invisible to sighted users, fully accessible
 * to assistive technology. Mirrors each chapter's chart so screen reader users
 * get the same data without needing to interact with the SVG visualisation.
 */

export interface DataTableColumn {
  key: string
  label: string
  format?: (value: unknown) => string
}

export interface DataTableProps {
  caption: string
  columns: DataTableColumn[]
  data: Record<string, unknown>[]
}

export function DataTable({ caption, columns, data }: DataTableProps) {
  return (
    <table className="sr-only">
      <caption>{caption}</caption>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} scope="col">
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            {columns.map((col) => (
              <td key={col.key}>
                {col.format
                  ? col.format(row[col.key])
                  : String(row[col.key] ?? '')}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
