'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Separator } from '@/shared/components/ui/separator'
import { useToast } from '@/shared/components/ui/use-toast'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/components/ui/tabs'
import {
  Loader2, 
  ArrowLeft, 
  Package, 
  Flame, 
  CheckCircle2, 
  AlertTriangle,
  Download,
  RefreshCw,
  Info,
  CheckCircle,
  Clock,
  Settings,
  History,
  LayoutGrid
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'

// Importazione componenti dedicati
import BatchTabs from '../../../components/NestingResult/BatchTabs'
import NestingDetailsCard from '../../../components/NestingResult/NestingDetailsCard'
import BatchParameters from '../../../components/NestingResult/BatchParameters'
import HistoryPanel from '../../../components/NestingResult/HistoryPanel'
import EfficiencyAnalysis from './components/EfficiencyAnalysis'

// Caricamento dinamico del canvas
const NestingCanvas = dynamic(() => import('./NestingCanvas'), {
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="text-center space-y-3">
        <Loader2 className="h-8 w-8 text-blue-500 mx-auto animate-spin" />
        <div>
          <p className="text-sm font-medium text-gray-700">Caricamento Canvas</p>
          <p className="text-xs text-gray-500">Inizializzazione componenti 3D...</p>
        </div>
      </div>
    </div>
  ),
  ssr: false
})

// ✅ Hook per garantire il mounting client-side
const useClientSideOnly = () => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return isMounted;
};

// Interfacce per i dati multi-batch
interface ToolPosition {
  odl_id: number
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean
  part_number?: string
  tool_nome?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore?: string
}

interface BatchNestingResult {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: AutoclaveInfo
  odl_ids: number[]
  configurazione_json: {
    canvas_width: number
    canvas_height: number
    tool_positions: ToolPosition[]
    plane_assignments: Record<string, number>
  } | null
  parametri?: {
    padding_mm: number
    min_distance_mm: number
    // priorita_area rimosso (non utilizzato dall'algoritmo)
  }
  created_at: string
  updated_at?: string
  numero_nesting: number
  peso_totale_kg?: number
  area_totale_utilizzata?: number
  valvole_totali_utilizzate?: number
  note?: string
  odl_esclusi?: Array<{
    odl_id: number
    motivo: string
    dettagli?: string
    debug_reasons?: string[]
    motivi_dettagliati?: string
  }>
  excluded_reasons?: Record<string, number>
  metrics?: {
    efficiency_percentage?: number
    total_area_used_mm2?: number
    total_weight_kg?: number
  }
  // Campi legacy per compatibilità
  efficiency?: number
  data_conferma?: string
  data_completamento?: string
  confermato_da_utente?: string
  confermato_da_ruolo?: string
}

interface MultiBatchResponse {
  batch_results: BatchNestingResult[]
  execution_id?: string
  total_batches: number
  is_partial_multi_batch?: boolean
  batch_type?: string
  total_attempted_autoclavi?: number
}

interface Props {
  params: {
    batch_id: string
  }
}

