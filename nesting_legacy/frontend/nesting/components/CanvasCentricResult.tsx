'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Grid3X3, 
  Ruler, 
  Info,
  Package,
  Flame,
  Award,
  TrendingUp,
  TrendingDown,
  RotateCcw,
  Download,
  RefreshCw
} from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import dynamic from 'next/dynamic'

// Import dinamico del canvas per SSR
const NestingCanvas = dynamic(() => import('../result/[batch_id]/NestingCanvas'), {
  loading: () => (
    <div className="flex items-center justify-center h-96 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="text-center space-y-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <div>
          <p className="text-sm font-medium text-gray-700">Caricamento Canvas</p>
          <p className="text-xs text-gray-500">Inizializzazione visualizzazione...</p>
        </div>
      </div>
    </div>
  ),
  ssr: false
})

interface ToolPosition {
  odl_id: number
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean | string
  part_number?: string
  tool_nome?: string
  excluded?: boolean
  numero_odl?: string | number
  descrizione_breve?: string
  part_number_tool?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore?: string
}

interface BatchData {
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
  }
  created_at: string
  numero_nesting: number
  peso_totale_kg?: number
  area_totale_utilizzata?: number
  valvole_totali_utilizzate?: number
  metrics?: {
    efficiency_percentage?: number
    total_area_used_mm2?: number
    total_weight_kg?: number
  }
  efficiency?: number
}

interface CanvasCentricResultProps {
  batchData: BatchData
  onBatchChange?: (batchId: string) => void
  availableBatches?: BatchData[]
  className?: string
}

