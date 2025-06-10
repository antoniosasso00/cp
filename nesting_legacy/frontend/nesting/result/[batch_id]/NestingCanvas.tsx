'use client'

import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { 
  Package, 
  AlertCircle, 
  CheckCircle, 
  Download, 
  ZoomIn, 
  ZoomOut,
  Maximize2,
  Grid3X3,
  Ruler,
  Info,
  RotateCcw,
  Target,
  Move,
  Square,
  Eye,
  EyeOff,
  X,
  Flame
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Switch } from '@/shared/components/ui/switch'
import { Label } from '@/shared/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/components/ui/tooltip'
import { useToast } from '@/components/ui/use-toast'
import { Separator } from '@/shared/components/ui/separator'

import CanvasWrapper, { 
  Layer, 
  Rect, 
  Text, 
  Group, 
  Line, 
  Circle,
  CanvasLoadingPlaceholder,
  useClientMount 
} from '@/shared/components/canvas/CanvasWrapper'

// ==================== INTERFACCE ====================

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
  onToolSelect?: (toolId: number | null) => void
  selectedToolId?: number | null
}

interface CanvasSettings {
  showGrid: boolean
  showRuler: boolean
  showTooltips: boolean
  showDimensions: boolean
  showCenter: boolean
  highlightOutOfBounds: boolean
}

interface ViewportState {
  zoom: number
  panX: number
  panY: number
  canvasWidth: number
  canvasHeight: number
}

// ==================== COSTANTI ====================

const COLORS = {
  // Traffic Light System
  success: '#22c55e',     // Verde - Tool validi
  warning: '#eab308',     // Giallo - Tool ruotati
  danger: '#ef4444',      // Rosso - Tool esclusi/errori
  info: '#3b82f6',        // Blu - Informazioni
  neutral: '#6b7280',     // Grigio - Elementi secondari
  
  // Background colors
  successBg: '#dcfce7',
  warningBg: '#fef3c7',
  dangerBg: '#fecaca',
  infoBg: '#dbeafe',
  
  // Canvas
  canvasBackground: '#f8fafc',
  autoclaveBackground: '#ffffff',
  autoclaveStroke: '#e2e8f0',
  gridColor: '#e5e7eb',
  rulerColor: '#374151',
  centerLineColor: '#f59e0b'
}

const DEFAULTS = {
  zoom: 1,
  minZoom: 0.1,
  maxZoom: 5,
  gridSpacing: 100, // 10cm
  rulerSpacing: 100,
  toolMinSize: 10,
  panSensitivity: 1,
  zoomSensitivity: 0.1
}

// ==================== UTILITY FUNCTIONS ====================

const normalizeToolData = (tool: ToolPosition): ToolPosition => ({
  ...tool,
  x: Number(tool.x) || 0,
  y: Number(tool.y) || 0,
  width: Math.max(Number(tool.width) || 50, DEFAULTS.toolMinSize),
  height: Math.max(Number(tool.height) || 50, DEFAULTS.toolMinSize),
  peso: Number(tool.peso) || 0,
  rotated: Boolean(tool.rotated === true || tool.rotated === 'true'),
  excluded: Boolean(tool.excluded)
})

const formatDimension = (mm: number): string => {
  if (mm >= 1000) return `${(mm / 1000).toFixed(1)}m`
  if (mm >= 100) return `${(mm / 10).toFixed(1)}cm`
  return `${mm.toFixed(0)}mm`
}

const getToolColor = (tool: ToolPosition, isOutOfBounds: boolean, isSelected: boolean) => {
  let baseColor = COLORS.success
  let strokeColor = COLORS.success
  
  if (tool.excluded) {
    baseColor = COLORS.danger
    strokeColor = COLORS.danger
  } else if (isOutOfBounds) {
    baseColor = COLORS.warning
    strokeColor = COLORS.warning
  } else if (tool.rotated) {
    baseColor = '#34d399' // Verde più chiaro per ruotati
    strokeColor = COLORS.success
  }
  
  return {
    fill: isSelected ? baseColor : baseColor + 'CC', // 80% opacity when not selected
    stroke: strokeColor,
    strokeWidth: isSelected ? 3 : 1.5,
    opacity: isSelected ? 1 : 0.9
  }
}

