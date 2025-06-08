'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  Search, 
  Filter, 
  Calendar, 
  FileText, 
  Loader2, 
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react'
import { odlApi, type ODLResponse } from '@/lib/api'
import Link from 'next/link'

interface ODLHistoryTableProps {
  maxItems?: number
  showFilters?: boolean
  className?: string
}

export function ODLHistoryTable({ 
  maxItems = 10, 
  showFilters = true, 
  className = "" 
}: ODLHistoryTableProps) {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filtri - INIZIALIZZATI CON VALORI SICURI per evitare crash Select
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [dateRange, setDateRange] = useState<string>('30') // giorni

  const fetchODLHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Filtri per la ricerca
      const filters: any = {}
      if (statusFilter) filters.status = statusFilter
      if (searchTerm) filters.search = searchTerm
      if (dateRange && dateRange !== 'all') {
        const days = parseInt(dateRange)
        const cutoffDate = new Date()
        cutoffDate.setDate(cutoffDate.getDate() - days)
        filters.date_from = cutoffDate.toISOString().split('T')[0]
      }
      
      const data = await odlApi.fetchODLs(filters)
      
      // Ordina per data di creazione (più recenti prima) e limita
      const sortedData = data
        .sort((a, b) => 
          new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
        )
        .slice(0, maxItems)
      
      setOdlList(sortedData)
      
    } catch (err) {
      console.error('Errore nel caricamento dello storico ODL:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
  }

  // Funzione per analizzare l'univocità parte-tool
  const analyzePartToolUniqueness = (items: ODLResponse[]) => {
    const partToTools = new Map<string, Set<string>>()
    const toolToParts = new Map<string, Set<string>>()
    
    // Analizza le relazioni parte-tool
    items.forEach(item => {
      const partNumber = item.parte.part_number
      const toolNumber = item.tool.part_number_tool
      
      if (!partToTools.has(partNumber)) {
        partToTools.set(partNumber, new Set())
      }
      partToTools.get(partNumber)!.add(toolNumber)
      
      if (!toolToParts.has(toolNumber)) {
        toolToParts.set(toolNumber, new Set())
      }
      toolToParts.get(toolNumber)!.add(partNumber)
    })
    
    // Determina quando mostrare il tool
    const shouldShowTool = new Set<string>()
    
    items.forEach(item => {
      const partNumber = item.parte.part_number
      const toolNumber = item.tool.part_number_tool
      const odlKey = `${partNumber}-${toolNumber}`
      
      // Mostra tool se:
      // 1. Una parte ha più tool diversi
      // 2. Un tool è usato per più parti diverse
      const partHasMultipleTools = partToTools.get(partNumber)!.size > 1
      const toolHasMultipleParts = toolToParts.get(toolNumber)!.size > 1
      
      if (partHasMultipleTools || toolHasMultipleParts) {
        shouldShowTool.add(odlKey)
      }
    })
    
    return shouldShowTool
  }

  useEffect(() => {
    fetchODLHistory()
  }, [statusFilter, searchTerm, dateRange, maxItems])

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'Preparazione': { variant: 'secondary', color: 'bg-gray-500' },
      'Laminazione': { variant: 'default', color: 'bg-blue-500' },
      'In Coda': { variant: 'outline', color: 'bg-yellow-500' },
      'Attesa Cura': { variant: 'secondary', color: 'bg-orange-500' },
      'Cura': { variant: 'default', color: 'bg-purple-500' },
      'Finito': { variant: 'default', color: 'bg-green-500' }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { variant: 'outline', color: 'bg-gray-500' }
    
    return (
      <Badge variant={config.variant as any} className="text-xs">
        {status}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleRefresh = () => {
    fetchODLHistory()
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Storico ODL
            </CardTitle>
            <CardDescription>
              Cronologia degli ordini di lavorazione
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        
        {showFilters && (
          <div className="flex flex-wrap gap-3 mt-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Cerca ODL, PN, Tool..."
                  value={searchTerm || ''} // SICUREZZA: fallback a stringa vuota
                  onChange={(e) => setSearchTerm(e.target.value || '')}
                  className="pl-8"
                />
              </div>
            </div>
            
            <Select value={statusFilter || 'all'} onValueChange={(value) => setStatusFilter(value === 'all' ? '' : value)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Stato" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti gli stati</SelectItem>
                <SelectItem value="Preparazione">Preparazione</SelectItem>
                <SelectItem value="Laminazione">Laminazione</SelectItem>
                <SelectItem value="In Coda">In Coda</SelectItem>
                <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                <SelectItem value="Cura">Cura</SelectItem>
                <SelectItem value="Finito">Finito</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={dateRange || '30'} onValueChange={(value) => setDateRange(value || '30')}>
              <SelectTrigger className="w-[130px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Ultimi 7 giorni</SelectItem>
                <SelectItem value="30">Ultimi 30 giorni</SelectItem>
                <SelectItem value="90">Ultimi 3 mesi</SelectItem>
                <SelectItem value="all">Tutti</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Caricamento...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-600 mb-3">{error}</p>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              Riprova
            </Button>
          </div>
        ) : odlList.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              Nessun ODL trovato con i filtri selezionati
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">ODL</TableHead>
                  <TableHead className="min-w-[280px]">Parte & Tool</TableHead>
                  <TableHead className="w-24 text-center">Stato</TableHead>
                  <TableHead className="w-20 text-center">Priorità</TableHead>
                  <TableHead className="w-32">Data</TableHead>
                  <TableHead className="w-16 text-center">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(() => {
                  const toolVisibilityMap = analyzePartToolUniqueness(odlList)
                  return odlList.filter(odl => odl?.id).map((odl) => ( // FILTRO SICUREZZA: solo ODL con ID valido
                    <TableRow key={odl.id} className="hover:bg-muted/50">
                      <TableCell className="font-medium">
                        <span className="font-mono text-sm">#{odl.id}</span>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">
                              {odl.parte?.part_number || 'N/A'}
                            </span>
                            <span className="text-xs text-muted-foreground leading-tight max-w-[240px]">
                              {odl.parte?.descrizione_breve || 'Descrizione non disponibile'}
                            </span>
                          </div>
                          {toolVisibilityMap.has(`${odl.parte?.part_number}-${odl.tool?.part_number_tool}`) && (
                            <div className="text-xs">
                              <span className="bg-slate-100 px-2 py-0.5 rounded text-muted-foreground">
                                Tool: {odl.tool?.part_number_tool || 'N/A'}
                              </span>
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {getStatusBadge(odl.status || 'Sconosciuto')}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="text-xs">
                          P{odl.priorita || 0}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {odl.created_at ? formatDate(odl.created_at) : 'Data non disponibile'}
                      </TableCell>
                      <TableCell className="text-center">
                        <Link href={`/dashboard/shared/odl/${odl.id}`}>
                          <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                            <FileText className="h-3 w-3" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                })()}
              </TableBody>
            </Table>
            
            {odlList.length === maxItems && (
              <div className="text-center pt-4 border-t">
                <Link href="/dashboard/shared/odl">
                  <Button variant="outline" size="sm">
                    Visualizza tutti gli ODL
                  </Button>
                </Link>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
} 