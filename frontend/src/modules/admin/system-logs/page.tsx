'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { DatePicker } from '@/components/ui/date-picker'
import { useToast } from '@/components/ui/use-toast'
import { 
  Calendar, 
  Download, 
  Filter, 
  RefreshCw, 
  Search, 
  AlertTriangle, 
  Info, 
  AlertCircle, 
  XCircle,
  Eye,
  FileText
} from 'lucide-react'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'
import { systemLogsApi, SystemLogResponse, SystemLogFilter, SystemLogStats } from '@/lib/api'

/**
 * 🎯 PAGINA SYSTEM LOGS - ADMIN
 * 
 * Questa pagina permette agli amministratori di:
 * - Visualizzare tutti i log di sistema in una tabella
 * - Filtrare per data, livello, tipo evento, ruolo utente
 * - Esportare i log in formato CSV
 * - Vedere statistiche sui log
 * 
 * Utilizza:
 * - shadcn/ui Table per la visualizzazione
 * - DatePicker per i filtri data
 * - API systemLogsApi per il data fetching
 */

// Configurazione colori per i livelli di log
const getLevelBadgeVariant = (level: string) => {
  switch (level) {
    case 'INFO':
      return 'default'
    case 'WARNING':
      return 'secondary'
    case 'ERROR':
      return 'destructive'
    case 'CRITICAL':
      return 'destructive'
    default:
      return 'outline'
  }
}

// Icone per i livelli di log
const getLevelIcon = (level: string) => {
  switch (level) {
    case 'INFO':
      return <Info className="h-4 w-4" />
    case 'WARNING':
      return <AlertTriangle className="h-4 w-4" />
    case 'ERROR':
      return <AlertCircle className="h-4 w-4" />
    case 'CRITICAL':
      return <XCircle className="h-4 w-4" />
    default:
      return <FileText className="h-4 w-4" />
  }
}

