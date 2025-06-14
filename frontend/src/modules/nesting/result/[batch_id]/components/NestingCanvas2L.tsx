'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { Badge } from '@/shared/components/ui/badge'
import { Button } from '@/shared/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
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
  EyeOff,
  Layers,
  Target,
  Box,
  Building
} from 'lucide-react'

// 🎯 Interfacce per nesting 2L
interface ToolPosition2L {
  odl_id: number
  tool_id: number
  x: number
  y: number
  width: number
  height: number
  rotated: boolean
  weight_kg: number
  level: number // 0 = piano base, 1 = su cavalletti
  z_position: number
  lines_used: number
  part_number?: string
  descrizione_breve?: string
  numero_odl?: string | number
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

interface NestingCanvas2LProps {
  positioned_tools: ToolPosition2L[]
  cavalletti: Cavalletto[]
  canvas_width: number
  canvas_height: number
  className?: string
  showLevelFilter?: boolean
  onToolClick?: (tool: ToolPosition2L) => void
  onStandClick?: (stand: Cavalletto) => void
}

// 🎨 Layer Visibility State con controlli opacity
interface LayerVisibility {
  level0: boolean
  level1: boolean
  cavalletti: boolean
  grid: boolean
  dimensions: boolean
  coordinates: boolean
  level0Opacity: number
  level1Opacity: number
  cavallettiOpacity: number
  isolationMode: 'none' | 'level0' | 'level1' | 'cavalletti'
  showDepthIndicators: boolean
  showZLevels: boolean
}

// 🎮 Viewport State per zoom e pan con autofit
interface ViewportState {
  scale: number
  offsetX: number
  offsetY: number
  isDragging: boolean
  lastPointerPos: { x: number, y: number }
}

// 🛠️ Canvas Settings
interface CanvasSettings {
  showGrid: boolean
  showRuler: boolean
  showDimensions: boolean
  showToolInfo: boolean
  gridSize: number
  antialiasing: boolean
  showShadows: boolean
  enhancedDepth: boolean
  compactMode: boolean
}

// 🎨 Color Palette (Design System neutro industriale)
const COLORS = {
  background: '#ffffff',
  grid: '#f1f5f9',
  gridMajor: '#e2e8f0',
  level0: {
    fill: '#e0f2fe',
    stroke: '#0284c7',
    fillSelected: '#0284c7',
    strokeSelected: '#0369a1'
  },
  level1: {
    fill: '#fef3c7',
    stroke: '#f59e0b',
    fillSelected: '#f59e0b',
    strokeSelected: '#d97706'
  },
  cavalletto: {
    fill: '#f1f5f9',
    stroke: '#64748b',
    fillHover: '#e2e8f0',
    pattern: '#94a3b8'
  },
  text: '#1e293b',
  textSecondary: '#64748b',
  accent: '#ef4444',
  ruler: '#6b7280'
}

// 🛠️ Utility Functions
const formatDimension = (value: number): string => {
  return `${Math.round(value)}mm`
}

const formatWeight = (weight: number): string => {
  return `${weight.toFixed(1)}kg`
}

const getToolDisplayInfo = (tool: ToolPosition2L) => {
  const numeroODL = tool.numero_odl || `ODL${String(tool.odl_id).padStart(3, '0')}`
  const partNumber = tool.part_number || 'N/A'
  const descrizione = tool.descrizione_breve || ''
  const dimensioni = `${formatDimension(tool.width)}×${formatDimension(tool.height)}`
  const levelText = tool.level === 0 ? 'Piano Base' : 'Su Cavalletti'
  const altezza = tool.z_position ? formatDimension(tool.z_position) : '0mm'
  
  return {
    numeroODL,
    partNumber,
    descrizione,
    dimensioni,
    levelText,
    altezza,
    peso: formatWeight(tool.weight_kg)
  }
}

export const NestingCanvas2L: React.FC<NestingCanvas2LProps> = ({
  positioned_tools,
  cavalletti,
  canvas_width,
  canvas_height,
  className = '',
  showLevelFilter = true,
  onToolClick,
  onStandClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedTool, setSelectedTool] = useState<ToolPosition2L | null>(null)
  const [selectedCavalletto, setSelectedCavalletto] = useState<Cavalletto | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  
  // 🎮 Viewport state con autofit iniziale
  const [viewport, setViewport] = useState<ViewportState>({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    lastPointerPos: { x: 0, y: 0 }
  })

  // 🎨 Layer visibility state
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    level0: true,
    level1: true,
    cavalletti: true,
    grid: true,
    dimensions: false,
    coordinates: false,
    level0Opacity: 1,
    level1Opacity: 1,
    cavallettiOpacity: 1,
    isolationMode: 'none',
    showDepthIndicators: false,
    showZLevels: false
  })

  // 🛠️ Canvas settings
  const [settings, setSettings] = useState<CanvasSettings>({
    showGrid: true,
    showRuler: true,
    showDimensions: false,
    showToolInfo: true,
    gridSize: 100,
    antialiasing: true,
    showShadows: true,
    enhancedDepth: true,
    compactMode: false
  })

  // 🎨 Canvas context
  const getCanvasContext = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return null
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    
    ctx.imageSmoothingEnabled = settings.antialiasing
    ctx.imageSmoothingQuality = 'high'
    
    return ctx
  }, [settings.antialiasing])

  // 🎯 Autofit calculation (come in NestingCanvas originale)
  const calculateAutofit = useCallback(() => {
    const container = containerRef.current
    if (!container) return { scale: 1, offsetX: 0, offsetY: 0 }

    const containerRect = container.getBoundingClientRect()
    const canvasWidth = Math.max(800, containerRect.width - 40)
    const canvasHeight = Math.max(600, isFullscreen ? window.innerHeight - 100 : 600)

    // Calculate scale to fit autoclave dimensions with padding
    const padding = 60
    const baseScaleX = (canvasWidth - 2 * padding) / canvas_width
    const baseScaleY = (canvasHeight - 2 * padding) / canvas_height
    const baseScale = Math.min(baseScaleX, baseScaleY)

    // Calculate center offsets
    const scaledAutoclaveWidth = canvas_width * baseScale
    const scaledAutoclaveHeight = canvas_height * baseScale
    const centerOffsetX = (canvasWidth - scaledAutoclaveWidth) / 2
    const centerOffsetY = (canvasHeight - scaledAutoclaveHeight) / 2

    return {
      scale: baseScale,
      offsetX: centerOffsetX,
      offsetY: centerOffsetY
    }
  }, [canvas_width, canvas_height, isFullscreen])

  // 🎮 Coordinate transformation
  const screenToCanvas = useCallback((screenX: number, screenY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return { x: 0, y: 0 }
    
    const x = (screenX - rect.left - viewport.offsetX) / viewport.scale
    const y = (screenY - rect.top - viewport.offsetY) / viewport.scale
    
    return { x, y }
  }, [viewport])

  // 🎨 Main render function
  const render = useCallback(() => {
    const ctx = getCanvasContext()
    if (!ctx || !canvasRef.current || !containerRef.current) return

    const container = containerRef.current
    const canvas = canvasRef.current
    const containerRect = container.getBoundingClientRect()
    
    // Responsive canvas sizing
    const canvasWidth = Math.max(800, containerRect.width - 40)
    const canvasHeight = Math.max(600, isFullscreen ? window.innerHeight - 100 : 600)
    
    canvas.width = canvasWidth
    canvas.height = canvasHeight

    // Apply autofit calculation for initial scale and offset
    const autofit = calculateAutofit()
    const scale = autofit.scale * viewport.scale
    const offsetX = autofit.offsetX + viewport.offsetX
    const offsetY = autofit.offsetY + viewport.offsetY

    // Clear canvas con background neutro
    ctx.fillStyle = COLORS.background
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    // Draw autoclave perimeter
    ctx.fillStyle = '#ffffff'
    ctx.strokeStyle = '#495057'
    ctx.lineWidth = 2
    
    const scaledWidth = canvas_width * scale
    const scaledHeight = canvas_height * scale
    
    ctx.fillRect(offsetX, offsetY, scaledWidth, scaledHeight)
    ctx.strokeRect(offsetX, offsetY, scaledWidth, scaledHeight)

    // Draw grid (se abilitato)
    if (layerVisibility.grid) {
      ctx.strokeStyle = COLORS.grid
      ctx.lineWidth = 0.5
      const gridSize = settings.gridSize * scale
      
      for (let x = gridSize; x < scaledWidth; x += gridSize) {
        ctx.beginPath()
        ctx.moveTo(offsetX + x, offsetY)
        ctx.lineTo(offsetX + x, offsetY + scaledHeight)
        ctx.stroke()
      }
      
      for (let y = gridSize; y < scaledHeight; y += gridSize) {
        ctx.beginPath()
        ctx.moveTo(offsetX, offsetY + y)
        ctx.lineTo(offsetX + scaledWidth, offsetY + y)
        ctx.stroke()
      }
    }

    // Draw cavalletti first (background layer) - 🏗️ AGGIORNATO: Segmenti trasversali fissi
    if (layerVisibility.cavalletti && (layerVisibility.isolationMode === 'none' || layerVisibility.isolationMode === 'cavalletti')) {
      ctx.globalAlpha = layerVisibility.cavallettiOpacity
      
      // 🎯 NUOVO APPROCCIO: Raggruppa cavalletti per posizione X (segmenti trasversali)
      const cavallettiGrouped = new Map<number, Cavalletto[]>()
      
      cavalletti.forEach(cavalletto => {
        const xKey = Math.round(cavalletto.x) // Raggruppa per posizione X
        if (!cavallettiGrouped.has(xKey)) {
          cavallettiGrouped.set(xKey, [])
        }
        cavallettiGrouped.get(xKey)!.push(cavalletto)
      })
      
      // 🏗️ Disegna ogni gruppo come segmento trasversale
      Array.from(cavallettiGrouped.entries()).forEach(([xPos, gruppo]) => {
        const isSelected = gruppo.some(cav => selectedCavalletto === cav)
        
        // 🎨 Colori per segmenti trasversali
        ctx.fillStyle = isSelected ? '#fbbf24' : '#94a3b8'  // Giallo per selezione, grigio per normale
        ctx.strokeStyle = isSelected ? '#f59e0b' : '#475569'  // Bordo più scuro
        ctx.lineWidth = isSelected ? 4 : 3
        
        if (isSelected) ctx.setLineDash([10, 5])
        
        // 🏗️ SEGMENTO TRASVERSALE: Si estende per tutta l'altezza dell'autoclave
        const segmentX = offsetX + xPos * scale
        const segmentY = offsetY  // Inizia dal bordo superiore
        const segmentWidth = (gruppo[0]?.height || 60) * scale  // Spessore del segmento
        const segmentHeight = canvas_height * scale  // Attraversa tutta l'altezza
        
        // Disegna il segmento trasversale
        ctx.fillRect(segmentX, segmentY, segmentWidth, segmentHeight)
        ctx.strokeRect(segmentX, segmentY, segmentWidth, segmentHeight)
        
        // 🔧 Pattern diagonale per indicare che è un supporto fisso
        ctx.save()
        ctx.strokeStyle = isSelected ? '#f59e0b' : '#64748b'
        ctx.lineWidth = 1
        ctx.setLineDash([6, 6])
        
        // Linee diagonali per pattern (più dense per segmenti)
        for (let i = 0; i < segmentWidth + segmentHeight; i += 12) {
          ctx.beginPath()
          ctx.moveTo(segmentX + i, segmentY)
          ctx.lineTo(segmentX, segmentY + i)
          ctx.stroke()
        }
        ctx.restore()
        
        ctx.setLineDash([])
        
        // 🏗️ Etichetta del segmento
        ctx.fillStyle = isSelected ? '#1f2937' : '#374151'
        const fontSize = Math.max(12, Math.min(16, segmentWidth / 4))
        ctx.font = `bold ${fontSize}px monospace`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        
        // Icona cavalletto fisso
        ctx.fillText('⚏', segmentX + segmentWidth / 2, segmentY + 30)
        
        // Numero segmento
        ctx.font = `${fontSize - 2}px sans-serif`
        ctx.fillText(`Segmento #${xPos + 1}`, 
                    segmentX + segmentWidth / 2, segmentY + 50)
        
        // 📏 Informazioni tecniche se zoom sufficiente
        if (scale > 0.4 && segmentWidth > 30) {
          ctx.font = `${Math.max(8, fontSize - 4)}px sans-serif`
          ctx.fillStyle = isSelected ? '#059669' : '#6b7280'
          
          // Spessore segmento
          const thicknessText = `${Math.round(gruppo[0]?.height || 60)}mm`
          ctx.fillText(thicknessText, segmentX + segmentWidth / 2, segmentY + 70)
          
          // Numero tool supportati
          const toolCount = gruppo.length
          ctx.fillText(`${toolCount} tool`, segmentX + segmentWidth / 2, segmentY + 85)
        }
        
        // 🎯 Indicatori di carico per ogni tool supportato
        if (scale > 0.3) {
          gruppo.forEach((cavalletto, index) => {
            const indicatorY = segmentY + 100 + (index * 20)
            const indicatorSize = 8
            
            // Piccolo indicatore per ogni tool
            ctx.fillStyle = isSelected ? '#10b981' : '#6b7280'
            ctx.fillRect(
              segmentX + segmentWidth / 2 - indicatorSize / 2, 
              indicatorY, 
              indicatorSize, 
              indicatorSize
            )
            
            // ODL ID se spazio sufficiente
            if (segmentWidth > 50) {
              ctx.font = `${Math.max(6, fontSize - 6)}px sans-serif`
              ctx.fillStyle = isSelected ? '#1f2937' : '#6b7280'
              ctx.fillText(`ODL${cavalletto.tool_odl_id}`, 
                          segmentX + segmentWidth / 2, indicatorY + indicatorSize + 10)
            }
          })
        }
      })
      
      ctx.globalAlpha = 1
    }

    // Draw tools per livello
    const drawToolsForLevel = (level: number) => {
      const levelVisible = level === 0 ? layerVisibility.level0 : layerVisibility.level1
      const isolationCheck = 
        layerVisibility.isolationMode === 'none' ||
        (layerVisibility.isolationMode === 'level0' && level === 0) ||
        (layerVisibility.isolationMode === 'level1' && level === 1)
      
      if (!levelVisible || !isolationCheck) return
      
      const opacity = level === 0 ? layerVisibility.level0Opacity : layerVisibility.level1Opacity
      ctx.globalAlpha = opacity
      
      positioned_tools.filter(tool => tool.level === level).forEach(tool => {
        const isSelected = selectedTool === tool
        const colors = level === 0 ? COLORS.level0 : COLORS.level1
        
        ctx.fillStyle = isSelected ? colors.fillSelected : colors.fill
        ctx.strokeStyle = isSelected ? colors.strokeSelected : colors.stroke
        ctx.lineWidth = isSelected ? 3 : 2
        
        const toolX = offsetX + tool.x * scale
        const toolY = offsetY + tool.y * scale
        const toolWidth = tool.width * scale
        const toolHeight = tool.height * scale
        
        // Enhanced styling for level 1
        if (level === 1) {
          if (!isSelected) ctx.setLineDash([8, 4])
          if (settings.showShadows) {
            ctx.shadowColor = 'rgba(245, 158, 11, 0.4)'
            ctx.shadowBlur = 8
            ctx.shadowOffsetX = 3
            ctx.shadowOffsetY = 4
          }
        }
        
        ctx.fillRect(toolX, toolY, toolWidth, toolHeight)
        ctx.strokeRect(toolX, toolY, toolWidth, toolHeight)
        
        // Reset effects
        ctx.setLineDash([])
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
        ctx.shadowOffsetX = 0
        ctx.shadowOffsetY = 0
        
        // Tool content rendering
        if (settings.showToolInfo && scale > 0.3) {
          const info = getToolDisplayInfo(tool)
          const area = toolWidth * toolHeight
          let fontSize = Math.max(8, Math.min(16, Math.sqrt(area) / 20))
          if (settings.compactMode) fontSize = Math.max(6, fontSize - 2)
          
          ctx.fillStyle = COLORS.text
          ctx.font = `bold ${fontSize}px sans-serif`
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          
          const centerX = toolX + toolWidth / 2
          const centerY = toolY + toolHeight / 2
          
          // Multi-line content
          const lines = []
          if (fontSize >= 8) lines.push(String(info.numeroODL))
          if (fontSize >= 10 && info.partNumber !== 'N/A') lines.push(info.partNumber)
          if (fontSize >= 9) {
            const levelColor = level === 0 ? '#0284c7' : '#f59e0b'
            ctx.fillStyle = levelColor
            lines.push(`L${level}`)
          }
          
          const lineHeight = fontSize * 1.2
          const startY = centerY - (lines.length * lineHeight) / 2 + lineHeight / 2
          
          lines.forEach((line, index) => {
            ctx.fillText(line, centerX, startY + index * lineHeight)
          })
        }
        
        // Rotation indicator
        if (tool.rotated) {
          ctx.fillStyle = COLORS.accent
          ctx.font = '12px sans-serif'
          ctx.fillText('↻', toolX + toolWidth - 10, toolY + 12)
        }
      })
      
      ctx.globalAlpha = 1
    }

    // Draw level 0 tools first, then level 1
    drawToolsForLevel(0)
    drawToolsForLevel(1)

    // Draw ruler
    if (settings.showRuler) {
      ctx.strokeStyle = COLORS.ruler
      ctx.lineWidth = 2
      ctx.fillStyle = COLORS.ruler
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      
      const rulerX = canvasWidth - 200
      const rulerY = canvasHeight - 40
      const rulerLength = 100 * scale
      
      ctx.beginPath()
      ctx.moveTo(rulerX, rulerY)
      ctx.lineTo(rulerX + rulerLength, rulerY)
      ctx.stroke()
      
      ctx.beginPath()
      ctx.moveTo(rulerX, rulerY - 5)
      ctx.lineTo(rulerX, rulerY + 5)
      ctx.moveTo(rulerX + rulerLength, rulerY - 5)
      ctx.lineTo(rulerX + rulerLength, rulerY + 5)
      ctx.stroke()
      
      ctx.fillText('100mm', rulerX + rulerLength / 2, rulerY + 20)
    }

    // Mouse coordinates
    if (layerVisibility.coordinates) {
      const canvasCoords = screenToCanvas(mousePos.x, mousePos.y)
      
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
      ctx.fillRect(10, canvasHeight - 30, 150, 20)
      
      ctx.fillStyle = 'white'
      ctx.font = '12px monospace'
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillText(
        `X: ${Math.round(canvasCoords.x)} Y: ${Math.round(canvasCoords.y)}`,
        15,
        canvasHeight - 20
      )
    }

    // Draw title and info
    ctx.fillStyle = '#495057'
    ctx.font = 'bold 18px Arial'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'top'
    ctx.fillText(
      `Canvas 2L (${formatDimension(canvas_width)}×${formatDimension(canvas_height)})`,
      20,
      20
    )

  }, [
    getCanvasContext, viewport, calculateAutofit, canvas_width, canvas_height, 
    isFullscreen, layerVisibility, settings, positioned_tools, cavalletti, 
    selectedTool, selectedCavalletto, screenToCanvas, mousePos
  ])

  // 🎮 Event handlers
  const handleCanvasMouseMove = useCallback((event: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    
    setMousePos({
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    })
    
    if (viewport.isDragging) {
      const deltaX = event.clientX - viewport.lastPointerPos.x
      const deltaY = event.clientY - viewport.lastPointerPos.y
      
      setViewport(prev => ({
        ...prev,
        offsetX: prev.offsetX + deltaX,
        offsetY: prev.offsetY + deltaY,
        lastPointerPos: { x: event.clientX, y: event.clientY }
      }))
    }
  }, [viewport.isDragging, viewport.lastPointerPos])

  const handleCanvasMouseDown = useCallback((event: React.MouseEvent) => {
    const canvasCoords = screenToCanvas(event.clientX, event.clientY)
    
    // Check for tool selection
    const clickedTool = positioned_tools.find(tool => 
      canvasCoords.x >= tool.x && canvasCoords.x <= tool.x + tool.width &&
      canvasCoords.y >= tool.y && canvasCoords.y <= tool.y + tool.height
    )
    
    if (clickedTool) {
      setSelectedTool(clickedTool)
      setSelectedCavalletto(null)
      onToolClick?.(clickedTool)
      return
    }
    
    // 🏗️ AGGIORNATO: Check for cavalletto selection (segmenti trasversali)
    // Raggruppa cavalletti per posizione X come nel rendering
    const cavallettiGrouped = new Map<number, Cavalletto[]>()
    cavalletti.forEach(cavalletto => {
      const xKey = Math.round(cavalletto.x)
      if (!cavallettiGrouped.has(xKey)) {
        cavallettiGrouped.set(xKey, [])
      }
      cavallettiGrouped.get(xKey)!.push(cavalletto)
    })
    
    // Verifica click su segmenti trasversali
    let clickedCavalletto: Cavalletto | null = null
    for (const [xPos, gruppo] of Array.from(cavallettiGrouped.entries())) {
      const segmentThickness = gruppo[0]?.height || 60
      
      // Verifica se il click è dentro il segmento trasversale
      if (canvasCoords.x >= xPos && 
          canvasCoords.x <= xPos + segmentThickness &&
          canvasCoords.y >= 0 && 
          canvasCoords.y <= canvas_height) {
        
        // Seleziona il primo cavalletto del gruppo (rappresentativo)
        clickedCavalletto = gruppo[0]
        break
      }
    }
    
    if (clickedCavalletto) {
      setSelectedCavalletto(clickedCavalletto)
      setSelectedTool(null)
      onStandClick?.(clickedCavalletto)
      return
    }
    
    // Start dragging
    setViewport(prev => ({
      ...prev,
      isDragging: true,
      lastPointerPos: { x: event.clientX, y: event.clientY }
    }))
    
    setSelectedTool(null)
    setSelectedCavalletto(null)
  }, [screenToCanvas, positioned_tools, cavalletti, canvas_height, onToolClick, onStandClick])

  const handleCanvasMouseUp = useCallback(() => {
    setViewport(prev => ({ ...prev, isDragging: false }))
  }, [])

  const handleWheel = useCallback((event: React.WheelEvent) => {
    event.preventDefault()
    
    const zoomDelta = event.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.max(0.1, Math.min(5, viewport.scale * zoomDelta))
    
    setViewport(prev => ({ ...prev, scale: newScale }))
  }, [viewport.scale])

  // 🎮 Control functions
  const handleZoom = (delta: number) => {
    const newScale = Math.max(0.1, Math.min(5, viewport.scale + delta))
    setViewport(prev => ({ ...prev, scale: newScale }))
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

  const toggleLayer = (layer: keyof LayerVisibility) => {
    if (typeof layerVisibility[layer] === 'boolean') {
      setLayerVisibility(prev => ({ ...prev, [layer]: !prev[layer] }))
    }
  }

  // 🎨 Canvas resize and render effects
  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return
    
    const resizeCanvas = () => {
      render()
    }
    
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    return () => window.removeEventListener('resize', resizeCanvas)
  }, [render])

  useEffect(() => {
    render()
  }, [render])

  // 📊 Statistics
  const stats = {
    level0Tools: positioned_tools.filter(t => t.level === 0).length,
    level1Tools: positioned_tools.filter(t => t.level === 1).length,
    totalCavalletti: cavalletti.length,
    totalWeight: positioned_tools.reduce((sum, tool) => sum + tool.weight_kg, 0),
    // 🆕 NUOVO: Statistiche più chiare
    cavallettiUtilizzati: cavalletti.length, // Numero di supporti fisici
    toolSuCavalletti: positioned_tools.filter(t => t.level === 1).length // Pezzi sui cavalletti
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* 🎮 Advanced Controls Toolbar */}
      <div className="flex flex-col gap-3 p-3 bg-slate-50 border-b border-slate-200">
        {/* Layer Controls Row 1 - Visibility */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-600">Layers:</span>
            <Button
              variant={layerVisibility.level0 ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('level0')}
              className={`gap-1 ${layerVisibility.isolationMode === 'level0' ? 'ring-2 ring-blue-400' : ''}`}
            >
              <Box className="w-4 h-4" />
              Piano ({stats.level0Tools})
            </Button>
            <Button
              variant={layerVisibility.level1 ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('level1')}
              className={`gap-1 ${layerVisibility.isolationMode === 'level1' ? 'ring-2 ring-orange-400' : ''}`}
            >
              <Building className="w-4 h-4" />
              Livello 1 ({stats.toolSuCavalletti})
            </Button>
            <Button
              variant={layerVisibility.cavalletti ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('cavalletti')}
              className={`gap-1 ${layerVisibility.isolationMode === 'cavalletti' ? 'ring-2 ring-slate-400' : ''}`}
            >
              <Target className="w-4 h-4" />
              Cavalletti ({stats.cavallettiUtilizzati})
            </Button>
          </div>
          
          {/* Isolation Mode Controls */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Modalità:</span>
            <Button
              variant={layerVisibility.isolationMode === 'none' ? "default" : "outline"}
              size="sm"
              onClick={() => setLayerVisibility(prev => ({ ...prev, isolationMode: 'none' }))}
              className="gap-1"
            >
              <Layers className="w-3 h-3" />
              Combinato
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const current = layerVisibility.isolationMode
                const modes: (typeof layerVisibility.isolationMode)[] = ['none', 'level0', 'level1', 'cavalletti']
                const currentIndex = modes.indexOf(current)
                const nextMode = modes[(currentIndex + 1) % modes.length]
                setLayerVisibility(prev => ({ ...prev, isolationMode: nextMode }))
              }}
              className="gap-1"
            >
              <Eye className="w-3 h-3" />
              Isola
            </Button>
          </div>
        </div>

        {/* Layer Controls Row 2 - Opacity & Advanced */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          {/* Opacity Controls */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">Trasparenza:</span>
            
            <div className="flex items-center gap-1">
              <Box className="w-3 h-3 text-blue-600" />
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={layerVisibility.level0Opacity}
                onChange={(e) => setLayerVisibility(prev => ({ 
                  ...prev, 
                  level0Opacity: parseFloat(e.target.value) 
                }))}
                className="w-12 h-1 bg-slate-200 rounded-lg"
              />
              <span className="text-xs font-mono text-slate-500 min-w-[30px]">
                {Math.round(layerVisibility.level0Opacity * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-1">
              <Building className="w-3 h-3 text-orange-600" />
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={layerVisibility.level1Opacity}
                onChange={(e) => setLayerVisibility(prev => ({ 
                  ...prev, 
                  level1Opacity: parseFloat(e.target.value) 
                }))}
                className="w-12 h-1 bg-slate-200 rounded-lg"
              />
              <span className="text-xs font-mono text-slate-500 min-w-[30px]">
                {Math.round(layerVisibility.level1Opacity * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-1">
              <Target className="w-3 h-3 text-slate-600" />
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={layerVisibility.cavallettiOpacity}
                onChange={(e) => setLayerVisibility(prev => ({ 
                  ...prev, 
                  cavallettiOpacity: parseFloat(e.target.value) 
                }))}
                className="w-12 h-1 bg-slate-200 rounded-lg"
              />
              <span className="text-xs font-mono text-slate-500 min-w-[30px]">
                {Math.round(layerVisibility.cavallettiOpacity * 100)}%
              </span>
            </div>
          </div>

          {/* Advanced Visual Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant={layerVisibility.showDepthIndicators ? "default" : "outline"}
              size="sm"
              onClick={() => setLayerVisibility(prev => ({ ...prev, showDepthIndicators: !prev.showDepthIndicators }))}
              className="gap-1"
            >
              <Package className="w-3 h-3" />
              Profondità
            </Button>
            <Button
              variant={layerVisibility.showZLevels ? "default" : "outline"}
              size="sm"
              onClick={() => setLayerVisibility(prev => ({ ...prev, showZLevels: !prev.showZLevels }))}
              className="gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Quote Z
            </Button>
          </div>
        </div>

        {/* View Controls Row 3 */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Button
              variant={layerVisibility.grid ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('grid')}
              className="gap-1"
            >
              <Grid3X3 className="w-4 h-4" />
              Griglia
            </Button>
            <Button
              variant={layerVisibility.dimensions ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('dimensions')}
              className="gap-1"
            >
              <Ruler className="w-4 h-4" />
              Quote
            </Button>
            <Button
              variant={layerVisibility.coordinates ? "default" : "outline"}
              size="sm"
              onClick={() => toggleLayer('coordinates')}
              className="gap-1"
            >
              <Info className="w-4 h-4" />
              Coordinate
            </Button>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => handleZoom(-0.2)}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-sm font-mono text-slate-600 min-w-[60px] text-center">
              {Math.round(viewport.scale * 100)}%
            </span>
            <Button variant="outline" size="sm" onClick={() => handleZoom(0.2)}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={resetView}>
              <Home className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setIsFullscreen(!isFullscreen)}>
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 📊 Stats Bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-white border-b border-slate-200">
        <div className="flex items-center gap-4 text-sm">
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            Piano: {stats.level0Tools} pezzi
          </Badge>
          <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
            Su cavalletti: {stats.toolSuCavalletti} pezzi
          </Badge>
          <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200">
            Cavalletti: {stats.cavallettiUtilizzati} supporti
          </Badge>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            Peso totale: {formatWeight(stats.totalWeight)}
          </Badge>
        </div>
        <div className="text-sm text-slate-500">
          Dimensioni: {formatDimension(canvas_width)} × {formatDimension(canvas_height)}
        </div>
      </div>

      {/* 🎨 Canvas Container */}
      <div 
        ref={containerRef}
        className={`flex-1 relative overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}
      >
        <canvas
          ref={canvasRef}
          className="w-full h-full cursor-grab active:cursor-grabbing"
          onMouseMove={handleCanvasMouseMove}
          onMouseDown={handleCanvasMouseDown}
          onMouseUp={handleCanvasMouseUp}
          onWheel={handleWheel}
        />
        
        {/* 📋 Tool Info Overlay */}
        {selectedTool && (
          <ToolInfoPanel2L
            tool={selectedTool}
            onClose={() => setSelectedTool(null)}
          />
        )}
        
        {/* 🏗️ Cavalletto Info Overlay */}
        {selectedCavalletto && (
          <CavallettoInfoPanel
            cavalletto={selectedCavalletto}
            onClose={() => setSelectedCavalletto(null)}
          />
        )}
      </div>
    </div>
  )
}

// 📋 Tool Info Panel Component
const ToolInfoPanel2L: React.FC<{
  tool: ToolPosition2L
  onClose: () => void
}> = ({ tool, onClose }) => {
  const info = getToolDisplayInfo(tool)
  
  return (
    <Card className="absolute top-4 right-4 w-80 bg-white/95 backdrop-blur-sm shadow-lg border border-slate-200">
          <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-slate-800">
            {info.numeroODL}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="font-medium text-slate-600">Part Number:</span>
            <div className="font-mono text-slate-800">{info.partNumber}</div>
          </div>
          <div>
            <span className="font-medium text-slate-600">Livello:</span>
            <div className="flex items-center gap-2">
              <Badge variant={tool.level === 0 ? "secondary" : "default"}>
                {info.levelText}
              </Badge>
            </div>
          </div>
              <div>
            <span className="font-medium text-slate-600">Dimensioni:</span>
            <div className="font-mono text-slate-800">{info.dimensioni}</div>
              </div>
              <div>
            <span className="font-medium text-slate-600">Peso:</span>
            <div className="font-mono text-slate-800">{info.peso}</div>
              </div>
              <div>
            <span className="font-medium text-slate-600">Posizione:</span>
            <div className="font-mono text-slate-800">
              ({Math.round(tool.x)}, {Math.round(tool.y)})
            </div>
              </div>
              <div>
            <span className="font-medium text-slate-600">Altezza:</span>
            <div className="font-mono text-slate-800">{info.altezza}</div>
          </div>
        </div>
        
        {info.descrizione && (
          <div>
            <span className="font-medium text-slate-600">Descrizione:</span>
            <div className="text-slate-800 mt-1">{info.descrizione}</div>
                  </div>
                )}
        
        <div className="flex items-center gap-2 pt-2 border-t border-slate-200">
          {tool.rotated && (
            <Badge variant="outline" className="text-orange-600 border-orange-300">
              <RotateCcw className="w-3 h-3 mr-1" />
              Ruotato
            </Badge>
          )}
          <Badge variant="outline" className="text-slate-600">
            <Package className="w-3 h-3 mr-1" />
            {tool.lines_used} linee vuoto
          </Badge>
            </div>
          </CardContent>
        </Card>
  )
}

// 🏗️ Cavalletto Info Panel Component
const CavallettoInfoPanel: React.FC<{
  cavalletto: Cavalletto
  onClose: () => void
}> = ({ cavalletto, onClose }) => {
  return (
    <Card className="absolute top-4 left-4 w-80 bg-white/95 backdrop-blur-sm shadow-lg border border-amber-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <Target className="w-5 h-5 text-amber-600" />
            Cavalletto #{cavalletto.sequence_number + 1}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="text-sm text-slate-600">
          Supporto fisico 1D per tool ODL #{cavalletto.tool_odl_id}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="font-medium text-slate-600">Supporta ODL:</span>
            <Badge variant="outline" className="font-mono text-blue-700 border-blue-300">
              #{cavalletto.tool_odl_id}
            </Badge>
          </div>
          <div>
            <span className="font-medium text-slate-600">Capacità carico:</span>
            <div className="font-mono text-green-700 font-semibold">{formatWeight(cavalletto.load_capacity_kg)}</div>
          </div>
          <div>
            <span className="font-medium text-slate-600">Dimensioni:</span>
            <div className="font-mono text-slate-800">
              {formatDimension(cavalletto.width)}×{formatDimension(cavalletto.height)}
            </div>
          </div>
          <div>
            <span className="font-medium text-slate-600">Altezza cavalletto:</span>
            <div className="font-mono text-amber-700 font-semibold">{formatDimension(cavalletto.height_mm)}</div>
          </div>
          <div>
            <span className="font-medium text-slate-600">Posizione:</span>
            <div className="font-mono text-slate-800">
              ({Math.round(cavalletto.x)}, {Math.round(cavalletto.y)})
            </div>
          </div>
          <div>
            <span className="font-medium text-slate-600">Area supporto:</span>
            <div className="font-mono text-slate-800">
              {(cavalletto.support_area_mm2 / 100).toFixed(1)} cm²
            </div>
          </div>
        </div>
        
        <Separator />
        
        <div className="bg-amber-50 p-3 rounded-md border border-amber-200">
          <div className="text-xs text-amber-800">
            <strong>💡 Funzione:</strong> Questo cavalletto è un supporto fisico che attraversa 
            il lato corto dell'autoclave ({formatDimension(cavalletto.width)} di larghezza) 
            per sostenere il tool al livello superiore.
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-slate-600">
            <Building className="w-3 h-3 mr-1" />
            Supporto livello 1
          </Badge>
          {cavalletto.tool_id && (
            <Badge variant="outline" className="text-slate-600">
              Tool ID: #{cavalletto.tool_id}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default NestingCanvas2L 