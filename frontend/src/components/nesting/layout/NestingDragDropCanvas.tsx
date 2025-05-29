'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  useDraggable,
  useDroppable,
} from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from "@/components/ui/progress"
import { 
  Save, 
  RotateCcw, 
  Loader2, 
  Move3D, 
  Target, 
  Package,
  AlertCircle,
  CheckCircle,
  RefreshCcw,
  Layers,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  CheckCircle2,
  RotateCw
} from 'lucide-react'
import { nestingApi, ToolPosition, NestingLayoutData } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'
import { ExtractedNestingData } from '../manual/NestingStep1ODLSelection'
import { AutoclaveSelectionData } from '../manual/NestingStep2AutoclaveSelection'

// Tipi per drag and drop
interface DragItem {
  odl_id: number
  width: number
  height: number
  rotated: boolean
  piano: number
}

interface ToolItemProps {
  position: ToolPosition
  tool_info: any
  onRotate: (odl_id: number) => void
  onChangePlane: (odl_id: number, new_piano: number) => void
  scale: number
  isReadOnly?: boolean
  isDragging?: boolean
}

// Componente per un singolo tool trascinabile
function DraggableToolItem({ 
  position, 
  tool_info, 
  onRotate, 
  onChangePlane,
  scale,
  isReadOnly = false,
  isDragging = false
}: ToolItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
  } = useDraggable({
    id: position.odl_id.toString(),
    disabled: isReadOnly,
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    left: position.x * scale,
    top: position.y * scale,
    width: position.width * scale,
    height: position.height * scale,
    fontSize: Math.max(8, 10 * scale)
  }

  const handleDoubleClick = () => {
    if (!isReadOnly) {
      onRotate(position.odl_id)
    }
  }

  const handleRightClick = (e: React.MouseEvent) => {
    if (!isReadOnly) {
      e.preventDefault()
      const newPlane = position.piano === 1 ? 2 : 1
      onChangePlane(position.odl_id, newPlane)
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={cn(
        "absolute border-2 cursor-move transition-all duration-200",
        "flex items-center justify-center text-xs font-medium",
        "hover:z-20 select-none",
        isDragging && "opacity-50 z-30",
        position.piano === 1 ? "bg-blue-100 border-blue-500" : "bg-orange-100 border-orange-500",
        position.rotated && "bg-green-100 border-green-500",
        !isReadOnly && "hover:shadow-lg hover:scale-105"
      )}
      onDoubleClick={handleDoubleClick}
      onContextMenu={handleRightClick}
      title={`ODL #${position.odl_id} - ${tool_info?.part_number_tool || 'N/A'} 
${position.rotated ? '🔄 Ruotato' : ''} 
Piano ${position.piano}
Doppio click: ruota
Click destro: cambia piano`}
    >
      <div className="text-center leading-tight">
        <div className="font-bold">#{position.odl_id}</div>
        {tool_info?.part_number_tool && (
          <div className="truncate">{tool_info.part_number_tool.substring(0, 8)}</div>
        )}
        <div className="flex items-center justify-center gap-1 mt-1">
          {position.rotated && <span className="text-green-600">🔄</span>}
          <Badge variant={position.piano === 1 ? "default" : "secondary"} className="text-xs">
            P{position.piano}
          </Badge>
        </div>
      </div>
    </div>
  )
}

// Area di drop per l'autoclave
interface DropZoneProps {
  children: React.ReactNode
  autoclave: any
  scale: number
  isReadOnly?: boolean
  onMouseMove?: (e: React.MouseEvent) => void
}

function AutoclaveDropZone({ children, autoclave, scale, isReadOnly = false, onMouseMove }: DropZoneProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: 'autoclave-drop-zone'
  })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "relative border-4 border-dashed border-gray-300 rounded-lg transition-colors",
        isOver ? "border-blue-500 bg-blue-50" : "bg-gray-50"
      )}
      style={{
        width: autoclave.lunghezza * scale,
        height: autoclave.larghezza_piano * scale,
        minHeight: 400,
        backgroundImage: `
          linear-gradient(to right, rgba(0,0,0,0.1) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(0,0,0,0.1) 1px, transparent 1px)
        `,
        backgroundSize: `${20 * scale}px ${20 * scale}px`
      }}
      onMouseMove={onMouseMove}
    >
      <div className="absolute top-2 left-2 text-sm font-medium text-gray-600">
        {autoclave.nome} ({autoclave.lunghezza}x{autoclave.larghezza_piano}mm)
      </div>
      {children}
    </div>
  )
}

