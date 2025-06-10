'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

// Force dynamic rendering for this page
export const dynamic = 'force-dynamic'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  Activity, 
  Clock, 
  Flame, 
  RefreshCw, 
  Search,
  AlertCircle,
  CheckCircle,
  Thermometer,
  Gauge,
  ChevronDown,
  ChevronRight,
  Package,
  ClipboardCheck,
  PlayCircle
} from 'lucide-react'
import { batchNestingApi } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { MetricCard } from '@/shared/components/ui/common/MetricCard'
import { useBatchTrends } from '@/shared/hooks/useBatchTrends'

interface BatchMonitoring {
  id: string
  nome: string
  stato: 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato' | 'in_cura' | 'completato' | 'errore' | 'attesa'
  autoclave_id: number
  autoclave_nome?: string
  numero_odl?: number
  numero_nesting?: number
  ciclo_cura_id?: number
  ciclo_nome?: string
  temperatura_target?: number
  temperatura_attuale?: number
  pressione_target?: number
  pressione_attuale?: number
  tempo_rimanente_minuti?: number
  tempo_totale_minuti?: number
  data_inizio_cura?: string
  data_fine_prevista?: string
  created_at: string
  updated_at: string
}

// Configurazione sezioni workflow
interface WorkflowSection {
  id: string
  title: string
  description: string
  icon: any
  color: string
  states: string[]
  defaultOpen: boolean
}

const WORKFLOW_SECTIONS: WorkflowSection[] = [
  {
    id: 'sospeso',
    title: 'In Sospeso',
    description: 'Batch generati in attesa di conferma',
    icon: Clock,
    color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    states: ['sospeso'],
    defaultOpen: true
  },
  {
    id: 'confermato',
    title: 'Confermati',
    description: 'Batch confermati pronti per il caricamento',
    icon: CheckCircle,
    color: 'text-green-600 bg-green-50 border-green-200',
    states: ['confermato'],
    defaultOpen: true
  },
  {
    id: 'caricato',
    title: 'Caricati',
    description: 'Batch caricati in autoclave',
    icon: Package,
    color: 'text-blue-600 bg-blue-50 border-blue-200',
    states: ['loaded', 'attesa'],
    defaultOpen: true
  },
  {
    id: 'in_cura',
    title: 'In Cura',
    description: 'Batch attualmente in processo di cura',
    icon: Flame,
    color: 'text-red-600 bg-red-50 border-red-200',
    states: ['cured', 'in_cura'],
    defaultOpen: true
  },
  {
    id: 'completato',
    title: 'Completati',
    description: 'Batch con cura terminata (ultime 24h)',
    icon: ClipboardCheck,
    color: 'text-gray-600 bg-gray-50 border-gray-200',
    states: ['completato'],
    defaultOpen: false
  }
]

