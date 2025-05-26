'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  Info
} from 'lucide-react'
import { TwoLevelNestingResponse } from '@/lib/api'

interface NestingPreviewProps {
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

export function NestingPreview({ 
  nestingData, 
  onModify, 
  onConfirm, 
  isEditable = true 
}: NestingPreviewProps) {
  const { toast } = useToast()
  const [modifiedData, setModifiedData] = useState<TwoLevelNestingResponse>(nestingData)
  const [superficiePiano2, setSuperficiePiano2] = useState<number>(
    nestingData.statistiche.area_piano_2_cm2 || 5000
  )
  const [selectedTool, setSelectedTool] = useState<number | null>(null)

  // Combina le posizioni dei due piani in un array unificato
  const getAllPositions = (): ToolPosition[] => {
    const positions: ToolPosition[] = []
    
    // Piano 1
    modifiedData.piano_1.forEach((odl, index) => {
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
    modifiedData.piano_2.forEach((odl, index) => {
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
  }

  const [toolPositions, setToolPositions] = useState<ToolPosition[]>(getAllPositions())

  // Aggiorna le posizioni quando cambiano i dati
  useEffect(() => {
    setToolPositions(getAllPositions())
  }, [modifiedData])

  // Calcola le dimensioni del piano per la visualizzazione
  const SCALE_FACTOR = 0.2 // 1mm = 0.2px per la visualizzazione
  const planeWidth = modifiedData.autoclave.lunghezza * SCALE_FACTOR
  const planeHeight = modifiedData.autoclave.larghezza_piano * SCALE_FACTOR

  // Funzione per spostare un tool da un piano all'altro
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

    // Aggiungi all'array target
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

  // Funzione per aggiornare la superficie del piano 2
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

  // Renderizza un singolo tool
  const renderTool = (position: ToolPosition) => {
    const isSelected = selectedTool === position.odl_id
    const colorClass = position.piano === 1 ? 'bg-blue-100 border-blue-300' : 'bg-green-100 border-green-300'
    const selectedClass = isSelected ? 'ring-2 ring-orange-400' : ''

    return (
      <div
        key={`${position.odl_id}-${position.piano}`}
        className={`absolute border-2 rounded cursor-pointer transition-all hover:shadow-md ${colorClass} ${selectedClass}`}
        style={{
          left: position.x * SCALE_FACTOR,
          top: position.y * SCALE_FACTOR,
          width: position.width * SCALE_FACTOR,
          height: position.height * SCALE_FACTOR,
          minWidth: '40px',
          minHeight: '30px'
        }}
        onClick={() => setSelectedTool(isSelected ? null : position.odl_id)}
        title={`${position.part_number} - ${position.descrizione} (${position.peso_kg}kg)`}
      >
        <div className="p-1 text-xs font-medium text-center overflow-hidden">
          <div className="truncate">{position.part_number}</div>
          <div className="text-gray-600">{position.peso_kg}kg</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header con statistiche */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Weight className="h-4 w-4" />
              Carico Totale
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {modifiedData.statistiche.peso_totale_kg.toFixed(1)} kg
            </div>
            <div className="text-sm text-muted-foreground">
              Max: {modifiedData.autoclave.max_load_kg} kg
            </div>
            {modifiedData.statistiche.carico_valido ? (
              <Badge variant="success" className="mt-2">
                <CheckCircle className="h-3 w-3 mr-1" />
                Carico Valido
              </Badge>
            ) : (
              <Badge variant="destructive" className="mt-2">
                <AlertTriangle className="h-3 w-3 mr-1" />
                Carico Eccessivo
              </Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Piano 1
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {modifiedData.piano_1.length} tools
            </div>
            <div className="text-sm text-muted-foreground">
              {modifiedData.statistiche.peso_piano_1_kg.toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground">
              {modifiedData.statistiche.area_piano_1_cm2.toFixed(0)} cm²
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Piano 2
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {modifiedData.piano_2.length} tools
            </div>
            <div className="text-sm text-muted-foreground">
              {modifiedData.statistiche.peso_piano_2_kg.toFixed(1)} kg
            </div>
            <div className="text-xs text-muted-foreground">
              {modifiedData.statistiche.area_piano_2_cm2.toFixed(0)} cm²
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Configurazione superficie piano 2 */}
      {isEditable && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Configurazione Piano 2</CardTitle>
            <CardDescription>
              Modifica la superficie effettiva del piano superiore
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Label htmlFor="superficie-piano-2">Superficie Piano 2 (cm²)</Label>
              <Input
                id="superficie-piano-2"
                type="number"
                value={superficiePiano2}
                onChange={(e) => updateSuperficiePiano2(Number(e.target.value))}
                className="w-32"
                min="0"
                step="100"
              />
              <Badge variant="outline">
                Max: {modifiedData.autoclave.lunghezza * modifiedData.autoclave.larghezza_piano / 100} cm²
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Visualizzazione 2D dei piani */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Piano 1 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              Piano 1 (Inferiore)
            </CardTitle>
            <CardDescription>
              {modifiedData.piano_1.length} tools - {modifiedData.statistiche.peso_piano_1_kg.toFixed(1)} kg
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div 
              className="relative border-2 border-dashed border-gray-300 bg-gray-50"
              style={{ 
                width: planeWidth, 
                height: planeHeight,
                minWidth: '300px',
                minHeight: '200px'
              }}
            >
              {toolPositions
                .filter(p => p.piano === 1)
                .map(position => renderTool(position))
              }
            </div>
          </CardContent>
        </Card>

        {/* Piano 2 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              Piano 2 (Superiore)
            </CardTitle>
            <CardDescription>
              {modifiedData.piano_2.length} tools - {modifiedData.statistiche.peso_piano_2_kg.toFixed(1)} kg
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div 
              className="relative border-2 border-dashed border-gray-300 bg-gray-50"
              style={{ 
                width: planeWidth, 
                height: planeHeight,
                minWidth: '300px',
                minHeight: '200px'
              }}
            >
              {toolPositions
                .filter(p => p.piano === 2)
                .map(position => renderTool(position))
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pannello di controllo per tool selezionato */}
      {selectedTool && isEditable && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Controlli Tool Selezionato</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const tool = toolPositions.find(p => p.odl_id === selectedTool)
              if (!tool) return null

              return (
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="font-medium">{tool.part_number}</div>
                    <div className="text-sm text-muted-foreground">{tool.descrizione}</div>
                    <div className="text-xs text-muted-foreground">
                      {tool.peso_kg}kg - Piano {tool.piano}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => moveToolToPiano(selectedTool, 1)}
                      disabled={tool.piano === 1}
                    >
                      <Move className="h-4 w-4 mr-1" />
                      Piano 1
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => moveToolToPiano(selectedTool, 2)}
                      disabled={tool.piano === 2}
                    >
                      <Move className="h-4 w-4 mr-1" />
                      Piano 2
                    </Button>
                  </div>
                </div>
              )
            })()}
          </CardContent>
        </Card>
      )}

      {/* Lista ODL non pianificabili */}
      {modifiedData.odl_non_pianificabili.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              ODL Non Pianificabili ({modifiedData.odl_non_pianificabili.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {modifiedData.odl_non_pianificabili.map((odl) => (
                <div key={odl.odl_id} className="flex justify-between items-center p-2 bg-orange-50 rounded">
                  <div>
                    <div className="font-medium">{odl.part_number}</div>
                    <div className="text-sm text-muted-foreground">{odl.descrizione}</div>
                  </div>
                  <Badge variant="outline" className="text-orange-700">
                    {odl.motivo}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pulsanti di azione */}
      {isEditable && onConfirm && (
        <div className="flex justify-end gap-4">
          <Button
            onClick={() => setModifiedData(nestingData)}
            variant="outline"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Ripristina
          </Button>
          <Button
            onClick={onConfirm}
            disabled={!modifiedData.statistiche.carico_valido}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Conferma Nesting
          </Button>
        </div>
      )}
    </div>
  )
} 