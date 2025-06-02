'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { Package, AlertCircle, Loader2, Info, CheckCircle, TrendingUp, TrendingDown } from 'lucide-react'
import dynamic from 'next/dynamic'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/components/ui/use-toast'

// ✅ CORREZIONE: Definisco i componenti helper prima degli import dinamici
// Componente di caricamento
const CanvasLoader: React.FC = () => (
  <div className="flex items-center justify-center bg-muted/30 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-2">
      <Loader2 className="h-12 w-12 text-blue-500 mx-auto animate-spin" />
      <p className="text-muted-foreground">Caricamento canvas...</p>
      <p className="text-xs text-muted-foreground">Inizializzazione react-konva</p>
    </div>
  </div>
)

// ✅ CORREZIONE: Interfaccia corretta per i tool dal backend
interface ToolPosition {
  odl_id: number
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean | string  // ✅ Gestisce sia boolean che string
  part_number?: string
  tool_nome?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}

// 🎯 NUOVO v1.4.16-DEMO: Interfaccia per motivi di esclusione
interface ExclusionReason {
  odl_id: number
  motivo: string
  dettagli?: string
  debug_reasons?: string[]
  motivi_dettagliati?: string
}

// 🎯 NUOVO v1.4.16-DEMO: Interfaccia per metriche estese
interface ExtendedMetrics {
  efficiency: number
  area_utilization: number
  weight_utilization: number
  vacuum_utilization: number
  tools_positioned: number
  tools_excluded: number
  total_weight: number
  total_area: number
}

interface NestingCanvasProps {
  batchData: {
    configurazione_json: {
      canvas_width: number
      canvas_height: number
      tool_positions: ToolPosition[]
    } | null
    autoclave: AutoclaveInfo | undefined
    // 🎯 NUOVO v1.4.16-DEMO: Dati per motivi di esclusione
    odl_esclusi?: ExclusionReason[]
    excluded_reasons?: Record<string, number>
    metrics?: any
  }
  className?: string
}

// ✅ FUNZIONE DI NORMALIZZAZIONE DATI
const normalizeToolData = (tool: ToolPosition): ToolPosition => {
  return {
    ...tool,
    x: Number(tool.x) || 0,
    y: Number(tool.y) || 0,
    width: Number(tool.width) || 50,
    height: Number(tool.height) || 50,
    peso: Number(tool.peso) || 0,
    rotated: Boolean(tool.rotated === true || tool.rotated === 'true')
  }
}