export default function NestingResultPage({ params }: Props) {
  const { toast } = useToast()
  const router = useRouter()
  const [multiBatchData, setMultiBatchData] = useState<MultiBatchResponse | null>(null)
  const [selectedBatchIndex, setSelectedBatchIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)
  const isMounted = useClientSideOnly()

  useEffect(() => {
    loadMultiBatchData()
  }, [params.batch_id])

  // ✅ ROBUST MULTI-BATCH DETECTION: Always try multi-batch first
  const tryMultiBatchFirst = async (): Promise<MultiBatchResponse | null> => {
    try {
      console.log(`🚀 Trying multi-batch endpoint directly`)
      const multiUrl = `/api/batch_nesting/result/${params.batch_id}?multi=true`
      
      const multiResponse = await fetch(multiUrl, {
        headers: { 'Cache-Control': 'no-cache' }
      })
      
      if (multiResponse.ok) {
        const multiData: MultiBatchResponse = await multiResponse.json()
        
        // 🔧 FIX MULTI-BATCH PARZIALE: Considera anche batch singoli che erano parte di un tentativo multi-batch
        const hasBatchResults = multiData.batch_results && multiData.batch_results.length > 0
        const isPartialMultiBatch = multiData.is_partial_multi_batch || 
                                   multiData.batch_type === "multi_partial" ||
                                   (multiData.total_attempted_autoclavi || 0) > 1
        
        if (hasBatchResults && (multiData.batch_results.length > 1 || isPartialMultiBatch)) {
          const batchType = multiData.batch_results.length > 1 ? 'MULTI-COMPLETO' : 'MULTI-PARZIALE'
          console.log(`✅ Multi-batch FOUND: ${multiData.batch_results.length} batch (${batchType})`)
          
          if (isPartialMultiBatch) {
            console.log(`🚨 MULTI-BATCH PARZIALE: ${multiData.batch_results.length}/${multiData.total_attempted_autoclavi || 0} autoclavi riuscite`)
          }
          
          return multiData
        } else {
          console.log(`🔄 Multi-batch endpoint returned ${multiData.batch_results?.length || 0} batch - fallback to single`)
          return null
        }
      } else {
        console.log(`⚠️ Multi-batch endpoint failed: ${multiResponse.status}`)
        return null
      }
    } catch (error) {
      console.log(`⚠️ Multi-batch error:`, error)
      return null
    }
  }

  const loadMultiBatchData = async () => {
    try {
      setLoading(true)
      setError(null)

      console.log(`🔄 === ROBUST BATCH LOADING === ${params.batch_id}`)

      // ✅ PHASE 1: TRY MULTI-BATCH FIRST (always)
      console.log(`📡 Phase 1 - Multi-batch attempt`)
      const multiBatchResult = await tryMultiBatchFirst()
      
      let finalResult: MultiBatchResponse

      if (multiBatchResult) {
        // ✅ Multi-batch found - use it
        console.log(`✅ Using multi-batch data: ${multiBatchResult.batch_results.length} batches`)
        finalResult = multiBatchResult
      } else {
        // ✅ PHASE 2: FALLBACK TO SINGLE BATCH
        console.log(`📡 Phase 2 - Single batch fallback`)
        const metadataUrl = `/api/batch_nesting/${params.batch_id}`
        
        const metadataResponse = await fetch(metadataUrl, {
          headers: { 'Cache-Control': 'no-cache' }
        })
        
        if (!metadataResponse.ok) {
          throw new Error(`Metadata error: ${metadataResponse.status}`)
        }
        
        const baseBatch: BatchNestingResult = await metadataResponse.json()
        console.log(`✅ Single batch loaded: ${baseBatch.autoclave?.nome}`)
        
        finalResult = { batch_results: [baseBatch], total_batches: 1 }
      }

      // ✅ PHASE 4: VALIDATE AND NORMALIZE DATA
      const validBatches = finalResult.batch_results?.filter(batch => 
        batch && batch.id && batch.autoclave_id
      ) || []

      // ✅ NORMALIZE DATA: Assicura compatibilità e calcoli corretti
      const normalizedBatches = validBatches.map(batch => {
        // Normalizza efficiency per compatibilità legacy
        if (batch.efficiency && !batch.metrics?.efficiency_percentage) {
          batch.metrics = {
            ...batch.metrics,
            efficiency_percentage: batch.efficiency
          }
        }
        
        // Assicura che ci siano i campi minimi per il rendering
        if (!batch.metrics) {
          batch.metrics = {
            efficiency_percentage: batch.efficiency || 0,
            total_area_used_mm2: batch.area_totale_utilizzata || 0,
            total_weight_kg: batch.peso_totale_kg || 0
          }
        }
        
        // ✅ CALCOLO EFFICIENZA FALLBACK: Se l'efficienza è 0 ma ci sono tool posizionati
        if ((!batch.metrics.efficiency_percentage || batch.metrics.efficiency_percentage === 0) && 
            batch.configurazione_json?.tool_positions && 
            batch.configurazione_json.tool_positions.length > 0) {
          
          const toolPositions = batch.configurazione_json.tool_positions
          const autoclave = batch.autoclave
          
          if (autoclave && autoclave.lunghezza && autoclave.larghezza_piano) {
            // Calcola area totale utilizzata dai tool
            const totalToolArea = toolPositions.reduce((sum, tool) => {
              return sum + (tool.width * tool.height)
            }, 0)
            
            // Calcola area autoclave
            const autoclaveArea = autoclave.lunghezza * autoclave.larghezza_piano
            
            // Calcola efficienza come percentuale
            const calculatedEfficiency = (totalToolArea / autoclaveArea) * 100
            
            console.log(`🔧 CALCOLO EFFICIENZA FALLBACK:`)
            console.log(`   Tool area: ${totalToolArea} mm²`)
            console.log(`   Autoclave area: ${autoclaveArea} mm²`)
            console.log(`   Efficienza calcolata: ${calculatedEfficiency.toFixed(1)}%`)
            
            batch.metrics.efficiency_percentage = Math.round(calculatedEfficiency * 10) / 10
          }
        }
        
        return batch
      })

      console.log(`📊 Final validation: ${normalizedBatches.length} valid batches`)
      
      // Log efficienza per debug
      normalizedBatches.forEach((batch, i) => {
        const efficiency = batch.metrics?.efficiency_percentage || batch.efficiency || 0
        console.log(`   Batch ${i+1} efficienza: ${efficiency}%`)
      })

      // ✅ PHASE 5: SET IMMUTABLE STATE
      const immutableState: MultiBatchResponse = {
        batch_results: normalizedBatches,
        total_batches: normalizedBatches.length,
        execution_id: finalResult.execution_id
      }

      setMultiBatchData(immutableState)
      
      const currentIndex = normalizedBatches.findIndex(b => b.id === params.batch_id)
      setSelectedBatchIndex(currentIndex >= 0 ? currentIndex : 0)

      // ✅ PHASE 6: DETERMINISTIC LOGGING & NOTIFICATIONS
      const isMultiBatch = normalizedBatches.length > 1
      const isPartialMultiBatch = finalResult.is_partial_multi_batch || 
                                 finalResult.batch_type === "multi_partial" ||
                                 (finalResult.total_attempted_autoclavi || 0) > 1
      const uniqueAutoclavi = new Set(normalizedBatches.map(b => b.autoclave_id)).size
      const totalAttempted = finalResult.total_attempted_autoclavi || uniqueAutoclavi

      console.log(`🎯 === FINAL STATE ===`)
      console.log(`   Type: ${isMultiBatch ? 'MULTI-BATCH' : (isPartialMultiBatch ? 'MULTI-BATCH PARZIALE' : 'SINGLE-BATCH')}`)
      console.log(`   Batches: ${normalizedBatches.length}`)
      console.log(`   Autoclavi riuscite: ${uniqueAutoclavi}`)
      console.log(`   Autoclavi tentate: ${totalAttempted}`)
      console.log(`   Selected: ${currentIndex >= 0 ? currentIndex : 0}`)

      if (isMultiBatch) {
        normalizedBatches.forEach((batch, i) => {
          const autoclave = batch.autoclave?.nome || 'N/A'
          const efficiency = batch.metrics?.efficiency_percentage || batch.efficiency || 0
          console.log(`   ${i+1}. ${autoclave}: ${efficiency.toFixed(1)}%`)
        })

        toast({
          title: "🚀 Multi-Batch Confermato",
          description: `${normalizedBatches.length} batch per ${uniqueAutoclavi} autoclavi diverse`,
          duration: 4000,
        })
      } else if (isPartialMultiBatch) {
        // 🆕 CASO MULTI-BATCH PARZIALE
        const currentBatch = normalizedBatches[0]
        const autoclave = currentBatch?.autoclave?.nome || 'N/A'
        const efficiency = currentBatch?.metrics?.efficiency_percentage || currentBatch?.efficiency || 0
        
        console.log(`🚨 Multi-batch parziale confermato - ${autoclave}: ${efficiency.toFixed(1)}%`)
        
        toast({
          title: "⚠️ Multi-Batch Parziale",
          description: `1/${totalAttempted} autoclavi riuscite - Successo parziale su ${autoclave}`,
          duration: 6000,
        })
      } else {
        // Toast anche per single batch per confermare che i dati sono caricati
        const currentBatch = normalizedBatches[0]
        const efficiency = currentBatch?.metrics?.efficiency_percentage || currentBatch?.efficiency || 0
        console.log(`🔄 Single-batch confermato - Efficienza: ${efficiency.toFixed(1)}%`)
      }

    } catch (err) {
      console.error('❌ Fatal error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const currentBatch = multiBatchData?.batch_results[selectedBatchIndex]

  const getStatoBadge = (stato: string) => {
    switch (stato?.toLowerCase()) {
      case 'sospeso':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
          <Clock className="h-3 w-3 mr-1" />
          Sospeso
        </Badge>
      case 'confermato':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          <CheckCircle className="h-3 w-3 mr-1" />
          Confermato
        </Badge>
      case 'terminato':
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Terminato
        </Badge>
      default:
        return <Badge variant="secondary">{stato}</Badge>
    }
  }

  const handleConfirmBatch = async () => {
    if (!currentBatch || currentBatch.stato !== 'sospeso') return

    try {
      setIsConfirming(true)
      
      // Parametri richiesti per la conferma
      const confermato_da_utente = "ADMIN" // TODO: ottenere dall'utente loggato
      const confermato_da_ruolo = "ADMIN"
      
      const params = new URLSearchParams({
        confermato_da_utente,
        confermato_da_ruolo
      })
      
      const response = await fetch(`/api/batch_nesting/${currentBatch.id}/confirm?${params}`, {
        method: 'PATCH'
      })

      if (!response.ok) {
        const errorData = await response.text()
        throw new Error(errorData || 'Errore nella conferma del batch')
      }

      toast({
        title: "Batch Confermato",
        description: `Il batch ${currentBatch.nome} è stato confermato con successo`,
      })

      // Ricarica i dati
      await loadMultiBatchData()

    } catch (err) {
      console.error('❌ Errore conferma batch:', err)
      toast({
        title: "Errore",
        description: err instanceof Error ? err.message : "Errore nella conferma",
        variant: "destructive"
      })
    } finally {
      setIsConfirming(false)
    }
  }

  const handleDownloadReport = () => {
    if (!currentBatch) return
    
    const url = `/api/batch_nesting/${currentBatch.id}/export?format=pdf`
    window.open(url, '_blank')
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 text-blue-500 mx-auto animate-spin" />
            <div>
              <h3 className="text-lg font-semibold text-gray-700">Caricamento Risultati</h3>
              <p className="text-gray-500">Recupero dati batch nesting...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !multiBatchData) {
    return (
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-4">
            <AlertTriangle className="h-16 w-16 text-red-500 mx-auto" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">Errore nel Caricamento</h3>
              <p className="text-red-600">{error}</p>
              <div className="mt-4 space-x-2">
                <Button onClick={loadMultiBatchData} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Riprova
                </Button>
                <Link href="/dashboard/curing/nesting">
                  <Button variant="ghost">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Torna alla Lista
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-6">
      {/* Header con navigazione */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/curing/nesting">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Lista Nesting
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              {(() => {
                const isMultiBatch = multiBatchData.total_batches > 1
                const isPartialMultiBatch = multiBatchData.is_partial_multi_batch || 
                                           multiBatchData.batch_type === "multi_partial" ||
                                           (multiBatchData.total_attempted_autoclavi || 0) > 1
                
                if (isMultiBatch) {
                  return (
                    <>
                      🚀 Risultati Multi-Batch
                      <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-300">
                        {multiBatchData.total_batches} Autoclavi
                      </Badge>
                    </>
                  )
                } else if (isPartialMultiBatch) {
                  return (
                    <>
                      ⚠️ Multi-Batch Parziale
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300">
                        1/{multiBatchData.total_attempted_autoclavi} Riuscite
                      </Badge>
                    </>
                  )
                } else {
                  return 'Risultati Nesting'
                }
              })()}
            </h1>
            <p className="text-gray-600">
              {(() => {
                const isMultiBatch = multiBatchData.total_batches > 1
                const isPartialMultiBatch = multiBatchData.is_partial_multi_batch || 
                                           multiBatchData.batch_type === "multi_partial" ||
                                           (multiBatchData.total_attempted_autoclavi || 0) > 1
                
                if (isMultiBatch) {
                  return `${multiBatchData.total_batches} batch generati per autoclavi diverse`
                } else if (isPartialMultiBatch) {
                  return `Successo parziale: solo ${currentBatch?.autoclave?.nome} completata con successo`
                } else {
                  return 'Batch singolo'
                }
              })()} • {currentBatch?.autoclave?.nome || `Autoclave ${currentBatch?.autoclave_id}`}
              {multiBatchData.execution_id && ` • ID: ${multiBatchData.execution_id}`}
            </p>
          </div>
        </div>

        {/* Azioni batch corrente */}
        <div className="flex items-center gap-3">
          {currentBatch && getStatoBadge(currentBatch.stato)}
          

          
          <Button
            onClick={handleConfirmBatch}
            disabled={!currentBatch || currentBatch.stato !== 'sospeso' || isConfirming}
            className="bg-green-600 hover:bg-green-700"
          >
            {isConfirming ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2" />
            )}
            Conferma Batch
          </Button>

          <Button
            onClick={handleDownloadReport}
            variant="outline"
            disabled={!currentBatch}
          >
            <Download className="h-4 w-4 mr-2" />
            Esporta PDF
          </Button>
        </div>
      </div>

      {/* Navigazione Multi-Batch tramite Tab */}
      <BatchTabs
        batches={multiBatchData.batch_results}
        selectedIndex={selectedBatchIndex}
        onSelectionChange={setSelectedBatchIndex}
      />

      {/* Contenuto del batch selezionato */}
      {currentBatch && isMounted && (
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Canvas Principale - 3/4 della larghezza su desktop */}
          <div className="xl:col-span-3 order-2 xl:order-1 space-y-6">
            {/* Canvas Nesting */}
            <Card className="h-fit">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2">
                  <LayoutGrid className="h-5 w-5" />
                  Layout Nesting - {currentBatch.autoclave?.nome || `Autoclave ${currentBatch.autoclave_id}`}
                </CardTitle>
                <CardDescription>
                  Visualizzazione del posizionamento strumenti sull'autoclave
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-4">
                <NestingCanvas 
                  batchData={{
                    configurazione_json: currentBatch.configurazione_json,
                    autoclave: currentBatch.autoclave,
                    metrics: currentBatch.metrics,
                    id: currentBatch.id
                  }}
                  className="w-full"
                />
              </CardContent>
            </Card>

            {/* 🚀 ANALISI EFFICIENZA AEROSPACE */}
            {currentBatch.configurazione_json && currentBatch.autoclave && (
              <EfficiencyAnalysis
                efficiency={currentBatch.metrics?.efficiency_percentage || 0}
                totalAreaUsed={currentBatch.metrics?.total_area_used_mm2 || 0}
                totalWeight={currentBatch.metrics?.total_weight_kg || 0}
                planeWidth={currentBatch.autoclave.lunghezza}
                planeHeight={currentBatch.autoclave.larghezza_piano}
                toolPositions={currentBatch.configurazione_json.tool_positions || []}
                padding={currentBatch.parametri?.padding_mm || 1}
                minDistance={currentBatch.parametri?.min_distance_mm || 1}
              />
            )}
          </div>

          {/* Pannello Informazioni - 1/4 della larghezza su desktop */}
          <div className="xl:col-span-1 order-1 xl:order-2 space-y-4">
            {/* Dettagli Batch */}
            <NestingDetailsCard batch={currentBatch} />

            {/* Tab per informazioni aggiuntive */}
            <Card>
              <Tabs defaultValue="parameters" className="w-full">
                <CardHeader className="pb-3">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="parameters">
                      <Settings className="h-4 w-4 mr-1" />
                      Parametri
                    </TabsTrigger>
                    <TabsTrigger value="layout">
                      <Info className="h-4 w-4 mr-1" />
                      Layout
                    </TabsTrigger>
                    <TabsTrigger value="history">
                      <History className="h-4 w-4 mr-1" />
                      Cronologia
                    </TabsTrigger>
                  </TabsList>
                </CardHeader>

                <CardContent>
                  <TabsContent value="parameters" className="mt-0">
                    {currentBatch.parametri ? (
                      <BatchParameters batch={currentBatch} />
                    ) : (
                      <p className="text-sm text-gray-500">Nessun parametro disponibile</p>
                    )}
                  </TabsContent>

                  <TabsContent value="layout" className="mt-0">
                    <div className="space-y-3">
                      <h4 className="font-medium text-sm text-gray-700">Configurazione JSON</h4>
                      <pre className="text-xs bg-gray-50 p-3 rounded border overflow-auto max-h-64">
                        {JSON.stringify(currentBatch.configurazione_json, null, 2)}
                      </pre>
                    </div>
                  </TabsContent>

                  <TabsContent value="history" className="mt-0">
                    <HistoryPanel batch={currentBatch} />
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