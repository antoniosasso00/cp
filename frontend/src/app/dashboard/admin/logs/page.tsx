'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Calendar, Download, Filter, RefreshCw, Search } from 'lucide-react'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'

interface SystemLog {
  id: number
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'critical'
  event_type: string
  user_role: string
  user_id?: string
  action: string
  entity_type?: string
  entity_id?: number
  details?: string
  old_value?: string
  new_value?: string
  ip_address?: string
}

interface LogStats {
  total_logs: number
  logs_by_type: Record<string, number>
  logs_by_role: Record<string, number>
  logs_by_level: Record<string, number>
  recent_errors: SystemLog[]
}

const EVENT_TYPE_LABELS = {
  'odl_state_change': 'Cambio Stato ODL',
  'nesting_confirm': 'Conferma Nesting',
  'nesting_modify': 'Modifica Nesting',
  'cura_start': 'Avvio Cura',
  'cura_complete': 'Completamento Cura',
  'tool_modify': 'Modifica Tool',
  'autoclave_modify': 'Modifica Autoclave',
  'ciclo_modify': 'Modifica Ciclo',
  'backup_create': 'Creazione Backup',
  'backup_restore': 'Ripristino Backup',
  'user_login': 'Login Utente',
  'user_logout': 'Logout Utente',
  'system_error': 'Errore Sistema'
}

const ROLE_LABELS = {
  'admin': 'Amministratore',
      'management': 'Management',
    'curing': 'Curing',
    'clean_room': 'Clean Room',
  'sistema': 'Sistema'
}

const LEVEL_COLORS = {
  'info': 'bg-blue-100 text-blue-800',
  'warning': 'bg-yellow-100 text-yellow-800',
  'error': 'bg-red-100 text-red-800',
  'critical': 'bg-red-200 text-red-900'
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<SystemLog[]>([])
  const [stats, setStats] = useState<LogStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    event_type: '',
    user_role: '',
    level: '',
    entity_type: '',
    start_date: '',
    end_date: '',
    limit: 100
  })

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value.toString())
      })

      const response = await fetch(`/api/v1/system-logs/?${params}`)
      if (response.ok) {
        const data = await response.json()
        setLogs(data)
      }
    } catch (error) {
      console.error('Errore nel caricamento dei log:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/system-logs/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Errore nel caricamento delle statistiche:', error)
    }
  }

  const exportLogs = async () => {
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value && key !== 'limit') params.append(key, value.toString())
      })

      const response = await fetch(`/api/v1/system-logs/export?${params}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `system_logs_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Errore nell\'esportazione:', error)
    }
  }

  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [filters])

  const formatTimestamp = (timestamp: string) => {
    return format(new Date(timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: it })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Log di Sistema</h1>
          <p className="text-gray-600">Visualizza e analizza tutti gli eventi del sistema</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchLogs} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Aggiorna
          </Button>
          <Button onClick={exportLogs} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Esporta CSV
          </Button>
        </div>
      </div>

      {/* Statistiche */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Totale Log</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_logs}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Errori Recenti</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.recent_errors.length}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Tipo Più Frequente</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                {Object.entries(stats.logs_by_type).length > 0 && 
                  EVENT_TYPE_LABELS[Object.entries(stats.logs_by_type).sort(([,a], [,b]) => b - a)[0][0] as keyof typeof EVENT_TYPE_LABELS]
                }
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Ruolo Più Attivo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                {Object.entries(stats.logs_by_role).length > 0 && 
                  ROLE_LABELS[Object.entries(stats.logs_by_role).sort(([,a], [,b]) => b - a)[0][0] as keyof typeof ROLE_LABELS]
                }
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtri */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Select
              value={filters.event_type || 'all'}
              onValueChange={(value) => setFilters(prev => ({ ...prev, event_type: value === 'all' ? '' : value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Tipo Evento" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.user_role || 'all'}
              onValueChange={(value) => setFilters(prev => ({ ...prev, user_role: value === 'all' ? '' : value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Ruolo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                {Object.entries(ROLE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.level || 'all'}
              onValueChange={(value) => setFilters(prev => ({ ...prev, level: value === 'all' ? '' : value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Livello" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>

            <Input
              type="date"
              placeholder="Data inizio"
              value={filters.start_date}
              onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
            />

            <Input
              type="date"
              placeholder="Data fine"
              value={filters.end_date}
              onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
            />

            <Select
              value={filters.limit.toString()}
              onValueChange={(value) => setFilters(prev => ({ ...prev, limit: parseInt(value) }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Limite" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
                <SelectItem value="200">200</SelectItem>
                <SelectItem value="500">500</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tabella Log */}
      <Card>
        <CardHeader>
          <CardTitle>Log Eventi ({logs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Livello</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Ruolo</TableHead>
                    <TableHead>Azione</TableHead>
                    <TableHead>Entità</TableHead>
                    <TableHead>Dettagli</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-sm">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge className={LEVEL_COLORS[log.level]}>
                          {log.level.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {EVENT_TYPE_LABELS[log.event_type as keyof typeof EVENT_TYPE_LABELS] || log.event_type}
                      </TableCell>
                      <TableCell>
                        {ROLE_LABELS[log.user_role as keyof typeof ROLE_LABELS] || log.user_role}
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {log.action}
                      </TableCell>
                      <TableCell>
                        {log.entity_type && log.entity_id && (
                          <span className="text-sm text-gray-600">
                            {log.entity_type} #{log.entity_id}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs">
                        {log.details && (
                          <div className="text-sm text-gray-600 truncate" title={log.details}>
                            {log.details}
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 