function StatoBadge({ stato }: { stato: string }) {
  const getColor = () => {
    switch (stato) {
      case 'sospeso':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'confermato':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'loaded':
      case 'attesa':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'in_cura':
      case 'cured':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'completato':
      case 'terminato':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      case 'errore':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getLabel = () => {
    switch (stato) {
      case 'sospeso':
        return 'In Sospeso'
      case 'confermato':
        return 'Confermato'
      case 'loaded':
        return 'Caricato'
      case 'cured':
        return 'In Cura'
      case 'in_cura':
        return 'In Cura'
      case 'completato':
        return 'Completato'
      case 'terminato':
        return 'Terminato'
      case 'attesa':
        return 'In Attesa'
      case 'errore':
        return 'Errore'
      default:
        return stato
    }
  }

  return (
    <Badge className={`${getColor()} border flex items-center gap-1`} variant="outline">
      {getLabel()}
    </Badge>
  )
}

export default function BatchMonitoringPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const statusFilter = searchParams.get('status') || 'all'
  
  const [batches, setBatches] = useState<BatchMonitoring[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('')
  
  // Stati di apertura/chiusura delle sezioni
  const [sectionStates, setSectionStates] = useState<Record<string, boolean>>(() => {
    const initialStates: Record<string, boolean> = {}
    WORKFLOW_SECTIONS.forEach(section => {
      initialStates[section.id] = section.defaultOpen
    })
    return initialStates
  })

  // Calcolo trend giornalieri
  const trends = useBatchTrends(batches.map(b => ({
    id: b.id,
    stato: b.stato,
    created_at: b.created_at,
    updated_at: b.updated_at
  })))

  // Calcolo delle statistiche
  const stats = {
    totale: batches.length,
    sospeso: batches.filter(b => b.stato === 'sospeso').length,
    confermato: batches.filter(b => b.stato === 'confermato').length,
    loaded: batches.filter(b => ['loaded', 'attesa'].includes(b.stato)).length,
    in_cura: batches.filter(b => ['cured', 'in_cura'].includes(b.stato)).length,
    completato: batches.filter(b => b.stato === 'completato').length,
  }

  const loadBatches = async () => {
    try {
      setLoading(true)
      setError(null)

      // Mock data per testing - in produzione sostituire con API reale
      const mockBatches: BatchMonitoring[] = [
        {
          id: '1',
          nome: 'Batch Test 1',
          stato: 'sospeso',
          autoclave_id: 1,
          autoclave_nome: 'Autoclave PANINI',
          numero_odl: 5,
          numero_nesting: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          nome: 'Batch Test 2',
          stato: 'confermato',
          autoclave_id: 2,
          autoclave_nome: 'Autoclave ISMAR',
          numero_odl: 3,
          numero_nesting: 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '3',
          nome: 'Batch Test 3',
          stato: 'in_cura',
          autoclave_id: 3,
          autoclave_nome: 'Autoclave MAROSO',
          numero_odl: 7,
          numero_nesting: 3,
          temperatura_target: 180,
          temperatura_attuale: 175,
          pressione_target: 6.0,
          pressione_attuale: 5.8,
          tempo_rimanente_minuti: 120,
          tempo_totale_minuti: 480,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]

      setBatches(mockBatches)
    } catch (err) {
      console.error('Errore nel caricamento dei batch:', err)
      setError('Errore nel caricamento dei dati. Riprova più tardi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBatches()
  }, [])

  const formatDuration = (minutes: number | undefined) => {
    if (!minutes) return '-'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const formatTemperature = (temp: number | undefined) => {
    return temp ? `${temp}°C` : '-'
  }

  const formatPressure = (pressure: number | undefined) => {
    return pressure ? `${pressure} bar` : '-'
  }

  const getProgressPercentage = (batch: BatchMonitoring) => {
    if (!batch.tempo_totale_minuti || !batch.tempo_rimanente_minuti) return 0
    const elapsed = batch.tempo_totale_minuti - batch.tempo_rimanente_minuti
    return (elapsed / batch.tempo_totale_minuti) * 100
  }

  // Filtri applicati
  const filteredBatches = batches.filter(batch => {
    // Filtro per stato
    if (statusFilter !== 'all') {
      const section = WORKFLOW_SECTIONS.find(s => s.id === statusFilter)
      if (section && !section.states.includes(batch.stato)) {
        return false
      }
    }

    // Filtro per ricerca
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        batch.nome.toLowerCase().includes(query) ||
        batch.id.toLowerCase().includes(query) ||
        batch.autoclave_nome?.toLowerCase().includes(query)
      )
    }

    // Filtro per autoclave
    if (selectedAutoclave && selectedAutoclave !== 'all') {
      return batch.autoclave_id.toString() === selectedAutoclave
    }

    return true
  })

  const getBatchesForSection = (section: WorkflowSection) => {
    return filteredBatches.filter(batch => section.states.includes(batch.stato))
  }

  const toggleSection = (sectionId: string) => {
    setSectionStates(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }))
  }

  const handleStatusFilter = (status: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (status === 'all') {
      params.delete('status')
    } else {
      params.set('status', status)
    }
    router.push(`?${params.toString()}`)
  }

  const getMetricVariant = (status: string): 'default' | 'success' | 'warning' | 'destructive' => {
    switch (status) {
      case 'sospeso':
        return 'warning'
      case 'confermato':
        return 'success'
      case 'completato':
        return 'default'
      default:
        return 'default'
    }
  }

  if (loading && batches.length === 0) {
    return (
      <div className="container mx-auto p-6" data-testid="batch-monitoring-page">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-muted-foreground">Caricamento monitoraggio batch...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6" data-testid="batch-monitoring-page">
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              <AlertCircle className="h-8 w-8 mx-auto mb-4" />
              <p>{error}</p>
              <Button onClick={loadBatches} className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Riprova
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6" data-testid="batch-monitoring-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio Batch</h1>
          <p className="text-muted-foreground">
            Controllo workflow dei batch in tempo reale
          </p>
        </div>
        <Button onClick={loadBatches} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      {/* Dashboard Statistiche con MetricCard */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Totale Batch"
          value={stats.totale}
          icon={Activity}
          variant="default"
          trend={{
            value: trends.total.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('all')}
          selected={statusFilter === 'all'}
          data-testid="metric-card-total"
        />

        <MetricCard
          title="In Sospeso"
          value={stats.sospeso}
          icon={Clock}
          variant={getMetricVariant('sospeso')}
          trend={{
            value: trends.sospeso.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('sospeso')}
          selected={statusFilter === 'sospeso'}
          data-testid="metric-card-sospeso"
        />

        <MetricCard
          title="Confermati"
          value={stats.confermato}
          icon={CheckCircle}
          variant={getMetricVariant('confermato')}
          trend={{
            value: trends.confermato.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('confermato')}
          selected={statusFilter === 'confermato'}
          data-testid="metric-card-confermato"
        />

        <MetricCard
          title="Caricati"
          value={stats.loaded}
          icon={Package}
          variant="default"
          trend={{
            value: trends.loaded.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('caricato')}
          selected={statusFilter === 'caricato'}
          data-testid="metric-card-loaded"
        />

        <MetricCard
          title="In Cura"
          value={stats.in_cura}
          icon={Flame}
          variant="destructive"
          trend={{
            value: trends.cured.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('in_cura')}
          selected={statusFilter === 'in_cura'}
          data-testid="metric-card-cured"
        />

        <MetricCard
          title="Completati"
          value={stats.completato}
          icon={ClipboardCheck}
          variant="default"
          trend={{
            value: trends.completato.delta,
            label: 'da ieri'
          }}
          onClick={() => handleStatusFilter('completato')}
          selected={statusFilter === 'completato'}
          data-testid="metric-card-completato"
        />
      </div>

      {/* Filtri Globali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Filtri
            </div>
            {statusFilter && statusFilter !== 'all' && (
              <Badge variant="secondary" className="flex items-center gap-1">
                Filtro attivo: {statusFilter}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 ml-1"
                  onClick={() => handleStatusFilter('all')}
                >
                  ×
                </Button>
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium">Ricerca</label>
              <Input
                placeholder="Nome batch, ID, Autoclave..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Autoclave</label>
              <Select value={selectedAutoclave} onValueChange={setSelectedAutoclave}>
                <SelectTrigger>
                  <SelectValue placeholder="Tutte le autoclavi" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte</SelectItem>
                  <SelectItem value="1">Autoclave 1</SelectItem>
                  <SelectItem value="2">Autoclave 2</SelectItem>
                  <SelectItem value="3">Autoclave 3</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Stato</label>
              <Select value={statusFilter} onValueChange={handleStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Tutti gli stati" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti</SelectItem>
                  <SelectItem value="sospeso">In Sospeso</SelectItem>
                  <SelectItem value="confermato">Confermati</SelectItem>
                  <SelectItem value="caricato">Caricati</SelectItem>
                  <SelectItem value="in_cura">In Cura</SelectItem>
                  <SelectItem value="completato">Completati</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sezioni Workflow con Accordion */}
      <div className="space-y-4">
        {WORKFLOW_SECTIONS.map((section) => {
          const sectionBatches = getBatchesForSection(section)
          const isOpen = sectionStates[section.id]
          const IconComponent = section.icon

          return (
            <Card 
              key={section.id} 
              className={`border-2 ${section.color}`}
              data-testid={`workflow-section-${section.id}`}
            >
              <Collapsible 
                open={isOpen} 
                onOpenChange={() => toggleSection(section.id)}
              >
                <CollapsibleTrigger asChild>
                  <CardHeader 
                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                    data-testid={`workflow-header-${section.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-3">
                        <IconComponent className="h-5 w-5" />
                        {section.title}
                        <Badge variant="secondary" className="ml-2" data-testid="section-badge">
                          {sectionBatches.length}
                        </Badge>
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground hidden md:block">
                          {section.description}
                        </span>
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                </CollapsibleTrigger>
                
                <CollapsibleContent data-testid={`workflow-content-${section.id}`}>
                  <CardContent>
                    {sectionBatches.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground" data-testid="empty-state">
                        <IconComponent className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Nessun batch in questa fase</p>
                      </div>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Batch</TableHead>
                            <TableHead>Stato</TableHead>
                            <TableHead>Autoclave</TableHead>
                            {section.id === 'in_cura' && <TableHead>Progresso</TableHead>}
                            {section.id === 'in_cura' && <TableHead>Temperatura</TableHead>}
                            {section.id === 'in_cura' && <TableHead>Pressione</TableHead>}
                            {section.id === 'in_cura' && <TableHead>Tempo Rimanente</TableHead>}
                            <TableHead>Creato</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {sectionBatches.map(batch => (
                            <TableRow key={batch.id}>
                              <TableCell>
                                <div>
                                  <div className="font-medium">{batch.nome}</div>
                                  <div className="text-sm text-muted-foreground">
                                    {batch.numero_odl} ODL • {batch.numero_nesting} Nesting
                                  </div>
                                </div>
                              </TableCell>
                              
                              <TableCell>
                                <StatoBadge stato={batch.stato} />
                              </TableCell>
                              
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Gauge className="h-4 w-4 text-muted-foreground" />
                                  {batch.autoclave_nome}
                                </div>
                              </TableCell>
                              
                              {section.id === 'in_cura' && (
                                <>
                                  <TableCell>
                                    {batch.stato === 'in_cura' ? (
                                      <div className="space-y-1">
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                          <div 
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${getProgressPercentage(batch)}%` }}
                                          />
                                        </div>
                                        <div className="text-xs text-muted-foreground">
                                          {getProgressPercentage(batch).toFixed(1)}%
                                        </div>
                                      </div>
                                    ) : (
                                      <span className="text-muted-foreground">-</span>
                                    )}
                                  </TableCell>
                                  
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <Thermometer className="h-4 w-4 text-muted-foreground" />
                                      <div>
                                        <div className="text-sm">{formatTemperature(batch.temperatura_attuale)}</div>
                                        {batch.temperatura_target && (
                                          <div className="text-xs text-muted-foreground">
                                            Target: {formatTemperature(batch.temperatura_target)}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </TableCell>
                                  
                                  <TableCell>
                                    <div>
                                      <div className="text-sm">{formatPressure(batch.pressione_attuale)}</div>
                                      {batch.pressione_target && (
                                        <div className="text-xs text-muted-foreground">
                                          Target: {formatPressure(batch.pressione_target)}
                                        </div>
                                      )}
                                    </div>
                                  </TableCell>
                                  
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <Clock className="h-4 w-4 text-muted-foreground" />
                                      {formatDuration(batch.tempo_rimanente_minuti)}
                                    </div>
                                  </TableCell>
                                </>
                              )}
                              
                              <TableCell>
                                <div className="text-sm">
                                  {formatDateTime(batch.created_at)}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          )
        })}
      </div>
    </div>
  )
}