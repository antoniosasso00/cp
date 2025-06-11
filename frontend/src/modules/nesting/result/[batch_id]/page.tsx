'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/components/ui/tabs'
import { Separator } from '@/shared/components/ui/separator'
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
  Award,
  Save,
  AlertCircle,
  Clock
} from 'lucide-react'
import { batchNestingApi } from '@/shared/lib/api'
import { formatDateTime } from '@/shared/lib/utils'
import dynamic from 'next/dynamic'
import { formatDistanceToNow } from 'date-fns'
import { it } from 'date-fns/locale'

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
  'draft': 'Bozza',
  'sospeso': 'In Sospeso',
  'confermato': 'Confermato', 
  'loaded': 'Caricato',
  'cured': 'In Cura',
  'terminato': 'Terminato',
  'undefined': 'Sconosciuto'
} as const

const STATO_COLORS = {
  'draft': 'bg-gray-100 text-gray-600',
  'sospeso': 'bg-yellow-100 text-yellow-800',
  'confermato': 'bg-green-100 text-green-800',
  'loaded': 'bg-blue-100 text-blue-800',
  'cured': 'bg-red-100 text-red-800',
  'terminato': 'bg-gray-100 text-gray-800',
  'undefined': 'bg-red-100 text-red-800'
} as const

// 🛡️ HELPER: Gestione sicura dello stato
const getSafeStatus = (stato: string | undefined): string => {
  return stato || 'undefined'
}

// 🛡️ HELPER: Gestione universale formati tool (compatibilità backward)
const getToolsFromBatch = (batch: any) => {
  // Prova prima il formato database standard, poi quello draft
  return batch?.configurazione_json?.tool_positions || batch?.configurazione_json?.positioned_tools || []
}

// 🛡️ HELPER: Verifica se il batch è una bozza salvabile
const isDraftBatch = (batch: any) => {
  if (!batch || !batch.stato) return false
  return batch.stato === 'draft' || batch.stato === 'DRAFT'
}

// 🛡️ HELPER: Icona stato batch
const getStatusIcon = (stato: string | undefined) => {
  if (!stato) return <AlertCircle className="h-4 w-4" />
  
  switch (stato.toLowerCase()) {
    case 'draft': return <Clock className="h-4 w-4" />
    case 'sospeso': return <Save className="h-4 w-4" />
    case 'confermato': return <CheckCircle2 className="h-4 w-4" />
    default: return <AlertCircle className="h-4 w-4" />
  }
}

// 🛡️ HELPER: Colore badge stato
const getStatusBadgeVariant = (stato: string | undefined): "default" | "secondary" | "destructive" | "outline" => {
  if (!stato) return 'outline'
  
  switch (stato.toLowerCase()) {
    case 'draft': return 'outline'
    case 'sospeso': return 'secondary'  
    case 'confermato': return 'default'
    default: return 'outline'
  }
}

