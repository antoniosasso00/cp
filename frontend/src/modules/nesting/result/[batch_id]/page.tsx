'use client'

import { useState, useEffect, useMemo, useCallback } from 'react'
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
  Clock,
  Layers,
  Layers3
} from 'lucide-react'
import { batchNestingApi } from '@/shared/lib/api'
import { formatDateTime } from '@/shared/lib/utils'
import dynamic from 'next/dynamic'
import { formatDistanceToNow } from 'date-fns'
import { it } from 'date-fns/locale'
import { ExitConfirmationDialog } from '@/shared/components/ui/exit-confirmation-dialog'
import { useDraftLifecycle } from '@/shared/hooks/use-draft-lifecycle'
import { DraftActionDialog } from './components/DraftActionDialog'
import { ExitPageDialog } from './components/ExitPageDialog'
import { CompatibilityTest } from './components/CompatibilityTest'

// 🎯 INTERFACCE COMPLETE: Supporto per tool positioning unificato
interface ToolPosition {
  odl_id?: number
  tool_id?: number
  x: number
  y: number
  width: number
  height: number
  rotated?: boolean
  weight_kg?: number
  // 🆕 CAMPI 2L: Supporto per livelli e cavalletti
  level?: number               // 0 = piano base, 1 = su cavalletti
  z_position?: number          // Posizione Z (altezza)
  lines_used?: number          // Linee vuoto utilizzate
  // Informazioni aggiuntive
  part_number?: string          // Part number della parte
  part_number_tool?: string     // Part number del tool (diverso)
  numero_odl?: string | number  // Numero ODL (non ID)
  descrizione_breve?: string    // Descrizione della parte
  tool_nome?: string           // Nome tool come fallback
  peso?: number                // Peso per tooltip
}

interface Cavalletto {
  x: number
  y: number
  width: number
  height: number
  tool_odl_id: number
  tool_id?: number
  sequence_number: number
  center_x: number
  center_y: number
  support_area_mm2: number
  height_mm: number
  load_capacity_kg: number
}

// 🎯 SMART CANVAS LOADING: Dynamic import con auto-detection 2L
const NestingCanvas = dynamic(() => import('./components/NestingCanvas'), {
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-50 border rounded-lg">
      <div className="text-center space-y-3">
        <Loader2 className="h-8 w-8 text-blue-500 mx-auto animate-spin" />
        <p className="text-sm text-gray-600">Caricamento canvas 1L...</p>
      </div>
    </div>
  ),
  ssr: false
})