// ==================== COMPONENTI CANVAS ====================

const GridLayer: React.FC<{ 
  width: number
  height: number
  settings: CanvasSettings
  viewport: ViewportState
}> = ({ width, height, settings, viewport }) => {
  const lines = useMemo(() => {
    if (!settings.showGrid) return []
    
    const spacing = DEFAULTS.gridSpacing
    const gridLines: number[] = []
    
    // Ottimizzazione: mostra griglia solo se zoom > 0.3
    if (viewport.zoom < 0.3) return []
    
    // Linee verticali ogni 10cm
    for (let x = 0; x <= width; x += spacing) {
      gridLines.push(x, 0, x, height)
    }
    
    // Linee orizzontali ogni 10cm  
    for (let y = 0; y <= height; y += spacing) {
      gridLines.push(0, y, width, y)
    }
    
    return gridLines
  }, [width, height, settings.showGrid, viewport.zoom])

  const rulerMarks = useMemo(() => {
    if (!settings.showRuler || viewport.zoom < 0.5) return []
    
    const spacing = DEFAULTS.rulerSpacing
    const marks: Array<{ x: number, y: number, text: string, type: 'horizontal' | 'vertical' }> = []
    
    // Righello orizzontale (max 30 marks per performance)
    for (let i = 0; i <= Math.min(Math.floor(width / spacing), 30); i += 2) {
      const x = i * spacing
      marks.push({
        x: x + 5,
        y: 15,
        text: `${(x / 10).toFixed(0)}cm`,
        type: 'horizontal'
      })
    }
    
    // Righello verticale (max 25 marks per performance)
    for (let i = 0; i <= Math.min(Math.floor(height / spacing), 25); i += 2) {
      const y = i * spacing
      marks.push({
        x: 25,
        y: y + 5,
        text: `${(y / 10).toFixed(0)}cm`,
        type: 'vertical'
      })
    }
    
    return marks
  }, [width, height, settings.showRuler, viewport.zoom])

  if (!settings.showGrid && !settings.showRuler) return null
  
  return (
    <Group>
      {/* Griglia */}
      {lines.length > 0 && (
        <Line
          points={lines}
          stroke={COLORS.gridColor}
          strokeWidth={0.5}
          opacity={0.6}
        />
      )}
      
      {/* Linee righello */}
      {settings.showRuler && (
        <Group>
          {rulerMarks.map((mark, i) => (
            <Group key={i}>
              {mark.type === 'horizontal' ? (
                <>
                  <Line
                    points={[mark.x - 5, 0, mark.x - 5, 20]}
                    stroke={COLORS.rulerColor}
                    strokeWidth={1}
                  />
                  <Text
                    x={mark.x}
                    y={mark.y}
                    text={mark.text}
                    fontSize={Math.max(10, 10 * viewport.zoom)}
                    fill={COLORS.rulerColor}
                    opacity={0.8}
                  />
                </>
              ) : (
                <>
                  <Line
                    points={[0, mark.y - 5, 20, mark.y - 5]}
                    stroke={COLORS.rulerColor}
                    strokeWidth={1}
                  />
                  <Text
                    x={mark.x}
                    y={mark.y}
                    text={mark.text}
                    fontSize={Math.max(10, 10 * viewport.zoom)}
                    fill={COLORS.rulerColor}
                    opacity={0.8}
                    rotation={-90}
                  />
                </>
              )}
            </Group>
          ))}
        </Group>
      )}
      
      {/* Centro autoclave */}
      {settings.showCenter && (
        <Group>
          <Line
            points={[width / 2 - 20, height / 2, width / 2 + 20, height / 2]}
            stroke={COLORS.centerLineColor}
            strokeWidth={2}
            opacity={0.7}
          />
          <Line
            points={[width / 2, height / 2 - 20, width / 2, height / 2 + 20]}
            stroke={COLORS.centerLineColor}
            strokeWidth={2}
            opacity={0.7}
          />
          <Circle
            x={width / 2}
            y={height / 2}
            radius={5}
            fill={COLORS.centerLineColor}
            opacity={0.7}
          />
        </Group>
      )}
    </Group>
  )
}

