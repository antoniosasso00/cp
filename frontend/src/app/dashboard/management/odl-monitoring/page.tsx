'use client';

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Eye, RefreshCw, Search, AlertCircle, Clock } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { NoDataEmptyState } from '@/components/ui/empty-state'

interface ODLMonitoringSummary {
  id: number
  parte_nome: string
  tool_nome: string
  status: string
  priorita: number
  created_at: string
  updated_at: string
  nesting_stato?: string
  autoclave_nome?: string
  ultimo_evento?: string
  ultimo_evento_timestamp?: string
  tempo_in_stato_corrente?: number
}

export default function ODLMonitoringPage() {
  const router = useRouter()
  const { toast } = useToast()
  
  const [odlList, setOdlList] = useState<ODLMonitoringSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [prioritaMin, setPrioritaMin] = useState('')
  const [soloAttivi, setSoloAttivi] = useState(true)

  // Carica la lista ODL
  const fetchODLList = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        skip: '0',
        limit: '100',
        solo_attivi: soloAttivi.toString()
      })
      
      if (statusFilter !== 'all') params.append('status_filter', statusFilter)
      if (prioritaMin) params.append('priorita_min', prioritaMin)
      
      const response = await fetch(`/api/v1/odl-monitoring/monitoring?${params}`)
      
      if (!response.ok) {
        throw new Error(`Errore ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Filtra per termine di ricerca se presente
      let filteredData = data
      if (searchTerm) {
        filteredData = data.filter((odl: ODLMonitoringSummary) =>
          (odl.parte_nome && odl.parte_nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (odl.tool_nome && odl.tool_nome.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (odl.id && odl.id.toString().includes(searchTerm))
        )
      }
      
      setOdlList(filteredData)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto nel caricamento ODL'
      console.error('Errore nel caricamento ODL:', err)
      setError(errorMessage)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Carica i dati al mount e quando cambiano i filtri
  useEffect(() => {
    fetchODLList()
  }, [statusFilter, prioritaMin, soloAttivi])

  // Filtra per termine di ricerca
  useEffect(() => {
    if (searchTerm === '') {
      fetchODLList()
    }
  }, [searchTerm])

  // Gestione cambio filtro solo attivi
  const handleSoloAttiviChange = (value: string) => {
    setSoloAttivi(value === 'true')
  }

  // Gestione ricerca
  const handleSearch = () => {
    fetchODLList()
  }

  // Gestione refresh
  const handleRefresh = () => {
    fetchODLList()
  }

  // Naviga ai dettagli timeline
  const navigateToTimeline = (odlId: number) => {
    router.push(`/dashboard/management/odl-monitoring/${odlId}`)
  }

  // Formatta il tempo
  const formatTempo = (minuti?: number) => {
    if (!minuti) return 'N/A'
    const ore = Math.floor(minuti / 60)
    const min = minuti % 60
    return `${ore}h ${min}m`
  }

  // Ottieni colore badge per stato
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'Finito':
        return 'default'
      case 'Cura':
        return 'destructive'
      case 'Attesa Cura':
        return 'secondary'
      case 'Laminazione':
        return 'outline'
      default:
        return 'secondary'
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Monitoraggio ODL</h1>
            <p className="text-muted-foreground">Timeline e dettagli degli ODL</p>
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        
        <Card>
          <CardContent className="p-6">
            <div className="space-y-4">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Monitoraggio ODL</h1>
          <p className="text-muted-foreground">Timeline e dettagli degli ODL</p>
        </div>
        
        <Button 
          variant="outline" 
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      {/* Filtri */}
      <Card>
        <CardHeader>
          <CardTitle>Filtri</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Ricerca</label>
              <div className="flex gap-2">
                <Input
                  placeholder="ID, parte o tool..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button variant="outline" size="icon" onClick={handleSearch}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Stato</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Tutti gli stati" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli stati</SelectItem>
                  <SelectItem value="Preparazione">Preparazione</SelectItem>
                  <SelectItem value="Laminazione">Laminazione</SelectItem>
                  <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                  <SelectItem value="Cura">Cura</SelectItem>
                  <SelectItem value="Finito">Finito</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Priorità minima</label>
              <Input
                type="number"
                placeholder="1-10"
                value={prioritaMin}
                onChange={(e) => setPrioritaMin(e.target.value)}
                min="1"
                max="10"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Visualizzazione</label>
              <Select value={soloAttivi.toString()} onValueChange={handleSoloAttiviChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Solo attivi</SelectItem>
                  <SelectItem value="false">Tutti gli ODL</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Messaggio di errore */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Errore</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Lista ODL */}
      {odlList.length === 0 ? (
        <NoDataEmptyState
          hasFilters={searchTerm !== '' || statusFilter !== 'all' || prioritaMin !== '' || !soloAttivi}
          onReset={() => {
            setSearchTerm('')
            setStatusFilter('all')
            setPrioritaMin('')
            setSoloAttivi(true)
          }}
        />
      ) : (
        <div className="space-y-4">
          {odlList.map((odl) => (
            <Card key={odl.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-4">
                      <h3 className="text-lg font-semibold">ODL #{odl.id}</h3>
                      <Badge variant={getStatusBadgeVariant(odl.status)}>
                        {odl.status}
                      </Badge>
                      <Badge variant="outline">
                        Priorità {odl.priorita}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="font-medium text-muted-foreground">Parte</p>
                        <p>{odl.parte_nome}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground">Tool</p>
                        <p>{odl.tool_nome}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground">Autoclave</p>
                        <p>{odl.autoclave_nome || 'Non assegnata'}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>Tempo nello stato: {formatTempo(odl.tempo_in_stato_corrente)}</span>
                      </div>
                      <div>
                        Creato: {new Date(odl.created_at).toLocaleDateString('it-IT')}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigateToTimeline(odl.id)}
                      className="flex items-center gap-2"
                    >
                      <Eye className="h-4 w-4" />
                      Timeline
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
} 