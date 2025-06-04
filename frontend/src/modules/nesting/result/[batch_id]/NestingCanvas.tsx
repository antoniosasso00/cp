'use client'

import React, { useEffect, useState, useCallback, useRef, useLayoutEffect } from 'react'
import { Package, AlertCircle, Loader2, Info, CheckCircle, TrendingUp, TrendingDown, Download, Grid3X3, Ruler, ZoomIn, ZoomOut } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useToast } from '@/components/ui/use-toast'
// ✅ NUOVO: Import del wrapper centralizzato per react-konva
import CanvasWrapper, { 
  Layer, 
  Rect, 
  Text, 
  Group, 
  Line, 
  CanvasLoadingPlaceholder,
  useClientMount 
} from '@/components/canvas/CanvasWrapper'

// ✅ NUOVO v1.4.18-DEMO: Interfacce aggiornate
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
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
}

interface ValidationResult {
  in_bounds: boolean
  no_overlap: boolean
  overlaps: [number, number][]
  scale_ok: boolean
  details: {
    total_pieces: number
    out_of_bounds_pieces: number
    overlapping_pairs: number
    area_ratio_pct: number
    autoclave_dimensions: string
  }
}

// 🎯 NUOVO v1.4.19-DEMO: Interfacce per debug SVG
interface DebugDifference {
  odl_id: number
  dx: number
  dy: number
  dW: number
  dH: number
  error_mm: number
}

interface DebugState {
  showGroundTruth: boolean
  useSvgOnly: boolean
  svgContent: string | null
  differences: DebugDifference[]
  scaleError: number
}

interface NestingCanvasProps {
  batchData: {
    configurazione_json: {
      canvas_width: number
      canvas_height: number
      tool_positions: ToolPosition[]
      autoclave_mm?: [number, number]  // 🎯 NUOVO: Dimensioni autoclave in mm
      bounding_px?: [number, number]   // 🎯 NUOVO: Dimensioni container in px
    } | null
    autoclave: AutoclaveInfo | undefined
    metrics?: any
    id?: string
  }
  className?: string
}

// ✅ NUOVO v1.4.18-DEMO: Normalizzazione dati
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

// ✅ NUOVO v1.4.18-DEMO: Hook di validazione
const useNestingValidation = (batchId?: string) => {
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!batchId) return

    const fetchValidation = async () => {
      setLoading(true)
      try {
        const response = await fetch(`/api/v1/batch_nesting/${batchId}/validate`)
        if (response.ok) {
          const data = await response.json()
          setValidation(data)
        }
      } catch (error) {
        console.error('Errore validazione:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchValidation()
  }, [batchId])

  return { validation, loading }
}