const ToolRect: React.FC<{ 
  tool: ToolPosition
  onClick?: () => void
  isSelected?: boolean
  autoclaveWidth: number
  autoclaveHeight: number
  settings: CanvasSettings
  viewport: ViewportState
}> = ({ tool, onClick, isSelected = false, autoclaveWidth, autoclaveHeight, settings, viewport }) => {
  
  const isOutOfBoundsX = tool.x + tool.width > autoclaveWidth
  const isOutOfBoundsY = tool.y + tool.height > autoclaveHeight
  const isOutOfBounds = isOutOfBoundsX || isOutOfBoundsY
  
  const colors = getToolColor(tool, isOutOfBounds, isSelected)
  
  // ✅ CALCOLO FONT SIZE DINAMICO BASATO SU AREA
  const area = tool.width * tool.height
  const baseFontSize = Math.min(
    Math.max(6, Math.log10(area / 100) * 2), // Scala logaritmica 6-16px
    Math.min(tool.width / 8, tool.height / 4) // Limitato dalle dimensioni
  )
  
  // ✅ PREPARAZIONE TESTI INFORMATIVI
  const numeroODL = tool.numero_odl || `ODL${String(tool.odl_id).padStart(3, '0')}`
  const partNumber = tool.part_number || 'N/A'
  const toolCode = tool.part_number_tool || tool.tool_nome || 'TOOL'
  const descrizione = tool.descrizione_breve || ''
  const dimensioni = `${formatDimension(tool.width)} × ${formatDimension(tool.height)}`
  
  // ✅ LOGICA ADATTIVA PER CONTENUTO
  const showDetails = viewport.zoom > 0.4 && baseFontSize >= 6
  const showText = viewport.zoom > 0.6 && baseFontSize >= 8
  const showFullDetails = viewport.zoom > 0.8 && tool.height > 60 && baseFontSize >= 10
  
  return (
    <Group>
      {/* Rettangolo principale tool */}
      <Rect
        x={tool.x}
        y={tool.y}
        width={tool.width}
        height={tool.height}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={colors.strokeWidth}
        opacity={colors.opacity}
        onClick={onClick}
        onTap={onClick}
        cornerRadius={2}
        perfectDrawEnabled={false} // Performance optimization
        shadowColor={isSelected ? '#000000' : undefined}
        shadowOpacity={isSelected ? 0.3 : 0}
        shadowOffsetX={isSelected ? 2 : 0}
        shadowOffsetY={isSelected ? 2 : 0}
        shadowBlur={isSelected ? 6 : 0}
      />
      
      {/* Indicatore rotazione */}
      {tool.rotated && showDetails && (
        <Group>
          <Circle
            x={tool.x + tool.width - 8}
            y={tool.y + 8}
            radius={6}
            fill={COLORS.warning}
            stroke={COLORS.canvasBackground}
            strokeWidth={1}
          />
          <Text
            x={tool.x + tool.width - 8}
            y={tool.y + 8}
            text="R"
            fontSize={8}
            fill={COLORS.canvasBackground}
            align="center"
            verticalAlign="middle"
          />
        </Group>
      )}
      
      {/* ✅ CONTENUTO MULTILINEA MIGLIORATO */}
      {showText && (
        <Group>
          {/* Background semi-trasparente per migliore leggibilità */}
          {showFullDetails && (
            <Rect
              x={tool.x + 2}
              y={tool.y + 2}
              width={tool.width - 4}
              height={baseFontSize * 4 + 20}
              fill="rgba(255, 255, 255, 0.9)"
              cornerRadius={2}
              opacity={0.8}
            />
          )}
          
          {/* Linea 1: Numero ODL (sempre priorità) */}
          <Text
            x={tool.x + tool.width / 2}
            y={tool.y + baseFontSize + 8}
            text={numeroODL}
            fontSize={baseFontSize}
            fill="#1f2937"
            align="center"
            verticalAlign="middle"
            fontStyle="bold"
          />
          
          {/* Linea 2: Part Number (se c'è spazio) */}
          {showFullDetails && (
            <Text
              x={tool.x + tool.width / 2}
              y={tool.y + baseFontSize * 2 + 12}
              text={partNumber}
              fontSize={Math.max(7, baseFontSize - 1)}
              fill="#374151"
              align="center"
              verticalAlign="middle"
              fontStyle="bold"
            />
          )}
          
          {/* Linea 3: Descrizione breve (se c'è spazio) */}
          {showFullDetails && tool.height > 80 && descrizione && (
            <Text
              x={tool.x + tool.width / 2}
              y={tool.y + baseFontSize * 3 + 16}
              text={descrizione.length > 25 ? descrizione.substring(0, 22) + '...' : descrizione}
              fontSize={Math.max(6, baseFontSize - 2)}
              fill="#4b5563"
              align="center"
              verticalAlign="middle"
            />
          )}
          
          {/* Linea 4: Dimensioni (solo per tool grandi) */}
          {showFullDetails && tool.height > 100 && (
            <Text
              x={tool.x + tool.width / 2}
              y={tool.y + baseFontSize * 4 + 20}
              text={dimensioni}
              fontSize={Math.max(6, baseFontSize - 3)}
              fill="#6b7280"
              align="center"
              verticalAlign="middle"
              fontStyle="italic"
            />
          )}
          
          {/* Peso nell'angolo in basso a destra */}
          {tool.peso > 0 && tool.height > 40 && (
            <Text
              x={tool.x + tool.width - 8}
              y={tool.y + tool.height - 8}
              text={`${tool.peso}kg`}
              fontSize={Math.max(7, baseFontSize - 2)}
              fill="#1f2937"
              align="right"
              verticalAlign="bottom"
              fontStyle="bold"
            />
          )}
        </Group>
      )}
      
      {/* ✅ DIMENSIONI ESTERNE (se abilitate) */}
      {settings.showDimensions && showDetails && (
        <Group>
          <Text
            x={tool.x}
            y={tool.y - 8}
            text={dimensioni}
            fontSize={Math.max(8, baseFontSize)}
            fill={COLORS.neutral}
            opacity={0.9}
            fontStyle="bold"
          />
        </Group>
      )}
      
      {/* Highlight out of bounds */}
      {isOutOfBounds && settings.highlightOutOfBounds && (
        <Group>
          <Rect
            x={tool.x - 2}
            y={tool.y - 2}
            width={tool.width + 4}
            height={tool.height + 4}
            stroke={COLORS.danger}
            strokeWidth={2}
            fill="transparent"
            dash={[5, 5]}
            opacity={0.8}
          />
        </Group>
      )}
    </Group>
  )
}