export default function SystemLogsPage() {
  // 📊 State per i dati
  const [logs, setLogs] = useState<SystemLogResponse[]>([])
  const [stats, setStats] = useState<SystemLogStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  
  // 🔍 State per i filtri
  const [filters, setFilters] = useState<SystemLogFilter>({
    limit: 100,
    offset: 0
  })
  
  // 📅 State per le date
  const [startDate, setStartDate] = useState<Date | undefined>()
  const [endDate, setEndDate] = useState<Date | undefined>()
  
  // 🔧 Hooks
  const { toast } = useToast()

  /**
   * 📡 Funzione per caricare i log dal server
   */
  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      console.log('🔄 Caricamento system logs...', filters)
      
      // Prepara i filtri con le date formattate
      const apiFilters: SystemLogFilter = {
        ...filters,
        start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
        end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
      }
      
      const data = await systemLogsApi.fetchSystemLogs(apiFilters)
      setLogs(data)
      
      console.log(`✅ Caricati ${data.length} log`)
      
      toast({
        title: "Log caricati",
        description: `Trovati ${data.length} log di sistema`,
      })
      
    } catch (error: any) {
      console.error('❌ Errore nel caricamento dei log:', error)
      toast({
        title: "Errore",
        description: error.message || 'Errore nel caricamento dei log',
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }, [filters, startDate, endDate, toast])

  /**
   * 📊 Funzione per caricare le statistiche
   */
  const fetchStats = useCallback(async () => {
    try {
      console.log('📊 Caricamento statistiche log...')
      const data = await systemLogsApi.fetchSystemLogStats(30) // Ultimi 30 giorni
      setStats(data)
      console.log('✅ Statistiche caricate:', data)
    } catch (error: any) {
      console.error('❌ Errore nel caricamento delle statistiche:', error)
      // Non mostriamo toast per le statistiche per non essere invasivi
    }
  }, [])

  /**
   * 📤 Funzione per esportare i log in CSV
   */
  const handleExport = async () => {
    setExporting(true)
    try {
      console.log('📤 Avvio esportazione CSV...')
      
      const exportFilters: SystemLogFilter = {
        event_type: filters.event_type,
        user_role: filters.user_role,
        level: filters.level,
        start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
        end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
      }
      
      await systemLogsApi.exportSystemLogsCsv(exportFilters)
      
      toast({
        title: "Esportazione completata",
        description: "Il file CSV è stato scaricato",
      })
      
    } catch (error: any) {
      console.error('❌ Errore nell\'esportazione:', error)
      toast({
        title: "Errore esportazione",
        description: error.message || 'Errore nell\'esportazione del CSV',
        variant: "destructive",
      })
    } finally {
      setExporting(false)
    }
  }

  /**
   * 🔄 Funzione per aggiornare i filtri
   */
  const updateFilter = (key: keyof SystemLogFilter, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === 'all' ? undefined : value // Gestisco "all" come undefined
    }))
  }

  /**
   * 🧹 Funzione per pulire tutti i filtri
   */
  const clearFilters = () => {
    setFilters({ limit: 100, offset: 0 })
    setStartDate(undefined)
    setEndDate(undefined)
  }

  /**
   * 🕒 Formattazione timestamp per visualizzazione
   */
  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: it })
    } catch {
      return timestamp // Fallback se la data non è valida
    }
  }

  /**
   * 📄 Formattazione dettagli per visualizzazione
   */
  const formatDetails = (details?: string) => {
    if (!details) return '-'
    
    // Se è JSON, prova a formattarlo
    try {
      const parsed = JSON.parse(details)
      return JSON.stringify(parsed, null, 2)
    } catch {
      // Se non è JSON, restituisci come stringa
      return details.length > 100 ? `${details.substring(0, 100)}...` : details
    }
  }

  // 🚀 Effetti per il caricamento iniziale
  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [fetchLogs, fetchStats])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 📊 Header con titolo e statistiche */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Logs</h1>
          <p className="text-muted-foreground">
            Visualizza e gestisci i log di sistema per monitorare le attività
          </p>
        </div>
        
        {/* Statistiche rapide */}
        {stats && (
          <div className="flex gap-4">
            <Card className="p-3">
              <div className="text-2xl font-bold">{stats.total_logs}</div>
              <div className="text-xs text-muted-foreground">Log totali</div>
            </Card>
            <Card className="p-3">
              <div className="text-2xl font-bold text-red-600">
                {stats.recent_errors.length}
              </div>
              <div className="text-xs text-muted-foreground">Errori recenti</div>
            </Card>
          </div>
        )}
      </div>

      {/* 🔍 Sezione filtri */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri di ricerca
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Filtro per tipo evento */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo Evento</label>
              <Select
                value={filters.event_type || 'all'}
                onValueChange={(value) => updateFilter('event_type', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti i tipi" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i tipi</SelectItem>
                  <SelectItem value="odl_state_change">Cambio stato ODL</SelectItem>
                  <SelectItem value="user_login">Login utente</SelectItem>
                  <SelectItem value="data_modification">Modifica dati</SelectItem>
                  <SelectItem value="system_error">Errore sistema</SelectItem>
                  <SelectItem value="batch_operation">Operazione batch</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro per ruolo utente */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Ruolo Utente</label>
              <Select
                value={filters.user_role || 'all'}
                onValueChange={(value) => updateFilter('user_role', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti i ruoli" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i ruoli</SelectItem>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                  <SelectItem value="Management">Management</SelectItem>
                  <SelectItem value="Curing">Curing</SelectItem>
                  <SelectItem value="Clean Room">Clean Room</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro per livello */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Livello</label>
              <Select
                value={filters.level || 'all'}
                onValueChange={(value) => updateFilter('level', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti i livelli" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i livelli</SelectItem>
                  <SelectItem value="INFO">Info</SelectItem>
                  <SelectItem value="WARNING">Warning</SelectItem>
                  <SelectItem value="ERROR">Error</SelectItem>
                  <SelectItem value="CRITICAL">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Filtro per entità */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo Entità</label>
              <Input
                placeholder="es. odl, tool, autoclave"
                value={filters.entity_type || ''}
                onChange={(e) => updateFilter('entity_type', e.target.value)}
              />
            </div>
          </div>

          {/* Filtri data */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Data inizio</label>
              <DatePicker
                date={startDate}
                onDateChange={setStartDate}
                placeholder="Seleziona data inizio"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Data fine</label>
              <DatePicker
                date={endDate}
                onDateChange={setEndDate}
                placeholder="Seleziona data fine"
              />
            </div>
          </div>

          {/* Azioni filtri */}
          <div className="flex gap-2 mt-4">
            <Button onClick={fetchLogs} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              {loading ? 'Caricamento...' : 'Cerca'}
            </Button>
            <Button variant="outline" onClick={clearFilters}>
              Pulisci filtri
            </Button>
            <Button variant="outline" onClick={handleExport} disabled={exporting}>
              <Download className="h-4 w-4 mr-2" />
              {exporting ? 'Esportando...' : 'Esporta CSV'}
            </Button>
            <Button variant="outline" onClick={fetchLogs}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Aggiorna
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 📋 Tabella dei log */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Log di Sistema ({logs.length})</span>
            {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[180px]">Timestamp</TableHead>
                  <TableHead className="w-[100px]">Livello</TableHead>
                  <TableHead className="w-[150px]">Tipo Evento</TableHead>
                  <TableHead className="w-[120px]">Ruolo</TableHead>
                  <TableHead className="w-[200px]">Azione</TableHead>
                  <TableHead className="w-[120px]">Entità</TableHead>
                  <TableHead>Dettagli</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      {loading ? 'Caricamento log...' : 'Nessun log trovato con i filtri selezionati'}
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-sm">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={getLevelBadgeVariant(log.level)}
                          className="flex items-center gap-1"
                        >
                          {getLevelIcon(log.level)}
                          {log.level}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        {log.event_type}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{log.user_role}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate" title={log.action}>
                        {log.action}
                      </TableCell>
                      <TableCell>
                        {log.entity_type && (
                          <span className="text-sm">
                            {log.entity_type}
                            {log.entity_id && ` #${log.entity_id}`}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-[300px]">
                        <details className="cursor-pointer">
                          <summary className="text-sm text-muted-foreground hover:text-foreground">
                            <Eye className="h-3 w-3 inline mr-1" />
                            Visualizza dettagli
                          </summary>
                          <div className="mt-2 p-2 bg-muted rounded text-xs font-mono whitespace-pre-wrap">
                            {formatDetails(log.details)}
                            {log.old_value && (
                              <div className="mt-2">
                                <strong>Valore precedente:</strong> {log.old_value}
                              </div>
                            )}
                            {log.new_value && (
                              <div className="mt-1">
                                <strong>Nuovo valore:</strong> {log.new_value}
                              </div>
                            )}
                            {log.ip_address && (
                              <div className="mt-1">
                                <strong>IP:</strong> {log.ip_address}
                              </div>
                            )}
                          </div>
                        </details>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 