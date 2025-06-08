'use client'

import React, { useEffect, useState, useCallback, useRef, useLayoutEffect } from 'react'
import { Package, AlertCircle, CheckCircle, Download, ZoomIn, ZoomOut } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

import { useToast } from '@/components/ui/use-toast'
import CanvasWrapper, { 
  Layer, 
  Rect, 
  Text, 
  Group, 
  Line, 
  CanvasLoadingPlaceholder,
  useClientMount 
} from '@/shared/components/canvas/CanvasWrapper'

// ✨ Interfacce aggiornate e semplificate
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
  excluded?: boolean // Flag per tool esclusi nel batch
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}



interface NestingCanvasProps {
  batchData: {
    configurazione_json: {
      canvas_width: number
      canvas_height: number
      tool_positions: ToolPosition[]
      autoclave_mm?: [number, number]
      bounding_px?: [number, number]
    } | null
    autoclave: AutoclaveInfo | undefined
    metrics?: {
      efficiency_percentage?: number
    }
    id?: string
  }
  className?: string
}

// ✨ Normalizzazione dati tool
const normalizeToolData = (tool: ToolPosition): ToolPosition => {
  return {
    ...tool,
    x: Number(tool.x) || 0,
    y: Number(tool.y) || 0,
    width: Number(tool.width) || 50,
    height: Number(tool.height) || 50,
    peso: Number(tool.peso) || 0,
    rotated: Boolean(tool.rotated === true || tool.rotated === 'true'),
    excluded: Boolean(tool.excluded)
  }
}

