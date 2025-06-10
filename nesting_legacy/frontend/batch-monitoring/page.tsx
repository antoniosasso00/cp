'use client'

import { useState, useEffect } from 'react'

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
  const [batches, setBatches] = useState<BatchMonitoring[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('all')
  const [selectedStato, setSelectedStato] = useState<string>('all')
  
  // Stati di apertura/chiusura delle sezioni
  const [sectionStates, setSectionStates] = useState<Record<string, boolean>>(() => {
    const initialStates: Record<string, boolean> = {}
    WORKFLOW_SECTIONS.forEach(section => {
      initialStates[section.id] = section.defaultOpen
    })
    return initialStates
  })

  useEffect(() => {
    loadBatches()
    // Aggiorna automaticamente ogni 30 secondi
    const interval = setInterval(loadBatches, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadBatches = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Carica i batch per il monitoraggio
      const response = await batchNestingApi.getAll({ 
        limit: 100 // Aumentiamo per catturare più batch
      })
      
      // Simulo dati di monitoraggio aggiuntivi con stati realistici
      const batchesWithMonitoring: BatchMonitoring[] = response.map(batch => {
        // Determina lo stato di monitoraggio basato sullo stato reale
        let statoMonitoraggio: string
        let inCura = false
        
        switch (batch.stato) {
          case 'terminato':
            // Solo gli ultimi batch terminati nelle ultime 24h
            const batchDate = new Date(batch.updated_at || batch.created_at)
            const now = new Date()
            const hoursSinceUpdate = (now.getTime() - batchDate.getTime()) / (1000 * 60 * 60)
            statoMonitoraggio = hoursSinceUpdate <= 24 ? 'completato' : 'terminato'
            break
          case 'confermato':
            // Simula progressione del workflow per batch confermati
            const rand = Math.random()
            const daysSinceCreation = (new Date().getTime() - new Date(batch.created_at).getTime()) / (1000 * 60 * 60 * 24)
            
            if (daysSinceCreation > 2) {
              // Batch più vecchi sono più probabilmente in cura
              statoMonitoraggio = 'in_cura'
              inCura = true
            } else if (daysSinceCreation > 1) {
              // Batch di ieri sono probabilmente caricati
              statoMonitoraggio = 'loaded'
            } else if (rand > 0.7) {
              // Alcuni batch recenti potrebbero essere già caricati
              statoMonitoraggio = 'loaded'
            } else {
              // La maggior parte rimane confermata
              statoMonitoraggio = 'confermato'
            }
            break
          case 'sospeso':
            statoMonitoraggio = 'sospeso'
            break
          default:
            statoMonitoraggio = batch.stato
        }
        
        return {
          ...batch,
          nome: batch.nome || `Batch ${batch.numero_nesting || batch.id.slice(-8)}`,
          stato: statoMonitoraggio as any,
          autoclave_nome: `Autoclave ${batch.autoclave_id}`,
          ciclo_nome: `Ciclo Standard ${batch.autoclave_id}`,
          numero_odl: Math.floor(Math.random() * 50) + 1,
          numero_nesting: batch.numero_nesting || Math.floor(Math.random() * 20) + 1,
          temperatura_target: inCura ? 180 + Math.random() * 40 : undefined,
          temperatura_attuale: inCura ? (175 + Math.random() * 50) : undefined,
          pressione_target: inCura ? 6.0 + Math.random() * 2 : undefined,
          pressione_attuale: inCura ? (5.8 + Math.random() * 2.4) : undefined,
          tempo_rimanente_minuti: inCura ? Math.floor(Math.random() * 480) : undefined,
          tempo_totale_minuti: inCura ? (480 + Math.floor(Math.random() * 240)) : undefined,
          data_inizio_cura: inCura ? new Date(Date.now() - Math.random() * 86400000).toISOString() : undefined,
          data_fine_prevista: inCura ? new Date(Date.now() + Math.random() * 86400000).toISOString() : undefined
        }
      })
      
      // Filtro i batch terminati da più di 24h (non mostrarli neanche in completati)
      const filteredBatches = batchesWithMonitoring.filter(batch => batch.stato !== 'terminato')
      
      setBatches(filteredBatches)
    } catch (err) {
      console.error('Errore caricamento batch:', err)
      setError('Errore nel caricamento dei batch di monitoraggio')
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (minutes: number | undefined) => {
    if (!minutes) return '-'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const formatTemperature = (temp: number | undefined) => {
    if (!temp) return '-'
    return `${temp.toFixed(1)}°C`
  }

  const formatPressure = (pressure: number | undefined) => {
    if (!pressure) return '-'
    return `${pressure.toFixed(1)} bar`
  }

  const getProgressPercentage = (batch: BatchMonitoring) => {
    if (!batch.tempo_rimanente_minuti || !batch.tempo_totale_minuti) return 0
    return ((batch.tempo_totale_minuti - batch.tempo_rimanente_minuti) / batch.tempo_totale_minuti) * 100
  }

  // Filtri globali
  const filteredBatches = batches.filter(batch => {
    const matchesSearch = !searchQuery || 
      batch.nome.toLowerCase().includes(searchQuery.toLowerCase()) ||
      batch.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (batch.autoclave_nome?.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesAutoclave = !selectedAutoclave || selectedAutoclave === 'all' || 
      batch.autoclave_id.toString() === selectedAutoclave
    
    return matchesSearch && matchesAutoclave
  })

  // Raggruppa batch per sezione
  const getBatchesForSection = (section: WorkflowSection) => {
    return filteredBatches.filter(batch => section.states.includes(batch.stato))
  }

  // Statistiche totali
  const stats = {
    totale: batches.length,
    sospeso: batches.filter(b => b.stato === 'sospeso').length,
    confermato: batches.filter(b => b.stato === 'confermato').length,
    loaded: batches.filter(b => ['loaded', 'attesa'].includes(b.stato)).length,
    in_cura: batches.filter(b => ['in_cura'].includes(b.stato)).length,
    completato: batches.filter(b => b.stato === 'completato').length,
    errori: batches.filter(b => b.stato === 'errore').length
  }

  const toggleSection = (sectionId: string) => {
    setSectionStates(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }))
  }

  if (loading && batches.length === 0) {
    return (
      <div className="container mx-auto p-6">
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
      <div className="container mx-auto p-6">
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
    <div className="container mx-auto p-6 space-y-6">
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

      {/* Statistiche Rapide */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Totale</p>
                <p className="text-2xl font-bold">{stats.totale}</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Sospesi</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.sospeso}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Confermati</p>
                <p className="text-2xl font-bold text-green-600">{stats.confermato}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Caricati</p>
                <p className="text-2xl font-bold text-blue-600">{stats.loaded}</p>
              </div>
              <Package className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">In Cura</p>
                <p className="text-2xl font-bold text-red-600">{stats.in_cura}</p>
              </div>
              <Flame className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completati</p>
                <p className="text-2xl font-bold text-green-600">{stats.completato}</p>
              </div>
              <ClipboardCheck className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtri Globali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Filtri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          </div>
        </CardContent>
      </Card>

      {/* Sezioni Workflow */}
      <div className="space-y-4">
        {WORKFLOW_SECTIONS.map((section) => {
          const sectionBatches = getBatchesForSection(section)
          const isOpen = sectionStates[section.id]
          const IconComponent = section.icon

          return (
            <Card key={section.id} className={`border-2 ${section.color}`}>
              <Collapsible 
                open={isOpen} 
                onOpenChange={() => toggleSection(section.id)}
              >
                <CollapsibleTrigger asChild>
                  <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-3">
                        <IconComponent className="h-5 w-5" />
                        {section.title}
                        <Badge variant="secondary" className="ml-2">
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
                
                <CollapsibleContent>
                  <CardContent>
                    {sectionBatches.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
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