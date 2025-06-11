'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Separator } from '@/shared/components/ui/separator'
import { 
  Package, 
  RotateCcw, 
  X, 
  Info, 
  Ruler, 
  Grid3X3, 
  Maximize2,
  ZoomIn,
  ZoomOut,
  Home,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react'

interface ToolPosition {
  x: number
  y: number
  width: number
  height: number
  rotated?: boolean
  // Informazioni richieste per i tool
  part_number?: string          // Part number della parte
  part_number_tool?: string     // Part number del tool (diverso)
  numero_odl?: string | number  // Numero ODL (non ID)
  odl_id?: number              // ID ODL come fallback
  descrizione_breve?: string    // Descrizione della parte
  tool_nome?: string           // Nome tool come fallback
  peso?: number                // Peso per tooltip
}

interface AutoclaveInfo {
  nome: string
  codice?: string
  lunghezza: number
  larghezza_piano: number
}

interface BatchCanvasData {
  id: string
  configurazione_json?: {
    tool_positions?: ToolPosition[]     // ✅ Formato database standard
    positioned_tools?: ToolPosition[]   // ✅ Formato draft
    canvas_width?: number
    canvas_height?: number
  }
  autoclave?: AutoclaveInfo
  metrics?: {
    efficiency_percentage: number
    total_weight_kg: number
    positioned_tools: number
    excluded_tools: number
  }
}

interface NestingCanvasProps {
  batchData: BatchCanvasData
}

interface CanvasSettings {
  showGrid: boolean
  showRuler: boolean
  showDimensions: boolean
  showToolInfo: boolean
  gridSize: number
}

interface ViewportState {
  scale: number
  offsetX: number
  offsetY: number
  isDragging: boolean
  lastPointerPos: { x: number, y: number }
}

// Utility functions per formattazione
const formatDimension = (value: number): string => {
  return `${Math.round(value)}mm`
}

const formatArea = (area: number): string => {
  if (area > 1000000) {
    return `${(area / 1000000).toFixed(2)}m²`
  }
  return `${(area / 1000).toFixed(1)}cm²`
}

const getToolDisplayInfo = (tool: ToolPosition) => {
  // Numero ODL: priorità a numero_odl, fallback a ID formattato
  const numeroODL = tool.numero_odl 
    ? String(tool.numero_odl) 
    : `ODL${String(tool.odl_id || 0).padStart(3, '0')}`
  
  // Part number della parte (non del tool)
  const partNumber = tool.part_number || 'N/A'
  
  // Descrizione della parte
  const descrizione = tool.descrizione_breve || ''
  
  // Dimensioni del tool
  const dimensioni = `${formatDimension(tool.width)} × ${formatDimension(tool.height)}`
  
  return {
    numeroODL,
    partNumber,
    descrizione,
    dimensioni
  }
}

const getToolColor = (tool: ToolPosition, isSelected: boolean = false) => {
  if (isSelected) {
    return {
      fill: '#3b82f6',
      stroke: '#1d4ed8',
      textFill: '#ffffff'
    }
  }
  
  if (tool.rotated) {
    return {
      fill: '#d4edda',
      stroke: '#28a745',
      textFill: '#1f2937'
    }
  }
  
  return {
    fill: '#e3f2fd',
    stroke: '#1976d2',
    textFill: '#1f2937'
  }
}

// 🛡️ HELPER: Ottiene tool dal batch (compatibilità universale)
const getToolsFromBatch = (batchData: BatchCanvasData): ToolPosition[] => {
  if (!batchData.configurazione_json) return []
  
  // Prova prima il formato database standard, poi quello draft
  return batchData.configurazione_json.tool_positions || 
         batchData.configurazione_json.positioned_tools || 
         []
}

export default function NestingCanvas({ batchData }: NestingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  const [selectedTool, setSelectedTool] = useState<ToolPosition | null>(null)
  const [settings, setSettings] = useState<CanvasSettings>({
    showGrid: true,
    showRuler: true,
    showDimensions: true,
    showToolInfo: true,
    gridSize: 100
  })
  
  const [viewport, setViewport] = useState<ViewportState>({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    lastPointerPos: { x: 0, y: 0 }
  })
  
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [mousePos, setMousePos] = useState<{ x: number, y: number } | null>(null)

  const drawCanvas = useCallback(() => {
    if (!canvasRef.current || !batchData.autoclave) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Canvas dimensions responsive
    const container = containerRef.current
    if (!container) return
    
    const containerRect = container.getBoundingClientRect()
    const canvasWidth = Math.max(800, containerRect.width - 40)
    const canvasHeight = Math.max(600, isFullscreen ? window.innerHeight - 100 : 600)
    
    canvas.width = canvasWidth
    canvas.height = canvasHeight

    // Autoclave dimensions
    const autoclaveWidth = batchData.autoclave.lunghezza || 1000
    const autoclaveHeight = batchData.autoclave.larghezza_piano || 800

    // Calculate scale with viewport
    const padding = 60
    const baseScaleX = (canvasWidth - 2 * padding) / autoclaveWidth
    const baseScaleY = (canvasHeight - 2 * padding) / autoclaveHeight
    const baseScale = Math.min(baseScaleX, baseScaleY)
    const scale = baseScale * viewport.scale

    // Calculate offset
    const scaledAutoclaveWidth = autoclaveWidth * scale
    const scaledAutoclaveHeight = autoclaveHeight * scale
    const centerOffsetX = (canvasWidth - scaledAutoclaveWidth) / 2
    const centerOffsetY = (canvasHeight - scaledAutoclaveHeight) / 2
    const offsetX = centerOffsetX + viewport.offsetX
    const offsetY = centerOffsetY + viewport.offsetY

    // Clear canvas with neutral background (best practice industriale)
    ctx.fillStyle = '#f8f9fa'
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    // Draw autoclave background
    ctx.fillStyle = '#ffffff'
    ctx.strokeStyle = '#495057'
    ctx.lineWidth = 2
    ctx.fillRect(offsetX, offsetY, scaledAutoclaveWidth, scaledAutoclaveHeight)
    ctx.strokeRect(offsetX, offsetY, scaledAutoclaveWidth, scaledAutoclaveHeight)

    // Draw grid (se abilitato)
    if (settings.showGrid) {
      ctx.strokeStyle = '#e9ecef'
      ctx.lineWidth = 0.5
      const gridSize = settings.gridSize * scale
      
      // Vertical lines
      for (let x = gridSize; x < scaledAutoclaveWidth; x += gridSize) {
        ctx.beginPath()
        ctx.moveTo(offsetX + x, offsetY)
        ctx.lineTo(offsetX + x, offsetY + scaledAutoclaveHeight)
        ctx.stroke()
      }
      
      // Horizontal lines
      for (let y = gridSize; y < scaledAutoclaveHeight; y += gridSize) {
        ctx.beginPath()
        ctx.moveTo(offsetX, offsetY + y)
        ctx.lineTo(offsetX + scaledAutoclaveWidth, offsetY + y)
        ctx.stroke()
      }
    }

    // Draw tools con informazioni migliorate
    const toolPositions = getToolsFromBatch(batchData)
    
    toolPositions.forEach((tool, index) => {
      if (tool.x == null || tool.y == null || tool.width == null || tool.height == null) return

      const toolX = offsetX + tool.x * scale
      const toolY = offsetY + tool.y * scale
      const toolWidth = tool.width * scale
      const toolHeight = tool.height * scale

      const isSelected = selectedTool === tool
      const colors = getToolColor(tool, isSelected)

      // Draw tool rectangle
      ctx.fillStyle = colors.fill
      ctx.strokeStyle = colors.stroke
      ctx.lineWidth = isSelected ? 3 : 1.5
      
      ctx.fillRect(toolX, toolY, toolWidth, toolHeight)
      ctx.strokeRect(toolX, toolY, toolWidth, toolHeight)

      // *** CONTENUTO NEI TOOL BOX - INFORMAZIONI RICHIESTE ***
      if (settings.showToolInfo && scale > 0.3) {
        const info = getToolDisplayInfo(tool)
        
        // Calcola font size dinamico basato su area e zoom
        const area = toolWidth * toolHeight
        const baseFontSize = Math.max(8, Math.min(16, Math.sqrt(area) / 8))
        const fontSize = Math.max(6, baseFontSize * Math.min(1, scale))
        
        ctx.fillStyle = colors.textFill
        ctx.font = `bold ${fontSize}px Arial`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        
        const centerX = toolX + toolWidth / 2
        let textY = toolY + 4
        const lineHeight = fontSize + 2
        
        // Background semi-trasparente per leggibilità
        if (fontSize >= 8) {
          ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
          ctx.fillRect(toolX + 2, toolY + 2, toolWidth - 4, Math.min(toolHeight - 4, lineHeight * 4 + 6))
        }
        
        ctx.fillStyle = colors.textFill
        
        // 1. NUMERO ODL (sempre priorità)
        if (fontSize >= 8) {
          ctx.font = `bold ${fontSize}px Arial`
          ctx.fillText(info.numeroODL, centerX, textY)
          textY += lineHeight
        }
        
        // 2. PART NUMBER (se c'è spazio)
        if (fontSize >= 10 && toolHeight > 40) {
          ctx.font = `${fontSize - 1}px Arial`
          const truncatedPart = info.partNumber.length > 15 
            ? info.partNumber.substring(0, 12) + '...' 
            : info.partNumber
          ctx.fillText(truncatedPart, centerX, textY)
          textY += lineHeight
        }
        
        // 3. DESCRIZIONE (se c'è spazio)
        if (fontSize >= 9 && toolHeight > 60 && info.descrizione) {
          ctx.font = `${fontSize - 2}px Arial`
          const truncatedDesc = info.descrizione.length > 20 
            ? info.descrizione.substring(0, 17) + '...' 
            : info.descrizione
          ctx.fillText(truncatedDesc, centerX, textY)
          textY += lineHeight
        }
        
        // 4. DIMENSIONI (se c'è spazio)
        if (fontSize >= 8 && toolHeight > 80 && settings.showDimensions) {
          ctx.font = `${fontSize - 2}px Arial`
          ctx.fillStyle = '#6c757d'
          ctx.fillText(info.dimensioni, centerX, textY)
        }
      }
    })

    // Draw ruler (se abilitato)
    if (settings.showRuler) {
      ctx.strokeStyle = '#495057'
      ctx.lineWidth = 2
      ctx.fillStyle = '#495057'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      
      const rulerX = canvasWidth - 200
      const rulerY = canvasHeight - 40
      const rulerLength = 100 * scale // 100mm reference
      
      ctx.beginPath()
      ctx.moveTo(rulerX, rulerY)
      ctx.lineTo(rulerX + rulerLength, rulerY)
      ctx.stroke()
      
      // Tick marks
      ctx.beginPath()
      ctx.moveTo(rulerX, rulerY - 5)
      ctx.lineTo(rulerX, rulerY + 5)
      ctx.moveTo(rulerX + rulerLength, rulerY - 5)
      ctx.lineTo(rulerX + rulerLength, rulerY + 5)
      ctx.stroke()
      
      ctx.fillText('100mm', rulerX + rulerLength / 2, rulerY + 20)
    }

    // Draw title and info (stile industriale pulito)
    ctx.fillStyle = '#495057'
    ctx.font = 'bold 18px Arial'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(
      `${batchData.autoclave.nome} (${autoclaveWidth}×${autoclaveHeight}mm)`,
      20,
      20
    )

    // Draw metrics con priorità alle informazioni critiche
    if (batchData.metrics) {
      ctx.font = '14px Arial'
      ctx.fillStyle = batchData.metrics.efficiency_percentage < 50 ? '#dc3545' : '#28a745'
      const efficiency = `Efficienza: ${batchData.metrics.efficiency_percentage.toFixed(1)}%`
      
      ctx.fillStyle = '#6c757d'
      const metricsText = `${efficiency} | Tool: ${batchData.metrics.positioned_tools} | Peso: ${batchData.metrics.total_weight_kg.toFixed(1)}kg`
      ctx.fillText(metricsText, 20, 50)
    }

    // Mouse coordinates (per precisione industriale)
    if (mousePos && scale > 0.5) {
      const mouseX = (mousePos.x - offsetX) / scale
      const mouseY = (mousePos.y - offsetY) / scale
      
      if (mouseX >= 0 && mouseX <= autoclaveWidth && mouseY >= 0 && mouseY <= autoclaveHeight) {
        ctx.fillStyle = '#495057'
        ctx.font = '12px Arial'
        ctx.textAlign = 'right'
        ctx.fillText(
          `X: ${mouseX.toFixed(0)}mm, Y: ${mouseY.toFixed(0)}mm`,
          canvasWidth - 20,
          20
        )
      }
    }

  }, [batchData, selectedTool, settings, viewport, isFullscreen, mousePos])

  // Event handlers
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !batchData.autoclave) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Calculate world coordinates
    const autoclaveWidth = batchData.autoclave.lunghezza || 1000
    const autoclaveHeight = batchData.autoclave.larghezza_piano || 800
    const padding = 60
    const baseScaleX = (canvas.width - 2 * padding) / autoclaveWidth
    const baseScaleY = (canvas.height - 2 * padding) / autoclaveHeight
    const baseScale = Math.min(baseScaleX, baseScaleY)
    const scale = baseScale * viewport.scale
    
    const scaledAutoclaveWidth = autoclaveWidth * scale
    const scaledAutoclaveHeight = autoclaveHeight * scale
    const centerOffsetX = (canvas.width - scaledAutoclaveWidth) / 2
    const centerOffsetY = (canvas.height - scaledAutoclaveHeight) / 2
    const offsetX = centerOffsetX + viewport.offsetX
    const offsetY = centerOffsetY + viewport.offsetY

    const worldX = (x - offsetX) / scale
    const worldY = (y - offsetY) / scale

    // Check tool collision
    const toolPositions = getToolsFromBatch(batchData)
    const clickedTool = toolPositions.find(tool => 
      worldX >= tool.x && worldX <= tool.x + tool.width &&
      worldY >= tool.y && worldY <= tool.y + tool.height
    )

    setSelectedTool(clickedTool || null)
  }, [batchData, viewport])

  const handleCanvasMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    setMousePos({ x, y })

    if (viewport.isDragging) {
      const deltaX = x - viewport.lastPointerPos.x
      const deltaY = y - viewport.lastPointerPos.y
      
      setViewport(prev => ({
        ...prev,
        offsetX: prev.offsetX + deltaX,
        offsetY: prev.offsetY + deltaY,
        lastPointerPos: { x, y }
      }))
    }
  }, [viewport.isDragging, viewport.lastPointerPos])

  const handleMouseDown = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    setViewport(prev => ({
      ...prev,
      isDragging: true,
      lastPointerPos: { x, y }
    }))
  }, [])

  const handleMouseUp = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      isDragging: false
    }))
  }, [])

  const handleZoom = (delta: number) => {
    setViewport(prev => ({
      ...prev,
      scale: Math.max(0.1, Math.min(5, prev.scale + delta))
    }))
  }

  const resetView = () => {
    setViewport({
      scale: 1,
      offsetX: 0,
      offsetY: 0,
      isDragging: false,
      lastPointerPos: { x: 0, y: 0 }
    })
  }

  useEffect(() => {
    drawCanvas()
  }, [drawCanvas])

  useEffect(() => {
    const handleMouseUpGlobal = () => {
      setViewport(prev => ({
        ...prev,
        isDragging: false
      }))
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'Escape') {
        setSelectedTool(null)
      }
    }

    document.addEventListener('mouseup', handleMouseUpGlobal)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mouseup', handleMouseUpGlobal)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  if (!batchData.autoclave) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 border rounded-lg">
        <p className="text-gray-500">Nessun dato autoclave disponibile</p>
      </div>
    )
  }

  return (
    <div className={`w-full ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between p-4 bg-white border-b">
        <div className="flex items-center gap-2">
          <Button
            variant={settings.showGrid ? "default" : "outline"}
            size="sm"
            onClick={() => setSettings(prev => ({ ...prev, showGrid: !prev.showGrid }))}
          >
            <Grid3X3 className="h-4 w-4" />
            Griglia
          </Button>
          
          <Button
            variant={settings.showRuler ? "default" : "outline"}
            size="sm"
            onClick={() => setSettings(prev => ({ ...prev, showRuler: !prev.showRuler }))}
          >
            <Ruler className="h-4 w-4" />
            Righello
          </Button>
          
          <Button
            variant={settings.showDimensions ? "default" : "outline"}
            size="sm"
            onClick={() => setSettings(prev => ({ ...prev, showDimensions: !prev.showDimensions }))}
          >
            {settings.showDimensions ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            Quote
          </Button>
          
          <Button
            variant={settings.showToolInfo ? "default" : "outline"}
            size="sm"
            onClick={() => setSettings(prev => ({ ...prev, showToolInfo: !prev.showToolInfo }))}
          >
            <Info className="h-4 w-4" />
            Info
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleZoom(-0.2)}
            disabled={viewport.scale <= 0.1}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <span className="text-sm font-mono px-2">
            {Math.round(viewport.scale * 100)}%
          </span>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleZoom(0.2)}
            disabled={viewport.scale >= 5}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={resetView}
          >
            <Home className="h-4 w-4" />
            Reset
          </Button>
          
          <Button
            variant={isFullscreen ? "default" : "outline"}
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            <Maximize2 className="h-4 w-4" />
            {isFullscreen ? 'Esci' : 'Fullscreen'}
          </Button>
        </div>
      </div>

      {/* Canvas Container */}
      <div 
        ref={containerRef}
        className={`relative ${isFullscreen ? 'h-full' : 'h-[600px]'} bg-gray-50 overflow-hidden`}
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-crosshair"
          onClick={handleCanvasClick}
          onMouseMove={handleCanvasMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          style={{ touchAction: 'none' }}
        />

        {/* Tool Info Panel */}
        {selectedTool && (
          <ToolInfoPanel 
            tool={selectedTool}
            autoclave={batchData.autoclave}
            onClose={() => setSelectedTool(null)}
          />
        )}
      </div>

      {/* Info Panel Bottom */}
      <div className="p-4 bg-muted">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Dimensioni Autoclave:</span>
            <br />
            <span className="font-mono">{batchData.autoclave.lunghezza}×{batchData.autoclave.larghezza_piano}mm</span>
          </div>
          {batchData.metrics && (
            <>
              <div>
                <span className="font-medium text-gray-700">Efficienza:</span>
                <br />
                <span className={`font-bold ${batchData.metrics.efficiency_percentage >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                  {batchData.metrics.efficiency_percentage.toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Tool Posizionati:</span>
                <br />
                <span className="font-mono">{batchData.metrics.positioned_tools}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Peso Totale:</span>
                <br />
                <span className="font-mono">{batchData.metrics.total_weight_kg.toFixed(1)}kg</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// Componente Tool Info Panel separato
const ToolInfoPanel: React.FC<{
  tool: ToolPosition
  autoclave: AutoclaveInfo
  onClose: () => void
}> = ({ tool, autoclave, onClose }) => {
  const info = getToolDisplayInfo(tool)
  const area = (tool.width * tool.height) / 1000000 // m²
  const posizione = `${formatDimension(tool.x)}, ${formatDimension(tool.y)}`

  return (
    <div className="absolute top-4 right-4 z-20 w-80">
      <Card className="bg-white/95 backdrop-blur-sm shadow-lg border border-gray-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4" />
              {info.numeroODL}
              {tool.rotated && (
                <Badge variant="secondary" className="text-xs">
                  <RotateCcw className="h-3 w-3 mr-1" />
                  Ruotato
                </Badge>
              )}
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0">
              <X className="h-3 w-3" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Informazioni Parte */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-800 flex items-center gap-1">
              <Info className="h-3 w-3" />
              Informazioni Parte
            </h4>
            <div className="grid grid-cols-1 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Part Number:</span>
                <span className="font-medium font-mono">{info.partNumber}</span>
              </div>
              {tool.part_number_tool && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Tool Code:</span>
                  <span className="font-medium font-mono">{tool.part_number_tool}</span>
                </div>
              )}
              {info.descrizione && (
                <div className="bg-gray-50 p-2 rounded">
                  <span className="text-gray-600">Descrizione:</span>
                  <p className="font-medium mt-1">{info.descrizione}</p>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Informazioni Geometriche */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-800">
              Geometria e Posizione
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-600">Dimensioni:</span>
                <div className="font-mono font-medium">{info.dimensioni}</div>
              </div>
              <div>
                <span className="text-gray-600">Area:</span>
                <div className="font-mono font-medium">{formatArea(tool.width * tool.height)}</div>
              </div>
              <div>
                <span className="text-gray-600">Posizione:</span>
                <div className="font-mono font-medium">{posizione}</div>
              </div>
              {tool.peso && (
                <div>
                  <span className="text-gray-600">Peso:</span>
                  <div className="font-mono font-medium">{tool.peso.toFixed(1)}kg</div>
                </div>
              )}
            </div>
          </div>

          {/* Istruzioni Caricamento */}
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">
              Istruzioni Caricamento
            </h4>
            <div className="text-xs text-blue-700 space-y-1">
              <div>• Posizionare la parte secondo le coordinate indicate</div>
              <div>• Verificare l'orientamento {tool.rotated ? '(RUOTATO 90°)' : '(STANDARD)'}</div>
              <div>• Controllare le dimensioni prima del caricamento</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 