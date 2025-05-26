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
      
      // Costruisci i parametri di filtro
      const params: any = {
        limit: maxItems * 2, // Prendiamo più dati per permettere il filtro locale
        skip: 0
      }
      
      // CONTROLLO SICUREZZA: verifica che statusFilter non sia undefined
      if (statusFilter && statusFilter.trim() !== '') {
        params.status = statusFilter
      }
      
      const data = await odlApi.getAll(params)
      
      // Filtro locale per search term e date range
      let filteredData = data
      
      // CONTROLLO SICUREZZA: verifica che searchTerm non sia undefined
      if (searchTerm && searchTerm.trim() !== '') {
        const searchLower = searchTerm.toLowerCase()
        filteredData = filteredData.filter(odl => 
          odl.parte?.part_number?.toLowerCase().includes(searchLower) ||
          odl.parte?.descrizione_breve?.toLowerCase().includes(searchLower) ||
          odl.tool?.part_number_tool?.toLowerCase().includes(searchLower) ||
          odl.id?.toString().includes(searchLower)
        )
      }
      
      // Filtro per data (ultimi N giorni) - CONTROLLO SICUREZZA
      if (dateRange && dateRange !== 'all' && dateRange.trim() !== '') {
        const daysAgo = parseInt(dateRange)
        if (!isNaN(daysAgo)) {
          const cutoffDate = new Date()
          cutoffDate.setDate(cutoffDate.getDate() - daysAgo)
          
          filteredData = filteredData.filter(odl => 
            odl.created_at && new Date(odl.created_at) >= cutoffDate
          )
        }
      }
      
      // Ordina per data di creazione (più recenti prima)
      filteredData.sort((a, b) => 
        new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      )
      
      // Limita al numero massimo richiesto
      setOdlList(filteredData.slice(0, maxItems))
      
    } catch (err) {
      console.error('Errore nel caricamento dello storico ODL:', err)
      setError('Errore nel caricamento dei dati')
    } finally {
      setLoading(false)
    }
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
                  <TableHead>ODL</TableHead>
                  <TableHead>Parte</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Priorità</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlList.filter(odl => odl?.id).map((odl) => ( // FILTRO SICUREZZA: solo ODL con ID valido
                  <TableRow key={odl.id} className="hover:bg-muted/50">
                    <TableCell className="font-medium">
                      #{odl.id}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium text-sm">
                          {odl.parte?.part_number || 'N/A'}
                        </div>
                        <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                          {odl.parte?.descrizione_breve || 'Descrizione non disponibile'}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {odl.tool?.part_number_tool || 'N/A'}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(odl.status || 'Sconosciuto')}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        P{odl.priorita || 0}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {odl.created_at ? formatDate(odl.created_at) : 'Data non disponibile'}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Link href={`/dashboard/shared/odl/${odl.id}`}>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <FileText className="h-3 w-3" />
                          </Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
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