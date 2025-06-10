'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useParams, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/components/ui/tabs'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  ArrowLeft, 
  Loader2, 
  LayoutGrid, 
  Package,
  Settings,
  CheckCircle2,
  Download,
  RefreshCw,
  Info,
  Award
} from 'lucide-react'
import { batchNestingApi } from '@/shared/lib/api'
import { formatDateTime } from '@/shared/lib/utils'
import dynamic from 'next/dynamic'

// Dynamic import for canvas component
const NestingCanvas = dynamic(() => import('./components/NestingCanvas'), {
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-50 border rounded-lg">
      <div className="text-center space-y-3">
        <Loader2 className="h-8 w-8 text-blue-500 mx-auto animate-spin" />
        <p className="text-sm text-gray-600">Caricamento canvas...</p>
      </div>
    </div>
  ),
  ssr: false
})

interface BatchData {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: {
    nome: string
    codice: string
    lunghezza: number
    larghezza_piano: number
  }
  configurazione_json?: any
  metrics?: {
    efficiency_percentage: number
    total_weight_kg: number
    positioned_tools: number
    excluded_tools: number
  }
  created_at: string
  updated_at: string
}

interface MultiBatchData {
  batch_results: BatchData[]
  is_real_multi_batch?: boolean
}

const STATO_LABELS = {
  'sospeso': 'In Sospeso',
  'confermato': 'Confermato', 
  'loaded': 'Caricato',
  'cured': 'In Cura',
  'terminato': 'Terminato'
}

const STATO_COLORS = {
  'sospeso': 'bg-yellow-100 text-yellow-800',
  'confermato': 'bg-green-100 text-green-800',
  'loaded': 'bg-blue-100 text-blue-800',
  'cured': 'bg-red-100 text-red-800',
  'terminato': 'bg-gray-100 text-gray-800'
}

