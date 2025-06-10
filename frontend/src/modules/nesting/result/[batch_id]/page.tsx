'use client'

import React, { useState, useEffect, Suspense, useCallback, useMemo } from 'react'
import { useToast } from '@/shared/components/ui/use-toast'
import { Loader2, MousePointer, X } from 'lucide-react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { Button } from '@/shared/components/ui/button'

// Importazione componenti nuovi
import CompactHeader from './components/CompactHeader'
import BatchActions from './components/BatchActions'

// Lazy loading per NestingCanvasV2 e NestingToolbox
const NestingCanvasV2 = dynamic(() => import('./components/NestingCanvasV2'), {
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

const NestingToolbox = dynamic(() => import('./components/NestingToolbox'), {
  loading: () => (
    <div className="flex items-center justify-center h-64 bg-gray-50 border border-gray-200 rounded-lg">
      <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
    </div>
  ),
  ssr: false
})



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
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [selectedToolId, setSelectedToolId] = useState<number | null>(null)
  const [showToolDrawer, setShowToolDrawer] = useState(false)

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

  // Callback per apertura drawer quando tool selezionato
  const handleToolSelect = useCallback((odlId: number | null) => {
    setSelectedToolId(odlId)
    setShowToolDrawer(!!odlId)
  }, [])

  // Trova le informazioni del tool selezionato
  const selectedToolInfo = useMemo(() => {
    if (!selectedToolId || !currentBatch?.configurazione_json?.tool_positions.length) return null
    
    const tool = currentBatch.configurazione_json.tool_positions.find(t => t.odl_id === selectedToolId)
    if (!tool) return null
    
    // Trova ODL associato se possibile
    const odlInfo = currentBatch.odl_ids?.includes(selectedToolId) ? {
      id: selectedToolId,
      // Aggiungi altre informazioni ODL se disponibili
    } : null
    
    return { tool, odlInfo }
  }, [selectedToolId, currentBatch])

  const handleConfirmBatch = async () => {
    if (!currentBatch || currentBatch.stato !== 'sospeso') return

    try {
      setIsFullscreen(true)
      
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
    }
  }

  const handleDownloadReport = () => {
    if (!currentBatch) return
    
    const url = `/api/batch_nesting/${currentBatch.id}/export?format=pdf`
    window.open(url, '_blank')
  }

  // Get canvas data
  const canvasData = currentBatch?.configurazione_json
  const toolPositions = canvasData?.tool_positions || []
  const canvasWidth = canvasData?.canvas_width || 1000
  const canvasHeight = canvasData?.canvas_height || 800
  const efficiency = currentBatch?.metrics?.efficiency_percentage || currentBatch?.efficiency || 0

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
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="text-red-500 text-6xl">⚠️</div>
          <div>
            <p className="text-lg font-medium text-gray-700">Errore nel caricamento</p>
            <p className="text-sm text-gray-500">{error || 'Dati non trovati'}</p>
          </div>
          <button 
            onClick={loadMultiBatchData}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Riprova
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compact Header */}
      <CompactHeader
        batchName={currentBatch?.nome || `Batch ${currentBatch?.numero_nesting || ''}`}
        batchState={currentBatch?.stato || ''}
        efficiency={efficiency}
        totalBatches={multiBatchData?.total_batches}
        onRefresh={loadMultiBatchData}
        onDownload={handleDownloadReport}
        isLoading={loading}
      />

      {/* Main Content - Layout 80/20 */}
      <div className="flex h-[calc(100vh-80px)]">
        {/* Left section - Canvas (80%) */}
        <div className="flex-1 p-4">
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-full bg-white border border-gray-200 rounded-lg">
                <div className="text-center space-y-3">
                  <Loader2 className="h-12 w-12 text-blue-500 mx-auto animate-spin" />
                  <div>
                    <p className="text-lg font-medium text-gray-700">Caricamento Canvas</p>
                    <p className="text-sm text-gray-500">Inizializzazione vista 3D...</p>
                  </div>
                </div>
              </div>
            }
          >
            <NestingCanvasV2
              canvasWidth={canvasWidth}
              canvasHeight={canvasHeight}
              toolPositions={toolPositions}
              planeAssignments={canvasData?.plane_assignments}
              isFullscreen={isFullscreen}
              onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
              onToolSelect={handleToolSelect}
              className={isFullscreen ? 'fixed inset-0 z-50 bg-white' : 'h-full'}
            />
          </Suspense>
        </div>

        {/* Right section - Sidebar (20%) */}
        <div className="w-80 border-l bg-white p-4 space-y-4 overflow-y-auto">
          {/* Tool Drawer */}
          {showToolDrawer && selectedToolInfo && (
            <div className="border rounded-lg p-4 bg-blue-50 border-blue-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-blue-800 flex items-center gap-2">
                  <MousePointer className="h-4 w-4" />
                  Tool Selezionato
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowToolDrawer(false)}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="font-medium text-blue-800">ODL {selectedToolInfo.tool.odl_id}</div>
                  {selectedToolInfo.tool.part_number && (
                    <div className="text-sm text-blue-600">{selectedToolInfo.tool.part_number}</div>
                  )}
                  {selectedToolInfo.tool.tool_nome && (
                    <div className="text-sm text-blue-600">{selectedToolInfo.tool.tool_nome}</div>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="font-medium">Posizione:</span>
                    <div className="text-blue-600">
                      X: {selectedToolInfo.tool.x.toFixed(0)}mm<br/>
                      Y: {selectedToolInfo.tool.y.toFixed(0)}mm
                    </div>
                  </div>
                  <div>
                    <span className="font-medium">Dimensioni:</span>
                    <div className="text-blue-600">
                      {selectedToolInfo.tool.width.toFixed(0)} × {selectedToolInfo.tool.height.toFixed(0)}mm
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="font-medium">Peso:</span>
                    <div className="text-blue-600">{selectedToolInfo.tool.peso.toFixed(1)} kg</div>
                  </div>
                  <div>
                    <span className="font-medium">Orientamento:</span>
                    <div className="text-blue-600">
                      {selectedToolInfo.tool.rotated ? 'Ruotato' : 'Normale'}
                    </div>
                  </div>
                </div>
                
                <div className="pt-2 border-t border-blue-200">
                  <div className="text-xs text-blue-600">
                    📍 Posizionato automaticamente dall'algoritmo di nesting
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Batch Actions */}
          <BatchActions
            batchId={currentBatch?.id || ''}
            batchState={currentBatch?.stato || ''}
            onSaveDraft={async () => {}} 
            onConfirm={handleConfirmBatch}
            onCancel={async () => {}}
            onDelete={async () => {}}
            onDownload={() => handleDownloadReport()}
            onExportReport={() => handleDownloadReport()}
            isLoading={loading}
          />

          {/* Multi-batch selector */}
          {multiBatchData?.total_batches > 1 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-700">Seleziona Batch</h3>
              <div className="space-y-1">
                {multiBatchData?.batch_results.map((batch, index) => (
                  <button
                    key={batch.id}
                    onClick={() => setSelectedBatchIndex(index)}
                    className={`w-full text-left p-2 rounded border text-sm ${
                      index === selectedBatchIndex
                        ? 'bg-blue-50 border-blue-200 text-blue-800'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}</div>
                    <div className="text-xs text-gray-500">
                      {(batch.metrics?.efficiency_percentage || batch.efficiency || 0).toFixed(1)}% efficienza
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Nesting Toolbox */}
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-64 bg-gray-50 border border-gray-200 rounded-lg">
                <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
              </div>
            }
          >
            <NestingToolbox
              toolPositions={toolPositions}
              autoclave={currentBatch?.autoclave}
              canvasWidth={canvasWidth}
              canvasHeight={canvasHeight}
              efficiency={efficiency}
              totalWeight={currentBatch?.peso_totale_kg}
              totalArea={currentBatch?.area_totale_utilizzata}
              odlExcluded={currentBatch?.odl_esclusi}
            />
          </Suspense>
        </div>
      </div>
    </div>
  )
}