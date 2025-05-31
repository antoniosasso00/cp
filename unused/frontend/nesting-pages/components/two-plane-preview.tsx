'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import { 
  DragDropContext, 
  Droppable, 
  Draggable, 
  DropResult 
} from '@hello-pangea/dnd'
import { 
  Layers, 
  Package, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Weight,
  Maximize2
} from 'lucide-react'

interface ODLInfo {
  id: number
  parte: {
    part_number: string
    descrizione_breve: string
    num_valvole_richieste: number
    peso_unitario: number
    area_superficie: number
  }
  ciclo_cura: string
  priorita: 'ALTA' | 'MEDIA' | 'BASSA'
  data_scadenza: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  codice: string
  capacita_max_kg: number
  area_piano_cm2: number
  num_linee_vuoto: number
  supporta_due_piani: boolean
}

interface TwoPlanePreviewProps {
  autoclave: AutoclaveInfo
  odlDisponibili: ODLInfo[]
  onSave: (piano1: ODLInfo[], piano2: ODLInfo[]) => void
  onCancel: () => void
}

// Colori per cicli di cura
const CICLO_COLORS = {
  'Standard': 'bg-blue-100 border-blue-300 text-blue-800',
  'Rapido': 'bg-green-100 border-green-300 text-green-800',
  'Delicato': 'bg-yellow-100 border-yellow-300 text-yellow-800',
  'Intensivo': 'bg-red-100 border-red-300 text-red-800',
  'Personalizzato': 'bg-purple-100 border-purple-300 text-purple-800'
}

// Colori per priorità
const PRIORITA_COLORS = {
  'ALTA': 'bg-red-500',
  'MEDIA': 'bg-yellow-500', 
  'BASSA': 'bg-green-500'
}