export default function NestingResultPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const { toast } = useStandardToast()

  const batchId = params.batch_id as string
  const forceMultiBatch = searchParams.get('multi') === 'true'

  const [batchData, setBatchData] = useState<BatchData | null>(null)
  const [allBatches, setAllBatches] = useState<BatchData[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState<string>(batchId)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  // Determina se è multi-batch basandosi sui dati disponibili
  const isMultiBatch = allBatches.length > 1 || forceMultiBatch

  useEffect(() => {
    loadBatchData()
  }, [batchId, forceMultiBatch])

  const loadBatchData = async () => {
    try {
      setLoading(true)
      
      // Tenta sempre di caricare come multi-batch per verificare se ci sono più batch
      const response = await batchNestingApi.getResult(batchId, { multi: true })
      
      if (response.batch_results && Array.isArray(response.batch_results)) {
        // Multi-batch response
        const sortedBatches = response.batch_results.sort((a: BatchData, b: BatchData) => {
          const effA = a.metrics?.efficiency_percentage || 0
          const effB = b.metrics?.efficiency_percentage || 0
          return effB - effA // Ordina per efficienza decrescente
        })
        
        setAllBatches(sortedBatches)
        
        // Trova il batch corrente o usa il primo
        const currentBatch = sortedBatches.find((b: BatchData) => b.id === batchId) || sortedBatches[0]
        setBatchData(currentBatch)
        setSelectedBatchId(currentBatch.id)
        
        toast({
          title: 'Dati caricati',
          description: `${sortedBatches.length} batch caricati (modalità multi-batch)`
        })
      } else {
        // Single batch fallback
        const singleResponse = await batchNestingApi.getResult(batchId)
        setAllBatches([singleResponse])
        setBatchData(singleResponse)
        setSelectedBatchId(singleResponse.id)
        
        toast({
          title: 'Dati caricati',
          description: 'Batch singolo caricato'
        })
      }

    } catch (error) {
      toast({
        title: 'Errore caricamento',
        description: 'Impossibile caricare i dati del batch',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleBatchChange = (batchId: string) => {
    const batch = allBatches.find(b => b.id === batchId)
    if (batch) {
      setSelectedBatchId(batchId)
      setBatchData(batch)
    }
  }

  const handleConfirmBatch = async () => {
    if (!batchData) return

    try {
      setUpdating(true)
      await batchNestingApi.confirm(batchData.id, {
        confermato_da_utente: 'ADMIN',
        confermato_da_ruolo: 'ADMIN'
      })
      
      await loadBatchData()
      toast({
        title: 'Batch confermato',
        description: 'Il batch è stato confermato con successo'
      })
    } catch (error) {
      toast({
        title: 'Errore conferma',
        description: 'Impossibile confermare il batch',
        variant: 'destructive'
      })
    } finally {
      setUpdating(false)
    }
  }

  const handleExport = async () => {
    if (!batchData) return

    try {
      const data = {
        batch: batchData,
        all_batches: isMultiBatch ? allBatches : undefined,
        export_timestamp: new Date().toISOString()
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `batch_${batchData.id.slice(0, 8)}_${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast({
        title: 'Export completato',
        description: 'Dati esportati con successo'
      })
    } catch (error) {
      toast({
        title: 'Errore export',
        description: 'Impossibile esportare i dati',
        variant: 'destructive'
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Caricamento risultati...</p>
        </div>
      </div>
    )
  }

  if (!batchData) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="text-center py-8">
            <Package className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Batch non trovato</p>
            <Button onClick={() => router.push('/nesting/list')} className="mt-4">
              Torna alla lista
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Calcola statistiche aggregate per multi-batch
  const aggregateStats = isMultiBatch ? {
    avgEfficiency: allBatches.reduce((sum, b) => sum + (b.metrics?.efficiency_percentage || 0), 0) / allBatches.length,
    totalTools: allBatches.reduce((sum, b) => sum + (b.metrics?.positioned_tools || 0), 0),
    totalWeight: allBatches.reduce((sum, b) => sum + (b.metrics?.total_weight_kg || 0), 0),
    bestEfficiency: Math.max(...allBatches.map(b => b.metrics?.efficiency_percentage || 0))
  } : null

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            onClick={() => router.push('/nesting/list')}
            variant="outline"
            size="sm"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Lista Batch
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {isMultiBatch ? (
                <span className="flex items-center gap-2">
                  Risultati Multi-Batch
                  <Badge variant="secondary">{allBatches.length} batch</Badge>
                </span>
              ) : (
                'Risultati Batch'
              )}
            </h1>
            <p className="text-muted-foreground">
              {batchData.nome}
              {aggregateStats && (
                <span className="ml-2 text-sm">
                  • Media: {aggregateStats.avgEfficiency.toFixed(1)}% 
                  • Best: {aggregateStats.bestEfficiency.toFixed(1)}%
                </span>
              )}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button onClick={loadBatchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button onClick={handleExport} variant="outline" size="sm">
            <Download className="h-4 w-4" />
          </Button>
          {batchData.stato === 'sospeso' && (
            <Button 
              onClick={handleConfirmBatch}
              disabled={updating}
              size="sm"
            >
              {updating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 className="mr-2 h-4 w-4" />
              )}
              Conferma
            </Button>
          )}
        </div>
      </div>

      {/* Multi-batch Tabs */}
      {isMultiBatch && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Batch Generati - Ordinati per Efficienza
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={selectedBatchId} onValueChange={handleBatchChange} className="w-full">
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 h-auto">
                {allBatches.map((batch, index) => (
                  <TabsTrigger 
                    key={batch.id} 
                    value={batch.id}
                    className="flex flex-col items-center p-3 h-auto data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    <div className="flex items-center gap-2">
                      {index === 0 && <Award className="h-4 w-4 text-yellow-500" />}
                      <span className="font-medium">
                        {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Efficienza: {batch.metrics?.efficiency_percentage?.toFixed(1) || '0.0'}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Tool: {batch.metrics?.positioned_tools || 0}
                    </div>
                  </TabsTrigger>
                ))}
              </TabsList>

              {allBatches.map((batch, index) => (
                <TabsContent key={batch.id} value={batch.id} className="mt-6">
                  <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                    {/* Canvas - 3/4 width */}
                    <div className="xl:col-span-3 space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <LayoutGrid className="h-5 w-5" />
                            Layout Nesting - {batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}
                            {index === 0 && (
                              <Badge variant="default" className="ml-2 bg-yellow-500">
                                <Award className="h-3 w-3 mr-1" />
                                Migliore
                              </Badge>
                            )}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <NestingCanvas
                            batchData={{
                              id: batch.id,
                              configurazione_json: batch.configurazione_json,
                              autoclave: batch.autoclave,
                              metrics: batch.metrics
                            }}
                          />
                        </CardContent>
                      </Card>
                    </div>

                    {/* Sidebar - 1/4 width */}
                    <div className="xl:col-span-1 space-y-4">
                      {/* Batch Info */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <Package className="h-5 w-5" />
                            Dettagli Batch
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Stato</p>
                            <Badge className={STATO_COLORS[batch.stato as keyof typeof STATO_COLORS] || 'bg-gray-100 text-gray-800'}>
                              {STATO_LABELS[batch.stato as keyof typeof STATO_LABELS] || batch.stato}
                            </Badge>
                          </div>
                          
                          <div>
                            <p className="text-sm font-medium text-muted-foreground">ID Batch</p>
                            <p className="text-sm font-mono text-xs">{batch.id}</p>
                          </div>

                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Autoclave</p>
                            <p className="text-sm">{batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}</p>
                            {batch.autoclave?.codice && (
                              <p className="text-xs text-muted-foreground">{batch.autoclave.codice}</p>
                            )}
                          </div>

                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Dimensioni</p>
                            <p className="text-sm">
                              {batch.autoclave?.lunghezza || 0}×{batch.autoclave?.larghezza_piano || 0}mm
                            </p>
                          </div>

                          <div>
                            <p className="text-sm font-medium text-muted-foreground">Creato</p>
                            <p className="text-sm">{formatDateTime(batch.created_at)}</p>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Metrics */}
                      {batch.metrics && (
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              <Info className="h-5 w-5" />
                              Metriche
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div>
                              <p className="text-sm font-medium text-muted-foreground">Efficienza</p>
                              <p className="text-lg font-bold text-green-600">
                                {batch.metrics.efficiency_percentage.toFixed(1)}%
                              </p>
                            </div>

                            <div>
                              <p className="text-sm font-medium text-muted-foreground">Tool Posizionati</p>
                              <p className="text-lg font-bold">{batch.metrics.positioned_tools}</p>
                            </div>

                            {batch.metrics.excluded_tools > 0 && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground">Tool Esclusi</p>
                                <p className="text-lg font-bold text-red-600">{batch.metrics.excluded_tools}</p>
                              </div>
                            )}

                            <div>
                              <p className="text-sm font-medium text-muted-foreground">Peso Totale</p>
                              <p className="text-lg font-bold">{batch.metrics.total_weight_kg.toFixed(1)}kg</p>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Configuration Tabs */}
                      <Card>
                        <Tabs defaultValue="tools" className="w-full">
                          <CardHeader className="pb-3">
                            <TabsList className="grid w-full grid-cols-2">
                              <TabsTrigger value="tools">Tool</TabsTrigger>
                              <TabsTrigger value="config">Config</TabsTrigger>
                            </TabsList>
                          </CardHeader>

                          <CardContent>
                            <TabsContent value="tools" className="space-y-2">
                              {batch.configurazione_json?.tool_positions?.length > 0 ? (
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                  {batch.configurazione_json.tool_positions.map((tool: any, index: number) => (
                                    <div key={index} className="text-xs p-2 bg-muted rounded">
                                      <p className="font-medium">{tool.part_number_tool || `Tool ${index + 1}`}</p>
                                      <p className="text-muted-foreground">
                                        {tool.x?.toFixed(0)},{tool.y?.toFixed(0)} 
                                        {tool.rotated ? ' (ruotato)' : ''}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground">Nessun tool posizionato</p>
                              )}
                            </TabsContent>

                            <TabsContent value="config" className="space-y-2">
                              <div className="text-xs space-y-2">
                                <div>
                                  <span className="font-medium">Padding:</span> {
                                    batch.configurazione_json?.padding_mm || 
                                    batch.configurazione_json?.parametri_nesting?.padding_mm || 
                                    batch.configurazione_json?.parametri?.padding_mm ||
                                    (batch.configurazione_json?.request_data?.parametri?.padding_mm) ||
                                    'N/A'
                                  }mm
                                </div>
                                <div>
                                  <span className="font-medium">Algoritmo:</span> {
                                    batch.configurazione_json?.algorithm_used || 
                                    batch.configurazione_json?.strategy_mode || 
                                    batch.configurazione_json?.algoritmo ||
                                    'Aerospace'
                                  }
                                </div>
                                <div>
                                  <span className="font-medium">Tempo:</span> {
                                    batch.configurazione_json?.execution_time_ms || 
                                    batch.configurazione_json?.total_generation_time_ms || 
                                    batch.configurazione_json?.tempo_esecuzione_ms ||
                                    'N/A'
                                  }{batch.configurazione_json?.execution_time_ms || batch.configurazione_json?.total_generation_time_ms ? 'ms' : ''}
                                </div>
                                {(batch.configurazione_json?.parametri_nesting?.min_distance_mm || 
                                  batch.configurazione_json?.parametri?.min_distance_mm ||
                                  batch.configurazione_json?.request_data?.parametri?.min_distance_mm) && (
                                  <div>
                                    <span className="font-medium">Distanza min:</span> {
                                      batch.configurazione_json?.parametri_nesting?.min_distance_mm || 
                                      batch.configurazione_json?.parametri?.min_distance_mm ||
                                      batch.configurazione_json?.request_data?.parametri?.min_distance_mm
                                    }mm
                                  </div>
                                )}
                                {batch.configurazione_json?.autoclave_target && (
                                  <div>
                                    <span className="font-medium">Target:</span> {batch.configurazione_json.autoclave_target}
                                  </div>
                                )}
                                {(batch.configurazione_json?.odl_ids || batch.configurazione_json?.request_data?.odl_ids) && (
                                  <div>
                                    <span className="font-medium">ODL IDs:</span> {
                                      Array.isArray(batch.configurazione_json?.odl_ids) ? 
                                        batch.configurazione_json.odl_ids.join(', ') : 
                                      Array.isArray(batch.configurazione_json?.request_data?.odl_ids) ?
                                        batch.configurazione_json.request_data.odl_ids.join(', ') :
                                        'N/A'
                                    }
                                  </div>
                                )}
                              </div>
                            </TabsContent>
                          </CardContent>
                        </Tabs>
                      </Card>
                    </div>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Single Batch Layout (when not multi-batch) */}
      {!isMultiBatch && (
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Canvas - 3/4 width */}
          <div className="xl:col-span-3 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LayoutGrid className="h-5 w-5" />
                  Layout Nesting - {batchData.autoclave?.nome || `Autoclave ${batchData.autoclave_id}`}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <NestingCanvas
                  batchData={{
                    id: batchData.id,
                    configurazione_json: batchData.configurazione_json,
                    autoclave: batchData.autoclave,
                    metrics: batchData.metrics
                  }}
                />
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - 1/4 width */}
          <div className="xl:col-span-1 space-y-4">
            {/* Batch Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Dettagli Batch
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Stato</p>
                  <Badge className={STATO_COLORS[batchData.stato as keyof typeof STATO_COLORS] || 'bg-gray-100 text-gray-800'}>
                    {STATO_LABELS[batchData.stato as keyof typeof STATO_LABELS] || batchData.stato}
                  </Badge>
                </div>
                
                <div>
                  <p className="text-sm font-medium text-muted-foreground">ID Batch</p>
                  <p className="text-sm font-mono">{batchData.id}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Autoclave</p>
                  <p className="text-sm">{batchData.autoclave?.nome || `Autoclave ${batchData.autoclave_id}`}</p>
                  {batchData.autoclave?.codice && (
                    <p className="text-xs text-muted-foreground">{batchData.autoclave.codice}</p>
                  )}
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Dimensioni</p>
                  <p className="text-sm">
                    {batchData.autoclave?.lunghezza || 0}×{batchData.autoclave?.larghezza_piano || 0}mm
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">Creato</p>
                  <p className="text-sm">{formatDateTime(batchData.created_at)}</p>
                </div>
              </CardContent>
            </Card>

            {/* Metrics */}
            {batchData.metrics && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="h-5 w-5" />
                    Metriche
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Efficienza</p>
                    <p className="text-lg font-bold text-green-600">
                      {batchData.metrics.efficiency_percentage.toFixed(1)}%
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Tool Posizionati</p>
                    <p className="text-lg font-bold">{batchData.metrics.positioned_tools}</p>
                  </div>

                  {batchData.metrics.excluded_tools > 0 && (
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Tool Esclusi</p>
                      <p className="text-lg font-bold text-red-600">{batchData.metrics.excluded_tools}</p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Peso Totale</p>
                    <p className="text-lg font-bold">{batchData.metrics.total_weight_kg.toFixed(1)}kg</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Configuration Tabs */}
            <Card>
              <Tabs defaultValue="tools" className="w-full">
                <CardHeader className="pb-3">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="tools">Tool</TabsTrigger>
                    <TabsTrigger value="config">Config</TabsTrigger>
                  </TabsList>
                </CardHeader>

                <CardContent>
                  <TabsContent value="tools" className="space-y-2">
                    {batchData.configurazione_json?.tool_positions?.length > 0 ? (
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {batchData.configurazione_json.tool_positions.map((tool: any, index: number) => (
                          <div key={index} className="text-xs p-2 bg-muted rounded">
                            <p className="font-medium">{tool.part_number_tool || `Tool ${index + 1}`}</p>
                            <p className="text-muted-foreground">
                              {tool.x?.toFixed(0)},{tool.y?.toFixed(0)} 
                              {tool.rotated ? ' (ruotato)' : ''}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">Nessun tool posizionato</p>
                    )}
                  </TabsContent>

                  <TabsContent value="config" className="space-y-2">
                    <div className="text-xs space-y-2">
                      <div>
                        <span className="font-medium">Padding:</span> {
                          batchData.configurazione_json?.padding_mm || 
                          batchData.configurazione_json?.parametri_nesting?.padding_mm || 
                          batchData.configurazione_json?.parametri?.padding_mm ||
                          (batchData.configurazione_json?.request_data?.parametri?.padding_mm) ||
                          'N/A'
                        }mm
                      </div>
                      <div>
                        <span className="font-medium">Algoritmo:</span> {
                          batchData.configurazione_json?.algorithm_used || 
                          batchData.configurazione_json?.strategy_mode || 
                          batchData.configurazione_json?.algoritmo ||
                          'Aerospace'
                        }
                      </div>
                      <div>
                        <span className="font-medium">Tempo:</span> {
                          batchData.configurazione_json?.execution_time_ms || 
                          batchData.configurazione_json?.total_generation_time_ms || 
                          batchData.configurazione_json?.tempo_esecuzione_ms ||
                          'N/A'
                        }{batchData.configurazione_json?.execution_time_ms || batchData.configurazione_json?.total_generation_time_ms ? 'ms' : ''}
                      </div>
                      {(batchData.configurazione_json?.parametri_nesting?.min_distance_mm || 
                        batchData.configurazione_json?.parametri?.min_distance_mm ||
                        batchData.configurazione_json?.request_data?.parametri?.min_distance_mm) && (
                        <div>
                          <span className="font-medium">Distanza min:</span> {
                            batchData.configurazione_json?.parametri_nesting?.min_distance_mm || 
                            batchData.configurazione_json?.parametri?.min_distance_mm ||
                            batchData.configurazione_json?.request_data?.parametri?.min_distance_mm
                          }mm
                        </div>
                      )}
                      {batchData.configurazione_json?.autoclave_target && (
                        <div>
                          <span className="font-medium">Target:</span> {batchData.configurazione_json.autoclave_target}
                        </div>
                      )}
                      {(batchData.configurazione_json?.odl_ids || batchData.configurazione_json?.request_data?.odl_ids) && (
                        <div>
                          <span className="font-medium">ODL IDs:</span> {
                            Array.isArray(batchData.configurazione_json?.odl_ids) ? 
                              batchData.configurazione_json.odl_ids.join(', ') : 
                            Array.isArray(batchData.configurazione_json?.request_data?.odl_ids) ?
                              batchData.configurazione_json.request_data.odl_ids.join(', ') :
                              'N/A'
                          }
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </CardContent>
              </Tabs>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
} 