// Componente principale
interface NestingDragDropCanvasProps {
  nestingId: number
  isReadOnly?: boolean
  onPositionsChange?: (positions: ToolPosition[]) => void
}

export function NestingDragDropCanvas({ 
  nestingId, 
  isReadOnly = false,
  onPositionsChange 
}: NestingDragDropCanvasProps) {
  const [positions, setPositions] = useState<ToolPosition[]>([])
  const [layoutData, setLayoutData] = useState<NestingLayoutData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [scale, setScale] = useState(0.5) // Scala di visualizzazione
  const [activeId, setActiveId] = useState<string | null>(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  
  const { toast } = useToast()

  // Sensori per il drag and drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // Carica dati iniziali
  useEffect(() => {
    loadNestingData()
  }, [nestingId])

  const loadNestingData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Carica layout e posizioni
      const [layoutResponse, positionsResponse] = await Promise.all([
        nestingApi.getLayout(nestingId),
        nestingApi.getToolPositions(nestingId)
      ])

      if (layoutResponse.success && layoutResponse.layout_data) {
        setLayoutData(layoutResponse.layout_data)
      }

      if (positionsResponse.success) {
        setPositions(positionsResponse.positions)
        setHasUnsavedChanges(false)
      }

    } catch (error) {
      console.error('❌ Errore caricamento layout:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore nel caricamento'
      setError(errorMessage)
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Gestisce l'inizio del drag
  const handleDragStart = (event: DragStartEvent) => {
    if (isReadOnly) return
    setActiveId(event.active.id as string)
  }

  // Gestisce la fine del drag
  const handleDragEnd = (event: DragEndEvent) => {
    if (isReadOnly) return
    
    setActiveId(null)
    
    const { active, delta } = event
    if (!delta) return

    const toolId = parseInt(active.id as string)
    
    setPositions(prev => {
      const newPositions = prev.map(pos => {
        if (pos.odl_id === toolId) {
          return {
            ...pos,
            x: Math.max(0, pos.x + (delta.x / scale)),
            y: Math.max(0, pos.y + (delta.y / scale))
          }
        }
        return pos
      })
      
      setHasUnsavedChanges(true)
      if (onPositionsChange) {
        onPositionsChange(newPositions)
      }
      return newPositions
    })
  }

  // Ruota un tool
  const handleToolRotate = useCallback((odl_id: number) => {
    if (isReadOnly) return

    setPositions(prev => {
      const newPositions = prev.map(pos => 
        pos.odl_id === odl_id 
          ? { 
              ...pos, 
              rotated: !pos.rotated,
              width: pos.height,
              height: pos.width
            }
          : pos
      )
      setHasUnsavedChanges(true)
      if (onPositionsChange) {
        onPositionsChange(newPositions)
      }
      return newPositions
    })
  }, [isReadOnly, onPositionsChange])

  // Cambia piano di un tool
  const handleChangePlane = useCallback((odl_id: number, new_piano: number) => {
    if (isReadOnly) return

    setPositions(prev => {
      const newPositions = prev.map(pos => 
        pos.odl_id === odl_id 
          ? { ...pos, piano: new_piano }
          : pos
      )
      setHasUnsavedChanges(true)
      if (onPositionsChange) {
        onPositionsChange(newPositions)
      }
      return newPositions
    })
  }, [isReadOnly, onPositionsChange])

  // Salva le posizioni
  const handleSavePositions = async () => {
    if (isReadOnly) return

    try {
      setSaving(true)
      const response = await nestingApi.saveToolPositions(nestingId, positions)
      
      if (response.success) {
        setHasUnsavedChanges(false)
        toast({
          title: "Posizioni Salvate",
          description: `${response.statistiche.tools_posizionati} tool posizionati con successo`,
        })
      }
    } catch (error) {
      console.error('❌ Errore salvataggio:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore nel salvataggio'
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  // Resetta al layout automatico
  const handleResetLayout = async () => {
    if (isReadOnly) return

    try {
      setSaving(true)
      const response = await nestingApi.resetToolPositions(nestingId)
      
      if (response.success) {
        setPositions(response.positions)
        setHasUnsavedChanges(false)
        toast({
          title: "Layout Resettato",
          description: "Posizioni ripristinate al layout automatico",
        })
      }
    } catch (error) {
      console.error('❌ Errore reset:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore nel reset'
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Move3D className="h-5 w-5" />
            Layout Nesting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Caricamento layout...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !layoutData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Move3D className="h-5 w-5" />
            Layout Nesting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Errore</AlertTitle>
            <AlertDescription>
              {error || 'Dati del layout non disponibili'}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  const piano1Tools = positions.filter(pos => pos.piano === 1)
  const piano2Tools = positions.filter(pos => pos.piano === 2)
  const activeTool = positions.find(pos => pos.odl_id.toString() === activeId)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Move3D className="h-5 w-5" />
              Layout Nesting #{nestingId}
              {hasUnsavedChanges && (
                <Badge variant="outline" className="text-orange-600">
                  Modifiche non salvate
                </Badge>
              )}
            </CardTitle>
            <CardDescription>
              {isReadOnly 
                ? "Visualizzazione layout (sola lettura)"
                : "Trascina i tool per riorganizzare il layout. Doppio click per ruotare, click destro per cambiare piano."
              }
            </CardDescription>
          </div>
          
          {!isReadOnly && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setScale(prev => Math.min(1.0, prev + 0.1))}
              >
                Zoom +
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setScale(prev => Math.max(0.2, prev - 0.1))}
              >
                Zoom -
              </Button>
              <Button
                variant="outline"
                onClick={handleResetLayout}
                disabled={isSaving}
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset Auto
              </Button>
              <Button
                onClick={handleSavePositions}
                disabled={!hasUnsavedChanges || isSaving}
                className="flex items-center gap-2"
              >
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Salva Layout
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Statistiche */}
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div className="bg-blue-50 p-3 rounded">
            <div className="font-medium text-blue-900">Piano 1</div>
            <div className="text-blue-700">{piano1Tools.length} tool</div>
          </div>
          <div className="bg-orange-50 p-3 rounded">
            <div className="font-medium text-orange-900">Piano 2</div>
            <div className="text-orange-700">{piano2Tools.length} tool</div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="font-medium text-green-900">Ruotati</div>
            <div className="text-green-700">{positions.filter(p => p.rotated).length} tool</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="font-medium text-gray-900">Scala</div>
            <div className="text-gray-700">{Math.round(scale * 100)}%</div>
          </div>
        </div>

        {/* Canvas principale */}
        <div className="space-y-4">
          <h4 className="font-medium flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Autoclave: {layoutData.autoclave.nome}
          </h4>
          
          <DndContext
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="border rounded-lg p-4 bg-gray-50 overflow-auto">
              <AutoclaveDropZone
                autoclave={layoutData.autoclave}
                scale={scale}
                isReadOnly={isReadOnly}
              >
                {positions.map((position) => {
                  const toolInfo = layoutData.odl_list.find(odl => odl.id === position.odl_id)?.tool
                  return (
                    <DraggableToolItem
                      key={position.odl_id}
                      position={position}
                      tool_info={toolInfo}
                      onRotate={handleToolRotate}
                      onChangePlane={handleChangePlane}
                      scale={scale}
                      isReadOnly={isReadOnly}
                      isDragging={activeId === position.odl_id.toString()}
                    />
                  )
                })}
              </AutoclaveDropZone>
            </div>

            <DragOverlay>
              {activeTool && (
                <div
                  className="bg-blue-200 border-2 border-blue-500 rounded opacity-90"
                  style={{
                    width: activeTool.width * scale,
                    height: activeTool.height * scale
                  }}
                >
                  <div className="text-xs font-bold text-center">
                    #{activeTool.odl_id}
                  </div>
                </div>
              )}
            </DragOverlay>
          </DndContext>

          {/* Legenda */}
          <div className="bg-gray-50 p-3 rounded text-xs space-y-1">
            <div className="font-medium">Legenda:</div>
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-blue-100 border border-blue-500 rounded"></div>
                <span>Piano 1</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-orange-100 border border-orange-500 rounded"></div>
                <span>Piano 2</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-green-100 border border-green-500 rounded"></div>
                <span>Ruotato</span>
              </div>
              {!isReadOnly && (
                <>
                  <span>•</span>
                  <span>Doppio click: ruota tool</span>
                  <span>•</span>
                  <span>Click destro: cambia piano</span>
                </>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ✅ NUOVO: Dati del layout con divisione per ciclo cura
export interface LayoutCanvasData {
  nesting_id: number
  odl_layout_data: ODLLayoutGroup[]
  final_positions: ToolPosition[]
  validation_results: {
    has_conflicts: boolean
    efficiency_score: number
    coverage_percentage: number
    cycle_separation_ok: boolean
  }
  layout_notes: string[]
}

export interface ODLLayoutGroup {
  ciclo_cura: string
  color: string
  odl_list: Array<{
    id: number
    parte_nome: string
    tool_nome: string
    priorita: number
    dimensioni: {
      larghezza: number
      lunghezza: number
      peso?: number
    }
    position?: ToolPosition
  }>
  total_area: number
  total_weight: number
}

interface NestingStep3LayoutCanvasProps {
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  onNext: (data: LayoutCanvasData) => void
  onBack: () => void
  isLoading?: boolean
  savedProgress?: {
    saved_positions?: ToolPosition[]
    saved_nesting_id?: number
  }
}

// Colori per i cicli di cura
const CYCLE_COLORS = [
  'bg-blue-100 border-blue-300 text-blue-800',
  'bg-green-100 border-green-300 text-green-800',
  'bg-purple-100 border-purple-300 text-purple-800',
  'bg-orange-100 border-orange-300 text-orange-800',
  'bg-pink-100 border-pink-300 text-pink-800',
  'bg-yellow-100 border-yellow-300 text-yellow-800'
]

// Componente Tool trascinabile con animazioni
interface DraggableToolProps {
  odl: any
  position: ToolPosition
  groupColor: string
  scale: number
  onRotate: (odlId: number) => void
  onChangePlane: (odlId: number, plane: number) => void
  isConflicted?: boolean
  isDragging?: boolean
}

function DraggableToolItemStep3({ 
  odl, 
  position, 
  groupColor, 
  scale, 
  onRotate, 
  onChangePlane,
  isConflicted = false,
  isDragging = false
}: DraggableToolProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: `tool-${odl.id}`,
    data: {
      odl_id: odl.id,
      width: position.width,
      height: position.height,
      rotated: position.rotated,
      piano: position.piano
    }
  })

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0) scale(${scale})`,
    zIndex: isDragging ? 1000 : 1
  } : {
    transform: `scale(${scale})`,
    zIndex: 1
  }

  const handleDoubleClick = () => {
    onRotate(odl.id)
  }

  const handleRightClick = (e: React.MouseEvent) => {
    e.preventDefault()
    onChangePlane(odl.id, position.piano === 1 ? 2 : 1)
  }

  return (
    <div
      ref={setNodeRef}
      style={{
        ...style,
        position: 'absolute',
        left: position.x * scale,
        top: position.y * scale,
        width: position.width * scale,
        height: position.height * scale,
      }}
      className={cn(
        "border-2 rounded cursor-move transition-all duration-200",
        groupColor,
        isConflicted ? "border-red-500 bg-red-100" : "",
        isDragging ? "shadow-lg opacity-80" : "hover:shadow-md",
        position.rotated ? "ring-2 ring-yellow-400" : "",
        position.piano === 2 ? "ring-2 ring-orange-400" : ""
      )}
      {...listeners}
      {...attributes}
      onDoubleClick={handleDoubleClick}
      onContextMenu={handleRightClick}
      title={`ODL ${odl.id} - ${odl.parte_nome} | Tool: ${odl.tool_nome}${position.rotated ? ' (Ruotato)' : ''}${position.piano === 2 ? ' (Piano 2)' : ''}`}
    >
      <div className="p-1 text-xs font-medium truncate">
        #{odl.id}
      </div>
      <div className="absolute bottom-0 right-0 flex gap-1">
        {position.rotated && (
          <RotateCw className="h-3 w-3 text-yellow-600" />
        )}
        {position.piano === 2 && (
          <Layers className="h-3 w-3 text-orange-600" />
        )}
        {isConflicted && (
          <AlertTriangle className="h-3 w-3 text-red-600" />
        )}
      </div>
    </div>
  )
}

export function NestingStep3LayoutCanvas({ 
  odlData, 
  autoclaveData, 
  onNext, 
  onBack, 
  isLoading = false,
  savedProgress 
}: NestingStep3LayoutCanvasProps) {
  const { toast } = useToast()
  
  // State principale
  const [nestingId, setNestingId] = useState<number | null>(savedProgress?.saved_nesting_id || null)
  const [layoutGroups, setLayoutGroups] = useState<ODLLayoutGroup[]>([])
  const [toolPositions, setToolPositions] = useState<ToolPosition[]>(savedProgress?.saved_positions || [])
  const [scale, setScale] = useState(0.5)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [validationResults, setValidationResults] = useState<any>(null)
  const [conflictedODL, setConflictedODL] = useState<Set<number>>(new Set())
  
  // State drag and drop
  const [activeDrag, setActiveDrag] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Sensori per drag and drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // Carica i dati iniziali
  useEffect(() => {
    initializeLayoutData()
  }, [odlData, autoclaveData])

  // Valida il layout quando cambiano le posizioni
  useEffect(() => {
    if (toolPositions.length > 0) {
      validateLayout()
    }
  }, [toolPositions])

  const initializeLayoutData = async () => {
    try {
      setLoading(true)
      
      // Crea o carica il nesting dal backend
      let currentNestingId = nestingId
      
      if (!currentNestingId) {
        // ✅ CORRETTO: Usa solo note per creare il nesting
        const newNesting = await nestingApi.create({
          note: `Nesting manuale - ${new Date().toLocaleString()}`
        })
        currentNestingId = parseInt(newNesting.id)
        setNestingId(currentNestingId)
      }
      
      // Raggruppa ODL per ciclo di cura
      const groups = await groupODLByCycle()
      setLayoutGroups(groups)
      
      // Carica o genera posizioni iniziali
      if (savedProgress?.saved_positions?.length) {
        setToolPositions(savedProgress.saved_positions)
      } else {
        await generateInitialLayout(currentNestingId)
      }
      
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore inizializzazione",
        description: "Non è stato possibile inizializzare il layout canvas"
      })
    } finally {
      setLoading(false)
    }
  }

  // ✅ CHIAVE: Raggruppa ODL per ciclo di cura
  const groupODLByCycle = async (): Promise<ODLLayoutGroup[]> => {
    const groups: { [cycle: string]: any[] } = {}
    
    // Simula caricamento dettagli ODL (in realtà dovremmo chiamare API)
    odlData.selected_odl_ids.forEach((odlId, index) => {
      const cycle = odlData.cicli_cura_coinvolti[index % odlData.cicli_cura_coinvolti.length] || 'Sconosciuto'
      
      if (!groups[cycle]) {
        groups[cycle] = []
      }
      
      groups[cycle].push({
        id: odlId,
        parte_nome: `Parte-${odlId}`,
        tool_nome: `Tool-${odlId}`,
        priorita: Math.floor(Math.random() * 10) + 1,
        dimensioni: {
          larghezza: 50 + Math.random() * 100,
          lunghezza: 50 + Math.random() * 100,
          peso: 1 + Math.random() * 5
        }
      })
    })

    return Object.entries(groups).map(([cycle, odlList], index) => ({
      ciclo_cura: cycle,
      color: CYCLE_COLORS[index % CYCLE_COLORS.length],
      odl_list: odlList,
      total_area: odlList.reduce((sum, odl) => sum + (odl.dimensioni.larghezza * odl.dimensioni.lunghezza / 100), 0),
      total_weight: odlList.reduce((sum, odl) => sum + (odl.dimensioni.peso || 0), 0)
    }))
  }

  const generateInitialLayout = async (nestingId: number) => {
    try {
      // Richiama l'API per il layout automatico o genera posizioni di base
      const response = await nestingApi.getToolPositions(nestingId)
      
      if (response.positions.length > 0) {
        setToolPositions(response.positions)
      } else {
        // Genera layout semplice se l'API non ha posizioni
        const simplePositions = generateSimpleGrid()
        setToolPositions(simplePositions)
      }
    } catch (error) {
      // Fallback su layout grid semplice
      const simplePositions = generateSimpleGrid()
      setToolPositions(simplePositions)
    }
  }

  const generateSimpleGrid = (): ToolPosition[] => {
    const positions: ToolPosition[] = []
    let x = 20
    let y = 20
    const rowHeight = 80
    const colWidth = 80
    
    odlData.selected_odl_ids.forEach((odlId, index) => {
      if (x + colWidth > autoclaveData.autoclave_data.lunghezza - 20) {
        x = 20
        y += rowHeight
      }
      
      positions.push({
        odl_id: odlId,
        x,
        y,
        width: 60,
        height: 40,
        rotated: false,
        piano: 1
      })
      
      x += colWidth
    })
    
    return positions
  }

  // ✅ VALIDAZIONE: Controlla conflitti cicli e ottimizzazione
  const validateLayout = () => {
    const conflicts = new Set<number>()
    const results = {
      has_conflicts: false,
      efficiency_score: 0,
      coverage_percentage: 0,
      cycle_separation_ok: true
    }
    
    // Verifica sovrapposizioni tra ODL di cicli diversi
    const odlByCycle = new Map<string, number[]>()
    
    layoutGroups.forEach(group => {
      group.odl_list.forEach(odl => {
        const cycle = group.ciclo_cura
        if (!odlByCycle.has(cycle)) {
          odlByCycle.set(cycle, [])
        }
        odlByCycle.get(cycle)!.push(odl.id)
      })
    })
    
    // Controlla sovrapposizioni
    toolPositions.forEach(pos1 => {
      const cycle1 = getCycleForODL(pos1.odl_id)
      
      toolPositions.forEach(pos2 => {
        if (pos1.odl_id === pos2.odl_id) return
        
        const cycle2 = getCycleForODL(pos2.odl_id)
        
        // Verifica sovrapposizione fisica
        if (isOverlapping(pos1, pos2)) {
          if (cycle1 !== cycle2) {
            // Conflitto: ODL di cicli diversi si sovrappongono
            conflicts.add(pos1.odl_id)
            conflicts.add(pos2.odl_id)
            results.has_conflicts = true
            results.cycle_separation_ok = false
          }
        }
      })
    })
    
    // Calcola efficienza area
    const totalArea = toolPositions.reduce((sum, pos) => sum + (pos.width * pos.height), 0)
    const autoclaveArea = autoclaveData.autoclave_data.lunghezza * autoclaveData.autoclave_data.larghezza_piano
    results.coverage_percentage = (totalArea / autoclaveArea) * 100
    results.efficiency_score = Math.min(100, results.coverage_percentage * (results.cycle_separation_ok ? 1 : 0.5))
    
    setConflictedODL(conflicts)
    setValidationResults(results)
  }

  const getCycleForODL = (odlId: number): string => {
    for (const group of layoutGroups) {
      if (group.odl_list.some(odl => odl.id === odlId)) {
        return group.ciclo_cura
      }
    }
    return 'Sconosciuto'
  }

  const isOverlapping = (pos1: ToolPosition, pos2: ToolPosition): boolean => {
    return !(
      pos1.x + pos1.width <= pos2.x ||
      pos2.x + pos2.width <= pos1.x ||
      pos1.y + pos1.height <= pos2.y ||
      pos2.y + pos2.height <= pos1.y ||
      pos1.piano !== pos2.piano
    )
  }

  // Gestione drag and drop
  const handleDragStart = (event: DragStartEvent) => {
    setActiveDrag(event.active.data.current)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, delta } = event
    
    if (delta.x === 0 && delta.y === 0) {
      setActiveDrag(null)
      return
    }
    
    const odlId = active.data.current?.odl_id
    if (!odlId) return
    
    setToolPositions(prev => prev.map(pos => {
      if (pos.odl_id === odlId) {
        return {
          ...pos,
          x: Math.max(0, pos.x + delta.x / scale),
          y: Math.max(0, pos.y + delta.y / scale)
        }
      }
      return pos
    }))
    
    setHasUnsavedChanges(true)
    setActiveDrag(null)
  }

  // Azioni sui tool
  const handleRotateTool = (odlId: number) => {
    setToolPositions(prev => prev.map(pos => {
      if (pos.odl_id === odlId) {
        return {
          ...pos,
          rotated: !pos.rotated,
          width: pos.height,
          height: pos.width
        }
      }
      return pos
    }))
    setHasUnsavedChanges(true)
  }

  const handleChangePlane = (odlId: number, newPlane: number) => {
    setToolPositions(prev => prev.map(pos => {
      if (pos.odl_id === odlId) {
        return { ...pos, piano: newPlane }
      }
      return pos
    }))
    setHasUnsavedChanges(true)
  }

  // Salvataggio layout
  const handleSaveLayout = async () => {
    if (!nestingId) return
    
    try {
      await nestingApi.saveToolPositions(nestingId, toolPositions)
      setHasUnsavedChanges(false)
      
      toast({
        title: "Layout salvato",
        description: "Le posizioni dei tool sono state salvate con successo"
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore salvataggio",
        description: "Non è stato possibile salvare il layout"
      })
    }
  }

  // Reset layout
  const handleResetLayout = async () => {
    if (!nestingId) return
    
    try {
      const response = await nestingApi.resetToolPositions(nestingId)
      setToolPositions(response.positions)
      setHasUnsavedChanges(false)
      
      toast({
        title: "Layout resettato",
        description: "Il layout è stato resettato al calcolo automatico"
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore reset",
        description: "Non è stato possibile resettare il layout"
      })
    }
  }

  const handleNext = () => {
    if (!validationResults || !nestingId) return
    
    const layoutData: LayoutCanvasData = {
      nesting_id: nestingId,
      odl_layout_data: layoutGroups,
      final_positions: toolPositions,
      validation_results: validationResults,
      layout_notes: [
        validationResults.cycle_separation_ok ? "Separazione cicli OK" : "ATTENZIONE: Conflitti tra cicli",
        `Efficienza area: ${validationResults.efficiency_score.toFixed(1)}%`,
        `Copertura: ${validationResults.coverage_percentage.toFixed(1)}%`
      ]
    }
    
    onNext(layoutData)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 3: Layout Canvas</h2>
          <p className="text-gray-600 mt-1">
            Posiziona i tool nell'autoclave {autoclaveData.autoclave_data.nome} tramite drag and drop
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={validationResults?.efficiency_score || 0} className="w-32" />
          <span className="text-sm text-gray-500">
            {validationResults?.efficiency_score?.toFixed(0) || 0}% efficienza
          </span>
        </div>
      </div>

      {/* Controlli layout */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Controlli Layout</span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setScale(Math.max(0.2, scale - 0.1))}
                disabled={scale <= 0.2}
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-sm min-w-12 text-center">{Math.round(scale * 100)}%</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setScale(Math.min(1.0, scale + 0.1))}
                disabled={scale >= 1.0}
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={handleSaveLayout}
              disabled={!hasUnsavedChanges || !nestingId}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              Salva Layout
            </Button>
            
            <Button
              variant="outline"
              onClick={handleResetLayout}
              disabled={!nestingId}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Reset Automatico
            </Button>
            
            {hasUnsavedChanges && (
              <Badge variant="secondary">Modifiche non salvate</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Gruppi cicli di cura */}
      <Card>
        <CardHeader>
          <CardTitle>Gruppi per Ciclo di Cura</CardTitle>
          <CardDescription>
            {odlData.conflitti_cicli ? 
              "⚠️ Attenzione: Evita sovrapposizioni tra cicli diversi" : 
              "✅ Ciclo di cura uniforme"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {layoutGroups.map((group, index) => (
              <div key={group.ciclo_cura} className={cn("p-4 rounded-lg border-2", group.color)}>
                <h4 className="font-medium mb-2">{group.ciclo_cura}</h4>
                <div className="text-sm space-y-1">
                  <div>ODL: {group.odl_list.length}</div>
                  <div>Area: {group.total_area.toFixed(0)} cm²</div>
                  <div>Peso: {group.total_weight.toFixed(1)} kg</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Validazione layout con alert conflitti */}
      {validationResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {validationResults.cycle_separation_ok ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-600" />
              )}
              Validazione Layout
            </CardTitle>
          </CardHeader>
          <CardContent>
            {validationResults.has_conflicts && (
              <Alert className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Conflitti rilevati:</strong> Alcuni ODL di cicli diversi si sovrappongono. 
                  Sposta i tool evidenziati in rosso per risolvere i conflitti.
                </AlertDescription>
              </Alert>
            )}
            
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {validationResults.efficiency_score.toFixed(1)}%
                </div>
                <div className="text-sm text-blue-800">Efficienza Totale</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">
                  {validationResults.coverage_percentage.toFixed(1)}%
                </div>
                <div className="text-sm text-green-800">Copertura Area</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-2xl font-bold text-purple-600">
                  {conflictedODL.size}
                </div>
                <div className="text-sm text-purple-800">ODL in Conflitto</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Canvas drag and drop */}
      <Card>
        <CardHeader>
          <CardTitle>Canvas Autoclave</CardTitle>
          <CardDescription>
            Trascina i tool per posizionarli. Doppio click = ruota, Click destro = cambia piano
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DndContext 
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <AutoclaveDropZone 
              autoclave={autoclaveData.autoclave_data}
              scale={scale}
            >
              {toolPositions.map((position) => {
                const odl = layoutGroups
                  .flatMap(group => group.odl_list)
                  .find(o => o.id === position.odl_id)
                
                if (!odl) return null
                
                const group = layoutGroups.find(g => 
                  g.odl_list.some(o => o.id === position.odl_id)
                )
                
                return (
                  <DraggableToolItemStep3
                    key={position.odl_id}
                    odl={odl}
                    position={position}
                    groupColor={group?.color || CYCLE_COLORS[0]}
                    scale={scale}
                    onRotate={handleRotateTool}
                    onChangePlane={handleChangePlane}
                    isConflicted={conflictedODL.has(position.odl_id)}
                    isDragging={activeDrag?.odl_id === position.odl_id}
                  />
                )
              })}
            </AutoclaveDropZone>
            
            <DragOverlay>
              {activeDrag && (
                <div 
                  className="border-2 border-blue-500 bg-blue-100 rounded opacity-80"
                  style={{
                    width: activeDrag.width * scale,
                    height: activeDrag.height * scale
                  }}
                >
                  <div className="p-1 text-xs font-medium">
                    ODL #{activeDrag.odl_id}
                  </div>
                </div>
              )}
            </DragOverlay>
          </DndContext>
        </CardContent>
      </Card>

      {/* Pulsanti navigazione */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Torna alla Selezione Autoclave
        </Button>

        <Button
          onClick={handleNext}
          disabled={!validationResults || validationResults.has_conflicts || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Elaborazione...
            </>
          ) : (
            <>
              Procedi alla Validazione
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 