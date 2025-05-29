'use client'

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { 
  Eye, 
  ZoomIn, 
  ZoomOut, 
  RotateCw, 
  Maximize2, 
  Download,
  Settings,
  Package,
  Layers,
  AlertTriangle,
  Grid3X3,
  Move,
  Info,
  Ruler,
  Target
} from 'lucide-react'
import { 
  nestingApi, 
  NestingLayoutData, 
  ToolPosition, 
  ODLLayoutInfo,
  AutoclaveLayoutInfo 
} from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingCanvasProps {
  nestingId: number
  onToolClick?: (odl: ODLLayoutInfo) => void
  showControls?: boolean
  className?: string
  height?: number
}

interface ViewportState {
  zoom: number
  panX: number
  panY: number
  isDragging: boolean
  dragStart: { x: number; y: number }
}

export function NestingCanvas({ 
  nestingId, 
  onToolClick, 
  showControls = true,
  className = "",
  height = 600
}: NestingCanvasProps) {
  const [layoutData, setLayoutData] = useState<NestingLayoutData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedOdl, setSelectedOdl] = useState<number | null>(null)
  const [hoveredOdl, setHoveredOdl] = useState<number | null>(null)
  
  // Stato del viewport
  const [viewport, setViewport] = useState<ViewportState>({
    zoom: 1,
    panX: 0,
    panY: 0,
    isDragging: false,
    dragStart: { x: 0, y: 0 }
  })
  
  // Opzioni di visualizzazione
  const [showExcluded, setShowExcluded] = useState(true)
  const [showDimensions, setShowDimensions] = useState(true)
  const [showToolNames, setShowToolNames] = useState(true)
  const [showGrid, setShowGrid] = useState(true)
  const [showValves, setShowValves] = useState(true)
  const [showPriorities, setShowPriorities] = useState(true)
  
  // Parametri di layout
  const [paddingMm, setPaddingMm] = useState(10)
  const [bordaMm, setBordaMm] = useState(20)
  const [rotazioneAbilitata, setRotazioneAbilitata] = useState(true)
  
  const svgRef = useRef<SVGSVGElement>(null)
  const { toast } = useToast()

  // Carica i dati del layout
  const loadLayoutData = async () => {
    try {
      setIsLoading(true)
      const response = await nestingApi.getLayout(nestingId, {
        padding_mm: paddingMm,
        borda_mm: bordaMm,
        rotazione_abilitata: rotazioneAbilitata
      })
      
      if (response.success && response.layout_data) {
        setLayoutData(response.layout_data)
        
        // Reset viewport quando cambiano i dati
        setViewport(prev => ({
          ...prev,
          zoom: 1,
          panX: 0,
          panY: 0
        }))
      } else {
        throw new Error(response.message || 'Errore nel caricamento del layout')
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare il layout del nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadLayoutData()
  }, [nestingId, paddingMm, bordaMm, rotazioneAbilitata])

  // Calcola le dimensioni del viewport SVG
  const svgDimensions = useMemo(() => {
    if (!layoutData) return { 
      width: 800, 
      height: 600, 
      viewBox: "0 0 800 600",
      autoclaveX: 50,
      autoclaveY: 50,
      autoclaveWidth: 700,
      autoclaveHeight: 500,
      scale: 1
    }
    
    const autoclave = layoutData.autoclave
    const margin = 100 // Margine per le etichette e la legenda
    
    // Scala per convertire mm in pixel (adattiva)
    const maxWidth = 1000
    const maxHeight = height - 100
    const scaleX = maxWidth / (autoclave.lunghezza + margin * 2)
    const scaleY = maxHeight / (autoclave.larghezza_piano + margin * 2)
    const scale = Math.min(scaleX, scaleY, 1) // Non ingrandire oltre 1:1
    
    const scaledWidth = (autoclave.lunghezza + margin * 2) * scale
    const scaledHeight = (autoclave.larghezza_piano + margin * 2) * scale
    
    return {
      width: Math.max(scaledWidth, 400),
      height: Math.max(scaledHeight, 300),
      viewBox: `0 0 ${scaledWidth} ${scaledHeight}`,
      autoclaveX: margin * scale,
      autoclaveY: margin * scale,
      autoclaveWidth: autoclave.lunghezza * scale,
      autoclaveHeight: autoclave.larghezza_piano * scale,
      scale
    }
  }, [layoutData, height])

  // Genera colori per i tool basati sulla priorità
  const getToolColor = (priorita: number, isExcluded: boolean = false, isSelected: boolean = false, isHovered: boolean = false) => {
    if (isExcluded) return '#ef4444' // Rosso per esclusi
    if (isSelected) return '#3b82f6' // Blu per selezionato
    if (isHovered) return '#8b5cf6' // Viola per hover
    
    // Gradiente dal verde (priorità bassa) al rosso (priorità alta)
    const hue = Math.max(0, 120 - (priorita * 12)) // 120 = verde, 0 = rosso
    return `hsl(${hue}, 70%, 60%)`
  }

  // Gestisce il click su un tool
  const handleToolClick = (position: ToolPosition) => {
    const odl = layoutData?.odl_list.find(o => o.id === position.odl_id)
    if (odl) {
      setSelectedOdl(odl.id)
      if (onToolClick) {
        onToolClick(odl)
      }
    }
  }

  // Gestione zoom
  const handleZoom = useCallback((delta: number, centerX?: number, centerY?: number) => {
    setViewport(prev => {
      const newZoom = Math.max(0.1, Math.min(5, prev.zoom + delta))
      
      // Se abbiamo un centro, zoom verso quel punto
      if (centerX !== undefined && centerY !== undefined) {
        const zoomFactor = newZoom / prev.zoom
        const newPanX = centerX - (centerX - prev.panX) * zoomFactor
        const newPanY = centerY - (centerY - prev.panY) * zoomFactor
        
        return {
          ...prev,
          zoom: newZoom,
          panX: newPanX,
          panY: newPanY
        }
      }
      
      return { ...prev, zoom: newZoom }
    })
  }, [])

  // Gestione pan
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) { // Solo click sinistro
      setViewport(prev => ({
        ...prev,
        isDragging: true,
        dragStart: { x: e.clientX - prev.panX, y: e.clientY - prev.panY }
      }))
    }
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (viewport.isDragging) {
      setViewport(prev => ({
        ...prev,
        panX: e.clientX - prev.dragStart.x,
        panY: e.clientY - prev.dragStart.y
      }))
    }
  }, [viewport.isDragging])

  const handleMouseUp = useCallback(() => {
    setViewport(prev => ({ ...prev, isDragging: false }))
  }, [])

  // Gestione wheel per zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const rect = svgRef.current?.getBoundingClientRect()
    if (rect) {
      const centerX = e.clientX - rect.left
      const centerY = e.clientY - rect.top
      handleZoom(-e.deltaY * 0.001, centerX, centerY)
    }
  }, [handleZoom])

  // Reset viewport
  const resetViewport = () => {
    setViewport({
      zoom: 1,
      panX: 0,
      panY: 0,
      isDragging: false,
      dragStart: { x: 0, y: 0 }
    })
  }

  // Fit to view
  const fitToView = () => {
    if (!layoutData || !svgRef.current) return
    
    const svg = svgRef.current
    const rect = svg.getBoundingClientRect()
    const viewBox = svg.viewBox.baseVal
    
    const scaleX = rect.width / viewBox.width
    const scaleY = rect.height / viewBox.height
    const scale = Math.min(scaleX, scaleY) * 0.9 // 90% per margine
    
    setViewport({
      zoom: scale,
      panX: (rect.width - viewBox.width * scale) / 2,
      panY: (rect.height - viewBox.height * scale) / 2,
      isDragging: false,
      dragStart: { x: 0, y: 0 }
    })
  }

  // Esporta l'SVG come immagine
  const exportSVG = () => {
    const svgElement = document.getElementById(`nesting-canvas-${nestingId}`)
    if (!svgElement) return

    const svgData = new XMLSerializer().serializeToString(svgElement)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      ctx?.drawImage(img, 0, 0)
      
      const link = document.createElement('a')
      link.download = `nesting-${nestingId}-layout.png`
      link.href = canvas.toDataURL()
      link.click()
    }
    
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData)
  }

  // Trova ODL esclusi (quelli senza posizione)
  const excludedOdls = useMemo(() => {
    if (!layoutData) return []
    
    const positionedOdlIds = new Set(layoutData.posizioni_tool.map(p => p.odl_id))
    return layoutData.odl_list.filter(odl => !positionedOdlIds.has(odl.id))
  }, [layoutData])

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Canvas Nesting
          </CardTitle>
          <CardDescription>
            Caricamento layout del nesting...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full" style={{ height: height }} />
        </CardContent>
      </Card>
    )
  }

  if (!layoutData) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Errore Visualizzazione
          </CardTitle>
          <CardDescription>
            Impossibile caricare i dati del layout
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={loadLayoutData} variant="outline">
            Riprova
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <TooltipProvider>
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Canvas Nesting - {layoutData.autoclave.nome}
              </CardTitle>
              <CardDescription>
                {layoutData.odl_list.length} ODL • {layoutData.posizioni_tool.length} posizionati • {excludedOdls.length} esclusi
              </CardDescription>
            </div>
            
            {showControls && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleZoom(0.2)}
                  disabled={viewport.zoom >= 5}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleZoom(-0.2)}
                  disabled={viewport.zoom <= 0.1}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetViewport}
                >
                  <Target className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fitToView}
                >
                  <Maximize2 className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={exportSVG}
                >
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Controlli di visualizzazione */}
          {showControls && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-grid"
                  checked={showGrid}
                  onCheckedChange={setShowGrid}
                />
                <Label htmlFor="show-grid" className="text-sm">Griglia</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-dimensions"
                  checked={showDimensions}
                  onCheckedChange={setShowDimensions}
                />
                <Label htmlFor="show-dimensions" className="text-sm">Quote</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-names"
                  checked={showToolNames}
                  onCheckedChange={setShowToolNames}
                />
                <Label htmlFor="show-names" className="text-sm">Nomi</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-valves"
                  checked={showValves}
                  onCheckedChange={setShowValves}
                />
                <Label htmlFor="show-valves" className="text-sm">Valvole</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-excluded"
                  checked={showExcluded}
                  onCheckedChange={setShowExcluded}
                />
                <Label htmlFor="show-excluded" className="text-sm">Esclusi</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-priorities"
                  checked={showPriorities}
                  onCheckedChange={setShowPriorities}
                />
                <Label htmlFor="show-priorities" className="text-sm">Priorità</Label>
              </div>
              
              <div className="col-span-2 flex items-center space-x-2">
                <Label className="text-sm">Zoom: {Math.round(viewport.zoom * 100)}%</Label>
                <Slider
                  value={viewport.zoom}
                  onValueChange={(value) => setViewport(prev => ({ ...prev, zoom: value }))}
                  min={0.1}
                  max={5}
                  step={0.1}
                  className="flex-1"
                />
              </div>
            </div>
          )}

          {/* Canvas SVG */}
          <div 
            className="relative border rounded-lg overflow-hidden bg-gray-50"
            style={{ height: height }}
          >
            <svg
              ref={svgRef}
              id={`nesting-canvas-${nestingId}`}
              width="100%"
              height="100%"
              viewBox={svgDimensions.viewBox}
              className="cursor-move"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              style={{
                transform: `translate(${viewport.panX}px, ${viewport.panY}px) scale(${viewport.zoom})`,
                transformOrigin: '0 0'
              }}
            >
              {/* Definizioni per pattern e filtri */}
              <defs>
                {/* Pattern griglia */}
                <pattern
                  id="grid"
                  width={50 * svgDimensions.scale}
                  height={50 * svgDimensions.scale}
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d={`M ${50 * svgDimensions.scale} 0 L 0 0 0 ${50 * svgDimensions.scale}`}
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="1"
                  />
                </pattern>
                
                {/* Filtro ombra */}
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.3"/>
                </filter>
                
                {/* Pattern per tool ruotati */}
                <pattern id="rotated-pattern" patternUnits="userSpaceOnUse" width="4" height="4">
                  <rect width="4" height="4" fill="white"/>
                  <path d="M 0,4 l 4,-4 M -1,1 l 2,-2 M 3,5 l 2,-2" stroke="#666" strokeWidth="1"/>
                </pattern>
              </defs>

              {/* Griglia di sfondo */}
              {showGrid && (
                <rect
                  x="0"
                  y="0"
                  width={svgDimensions.width}
                  height={svgDimensions.height}
                  fill="url(#grid)"
                />
              )}

              {/* Autoclave */}
              <g>
                {/* Bordo autoclave */}
                <rect
                  x={svgDimensions.autoclaveX}
                  y={svgDimensions.autoclaveY}
                  width={svgDimensions.autoclaveWidth}
                  height={svgDimensions.autoclaveHeight}
                  fill="none"
                  stroke="#1f2937"
                  strokeWidth="3"
                  strokeDasharray="10,5"
                />
                
                {/* Etichetta autoclave */}
                <text
                  x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth / 2}
                  y={svgDimensions.autoclaveY - 10}
                  textAnchor="middle"
                  className="fill-gray-700 text-sm font-semibold"
                >
                  {layoutData.autoclave.nome} ({layoutData.autoclave.lunghezza}×{layoutData.autoclave.larghezza_piano}mm)
                </text>
                
                {/* Quote autoclave */}
                {showDimensions && (
                  <>
                    {/* Quota lunghezza */}
                    <g>
                      <line
                        x1={svgDimensions.autoclaveX}
                        y1={svgDimensions.autoclaveY + svgDimensions.autoclaveHeight + 20}
                        x2={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth}
                        y2={svgDimensions.autoclaveY + svgDimensions.autoclaveHeight + 20}
                        stroke="#666"
                        strokeWidth="1"
                      />
                      <text
                        x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth / 2}
                        y={svgDimensions.autoclaveY + svgDimensions.autoclaveHeight + 35}
                        textAnchor="middle"
                        className="fill-gray-600 text-xs"
                      >
                        {layoutData.autoclave.lunghezza}mm
                      </text>
                    </g>
                    
                    {/* Quota larghezza */}
                    <g>
                      <line
                        x1={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth + 20}
                        y1={svgDimensions.autoclaveY}
                        x2={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth + 20}
                        y2={svgDimensions.autoclaveY + svgDimensions.autoclaveHeight}
                        stroke="#666"
                        strokeWidth="1"
                      />
                      <text
                        x={svgDimensions.autoclaveX + svgDimensions.autoclaveWidth + 35}
                        y={svgDimensions.autoclaveY + svgDimensions.autoclaveHeight / 2}
                        textAnchor="middle"
                        className="fill-gray-600 text-xs"
                        transform={`rotate(90, ${svgDimensions.autoclaveX + svgDimensions.autoclaveWidth + 35}, ${svgDimensions.autoclaveY + svgDimensions.autoclaveHeight / 2})`}
                      >
                        {layoutData.autoclave.larghezza_piano}mm
                      </text>
                    </g>
                  </>
                )}
              </g>

              {/* Tool posizionati */}
              {layoutData.posizioni_tool.map((position) => {
                const odl = layoutData.odl_list.find(o => o.id === position.odl_id)
                if (!odl) return null

                const x = svgDimensions.autoclaveX + (position.x * svgDimensions.scale)
                const y = svgDimensions.autoclaveY + (position.y * svgDimensions.scale)
                const width = position.width * svgDimensions.scale
                const height = position.height * svgDimensions.scale
                
                const isSelected = selectedOdl === odl.id
                const isHovered = hoveredOdl === odl.id
                const toolColor = getToolColor(odl.priorita, false, isSelected, isHovered)

                return (
                  <Tooltip key={position.odl_id}>
                    <TooltipTrigger asChild>
                      <g
                        className="cursor-pointer transition-all duration-200"
                        onClick={() => handleToolClick(position)}
                        onMouseEnter={() => setHoveredOdl(odl.id)}
                        onMouseLeave={() => setHoveredOdl(null)}
                      >
                        {/* Rettangolo tool */}
                        <rect
                          x={x}
                          y={y}
                          width={width}
                          height={height}
                          fill={toolColor}
                          stroke={isSelected ? "#1f2937" : "#374151"}
                          strokeWidth={isSelected ? "3" : "1"}
                          filter={isHovered ? "url(#shadow)" : undefined}
                          opacity={isHovered ? 0.9 : 0.8}
                        />
                        
                        {/* Pattern per tool ruotati */}
                        {position.rotated && (
                          <rect
                            x={x}
                            y={y}
                            width={width}
                            height={height}
                            fill="url(#rotated-pattern)"
                            opacity="0.3"
                          />
                        )}
                        
                        {/* Icona rotazione */}
                        {position.rotated && (
                          <g transform={`translate(${x + width - 15}, ${y + 5})`}>
                            <circle r="8" fill="white" opacity="0.9"/>
                            <RotateCw className="h-3 w-3" x="-6" y="-6" />
                          </g>
                        )}
                        
                        {/* Nome tool */}
                        {showToolNames && width > 60 && height > 30 && (
                          <text
                            x={x + width / 2}
                            y={y + height / 2 - 5}
                            textAnchor="middle"
                            className="fill-white text-xs font-medium"
                            style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.7)' }}
                          >
                            {odl.tool.part_number_tool}
                          </text>
                        )}
                        
                        {/* Numero valvole */}
                        {showValves && (
                          <text
                            x={x + width / 2}
                            y={y + height / 2 + 10}
                            textAnchor="middle"
                            className="fill-white text-xs"
                            style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.7)' }}
                          >
                            {odl.parte.num_valvole_richieste}V
                          </text>
                        )}
                        
                        {/* Badge priorità */}
                        {showPriorities && (
                          <g transform={`translate(${x + 5}, ${y + 5})`}>
                            <circle r="10" fill="white" opacity="0.9"/>
                            <text
                              textAnchor="middle"
                              y="4"
                              className="fill-gray-800 text-xs font-bold"
                            >
                              {odl.priorita}
                            </text>
                          </g>
                        )}
                        
                        {/* Quote dimensioni */}
                        {showDimensions && isSelected && (
                          <>
                            <text
                              x={x + width / 2}
                              y={y - 5}
                              textAnchor="middle"
                              className="fill-blue-600 text-xs font-medium"
                            >
                              {Math.round(position.width)}mm
                            </text>
                            <text
                              x={x - 5}
                              y={y + height / 2}
                              textAnchor="middle"
                              className="fill-blue-600 text-xs font-medium"
                              transform={`rotate(-90, ${x - 5}, ${y + height / 2})`}
                            >
                              {Math.round(position.height)}mm
                            </text>
                          </>
                        )}
                      </g>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs">
                      <div className="space-y-1">
                        <div className="font-semibold">{odl.tool.part_number_tool}</div>
                        <div className="text-sm text-muted-foreground">{odl.parte.part_number}</div>
                        <div className="text-xs">
                          Priorità: {odl.priorita} • Valvole: {odl.parte.num_valvole_richieste}
                        </div>
                        <div className="text-xs">
                          Dimensioni: {Math.round(position.width)}×{Math.round(position.height)}mm
                          {position.rotated && " (ruotato)"}
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                )
              })}
            </svg>
            
            {/* Informazioni viewport */}
            <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-600">
              Zoom: {Math.round(viewport.zoom * 100)}% • Pan: {Math.round(viewport.panX)}, {Math.round(viewport.panY)}
            </div>
          </div>

          {/* Legenda e statistiche */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Legenda priorità */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  Legenda Priorità
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Array.from({ length: 10 }, (_, i) => i + 1).map(priority => (
                  <div key={priority} className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: getToolColor(priority) }}
                    />
                    <span className="text-sm">Priorità {priority}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Statistiche */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Info className="h-4 w-4" />
                  Statistiche Layout
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>ODL totali:</span>
                  <Badge variant="secondary">{layoutData.odl_list.length}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>ODL posizionati:</span>
                  <Badge variant="default">{layoutData.posizioni_tool.length}</Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span>ODL esclusi:</span>
                  <Badge variant="destructive">{excludedOdls.length}</Badge>
                </div>
                <Separator />
                <div className="flex justify-between text-sm">
                  <span>Valvole utilizzate:</span>
                  <span>{layoutData.valvole_utilizzate}/{layoutData.valvole_totali}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Area utilizzata:</span>
                  <span>{Math.round(layoutData.area_utilizzata)}cm²</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Efficienza:</span>
                  <Badge variant="outline">
                    {Math.round((layoutData.area_utilizzata / layoutData.area_totale) * 100)}%
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ODL esclusi */}
          {showExcluded && excludedOdls.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-destructive" />
                  ODL Esclusi ({excludedOdls.length})
                </CardTitle>
                <CardDescription>
                  ODL che non sono stati inclusi nel layout per mancanza di spazio o altri vincoli
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {excludedOdls.map(odl => (
                    <div
                      key={odl.id}
                      className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded"
                    >
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: getToolColor(odl.priorita, true) }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                          {odl.tool.part_number_tool}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                          {odl.parte.part_number} • P{odl.priorita} • {odl.parte.num_valvole_richieste}V
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </TooltipProvider>
  )
} 