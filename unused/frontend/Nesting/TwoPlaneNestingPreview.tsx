'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { 
  Package, 
  Weight, 
  Layers, 
  Move, 
  RotateCcw, 
  CheckCircle,
  AlertTriangle,
  Info,
  ArrowUpDown,
  Maximize2
} from 'lucide-react'
import { TwoLevelNestingResponse } from '@/lib/api'

interface TwoPlaneNestingPreviewProps {
  nestingData: TwoLevelNestingResponse
  onModify?: (modifiedData: TwoLevelNestingResponse) => void
  onConfirm?: () => void
  isEditable?: boolean
}

interface ToolPosition {
  odl_id: number
  x: number
  y: number
  width: number
  height: number
  piano: 1 | 2
  part_number: string
  descrizione: string
  peso_kg: number
  area_cm2: number
  priorita: number
}

interface PlaneStats {
  odl_count: number
  peso_totale: number
  area_utilizzata: number
  area_disponibile: number
  efficienza: number
}

export function TwoPlaneNestingPreview({ 
  nestingData, 
  onModify, 
  onConfirm, 
  isEditable = true 
}: TwoPlaneNestingPreviewProps) {
  const { toast } = useToast()
  const [modifiedData, setModifiedData] = useState<TwoLevelNestingResponse>(nestingData)
  const [superficiePiano2, setSuperficiePiano2] = useState<number>(
    nestingData.statistiche.area_piano_2_cm2 || 5000
  )
  const [selectedTool, setSelectedTool] = useState<number | null>(null)
  const [draggedTool, setDraggedTool] = useState<number | null>(null)

  // ✅ SEZIONE 3: Combina le posizioni dei due piani in un array unificato
  const getAllPositions = useCallback((): ToolPosition[] => {
    const positions: ToolPosition[] = []
    
    // Piano 1
    modifiedData.piano_1.forEach((odl) => {
      const position = modifiedData.posizioni_piano_1.find(p => p.odl_id === odl.odl_id)
      if (position) {
        positions.push({
          ...position,
          piano: 1,
          part_number: odl.part_number,
          descrizione: odl.descrizione,
          peso_kg: odl.peso_kg,
          area_cm2: odl.area_cm2,
          priorita: odl.priorita
        })
      }
    })
    
    // Piano 2
    modifiedData.piano_2.forEach((odl) => {
      const position = modifiedData.posizioni_piano_2.find(p => p.odl_id === odl.odl_id)
      if (position) {
        positions.push({
          ...position,
          piano: 2,
          part_number: odl.part_number,
          descrizione: odl.descrizione,
          peso_kg: odl.peso_kg,
          area_cm2: odl.area_cm2,
          priorita: odl.priorita
        })
      }
    })
    
    return positions
  }, [modifiedData])

  const [toolPositions, setToolPositions] = useState<ToolPosition[]>(getAllPositions())

  // Aggiorna le posizioni quando cambiano i dati
  useEffect(() => {
    setToolPositions(getAllPositions())
  }, [getAllPositions])

  // ✅ SEZIONE 3: Calcola le statistiche per ogni piano
  const getPlaneStats = (piano: 1 | 2): PlaneStats => {
    const planeData = piano === 1 ? modifiedData.piano_1 : modifiedData.piano_2
    const planePositions = piano === 1 ? modifiedData.posizioni_piano_1 : modifiedData.posizioni_piano_2
    
    const peso_totale = planeData.reduce((sum, odl) => sum + odl.peso_kg, 0)
    const area_utilizzata = planeData.reduce((sum, odl) => sum + odl.area_cm2, 0)
    const area_disponibile = piano === 1 
      ? modifiedData.autoclave.lunghezza * modifiedData.autoclave.larghezza_piano
      : superficiePiano2
    
    return {
      odl_count: planeData.length,
      peso_totale,
      area_utilizzata,
      area_disponibile,
      efficienza: area_disponibile > 0 ? (area_utilizzata / area_disponibile) * 100 : 0
    }
  }

  // ✅ SEZIONE 3: Funzione per spostare un tool da un piano all'altro
  const moveToolToPiano = (odlId: number, targetPiano: 1 | 2) => {
    if (!isEditable) return

    const currentPosition = toolPositions.find(p => p.odl_id === odlId)
    if (!currentPosition || currentPosition.piano === targetPiano) return

    // Trova l'ODL nei dati
    const sourceArray = currentPosition.piano === 1 ? modifiedData.piano_1 : modifiedData.piano_2
    const targetArray = targetPiano === 1 ? modifiedData.piano_1 : modifiedData.piano_2
    const sourcePositions = currentPosition.piano === 1 ? modifiedData.posizioni_piano_1 : modifiedData.posizioni_piano_2
    const targetPositions = targetPiano === 1 ? modifiedData.posizioni_piano_1 : modifiedData.posizioni_piano_2

    const odlIndex = sourceArray.findIndex(odl => odl.odl_id === odlId)
    const positionIndex = sourcePositions.findIndex(p => p.odl_id === odlId)

    if (odlIndex === -1 || positionIndex === -1) return

    // Rimuovi dall'array sorgente
    const [odlToMove] = sourceArray.splice(odlIndex, 1)
    const [positionToMove] = sourcePositions.splice(positionIndex, 1)

    // Aggiungi all'array target con posizione di default
    targetArray.push(odlToMove)
    targetPositions.push({
      ...positionToMove,
      x: 10, // Posizione di default
      y: 10
    })

    // Aggiorna lo stato
    const newData = { ...modifiedData }
    setModifiedData(newData)
    
    if (onModify) {
      onModify(newData)
    }

    toast({
      title: 'Tool spostato',
      description: `${odlToMove.part_number} spostato al piano ${targetPiano}`,
    })
  }

  // ✅ SEZIONE 3: Funzione per aggiornare la superficie del piano 2
  const updateSuperficiePiano2 = (newSuperficie: number) => {
    setSuperficiePiano2(newSuperficie)
    
    // Aggiorna i dati modificati
    const newData = {
      ...modifiedData,
      statistiche: {
        ...modifiedData.statistiche,
        area_piano_2_cm2: newSuperficie
      }
    }
    setModifiedData(newData)
    
    if (onModify) {
      onModify(newData)
    }
  }

  // Calcola le dimensioni del piano per la visualizzazione
  const SCALE_FACTOR = 0.15 // Fattore di scala per la visualizzazione
  const planeWidth = modifiedData.autoclave.lunghezza * SCALE_FACTOR
  const planeHeight = modifiedData.autoclave.larghezza_piano * SCALE_FACTOR

  // ✅ SEZIONE 3: Renderizza un singolo tool con drag & drop
  const renderTool = (position: ToolPosition) => {
    const isSelected = selectedTool === position.odl_id
    const isDragged = draggedTool === position.odl_id
    const colorClass = position.piano === 1 ? 'bg-blue-100 border-blue-300' : 'bg-green-100 border-green-300'
    const selectedClass = isSelected ? 'ring-2 ring-orange-400' : ''
    const draggedClass = isDragged ? 'opacity-50 scale-105' : ''

    // Colore basato sulla priorità
    const priorityColor = position.priorita === 1 ? 'border-red-500' : 
                         position.priorita === 2 ? 'border-orange-500' : 
                         'border-gray-300'

    return (
      <div
        key={`${position.odl_id}-${position.piano}`}
        className={`absolute border-2 rounded cursor-pointer transition-all hover:shadow-md ${colorClass} ${selectedClass} ${draggedClass} ${priorityColor}`}
        style={{
          left: position.x * SCALE_FACTOR,
          top: position.y * SCALE_FACTOR,
          width: Math.max(position.width * SCALE_FACTOR, 40),
          height: Math.max(position.height * SCALE_FACTOR, 30),
          minWidth: '40px',
          minHeight: '30px'
        }}
        onClick={() => setSelectedTool(isSelected ? null : position.odl_id)}
        onDragStart={(e) => {
          if (isEditable) {
            setDraggedTool(position.odl_id)
            e.dataTransfer.setData('text/plain', position.odl_id.toString())
          }
        }}
        onDragEnd={() => setDraggedTool(null)}
        draggable={isEditable}
        title={`${position.part_number} - ${position.descrizione} (${position.peso_kg}kg, Priorità: ${position.priorita})`}
      >
        <div className="p-1 text-xs font-medium text-center overflow-hidden">
          <div className="truncate font-bold">{position.part_number}</div>
          <div className="text-gray-600">{position.peso_kg}kg</div>
          <div className="text-xs text-gray-500">P{position.priorita}</div>
        </div>
      </div>
    )
  }

  // ✅ SEZIONE 3: Renderizza un piano con drop zone
  const renderPlane = (piano: 1 | 2) => {
    const stats = getPlaneStats(piano)
    const positions = toolPositions.filter(p => p.piano === piano)
    const planeTitle = piano === 1 ? 'Piano Inferiore' : 'Piano Superiore'
    const planeColor = piano === 1 ? 'border-blue-300 bg-blue-50' : 'border-green-300 bg-green-50'

    return (
      <Card className="flex-1">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              {planeTitle}
              <Badge variant={piano === 1 ? 'default' : 'secondary'}>
                {stats.odl_count} ODL
              </Badge>
            </div>
            {isEditable && selectedTool && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => moveToolToPiano(selectedTool, piano)}
                disabled={toolPositions.find(p => p.odl_id === selectedTool)?.piano === piano}
              >
                <ArrowUpDown className="h-4 w-4 mr-1" />
                Sposta qui
              </Button>
            )}
          </CardTitle>
          <CardDescription>
            Peso: {stats.peso_totale.toFixed(1)}kg | Area: {stats.area_utilizzata.toFixed(0)}cm² | 
            Efficienza: {stats.efficienza.toFixed(1)}%
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div 
            className={`relative border-2 border-dashed ${planeColor} rounded-lg overflow-hidden`}
            style={{
              width: planeWidth,
              height: planeHeight,
              minWidth: '400px',
              minHeight: '300px'
            }}
            onDrop={(e) => {
              if (isEditable) {
                e.preventDefault()
                const odlId = parseInt(e.dataTransfer.getData('text/plain'))
                if (odlId) {
                  moveToolToPiano(odlId, piano)
                }
              }
            }}
            onDragOver={(e) => {
              if (isEditable) {
                e.preventDefault()
              }
            }}
          >
            {/* Griglia di riferimento */}
            <div className="absolute inset-0 opacity-20">
              {Array.from({ length: Math.floor(planeWidth / 50) }).map((_, i) => (
                <div
                  key={`v-${i}`}
                  className="absolute border-l border-gray-300"
                  style={{ left: i * 50 }}
                />
              ))}
              {Array.from({ length: Math.floor(planeHeight / 50) }).map((_, i) => (
                <div
                  key={`h-${i}`}
                  className="absolute border-t border-gray-300"
                  style={{ top: i * 50 }}
                />
              ))}
            </div>

            {/* Renderizza i tool */}
            {positions.map(renderTool)}

            {/* Messaggio se vuoto */}
            {positions.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Nessun tool assegnato</p>
                  {isEditable && <p className="text-sm">Trascina qui i tool dall'altro piano</p>}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  const stats1 = getPlaneStats(1)
  const stats2 = getPlaneStats(2)
  const isValidLoad = modifiedData.statistiche.carico_valido

  return (
    <div className="space-y-6">
      {/* Header con informazioni generali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Maximize2 className="h-5 w-5" />
              Preview Nesting su Due Piani
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={isValidLoad ? 'default' : 'destructive'}>
                {isValidLoad ? 'Carico Valido' : 'Carico Non Valido'}
              </Badge>
              {onConfirm && (
                <Button onClick={onConfirm} disabled={!isValidLoad}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Conferma Nesting
                </Button>
              )}
            </div>
          </CardTitle>
          <CardDescription>
            Autoclave: {modifiedData.autoclave.nome} | 
            Peso totale: {modifiedData.statistiche.peso_totale_kg.toFixed(1)}kg / {modifiedData.autoclave.max_load_kg}kg |
            ODL totali: {stats1.odl_count + stats2.odl_count}
          </CardDescription>
        </CardHeader>
        
        {!isValidLoad && (
          <CardContent>
            <div className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span>{modifiedData.statistiche.motivo_invalidita}</span>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Controlli per piano 2 */}
      {isEditable && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Configurazione Piano Superiore</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Label htmlFor="superficie-piano-2">Superficie massima (cm²):</Label>
              <Input
                id="superficie-piano-2"
                type="number"
                value={superficiePiano2}
                onChange={(e) => updateSuperficiePiano2(Number(e.target.value))}
                className="w-32"
                min="1000"
                max="50000"
                step="100"
              />
              <span className="text-sm text-muted-foreground">
                Attuale: {stats2.area_utilizzata.toFixed(0)}cm²
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Visualizzazione dei due piani */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderPlane(1)}
        {renderPlane(2)}
      </div>

      {/* Informazioni tool selezionato */}
      {selectedTool && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Dettagli Tool Selezionato</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const tool = toolPositions.find(p => p.odl_id === selectedTool)
              if (!tool) return null
              
              return (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Part Number:</Label>
                    <p className="font-medium">{tool.part_number}</p>
                  </div>
                  <div>
                    <Label>Descrizione:</Label>
                    <p className="font-medium">{tool.descrizione}</p>
                  </div>
                  <div>
                    <Label>Peso:</Label>
                    <p className="font-medium">{tool.peso_kg}kg</p>
                  </div>
                  <div>
                    <Label>Area:</Label>
                    <p className="font-medium">{tool.area_cm2}cm²</p>
                  </div>
                  <div>
                    <Label>Piano Assegnato:</Label>
                    <p className="font-medium">Piano {tool.piano}</p>
                  </div>
                  <div>
                    <Label>Priorità:</Label>
                    <Badge variant={tool.priorita === 1 ? 'destructive' : tool.priorita === 2 ? 'default' : 'secondary'}>
                      Priorità {tool.priorita}
                    </Badge>
                  </div>
                  {isEditable && (
                    <div className="col-span-2">
                      <Label>Azioni:</Label>
                      <div className="flex gap-2 mt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => moveToolToPiano(selectedTool, 1)}
                          disabled={tool.piano === 1}
                        >
                          Sposta a Piano 1
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => moveToolToPiano(selectedTool, 2)}
                          disabled={tool.piano === 2}
                        >
                          Sposta a Piano 2
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}
          </CardContent>
        </Card>
      )}

      {/* Statistiche dettagliate */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg text-blue-600">Statistiche Piano 1</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span>ODL:</span>
              <span className="font-medium">{stats1.odl_count}</span>
            </div>
            <div className="flex justify-between">
              <span>Peso totale:</span>
              <span className="font-medium">{stats1.peso_totale.toFixed(1)}kg</span>
            </div>
            <div className="flex justify-between">
              <span>Area utilizzata:</span>
              <span className="font-medium">{stats1.area_utilizzata.toFixed(0)}cm²</span>
            </div>
            <div className="flex justify-between">
              <span>Efficienza:</span>
              <span className="font-medium">{stats1.efficienza.toFixed(1)}%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg text-green-600">Statistiche Piano 2</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span>ODL:</span>
              <span className="font-medium">{stats2.odl_count}</span>
            </div>
            <div className="flex justify-between">
              <span>Peso totale:</span>
              <span className="font-medium">{stats2.peso_totale.toFixed(1)}kg</span>
            </div>
            <div className="flex justify-between">
              <span>Area utilizzata:</span>
              <span className="font-medium">{stats2.area_utilizzata.toFixed(0)}cm²</span>
            </div>
            <div className="flex justify-between">
              <span>Efficienza:</span>
              <span className="font-medium">{stats2.efficienza.toFixed(1)}%</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 