// ✨ Componente per griglia del canvas con righello
const GridLayer: React.FC<{ 
  width: number, 
  height: number, 
  showRuler?: boolean 
}> = ({ width, height, showRuler = true }) => {
  const gridSpacing = 100 // Spaziatura griglia in mm (10cm)
  const lines: number[] = []
  
  // Linee verticali
  for (let x = 0; x <= width; x += gridSpacing) {
    lines.push(x, 0, x, height)
  }
  
  // Linee orizzontali
  for (let y = 0; y <= height; y += gridSpacing) {
    lines.push(0, y, width, y)
  }
  
  return (
    <Group>
      {/* Griglia principale */}
      <Line
        points={lines}
        stroke="#e5e7eb"
        strokeWidth={0.5}
        opacity={0.5}
      />
      
      {/* Righello orizzontale (se abilitato) */}
      {showRuler && (
        <Group>
          {/* Scala orizzontale ogni 100mm (limitata per performance) */}
          {Array.from({ length: Math.min(Math.floor(width / gridSpacing) + 1, 25) }, (_, i) => {
            const x = i * gridSpacing
            return (
              <Group key={`h-${i}`}>
                {/* Linea di misurazione */}
                <Line
                  points={[x, 0, x, 20]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {/* Testo misurazione */}
                {i % 2 === 0 && ( // Mostra etichette solo ogni 2 linee per ridurre il clutter
                  <Text
                    x={x + 5}
                    y={5}
                    text={`${(x / 10).toFixed(0)}cm`}
                    fontSize={10}
                    fill="#374151"
                    opacity={0.8}
                  />
                )}
              </Group>
            )
          })}
          
          {/* Scala verticale ogni 100mm (limitata per performance) */}
          {Array.from({ length: Math.min(Math.floor(height / gridSpacing) + 1, 30) }, (_, i) => {
            const y = i * gridSpacing
            return (
              <Group key={`v-${i}`}>
                {/* Linea di misurazione */}
                <Line
                  points={[0, y, 20, y]}
                  stroke="#374151"
                  strokeWidth={1}
                />
                {/* Testo misurazione */}
                {i % 2 === 0 && ( // Mostra etichette solo ogni 2 linee per ridurre il clutter
                  <Text
                    x={5}
                    y={y + 5}
                    text={`${(y / 10).toFixed(0)}cm`}
                    fontSize={10}
                    fill="#374151"
                    opacity={0.8}
                    rotation={-90}
                  />
                )}
              </Group>
            )
          })}
        </Group>
      )}
    </Group>
  )
}

// ✨ Componente tool con colori basati su stato e animazioni
const ToolRect: React.FC<{ 
  tool: ToolPosition, 
  onClick?: () => void,
  isSelected?: boolean,
  autoclaveWidth: number,
  autoclaveHeight: number,
  showTooltips?: boolean
}> = ({ tool, onClick, isSelected = false, autoclaveWidth, autoclaveHeight, showTooltips = true }) => {
  
  // Controlla se il tool è fuori dai bounds dell'autoclave
  const isOutOfBoundsX = tool.x + tool.width > autoclaveWidth
  const isOutOfBoundsY = tool.y + tool.height > autoclaveHeight
  const isOutOfBounds = isOutOfBoundsX || isOutOfBoundsY
  
  // Determinazione colore basato su stato + debug out of bounds
  const color = tool.excluded 
    ? '#ef4444' // Rosso per tool esclusi
    : isOutOfBounds
    ? '#f97316' // Arancione per tool fuori bounds
    : tool.rotated 
    ? '#eab308' // Giallo per tool ruotati
    : '#22c55e' // Verde per tool validi
  
  const strokeColor = tool.excluded 
    ? '#dc2626' 
    : isOutOfBounds
    ? '#ea580c'
    : tool.rotated 
    ? '#ca8a04' 
    : '#16a34a'

  const shadowConfig = isSelected 
    ? { shadowColor: '#000', shadowOpacity: 0.3, shadowOffsetX: 2, shadowOffsetY: 2, shadowBlur: 4 }
    : {}

  // Calcolo dimensioni font responsive
  const fontSize = Math.max(8, Math.min(tool.width, tool.height) * 0.15)
  
  return (
    <Group>
      {/* Ombra per tool selezionato */}
      {isSelected && (
        <Rect
          x={tool.x + 2}
          y={tool.y + 2}
          width={tool.width}
          height={tool.height}
          fill="#000"
          opacity={0.2}
          cornerRadius={2}
        />
      )}
      
      {/* Rettangolo principale del tool */}
      <Rect
        x={tool.x}
        y={tool.y}
        width={tool.width}
        height={tool.height}
        fill={color}
        stroke={strokeColor}
        strokeWidth={isSelected ? 3 : isOutOfBounds ? 2 : 1}
        opacity={tool.excluded ? 0.6 : 0.9}
        cornerRadius={2}
        onClick={onClick}
        onTap={onClick}
        {...shadowConfig}
      />
      
      {/* Indicatore di errore per tool fuori bounds */}
      {isOutOfBounds && (
        <Text
          x={tool.x + tool.width / 2}
          y={tool.y - 15}
          text="⚠️ OUT"
          fontSize={10}
          fill="#dc2626"
          fontStyle="bold"
          align="center"
        />
      )}
      
      {/* Testo con ID tool - più visibile */}
      <Text
        x={tool.x + tool.width / 2}
        y={tool.y + tool.height / 2}
        text={`ODL ${tool.odl_id}`}
        fontSize={fontSize}
        fill="#000"
        fontStyle="bold"
        align="center"
        verticalAlign="middle"
        onClick={onClick}
        onTap={onClick}
      />
      
      {/* Testo peso sotto l'ID (condizionale) */}
      {showTooltips && tool.height > 30 && (
        <Text
          x={tool.x + tool.width / 2}
          y={tool.y + tool.height / 2 + fontSize + 2}
          text={`${tool.peso}kg`}
          fontSize={Math.max(6, fontSize * 0.7)}
          fill="#000"
          opacity={0.8}
          align="center"
          verticalAlign="middle"
          onClick={onClick}
          onTap={onClick}
        />
      )}
      
      {/* Indicatore rotazione migliorato */}
      {tool.rotated && (
        <Group>
          <Rect
            x={tool.x + tool.width - 20}
            y={tool.y + 2}
            width={16}
            height={16}
            fill="#fff"
            stroke={strokeColor}
            strokeWidth={1}
            cornerRadius={8}
            opacity={0.9}
          />
          <Text
            x={tool.x + tool.width - 12}
            y={tool.y + 10}
            text="↻"
            fontSize={10}
            fill={strokeColor}
            fontStyle="bold"
            align="center"
            verticalAlign="middle"
          />
        </Group>
      )}
      
      {/* Indicatore esclusione */}
      {tool.excluded && (
        <Group>
          <Line
            points={[tool.x, tool.y, tool.x + tool.width, tool.y + tool.height]}
            stroke="#dc2626"
            strokeWidth={3}
            opacity={0.8}
          />
          <Line
            points={[tool.x + tool.width, tool.y, tool.x, tool.y + tool.height]}
            stroke="#dc2626"
            strokeWidth={3}
            opacity={0.8}
          />
        </Group>
      )}
    </Group>
  )
}

// ✨ Header informativo autoclave
const AutoclaveHeader: React.FC<{ 
  autoclave: AutoclaveInfo, 
  efficiency: number 
}> = ({ autoclave, efficiency }) => {
  
  // Colore efficienza basato su livello
  const getEfficiencyColor = (eff: number) => {
    if (eff >= 80) return 'text-green-600'
    if (eff >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }
  
  return (
    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg mb-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-800">{autoclave.nome}</h3>
        <p className="text-sm text-gray-600">
          {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
        </p>
      </div>
      <div className="text-right">
        <div className={`text-2xl font-bold ${getEfficiencyColor(efficiency)}`}>
          {efficiency.toFixed(1)}%
        </div>
        <p className="text-sm text-gray-600">Efficienza</p>
      </div>
    </div>
  )
}

// ✨ Legenda colori e statistiche
const ColorLegend: React.FC<{ 
  toolPositions: ToolPosition[],
  autoclaveArea: number 
}> = ({ toolPositions, autoclaveArea }) => {
  // Calcolo statistiche
  const validTools = toolPositions.filter(t => !t.excluded)
  const rotatedTools = toolPositions.filter(t => t.rotated && !t.excluded)
  const excludedTools = toolPositions.filter(t => t.excluded)
  
  const totalToolArea = validTools.reduce((sum, tool) => sum + (tool.width * tool.height), 0)
  const occupancyPercentage = ((totalToolArea / autoclaveArea) * 100).toFixed(1)
  const totalWeight = validTools.reduce((sum, tool) => sum + tool.peso, 0)

  return (
    <div className="space-y-3">
      {/* Legenda colori */}
      <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded border border-green-600"></div>
          <span className="text-sm">Tool Validi ({validTools.length})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 rounded border border-yellow-600"></div>
          <span className="text-sm">Tool Ruotati ({rotatedTools.length})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded border border-red-600"></div>
          <span className="text-sm">Tool Esclusi ({excludedTools.length})</span>
        </div>
      </div>
      
      {/* Statistiche */}
      <div className="grid grid-cols-2 gap-3 p-3 bg-blue-50 rounded-lg">
        <div className="text-center">
          <div className="text-xl font-bold text-blue-700">{occupancyPercentage}%</div>
          <div className="text-xs text-gray-600">Occupazione</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-green-700">{totalWeight.toFixed(1)}</div>
          <div className="text-xs text-gray-600">Peso (kg)</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-purple-700">{validTools.length}</div>
          <div className="text-xs text-gray-600">Tool Caricati</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-gray-700">{(totalToolArea / 1000000).toFixed(2)}</div>
          <div className="text-xs text-gray-600">Area (m²)</div>
        </div>
      </div>
    </div>
  )
}

// ✨ Canvas principale responsive e zoomabile
const ResponsiveCanvas: React.FC<{
  toolPositions: ToolPosition[]
  autoclave: AutoclaveInfo
  onToolClick: (toolId: number) => void
}> = ({ toolPositions, autoclave, onToolClick }) => {
  const stageRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [zoom, setZoom] = useState<number>(1)
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [isDragging, setIsDragging] = useState<boolean>(false)
  const [stagePos, setStagePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [showGrid, setShowGrid] = useState<boolean>(true)
  const [showRuler, setShowRuler] = useState<boolean>(true)
  const [showDimensions, setShowDimensions] = useState<boolean>(true)
  const [showTooltips, setShowTooltips] = useState<boolean>(true)
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null)
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false)
  const { toast } = useToast()
  
  // Dimensioni autoclave in mm
  const autoclaveWidth = autoclave.lunghezza || 2000
  const autoclaveHeight = autoclave.larghezza_piano || 1200
  const marginPx = 10
  
  // Verifica coerenza dimensioni autoclave vs configurazione JSON (solo in dev)
  if (process.env.NODE_ENV === 'development') {
    console.log('📐 Analisi dimensioni:', {
      autoclave: { width: autoclaveWidth, height: autoclaveHeight },
      toolCount: toolPositions.length
    })
  }
  
  // Auto-fit iniziale migliorato
  useLayoutEffect(() => {
    if (!containerRef.current) return
    
    // Aspetta che il container sia completamente renderizzato
    const timer = setTimeout(() => {
      const containerWidth = containerRef.current?.offsetWidth || 800
      const containerHeight = containerRef.current?.offsetHeight || 600
      
      console.log(`📐 Container: ${containerWidth}x${containerHeight}, Autoclave: ${autoclaveWidth}x${autoclaveHeight}`)
      
      // Riduci le dimensioni del container per il padding
      const availableWidth = containerWidth - marginPx * 4
      const availableHeight = containerHeight - marginPx * 4
      
      const scaleX = availableWidth / autoclaveWidth
      const scaleY = availableHeight / autoclaveHeight
      const initialScale = Math.min(scaleX, scaleY, 0.8) // Massimo 80% per lasciare spazio
      
             console.log(`🔍 Scale calcolata: ${initialScale} (X: ${scaleX}, Y: ${scaleY})`)
        setZoom(initialScale)
        
        // Centra il canvas al caricamento
        const scaledWidth = autoclaveWidth * initialScale
        const scaledHeight = autoclaveHeight * initialScale
        const centerX = (containerWidth - scaledWidth) / 2
        const centerY = (containerHeight - scaledHeight) / 2
        
        setStagePos({ x: centerX, y: centerY })
        console.log(`📍 Canvas centrato: (${centerX}, ${centerY})`)
     }, 100)
    
    return () => clearTimeout(timer)
  }, [autoclaveWidth, autoclaveHeight])

  // Controlli zoom
  const handleZoomIn = () => setZoom(prev => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setZoom(prev => Math.max(prev / 1.2, 0.1))
  const handleZoomReset = () => {
    if (!containerRef.current) return
    
    const containerWidth = containerRef.current.offsetWidth
    const containerHeight = containerRef.current.offsetHeight
    
    // Calcola scale per centrare l'autoclave
    const availableWidth = containerWidth - marginPx * 4
    const availableHeight = containerHeight - marginPx * 4
    
    const scaleX = availableWidth / autoclaveWidth
    const scaleY = availableHeight / autoclaveHeight
    const optimalScale = Math.min(scaleX, scaleY, 0.8)
    
    setZoom(optimalScale)
    
    // Centra il canvas
    const scaledWidth = autoclaveWidth * optimalScale
    const scaledHeight = autoclaveHeight * optimalScale
    const centerX = (containerWidth - scaledWidth) / 2
    const centerY = (containerHeight - scaledHeight) / 2
    
    setStagePos({ x: centerX, y: centerY })
  }

  // Export PNG
  const handleExportPNG = useCallback(() => {
    if (stageRef.current) {
      try {
        const dataURL = stageRef.current.toDataURL({
          mimeType: 'image/png',
          quality: 1,
          pixelRatio: 2
        })
        
        const link = document.createElement('a')
        link.download = `nesting_layout_${new Date().toISOString().slice(0, 10)}.png`
        link.href = dataURL
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        toast({
          title: "✅ Export completato",
          description: "Layout salvato come PNG"
        })
      } catch (error) {
        console.error('Export error:', error)
        toast({
          title: "❌ Errore Export",
          description: "Impossibile salvare l'immagine",
          variant: "destructive"
        })
      }
    }
  }, [toast])

  // Click tool con tooltip e selezione
  const handleToolClick = useCallback((toolId: number) => {
    setSelectedTool(prev => prev === toolId ? null : toolId)
    const tool = toolPositions.find(t => t.odl_id === toolId)
    if (tool) {
      onToolClick(toolId)
      
      toast({
        title: `🔧 Tool ODL ${toolId}`,
        description: (
          <div className="space-y-1 text-sm">
            <p><strong>Parte:</strong> {tool.part_number || 'N/A'}</p>
            <p><strong>Nome:</strong> {tool.tool_nome || 'N/A'}</p>
            <p><strong>Dimensioni:</strong> {tool.width} × {tool.height} mm</p>
            <p><strong>Peso:</strong> {tool.peso} kg</p>
            <p><strong>Posizione:</strong> X: {Math.round(tool.x)}, Y: {Math.round(tool.y)}</p>
            <p><strong>Rotazione:</strong> {tool.rotated ? 'Sì ↻' : 'No'}</p>
            {tool.excluded && <p className="text-red-600 font-semibold">⚠️ Escluso dal batch</p>}
          </div>
        ),
        duration: 4000
      })
    }
  }, [toolPositions, onToolClick, toast])

  return (
    <div className="space-y-4">
      {/* Controlli zoom e visualizzazione */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 min-w-[60px]">
              {(zoom * 100).toFixed(0)}%
            </span>
            <input
              type="range"
              value={zoom}
              onChange={(e) => setZoom(parseFloat(e.target.value))}
              min={0.1}
              max={3}
              step={0.1}
              className="w-32 h-2 bg-gray-200 rounded-lg"
            />
          </div>
          <Button variant="outline" size="sm" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleZoomReset}>
            Auto-Fit
          </Button>
        </div>
        
        {/* Controlli visualizzazione */}
        <div className="flex items-center gap-2">
          {/* Indicatore coordinate mouse migliorato */}
          {mousePos && (
            <div className="px-3 py-1 bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-md text-xs font-mono text-blue-800 shadow-sm">
              📍 X: {mousePos.x}mm, Y: {mousePos.y}mm
            </div>
          )}
          
          {/* Controlli visualizzazione raggruppati */}
          <div className="flex items-center gap-1 p-1 bg-gray-50 rounded-lg border">
            <Button 
              variant={showGrid ? "default" : "ghost"} 
              size="sm" 
              onClick={() => setShowGrid(!showGrid)}
              className="h-8 px-2"
            >
              <svg className="h-4 w-4 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M8 3v18M16 3v18M3 8h18M3 16h18"/>
              </svg>
              Griglia
            </Button>
            <Button 
              variant={showRuler ? "default" : "ghost"} 
              size="sm" 
              onClick={() => setShowRuler(!showRuler)}
              className="h-8 px-2"
            >
              <svg className="h-4 w-4 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M3 17h18a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1zM3 9h18M9 21V3"/>
              </svg>
              Righello
            </Button>
            <Button 
              variant={showDimensions ? "default" : "ghost"} 
              size="sm" 
              onClick={() => setShowDimensions(!showDimensions)}
              className="h-8 px-2"
            >
              📏 Quote
            </Button>
            <Button 
              variant={showTooltips ? "default" : "ghost"} 
              size="sm" 
              onClick={() => setShowTooltips(!showTooltips)}
              className="h-8 px-2"
            >
              💬 Info
            </Button>
          </div>
          
          {/* Controlli azioni */}
          <div className="flex items-center gap-1">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="flex items-center gap-2"
            >
              {isFullscreen ? (
                <>
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M8 3v3a2 2 0 0 1-2 2H3M21 8h-3a2 2 0 0 1-2-2V3M3 16h3a2 2 0 0 1 2 2v3M16 21v-3a2 2 0 0 1 2-2h3"/>
                  </svg>
                  Esci
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M3 7V4a1 1 0 0 1 1-1h3M21 7V4a1 1 0 0 0-1-1h-3M21 17v3a1 1 0 0 1-1 1h-3M3 17v3a1 1 0 0 0 1 1h3"/>
                  </svg>
                  Fullscreen
                </>
              )}
            </Button>
            <Button onClick={handleExportPNG} size="sm" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700">
              <Download className="h-4 w-4" />
              Esporta PNG
            </Button>
          </div>
        </div>
      </div>

      {/* Canvas container con altezza dinamica */}
      <div 
        ref={containerRef}
        className={`relative w-full border-2 rounded-lg overflow-hidden transition-all duration-300 ${
          isFullscreen 
            ? 'fixed inset-4 z-50 bg-white shadow-2xl border-gray-400' 
            : 'border-gray-300 bg-white'
        }`}
        style={isFullscreen ? {
          height: 'calc(100vh - 2rem)',
          minHeight: 'calc(100vh - 2rem)'
        } : { 
          height: `${Math.min(600, Math.max(400, autoclaveHeight * 0.3))}px`,
          minHeight: '400px'
        }}
      >
        <div 
          className="absolute top-0 left-0 w-full h-full flex items-center justify-center"
          style={{ padding: `${marginPx}px` }}
        >
          <CanvasWrapper 
            ref={stageRef}
            width={containerRef.current?.offsetWidth || 800} 
            height={containerRef.current?.offsetHeight || 600}
            onMouseMove={(e: any) => {
              const stage = e.target.getStage()
              const pointer = stage.getPointerPosition()
              if (pointer && stageRef.current) {
                // Calcola le coordinate reali del canvas
                const transform = stageRef.current.getAbsoluteTransform().copy()
                transform.invert()
                const pos = transform.point(pointer)
                
                if (pos.x >= 0 && pos.x <= autoclaveWidth && pos.y >= 0 && pos.y <= autoclaveHeight) {
                  setMousePos({ x: Math.round(pos.x), y: Math.round(pos.y) })
                } else {
                  setMousePos(null)
                }
              }
            }}
            onMouseLeave={() => setMousePos(null)}
          >
            <Layer
              scaleX={zoom}
              scaleY={zoom}
              x={stagePos.x}
              y={stagePos.y}
              draggable={true}
              onDragStart={() => setIsDragging(true)}
              onDragEnd={(e: any) => {
                setIsDragging(false)
                setStagePos({ x: e.target.x(), y: e.target.y() })
              }}
            >
              {/* Griglia con righello */}
              {showGrid && (
                <GridLayer 
                  width={autoclaveWidth} 
                  height={autoclaveHeight} 
                  showRuler={showRuler}
                />
              )}
              
              {/* 📏 DEBUG: Overlay bordo autoclave con evidenziazione rigida */}
              <Group>
                {/* Bordo autoclave principale */}
                <Rect
                  x={0}
                  y={0}
                  width={autoclaveWidth}
                  height={autoclaveHeight}
                  stroke="#2563eb"
                  strokeWidth={4}
                  dash={[10, 5]}
                  fill="transparent"
                />
                
                {/* 🧪 DEBUG: Bordo di sicurezza interno più sottile */}
                <Rect
                  x={5}
                  y={5}
                  width={autoclaveWidth - 10}
                  height={autoclaveHeight - 10}
                  stroke="#10b981"
                  strokeWidth={1}
                  opacity={0.5}
                  fill="transparent"
                />
                

                
                {/* Etichette dimensioni condizionali */}
                {showDimensions && (
                  <>
                    <Text
                      x={autoclaveWidth / 2}
                      y={-25}
                      text={`${autoclaveWidth}mm`}
                      fontSize={14}
                      fill="#2563eb"
                      fontStyle="bold"
                      align="center"
                    />
                    
                    <Text
                      x={-35}
                      y={autoclaveHeight / 2}
                      text={`${autoclaveHeight}mm`}
                      fontSize={14}
                      fill="#2563eb"
                      fontStyle="bold"
                      align="center"
                      rotation={-90}
                    />
                  </>
                )}
                

              </Group>
              
              {/* Indicatore origine (0,0) */}
              <Line
                points={[0, 0, 20, 15, 15, 20, 0, 0]}
                fill="#6b7280"
                closed
              />
              
              {/* Tool posizionati */}
              {toolPositions.map((tool) => (
                <ToolRect
                  key={tool.odl_id}
                  tool={tool}
                  isSelected={selectedTool === tool.odl_id}
                  onClick={() => handleToolClick(tool.odl_id)}
                  autoclaveWidth={autoclaveWidth}
                  autoclaveHeight={autoclaveHeight}
                  showTooltips={showTooltips}
                />
              ))}
            </Layer>
          </CanvasWrapper>
        </div>
      </div>
    </div>
  )
}

// ✨ Componente principale refactorizzato
const NestingCanvas: React.FC<NestingCanvasProps> = ({ batchData, className }) => {
  const mounted = useClientMount()
  const [renderError, setRenderError] = useState<string | null>(null)

  // Validazione dati con debug
  useEffect(() => {
      console.log('🎨 NestingCanvas - Validazione dati:', {
    mounted,
    batchData: {
      configurazione_json: batchData.configurazione_json ? 'presente' : 'mancante',
      autoclave: batchData.autoclave ? 'presente' : 'mancante',
      metrics: batchData.metrics
    },
    configDetails: batchData.configurazione_json ? {
      canvas_width: batchData.configurazione_json.canvas_width,
      canvas_height: batchData.configurazione_json.canvas_height,

      autoclave_mm: batchData.configurazione_json.autoclave_mm,
      bounding_px: batchData.configurazione_json.bounding_px
    } : null,
    autoclaveDetails: batchData.autoclave ? {
      lunghezza: batchData.autoclave.lunghezza,
      larghezza_piano: batchData.autoclave.larghezza_piano,
      nome: batchData.autoclave.nome
    } : null
  })
    
    if (mounted && batchData.configurazione_json?.tool_positions) {
      try {
        const positions = batchData.configurazione_json.tool_positions
        console.log(`🔧 Tool positions trovate: ${positions.length}`, positions)
        
        if (!Array.isArray(positions)) {
          throw new Error('Tool positions non è un array valido')
        }
        
        for (const tool of positions) {
          if (typeof tool.x !== 'number' || typeof tool.y !== 'number') {
            throw new Error(`Tool ${tool.odl_id} ha coordinate non valide`)
          }
        }
        
        console.log('✅ Validazione tool positions completata con successo')
      } catch (error) {
        console.error('❌ Errore validazione dati canvas:', error)
        setRenderError(error instanceof Error ? error.message : 'Dati non validi')
      }
    } else if (mounted) {
      console.log('⚠️ Dati canvas mancanti:', {
        configurazione_json: !!batchData.configurazione_json,
        tool_positions: !!batchData.configurazione_json?.tool_positions,
        autoclave: !!batchData.autoclave
      })
    }
  }, [mounted, batchData.configurazione_json])

  // Loading state
  if (!mounted) {
    return <CanvasLoadingPlaceholder width={800} height={400} />
  }

  // Error state
  if (renderError) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">Errore Dati Canvas</h3>
              <p className="text-red-600 text-sm">{renderError}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-3"
                onClick={() => {
                  setRenderError(null)
                  window.location.reload()
                }}
              >
                Ricarica Pagina
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Empty state
  if (!batchData.configurazione_json?.tool_positions || !batchData.autoclave) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center space-y-4">
            <Package className="h-16 w-16 text-muted-foreground mx-auto" />
            <div>
              <h3 className="text-lg font-semibold">Nessun layout disponibile</h3>
              <p className="text-muted-foreground">
                Non ci sono dati di posizionamento per questo batch
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const normalizedTools = batchData.configurazione_json.tool_positions.map(normalizeToolData)
  const efficiency = batchData.metrics?.efficiency_percentage || 0

  console.log('🔧 Tools normalizzati per rendering:', normalizedTools)
  console.log('📐 Dimensioni autoclave:', {
    lunghezza: batchData.autoclave.lunghezza,
    larghezza_piano: batchData.autoclave.larghezza_piano
  })

  const handleToolClick = (toolId: number) => {
    // Callback per gestire click tool se necessario
    console.log(`Clicked tool ${toolId}`)
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Layout Nesting - Visualizzazione Tool
            </CardTitle>
            <Badge variant="outline" className="text-sm">
              <CheckCircle className="h-3 w-3 mr-1" />
              {normalizedTools.length} Tool Posizionati
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Header autoclave con efficienza */}
          <AutoclaveHeader 
            autoclave={batchData.autoclave} 
            efficiency={efficiency}
          />
          
          {/* Canvas responsive */}
          <ResponsiveCanvas
            toolPositions={normalizedTools}
            autoclave={batchData.autoclave}
            onToolClick={handleToolClick}
          />
          
          {/* Legenda colori e statistiche */}
          <ColorLegend 
            toolPositions={normalizedTools}
            autoclaveArea={batchData.autoclave.lunghezza * batchData.autoclave.larghezza_piano}
          />
        </CardContent>
      </Card>
    </div>
  )
}

export default NestingCanvas 