const AutoclaveOutline: React.FC<{
  width: number
  height: number
  autoclave: AutoclaveInfo
}> = ({ width, height, autoclave }) => (
  <Group>
    {/* Sfondo autoclave */}
    <Rect
      x={0}
      y={0}
      width={width}
      height={height}
      fill={COLORS.autoclaveBackground}
      stroke={COLORS.autoclaveStroke}
      strokeWidth={2}
      cornerRadius={4}
    />
    
    {/* ✅ ETICHETTA AUTOCLAVE DISCRETA */}
    <Group>
      <Rect
        x={width - 160}
        y={10}
        width={150}
        height={25}
        fill={COLORS.infoBg}
        stroke={COLORS.info}
        strokeWidth={1}
        cornerRadius={6}
        opacity={0.85}
      />
      <Text
        x={width - 155}
        y={20}
        text={autoclave.nome}
        fontSize={10}
        fill={COLORS.info}
        fontStyle="bold"
      />
      <Text
        x={width - 155}
        y={32}
        text={`${formatDimension(width)} × ${formatDimension(height)}`}
        fontSize={8}
        fill={COLORS.neutral}
        opacity={0.8}
      />
    </Group>
  </Group>
)

const CanvasControls: React.FC<{
  viewport: ViewportState
  settings: CanvasSettings
  onZoomIn: () => void
  onZoomOut: () => void
  onZoomReset: () => void
  onAutoFit: () => void
  onSettingsChange: (settings: Partial<CanvasSettings>) => void
  totalTools: number
  validTools: number
  excludedTools: number
}> = ({ viewport, settings, onZoomIn, onZoomOut, onZoomReset, onAutoFit, onSettingsChange, totalTools, validTools, excludedTools }) => (
  <div className="absolute top-4 left-4 z-10 space-y-2 max-w-xs">
    {/* ✅ CONTROLLI ZOOM COMPATTI */}
    <Card className="p-2 bg-white/95 backdrop-blur-sm shadow-lg border border-gray-200">
      <div className="flex items-center gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onZoomOut}>
                <ZoomOut className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Zoom Out</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <div className="min-w-[60px] text-center">
          <span className="text-xs font-medium text-gray-700">{Math.round(viewport.zoom * 100)}%</span>
        </div>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onZoomIn}>
                <ZoomIn className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Zoom In</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onZoomReset}>
                <RotateCcw className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Reset Zoom</TooltipContent>
          </Tooltip>
        </TooltipProvider>
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onAutoFit}>
                <Maximize2 className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Auto Fit</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </Card>

    {/* ✅ CONTROLLI VISUALIZZAZIONE COMPATTI */}
    <Card className="p-2 bg-white/95 backdrop-blur-sm shadow-lg border border-gray-200">
      <div className="space-y-2">
        <div className="text-xs font-medium text-gray-700 mb-1">Visualizzazione</div>
        
        <div className="grid grid-cols-2 gap-2">
          <div className="flex items-center gap-1.5">
            <Switch
              checked={settings.showGrid}
              onCheckedChange={(checked) => onSettingsChange({ showGrid: checked })}
            />
            <Label className="text-xs text-gray-600">Griglia</Label>
          </div>
          
          <div className="flex items-center gap-1.5">
            <Switch
              checked={settings.showRuler}
              onCheckedChange={(checked) => onSettingsChange({ showRuler: checked })}
            />
            <Label className="text-xs text-gray-600">Righello</Label>
          </div>
          
          <div className="flex items-center gap-1.5">
            <Switch
              checked={settings.showDimensions}
              onCheckedChange={(checked) => onSettingsChange({ showDimensions: checked })}
            />
            <Label className="text-xs text-gray-600">Quote</Label>
          </div>
          
          <div className="flex items-center gap-1.5">
            <Switch
              checked={settings.showTooltips}
              onCheckedChange={(checked) => onSettingsChange({ showTooltips: checked })}
            />
            <Label className="text-xs text-gray-600">Info</Label>
          </div>
        </div>
      </div>
    </Card>

    {/* ✅ STATISTICHE COMPATTE */}
    <Card className="p-2 bg-white/95 backdrop-blur-sm shadow-lg border border-gray-200">
      <div className="space-y-1">
        <div className="text-xs font-medium text-gray-700">Tool</div>
        <div className="flex justify-between text-xs">
          <span className="text-green-600">Validi: {validTools}</span>
          {excludedTools > 0 && <span className="text-red-600">Esclusi: {excludedTools}</span>}
        </div>
        <div className="text-xs text-gray-500">Totale: {totalTools} componenti</div>
      </div>
    </Card>
  </div>
)