export function TwoPlanePreview({ autoclave, odlDisponibili, onSave, onCancel }: TwoPlanePreviewProps) {
  const [piano1ODL, setPiano1ODL] = useState<ODLInfo[]>([])
  const [piano2ODL, setPiano2ODL] = useState<ODLInfo[]>([])
  const [odlNonAssegnati, setODLNonAssegnati] = useState<ODLInfo[]>(odlDisponibili)

  // Calcola statistiche per ogni piano
  const calcolaStatsPiano = (odlPiano: ODLInfo[]) => {
    const pesoTotale = odlPiano.reduce((sum, odl) => sum + odl.parte.peso_unitario, 0)
    const areaTotale = odlPiano.reduce((sum, odl) => sum + odl.parte.area_superficie, 0)
    const valvoleTotali = odlPiano.reduce((sum, odl) => sum + odl.parte.num_valvole_richieste, 0)
    
    return {
      count: odlPiano.length,
      peso: pesoTotale,
      area: areaTotale,
      valvole: valvoleTotali,
      pesoPercentuale: (pesoTotale / autoclave.capacita_max_kg) * 100,
      areaPercentuale: (areaTotale / autoclave.area_piano_cm2) * 100,
      valvolePercentuale: (valvoleTotali / autoclave.num_linee_vuoto) * 100
    }
  }

  const statsPiano1 = calcolaStatsPiano(piano1ODL)
  const statsPiano2 = calcolaStatsPiano(piano2ODL)

  // Verifica se la configurazione è valida
  const isConfigurazioneValida = () => {
    return statsPiano1.peso <= autoclave.capacita_max_kg &&
           statsPiano2.peso <= autoclave.capacita_max_kg &&
           statsPiano1.area <= autoclave.area_piano_cm2 &&
           statsPiano2.area <= autoclave.area_piano_cm2 &&
           statsPiano1.valvole <= autoclave.num_linee_vuoto &&
           statsPiano2.valvole <= autoclave.num_linee_vuoto
  }

  // Gestisce il drag & drop
  const handleDragEnd = (result: DropResult) => {
    const { destination, source, draggableId } = result

    if (!destination) return

    const sourceId = source.droppableId
    const destId = destination.droppableId

    // Trova l'ODL trascinato
    const odlId = parseInt(draggableId.split('-')[1])
    let odlTrascinato: ODLInfo | undefined

    // Rimuovi l'ODL dalla lista di origine
    if (sourceId === 'non-assegnati') {
      odlTrascinato = odlNonAssegnati.find(odl => odl.id === odlId)
      setODLNonAssegnati(prev => prev.filter(odl => odl.id !== odlId))
    } else if (sourceId === 'piano1') {
      odlTrascinato = piano1ODL.find(odl => odl.id === odlId)
      setPiano1ODL(prev => prev.filter(odl => odl.id !== odlId))
    } else if (sourceId === 'piano2') {
      odlTrascinato = piano2ODL.find(odl => odl.id === odlId)
      setPiano2ODL(prev => prev.filter(odl => odl.id !== odlId))
    }

    if (!odlTrascinato) return

    // Aggiungi l'ODL alla lista di destinazione
    if (destId === 'non-assegnati') {
      setODLNonAssegnati(prev => [...prev, odlTrascinato!])
    } else if (destId === 'piano1') {
      setPiano1ODL(prev => [...prev, odlTrascinato!])
    } else if (destId === 'piano2') {
      setPiano2ODL(prev => [...prev, odlTrascinato!])
    }
  }

  // Componente per visualizzare un ODL
  const ODLCard = ({ odl, index }: { odl: ODLInfo; index: number }) => (
    <Draggable draggableId={`odl-${odl.id}`} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`
            p-3 border rounded-lg cursor-move transition-all
            ${CICLO_COLORS[odl.ciclo_cura as keyof typeof CICLO_COLORS] || 'bg-gray-100 border-gray-300'}
            ${snapshot.isDragging ? 'shadow-lg scale-105' : 'hover:shadow-md'}
          `}
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <div className="font-medium text-sm">ODL #{odl.id}</div>
              <div className="text-xs text-muted-foreground">{odl.parte.part_number}</div>
            </div>
            <div className={`w-3 h-3 rounded-full ${PRIORITA_COLORS[odl.priorita]}`} 
                 title={`Priorità ${odl.priorita}`} />
          </div>
          
          <div className="text-xs space-y-1">
            <div className="font-medium">{odl.parte.descrizione_breve}</div>
            <div className="flex justify-between text-muted-foreground">
              <span>{odl.parte.peso_unitario.toFixed(1)} kg</span>
              <span>{odl.parte.num_valvole_richieste} valvole</span>
            </div>
            <div className="text-muted-foreground">
              {odl.parte.area_superficie.toFixed(0)} cm²
            </div>
          </div>
          
          <Badge variant="outline" className="mt-2 text-xs">
            {odl.ciclo_cura}
          </Badge>
        </div>
      )}
    </Draggable>
  )

  // Componente per una zona droppable
  const DropZone = ({ 
    droppableId, 
    title, 
    odlList, 
    stats, 
    icon 
  }: { 
    droppableId: string
    title: string
    odlList: ODLInfo[]
    stats?: ReturnType<typeof calcolaStatsPiano>
    icon: React.ReactNode
  }) => (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          {icon}
          {title}
          <Badge variant="secondary">{odlList.length}</Badge>
        </CardTitle>
        {stats && (
          <div className="space-y-2">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <div className="text-muted-foreground">Peso</div>
                <div className="font-medium">{stats.peso.toFixed(1)} kg</div>
                <Progress value={stats.pesoPercentuale} className="h-1 mt-1" />
              </div>
              <div>
                <div className="text-muted-foreground">Area</div>
                <div className="font-medium">{stats.area.toFixed(0)} cm²</div>
                <Progress value={stats.areaPercentuale} className="h-1 mt-1" />
              </div>
              <div>
                <div className="text-muted-foreground">Valvole</div>
                <div className="font-medium">{stats.valvole}</div>
                <Progress value={stats.valvolePercentuale} className="h-1 mt-1" />
              </div>
            </div>
            
            {/* Indicatori di capacità */}
            <div className="flex gap-1">
              {stats.pesoPercentuale > 100 && (
                <Badge variant="destructive" className="text-xs">Peso eccessivo</Badge>
              )}
              {stats.areaPercentuale > 100 && (
                <Badge variant="destructive" className="text-xs">Area eccessiva</Badge>
              )}
              {stats.valvolePercentuale > 100 && (
                <Badge variant="destructive" className="text-xs">Troppe valvole</Badge>
              )}
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <Droppable droppableId={droppableId}>
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className={`
                min-h-[200px] space-y-2 p-2 border-2 border-dashed rounded-lg transition-colors
                ${snapshot.isDraggingOver ? 'border-primary bg-primary/5' : 'border-muted'}
              `}
            >
              {odlList.map((odl, index) => (
                <ODLCard key={odl.id} odl={odl} index={index} />
              ))}
              {provided.placeholder}
              
              {odlList.length === 0 && (
                <div className="flex items-center justify-center h-32 text-muted-foreground">
                  <div className="text-center">
                    <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <div className="text-sm">Trascina qui gli ODL</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </Droppable>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header con info autoclave */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Preview Nesting Due Piani - {autoclave.nome}
          </CardTitle>
          <CardDescription>
            Trascina gli ODL tra i piani per ottimizzare il carico. 
            Capacità: {autoclave.capacita_max_kg} kg per piano, {autoclave.area_piano_cm2} cm² per piano
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Alert validazione */}
      {!isConfigurazioneValida() && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            La configurazione attuale supera i limiti di capacità dell'autoclave. 
            Riorganizza gli ODL per rispettare i vincoli di peso, area e valvole.
          </AlertDescription>
        </Alert>
      )}

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ODL Non Assegnati */}
          <DropZone
            droppableId="non-assegnati"
            title="ODL Disponibili"
            odlList={odlNonAssegnati}
            icon={<Package className="h-5 w-5" />}
          />

          {/* Piano 1 */}
          <DropZone
            droppableId="piano1"
            title="Piano 1"
            odlList={piano1ODL}
            stats={statsPiano1}
            icon={<Layers className="h-5 w-5" />}
          />

          {/* Piano 2 */}
          <DropZone
            droppableId="piano2"
            title="Piano 2"
            odlList={piano2ODL}
            stats={statsPiano2}
            icon={<Layers className="h-5 w-5" />}
          />
        </div>
      </DragDropContext>

      {/* Statistiche totali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Riepilogo Configurazione
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{piano1ODL.length + piano2ODL.length}</div>
              <div className="text-sm text-muted-foreground">ODL Totali</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{(statsPiano1.peso + statsPiano2.peso).toFixed(1)} kg</div>
              <div className="text-sm text-muted-foreground">Peso Totale</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{statsPiano1.valvole + statsPiano2.valvole}</div>
              <div className="text-sm text-muted-foreground">Valvole Totali</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2">
                {isConfigurazioneValida() ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : (
                  <AlertTriangle className="h-6 w-6 text-red-500" />
                )}
              </div>
              <div className="text-sm text-muted-foreground">
                {isConfigurazioneValida() ? 'Configurazione Valida' : 'Configurazione Non Valida'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pulsanti di azione */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          Annulla
        </Button>
        <Button 
          onClick={() => onSave(piano1ODL, piano2ODL)}
          disabled={!isConfigurazioneValida() || (piano1ODL.length === 0 && piano2ODL.length === 0)}
        >
          Salva Configurazione
        </Button>
      </div>
    </div>
  )
} 