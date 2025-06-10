'use client'

import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react'
import { Card } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { 
  Maximize2, 
  Minimize2, 
  Grid, 
  Move, 
  Info, 
  Quote,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  MousePointer
} from 'lucide-react'

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

interface NestingCanvasV2Props {
  canvasWidth: number
  canvasHeight: number
  toolPositions: ToolPosition[]
  planeAssignments?: Record<string, number>
  isFullscreen?: boolean
  onToggleFullscreen?: () => void
  onToolSelect?: (odlId: number | null) => void
  className?: string
}

// Hook personalizzato per resize viewport con debounce
const useViewportResize = (isFullscreen: boolean, canvasWidth: number, canvasHeight: number, zoom: number) => {
  const [viewport, setViewport] = useState(() => {
    if (typeof window === 'undefined') return { width: 800, height: 600 }
    
    if (isFullscreen) {
      return {
        width: Math.min(window.innerWidth - 100, canvasWidth * zoom),
        height: Math.min(window.innerHeight - 200, canvasHeight * zoom)
      }
    }
    return {
      width: Math.min(800, canvasWidth * zoom),
      height: Math.min(600, canvasHeight * zoom)
    }
  })

  useEffect(() => {
    if (typeof window === 'undefined') return

    // PERF: debounced resize handler (16ms per 60fps)
    let resizeTimeout: NodeJS.Timeout
    const handleResize = () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(() => {
        if (isFullscreen) {
          setViewport({
            width: Math.min(window.innerWidth - 100, canvasWidth * zoom),
            height: Math.min(window.innerHeight - 200, canvasHeight * zoom)
          })
        } else {
          setViewport({
            width: Math.min(800, canvasWidth * zoom),
            height: Math.min(600, canvasHeight * zoom)
          })
        }
      }, 16)
    }

    window.addEventListener('resize', handleResize)
    
    // Aggiorna subito quando cambiano fullscreen, zoom o dimensioni
    handleResize()
    
    return () => {
      window.removeEventListener('resize', handleResize)
      clearTimeout(resizeTimeout)
    }
  }, [isFullscreen, canvasWidth, canvasHeight, zoom])

  return viewport
}