const NestingCanvas2L = dynamic(() => import('./components/NestingCanvas2L').then(mod => ({ default: mod.NestingCanvas2L })), {
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-50 border rounded-lg">
      <div className="text-center space-y-3">
        <Loader2 className="h-8 w-8 text-amber-500 mx-auto animate-spin" />
        <p className="text-sm text-gray-600">Caricamento canvas 2L...</p>
        <div className="flex items-center justify-center gap-1 text-xs text-amber-600">
          <Layers3 className="h-3 w-3" />
          <span>Modalità Multi-Livello</span>
        </div>
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
  'sospeso': 'Sospeso',
  'in_cura': 'In Cura',
  'terminato': 'Terminato',
  'undefined': 'Sconosciuto'
} as const

const STATO_COLORS = {
  'draft': 'bg-gray-100 text-gray-600',
  'sospeso': 'bg-yellow-100 text-yellow-800',
  'in_cura': 'bg-red-100 text-red-800',
  'terminato': 'bg-green-100 text-green-800',
  'undefined': 'bg-red-100 text-red-800'
} as const

// 🛡️ HELPER: Gestione sicura dello stato
const getSafeStatus = (stato: string | undefined): string => {
  return stato || 'undefined'
}

// 🛡️ HELPER: Ottiene tool dal batch (compatibilità universale)
const getToolsFromBatch = (batchData: BatchData): ToolPosition[] => {
  if (!batchData.configurazione_json) return []
  
  // 🎯 NUOVO: Parsing migliorato per compatibilità 2L/1L
  let tools = batchData.configurazione_json.tool_positions || 
              batchData.configurazione_json.positioned_tools || 
              []
  
  // 🔧 FIX: Converte format 2L in formato compatibile con frontend
  return tools.map((tool: any) => ({
    odl_id: tool.odl_id || tool.id,
    tool_id: tool.tool_id,
    x: tool.x,
    y: tool.y,
    width: tool.width,
    height: tool.height,
    rotated: tool.rotated || false,
    weight_kg: tool.weight_kg || tool.weight || tool.peso || 0,
    // 🆕 CAMPI 2L (con fallback per retrocompatibilità)
    level: tool.level !== undefined ? tool.level : 0,
    z_position: tool.z_position || (tool.level === 1 ? 100 : 0),
    lines_used: tool.lines_used || 1,
    // Informazioni aggiuntive
    part_number: tool.part_number,
    part_number_tool: tool.part_number_tool,
    numero_odl: typeof tool.numero_odl === 'string' ? tool.numero_odl : 
              typeof tool.numero_odl === 'number' ? tool.numero_odl.toString() :
              `ODL${String(tool.odl_id ?? 0).padStart(3, '0')}`,
    descrizione_breve: tool.descrizione_breve,
    tool_nome: tool.tool_nome,
    peso: tool.peso || tool.weight_kg || tool.weight || 0
  }))
}

// 🆕 HELPER: Ottiene cavalletti dal batch (nuovo per 2L)
const getCavallettiFromBatch = (batchData: BatchData): Cavalletto[] => {
  if (!batchData.configurazione_json?.cavalletti) return []
  
  return batchData.configurazione_json.cavalletti.map((cav: any) => ({
    x: cav.x,
    y: cav.y,
    width: cav.width,
    height: cav.height,
    tool_odl_id: cav.tool_odl_id,
    tool_id: cav.tool_id,
    sequence_number: cav.sequence_number || 0,
    center_x: cav.center_x || cav.x + cav.width / 2,
    center_y: cav.center_y || cav.y + cav.height / 2,
    support_area_mm2: cav.support_area_mm2 || cav.width * cav.height,
    height_mm: cav.height_mm || 100,
    load_capacity_kg: cav.load_capacity_kg || 300
  }))
}

// 🆕 HELPER: Verifica se il batch ha supporto 2L (migliorato)
const isBatch2L = (batch: any): boolean => {
  if (!batch) return false
  
  const tools = getToolsFromBatch(batch)
  const cavalletti = getCavallettiFromBatch(batch)
  const configJson = batch.configurazione_json || {}
  
  // Criteri multipli per detection 2L
  const has2LTools = tools.some(tool => 
    tool.level !== undefined && tool.level !== null && tool.level > 0
  )
  const hasCavalletti = cavalletti.length > 0
  const has2LMarkers = configJson.is_2l_batch === true || 
                       configJson.algorithm_used?.includes('2L') ||
                       configJson.level_0_count !== undefined ||
                       configJson.level_1_count !== undefined
  
  return has2LTools || hasCavalletti || has2LMarkers
}

// 🎯 COMPONENTE SMART CANVAS: Sceglie automaticamente il canvas giusto
const SmartCanvas: React.FC<{ batchData: any }> = ({ batchData }) => {
  const is2L = isBatch2L(batchData)
  const tools = getToolsFromBatch(batchData)
  const cavalletti = getCavallettiFromBatch(batchData)
  
  // 🔍 DEBUG COMPLETO: Log informazioni per troubleshooting
  console.log('🎯 SMART CANVAS - Auto-detection:', {
    batchId: batchData.id,
    is2L,
    toolsCount: tools.length,
    cavallettiCount: cavalletti.length,
    hasLevels: tools.some((t: any) => t.level !== undefined && t.level !== null),
    levelDistribution: {
      level0: tools.filter(t => (t.level ?? 0) === 0).length,
      level1: tools.filter(t => t.level === 1).length
    },
    // 🚨 DEBUG: Dati raw per verifica
    rawConfigJson: batchData.configurazione_json ? Object.keys(batchData.configurazione_json) : [],
    autoclaveData: batchData.autoclave ? 'presente' : 'mancante',
    toolSample: tools.slice(0, 2) // Prime 2 tool per debug
  })

  // 🛡️ VALIDAZIONE: Verifica dati canvas
  const hasValidAutoclave = batchData.autoclave || batchData.autoclave_id
  const canvasWidth = batchData.autoclave?.lunghezza || 1000
  const canvasHeight = batchData.autoclave?.larghezza_piano || 800

  if (!hasValidAutoclave) {
    console.warn('⚠️ SMART CANVAS: Dati autoclave mancanti', batchData)
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-center space-y-3">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto" />
          <p className="text-red-700 font-medium">Errore Dati Autoclave</p>
          <p className="text-red-600 text-sm">Impossibile visualizzare il canvas senza informazioni autoclave</p>
        </div>
      </div>
    )
  }

  if (tools.length === 0) {
    console.warn('⚠️ SMART CANVAS: Nessun tool trovato', batchData.configurazione_json)
    return (
      <div className="flex items-center justify-center h-96 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="text-center space-y-3">
          <Package className="h-8 w-8 text-yellow-500 mx-auto" />
          <p className="text-yellow-700 font-medium">Nessun Tool Posizionato</p>
          <p className="text-yellow-600 text-sm">Il batch non contiene tool da visualizzare</p>
        </div>
      </div>
    )
  }

  if (is2L) {
    // 🟡 BATCH 2L: Usa canvas specializzato
    console.log('✅ SMART CANVAS: Rendering 2L con', tools.length, 'tool e', cavalletti.length, 'cavalletti')
    
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-2 rounded-lg border border-amber-200">
          <Layers3 className="h-4 w-4" />
          <span className="font-medium">Batch 2L rilevato - Canvas multi-livello attivo</span>
          <Badge variant="secondary" className="ml-auto">
            L0: {tools.filter((t: any) => (t.level ?? 0) === 0).length} | 
            L1: {tools.filter((t: any) => t.level === 1).length}
          </Badge>
        </div>
        
        <NestingCanvas2L
          positioned_tools={tools.map(tool => ({
            odl_id: tool.odl_id ?? 0,
            tool_id: tool.tool_id ?? tool.odl_id ?? 0,
            x: tool.x,
            y: tool.y,
            width: tool.width,
            height: tool.height,
            rotated: Boolean(tool.rotated),
            weight_kg: tool.weight_kg ?? tool.peso ?? 0,
            level: tool.level ?? 0,
            z_position: tool.z_position ?? (tool.level === 1 ? 100 : 0),
            lines_used: tool.lines_used ?? 1,
            part_number: tool.part_number,
            descrizione_breve: tool.descrizione_breve,
            numero_odl: typeof tool.numero_odl === 'string' ? tool.numero_odl : 
                      typeof tool.numero_odl === 'number' ? tool.numero_odl.toString() :
                      `ODL${String(tool.odl_id ?? 0).padStart(3, '0')}`
          }))}
          cavalletti={cavalletti}
          canvas_width={canvasWidth}
          canvas_height={canvasHeight}
          showLevelFilter={true}
        />
      </div>
    )
  } else {
    // 🔵 BATCH 1L: Usa canvas standard (retrocompatibilità)
    console.log('✅ SMART CANVAS: Rendering 1L con', tools.length, 'tool')
    
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-2 rounded-lg border border-blue-200">
          <Layers className="h-4 w-4" />
          <span className="font-medium">Batch 1L standard - Canvas tradizionale</span>
          <Badge variant="secondary" className="ml-auto">
            Tools: {tools.length}
          </Badge>
        </div>
        
        <NestingCanvas
          batchData={{
            id: batchData.id,
            configurazione_json: batchData.configurazione_json,
            autoclave: batchData.autoclave,
            metrics: batchData.metrics
          }}
        />  
      </div>
    )
  }
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
  
  // 🔧 PARAMETERS: Enhanced URL parameter support for 2L debugging
  const isMultiMode = searchParams.get('multi') === 'true'
  const has2L = searchParams.get('has_2l') === 'true'
  const showAll = searchParams.get('show_all') === 'true'
  
  console.log('🎯 URL Params for 2L debugging:', { batchId, isMultiMode, has2L, showAll })

  const [batchData, setBatchData] = useState<BatchData | null>(null)
  const [allBatches, setAllBatches] = useState<BatchData[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState<string>(batchId)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  
  // 🎯 NEW: State per i nuovi dialog
  const [showDraftActionDialog, setShowDraftActionDialog] = useState(false)
  const [selectedBatchForAction, setSelectedBatchForAction] = useState<BatchData | null>(null)
  const [currentAction, setCurrentAction] = useState<'save' | 'delete' | null>(null)

  // 🚀 PERFORMANCE: Memoized computation for multi-batch detection
  const isMultiBatch = useMemo(() => allBatches.length > 1, [allBatches.length])

  // 🛡️ DRAFT LIFECYCLE MANAGEMENT: Enhanced with performance optimizations
  const draftLifecycle = useDraftLifecycle({
    allBatches,
    selectedBatchId,
    onBatchChange: useCallback((newBatchId, newBatchData) => {
      setSelectedBatchId(newBatchId)
      setBatchData(newBatchData as BatchData)
    }, []),
    onBatchRemoved: useCallback((batchId) => {
      setAllBatches(prev => prev.filter(batch => batch.id !== batchId))
    }, [])
  })

  useEffect(() => {
    loadBatchData()
  }, [batchId])

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

  // 🚀 PERFORMANCE & EDGE CASES: Enhanced loadBatchData with optimizations
  const loadBatchData = useCallback(async () => {
    // 🛡️ EDGE CASE: Validate batch ID
    if (!batchId || batchId === 'undefined') {
      setError('ID batch non valido')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      console.log('🔍 CARICAMENTO INTELLIGENTE: Provo multi-batch per batch', batchId)
      
      // 🎯 RILEVAMENTO AUTOMATICO: Il sistema ora rileva automaticamente multi-batch
      const response = await batchNestingApi.getResult(batchId)
      
      // 🛡️ EDGE CASE: Handle null/undefined response
      if (!response) {
        throw new Error('Nessuna risposta dal server')
      }
      
      if (response.batch_results && Array.isArray(response.batch_results) && response.batch_results.length > 1) {
        // ✅ MULTI-BATCH AUTO-RILEVATO: ordina per efficienza e arricchisci con dati autoclave
        console.log('🔧 MULTI-BATCH: Arricchimento dati autoclave per batch DRAFT...')
        
        // 🔧 DEBUG: Aggiungi logging per 2L detection
        const batch2LCount = response.batch_results.filter((batch: BatchData) => isBatch2L(batch)).length
        console.log(`📊 MULTI-BATCH ANALYSIS: ${response.batch_results.length} batch trovati, ${batch2LCount} sono 2L`)
        
        response.batch_results.forEach((batch: BatchData, index: number) => {
          const is2L = isBatch2L(batch)
          console.log(`   Batch ${index + 1}: ${batch.id} - Type: ${is2L ? '2L' : '1L'} - Autoclave: ${batch.autoclave_id}`)
        })
        
        // 🚀 PERFORMANCE: Process autoclave data in parallel
        const enrichedBatches = await Promise.all(
          response.batch_results.map((batch: BatchData) => enrichBatchWithAutoclaveData(batch))
        )
        
        // 🚀 PERFORMANCE: Optimized sorting with null checks
        const sortedBatches = enrichedBatches.sort((a: BatchData, b: BatchData) => {
          const effA = a.metrics?.efficiency_percentage || 0
          const effB = b.metrics?.efficiency_percentage || 0
          return effB - effA
        })
        
        setAllBatches(sortedBatches)
        
        // 🛡️ EDGE CASE: Handle missing selected batch
        const currentBatch = sortedBatches.find((b: BatchData) => b.id === batchId) || sortedBatches[0]
        if (!currentBatch) {
          throw new Error('Nessun batch valido trovato')
        }
        
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
      
      // 🛡️ EDGE CASE: Validate single response
      if (!singleResponse || !singleResponse.id) {
        throw new Error('Dati batch non validi')
      }
      
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
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto'
      setError(`Impossibile caricare i dati del batch: ${errorMessage}`)
      toast({
        title: 'Errore caricamento',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }, [batchId, toast]) // 🚀 PERFORMANCE: Memoized with dependencies

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

  // 🎯 NEW: Gestori per le azioni sui draft con dialog elegante
  const handleSaveDraftRequest = (batch: BatchData) => {
    setSelectedBatchForAction(batch)
    setCurrentAction('save')
    setShowDraftActionDialog(true)
  }

  const handleDeleteDraftRequest = (batch: BatchData) => {
    setSelectedBatchForAction(batch)
    setCurrentAction('delete')
    setShowDraftActionDialog(true)
  }

  const handleConfirmDraftAction = async () => {
    if (!selectedBatchForAction || !currentAction) return

    try {
      if (currentAction === 'save') {
        await draftLifecycle.handleSaveDraft(selectedBatchForAction.id)
      } else if (currentAction === 'delete') {
        await draftLifecycle.handleDeleteDraft(selectedBatchForAction.id)
      }
    } finally {
      setShowDraftActionDialog(false)
      setSelectedBatchForAction(null)
      setCurrentAction(null)
    }
  }

  const handleCloseDraftActionDialog = () => {
    setShowDraftActionDialog(false)
    setSelectedBatchForAction(null)
    setCurrentAction(null)
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

  // 🆕 Analisi batch misti (2L + 1L)
  const mixedBatchStats = isMultiBatch ? {
    batch2L: allBatches.filter(b => isBatch2L(b)),
    batch1L: allBatches.filter(b => !isBatch2L(b)),
    hasMixedConfiguration: allBatches.some(b => isBatch2L(b)) && allBatches.some(b => !isBatch2L(b))
  } : null

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      {/* EXIT CONFIRMATION DIALOG */}
      <ExitConfirmationDialog
        open={draftLifecycle.showExitDialog}
        onOpenChange={draftLifecycle.setShowExitDialog}
        draftCount={draftLifecycle.draftCount}
        onConfirmExit={draftLifecycle.handleConfirmExit}
        onSaveAll={draftLifecycle.handleSaveAllDrafts}
        isProcessing={draftLifecycle.savingDraft === 'all'}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            onClick={() => draftLifecycle.handleNavigation(() => router.push('/nesting/list'))}
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
                  Gestione Multi-Batch
                  <Badge variant="secondary">{allBatches.length} batch</Badge>
                  {draftLifecycle.hasUnsavedDrafts && (
                    <Badge variant="outline" className="text-amber-600 border-amber-300">
                      <Clock className="h-3 w-3 mr-1" />
                      {draftLifecycle.draftCount} DRAFT
                    </Badge>
                  )}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Risultati Batch
                  {draftLifecycle.isDraftBatch(batchData) && (
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
        
        <div className="flex items-center gap-2">
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
          
          {/* 🛡️ GESTIONE BOZZE: Pulsanti contestuali solo se è un draft */}
          {draftLifecycle.isDraftBatch(batchData) && (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => handleSaveDraftRequest(batchData)}
                disabled={draftLifecycle.savingDraft === batchData.id}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              >
                {draftLifecycle.savingDraft === batchData.id ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Salva Bozza
              </Button>
              
              <Button
                variant="outline"
                onClick={() => handleDeleteDraftRequest(batchData)}
                disabled={draftLifecycle.savingDraft === batchData.id}
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

      {/* 🆕 Pannello Informativo Batch Misti */}
      {isMultiBatch && mixedBatchStats?.hasMixedConfiguration && (
        <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Layers3 className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h3 className="font-medium text-amber-800">Configurazione Batch Mista Rilevata</h3>
                <p className="text-sm text-amber-700">
                  {mixedBatchStats.batch2L.length} batch generati con nesting 2L (cavalletti) + {mixedBatchStats.batch1L.length} batch con nesting 1L standard
                </p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-100">
                  <Layers3 className="h-3 w-3 mr-1" />
                  {mixedBatchStats.batch2L.length} × 2L
                </Badge>
                <Badge variant="outline" className="text-blue-700 border-blue-300 bg-blue-100">
                  <Layers className="h-3 w-3 mr-1" />
                  {mixedBatchStats.batch1L.length} × 1L
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
                {allBatches.map((batch, index) => {
                  const is2L = isBatch2L(batch)
                  return (
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
                        {/* 🆕 INDICATORE 2L/1L */}
                        {is2L ? (
                          <Layers3 className="h-3 w-3 text-amber-600" />
                        ) : (
                          <Layers className="h-3 w-3 text-blue-600" />
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Efficienza: {batch.metrics?.efficiency_percentage?.toFixed(1) || '0.0'}%
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <span>Tool: {batch.metrics?.positioned_tools || 0}</span>
                        {/* 🆕 BADGE MODALITÀ */}
                        <Badge variant="outline" className={`text-xs px-1 py-0 ${is2L ? 'text-amber-600 border-amber-300' : 'text-blue-600 border-blue-300'}`}>
                          {is2L ? '2L' : '1L'}
                        </Badge>
                      </div>
                    </TabsTrigger>
                  )
                })}
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
                          <SmartCanvas batchData={batch} />
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
                <SmartCanvas batchData={batchData} />
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

      {/* 🎯 NEW: Dialog per azioni sui draft (elegante come Conferma Avanzamento ODL) */}
      <DraftActionDialog
        open={showDraftActionDialog}
        onOpenChange={setShowDraftActionDialog}
        batch={selectedBatchForAction}
        action={currentAction}
        isProcessing={draftLifecycle.savingDraft === selectedBatchForAction?.id}
        onConfirm={handleConfirmDraftAction}
      />

      {/* 🚪 NEW: Dialog di uscita dalla pagina per proteggere draft */}
      <ExitPageDialog
        open={draftLifecycle.showExitDialog}
        onOpenChange={draftLifecycle.setShowExitDialog}
        draftBatches={draftLifecycle.draftBatches}
        isSaving={draftLifecycle.savingDraft === 'all'}
        onSaveAndExit={draftLifecycle.handleSaveAndExit}
        onExitWithoutSaving={draftLifecycle.handleExitWithoutSaving}
        onStayOnPage={draftLifecycle.handleStayOnPage}
      />

      {/* 🧪 DEBUG: Componente di test di compatibilità per troubleshooting */}
      {batchData && process.env.NODE_ENV === 'development' && (
        <div className="mt-6">
          <CompatibilityTest batchData={batchData} />
        </div>
      )}
    </div>
  )
} 