export default function NestingResultPage() {
  const router = useRouter()
  const params = useParams()
  const searchParams = useSearchParams()
  const { toast } = useStandardToast()

  const batchId = params.batch_id as string
  // Removed confusing URL parameters - auto-detection is now the default

  const [batchData, setBatchData] = useState<BatchData | null>(null)
  const [allBatches, setAllBatches] = useState<BatchData[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState<string>(batchId)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [savingDraft, setSavingDraft] = useState<string | null>(null) // Track which batch is being saved

  // 🚀 RILEVAMENTO AUTOMATICO MULTI-BATCH: basato sui dati, non sui parametri URL
  const isMultiBatch = allBatches.length > 1

  useEffect(() => {
    loadBatchData()
  }, [batchId]) // Removed showAllDrafts dependency - auto-detection is always active

  // 🛡️ HELPER: Recupera dati autoclave se mancanti (per batch DRAFT)
  const enrichBatchWithAutoclaveData = async (batch: BatchData): Promise<BatchData> => {
    if (batch.autoclave || !batch.autoclave_id) {
      return batch // Dati già presenti o ID mancante
    }

    try {
      console.log(`🔧 DRAFT FIX: Recupero dati autoclave ${batch.autoclave_id} per batch DRAFT`)
      const autoclaveResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/autoclavi/${batch.autoclave_id}`)
      if (autoclaveResponse.ok) {
        const autoclaveData = await autoclaveResponse.json()
        return {
          ...batch,
          autoclave: {
            nome: autoclaveData.nome,
            codice: autoclaveData.codice,
            lunghezza: autoclaveData.lunghezza,
            larghezza_piano: autoclaveData.larghezza_piano
          }
        }
      }
    } catch (error) {
      console.warn(`⚠️ Impossibile recuperare dati autoclave ${batch.autoclave_id}:`, error)
    }

    // Fallback con dati minimi
    return {
      ...batch,
      autoclave: {
        nome: `Autoclave ${batch.autoclave_id}`,
        codice: `AUTO_${batch.autoclave_id}`,
        lunghezza: 0,
        larghezza_piano: 0
      }
    }
  }

  const loadBatchData = async () => {
    try {
      setLoading(true)
      
      console.log('🔍 CARICAMENTO INTELLIGENTE: Provo multi-batch per batch', batchId)
      
      // 🎯 RILEVAMENTO AUTOMATICO: Il sistema ora rileva automaticamente multi-batch
      const response = await batchNestingApi.getResult(batchId)
      
      if (response.batch_results && Array.isArray(response.batch_results) && response.batch_results.length > 1) {
        // ✅ MULTI-BATCH AUTO-RILEVATO: ordina per efficienza e arricchisci con dati autoclave
        console.log('🔧 MULTI-BATCH: Arricchimento dati autoclave per batch DRAFT...')
        
        const enrichedBatches = await Promise.all(
          response.batch_results.map((batch: BatchData) => enrichBatchWithAutoclaveData(batch))
        )
        
        const sortedBatches = enrichedBatches.sort((a: BatchData, b: BatchData) => {
          const effA = a.metrics?.efficiency_percentage || 0
          const effB = b.metrics?.efficiency_percentage || 0
          return effB - effA
        })
        
        setAllBatches(sortedBatches)
        
        // Trova il batch corrente o usa il migliore
        const currentBatch = sortedBatches.find((b: BatchData) => b.id === batchId) || sortedBatches[0]
        setBatchData(currentBatch)
        setSelectedBatchId(currentBatch.id)
        
        console.log('✅ MULTI-BATCH AUTO-RILEVATO:', sortedBatches.length, 'batch caricati e arricchiti')
        
        toast({
          title: '🚀 Multi-Batch Auto-Rilevato',
          description: `${sortedBatches.length} batch generati per autoclavi diverse`
        })
        
        return // Multi-batch trovato, processo completato
      }
      
      // 🎯 SINGLE-BATCH: nessun batch correlato trovato, arricchisci con dati autoclave
      console.log('✅ SINGLE-BATCH CARICATO (nessun batch correlato)')
      const singleResponse = Array.isArray(response) ? response[0] : response
      
      // Arricchisci il single-batch con dati autoclave se necessario
      console.log('🔧 SINGLE-BATCH: Arricchimento dati autoclave per batch DRAFT...')
      const enrichedSingleBatch = await enrichBatchWithAutoclaveData(singleResponse)
      
      setAllBatches([enrichedSingleBatch])
      setBatchData(enrichedSingleBatch)
      setSelectedBatchId(enrichedSingleBatch.id)
      
      console.log('✅ SINGLE-BATCH CARICATO')
      
      toast({
        title: 'Batch Caricato',
        description: 'Risultati nesting disponibili'
      })

    } catch (error) {
      console.error('❌ ERRORE CARICAMENTO:', error)
      setError('Impossibile caricare i dati del batch')
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

  // 🛡️ FUNZIONE: Salva bozza (promuove da DRAFT a SOSPESO)
  const handleSaveDraft = async (batchId: string) => {
    try {
      setSavingDraft(batchId)
      toast({
        title: 'Salvataggio bozza',
        description: 'Salvataggio in corso...'
      })
      
      // Chiamata API per promuovere draft a sospeso
      const response = await fetch(`/api/batch_nesting/${batchId}/promote`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_state: 'sospeso',
          promoted_by_user: 'ADMIN', // TODO: usare utente reale
          promoted_by_role: 'ADMIN'
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore durante il salvataggio')
      }

      const result = await response.json()
      
      // Aggiorna lo stato locale
      setBatchData((prev: any) => prev?.id === batchId ? { ...prev, stato: 'sospeso' } : prev)
      setAllBatches(prev => prev.map(batch => 
        batch.id === batchId ? { ...batch, stato: 'sospeso' } : batch
      ))

      toast({
        title: 'Bozza salvata',
        description: 'Batch promosso a stato "Sospeso"'
      })
      
      // Refresh automatico per sincronizzare con il backend
      setTimeout(loadBatchData, 1500)
      
    } catch (error) {
      console.error('Errore salvataggio bozza:', error)
      toast({
        title: 'Errore salvataggio',
        description: `Impossibile salvare la bozza: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: 'destructive'
      })
    } finally {
      setSavingDraft(null)
    }
  }

  // 🛡️ FUNZIONE: Elimina bozza con conferma
  const handleDeleteDraft = async (batchId: string) => {
    const confirmed = window.confirm('Sei sicuro di voler eliminare questa bozza? L\'operazione non può essere annullata.')
    if (!confirmed) return

    try {
      setSavingDraft(batchId) // Riusa la stessa variabile per disabilitare i pulsanti
      toast({
        title: 'Eliminazione bozza',
        description: 'Eliminazione in corso...'
      })
      
      const response = await fetch(`/api/batch_nesting/draft/${batchId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore durante l\'eliminazione')
      }

      // Rimuovi dalla lista locale e redirigi se necessario
      if (batchData?.id === batchId) {
        // Se stiamo eliminando il batch corrente, redirigi alla lista
        toast({
          title: 'Bozza eliminata',
          description: 'Reindirizzamento alla lista...'
        })
        setTimeout(() => router.push('/nesting/list'), 1500)
      } else {
        // Rimuovi solo dalla lista
        setAllBatches(prev => prev.filter(batch => batch.id !== batchId))
        toast({
          title: 'Bozza eliminata',
          description: 'Eliminazione completata con successo'
        })
      }
      
    } catch (error) {
      console.error('Errore eliminazione bozza:', error)
      toast({
        title: 'Errore eliminazione',
        description: `Impossibile eliminare la bozza: ${error instanceof Error ? error.message : 'Errore sconosciuto'}`,
        variant: 'destructive'
      })
    } finally {
      setSavingDraft(null)
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
      {/* DRAFT WARNING BANNER */}
      {isDraftBatch(batchData) && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-amber-600" />
            <div className="flex-1">
              <p className="text-amber-800 font-medium">
                🚧 Batch in modalità BOZZA - Non ancora salvato nel database
              </p>
              <p className="text-amber-700 text-sm mt-1">
                Questo batch è temporaneo e verrà perso se non salvato. 
                {isMultiBatch ? `${allBatches.filter(isDraftBatch).length} di ${allBatches.length} batch sono bozze.` : 'Salva per renderlo permanente.'}
              </p>
            </div>
            <Button
              onClick={() => handleSaveDraft(batchData.id)}
              disabled={savingDraft === batchData.id}
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              {savingDraft === batchData.id ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Salva Ora
            </Button>
          </div>
        </div>
      )}

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
                  {allBatches.some(isDraftBatch) && (
                    <Badge variant="outline" className="text-amber-600 border-amber-300">
                      <Clock className="h-3 w-3 mr-1" />
                      DRAFT
                    </Badge>
                  )}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Risultati Batch
                  {isDraftBatch(batchData) && (
                    <Badge variant="outline" className="text-amber-600 border-amber-300">
                      <Clock className="h-3 w-3 mr-1" />
                      DRAFT
                    </Badge>
                  )}
                </span>
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
        
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadBatchData}
            disabled={updating}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${updating ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          
          {/* 🛡️ GESTIONE BOZZE: Pulsanti contestuali */}
          {isDraftBatch(batchData) && (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => handleSaveDraft(batchData.id)}
                disabled={savingDraft === batchData.id}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              >
                {savingDraft === batchData.id ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Salva Bozza
              </Button>
              
              <Button
                variant="outline"
                onClick={() => handleDeleteDraft(batchData.id)}
                disabled={savingDraft === batchData.id}
                className="flex items-center gap-2 text-red-600 border-red-200 hover:bg-red-50"
              >
                <AlertCircle className="h-4 w-4" />
                Elimina
              </Button>
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
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
                            <Badge className={getStatusBadgeVariant(batch.stato)}>
                              {getStatusIcon(batch.stato)}
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
                              {getToolsFromBatch(batch).length > 0 ? (
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                  {getToolsFromBatch(batch).map((tool: any, index: number) => (
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
                  <Badge className={getStatusBadgeVariant(batchData.stato)}>
                    {getStatusIcon(batchData.stato)}
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
                    {getToolsFromBatch(batchData).length > 0 ? (
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {getToolsFromBatch(batchData).map((tool: any, index: number) => (
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