// ✅ NUOVO v1.4.18-DEMO: Badge di validazione con colori
const ValidationBadge: React.FC<{ validation: ValidationResult | null, loading: boolean }> = ({ validation, loading }) => {
  const { toast } = useToast()

  useEffect(() => {
    if (validation && (!validation.no_overlap || !validation.scale_ok)) {
      toast({
        title: "⚠️ Layout da ricontrollare",
        description: validation.no_overlap ? "Proporzioni non ottimali" : "Overlap rilevato tra pezzi",
        variant: "destructive"
      })
    }
  }, [validation, toast])

  if (loading) {
    return <Badge variant="outline"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Validazione...</Badge>
  }

  if (!validation) {
    return <Badge variant="outline">Nessuna validazione</Badge>
  }

  const hasIssues = !validation.in_bounds || !validation.no_overlap || !validation.scale_ok

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className={hasIssues ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-green-600 hover:bg-green-700 text-white'}>
            {hasIssues ? <AlertCircle className="h-3 w-3 mr-1" /> : <CheckCircle className="h-3 w-3 mr-1" />}
            {hasIssues ? '⚠ Layout da ricontrollare' : '✅ Layout OK'}
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-2">
            <p className="font-semibold">Dettagli Validazione</p>
            <div className="text-sm space-y-1">
              <div>🎯 <strong>Pezzi totali:</strong> {validation.details.total_pieces}</div>
              <div>📐 <strong>Bounds:</strong> {validation.in_bounds ? '✅ OK' : '❌ Fuori limiti'}</div>
              <div>🔲 <strong>Overlap:</strong> {validation.no_overlap ? '✅ Nessuno' : `❌ ${validation.overlaps.length} rilevati`}</div>
              <div>📏 <strong>Scala:</strong> {validation.scale_ok ? '✅ OK' : '❌ Non ottimale'} ({validation.details.area_ratio_pct.toFixed(1)}%)</div>
              <div>🏭 <strong>Autoclave:</strong> {validation.details.autoclave_dimensions}</div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// 🎯 AGGIORNATO v1.4.20-DEMO: Griglia con coordinate mm native
const GridLayer: React.FC<{ width: number, height: number, scale: number }> = ({ width, height, scale }) => {
  const gridSpacing_mm = 100 // Spaziatura griglia in mm (ogni 100mm)
  const lines: number[] = []
  
  // Linee verticali (coordinate in mm)
  for (let x = 0; x <= width; x += gridSpacing_mm) {
    lines.push(x, 0, x, height)
  }
  
  // Linee orizzontali (coordinate in mm)
  for (let y = 0; y <= height; y += gridSpacing_mm) {
    lines.push(0, y, width, y)
  }

  return (
    <Line
      points={lines}
      stroke="#e5e7eb"
      strokeWidth={1}
      dash={[5, 5]}
      opacity={0.5}
    />
  )
}

// 🎯 AGGIORNATO v1.4.20-DEMO: Righello con coordinate mm native
const RulerLayer: React.FC<{ width: number, height: number, scale: number }> = ({ width, height, scale }) => {
  const markerSpacing_mm = 200 // Marker ogni 200mm
  const rulers: JSX.Element[] = []
  
  // Righello superiore
  for (let x = 0; x <= width; x += markerSpacing_mm) {
    rulers.push(
      <Text
        key={`top-${x}`}
        x={x - 15}
        y={5}
        text={`${x}mm`}
        fontSize={10}
        fill="#6b7280"
      />
    )
  }
  
  // Righello sinistro
  for (let y = 0; y <= height; y += markerSpacing_mm) {
    rulers.push(
      <Text
        key={`left-${y}`}
        x={5}
        y={y - 5}
        text={`${y}mm`}
        fontSize={10}
        fill="#6b7280"
      />
    )
  }
  
  return <>{rulers}</>
}

// ✅ NUOVO v1.4.18-DEMO: Componente autoclave outline
const AutoclaveOutline: React.FC<{ autoclave: AutoclaveInfo, scale: number }> = ({ autoclave, scale }) => {
  const width = (autoclave.larghezza_piano || autoclave.lunghezza || 2000) * scale
  const height = (autoclave.larghezza_piano || 1200) * scale
  
  return (
    <Group>
      <Rect
        x={0}
        y={0}
        width={width}
        height={height}
        stroke="#3b82f6"
        strokeWidth={2}
        dash={[10, 5]}
        fill="transparent"
      />
      <Text
        x={width - 120}
        y={height - 25}
        text={`${Math.round(width/scale)} × ${Math.round(height/scale)} mm`}
        fontSize={12}
        fill="#3b82f6"
        fontStyle="bold"
      />
    </Group>
  )
}

// 🎯 AGGIORNATO v1.4.20-DEMO: Componente tool con coordinate mm native
const ToolRect: React.FC<{ 
  tool: ToolPosition, 
  scale: number, 
  isOverlapping?: boolean,
  onClick?: () => void 
}> = ({ tool, scale, isOverlapping, onClick }) => {
  const [hovered, setHovered] = useState(false)
  
  // Coordinate già in mm - non applico più lo scaling qui
  const x = tool.x
  const y = tool.y
  const width = tool.width
  const height = tool.height
  
  const fillColor = isOverlapping ? '#ef4444' : '#2563eb'
  const strokeWidth = tool.rotated ? 3 : 1
  const opacity = hovered ? 0.8 : 0.7

  return (
    <Group
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fillColor}
        stroke={isOverlapping ? '#dc2626' : '#1d4ed8'}
        strokeWidth={strokeWidth}
        opacity={opacity}
      />
      <Text
        x={x + width/2}
        y={y + height/2}
        text={`ODL ${tool.odl_id}\n${Math.round(tool.width)}×${Math.round(tool.height)}mm${tool.rotated ? '\n🔄' : ''}`}
        fontSize={Math.max(8, Math.min(14, width/15))}
        fill="white"
        align="center"
        verticalAlign="middle"
      />
      {tool.rotated && (
        <Rect
          x={x + width - 15}
          y={y + 5}
          width={10}
          height={10}
          fill="#fbbf24"
          stroke="#f59e0b"
          strokeWidth={1}
          cornerRadius={2}
        />
      )}
    </Group>
  )
}

// ✅ NUOVO v1.4.18-DEMO: Legenda
const LegendCard: React.FC = () => (
  <Card className="absolute top-4 right-4 w-64 z-10 bg-white/95 backdrop-blur">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm flex items-center gap-2">
        <Info className="h-4 w-4" />
        Legenda Canvas
      </CardTitle>
    </CardHeader>
    <CardContent className="text-xs space-y-2">
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 bg-blue-600 rounded"></div>
        <span>Tool posizionati</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 bg-red-600 rounded"></div>
        <span>Tool con overlap</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-4 h-1 border-2 border-dashed border-blue-500"></div>
        <span>Contorno autoclave</span>
      </div>
      <div className="flex items-center gap-2">
        <Grid3X3 className="h-4 w-4 text-gray-400" />
        <span>Griglia 100mm</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-600"></div>
        <span>Origine (0,0)</span>
      </div>
    </CardContent>
  </Card>
)

// ✅ Error Boundary per il Canvas
class CanvasErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: string }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { 
      hasError: true, 
      error: error.message 
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Canvas Error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-96 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-center space-y-3">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">Errore Canvas</h3>
              <p className="text-red-600">{this.state.error || 'Errore sconosciuto nel rendering'}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-3"
                onClick={() => window.location.reload()}
              >
                Ricarica Pagina
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// ✅ NUOVO v1.4.19-DEMO: Canvas interattivo principale
const InteractiveCanvas: React.FC<{
  toolPositions: ToolPosition[]
  autoclave: AutoclaveInfo
  validation: ValidationResult | null
}> = ({ toolPositions, autoclave, validation }) => {
  const stageRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [zoom, setZoom] = useState<number>(1)
  const { toast } = useToast()
  
  // 🎯 NUOVO v1.4.22-DEMO: Dimensioni autoclave in mm (native coordinates)
  const autoclaveWidth_mm = autoclave.larghezza_piano || autoclave.lunghezza || 2000
  const autoclaveHeight_mm = autoclave.larghezza_piano || 1200
  const aspectRatio = autoclaveWidth_mm / autoclaveHeight_mm
  
  // 🎯 NUOVO v1.4.22-DEMO: Calcolo zoom iniziale automatico
  useLayoutEffect(() => {
    if (!containerRef.current) return
    
    const containerWidth = containerRef.current.offsetWidth
    const initialScale = Math.min(containerWidth / autoclaveWidth_mm, 1) // Non ingrandire oltre 1:1
    setZoom(initialScale)
  }, [autoclaveWidth_mm])

  // Identifica tool con overlap
  const overlappingToolIds = new Set<number>()
  if (validation?.overlaps) {
    validation.overlaps.forEach(([idA, idB]) => {
      overlappingToolIds.add(idA)
      overlappingToolIds.add(idB)
    })
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

  const handleToolClick = useCallback((toolId: number) => {
    setSelectedTool(toolId)
    const tool = toolPositions.find(t => t.odl_id === toolId)
    if (tool) {
      toast({
        title: `Tool ODL ${toolId}`,
        description: `${tool.width}×${tool.height}mm, ${tool.peso}kg ${tool.rotated ? '(ruotato)' : ''}`
      })
    }
  }, [toolPositions, toast])
  
  // 🎯 NUOVO v1.4.22-DEMO: Funzioni zoom
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 2))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5))
  const handleZoomReset = () => {
    if (!containerRef.current) return
    const containerWidth = containerRef.current.offsetWidth
    const initialScale = Math.min(containerWidth / autoclaveWidth_mm, 1)
    setZoom(initialScale)
  }

  return (
    <CanvasErrorBoundary>
      <div className="relative">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">Canvas Preview v1.4.22-DEMO</h3>
            {/* 🎯 NUOVO v1.4.22-DEMO: Badge scala NON più incoerente */}
            <Badge variant="outline" className="text-sm">
              Scala: 1 : {(1/zoom).toFixed(1)}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleExportPNG} size="sm" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Scarica PNG
            </Button>
          </div>
        </div>
        
        {/* 🎯 NUOVO v1.4.22-DEMO: Controlli zoom */}
        <div className="flex items-center gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <div className="flex-1 px-2">
            <input
              type="range"
              value={zoom}
              onChange={(e) => setZoom(parseFloat(e.target.value))}
              min={0.5}
              max={2}
              step={0.05}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <Button variant="outline" size="sm" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleZoomReset}>
            Auto-Fit
          </Button>
          <span className="text-sm text-muted-foreground min-w-[80px]">
            {(zoom * 100).toFixed(0)}%
          </span>
        </div>
        
        {/* 🎯 NUOVO v1.4.22-DEMO: Contenitore aspect-ratio fisso */}
        <div 
          ref={containerRef}
          className="relative w-full max-w-full border rounded-lg overflow-visible bg-white"
          style={{ aspectRatio: `${autoclaveWidth_mm} / ${autoclaveHeight_mm}` }}
        >
          {/* 🎯 NUOVO v1.4.22-DEMO: Scaling via CSS transform, NON stage.scale() */}
          <div 
            className="konva-container"
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: 'top left',
              width: `${autoclaveWidth_mm}px`,
              height: `${autoclaveHeight_mm}px`,
              position: 'absolute',
              top: 0,
              left: 0
            }}
          >
            <CanvasWrapper 
              ref={stageRef}
              width={autoclaveWidth_mm} 
              height={autoclaveHeight_mm}
              loadingDelay={800}
            >
              <Layer>
                {/* 🎯 NUOVO v1.4.22-DEMO: Griglia con coordinate native mm */}
                <GridLayer width={autoclaveWidth_mm} height={autoclaveHeight_mm} scale={1} />
                
                {/* 🎯 NUOVO v1.4.22-DEMO: Righelli con coordinate native mm */}
                <RulerLayer width={autoclaveWidth_mm} height={autoclaveHeight_mm} scale={1} />
                
                {/* Autoclave outline - usa dimensioni in mm direttamente */}
                <Rect
                  x={0}
                  y={0}
                  width={autoclaveWidth_mm}
                  height={autoclaveHeight_mm}
                  stroke="#2563eb"
                  strokeWidth={2}
                  dash={[5, 5]}
                  fill="transparent"
                />
                
                {/* Triangolo origine */}
                <Line
                  points={[0, 0, 15, 10, 10, 15, 0, 0]}
                  fill="#6b7280"
                  closed
                />
                
                {/* Tool - coordinate native in mm */}
                {toolPositions.map((tool) => (
                  <ToolRect
                    key={tool.odl_id}
                    tool={tool}
                    scale={1}  // 🎯 IMPORTANTE: scale=1 perché CSS applica già il scaling
                    isOverlapping={overlappingToolIds.has(tool.odl_id)}
                    onClick={() => handleToolClick(tool.odl_id)}
                  />
                ))}
              </Layer>
            </CanvasWrapper>
          </div>
        </div>
        
        <LegendCard />
        
        {validation?.overlaps && validation.overlaps.length > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 font-semibold">⚠️ Overlap rilevati:</p>
            <ul className="text-red-700 text-sm mt-1">
              {validation.overlaps.map(([idA, idB], index) => (
                <li key={index}>• ODL {idA} ↔ ODL {idB}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </CanvasErrorBoundary>
  )
}

// ✅ NUOVO v1.4.19-DEMO: Hook per debug SVG ground-truth
const useDebugSvg = (batchId?: string) => {
  const [debugState, setDebugState] = useState<DebugState>({
    showGroundTruth: false,
    useSvgOnly: false,
    svgContent: null,
    differences: [],
    scaleError: 0
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchGroundTruthSvg = useCallback(async () => {
    if (!batchId) return

    setLoading(true)
    setError(null)
    
    try {
      console.log(`🎯 Fetching SVG ground-truth per batch: ${batchId}`)
      
      // 🔧 FIX: Usa il nuovo endpoint batch-based
      const response = await fetch(`/api/v1/nesting/batch/${batchId}/svg`)
      
      if (response.ok) {
        const svgContent = await response.text()
        setDebugState(prev => ({ ...prev, svgContent }))
        console.log('✅ SVG Ground-Truth caricato:', svgContent.length, 'caratteri')
        
        // Verifica che l'SVG sia valido
        if (svgContent.includes('<svg') && svgContent.includes('</svg>')) {
          console.log('✅ SVG validato: struttura corretta')
        } else {
          console.warn('⚠️ SVG potenzialmente malformato')
        }
      } else {
        const errorText = await response.text()
        const errorMsg = `HTTP ${response.status}: ${errorText}`
        console.error('❌ Errore caricamento SVG:', errorMsg)
        setError(errorMsg)
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Errore di rete'
      console.error('❌ Errore fetch SVG:', errorMsg)
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [batchId])

  const toggleGroundTruth = useCallback(() => {
    setDebugState(prev => {
      const newShow = !prev.showGroundTruth
      if (newShow && !prev.svgContent && !error) {
        fetchGroundTruthSvg()
      }
      return { ...prev, showGroundTruth: newShow }
    })
  }, [fetchGroundTruthSvg, error])

  const toggleSvgOnly = useCallback(() => {
    setDebugState(prev => ({ ...prev, useSvgOnly: !prev.useSvgOnly }))
  }, [])

  const retryFetch = useCallback(() => {
    setError(null)
    fetchGroundTruthSvg()
  }, [fetchGroundTruthSvg])

  const calculateDifferences = useCallback((
    toolPositions: ToolPosition[],
    autoClaveInfo: AutoclaveInfo,
    containerWidth: number,
    containerHeight: number
  ) => {
    if (!debugState.svgContent) return

    // Calcola scala teorica
    const autoclaveMm = [autoClaveInfo.lunghezza, autoClaveInfo.larghezza_piano]
    const scaleCalc = Math.min(containerWidth / autoclaveMm[0], containerHeight / autoclaveMm[1])
    
    // Estrai scala Konva (assumendo 1:1 per ora)
    const scaleKonva = 1.0 // TODO: Ottenere dalla ref del stage
    
    const scaleError = Math.abs(scaleCalc - scaleKonva)
    
    // Calcola differenze per ogni tool
    const differences: DebugDifference[] = toolPositions.map(tool => {
      // Coordinate teoriche (da SVG)
      const svgX = tool.x
      const svgY = tool.y
      const svgW = tool.width
      const svgH = tool.height
      
      // Coordinate Konva (scalate)
      const konvaX = tool.x * scaleKonva
      const konvaY = tool.y * scaleKonva
      const konvaW = tool.width * scaleKonva
      const konvaH = tool.height * scaleKonva
      
      // Differenze in mm
      const dx = Math.abs(svgX - konvaX)
      const dy = Math.abs(svgY - konvaY)
      const dW = Math.abs(svgW - konvaW)
      const dH = Math.abs(svgH - konvaH)
      
      const error_mm = Math.max(dx, dy, dW, dH)
      
      return {
        odl_id: tool.odl_id,
        dx, dy, dW, dH,
        error_mm
      }
    })
    
    // Log delle differenze per debugging
    console.table(differences)
    
    // Aggiorna stato
    setDebugState(prev => ({
      ...prev,
      differences,
      scaleError
    }))
    
    // Toast per errori di scala significativi
    if (scaleError > 0.02) {
      console.warn(`🔴 Scala incoerente: calc=${scaleCalc.toFixed(3)}, konva=${scaleKonva.toFixed(3)}`)
    }
    
  }, [debugState.svgContent])

  return {
    debugState,
    loading,
    error,
    toggleGroundTruth,
    toggleSvgOnly,
    calculateDifferences,
    retryFetch
  }
}

// ✅ NUOVO v1.4.19-DEMO: Componente SVG overlay per debug
const SvgGroundTruthOverlay: React.FC<{
  svgContent: string
  containerWidth: number
  containerHeight: number
  opacity?: number
}> = ({ svgContent, containerWidth, containerHeight, opacity = 0.3 }) => {
  
  // Parse SVG per estrarre dimensioni
  const svgMatch = svgContent.match(/viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/)
  const svgWidth = svgMatch ? parseFloat(svgMatch[1]) : containerWidth
  const svgHeight = svgMatch ? parseFloat(svgMatch[2]) : containerHeight
  
  // Calcola scala per adattare SVG al container
  const scale = Math.min(containerWidth / svgWidth, containerHeight / svgHeight)
  
  return (
    <div 
      className="absolute inset-0 pointer-events-none"
      style={{
        opacity,
        transform: `scale(${scale})`,
        transformOrigin: 'top left',
        zIndex: 10
      }}
    >
      <div 
        dangerouslySetInnerHTML={{ __html: svgContent }}
        style={{
          width: svgWidth,
          height: svgHeight
        }}
      />
    </div>
  )
}

// ✅ NUOVO v1.4.19-DEMO: Componenti di controllo debug
const DebugControls: React.FC<{
  debugState: DebugState
  loading: boolean
  error: string | null
  onToggleGroundTruth: () => void
  onToggleSvgOnly: () => void
  onRetry: () => void
}> = ({ debugState, loading, error, onToggleGroundTruth, onToggleSvgOnly, onRetry }) => {
  return (
    <div className="space-y-2">
      <div className="flex gap-2 mb-4">
        <Button
          variant={debugState.showGroundTruth ? "default" : "outline"}
          size="sm"
          onClick={onToggleGroundTruth}
          disabled={loading}
          className="flex items-center gap-2"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Grid3X3 className="h-4 w-4" />}
          {debugState.showGroundTruth ? 'Nascondi GT' : 'Mostra GT'}
        </Button>
        
        {debugState.svgContent && (
          <Button
            variant={debugState.useSvgOnly ? "default" : "outline"}
            size="sm"
            onClick={onToggleSvgOnly}
            className="flex items-center gap-2"
          >
            <Ruler className="h-4 w-4" />
            {debugState.useSvgOnly ? 'Mostra Konva' : 'Solo SVG'}
          </Button>
        )}
        
        {error && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="flex items-center gap-2 border-red-300 text-red-700 hover:bg-red-50"
          >
            <AlertCircle className="h-4 w-4" />
            Riprova
          </Button>
        )}
        
        {debugState.scaleError > 0.02 && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            Scala incoerente: {(debugState.scaleError * 100).toFixed(1)}%
          </Badge>
        )}
        
        {debugState.differences.length > 0 && (
          <Badge variant="secondary">
            Differenze: {debugState.differences.filter(d => d.error_mm > 1).length} &gt; 1mm
          </Badge>
        )}
      </div>
      
      {/* 🎯 NUOVO: Pannello errori SVG */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-red-800 font-semibold text-sm">Errore Caricamento SVG Ground-Truth</h4>
              <p className="text-red-700 text-xs mt-1 font-mono">{error}</p>
              <p className="text-red-600 text-xs mt-2">
                Verifica che il backend sia attivo e che il batch contenga dati di nesting validi.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ✅ NUOVO v1.4.22-DEMO: Componente principale con titolo aggiornato
const NestingCanvas: React.FC<NestingCanvasProps> = ({ batchData, className }) => {
  const { validation, loading: validationLoading } = useNestingValidation(batchData.id)
  const { 
    debugState, 
    loading: debugLoading, 
    error: debugError,
    toggleGroundTruth, 
    toggleSvgOnly, 
    calculateDifferences,
    retryFetch 
  } = useDebugSvg(batchData.id)
  const mounted = useClientMount()
  const [renderError, setRenderError] = useState<string | null>(null)

  // ✅ Protezione aggiuntiva: Verifica dati
  useEffect(() => {
    if (mounted && batchData.configurazione_json?.tool_positions) {
      try {
        // Verifica che i dati siano validi
        const positions = batchData.configurazione_json.tool_positions
        if (!Array.isArray(positions)) {
          throw new Error('Tool positions non è un array valido')
        }
        
        // Verifica che ogni position abbia i campi necessari
        for (const tool of positions) {
          if (typeof tool.x !== 'number' || typeof tool.y !== 'number') {
            throw new Error(`Tool ${tool.odl_id} ha coordinate non valide`)
          }
        }
      } catch (error) {
        console.error('Errore validazione dati canvas:', error)
        setRenderError(error instanceof Error ? error.message : 'Dati non validi')
      }
    }
  }, [mounted, batchData.configurazione_json])

  // 🎯 NUOVO: Calcola differenze quando i dati sono pronti
  useEffect(() => {
    if (debugState.svgContent && batchData.configurazione_json?.tool_positions && batchData.autoclave) {
      calculateDifferences(
        batchData.configurazione_json.tool_positions,
        batchData.autoclave,
        800, // containerWidth
        600  // containerHeight
      )
    }
  }, [debugState.svgContent, batchData.configurazione_json?.tool_positions, batchData.autoclave, calculateDifferences])

  if (!mounted) {
    return <CanvasLoadingPlaceholder width={800} height={600} />
  }

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

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Layout Nesting v1.4.22-DEMO CSS Aspect-Ratio
            </CardTitle>
            <div className="flex items-center gap-2">
              <ValidationBadge validation={validation} loading={validationLoading} />
              {process.env.NODE_ENV === 'development' && (
                <Badge variant="outline" className="text-xs">
                  🎯 DEBUG
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* 🎯 NUOVO: Controlli debug SVG */}
          {process.env.NODE_ENV === 'development' && (
            <DebugControls
              debugState={debugState}
              loading={debugLoading}
              error={debugError}
              onToggleGroundTruth={toggleGroundTruth}
              onToggleSvgOnly={toggleSvgOnly}
              onRetry={retryFetch}
            />
          )}
          
          <CanvasErrorBoundary>
            <div className="relative">
              {/* Canvas Konva principale (nascosto se in modalità SVG-only) */}
              {!debugState.useSvgOnly && (
                <InteractiveCanvas
                  toolPositions={normalizedTools}
                  autoclave={batchData.autoclave}
                  validation={validation}
                />
              )}
              
              {/* 🎯 NUOVO: SVG Ground-Truth Overlay */}
              {debugState.showGroundTruth && debugState.svgContent && !debugError && (
                <div className="relative">
                  {debugState.useSvgOnly && (
                    <div className="border rounded-lg overflow-hidden bg-gray-50" style={{ width: 800, height: 600 }}>
                      <SvgGroundTruthOverlay
                        svgContent={debugState.svgContent}
                        containerWidth={800}
                        containerHeight={600}
                        opacity={1.0} // Opacità completa per modalità SVG-only
                      />
                    </div>
                  )}
                  
                  {!debugState.useSvgOnly && (
                    <SvgGroundTruthOverlay
                      svgContent={debugState.svgContent}
                      containerWidth={800}
                      containerHeight={600}
                      opacity={0.3} // Overlay trasparente
                    />
                  )}
                </div>
              )}
              
              {/* 🎯 NUOVO: Pannello diagnostica differenze */}
              {debugState.differences.length > 0 && process.env.NODE_ENV === 'development' && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="text-blue-800 font-semibold mb-2">🔍 Diagnostica Coordinate (Debug)</h4>
                  <div className="text-sm text-blue-700 space-y-1">
                    <p>Tolleranza: 1mm | Errori rilevati: {debugState.differences.filter(d => d.error_mm > 1).length}</p>
                    {debugState.differences.filter(d => d.error_mm > 1).slice(0, 3).map(diff => (
                      <div key={diff.odl_id} className="font-mono text-xs">
                        ODL {diff.odl_id}: dx={diff.dx.toFixed(1)}mm, dy={diff.dy.toFixed(1)}mm, err={diff.error_mm.toFixed(1)}mm
                      </div>
                    ))}
                    {debugState.differences.filter(d => d.error_mm > 1).length > 3 && (
                      <p className="text-xs italic">...e {debugState.differences.filter(d => d.error_mm > 1).length - 3} altri</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CanvasErrorBoundary>
        </CardContent>
      </Card>
    </div>
  )
}

export default NestingCanvas 