const NestingCanvasV2: React.FC<NestingCanvasV2Props> = ({
  canvasWidth,
  canvasHeight,
  toolPositions,
  planeAssignments = {},
  isFullscreen = false,
  onToggleFullscreen,
  onToolSelect,
  className = ''
}) => {
  const [showGrid, setShowGrid] = useState(true)
  const [showRuler, setShowRuler] = useState(true)
  const [showQuotes, setShowQuotes] = useState(false)
  const [showInfo, setShowInfo] = useState(true)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  
  const canvasRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const zoomTimeoutRef = useRef<NodeJS.Timeout>()
  const panTimeoutRef = useRef<NodeJS.Timeout>()

  // Usa hook personalizzato per viewport con performance ottimizzate
  const viewport = useViewportResize(isFullscreen, canvasWidth, canvasHeight, zoom)

  // PERF: debounce per zoom/pan operations (16ms per 60fps)
  const debouncedSetZoom = useCallback((newZoom: number) => {
    if (zoomTimeoutRef.current) clearTimeout(zoomTimeoutRef.current)
    zoomTimeoutRef.current = setTimeout(() => {
      setZoom(newZoom)
    }, 16)
  }, [])

  const debouncedSetPan = useCallback((newPan: { x: number, y: number }) => {
    if (panTimeoutRef.current) clearTimeout(panTimeoutRef.current)
    panTimeoutRef.current = setTimeout(() => {
      setPan(newPan)
    }, 16)
  }, [])



  // PERF: memoized viewport bounds per virtualizzazione
  const viewportBounds = useMemo(() => {
    const scaledPan = { x: pan.x / zoom, y: pan.y / zoom }
    return {
      left: -scaledPan.x,
      top: -scaledPan.y,
      right: -scaledPan.x + viewport.width / zoom,
      bottom: -scaledPan.y + viewport.height / zoom
    }
  }, [pan, zoom, viewport])

  // PERF: virtualization per rendering se >100 tool
  const visibleTools = useMemo(() => {
    if (toolPositions.length <= 100) {
      return toolPositions // Non virtualizzare se <=100 tool
    }
    
    // PERF: virtualized - renderizza solo tool visibili nel viewport
    return toolPositions.filter(tool => {
      return !(tool.x + tool.width < viewportBounds.left ||
               tool.x > viewportBounds.right ||
               tool.y + tool.height < viewportBounds.top ||
               tool.y > viewportBounds.bottom)
    })
  }, [toolPositions, viewportBounds])

  // Gestione zoom con wheel + Ctrl
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (!e.ctrlKey && !e.metaKey) return
    
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    const newZoom = Math.max(0.1, Math.min(5, zoom * delta))
    debouncedSetZoom(newZoom)
  }, [zoom, debouncedSetZoom])

  // Gestione zoom con pulsanti
  const handleZoomIn = useCallback(() => {
    const newZoom = Math.min(zoom * 1.2, 5)
    debouncedSetZoom(newZoom)
  }, [zoom, debouncedSetZoom])

  const handleZoomOut = useCallback(() => {
    const newZoom = Math.max(zoom / 1.2, 0.1)
    debouncedSetZoom(newZoom)
  }, [zoom, debouncedSetZoom])

  const handleResetView = useCallback(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }, [])

  // Gestione drag per pan con debounce
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target === svgRef.current || (e.target as Element).closest('svg rect[data-background]')) {
      setIsDragging(true)
      setDragStart({ 
        x: e.clientX - pan.x, 
        y: e.clientY - pan.y 
      })
    }
  }, [pan])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    // Aggiorna posizione mouse per debug
    if (svgRef.current) {
      const rect = svgRef.current.getBoundingClientRect()
      const x = (e.clientX - rect.left - pan.x) / zoom
      const y = (e.clientY - rect.top - pan.y) / zoom
      setMousePos({ x, y })
    }

    if (!isDragging) return
    
    const newPan = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    }
    debouncedSetPan(newPan)
  }, [isDragging, dragStart, zoom, pan.x, pan.y, debouncedSetPan])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Tool selection con callback
  const handleToolSelect = useCallback((odlId: number | null) => {
    setSelectedTool(odlId)
    if (onToolSelect) {
      onToolSelect(odlId)
    }
  }, [onToolSelect])

  // Genera la griglia (10mm come specificato)
  const GridPattern = useMemo(() => {
    if (!showGrid) return null
    
    const gridSize = 10 // 10mm come richiesto nel contract
    const lines = []
    
    // PERF: genera solo linee visibili nel viewport per performance
    const startX = Math.max(0, Math.floor(viewportBounds.left / gridSize) * gridSize)
    const endX = Math.min(canvasWidth, Math.ceil(viewportBounds.right / gridSize) * gridSize)
    const startY = Math.max(0, Math.floor(viewportBounds.top / gridSize) * gridSize)
    const endY = Math.min(canvasHeight, Math.ceil(viewportBounds.bottom / gridSize) * gridSize)
    
    // Linee verticali
    for (let x = startX; x <= endX; x += gridSize) {
      lines.push(
        <line
          key={`v-${x}`}
          x1={x}
          y1={Math.max(0, startY)}
          x2={x}
          y2={Math.min(canvasHeight, endY)}
          stroke="#e5e7eb"
          strokeWidth={0.5 / zoom}
          strokeDasharray={`${2 / zoom},${2 / zoom}`}
        />
      )
    }
    
    // Linee orizzontali
    for (let y = startY; y <= endY; y += gridSize) {
      lines.push(
        <line
          key={`h-${y}`}
          x1={Math.max(0, startX)}
          y1={y}
          x2={Math.min(canvasWidth, endX)}
          y2={y}
          stroke="#e5e7eb"
          strokeWidth={0.5 / zoom}
          strokeDasharray={`${2 / zoom},${2 / zoom}`}
        />
      )
    }
    
    return <g>{lines}</g>
  }, [showGrid, viewportBounds, canvasWidth, canvasHeight, zoom])

  // Righello con unità in mm
  const Ruler = useMemo(() => {
    if (!showRuler) return null
    
    const ticks = []
    const tickInterval = zoom > 2 ? 50 : zoom > 1 ? 100 : 200 // Adattivo in base al zoom
    
    // PERF: genera solo tick visibili
    const startX = Math.max(0, Math.floor(viewportBounds.left / tickInterval) * tickInterval)
    const endX = Math.min(canvasWidth, Math.ceil(viewportBounds.right / tickInterval) * tickInterval)
    const startY = Math.max(0, Math.floor(viewportBounds.top / tickInterval) * tickInterval)
    const endY = Math.min(canvasHeight, Math.ceil(viewportBounds.bottom / tickInterval) * tickInterval)
    
    // Tick orizzontali (asse X)
    for (let x = startX; x <= endX; x += tickInterval) {
      ticks.push(
        <g key={`h-tick-${x}`}>
          <line 
            x1={x} y1={-15} x2={x} y2={0} 
            stroke="#666" strokeWidth={1 / zoom} 
          />
          <text 
            x={x} y={-18} 
            fontSize={12 / zoom} 
            fill="#666" 
            textAnchor="middle"
          >
            {x}mm
          </text>
        </g>
      )
    }
    
    // Tick verticali (asse Y)
    for (let y = startY; y <= endY; y += tickInterval) {
      ticks.push(
        <g key={`v-tick-${y}`}>
          <line 
            x1={-15} y1={y} x2={0} y2={y} 
            stroke="#666" strokeWidth={1 / zoom} 
          />
          <text 
            x={-18} y={y + 4 / zoom} 
            fontSize={12 / zoom} 
            fill="#666" 
            textAnchor="end"
          >
            {y}mm
          </text>
        </g>
      )
    }
    
    return <g>{ticks}</g>
  }, [showRuler, viewportBounds, canvasWidth, canvasHeight, zoom])

  // PERF: memoized tool rendering
  const renderedTools = useMemo(() => {
    return visibleTools.map((tool, index) => {
      const isSelected = selectedTool === tool.odl_id
      const fillColor = isSelected ? '#3b82f6' : '#10b981'
      const strokeColor = isSelected ? '#1d4ed8' : '#059669'
      
      return (
        <g key={`tool-${tool.odl_id}`}>
          <rect
            x={tool.x}
            y={tool.y}
            width={tool.width}
            height={tool.height}
            fill={fillColor}
            fillOpacity={0.7}
            stroke={strokeColor}
            strokeWidth={2 / zoom}
            style={{ cursor: 'pointer' }}
            onClick={() => handleToolSelect(isSelected ? null : tool.odl_id)}
          />
          
          {/* Etichetta tool */}
          {showInfo && zoom > 0.5 && (
            <g>
              <text
                x={tool.x + tool.width / 2}
                y={tool.y + tool.height / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={12 / zoom}
                fill="white"
                fontWeight="bold"
              >
                ODL {tool.odl_id}
              </text>
              
              {tool.part_number && zoom > 0.8 && (
                <text
                  x={tool.x + tool.width / 2}
                  y={tool.y + tool.height / 2 + 14 / zoom}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={10 / zoom}
                  fill="white"
                >
                  {tool.part_number}
                </text>
              )}
            </g>
          )}
          
          {/* Quote dimensionali */}
          {showQuotes && isSelected && (
            <g stroke="#ef4444" fill="#ef4444" fontSize={10 / zoom}>
              {/* Quota larghezza */}
              <line 
                x1={tool.x} y1={tool.y - 15 / zoom} 
                x2={tool.x + tool.width} y2={tool.y - 15 / zoom}
                strokeWidth={1 / zoom}
              />
              <text 
                x={tool.x + tool.width / 2} 
                y={tool.y - 20 / zoom} 
                textAnchor="middle"
              >
                {tool.width.toFixed(0)}mm
              </text>
              
              {/* Quota altezza */}
              <line 
                x1={tool.x - 15 / zoom} y1={tool.y} 
                x2={tool.x - 15 / zoom} y2={tool.y + tool.height}
                strokeWidth={1 / zoom}
              />
              <text 
                x={tool.x - 20 / zoom} 
                y={tool.y + tool.height / 2} 
                textAnchor="middle"
                transform={`rotate(-90, ${tool.x - 20 / zoom}, ${tool.y + tool.height / 2})`}
              >
                {tool.height.toFixed(0)}mm
              </text>
            </g>
          )}
        </g>
      )
    })
  }, [visibleTools, selectedTool, showInfo, showQuotes, zoom, handleToolSelect])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (zoomTimeoutRef.current) clearTimeout(zoomTimeoutRef.current)
      if (panTimeoutRef.current) clearTimeout(panTimeoutRef.current)
    }
  }, [])

  return (
    <Card className={`relative ${className}`}>
      {/* Toolbar controlli */}
      <div className="flex items-center justify-between p-3 border-b bg-gray-50">
        <div className="flex items-center gap-2">
          <Button
            variant={showGrid ? "default" : "outline"}
            size="sm"
            onClick={() => setShowGrid(!showGrid)}
            title="Toggle Grid (10mm)"
          >
            <Grid className="h-4 w-4" />
          </Button>
          
          <Button
            variant={showRuler ? "default" : "outline"}
            size="sm"
            onClick={() => setShowRuler(!showRuler)}
            title="Toggle Ruler (mm)"
          >
            <Move className="h-4 w-4" />
          </Button>
          
          <Button
            variant={showQuotes ? "default" : "outline"}
            size="sm"
            onClick={() => setShowQuotes(!showQuotes)}
            title="Toggle Dimensions"
          >
            <Quote className="h-4 w-4" />
          </Button>
          
          <Button
            variant={showInfo ? "default" : "outline"}
            size="sm"
            onClick={() => setShowInfo(!showInfo)}
            title="Toggle Labels"
          >
            <Info className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut} title="Zoom Out">
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <Badge variant="outline" className="px-2 py-1 min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </Badge>
          
          <Button variant="outline" size="sm" onClick={handleZoomIn} title="Zoom In">
            <ZoomIn className="h-4 w-4" />
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleResetView} title="Reset View">
            <RotateCcw className="h-4 w-4" />
          </Button>
          
          {onToggleFullscreen && (
            <Button variant="outline" size="sm" onClick={onToggleFullscreen} title="Toggle Fullscreen">
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>

      {/* Performance info */}
      {toolPositions.length > 100 && (
        <div className="px-3 py-1 text-xs text-gray-600 bg-blue-50 border-b">
          ⚡ Virtualized: showing {visibleTools.length} of {toolPositions.length} tools (optimized for 60+ FPS)
        </div>
      )}

      {/* Canvas area */}
      <div 
        ref={canvasRef}
        className="overflow-hidden bg-white select-none"
        style={{ 
          width: viewport.width,
          height: viewport.height,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <svg
          ref={svgRef}
          width={viewport.width}
          height={viewport.height}
          viewBox={`${-pan.x / zoom} ${-pan.y / zoom} ${viewport.width / zoom} ${viewport.height / zoom}`}
        >
          {/* Background */}
          <rect 
            data-background="true"
            x={0} y={0} 
            width={canvasWidth} 
            height={canvasHeight}
            fill="#f9fafb" 
            stroke="#d1d5db" 
            strokeWidth={2 / zoom}
          />
          
          {/* Griglia */}
          {GridPattern}
          
          {/* Righello */}
          {Ruler}
          
          {/* PERF: virtualized tool rendering */}
          {renderedTools}
        </svg>
      </div>

      {/* Debug coordinate mouse */}
      {showInfo && (
        <div className="absolute top-16 left-4 bg-black/75 text-white px-2 py-1 rounded text-xs font-mono">
          x: {mousePos.x.toFixed(0)}mm, y: {mousePos.y.toFixed(0)}mm
        </div>
      )}

      {/* Info tool selezionato */}
      {selectedTool && (
        <div className="absolute bottom-4 right-4 bg-white p-3 rounded-lg shadow-lg border max-w-xs">
          {(() => {
            const tool = toolPositions.find(t => t.odl_id === selectedTool)
            if (!tool) return null
            
            return (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <MousePointer className="h-4 w-4" />
                  <h4 className="font-semibold">ODL {tool.odl_id}</h4>
                </div>
                {tool.part_number && <p className="text-sm text-gray-600">{tool.part_number}</p>}
                {tool.tool_nome && <p className="text-sm text-gray-600">{tool.tool_nome}</p>}
                <div className="text-sm space-y-1">
                  <div>Posizione: ({tool.x.toFixed(0)}, {tool.y.toFixed(0)}) mm</div>
                  <div>Dimensioni: {tool.width.toFixed(0)} × {tool.height.toFixed(0)} mm</div>
                  <div>Peso: {tool.peso.toFixed(1)} kg</div>
                  {tool.rotated && <Badge variant="outline" className="text-xs">Ruotato</Badge>}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  Click per aprire drawer dettagli
                </div>
              </div>
            )
          })()}
        </div>
      )}

      {/* Istruzioni controlli */}
      <div className="absolute bottom-4 left-4 bg-black/75 text-white px-3 py-2 rounded text-xs space-y-1">
        <div>🖱️ Drag: Pan camera</div>
        <div>⌨️ Ctrl+Wheel: Zoom</div>
        <div>🎯 Click tool: Select/Details</div>
      </div>
    </Card>
  )
}

export default NestingCanvasV2 