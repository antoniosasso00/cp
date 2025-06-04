'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import {
  Zap, 
  RotateCcw, 
  CheckCircle, 
  X, 
  Package,
  Gauge,
  Users,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Info,
  Settings,
  Clock,
  Weight,
  Layers,
  TrendingUp,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import Link from 'next/link'

// Import del canvas di nesting
import NestingCanvas from '../result/[batch_id]/NestingCanvas'

// =============== INTERFACES ===============

interface NestingParameters {
  padding_mm: number
  min_distance_mm: number
}

interface NestingPreviewData {
  layout: Array<{
    odl_id: number
    x: number
    y: number
    width: number
    height: number
    weight: number
    rotated: boolean
    lines_used: number
  }>
  metrics: {
    area_pct: number
    vacuum_util_pct?: number
    lines_used: number
    total_weight: number
    positioned_count: number
    excluded_count: number
    efficiency: number
    time_solver_ms?: number
    fallback_used?: boolean
    algorithm_status?: string
  }
  excluded_odls: Array<{
    odl_id: number
    motivo: string
    dettagli: string
  }>
  success: boolean
  algorithm_status: string
  message?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore: string
  max_load_kg: number
  num_linee_vuoto: number
}

interface ODLInfo {
  id: number
  parte: {
    part_number: string
    descrizione_breve: string
  }
  tool: {
    part_number_tool: string
    larghezza_piano: number
    lunghezza_piano: number
    peso: number
  }
  priorita: number
}

// =============== UTILITY FUNCTIONS ===============

/**
 * Calcola l'efficienza complessiva secondo la formula: 0.7·area_pct + 0.3·vacuum_util_pct
 */
function calculateEfficiencyScore(area_pct: number, vacuum_util_pct: number): number {
  return (0.7 * area_pct) + (0.3 * vacuum_util_pct)
}

/**
 * Determina il livello di efficienza (green/yellow/red)
 */
function getEfficiencyLevel(efficiency: number): string {
  if (efficiency >= 80) return "green"
  if (efficiency >= 60) return "yellow"
  return "red"
}

/**
 * Ritorna la classe CSS per colorare il badge
 */
function getEfficiencyColorClass(efficiency: number): string {
  const level = getEfficiencyLevel(efficiency)
  if (level === "green") return "bg-green-500"
  if (level === "yellow") return "bg-amber-500"
  return "bg-red-500"
}

/**
 * Mostra popup di warning per efficienza bassa
 */
function showEfficiencyWarning(efficiency: number, onRegenerate: () => void, onContinue: () => void, toastFn: (props: any) => void) {
  const level = getEfficiencyLevel(efficiency)
  
  if (level === "red") {
    // Badge rosso: warning con toastr ma l'utente può continuare
    toastFn({
      title: `⚠️ Efficienza Bassa: ${efficiency.toFixed(1)}%`,
      description: "Il batch ha un'efficienza sotto il 60%. Considera di rigenerare il layout o proseguire comunque.",
      variant: "destructive",
    })
  } else if (level === "yellow") {
    // Badge giallo: popup con scelta di rigenerare o continuare
    if (confirm(`🟡 Efficienza Media: ${efficiency.toFixed(1)}%\n\nVuoi migliorare il layout rigenerando il nesting?\n\n• Clicca OK per rigenerare\n• Clicca Annulla per proseguire`)) {
      onRegenerate()
    } else {
      onContinue()
    }
  }
  // Badge verde: nessun warning necessario
}

// =============== MAIN COMPONENT ===============