// 🎯 NUOVO v1.4.16-DEMO: Badge di efficienza colorato con tooltip
const EfficiencyBadge: React.FC<{ 
  metrics: ExtendedMetrics
  onLowEfficiency?: () => void 
}> = ({ metrics, onLowEfficiency }) => {
  const { efficiency } = metrics
  
  // Determina colore e icona in base all'efficienza
  const getBadgeVariant = (eff: number) => {
    if (eff >= 80) return { color: 'bg-green-500 hover:bg-green-600 text-white', icon: TrendingUp, label: 'Eccellente' }
    if (eff >= 60) return { color: 'bg-amber-500 hover:bg-amber-600 text-white', icon: TrendingUp, label: 'Buona' }
    return { color: 'bg-red-500 hover:bg-red-600 text-white', icon: TrendingDown, label: 'Sotto soglia' }
  }
  
  const badgeStyle = getBadgeVariant(efficiency)
  const IconComponent = badgeStyle.icon
  
  // Effetto per notifica di efficienza bassa
  useEffect(() => {
    if (efficiency < 60 && onLowEfficiency) {
      onLowEfficiency()
    }
  }, [efficiency, onLowEfficiency])
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className={`${badgeStyle.color} cursor-help transition-colors`}>
            <IconComponent className="h-3 w-3 mr-1" />
            Efficienza: {efficiency.toFixed(1)}% ({badgeStyle.label})
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-2">
            <p className="font-semibold">Metriche Dettagliate</p>
            <div className="text-sm space-y-1">
              <div>🎯 <strong>Efficienza Globale:</strong> {efficiency.toFixed(1)}%</div>
              <div>📐 <strong>Utilizzo Area:</strong> {metrics.area_utilization.toFixed(1)}%</div>
              <div>⚖️ <strong>Utilizzo Peso:</strong> {metrics.weight_utilization.toFixed(1)}%</div>
              <div>🔌 <strong>Utilizzo Valvole:</strong> {metrics.vacuum_utilization.toFixed(1)}%</div>
              <div>📦 <strong>Tool Posizionati:</strong> {metrics.tools_positioned}</div>
              <div>❌ <strong>Tool Esclusi:</strong> {metrics.tools_excluded}</div>
              <div>⚖️ <strong>Peso Totale:</strong> {metrics.total_weight.toFixed(1)}kg</div>
              <div>📏 <strong>Area Totale:</strong> {(metrics.total_area / 10000).toFixed(2)}m²</div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// 🎯 NUOVO v1.4.16-DEMO: Tabella collassabile per motivi di esclusione
const ExclusionReasonsTable: React.FC<{ 
  exclusions: ExclusionReason[]
  excludedReasons: Record<string, number>
}> = ({ exclusions, excludedReasons }) => {
  if (!exclusions || exclusions.length === 0) {
    return null
  }
  
  // Mappatura motivi human-readable
  const reasonLabels: Record<string, string> = {
    'oversize': 'Dimensioni eccessive',
    'weight_exceeded': 'Peso eccessivo', 
    'vacuum_lines': 'Linee vuoto insufficienti',
    'padding': 'Padding insufficiente',
    'placement_failed': 'Posizionamento fallito',
    'incompatible_cycle': 'Ciclo di cura incompatibile',
    'unknown': 'Motivo sconosciuto'
  }
  
  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardHeader className="pb-3">
        <Accordion type="single" collapsible>
          <AccordionItem value="exclusions">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                <span>Motivi Esclusione ({exclusions.length} ODL)</span>
              </div>
            </AccordionTrigger>
            
            <AccordionContent className="space-y-4">
              {/* Riassunto motivi */}
              {Object.keys(excludedReasons).length > 0 && (
                <div className="bg-white rounded-lg p-3 border">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Riassunto per Categoria:</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(excludedReasons).map(([reason, count]) => (
                      <Badge key={reason} variant="outline" className="text-xs">
                        {reasonLabels[reason] || reason}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Lista dettagliata */}
              <div className="bg-white rounded-lg border overflow-hidden">
                <div className="max-h-60 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left p-3 font-medium text-gray-900">ODL ID</th>
                        <th className="text-left p-3 font-medium text-gray-900">Motivo</th>
                        <th className="text-left p-3 font-medium text-gray-900">Dettagli</th>
                      </tr>
                    </thead>
                    <tbody>
                      {exclusions.map((exclusion, index) => (
                        <tr key={exclusion.odl_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="p-3 font-medium text-blue-600">
                            #{exclusion.odl_id}
                          </td>
                          <td className="p-3">
                            <Badge variant="outline" className="text-xs">
                              {reasonLabels[exclusion.motivo] || exclusion.motivo}
                            </Badge>
                          </td>
                          <td className="p-3 text-gray-600 text-xs">
                            {exclusion.dettagli || exclusion.motivi_dettagliati || 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardHeader>
    </Card>
  )
}

// 🎯 NUOVO v1.4.16-DEMO: Componente principale NestingCanvasPanel
const NestingCanvasPanel: React.FC<{
  toolPositions: ToolPosition[]
  autoclave: AutoclaveInfo
  canvasSize: { width: number; height: number }
  scale: number
  exclusions: ExclusionReason[]
  excludedReasons: Record<string, number>
}> = ({ toolPositions, autoclave, canvasSize, scale, exclusions, excludedReasons }) => {
  const { toast } = useToast()
  
  // Normalizza tutti i tool
  const normalizedTools = toolPositions.map(normalizeToolData)
  
  // Calcola metriche estese
  const totalTools = normalizedTools.length
  const totalWeight = normalizedTools.reduce((sum, tool) => sum + tool.peso, 0)
  const totalArea = normalizedTools.reduce((sum, tool) => sum + (tool.width * tool.height), 0)
  const autoclaveArea = autoclave.larghezza_piano * autoclave.lunghezza
  const areaUtilization = (totalArea / autoclaveArea) * 100
  
  // Stima utilizzo valvole (assumendo 1 valvola per tool come base)
  const estimatedVacuumLines = totalTools
  const maxVacuumLines = 12 // Valore di default, potrebbe venire dall'autoclave
  const vacuumUtilization = (estimatedVacuumLines / maxVacuumLines) * 100
  
  // Stima peso massimo autoclave
  const maxWeight = 1000 // kg, valore di default
  const weightUtilization = (totalWeight / maxWeight) * 100
  
  // Calcola efficienza globale (media pesata)
  const efficiency = (areaUtilization * 0.6) + (weightUtilization * 0.2) + (vacuumUtilization * 0.2)
  
  const metrics: ExtendedMetrics = {
    efficiency: Math.min(efficiency, 100),
    area_utilization: areaUtilization,
    weight_utilization: weightUtilization,
    vacuum_utilization: vacuumUtilization,
    tools_positioned: totalTools,
    tools_excluded: exclusions.length,
    total_weight: totalWeight,
    total_area: totalArea
  }
  
  // 🎯 NUOVO v1.4.16-DEMO: Gestione toast per efficienza bassa
  const handleLowEfficiency = useCallback(() => {
    toast({
      title: "⚠️ Layout sotto soglia",
      description: `L'efficienza del layout (${metrics.efficiency.toFixed(1)}%) è inferiore al 60%. Considera di ottimizzare la configurazione.`,
      variant: "destructive",
      duration: 5000,
    })
  }, [metrics.efficiency, toast])
  
  return (
    <div className="space-y-6">
      {/* Header con Badge Efficienza */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-600" />
            Layout Nesting Interattivo
          </h3>
          <p className="text-sm text-muted-foreground">
            Autoclave: {autoclave.nome} • Dimensioni: {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
          </p>
        </div>
        
        {/* 🎯 NUOVO: Badge Efficienza con tooltip metriche */}
        <EfficiencyBadge metrics={metrics} onLowEfficiency={handleLowEfficiency} />
      </div>
      
      {/* Canvas principale */}
      <Card>
        <CardContent className="p-6">
          <div 
            className="relative mx-auto border-2 border-dashed border-blue-300 bg-blue-50/30 rounded-lg overflow-hidden"
            style={{ 
              width: Math.min(canvasSize.width, 800), 
              height: Math.min(canvasSize.height, 500)
            }}
          >
            {/* Grid di sfondo */}
            <div 
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage: `
                  linear-gradient(to right, #e5e7eb 1px, transparent 1px),
                  linear-gradient(to bottom, #e5e7eb 1px, transparent 1px)
                `,
                backgroundSize: '50px 50px'
              }}
            />
            
            {/* Label autoclave */}
            <div className="absolute top-2 left-2 bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium">
              {autoclave.nome}
            </div>
            
            {/* Tool posizionati */}
            {normalizedTools.map((tool, index) => {
              const scaledX = (tool.x * scale) + 10
              const scaledY = (tool.y * scale) + 10  
              const scaledWidth = (tool.width * scale) * 0.8
              const scaledHeight = (tool.height * scale) * 0.8
              
              return (
                <div
                  key={tool.odl_id}
                  className="absolute bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded shadow-lg border-2 border-blue-400 hover:from-blue-600 hover:to-blue-700 transition-all duration-200 cursor-pointer"
                  style={{
                    left: `${Math.max(10, Math.min(scaledX, canvasSize.width - scaledWidth - 10))}px`,
                    top: `${Math.max(30, Math.min(scaledY, canvasSize.height - scaledHeight - 10))}px`,
                    width: `${Math.max(80, scaledWidth)}px`,
                    height: `${Math.max(60, scaledHeight)}px`,
                    transform: tool.rotated ? 'rotate(90deg)' : 'none'
                  }}
                  title={`ODL ${tool.odl_id}: ${tool.part_number || 'N/A'} • ${tool.peso}kg`}
                >
                  <div className="p-1 h-full flex flex-col justify-center items-center text-center">
                    <div className="text-xs font-bold">ODL {tool.odl_id}</div>
                    <div className="text-xs opacity-90">{tool.peso}kg</div>
                    {tool.rotated && (
                      <div className="text-xs opacity-75">🔄</div>
                    )}
                  </div>
                </div>
              )
            })}
            
            {/* Etichette dimensioni */}
            <div className="absolute bottom-1 right-1 bg-black/75 text-white px-2 py-1 rounded text-xs">
              {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* 🎯 NUOVO: Tabella collassabile motivi esclusione */}
      <ExclusionReasonsTable 
        exclusions={exclusions} 
        excludedReasons={excludedReasons} 
      />
      
      {/* Statistiche dettagliate aggiornate */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
          <div className="text-sm font-medium text-blue-800">Tool Posizionati</div>
          <div className="text-xl font-bold text-blue-900">{totalTools}</div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg border border-green-200">
          <div className="text-sm font-medium text-green-800">Peso Totale</div>
          <div className="text-xl font-bold text-green-900">{totalWeight.toFixed(1)} kg</div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
          <div className="text-sm font-medium text-purple-800">Area Utilizzata</div>
          <div className="text-xl font-bold text-purple-900">{(totalArea / 10000).toFixed(1)} m²</div>
        </div>
        <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
          <div className="text-sm font-medium text-orange-800">Efficienza</div>
          <div className="text-xl font-bold text-orange-900">{metrics.efficiency.toFixed(1)}%</div>
        </div>
      </div>
      
      {/* Lista tool dettagliata */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Dettagli Tool Posizionati</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {normalizedTools.map((tool, index) => (
              <div key={tool.odl_id} className="flex items-center justify-between bg-gray-50 rounded px-3 py-2 text-sm">
                <div>
                  <span className="font-medium">ODL {tool.odl_id}</span>
                  {tool.part_number && <span className="text-gray-600 ml-2">{tool.part_number}</span>}
                </div>
                <div className="text-gray-600">
                  {tool.width}×{tool.height}mm • {tool.peso}kg
                  {tool.rotated && <span className="ml-1">🔄</span>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Footer con informazioni */}
      <div className="flex items-center justify-between text-sm text-gray-600 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 border-2 border-blue-300 border-dashed"></div>
            <span>Bordo autoclave</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            <span>Tool posizionati</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-green-600">
          <CheckCircle className="h-4 w-4" />
          <span>Layout validato</span>
        </div>
      </div>
    </div>
  )
}

// ✅ NUOVO COMPONENTE CANVAS INTERATTIVO MIGLIORATO - Aggiornato per usare NestingCanvasPanel
const InteractiveCanvas: React.FC<{
  toolPositions: ToolPosition[]
  autoclave: AutoclaveInfo
  canvasSize: { width: number; height: number }
  scale: number
  exclusions: ExclusionReason[]
  excludedReasons: Record<string, number>
}> = ({ toolPositions, autoclave, canvasSize, scale, exclusions, excludedReasons }) => {
  
  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <NestingCanvasPanel
        toolPositions={toolPositions}
        autoclave={autoclave}
        canvasSize={canvasSize}
        scale={scale}
        exclusions={exclusions}
        excludedReasons={excludedReasons}
      />
    </div>
  )
}

// Componente di errore migliorato
const CanvasError: React.FC<{ onRetry: () => void; error?: string }> = ({ onRetry, error }) => (
  <div className="flex items-center justify-center bg-red-50 border border-red-200 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-3">
      <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
      <div>
        <p className="text-red-800 font-medium">Errore nel rendering del canvas</p>
        <p className="text-sm text-red-600">{error || 'Si è verificato un problema nella visualizzazione del layout nesting'}</p>
      </div>
      <button 
        onClick={onRetry}
        className="px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors"
      >
        Riprova
      </button>
    </div>
  </div>
)

// Componente dati mancanti
const NoDataCanvas: React.FC<{ message?: string }> = ({ message }) => (
  <div className="flex items-center justify-center bg-muted/30 rounded-lg" style={{ height: '400px' }}>
    <div className="text-center space-y-2">
      <Package className="h-12 w-12 text-muted-foreground mx-auto" />
      <p className="text-muted-foreground">
        {message || 'Nessun ODL configurato'}
      </p>
      <p className="text-sm text-muted-foreground">
        Verifica che il nesting contenga la configurazione_json con i dati degli ODL
      </p>
    </div>
  </div>
)

const NestingCanvas: React.FC<NestingCanvasProps> = ({ batchData, className }) => {
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 })
  const [scale, setScale] = useState(1)
  const [isClient, setIsClient] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [retryCount, setRetryCount] = useState(0)

  // Debug logging migliorato
  useEffect(() => {
    console.log('🔍 NestingCanvas props debug:', {
      hasBatchData: !!batchData,
      hasConfig: !!batchData?.configurazione_json,
      hasToolPositions: !!batchData?.configurazione_json?.tool_positions,
      toolPositionsCount: batchData?.configurazione_json?.tool_positions?.length || 0,
      toolPositionsData: batchData?.configurazione_json?.tool_positions || [],
      hasAutoclave: !!batchData?.autoclave,
      autoclaveData: batchData?.autoclave
    })
  }, [batchData])

  // Inizializzazione client-side
  useEffect(() => {
    setIsClient(true)
    
    // Simula un piccolo delay per assicurarsi che tutti i moduli siano caricati
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  // Calcolo dimensioni e scala del canvas con gestione errori
  useEffect(() => {
    if (!batchData?.configurazione_json || !batchData?.autoclave) return

    const config = batchData.configurazione_json
    const autoclave = batchData.autoclave

    try {
      // Dimensioni dell'autoclave in mm - con controlli di sicurezza
      const autoclaveLength = Number(autoclave.lunghezza) || 2000
      const autoclaveWidth = Number(autoclave.larghezza_piano) || 1200

      console.log('📐 Dimensioni autoclave:', { length: autoclaveLength, width: autoclaveWidth })

      // Calcola scala per far stare tutto nel canvas
      const maxCanvasWidth = 800
      const maxCanvasHeight = 500
      const padding = 50 // 25px per lato

      const scaleX = (maxCanvasWidth - padding) / autoclaveLength
      const scaleY = (maxCanvasHeight - padding) / autoclaveWidth
      const calculatedScale = Math.min(scaleX, scaleY, 0.8) // Scala massima 0.8

      // Dimensioni finali del canvas
      const finalWidth = autoclaveLength * calculatedScale + padding
      const finalHeight = autoclaveWidth * calculatedScale + padding

      setCanvasSize({ 
        width: Math.max(400, finalWidth), 
        height: Math.max(300, finalHeight) 
      })
      setScale(calculatedScale)

      console.log('📐 Canvas dimensions calculated:', {
        autoclave: { length: autoclaveLength, width: autoclaveWidth },
        scale: calculatedScale,
        canvasSize: { width: finalWidth, height: finalHeight }
      })

    } catch (error) {
      console.error('❌ Errore nel calcolo dimensioni canvas:', error)
      setErrorMessage('Errore nel calcolo dimensioni del canvas')
      setHasError(true)
    }
  }, [batchData])

  const handleRetry = useCallback(() => {
    console.log('🔄 Retry canvas render, attempt:', retryCount + 1)
    setHasError(false)
    setErrorMessage('')
    setIsLoading(true)
    setRetryCount(prev => prev + 1)
    
    setTimeout(() => {
      setIsLoading(false)
    }, 500)
  }, [retryCount])

  // ✅ VALIDAZIONE DATI MIGLIORATA
  if (!batchData) {
    return <NoDataCanvas message="Dati batch non disponibili" />
  }

  if (!batchData.configurazione_json) {
    return <NoDataCanvas message="Configurazione nesting non trovata" />
  }

  if (!batchData.configurazione_json.tool_positions || batchData.configurazione_json.tool_positions.length === 0) {
    return <NoDataCanvas message="Nessun tool posizionato nel nesting" />
  }

  if (!batchData.autoclave) {
    return <NoDataCanvas message="Informazioni autoclave non disponibili" />
  }

  // Gestione errori
  if (hasError) {
    return <CanvasError onRetry={handleRetry} error={errorMessage} />
  }

  // Caricamento
  if (!isClient || isLoading) {
    return <CanvasLoader />
  }

  // ✅ RENDERING PRINCIPALE CON CANVAS INTERATTIVO
  try {
    return (
      <div className={className || ''}>
        <InteractiveCanvas
          toolPositions={batchData.configurazione_json.tool_positions}
          autoclave={batchData.autoclave}
          canvasSize={canvasSize}
          scale={scale}
          exclusions={batchData.odl_esclusi || []}
          excludedReasons={batchData.excluded_reasons || {}}
        />
      </div>
    )
  } catch (error) {
    console.error('❌ Errore nel rendering canvas:', error)
    return <CanvasError onRetry={handleRetry} error="Errore nel rendering del canvas" />
  }
}

export default NestingCanvas 