export default function CanvasCentricResult({ 
  batchData, 
  onBatchChange, 
  availableBatches = [],
  className = ""
}: CanvasCentricResultProps) {
  // Stati canvas e controlli
  const [canvasSettings, setCanvasSettings] = useState({
    showGrid: true,
    showRuler: true,
    showTooltips: true,
    showInfo: true
  })
  
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const canvasContainerRef = useRef<HTMLDivElement>(null)

  // Calcoli metriche
  const efficiency = batchData.metrics?.efficiency_percentage || batchData.efficiency || 0
  const totalArea = batchData.metrics?.total_area_used_mm2 || batchData.area_totale_utilizzata || 0
  const totalWeight = batchData.metrics?.total_weight_kg || batchData.peso_totale_kg || 0
  const toolPositions = batchData.configurazione_json?.tool_positions || []
  const autoclaveArea = batchData.autoclave 
    ? batchData.autoclave.lunghezza * batchData.autoclave.larghezza_piano 
    : 0

  // Statistiche calcolate
  const validTools = toolPositions.filter(tool => !tool.excluded)
  const excludedTools = toolPositions.filter(tool => tool.excluded)
  const rotatedTools = validTools.filter(tool => tool.rotated)
  
  const averageToolSize = validTools.length > 0 
    ? validTools.reduce((sum, tool) => sum + (tool.width * tool.height), 0) / validTools.length / 1000000 // m²
    : 0

  // Gestione fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!isFullscreen && canvasContainerRef.current) {
      if (canvasContainerRef.current.requestFullscreen) {
        canvasContainerRef.current.requestFullscreen()
        setIsFullscreen(true)
      }
    } else if (isFullscreen && document.exitFullscreen) {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }, [isFullscreen])

  // Listener per fullscreen change
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  // Handler tool click
  const handleToolClick = useCallback((toolId: number) => {
    setSelectedTool(prev => prev === toolId ? null : toolId)
  }, [])

  // Funzioni utility
  const getEfficiencyColor = (eff: number) => {
    if (eff >= 80) return 'text-green-600 bg-green-50 border-green-200'
    if (eff >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    if (eff >= 40) return 'text-orange-600 bg-orange-50 border-orange-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const formatArea = (area: number) => {
    if (area > 1000000) return `${(area / 1000000).toFixed(2)} m²`
    return `${(area / 1000).toFixed(0)} dm²`
  }

  const formatWeight = (weight: number) => {
    if (weight > 1000) return `${(weight / 1000).toFixed(2)} t`
    return `${weight.toFixed(1)} kg`
  }

  // Componente tool selezionato
  const selectedToolData = selectedTool 
    ? toolPositions.find(tool => tool.odl_id === selectedTool)
    : null

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header con switch batch */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Package className="h-6 w-6" />
            Risultati Nesting
            {efficiency >= 80 && <Award className="h-5 w-5 text-yellow-500" />}
          </h1>
          <p className="text-muted-foreground flex items-center gap-2">
            <Flame className="h-4 w-4" />
            {batchData.autoclave?.nome} ({batchData.autoclave?.codice})
            <span className="mx-2">•</span>
            <span>{validTools.length} tool posizionati</span>
            {excludedTools.length > 0 && (
              <>
                <span className="mx-2">•</span>
                <span className="text-destructive">{excludedTools.length} esclusi</span>
              </>
            )}
          </p>
        </div>

        {/* Switch batch rapido */}
        {availableBatches.length > 1 && (
          <div className="flex items-center gap-2">
            <Label className="text-sm">Batch:</Label>
            <Tabs value={batchData.id} onValueChange={onBatchChange} className="w-auto">
              <TabsList className="grid grid-cols-2 lg:grid-cols-3">
                {availableBatches.slice(0, 3).map((batch) => (
                  <TabsTrigger key={batch.id} value={batch.id} className="text-xs">
                    <div className="flex items-center gap-1">
                      <span>{batch.autoclave?.codice || 'N/A'}</span>
                      <Badge variant="outline" className="text-xs">
                        {batch.metrics?.efficiency_percentage?.toFixed(0) || '0'}%
                      </Badge>
                    </div>
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </div>
        )}
      </div>

      {/* Layout principale canvas-centrico */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Canvas principale - 3/5 dello spazio */}
        <div className="lg:col-span-3 space-y-4">
          {/* Controlli canvas */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Canvas Nesting</CardTitle>
                <div className="flex items-center gap-2">
                  {/* Controlli visualizzazione */}
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={canvasSettings.showGrid}
                        onCheckedChange={(checked) => setCanvasSettings(prev => ({ ...prev, showGrid: checked }))}
                        id="grid-toggle"
                      />
                      <Label htmlFor="grid-toggle" className="text-sm flex items-center gap-1">
                        <Grid3X3 className="h-3 w-3" />
                        Griglia
                      </Label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={canvasSettings.showRuler}
                        onCheckedChange={(checked) => setCanvasSettings(prev => ({ ...prev, showRuler: checked }))}
                        id="ruler-toggle"
                      />
                      <Label htmlFor="ruler-toggle" className="text-sm flex items-center gap-1">
                        <Ruler className="h-3 w-3" />
                        Righello
                      </Label>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={canvasSettings.showInfo}
                        onCheckedChange={(checked) => setCanvasSettings(prev => ({ ...prev, showInfo: checked }))}
                        id="info-toggle"
                      />
                      <Label htmlFor="info-toggle" className="text-sm flex items-center gap-1">
                        <Info className="h-3 w-3" />
                        Info
                      </Label>
                    </div>
                  </div>

                  <Separator orientation="vertical" className="h-6" />

                  {/* Controlli zoom */}
                  <div className="flex items-center gap-1">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm">
                            <ZoomIn className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Zoom In</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm">
                            <ZoomOut className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Zoom Out</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm">
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Reset Zoom</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm" onClick={toggleFullscreen}>
                            <Maximize2 className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Fullscreen</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="p-0">
              <div 
                ref={canvasContainerRef}
                className={`transition-all duration-300 ${isFullscreen ? 'h-screen' : 'h-[600px]'}`}
              >
                <NestingCanvas
                  batchData={{
                    configurazione_json: batchData.configurazione_json,
                    autoclave: batchData.autoclave,
                    metrics: batchData.metrics,
                    id: batchData.id
                  }}
                  className="w-full h-full"
                />
              </div>
            </CardContent>
          </Card>

          {/* Leggenda integrata */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Leggenda & Parametri</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Colori tool */}
                <div className="space-y-2">
                  <h6 className="font-medium text-sm text-muted-foreground">STATO TOOL</h6>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-sm"></div>
                      <span>Posizionato</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-yellow-500 rounded-sm"></div>
                      <span>Ruotato</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-sm"></div>
                      <span>Escluso</span>
                    </div>
                  </div>
                </div>

                {/* Parametri */}
                <div className="space-y-2">
                  <h6 className="font-medium text-sm text-muted-foreground">PARAMETRI</h6>
                  <div className="space-y-1 text-xs">
                    <div>Padding: {batchData.parametri?.padding_mm || 10}mm</div>
                    <div>Distanza: {batchData.parametri?.min_distance_mm || 8}mm</div>
                  </div>
                </div>

                {/* Statistiche dimensioni */}
                <div className="space-y-2">
                  <h6 className="font-medium text-sm text-muted-foreground">DIMENSIONI</h6>
                  <div className="space-y-1 text-xs">
                    <div>Piano: {batchData.autoclave?.lunghezza}×{batchData.autoclave?.larghezza_piano}mm</div>
                    <div>Area: {formatArea(autoclaveArea)}</div>
                  </div>
                </div>

                {/* Contatori */}
                <div className="space-y-2">
                  <h6 className="font-medium text-sm text-muted-foreground">CONTATORI</h6>
                  <div className="space-y-1 text-xs">
                    <div>{validTools.length} tool posizionati</div>
                    <div>{rotatedTools.length} ruotati</div>
                    {excludedTools.length > 0 && (
                      <div className="text-destructive">{excludedTools.length} esclusi</div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pannello informazioni - 2/5 dello spazio */}
        <div className="lg:col-span-2 space-y-4">
          {/* Metriche principali */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Metriche Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Efficienza principale */}
              <div className="text-center space-y-2">
                <div className={`text-4xl font-bold ${getEfficiencyColor(efficiency).split(' ')[0]}`}>
                  {efficiency.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Efficienza Area</div>
              </div>

              <Separator />

              {/* Metriche secondarie */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <div className="text-muted-foreground">Peso Totale</div>
                  <div className="font-medium">{formatWeight(totalWeight)}</div>
                </div>
                
                <div className="space-y-1">
                  <div className="text-muted-foreground">Area Utilizzata</div>
                  <div className="font-medium">{formatArea(totalArea)}</div>
                </div>
                
                <div className="space-y-1">
                  <div className="text-muted-foreground">Valvole Totali</div>
                  <div className="font-medium">{batchData.valvole_totali_utilizzate || 0}</div>
                </div>
                
                <div className="space-y-1">
                  <div className="text-muted-foreground">Dimensione Media</div>
                  <div className="font-medium">{formatArea(averageToolSize * 1000000)}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tool selezionato */}
          {selectedToolData && (
            <Card className="border-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Tool Selezionato</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="font-medium">ODL #{selectedToolData.odl_id}</div>
                  {selectedToolData.part_number && (
                    <div className="text-sm">Part: {selectedToolData.part_number}</div>
                  )}
                  {selectedToolData.tool_nome && (
                    <div className="text-sm">Tool: {selectedToolData.tool_nome}</div>
                  )}
                </div>
                
                <Separator />
                
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-muted-foreground">Posizione:</span>
                    <div className="font-medium">{selectedToolData.x.toFixed(0)}, {selectedToolData.y.toFixed(0)}mm</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Dimensioni:</span>
                    <div className="font-medium">{selectedToolData.width.toFixed(0)}×{selectedToolData.height.toFixed(0)}mm</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Area:</span>
                    <div className="font-medium">{formatArea(selectedToolData.width * selectedToolData.height)}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Peso:</span>
                    <div className="font-medium">{selectedToolData.peso?.toFixed(1) || 'N/A'}kg</div>
                  </div>
                </div>
                
                {selectedToolData.rotated && (
                  <Badge variant="secondary" className="w-full justify-center">
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Tool Ruotato
                  </Badge>
                )}
              </CardContent>
            </Card>
          )}

          {/* Azioni rapide */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Azioni</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Esporta Report PDF
              </Button>
              
              <Button variant="outline" className="w-full justify-start" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Rigenera Nesting
              </Button>
              
              <Separator />
              
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Creato: {new Date(batchData.created_at).toLocaleDateString('it-IT')}</div>
                <div>Batch ID: {batchData.id.slice(0, 8)}...</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 