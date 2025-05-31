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
        
        // ✅ DEBUG: Verifica dimensioni reali
        console.log('🔧 NestingCanvas - Layout data caricato:', {
          nesting_id: nestingId,
          autoclave: {
            nome: response.layout_data.autoclave.nome,
            dimensioni: {
              lunghezza: response.layout_data.autoclave.lunghezza,
              larghezza_piano: response.layout_data.autoclave.larghezza_piano
            }
          },
          odl_count: response.layout_data.odl_list.length,
          posizioni_count: response.layout_data.posizioni_tool.length,
          prime_posizioni: response.layout_data.posizioni_tool.slice(0, 3).map(pos => ({
            odl_id: pos.odl_id,
            x: pos.x,
            y: pos.y,
            width: pos.width,
            height: pos.height,
            rotated: pos.rotated
          }))
        });
        
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
      console.error('❌ Errore caricamento layout:', error);
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
      scale: 1,
      gridSize: 50
    }
    
    const autoclave = layoutData.autoclave
    const margin = 120 // Margine per le etichette, righelli e legenda
    
    // Sistema di riferimento: 1mm = 1 unità SVG per accuratezza
    // Scala per convertire mm in pixel per la visualizzazione
    const maxDisplayWidth = 1200
    const maxDisplayHeight = height - 100
    const scaleX = maxDisplayWidth / (autoclave.lunghezza + margin * 2)
    const scaleY = maxDisplayHeight / (autoclave.larghezza_piano + margin * 2)
    const displayScale = Math.min(scaleX, scaleY, 0.8) // Max 0.8 per lasciare spazio ai controlli
    
    const scaledWidth = (autoclave.lunghezza + margin * 2) * displayScale
    const scaledHeight = (autoclave.larghezza_piano + margin * 2) * displayScale
    
    // Griglia: ogni 100mm (10cm) per il sistema di riferimento
    const gridSizeMm = 100
    const gridSizePixels = gridSizeMm * displayScale
    
    return {
      width: Math.max(scaledWidth, 600),
      height: Math.max(scaledHeight, 400),
      viewBox: `0 0 ${scaledWidth} ${scaledHeight}`,
      autoclaveX: margin * displayScale,
      autoclaveY: margin * displayScale,
      autoclaveWidth: autoclave.lunghezza * displayScale,
      autoclaveHeight: autoclave.larghezza_piano * displayScale,
      scale: displayScale,
      gridSize: gridSizePixels,
      gridSizeMm: gridSizeMm,
      margin: margin * displayScale,
      
      // Dimensioni reali per il sistema di riferimento
      realWidth: autoclave.lunghezza,
      realHeight: autoclave.larghezza_piano
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
                {/* Pattern griglia di riferimento */}
                <pattern
                  id="reference-grid"
                  width={svgDimensions.gridSize}
                  height={svgDimensions.gridSize}
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d={`M ${svgDimensions.gridSize} 0 L 0 0 0 ${svgDimensions.gridSize}`}
                    fill="none"
                    stroke="#d1d5db"
                    strokeWidth="1"
                  />
                  <circle
                    cx={svgDimensions.gridSize}
                    cy={svgDimensions.gridSize}
                    r="2"
                    fill="#9ca3af"
                  />
                </pattern>
                
                {/* Pattern griglia fine per precisione */}
                <pattern
                  id="fine-grid"
                  width={svgDimensions.gridSize / 5}
                  height={svgDimensions.gridSize / 5}
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d={`M ${svgDimensions.gridSize / 5} 0 L 0 0 0 ${svgDimensions.gridSize / 5}`}
                    fill="none"
                    stroke="#f3f4f6"
                    strokeWidth="0.5"
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

              {/* Sistema di riferimento - griglia di sfondo */}
              {showGrid && (
                <g>
                  {/* Griglia fine per precisione */}
                  <rect
                    x="0"
                    y="0"
                    width={svgDimensions.width}
                    height={svgDimensions.height}
                    fill="url(#fine-grid)"
                  />
                  
                  {/* Griglia principale di riferimento */}
                  <rect
                    x="0"
                    y="0"
                    width={svgDimensions.width}
                    height={svgDimensions.height}
                    fill="url(#reference-grid)"
                  />
                </g>
              )}

              {/* Righelli e coordinate */}
              {showDimensions && (
                <g>
                  {/* Righello orizzontale (asse X) */}
                  <g>
                    <line
                      x1={svgDimensions.margin || 50}
                      y1={(svgDimensions.margin || 50) - 30}
                      x2={(svgDimensions.margin || 50) + (svgDimensions.realWidth || 1000) * svgDimensions.scale}
                      y2={(svgDimensions.margin || 50) - 30}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    
                    {/* Tacche e etichette righello X */}
                    {Array.from({ length: Math.floor((svgDimensions.realWidth || 1000) / (svgDimensions.gridSizeMm || 100)) + 1 }, (_, i) => {
                      const xPos = (svgDimensions.margin || 50) + (i * svgDimensions.gridSize)
                      const mmValue = i * (svgDimensions.gridSizeMm || 100)
                      return (
                        <g key={`x-ruler-${i}`}>
                          <line
                            x1={xPos}
                            y1={(svgDimensions.margin || 50) - 35}
                            x2={xPos}
                            y2={(svgDimensions.margin || 50) - 25}
                            stroke="#374151"
                            strokeWidth="1"
                          />
                          <text
                            x={xPos}
                            y={(svgDimensions.margin || 50) - 40}
                            textAnchor="middle"
                            className="fill-gray-700 text-xs font-mono"
                          >
                            {mmValue}mm
                          </text>
                        </g>
                      )
                    })}
                  </g>
                  
                  {/* Righello verticale (asse Y) */}
                  <g>
                    <line
                      x1={(svgDimensions.margin || 50) - 30}
                      y1={svgDimensions.margin || 50}
                      x2={(svgDimensions.margin || 50) - 30}
                      y2={(svgDimensions.margin || 50) + (svgDimensions.realHeight || 800) * svgDimensions.scale}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    
                    {/* Tacche e etichette righello Y */}
                    {Array.from({ length: Math.floor((svgDimensions.realHeight || 800) / (svgDimensions.gridSizeMm || 100)) + 1 }, (_, i) => {
                      const yPos = (svgDimensions.margin || 50) + (i * svgDimensions.gridSize)
                      const mmValue = i * (svgDimensions.gridSizeMm || 100)
                      return (
                        <g key={`y-ruler-${i}`}>
                          <line
                            x1={(svgDimensions.margin || 50) - 35}
                            y1={yPos}
                            x2={(svgDimensions.margin || 50) - 25}
                            y2={yPos}
                            stroke="#374151"
                            strokeWidth="1"
                          />
                          <text
                            x={(svgDimensions.margin || 50) - 40}
                            y={yPos + 4}
                            textAnchor="middle"
                            className="fill-gray-700 text-xs font-mono"
                            transform={`rotate(-90, ${(svgDimensions.margin || 50) - 40}, ${yPos + 4})`}
                          >
                            {mmValue}mm
                          </text>
                        </g>
                      )
                    })}
                  </g>
                  
                  {/* Origine del sistema di coordinate */}
                  <g>
                    <circle
                      cx={svgDimensions.margin || 50}
                      cy={svgDimensions.margin || 50}
                      r="4"
                      fill="#dc2626"
                      stroke="white"
                      strokeWidth="2"
                    />
                    <text
                      x={(svgDimensions.margin || 50) + 10}
                      y={(svgDimensions.margin || 50) - 10}
                      className="fill-red-600 text-xs font-semibold"
                    >
                      (0,0)
                    </text>
                  </g>
                </g>
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
                        y2={svgDimensions.autoclaveX + svgDimensions.autoclaveHeight + 20}
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

              {/* Tool posizionati con coordinate reali */}
              {layoutData.posizioni_tool.map((position) => {
                const odl = layoutData.odl_list.find(o => o.id === position.odl_id)
                if (!odl) return null

                // Coordinate reali dal backend (già in mm)
                const realX = position.x  // Posizione X reale in mm
                const realY = position.y  // Posizione Y reale in mm
                const realWidth = position.width   // Larghezza reale in mm
                const realHeight = position.height // Altezza reale in mm

                // Coordinate visualizzazione (convertite per l'SVG)
                const displayX = (svgDimensions.margin || 50) + (realX * svgDimensions.scale)
                const displayY = (svgDimensions.margin || 50) + (realY * svgDimensions.scale)
                const displayWidth = realWidth * svgDimensions.scale
                const displayHeight = realHeight * svgDimensions.scale
                
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
                        {/* Rettangolo tool con bordo di precisione */}
                        <rect
                          x={displayX}
                          y={displayY}
                          width={displayWidth}
                          height={displayHeight}
                          fill={toolColor}
                          stroke={isSelected ? "#1f2937" : "#374151"}
                          strokeWidth={isSelected ? "3" : "1"}
                          filter={isHovered ? "url(#shadow)" : undefined}
                          opacity={isHovered ? 0.9 : 0.8}
                        />
                        
                        {/* Bordo interno per visualizzare precisione */}
                        {isSelected && (
                          <rect
                            x={displayX + 1}
                            y={displayY + 1}
                            width={displayWidth - 2}
                            height={displayHeight - 2}
                            fill="none"
                            stroke="#3b82f6"
                            strokeWidth="1"
                            strokeDasharray="3,2"
                            opacity="0.7"
                          />
                        )}
                        
                        {/* Pattern per tool ruotati */}
                        {position.rotated && (
                          <rect
                            x={displayX}
                            y={displayY}
                            width={displayWidth}
                            height={displayHeight}
                            fill="url(#rotated-pattern)"
                            opacity="0.3"
                          />
                        )}
                        
                        {/* Icona rotazione */}
                        {position.rotated && (
                          <g transform={`translate(${displayX + displayWidth - 15}, ${displayY + 5})`}>
                            <circle r="8" fill="white" opacity="0.9"/>
                            <RotateCw className="h-3 w-3" x="-6" y="-6" />
                          </g>
                        )}
                        
                        {/* Nome tool */}
                        {showToolNames && displayWidth > 60 && displayHeight > 30 && (
                          <text
                            x={displayX + displayWidth / 2}
                            y={displayY + displayHeight / 2 - 5}
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
                            x={displayX + displayWidth / 2}
                            y={displayY + displayHeight / 2 + 10}
                            textAnchor="middle"
                            className="fill-white text-xs"
                            style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.7)' }}
                          >
                            {odl.parte.num_valvole_richieste}V
                          </text>
                        )}
                        
                        {/* Badge priorità */}
                        {showPriorities && (
                          <g transform={`translate(${displayX + 5}, ${displayY + 5})`}>
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
                        
                        {/* Quote dimensioni e coordinate */}
                        {showDimensions && isSelected && (
                          <>
                            {/* Quota larghezza sopra */}
                            <text
                              x={displayX + displayWidth / 2}
                              y={displayY - 8}
                              textAnchor="middle"
                              className="fill-blue-600 text-xs font-medium bg-white"
                            >
                              {realWidth.toFixed(1)}mm
                            </text>
                            
                            {/* Quota altezza a sinistra */}
                            <text
                              x={displayX - 8}
                              y={displayY + displayHeight / 2}
                              textAnchor="middle"
                              className="fill-blue-600 text-xs font-medium"
                              transform={`rotate(-90, ${displayX - 8}, ${displayY + displayHeight / 2})`}
                            >
                              {realHeight.toFixed(1)}mm
                            </text>
                            
                            {/* Coordinate posizione */}
                            <text
                              x={displayX + 2}
                              y={displayY + displayHeight - 2}
                              className="fill-yellow-300 text-xs font-mono font-bold"
                              style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.8)' }}
                            >
                              ({realX.toFixed(0)},{realY.toFixed(0)})
                            </text>
                          </>
                        )}
                      </g>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs">
                      <div className="space-y-2">
                        <div className="font-semibold">{odl.tool.part_number_tool}</div>
                        <div className="text-sm text-muted-foreground">{odl.parte.part_number}</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>Priorità: {odl.priorita}</div>
                          <div>Valvole: {odl.parte.num_valvole_richieste}</div>
                          <div>Piano: {position.piano}</div>
                          <div>{position.rotated ? "Ruotato" : "Normale"}</div>
                        </div>
                        <div className="border-t pt-2 space-y-1">
                          <div className="text-xs font-semibold text-blue-600">Dimensioni reali:</div>
                          <div className="text-xs font-mono">
                            {realWidth.toFixed(1)}mm × {realHeight.toFixed(1)}mm
                          </div>
                          <div className="text-xs font-semibold text-green-600">Posizione:</div>
                          <div className="text-xs font-mono">
                            X: {realX.toFixed(1)}mm, Y: {realY.toFixed(1)}mm
                          </div>
                          <div className="text-xs text-gray-500">
                            Area: {(realWidth * realHeight / 100).toFixed(1)}cm²
                          </div>
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
            
            {/* ✅ DEBUG: Pannello informazioni dimensioni reali */}
            {layoutData && (
              <div className="absolute top-2 right-2 bg-blue-50/95 backdrop-blur-sm rounded px-3 py-2 text-xs border border-blue-200">
                <div className="font-semibold text-blue-800 mb-1">📏 Dimensioni Reali</div>
                <div className="space-y-1 text-blue-700">
                  <div><strong>Autoclave:</strong> {layoutData.autoclave.lunghezza}×{layoutData.autoclave.larghezza_piano}mm</div>
                  <div><strong>Scala:</strong> 1:{Math.round(1/svgDimensions.scale)}</div>
                  <div><strong>Tool:</strong> {layoutData.posizioni_tool.length} posizionati</div>
                  {layoutData.posizioni_tool.length > 0 && (
                    <div className="border-t border-blue-300 pt-1 mt-1">
                      <div className="font-medium">Primo tool:</div>
                      <div>Pos: ({layoutData.posizioni_tool[0].x.toFixed(0)}, {layoutData.posizioni_tool[0].y.toFixed(0)})mm</div>
                      <div>Size: {layoutData.posizioni_tool[0].width.toFixed(0)}×{layoutData.posizioni_tool[0].height.toFixed(0)}mm</div>
                      {layoutData.posizioni_tool[0].rotated && <div className="text-orange-600">🔄 Ruotato</div>}
                    </div>
                  )}
                </div>
              </div>
            )}
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