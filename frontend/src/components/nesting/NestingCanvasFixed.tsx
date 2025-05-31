import React, { useState, useEffect, useMemo, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { 
  ZoomIn, ZoomOut, RotateCw, Move, Grid, Ruler, 
  Eye, EyeOff, Download, RefreshCw, Settings
} from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"
import { nestingApi } from '../../lib/api/nesting'
import { NestingLayoutData, ToolPosition, ODLLayoutInfo } from '@/lib/api'

// ✅ FIXED: Definizioni dei tipi corretti
interface NestingCanvasFixedProps {
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

// ✅ FIXED: Costanti di conversione uniformi
const MM_TO_PIXEL_SCALE = 0.1 // 1mm = 0.1px per il calcolo base
const MIN_ZOOM = 0.05
const MAX_ZOOM = 10
const DEFAULT_MARGIN = 50 // Margine fisso in pixel

export function NestingCanvasFixed({ 
  nestingId, 
  onToolClick, 
  showControls = true,
  className = "",
  height = 600
}: NestingCanvasFixedProps) {
  const [layoutData, setLayoutData] = useState<NestingLayoutData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedOdl, setSelectedOdl] = useState<number | null>(null)
  const [hoveredOdl, setHoveredOdl] = useState<number | null>(null)
  
  // ✅ FIXED: Stato viewport con valori iniziali più conservativi
  const [viewport, setViewport] = useState<ViewportState>({
    zoom: 1,
    panX: 0,
    panY: 0,
    isDragging: false,
    dragStart: { x: 0, y: 0 }
  })
  
  // ✅ FIXED: Controlli di visualizzazione ottimizzati
  const [showGrid, setShowGrid] = useState(true)
  const [showDimensions, setShowDimensions] = useState(true)
  const [showToolNames, setShowToolNames] = useState(true)
  const [showValves, setShowValves] = useState(true)
  const [showPriorities, setShowPriorities] = useState(true)
  const [paddingMm, setPaddingMm] = useState(10.0)
  const [bordaMm, setBordaMm] = useState(20.0)
  const [rotazioneAbilitata, setRotazioneAbilitata] = useState(true)
  
  const svgRef = useRef<SVGSVGElement>(null)
  const { toast } = useToast()

  // ✅ FIXED: Caricamento dati con gestione errori migliorata
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
        
        // ✅ DEBUG: Log per verificare i dati
        console.log('🔧 FIXED - Layout data caricato:', {
          nesting_id: response.layout_data.id,
          autoclave: {
            nome: response.layout_data.autoclave.nome,
            dimensioni_mm: {
              lunghezza: response.layout_data.autoclave.lunghezza,
              larghezza_piano: response.layout_data.autoclave.larghezza_piano
            }
          },
          odl_count: response.layout_data.odl_list.length,
          posizioni_count: response.layout_data.posizioni_tool.length,
          prime_posizioni: response.layout_data.posizioni_tool.slice(0, 2).map((pos: ToolPosition) => ({
            odl_id: pos.odl_id,
            dimensioni_mm: { width: pos.width, height: pos.height },
            posizione_mm: { x: pos.x, y: pos.y },
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
      console.error('❌ FIXED - Errore caricamento layout:', error);
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

  // ✅ FIXED: Calcolo dimensioni SVG con proporzioni reali corrette
  const svgDimensions = useMemo(() => {
    if (!layoutData) return { 
      width: 800, 
      height: 600, 
      viewBox: "0 0 800 600",
      autoclaveX: DEFAULT_MARGIN,
      autoclaveY: DEFAULT_MARGIN,
      autoclaveWidth: 700,
      autoclaveHeight: 500,
      scale: 1,
      gridSize: 50,
      realWidth: 1000,
      realHeight: 800
    }
    
    const autoclave = layoutData.autoclave
    const margin = DEFAULT_MARGIN
    
    // ✅ FIXED: Sistema di riferimento rigoroso
    // Dimensioni reali autoclave in mm
    const autoclaveWidthMm = autoclave.lunghezza
    const autoclaveHeightMm = autoclave.larghezza_piano
    
    // Area disponibile per la visualizzazione (pixel)
    const maxDisplayWidth = Math.min(1400, window.innerWidth * 0.6)
    const maxDisplayHeight = height - 100
    
    // Calcola la scala per adattare l'autoclave mantenendo le proporzioni
    const scaleX = (maxDisplayWidth - margin * 2) / autoclaveWidthMm
    const scaleY = (maxDisplayHeight - margin * 2) / autoclaveHeightMm
    const scale = Math.min(scaleX, scaleY, 0.5) // Limita scala massima a 0.5
    
    // Dimensioni autoclave in pixel
    const autoclaveWidthPx = autoclaveWidthMm * scale
    const autoclaveHeightPx = autoclaveHeightMm * scale
    
    // Dimensioni totali canvas
    const totalWidth = autoclaveWidthPx + margin * 2
    const totalHeight = autoclaveHeightPx + margin * 2
    
    // Griglia: ogni 100mm
    const gridSizeMm = 100
    const gridSizePx = gridSizeMm * scale
    
    console.log('📐 FIXED - Calcolo dimensioni:', {
      autoclave_mm: { width: autoclaveWidthMm, height: autoclaveHeightMm },
      autoclave_px: { width: autoclaveWidthPx, height: autoclaveHeightPx },
      scale: scale,
      grid_size_px: gridSizePx,
      canvas_total: { width: totalWidth, height: totalHeight }
    });
    
    return {
      width: totalWidth,
      height: totalHeight,
      viewBox: `0 0 ${totalWidth} ${totalHeight}`,
      autoclaveX: margin,
      autoclaveY: margin,
      autoclaveWidth: autoclaveWidthPx,
      autoclaveHeight: autoclaveHeightPx,
      scale: scale,
      gridSize: Math.max(gridSizePx, 10), // Griglia minima 10px
      margin: margin,
      realWidth: autoclaveWidthMm,
      realHeight: autoclaveHeightMm
    }
  }, [layoutData, height])

  // ✅ FIXED: Colori tool con priorità visiva migliorata
  const getToolColor = (priorita: number, isExcluded: boolean = false, isSelected: boolean = false, isHovered: boolean = false) => {
    if (isExcluded) return '#ef4444' // Rosso per esclusi
    if (isSelected) return '#3b82f6' // Blu per selezionato
    if (isHovered) return '#10b981' // Verde per hover
    
    // Gradiente priorità: verde (bassa) -> giallo -> rosso (alta)
    const hue = Math.max(0, 120 - (priorita * 15))
    return `hsl(${hue}, 70%, 60%)`
  }

  // ✅ FIXED: Gestione click tool
  const handleToolClick = (position: ToolPosition) => {
    const odl = layoutData?.odl_list.find(o => o.id === position.odl_id)
    if (odl) {
      setSelectedOdl(odl.id)
      if (onToolClick) {
        onToolClick(odl)
      }
      console.log('🔧 FIXED - Tool clicked:', {
        odl_id: odl.id,
        tool_name: odl.tool.part_number_tool,
        position_mm: { x: position.x, y: position.y },
        size_mm: { width: position.width, height: position.height }
      });
    }
  }

  // ✅ FIXED: Gestione mouse per pan e zoom
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (e.button === 0) { // Click sinistro
      setViewport(prev => ({
        ...prev,
        isDragging: true,
        dragStart: { x: e.clientX - prev.panX, y: e.clientY - prev.panY }
      }))
    }
  }

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (viewport.isDragging) {
      setViewport(prev => ({
        ...prev,
        panX: e.clientX - prev.dragStart.x,
        panY: e.clientY - prev.dragStart.y
      }))
    }
  }

  const handleMouseUp = () => {
    setViewport(prev => ({ ...prev, isDragging: false }))
  }

  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    setViewport(prev => ({
      ...prev,
      zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev.zoom * zoomFactor))
    }))
  }

  // ✅ FIXED: Funzioni di controllo viewport
  const resetViewport = () => {
    setViewport({ zoom: 1, panX: 0, panY: 0, isDragging: false, dragStart: { x: 0, y: 0 } })
  }

  const fitToView = () => {
    // Calcola zoom per adattare tutto il contenuto
    const containerWidth = svgRef.current?.clientWidth || 800
    const containerHeight = svgRef.current?.clientHeight || 600
    const contentWidth = svgDimensions.width
    const contentHeight = svgDimensions.height
    
    const scaleX = containerWidth / contentWidth
    const scaleY = containerHeight / contentHeight
    const optimalZoom = Math.min(scaleX, scaleY) * 0.9 // 90% per margini
    
    setViewport({
      zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, optimalZoom)),
      panX: 0,
      panY: 0,
      isDragging: false,
      dragStart: { x: 0, y: 0 }
    })
  }

  const exportSVG = () => {
    if (!svgRef.current) return
    
    try {
      const svgData = new XMLSerializer().serializeToString(svgRef.current)
      const blob = new Blob([svgData], { type: 'image/svg+xml' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `nesting-${nestingId}-${new Date().toISOString().split('T')[0]}.svg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      toast({
        title: "Export completato",
        description: "Il file SVG è stato scaricato con successo"
      })
    } catch (error) {
      console.error('Errore export SVG:', error)
      toast({
        title: "Errore export",
        description: "Impossibile esportare il file SVG",
        variant: "destructive"
      })
    }
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-center space-y-4">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500" />
            <p className="text-muted-foreground">Caricamento layout nesting...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!layoutData) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8">
          <div className="text-center space-y-4">
            <div className="text-red-500">⚠️</div>
            <p className="text-muted-foreground">Impossibile caricare i dati del nesting</p>
            <Button onClick={loadLayoutData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Riprova
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Canvas Nesting #{nestingId} - {layoutData.autoclave.nome}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              📐 {layoutData.autoclave.lunghezza}×{layoutData.autoclave.larghezza_piano}mm
            </Badge>
            <Badge variant="secondary" className="text-xs">
              🔧 {layoutData.posizioni_tool.length} tools
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-4">
        {/* ✅ FIXED: Controlli ottimizzati */}
        {showControls && (
          <div className="space-y-4 mb-4">
            {/* Controlli zoom e viewport */}
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <Button onClick={resetViewport} variant="outline" size="sm">
                  <Move className="h-4 w-4" />
                </Button>
                <Button onClick={fitToView} variant="outline" size="sm">
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button onClick={exportSVG} variant="outline" size="sm">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex items-center gap-2 min-w-[200px]">
                <Label className="text-sm">Zoom: {Math.round(viewport.zoom * 100)}%</Label>
                <Slider
                  value={viewport.zoom}
                  onValueChange={(value: number) => setViewport(prev => ({ ...prev, zoom: value }))}
                  min={MIN_ZOOM}
                  max={MAX_ZOOM}
                  step={0.1}
                  className="flex-1"
                />
              </div>
            </div>
            
            {/* Interruttori visualizzazione */}
            <div className="flex items-center gap-4 flex-wrap text-sm">
              <div className="flex items-center gap-2">
                <Switch checked={showGrid} onCheckedChange={setShowGrid} />
                <Label>Griglia</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={showDimensions} onCheckedChange={setShowDimensions} />
                <Label>Quote</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={showToolNames} onCheckedChange={setShowToolNames} />
                <Label>Nomi</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={showValves} onCheckedChange={setShowValves} />
                <Label>Valvole</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={showPriorities} onCheckedChange={setShowPriorities} />
                <Label>Priorità</Label>
              </div>
            </div>
          </div>
        )}

        {/* ✅ FIXED: Canvas SVG con dimensioni corrette */}
        <div 
          className="relative border rounded-lg overflow-hidden bg-gray-50"
          style={{ height: height }}
        >
          <svg
            ref={svgRef}
            id={`nesting-canvas-fixed-${nestingId}`}
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
            {/* ✅ FIXED: Definizioni per pattern e filtri */}
            <defs>
              {/* Pattern griglia principale */}
              <pattern
                id="main-grid"
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
              
              {/* Pattern griglia fine */}
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

            {/* ✅ FIXED: Griglia di sfondo */}
            {showGrid && (
              <g>
                <rect
                  x="0"
                  y="0"
                  width={svgDimensions.width}
                  height={svgDimensions.height}
                  fill="url(#fine-grid)"
                />
                <rect
                  x="0"
                  y="0"
                  width={svgDimensions.width}
                  height={svgDimensions.height}
                  fill="url(#main-grid)"
                />
              </g>
            )}

            {/* ✅ FIXED: Sistema di coordinate */}
            {showDimensions && (
              <g>
                {/* Punto origine */}
                <g>
                  <circle
                    cx={svgDimensions.autoclaveX}
                    cy={svgDimensions.autoclaveY}
                    r="4"
                    fill="#dc2626"
                    stroke="white"
                    strokeWidth="2"
                  />
                  <text
                    x={svgDimensions.autoclaveX + 10}
                    y={svgDimensions.autoclaveY - 10}
                    className="fill-red-600 text-xs font-semibold"
                  >
                    (0,0)
                  </text>
                </g>
                
                {/* Righello orizzontale */}
                <g>
                  {Array.from({ length: Math.floor(svgDimensions.realWidth / 100) + 1 }, (_, i) => {
                    const x = svgDimensions.autoclaveX + (i * 100 * svgDimensions.scale)
                    return (
                      <g key={`h-${i}`}>
                        <line
                          x1={x}
                          y1={svgDimensions.autoclaveY - 10}
                          x2={x}
                          y2={svgDimensions.autoclaveY - 5}
                          stroke="#666"
                          strokeWidth="1"
                        />
                        <text
                          x={x}
                          y={svgDimensions.autoclaveY - 15}
                          textAnchor="middle"
                          className="fill-gray-600 text-xs"
                        >
                          {i * 100}
                        </text>
                      </g>
                    )
                  })}
                </g>
                
                {/* Righello verticale */}
                <g>
                  {Array.from({ length: Math.floor(svgDimensions.realHeight / 100) + 1 }, (_, i) => {
                    const y = svgDimensions.autoclaveY + (i * 100 * svgDimensions.scale)
                    return (
                      <g key={`v-${i}`}>
                        <line
                          x1={svgDimensions.autoclaveX - 10}
                          y1={y}
                          x2={svgDimensions.autoclaveX - 5}
                          y2={y}
                          stroke="#666"
                          strokeWidth="1"
                        />
                        <text
                          x={svgDimensions.autoclaveX - 15}
                          y={y + 3}
                          textAnchor="middle"
                          className="fill-gray-600 text-xs"
                          transform={`rotate(-90, ${svgDimensions.autoclaveX - 15}, ${y + 3})`}
                        >
                          {i * 100}
                        </text>
                      </g>
                    )
                  })}
                </g>
              </g>
            )}

            {/* ✅ FIXED: Autoclave */}
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

            {/* ✅ FIXED: Tool posizionati con coordinate corrette */}
            {layoutData.posizioni_tool.map((position) => {
              const odl = layoutData.odl_list.find(o => o.id === position.odl_id)
              if (!odl) return null

              // ✅ FIXED: Conversione coordinate rigorosa
              // Le coordinate dal backend sono già in mm, convertiamo in pixel
              const displayX = svgDimensions.autoclaveX + (position.x * svgDimensions.scale)
              const displayY = svgDimensions.autoclaveY + (position.y * svgDimensions.scale)
              const displayWidth = position.width * svgDimensions.scale
              const displayHeight = position.height * svgDimensions.scale
              
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
                      
                      {/* Bordo di selezione */}
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
                      
                      {/* Pattern rotazione */}
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
                      {position.rotated && displayWidth > 20 && displayHeight > 20 && (
                        <g transform={`translate(${displayX + displayWidth - 15}, ${displayY + 5})`}>
                          <circle r="8" fill="white" opacity="0.9"/>
                          <text x="0" y="3" textAnchor="middle" className="fill-blue-600 text-xs font-bold">
                            ↻
                          </text>
                        </g>
                      )}
                      
                      {/* Nome tool */}
                      {showToolNames && displayWidth > 60 && displayHeight > 25 && (
                        <text
                          x={displayX + displayWidth / 2}
                          y={displayY + displayHeight / 2 - 3}
                          textAnchor="middle"
                          className="fill-white text-xs font-medium"
                          style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.7)' }}
                        >
                          {odl.tool.part_number_tool}
                        </text>
                      )}
                      
                      {/* Valvole */}
                      {showValves && displayWidth > 40 && displayHeight > 25 && (
                        <text
                          x={displayX + displayWidth / 2}
                          y={displayY + displayHeight / 2 + 12}
                          textAnchor="middle"
                          className="fill-white text-xs"
                          style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.7)' }}
                        >
                          {odl.parte.num_valvole_richieste}V
                        </text>
                      )}
                      
                      {/* Badge priorità */}
                      {showPriorities && displayWidth > 30 && displayHeight > 30 && (
                        <g transform={`translate(${displayX + 5}, ${displayY + 5})`}>
                          <circle r="8" fill="white" opacity="0.9"/>
                          <text
                            textAnchor="middle"
                            y="3"
                            className="fill-gray-800 text-xs font-bold"
                          >
                            {odl.priorita}
                          </text>
                        </g>
                      )}
                      
                      {/* Quote dimensioni */}
                      {showDimensions && isSelected && (
                        <>
                          {/* Quota larghezza sopra */}
                          <text
                            x={displayX + displayWidth / 2}
                            y={displayY - 8}
                            textAnchor="middle"
                            className="fill-blue-600 text-xs font-medium"
                          >
                            {position.width.toFixed(0)}mm
                          </text>
                          
                          {/* Quota altezza a sinistra */}
                          <text
                            x={displayX - 8}
                            y={displayY + displayHeight / 2}
                            textAnchor="middle"
                            className="fill-blue-600 text-xs font-medium"
                            transform={`rotate(-90, ${displayX - 8}, ${displayY + displayHeight / 2})`}
                          >
                            {position.height.toFixed(0)}mm
                          </text>
                          
                          {/* Coordinate */}
                          <text
                            x={displayX + 2}
                            y={displayY + displayHeight - 2}
                            className="fill-yellow-300 text-xs font-mono font-bold"
                            style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.8)' }}
                          >
                            ({position.x.toFixed(0)},{position.y.toFixed(0)})
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
                          {position.width.toFixed(0)}mm × {position.height.toFixed(0)}mm
                        </div>
                        <div className="text-xs font-semibold text-green-600">Posizione:</div>
                        <div className="text-xs font-mono">
                          X: {position.x.toFixed(0)}mm, Y: {position.y.toFixed(0)}mm
                        </div>
                        <div className="text-xs text-gray-500">
                          Area: {(position.width * position.height / 100).toFixed(1)}cm²
                        </div>
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              )
            })}
          </svg>
          
          {/* ✅ FIXED: Pannello informazioni */}
          <div className="absolute top-2 right-2 bg-blue-50/95 backdrop-blur-sm rounded px-3 py-2 text-xs border border-blue-200">
            <div className="font-semibold text-blue-800 mb-1">📐 Informazioni Tecniche</div>
            <div className="space-y-1 text-blue-700">
              <div><strong>Autoclave:</strong> {layoutData.autoclave.lunghezza}×{layoutData.autoclave.larghezza_piano}mm</div>
              <div><strong>Scala:</strong> 1:{Math.round(1/svgDimensions.scale)}</div>
              <div><strong>Tools:</strong> {layoutData.posizioni_tool.length} posizionati</div>
              <div><strong>Zoom:</strong> {Math.round(viewport.zoom * 100)}%</div>
              {layoutData.posizioni_tool.length > 0 && (
                <div className="border-t border-blue-300 pt-1 mt-1">
                  <div className="font-medium">Tool selezionato:</div>
                  {selectedOdl ? (
                    <>
                      <div>ID: {selectedOdl}</div>
                      <div>Clic per dettagli</div>
                    </>
                  ) : (
                    <div className="text-gray-600">Nessuno</div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* Controlli viewport */}
          <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-sm rounded px-2 py-1 text-xs text-gray-600">
            Zoom: {Math.round(viewport.zoom * 100)}% • Pan: {Math.round(viewport.panX)}, {Math.round(viewport.panY)}
          </div>
        </div>

        {/* ✅ FIXED: Statistiche finali */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <div className="font-semibold text-blue-600">
              {((layoutData.area_utilizzata / layoutData.area_totale) * 100).toFixed(1)}%
            </div>
            <div className="text-muted-foreground">Efficienza</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-green-600">{layoutData.posizioni_tool.length}</div>
            <div className="text-muted-foreground">Tools Posizionati</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-orange-600">
              {(layoutData.posizioni_tool.reduce((acc, pos) => acc + (pos.width * pos.height / 100), 0)).toFixed(1)}cm²
            </div>
            <div className="text-muted-foreground">Area Utilizzata</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-purple-600">
              {layoutData.valvole_utilizzate}/{layoutData.valvole_totali}
            </div>
            <div className="text-muted-foreground">Valvole</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 