export default function NestingPreviewPage() {
  const router = useRouter()
  const { toast } = useToast()

  // =============== STATES ===============
  
  // Parametri configurabili
  const [parameters, setParameters] = useState<NestingParameters>({
    padding_mm: 20,
    min_distance_mm: 15
  })

  // Selezioni utente
  const [selectedOdlIds, setSelectedOdlIds] = useState<number[]>([])
  const [selectedAutoclaveId, setSelectedAutoclaveId] = useState<number | null>(null)

  // Dati caricati
  const [availableOdls, setAvailableOdls] = useState<ODLInfo[]>([])
  const [availableAutoclaves, setAvailableAutoclaves] = useState<AutoclaveInfo[]>([])
  
  // Stato preview
  const [previewData, setPreviewData] = useState<NestingPreviewData | null>(null)
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false)
  const [isConfirmingBatch, setIsConfirmingBatch] = useState(false)
  const [lastError, setLastError] = useState<string | null>(null)
  
  // ✅ NUOVO: Stato per aggiornamento automatico
  const [isAutoUpdating, setIsAutoUpdating] = useState(false)
  
  // ✅ NUOVO: Controllo per abilitare/disabilitare auto-update
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(true)
  
  // Loading states
  const [isLoadingInitialData, setIsLoadingInitialData] = useState(true)

  // =============== EFFECTS ===============

  useEffect(() => {
    loadInitialData()
  }, [])

  // ✅ MIGLIORATO: Aggiornamento automatico meno aggressivo
  useEffect(() => {
    // Non generare preview se disabilitato dall'utente
    if (!autoUpdateEnabled) {
      return
    }

    // Non generare preview se non abbiamo dati iniziali o se è in corso un'altra generazione
    if (isLoadingInitialData || isGeneratingPreview) {
      return
    }
    
    // Non generare preview se non abbiamo selezioni valide
    if (!selectedAutoclaveId || selectedOdlIds.length === 0) {
      setPreviewData(null) // Reset preview solo se selezioni non valide
      return
    }

    // Mostra indicatore di aggiornamento automatico
    setIsAutoUpdating(true)

    // ✅ DEBOUNCE AUMENTATO: 2.5 secondi per ridurre aggressività
    const timeoutId = setTimeout(() => {
      console.log('🔄 Auto-aggiornamento preview per cambio parametri/selezioni')
      handleGeneratePreview(true) // true = aggiornamento automatico
    }, 2500) // Aumentato da 1000ms a 2500ms

    // Cleanup del timeout se i parametri cambiano nuovamente prima della scadenza
    return () => {
      clearTimeout(timeoutId)
      setIsAutoUpdating(false)
    }
    
  }, [parameters, selectedOdlIds, selectedAutoclaveId, isLoadingInitialData, isGeneratingPreview, autoUpdateEnabled])

  // =============== DATA LOADING ===============

  const loadInitialData = async () => {
    try {
      setIsLoadingInitialData(true)
      setLastError(null)
      
      console.log('🔄 Inizio caricamento dati preview nesting...')

      // Carica ODL disponibili
      const odlResponse = await fetch('/api/v1/batch_nesting/data')
      if (!odlResponse.ok) {
        throw new Error('Errore nel caricamento degli ODL disponibili')
      }
      const odlData = await odlResponse.json()
      
      setAvailableOdls(odlData.odl_in_attesa_cura || [])
      setAvailableAutoclaves(odlData.autoclavi_disponibili || [])
      
      console.log('✅ Dati caricati:', {
        odl: odlData.odl_in_attesa_cura?.length || 0,
        autoclavi: odlData.autoclavi_disponibili?.length || 0
      })
      
    } catch (error) {
      console.error('❌ Errore caricamento dati:', error)
      const errorMessage = error instanceof Error ? error.message : "Errore nel caricamento dei dati"
      setLastError(errorMessage)
      toast({
        title: "Errore caricamento dati",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsLoadingInitialData(false)
    }
  }

  // =============== PREVIEW GENERATION ===============

  const handleGeneratePreview = async (isAutomatic: boolean = false) => {
    if (!selectedAutoclaveId || selectedOdlIds.length === 0) {
      toast({
        title: "⚠️ Selezione Incompleta",
        description: "Seleziona un'autoclave e almeno un ODL per generare l'anteprima.",
        variant: "destructive",
      })
      return
    }

    try {
      setIsGeneratingPreview(true)
      
      // ✅ MIGLIORAMENTO: Non resetto la preview durante aggiornamenti automatici
      // Questo implementa il pattern "stale-while-revalidate"
      if (!isAutomatic) {
        setPreviewData(null) // Reset solo per aggiornamenti manuali
      }
      
      setLastError(null)
      
      const payload = {
        odl_ids: selectedOdlIds,
        autoclave_id: selectedAutoclaveId,
        padding_mm: parameters.padding_mm,
        min_distance_mm: parameters.min_distance_mm
      }
      
      console.log('🚀 Generazione preview nesting:', payload)
      
      // ✅ FIX: Usa URL relativo per sfruttare il proxy Next.js
      const response = await fetch('/api/v1/batch_nesting/solve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella generazione del nesting')
      }
      
      const result = await response.json()
      
      // Trasforma i dati per compatibilità con l'interfaccia esistente
      const transformedData: NestingPreviewData = {
        layout: result.positioned_tools?.map((tool: any) => ({
          odl_id: tool.odl_id,
          x: tool.x,
          y: tool.y,
          width: tool.width,
          height: tool.height,
          weight: tool.weight_kg,
          rotated: tool.rotated,
          lines_used: 1 // Default se non specificato
        })) || [],
        metrics: {
          area_pct: result.metrics?.area_utilization_pct || 0,
          vacuum_util_pct: result.metrics?.vacuum_util_pct || 0,
          lines_used: result.metrics?.vacuum_lines_used || 0,
          total_weight: result.metrics?.total_weight_kg || 0,
          positioned_count: result.metrics?.pieces_positioned || 0,
          excluded_count: result.metrics?.pieces_excluded || 0,
          efficiency: result.metrics?.efficiency_score || 0,
          time_solver_ms: result.metrics?.time_solver_ms || 0,
          fallback_used: result.metrics?.fallback_used || false,
          algorithm_status: result.metrics?.algorithm_status || 'UNKNOWN'
        },
        excluded_odls: result.excluded_odls || [],
        success: result.success || false,
        algorithm_status: result.metrics?.algorithm_status || 'UNKNOWN',
        message: result.message
      }
      
      setPreviewData(transformedData)
      
      // ✅ Mostra toast solo per aggiornamenti manuali
      if (!isAutomatic) {
        toast({
          title: "✅ Anteprima Generata",
          description: `ODL posizionati: ${transformedData.metrics.positioned_count}, Efficienza: ${transformedData.metrics.efficiency.toFixed(1)}%`,
          variant: "default",
        })
      }
      
      // ✅ Mostra warning/popup per efficienza se necessario (solo per aggiornamenti manuali)
      if (!isAutomatic) {
        showEfficiencyWarning(
          transformedData.metrics.efficiency, 
          () => handleGeneratePreview(true), // Rigenera se utente sceglie di migliorare
          () => {}, // Non fa nulla se utente vuole continuare
          toast
        )
      }
      
    } catch (error) {
      console.error('❌ Errore generazione preview:', error)
      const errorMessage = error instanceof Error ? error.message : "Errore nella generazione dell'anteprima"
      setLastError(errorMessage)
      
      // ✅ Mostra toast errore solo per aggiornamenti manuali
      if (!isAutomatic) {
        toast({
          title: "❌ Errore Generazione Preview",
          description: errorMessage,
          variant: "destructive",
        })
      }
    } finally {
      setIsGeneratingPreview(false)
      setIsAutoUpdating(false) // ✅ Reset stato auto-aggiornamento
    }
  }

  // ✅ NUOVO: Wrapper per click manuali del pulsante
  const handleManualGeneratePreview = () => {
    handleGeneratePreview(false)
  }

  // =============== BATCH CONFIRMATION ===============

  const handleConfirmBatch = async () => {
    if (!previewData || !selectedAutoclaveId) {
      toast({
        title: "⚠️ Anteprima Mancante",
        description: "Nessuna anteprima disponibile per la conferma",
        variant: "destructive",
      })
      return
    }

    try {
      setIsConfirmingBatch(true)
      setLastError(null)
      
      // Crea batch definitivo usando l'endpoint di generazione
      const payload = {
        odl_ids: selectedOdlIds.map(id => id.toString()),
        autoclave_ids: [selectedAutoclaveId.toString()],
        parametri: {
          padding_mm: parameters.padding_mm,
          min_distance_mm: parameters.min_distance_mm
        },
        nome: `Batch Nesting ${new Date().toLocaleDateString('it-IT')}`
      }
      
      // ✅ FIX: Usa URL relativo per sfruttare il proxy Next.js
      const response = await fetch('/api/v1/batch_nesting/genera', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella creazione del batch')
      }
      
      const result = await response.json()
      
      toast({
        title: "✅ Batch Creato",
        description: `Batch ${result.batch_id} creato con successo`,
        variant: "default",
      })
      
      // Redirect alla pagina del batch creato
      router.push(`/dashboard/curing/nesting/result/${result.batch_id}`)
      
    } catch (error) {
      console.error('❌ Errore conferma batch:', error)
      const errorMessage = error instanceof Error ? error.message : "Errore nella conferma del batch"
      setLastError(errorMessage)
      toast({
        title: "❌ Errore Conferma Batch",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsConfirmingBatch(false)
    }
  }

  // =============== UTILITY FUNCTIONS ===============

  const handleReset = () => {
    setPreviewData(null)
    setLastError(null)
    setParameters({
      padding_mm: 20,
      min_distance_mm: 15
    })
  }

  const getSelectedAutoclave = () => {
    return availableAutoclaves.find(a => a.id === selectedAutoclaveId)
  }

  // =============== LOADING STATE ===============

  if (isLoadingInitialData) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin mr-3 text-blue-600" />
          <span className="text-lg">Caricamento dati nesting...</span>
        </div>
      </div>
    )
  }

  // =============== ERROR STATE ===============

  if (lastError && !previewData && availableOdls.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive" className="max-w-2xl mx-auto">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Errore di Caricamento</AlertTitle>
          <AlertDescription className="mt-2">
            {lastError}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadInitialData}
              className="mt-3"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Riprova
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // =============== RENDER ===============

  return (
    <div className="container mx-auto p-6 space-y-6">
      
      {/* =============== HEADER =============== */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/dashboard/curing/nesting">
            <Button variant="ghost" className="mr-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Torna al Nesting
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Preview Nesting</h1>
            <p className="text-muted-foreground">
              Configura i parametri e genera un'anteprima del layout ottimizzato
            </p>
          </div>
        </div>
      </div>

      {/* =============== ERROR ALERT =============== */}
      {lastError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Errore Rilevato</AlertTitle>
          <AlertDescription>
            {lastError}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setLastError(null)}
              className="mt-2 mr-2"
            >
              Chiudi
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleManualGeneratePreview}
              className="mt-2"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Riprova
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* =============== MAIN LAYOUT =============== */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* =============== PANNELLO PARAMETRI (COLONNA SINISTRA) =============== */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Selezione Autoclave */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Autoclave
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select 
                value={selectedAutoclaveId?.toString() || ''} 
                onValueChange={(value) => setSelectedAutoclaveId(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona autoclave" />
                </SelectTrigger>
                <SelectContent>
                  {availableAutoclaves.map(autoclave => (
                    <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                      <div className="flex flex-col">
                        <span className="font-medium">{autoclave.nome}</span>
                        <span className="text-xs text-muted-foreground">({autoclave.codice})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {getSelectedAutoclave() && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-1">
                      <Layers className="h-3 w-3 text-blue-600" />
                      <span className="text-muted-foreground">Dimensioni:</span>
                    </div>
                    <span className="font-medium">{getSelectedAutoclave()?.lunghezza} × {getSelectedAutoclave()?.larghezza_piano} mm</span>
                    
                    <div className="flex items-center gap-1">
                      <Weight className="h-3 w-3 text-blue-600" />
                      <span className="text-muted-foreground">Max peso:</span>
                    </div>
                    <span className="font-medium">{getSelectedAutoclave()?.max_load_kg} kg</span>
                    
                    <div className="flex items-center gap-1">
                      <Info className="h-3 w-3 text-blue-600" />
                      <span className="text-muted-foreground">Linee vuoto:</span>
                    </div>
                    <span className="font-medium">{getSelectedAutoclave()?.num_linee_vuoto}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Selezione ODL */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                ODL Disponibili
                <Badge variant="secondary">{availableOdls.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {availableOdls.map(odl => (
                  <div 
                    key={odl.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedOdlIds.includes(odl.id) 
                        ? 'bg-blue-50 border-blue-300 shadow-sm' 
                        : 'hover:bg-gray-50 hover:border-gray-300'
                    }`}
                    onClick={() => {
                      if (selectedOdlIds.includes(odl.id)) {
                        setSelectedOdlIds(prev => prev.filter(id => id !== odl.id))
                      } else {
                        setSelectedOdlIds(prev => [...prev, odl.id])
                      }
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm">ODL {odl.id}</div>
                        <div className="text-xs text-muted-foreground">{odl.parte.part_number}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {odl.tool.larghezza_piano}×{odl.tool.lunghezza_piano}mm
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{odl.tool.peso}kg</div>
                        <div className="text-xs text-muted-foreground">Priorità {odl.priorita}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <Separator className="my-3" />
              
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Selezionati: {selectedOdlIds.length}</span>
                <div className="space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedOdlIds(availableOdls.map(o => o.id))}
                  >
                    Tutti
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedOdlIds([])}
                  >
                    Nessuno
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Parametri Algoritmo */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Parametri Algoritmo
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Padding */}
              <div>
                <Label htmlFor="padding" className="text-sm font-medium">
                  Padding tra tool: {parameters.padding_mm}mm
                </Label>
                <div className="mt-2">
                  <Slider
                    value={parameters.padding_mm}
                    onValueChange={(value: number) => setParameters(prev => ({ ...prev, padding_mm: value }))}
                    max={50}
                    min={5}
                    step={5}
                    className="w-full"
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>5mm</span>
                  <span>50mm</span>
                </div>
              </div>

              {/* Min Distance */}
              <div>
                <Label htmlFor="distance" className="text-sm font-medium">
                  Distanza dai bordi: {parameters.min_distance_mm}mm
                </Label>
                <div className="mt-2">
                  <Slider
                    value={parameters.min_distance_mm}
                    onValueChange={(value: number) => setParameters(prev => ({ ...prev, min_distance_mm: value }))}
                    max={30}
                    min={5}
                    step={5}
                    className="w-full"
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>5mm</span>
                  <span>30mm</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bottone Genera Anteprima */}
          <div className="space-y-3">
            {/* ✅ NUOVO: Toggle Auto-Update */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
              <div className="flex flex-col">
                <span className="text-sm font-medium">Aggiornamento Automatico</span>
                <span className="text-xs text-muted-foreground">
                  Rigenera automaticamente quando modifichi i parametri
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoUpdateEnabled}
                  onChange={(e) => setAutoUpdateEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* ✅ MIGLIORATO: Indicatore aggiornamento meno invasivo */}
            {isAutoUpdating && autoUpdateEnabled && (
              <div className="flex items-center gap-2 p-2 bg-blue-50 border-l-4 border-blue-400 rounded-r-lg">
                <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
                <span className="text-xs text-blue-700">Aggiornamento in corso...</span>
              </div>
            )}
            
            <Button 
              onClick={handleManualGeneratePreview}
              disabled={isGeneratingPreview || selectedOdlIds.length === 0 || !selectedAutoclaveId}
              className="w-full"
              size="lg"
              variant={isAutoUpdating && autoUpdateEnabled ? "outline" : "default"}
            >
              {isGeneratingPreview ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generazione in corso...
                </>
              ) : isAutoUpdating && autoUpdateEnabled ? (
                <>
                  <Clock className="h-4 w-4 mr-2" />
                  Auto-Update Attivo
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  {autoUpdateEnabled ? "Aggiorna Ora" : "Genera Anteprima"}
                </>
              )}
            </Button>
          </div>

        </div>

        {/* =============== PANNELLO PRINCIPALE (COLONNA DESTRA) =============== */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Canvas di Preview */}
          {previewData ? (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Layout Nesting
                  <Badge variant={previewData.success ? "default" : "destructive"}>
                    {previewData.algorithm_status}
                  </Badge>
                  {previewData.metrics.fallback_used && (
                    <Badge variant="outline" className="text-orange-600 border-orange-300">
                      Fallback
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Anteprima del layout generato con algoritmo {previewData.algorithm_status}
                  {previewData.metrics.time_solver_ms && (
                    <span className="ml-2 text-xs">
                      • Tempo: {previewData.metrics.time_solver_ms.toFixed(0)}ms
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {getSelectedAutoclave() && (
                  <div className="border rounded-lg overflow-hidden">
                    <NestingCanvas
                      batchData={{
                        configurazione_json: {
                          canvas_width: 800,
                          canvas_height: 600,
                          tool_positions: previewData.layout.map(item => ({
                            odl_id: item.odl_id,
                            x: item.x,
                            y: item.y,
                            width: item.width,
                            height: item.height,
                            peso: item.weight,
                            rotated: item.rotated,
                            part_number: `ODL-${item.odl_id}`,
                            tool_nome: `Tool ${item.odl_id}`
                          }))
                        },
                        autoclave: getSelectedAutoclave()
                      }}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-16">
                <div className="text-center text-muted-foreground">
                  <Package className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">Anteprima Non Disponibile</h3>
                  {autoUpdateEnabled ? (
                    <>
                      <p className="mb-2">Seleziona un'autoclave e degli ODL per visualizzare automaticamente il layout</p>
                      <p className="text-sm">L'anteprima si aggiorna automaticamente quando modifichi i parametri</p>
                    </>
                  ) : (
                    <>
                      <p className="mb-2">Seleziona un'autoclave e degli ODL, poi clicca "Genera Anteprima"</p>
                      <p className="text-sm">Aggiornamento automatico disabilitato - usa il pulsante per generare manualmente</p>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* KPI Metriche */}
          {previewData && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <Card className="border-l-4 border-l-blue-500">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Gauge className="h-5 w-5 text-blue-600" />
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Area Occupata</div>
                      <div className="text-2xl font-bold text-blue-600">{previewData.metrics.area_pct.toFixed(1)}%</div>
                      <Progress value={previewData.metrics.area_pct} className="mt-2 h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-green-500">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Info className="h-5 w-5 text-green-600" />
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Linee Vuoto</div>
                      <div className="text-2xl font-bold text-green-600">
                        {previewData.metrics.lines_used}
                      </div>
                      {previewData.metrics.vacuum_util_pct && (
                        <Progress value={previewData.metrics.vacuum_util_pct} className="mt-2 h-2" />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-purple-500">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-600" />
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Efficienza</div>
                      <div className="flex items-center gap-2">
                        <div className="text-2xl font-bold text-purple-600">{previewData.metrics.efficiency.toFixed(1)}%</div>
                        <Badge 
                          className={`text-white font-semibold ${getEfficiencyColorClass(previewData.metrics.efficiency)}`}
                        >
                          {getEfficiencyLevel(previewData.metrics.efficiency).toUpperCase()}
                        </Badge>
                      </div>
                      <Progress value={previewData.metrics.efficiency} className="mt-2 h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-indigo-500">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-indigo-600" />
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">ODL Inclusi</div>
                      <div className="text-2xl font-bold text-indigo-600">{previewData.metrics.positioned_count}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        su {previewData.metrics.positioned_count + previewData.metrics.excluded_count} totali
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-orange-500">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Weight className="h-5 w-5 text-orange-600" />
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Peso Totale</div>
                      <div className="text-2xl font-bold text-orange-600">{previewData.metrics.total_weight.toFixed(1)}kg</div>
                      {getSelectedAutoclave() && (
                        <Progress 
                          value={(previewData.metrics.total_weight / getSelectedAutoclave()!.max_load_kg) * 100} 
                          className="mt-2 h-2" 
                        />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Informazioni Algoritmo */}
          {previewData && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  Informazioni Algoritmo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Algoritmo:</span>
                    <div className="font-medium">{previewData.algorithm_status}</div>
                  </div>
                  {previewData.metrics.time_solver_ms && (
                    <div>
                      <span className="text-muted-foreground">Tempo risoluzione:</span>
                      <div className="font-medium">{previewData.metrics.time_solver_ms.toFixed(0)}ms</div>
                    </div>
                  )}
                  <div>
                    <span className="text-muted-foreground">Fallback utilizzato:</span>
                    <div className="font-medium">
                      {previewData.metrics.fallback_used ? (
                        <Badge variant="outline" className="text-orange-600">Sì</Badge>
                      ) : (
                        <Badge variant="outline" className="text-green-600">No</Badge>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Successo:</span>
                    <div className="font-medium">
                      {previewData.success ? (
                        <Badge variant="outline" className="text-green-600">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Sì
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-red-600">
                          <AlertTriangle className="h-3 w-3 mr-1" />
                          No
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ODL Esclusi */}
          {previewData && previewData.excluded_odls.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  ODL Esclusi
                  <Badge variant="outline">{previewData.excluded_odls.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {previewData.excluded_odls.map((excluded, index) => (
                    <div key={index} className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        <div className="flex-1">
                          <div className="font-medium text-sm">ODL {excluded.odl_id}</div>
                          <div className="text-sm text-yellow-800 mt-1">{excluded.motivo}</div>
                          <div className="text-xs text-yellow-700 mt-2">{excluded.dettagli}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pulsanti di Azione */}
          {previewData && (
            <div className="flex items-center justify-end gap-4">
              <Button 
                variant="outline" 
                onClick={handleReset}
                className="min-w-[120px]"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Rigenera
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => router.push('/dashboard/curing/nesting')}
                className="min-w-[120px]"
              >
                <X className="h-4 w-4 mr-2" />
                Annulla
              </Button>
              
              <Button 
                onClick={handleConfirmBatch}
                disabled={isConfirmingBatch || !previewData.success}
                className="min-w-[140px]"
                size="lg"
              >
                {isConfirmingBatch ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Conferma...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Conferma Batch
                  </>
                )}
              </Button>
            </div>
          )}

        </div>
      </div>
    </div>
  )
} 