const ToolInfoPanel: React.FC<{
  tool: ToolPosition | null
  autoclave: AutoclaveInfo
  onClose: () => void
}> = ({ tool, autoclave, onClose }) => {
  if (!tool) return null

  const numeroODL = tool.numero_odl || `ODL${String(tool.odl_id).padStart(3, '0')}`
  const partNumber = tool.part_number || 'N/A'
  const toolCode = tool.part_number_tool || tool.tool_nome || 'N/A'
  const descrizione = tool.descrizione_breve || 'Nessuna descrizione'
  const dimensioni = `${formatDimension(tool.width)} × ${formatDimension(tool.height)}`
  const area = (tool.width * tool.height) / 1000000 // m²
  const posizione = `${formatDimension(tool.x)}, ${formatDimension(tool.y)}`

  return (
    <div className="absolute top-4 right-4 z-20 w-80">
      <Card className="bg-white/95 backdrop-blur-sm shadow-lg border border-gray-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4" />
              {numeroODL}
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
                <span className="font-medium font-mono">{partNumber}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tool Code:</span>
                <span className="font-medium font-mono">{toolCode}</span>
              </div>
              <div className="bg-gray-50 p-2 rounded">
                <span className="text-gray-600">Descrizione:</span>
                <p className="font-medium mt-1">{descrizione}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Informazioni Geometriche */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-800 flex items-center gap-1">
              <Ruler className="h-3 w-3" />
              Dimensioni & Posizionamento
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Larghezza:</span>
                  <span className="font-medium">{formatDimension(tool.width)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Altezza:</span>
                  <span className="font-medium">{formatDimension(tool.height)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Area:</span>
                  <span className="font-medium">{area.toFixed(3)} m²</span>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Posizione X:</span>
                  <span className="font-medium">{formatDimension(tool.x)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Posizione Y:</span>
                  <span className="font-medium">{formatDimension(tool.y)}</span>
                </div>
                {tool.peso > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Peso:</span>
                    <span className="font-medium">{tool.peso} kg</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Informazioni Autoclave */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-800 flex items-center gap-1">
              <Flame className="h-3 w-3" />
              Autoclave
            </h4>
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-600">Nome:</span>
                <span className="font-medium">{autoclave.nome}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Codice:</span>
                <span className="font-medium">{autoclave.codice}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Dimensioni Piano:</span>
                <span className="font-medium">{formatDimension(autoclave.lunghezza)} × {formatDimension(autoclave.larghezza_piano)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ==================== COMPONENTE PRINCIPALE ====================

const NestingCanvas: React.FC<NestingCanvasProps> = ({ 
  batchData, 
  className = "",
  onToolSelect,
  selectedToolId
}) => {
  const { toast } = useToast()
  const isMounted = useClientMount()
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Stati principali
  const [viewport, setViewport] = useState<ViewportState>({
    zoom: DEFAULTS.zoom,
    panX: 0,
    panY: 0,
    canvasWidth: 800,
    canvasHeight: 600
  })
  
  const [settings, setSettings] = useState<CanvasSettings>({
    showGrid: true,
    showRuler: true,
    showTooltips: true,
    showDimensions: true,
    showCenter: false,
    highlightOutOfBounds: true
  })
  
  const [selectedTool, setSelectedTool] = useState<number | null>(selectedToolId || null)
  const [isLoading, setIsLoading] = useState(true)

  // Dati processati
  const processedData = useMemo(() => {
    if (!batchData?.configurazione_json) return null
    
    const config = batchData.configurazione_json
    const autoclave = batchData.autoclave
    
    if (!autoclave) return null
    
    const toolPositions = (config.tool_positions || []).map(normalizeToolData)
    const autoclaveWidth = autoclave.lunghezza
    const autoclaveHeight = autoclave.larghezza_piano
    
    const validTools = toolPositions.filter(tool => !tool.excluded)
    const excludedTools = toolPositions.filter(tool => tool.excluded)
    
    return {
      toolPositions,
      validTools,
      excludedTools,
      autoclave,
      autoclaveWidth,
      autoclaveHeight,
      efficiency: batchData.metrics?.efficiency_percentage || 0
    }
  }, [batchData])

  // Gestione dimensioni canvas
  useEffect(() => {
    const updateCanvasSize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setViewport(prev => ({
          ...prev,
          canvasWidth: rect.width,
          canvasHeight: rect.height
        }))
      }
    }

    updateCanvasSize()
    window.addEventListener('resize', updateCanvasSize)
    return () => window.removeEventListener('resize', updateCanvasSize)
  }, [])

  // Gestione loading
  useEffect(() => {
    if (processedData) {
      setIsLoading(false)
    }
  }, [processedData])

  // Controlli zoom e pan
  const handleZoomIn = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      zoom: Math.min(prev.zoom * 1.25, DEFAULTS.maxZoom)
    }))
  }, [])

  const handleZoomOut = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      zoom: Math.max(prev.zoom / 1.25, DEFAULTS.minZoom)
    }))
  }, [])

  const handleZoomReset = useCallback(() => {
    setViewport(prev => ({
      ...prev,
      zoom: DEFAULTS.zoom,
      panX: 0,
      panY: 0
    }))
  }, [])

  const handleAutoFit = useCallback(() => {
    if (!processedData) return
    
    const { autoclaveWidth, autoclaveHeight } = processedData
    const { canvasWidth, canvasHeight } = viewport
    
    const scaleX = (canvasWidth - 100) / autoclaveWidth
    const scaleY = (canvasHeight - 100) / autoclaveHeight
    const optimalZoom = Math.min(scaleX, scaleY, DEFAULTS.maxZoom)
    
    setViewport(prev => ({
      ...prev,
      zoom: optimalZoom,
      panX: (canvasWidth - autoclaveWidth * optimalZoom) / 2,
      panY: (canvasHeight - autoclaveHeight * optimalZoom) / 2
    }))
  }, [processedData, viewport.canvasWidth, viewport.canvasHeight])

  // Gestione selezione tool
  const handleToolClick = useCallback((toolId: number) => {
    const newSelection = selectedTool === toolId ? null : toolId
    setSelectedTool(newSelection)
    onToolSelect?.(newSelection)
  }, [selectedTool, onToolSelect])

  const handleSettingsChange = useCallback((newSettings: Partial<CanvasSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }))
  }, [])

  // Gestione tool selezionato
  const selectedToolData = useMemo(() => {
    if (!selectedTool || !processedData) return null
    return processedData.toolPositions.find(tool => tool.odl_id === selectedTool) || null
  }, [selectedTool, processedData])

  if (!isMounted) {
    return <CanvasLoadingPlaceholder />
  }

  if (isLoading || !processedData) {
    return (
      <div className={`flex items-center justify-center min-h-[600px] bg-gray-50 border border-gray-200 rounded-lg ${className}`}>
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <div>
            <p className="text-sm font-medium text-gray-700">Caricamento Canvas</p>
            <p className="text-xs text-gray-500">Preparazione visualizzazione nesting...</p>
          </div>
        </div>
      </div>
    )
  }

  const { toolPositions, validTools, excludedTools, autoclave, autoclaveWidth, autoclaveHeight } = processedData

  return (
    <div className={`relative w-full h-full min-h-[600px] bg-gray-50 border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Container Canvas */}
      <div ref={containerRef} className="w-full h-full">
        <CanvasWrapper
          width={viewport.canvasWidth}
          height={viewport.canvasHeight}
          scaleX={viewport.zoom}
          scaleY={viewport.zoom}
          x={viewport.panX}
          y={viewport.panY}
          draggable={true}
          onDragEnd={(e: any) => {
            setViewport(prev => ({
              ...prev,
              panX: e.target.x(),
              panY: e.target.y()
            }))
          }}
        >
          <Layer>
            {/* Sfondo e outline autoclave */}
            <AutoclaveOutline
              width={autoclaveWidth} 
              height={autoclaveHeight} 
              autoclave={autoclave}
            />
            
            {/* Griglia e righello */}
            <GridLayer
              width={autoclaveWidth}
              height={autoclaveHeight}
              settings={settings}
              viewport={viewport}
            />
            
            {/* Tool positions */}
            {toolPositions.map((tool) => (
              <ToolRect
                key={tool.odl_id}
                tool={tool}
                onClick={() => handleToolClick(tool.odl_id)}
                isSelected={selectedTool === tool.odl_id}
                autoclaveWidth={autoclaveWidth}
                autoclaveHeight={autoclaveHeight}
                settings={settings}
                viewport={viewport}
              />
            ))}
          </Layer>
        </CanvasWrapper>
      </div>

      {/* Controlli Canvas */}
      <CanvasControls
        viewport={viewport}
        settings={settings}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onZoomReset={handleZoomReset}
        onAutoFit={handleAutoFit}
        onSettingsChange={handleSettingsChange}
        totalTools={toolPositions.length}
        validTools={validTools.length}
        excludedTools={excludedTools.length}
      />
      
      {/* Pannello info tool selezionato */}
      <ToolInfoPanel
        tool={selectedToolData}
        autoclave={autoclave}
        onClose={() => handleToolClick(selectedTool!)}
      />
    </div>
  )
}

export default NestingCanvas 