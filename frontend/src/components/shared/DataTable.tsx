import { useMemo, useState } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowUpDown } from 'lucide-react'

export type Column<T> = {
  key: string
  header: string
  accessor?: (row: T) => React.ReactNode
  sortable?: boolean
  className?: string
}

export type DataTableProps<T> = {
  rows: T[]
  columns: Column<T>[]
  loading?: boolean
  emptyText?: string
  pageSize?: number
  searchableKeys?: (keyof T)[]
}

export default function DataTable<T extends Record<string, any>>({
  rows = [], columns, loading = false, emptyText = 'No data', pageSize = 10, searchableKeys
}: DataTableProps<T>) {
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<{ key: string; dir: 'asc'|'desc' } | null>(null)

  const safeRows = rows || []

  const filtered = useMemo(() => {
    if (!q) return safeRows
    const needle = q.toLowerCase()
    return safeRows.filter(r => {
      const keys = searchableKeys?.length ? searchableKeys : (Object.keys(r) as (keyof T)[])
      return keys.some(k => String(r[k] ?? '').toLowerCase().includes(needle))
    })
  }, [safeRows, q, searchableKeys])

  const sorted = useMemo(() => {
    if (!sort) return filtered
    const copy = [...filtered]
    copy.sort((a,b) => {
      const av = a[sort.key]; const bv = b[sort.key]
      if (av == null && bv == null) return 0
      if (av == null) return sort.dir === 'asc' ? -1 : 1
      if (bv == null) return sort.dir === 'asc' ? 1 : -1
      if (typeof av === 'number' && typeof bv === 'number') return sort.dir === 'asc' ? av - bv : bv - av
      return sort.dir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
    return copy
  }, [filtered, sort])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const pageRows = sorted.slice((page-1)*pageSize, page*pageSize)

  const toggleSort = (key: string) => {
    setPage(1)
    setSort(prev => {
      if (!prev || prev.key !== key) return { key, dir: 'asc' }
      if (prev.dir === 'asc') return { key, dir: 'desc' }
      return null // off
    })
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Input
          placeholder="Search…"
          value={q}
          onChange={(e)=>{ setQ(e.target.value); setPage(1) }}
          className="max-w-xs"
        />
      </div>

      <div className="rounded-md border overflow-hidden">
        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 6 }).map((_,i)=>(
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !pageRows.length ? (
          <div className="p-4 text-sm text-slate-500">{emptyText}</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map(c => (
                  <TableHead
                    key={c.key}
                    className={c.className}
                  >
                    <button
                      className={`inline-flex items-center gap-1 ${c.sortable ? 'hover:underline' : 'cursor-default'}`}
                      onClick={() => c.sortable && toggleSort(c.key)}
                    >
                      {c.header}
                      {c.sortable && <ArrowUpDown className="h-3.5 w-3.5 opacity-50" />}
                    </button>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageRows.map((r, idx) => (
                <TableRow key={idx}>
                  {columns.map(c => (
                    <TableCell key={c.key} className={c.className}>
                      {c.accessor ? c.accessor(r) : String(r[c.key] ?? '—')}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <div className="flex items-center justify-end gap-2">
        <div className="text-xs text-slate-500">Page {page} / {totalPages}</div>
        <Button size="sm" variant="outline" onClick={()=>setPage(p=>Math.max(1, p-1))} disabled={page<=1}>Prev</Button>
        <Button size="sm" variant="outline" onClick={()=>setPage(p=>Math.min(totalPages, p+1))} disabled={page>=totalPages}>Next</Button>
      </div>
    </div>
  )
}
