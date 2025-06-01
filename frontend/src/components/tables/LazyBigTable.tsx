'use client'

import React, { useMemo, useState } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChevronLeft, ChevronRight, Search, Filter, Loader2 } from 'lucide-react'

interface Column {
  key: string
  label: string
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: any) => React.ReactNode
  width?: string
}

interface LazyBigTableProps {
  data: any[]
  columns: Column[]
  title?: string
  description?: string
  loading?: boolean
  error?: string
  searchable?: boolean
  filterable?: boolean
  paginated?: boolean
  pageSize?: number
  className?: string
  onRowClick?: (row: any) => void
  emptyMessage?: string
}

/**
 * Componente tabella ottimizzato per grandi dataset
 * 
 * 🎯 CARATTERISTICHE:
 * • Lazy loading per migliorare performance iniziale
 * • Paginazione per dataset grandi
 * • Ricerca e filtri integrati
 * • Sorting delle colonne
 * • Renderizzazione custom delle celle
 * • Stati di loading ed errore
 * 
 * 💡 USO:
 * import dynamic from 'next/dynamic'
 * const LazyBigTable = dynamic(() => import('./LazyBigTable'), { ssr: false })
 */
export default function LazyBigTable({
  data,
  columns,
  title,
  description,
  loading = false,
  error,
  searchable = true,
  filterable = true,
  paginated = true,
  pageSize = 10,
  className = "",
  onRowClick,
  emptyMessage = "Nessun dato disponibile"
}: LazyBigTableProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>({})

  // Filtri e ricerca
  const filteredData = useMemo(() => {
    let filtered = [...data]

    // Ricerca globale
    if (searchable && searchTerm) {
      filtered = filtered.filter(row =>
        columns.some(col =>
          String(row[col.key] || '').toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    // Filtri per colonna
    if (filterable) {
      Object.entries(columnFilters).forEach(([columnKey, filterValue]) => {
        if (filterValue) {
          filtered = filtered.filter(row =>
            String(row[columnKey] || '').toLowerCase().includes(filterValue.toLowerCase())
          )
        }
      })
    }

    return filtered
  }, [data, searchTerm, columnFilters, columns, searchable, filterable])

  // Sorting
  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]
      
      if (aVal === bVal) return 0
      
      const comparison = aVal < bVal ? -1 : 1
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [filteredData, sortColumn, sortDirection])

  // Paginazione
  const totalPages = Math.ceil(sortedData.length / pageSize)
  const paginatedData = useMemo(() => {
    if (!paginated) return sortedData
    
    const startIndex = (currentPage - 1) * pageSize
    return sortedData.slice(startIndex, startIndex + pageSize)
  }, [sortedData, currentPage, pageSize, paginated])

  const handleSort = (columnKey: string) => {
    const column = columns.find(col => col.key === columnKey)
    if (!column?.sortable) return

    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(columnKey)
      setSortDirection('asc')
    }
  }

  const handleColumnFilter = (columnKey: string, value: string) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: value
    }))
    setCurrentPage(1) // Reset alla prima pagina
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-muted-foreground">Caricamento dati...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={`border-destructive ${className}`}>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      
      <CardContent className="space-y-4">
        {/* Controlli ricerca e filtri */}
        <div className="flex flex-col sm:flex-row gap-4">
          {searchable && (
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Cerca..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          )}
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {filteredData.length} elementi
            </Badge>
          </div>
        </div>

        {/* Filtri per colonna */}
        {filterable && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {columns
              .filter(col => col.filterable)
              .map(column => (
                <div key={column.key} className="space-y-1">
                  <label className="text-xs text-muted-foreground">{column.label}</label>
                  <Input
                    placeholder={`Filtra ${column.label.toLowerCase()}...`}
                    value={columnFilters[column.key] || ''}
                    onChange={(e) => handleColumnFilter(column.key, e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
              ))}
          </div>
        )}

        {/* Tabella */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead
                    key={column.key}
                    className={`${column.sortable ? 'cursor-pointer hover:bg-muted/50' : ''} ${column.width || ''}`}
                    onClick={() => handleSort(column.key)}
                  >
                    <div className="flex items-center gap-2">
                      {column.label}
                      {column.sortable && sortColumn === column.key && (
                        <span className="text-xs">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length} className="text-center py-12 text-muted-foreground">
                    {emptyMessage}
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((row, index) => (
                  <TableRow
                    key={`row-${index}`}
                    className={onRowClick ? 'cursor-pointer hover:bg-muted/50' : ''}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <TableCell key={`${index}-${column.key}`} className={column.width || ''}>
                        {column.render
                          ? column.render(row[column.key], row)
                          : row[column.key] ?? '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Paginazione */}
        {paginated && totalPages > 1 && (
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Pagina {currentPage} di {totalPages} ({sortedData.length} elementi totali)
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Precedente
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
              >
                Successiva
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 