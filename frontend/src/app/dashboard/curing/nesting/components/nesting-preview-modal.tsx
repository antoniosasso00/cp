'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { NestingPreview, nestingApi } from '@/lib/api'
import { 
  Loader2, 
  Save, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Move,
  Eye,
  Trash2,
  RotateCcw,
  Download,
  RefreshCw,
  Settings,
  Info,
  Package,
  Gauge
} from 'lucide-react'
import { DragDropContext, Droppable, Draggable, DropResult, DroppableProvided, DroppableStateSnapshot, DraggableProvided, DraggableStateSnapshot } from 'react-beautiful-dnd'
import NestingParametersPanel, { NestingParameters } from '@/components/nesting/NestingParametersPanel'

interface NestingPreviewModalProps {
  isOpen: boolean
  onClose: () => void
  previewData: NestingPreview | null
  onSaveDraft: () => void
  onApprove: () => void
}

interface ODLItem {
  id: number
  part_number: string
  descrizione: string
  area_cm2: number
  num_valvole: number
  priorita: number
  color: string
}

interface AutoclaveData {
  id: number
  nome: string
  codice: string
  lunghezza: number
  larghezza_piano: number
  area_totale_cm2: number
  area_utilizzata_cm2: number
  valvole_totali: number
  valvole_utilizzate: number
  odl_inclusi: ODLItem[]
}

export default function NestingPreviewModal({
  isOpen,
  onClose,
  previewData,
  onSaveDraft,
  onApprove
}: NestingPreviewModalProps) {
  const [autoclavi, setAutoclavi] = useState<AutoclaveData[]>([])
  const [odlEsclusi, setOdlEsclusi] = useState<any[]>([])
  const [isModified, setIsModified] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('0')
  const [nestingParameters, setNestingParameters] = useState<NestingParameters>({
    distanza_perimetrale_cm: 1.0,
    spaziatura_tra_tool_cm: 0.5,
    rotazione_tool_abilitata: true,
    priorita_ottimizzazione: 'EQUILIBRATO'
  })
  const [isParametersPanelCollapsed, setIsParametersPanelCollapsed] = useState(false)
  const { toast } = useToast()

  // Inizializza i dati quando si apre il modal
  useEffect(() => {
    if (previewData && previewData.success) {
      setAutoclavi(previewData.autoclavi)
      setOdlEsclusi(previewData.odl_esclusi)
      setIsModified(false)
      // Imposta il primo tab attivo se ci sono autoclavi
      if (previewData.autoclavi.length > 0) {
        setActiveTab('0')
      }
    }
  }, [previewData])

  // Gestisce il drag and drop degli ODL
  const handleDragEnd = (result: DropResult) => {
    const { destination, source, draggableId } = result

    if (!destination) return

    // Se l'ODL è stato spostato nella stessa posizione, non fare nulla
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return
    }

    const odlId = parseInt(draggableId.split('-')[1])
    
    // Trova l'ODL da spostare
    let odlToMove: ODLItem | null = null
    let sourceAutoclaveIndex = -1
    
    // Cerca l'ODL nelle autoclavi
    autoclavi.forEach((autoclave, index) => {
      const odlIndex = autoclave.odl_inclusi.findIndex(odl => odl.id === odlId)
      if (odlIndex !== -1) {
        odlToMove = autoclave.odl_inclusi[odlIndex]
        sourceAutoclaveIndex = index
      }
    })

    if (!odlToMove || sourceAutoclaveIndex === -1) return

    const newAutoclavi = [...autoclavi]
    
    // Rimuovi l'ODL dalla posizione originale
    newAutoclavi[sourceAutoclaveIndex].odl_inclusi.splice(
      newAutoclavi[sourceAutoclaveIndex].odl_inclusi.findIndex(odl => odl.id === odlId),
      1
    )

    // Se la destinazione è "excluded", aggiungi agli esclusi
    if (destination.droppableId === 'excluded') {
      setOdlEsclusi(prev => [...prev, {
        id: odlToMove!.id,
        part_number: odlToMove!.part_number,
        descrizione: odlToMove!.descrizione,
        motivo: "Escluso manualmente",
        priorita: odlToMove!.priorita,
        num_valvole: odlToMove!.num_valvole
      }])
    } else {
      // Altrimenti, aggiungi alla nuova autoclave
      const destAutoclaveIndex = parseInt(destination.droppableId.split('-')[1])
      newAutoclavi[destAutoclaveIndex].odl_inclusi.splice(destination.index, 0, odlToMove)
    }

    // Ricalcola le statistiche per le autoclavi modificate
    updateAutoclaveStats(newAutoclavi, sourceAutoclaveIndex)
    if (destination.droppableId !== 'excluded') {
      const destAutoclaveIndex = parseInt(destination.droppableId.split('-')[1])
      updateAutoclaveStats(newAutoclavi, destAutoclaveIndex)
    }

    setAutoclavi(newAutoclavi)
    setIsModified(true)
  }

  // Aggiorna le statistiche di un'autoclave
  const updateAutoclaveStats = (autoclaveList: AutoclaveData[], autoclaveIndex: number) => {
    const autoclave = autoclaveList[autoclaveIndex]
    const totalArea = autoclave.odl_inclusi.reduce((sum, odl) => sum + odl.area_cm2, 0)
    const totalValvole = autoclave.odl_inclusi.reduce((sum, odl) => sum + odl.num_valvole, 0)
    
    autoclave.area_utilizzata_cm2 = totalArea
    autoclave.valvole_utilizzate = totalValvole
  }

  // Rimuove un ODL e lo mette negli esclusi
  const handleExcludeODL = (autoclaveIndex: number, odlIndex: number) => {
    const newAutoclavi = [...autoclavi]
    const odlToExclude = newAutoclavi[autoclaveIndex].odl_inclusi[odlIndex]
    
    // Rimuovi dall'autoclave
    newAutoclavi[autoclaveIndex].odl_inclusi.splice(odlIndex, 1)
    
    // Aggiungi agli esclusi
    setOdlEsclusi(prev => [...prev, {
      id: odlToExclude.id,
      part_number: odlToExclude.part_number,
      descrizione: odlToExclude.descrizione,
      motivo: "Escluso manualmente",
      priorita: odlToExclude.priorita,
      num_valvole: odlToExclude.num_valvole
    }])
    
    // Aggiorna statistiche
    updateAutoclaveStats(newAutoclavi, autoclaveIndex)
    setAutoclavi(newAutoclavi)
    setIsModified(true)
  }

  // Ripristina un ODL escluso
  const handleRestoreODL = (excludedIndex: number, targetAutoclaveIndex: number) => {
    const odlToRestore = odlEsclusi[excludedIndex]
    const newOdlEsclusi = [...odlEsclusi]
    const newAutoclavi = [...autoclavi]
    
    // Rimuovi dagli esclusi
    newOdlEsclusi.splice(excludedIndex, 1)
    
    // Aggiungi all'autoclave target
    const restoredODL: ODLItem = {
      id: odlToRestore.id,
      part_number: odlToRestore.part_number,
      descrizione: odlToRestore.descrizione,
      area_cm2: 0, // Dovremmo recuperare questo dato
      num_valvole: odlToRestore.num_valvole,
      priorita: odlToRestore.priorita,
      color: `#${Math.floor(Math.random()*16777215).toString(16)}`
    }
    
    newAutoclavi[targetAutoclaveIndex].odl_inclusi.push(restoredODL)
    
    // Aggiorna statistiche
    updateAutoclaveStats(newAutoclavi, targetAutoclaveIndex)
    
    setOdlEsclusi(newOdlEsclusi)
    setAutoclavi(newAutoclavi)
    setIsModified(true)
  }

  // Gestisce il cambiamento dei parametri di nesting
  const handleParametersChange = (newParameters: NestingParameters) => {
    setNestingParameters(newParameters)
  }

  // Gestisce la rigenerazione automatica quando cambiano i parametri
  const handleParametersRegeneratePreview = async () => {
    await handleRegenerateNesting()
  }

  // Rigenera il nesting
  const handleRegenerateNesting = async () => {
    try {
      setIsRegenerating(true)
      
      // Usa i parametri di nesting correnti per la rigenerazione
      const parametersForApi = {
        distanza_perimetrale_cm: nestingParameters.distanza_perimetrale_cm,
        spaziatura_tra_tool_cm: nestingParameters.spaziatura_tra_tool_cm,
        rotazione_tool_abilitata: nestingParameters.rotazione_tool_abilitata,
        priorita_ottimizzazione: nestingParameters.priorita_ottimizzazione
      }
      
      const newPreview = await nestingApi.getPreview(parametersForApi)
      
      if (newPreview.success) {
        setAutoclavi(newPreview.autoclavi)
        setOdlEsclusi(newPreview.odl_esclusi)
        setIsModified(false)
        
        toast({
          title: 'Nesting rigenerato!',
          description: `${newPreview.message} (Parametri applicati: ${parametersForApi.distanza_perimetrale_cm}cm perimetro, ${parametersForApi.spaziatura_tra_tool_cm}cm spaziatura)`,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore nella rigenerazione',
          description: newPreview.message,
        })
      }
    } catch (error) {
      console.error('Errore nella rigenerazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella rigenerazione',
        description: 'Impossibile rigenerare il nesting.',
      })
    } finally {
      setIsRegenerating(false)
    }
  }

  // Salva le modifiche come bozza
  const handleSaveModifications = async () => {
    if (!isModified) {
      toast({
        title: 'Nessuna modifica da salvare',
        description: 'Non sono state apportate modifiche al nesting.',
      })
      return
    }

    try {
      setIsSaving(true)
      
      const draftData = {
        autoclavi: autoclavi,
        odl_esclusi: odlEsclusi.map(odl => odl.id)
      }
      
      const result = await nestingApi.saveDraft(draftData)
      
      if (result.success) {
        toast({
          title: 'Modifiche salvate!',
          description: result.message,
        })
        setIsModified(false)
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore nel salvataggio',
          description: result.message,
        })
      }
    } catch (error) {
      console.error('Errore nel salvataggio:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nel salvataggio',
        description: 'Impossibile salvare le modifiche.',
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Approva il nesting finale
  const handleApproveNesting = async () => {
    try {
      // Prima salva le modifiche se necessario
      if (isModified) {
        await handleSaveModifications()
      }
      
      // Poi approva
      await onApprove()
      
      toast({
        title: 'Nesting approvato!',
        description: 'Il nesting è stato approvato e gli ODL sono stati aggiornati.',
      })
      
      onClose()
    } catch (error) {
      console.error('Errore nell\'approvazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nell\'approvazione',
        description: 'Impossibile approvare il nesting.',
      })
    }
  }

  // Calcola la percentuale di utilizzo
  const getUsagePercent = (used: number, total: number) => {
    return total > 0 ? Math.round((used / total) * 100) : 0
  }

  // Determina il colore del badge in base alla percentuale
  const getUsageBadgeVariant = (percent: number) => {
    if (percent >= 90) return 'destructive'
    if (percent >= 70) return 'default'
    return 'secondary'
  }

  // Calcola le statistiche totali
  const totalStats = {
    totalODL: autoclavi.reduce((sum, autoclave) => sum + autoclave.odl_inclusi.length, 0),
    totalExcluded: odlEsclusi.length,
    totalAutoclavi: autoclavi.length,
    averageAreaUsage: autoclavi.length > 0 
      ? Math.round(autoclavi.reduce((sum, autoclave) => 
          sum + getUsagePercent(autoclave.area_utilizzata_cm2, autoclave.area_totale_cm2), 0
        ) / autoclavi.length)
      : 0,
    averageValveUsage: autoclavi.length > 0
      ? Math.round(autoclavi.reduce((sum, autoclave) => 
          sum + getUsagePercent(autoclave.valvole_utilizzate, autoclave.valvole_totali), 0
        ) / autoclavi.length)
      : 0
  }

  if (!previewData) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Preview Nesting Interattivo
            {isModified && (
              <Badge variant="outline" className="ml-2">
                Modificato
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        {!previewData.success ? (
          <div className="flex-1 flex items-center justify-center">
            <Alert className="max-w-md">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                {previewData.message}
              </AlertDescription>
            </Alert>
          </div>
        ) : (
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Statistiche generali */}
            <div className="flex-shrink-0 grid grid-cols-5 gap-4 mb-4">
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Package className="h-4 w-4 text-blue-500" />
                    <div>
                      <div className="text-2xl font-bold">{totalStats.totalODL}</div>
                      <div className="text-xs text-muted-foreground">ODL Inclusi</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-500" />
                    <div>
                      <div className="text-2xl font-bold">{totalStats.totalExcluded}</div>
                      <div className="text-xs text-muted-foreground">ODL Esclusi</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Settings className="h-4 w-4 text-green-500" />
                    <div>
                      <div className="text-2xl font-bold">{totalStats.totalAutoclavi}</div>
                      <div className="text-xs text-muted-foreground">Autoclavi</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Gauge className="h-4 w-4 text-orange-500" />
                    <div>
                      <div className="text-2xl font-bold">{totalStats.averageAreaUsage}%</div>
                      <div className="text-xs text-muted-foreground">Area Media</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Gauge className="h-4 w-4 text-purple-500" />
                    <div>
                      <div className="text-2xl font-bold">{totalStats.averageValveUsage}%</div>
                      <div className="text-xs text-muted-foreground">Valvole Media</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Pannello Parametri Nesting */}
            <div className="flex-shrink-0 mb-4">
              <NestingParametersPanel
                parameters={nestingParameters}
                onParametersChange={handleParametersChange}
                onRegeneratePreview={handleParametersRegeneratePreview}
                isRegenerating={isRegenerating}
                isCollapsed={isParametersPanelCollapsed}
                onToggleCollapse={() => setIsParametersPanelCollapsed(!isParametersPanelCollapsed)}
              />
            </div>

            <DragDropContext onDragEnd={handleDragEnd}>
              <div className="flex-1 overflow-hidden">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                  <TabsList className="flex-shrink-0 grid w-full" style={{ gridTemplateColumns: `repeat(${autoclavi.length + 1}, 1fr)` }}>
                    {autoclavi.map((autoclave, index) => (
                      <TabsTrigger key={autoclave.id} value={index.toString()} className="text-xs">
                        <div className="flex flex-col items-center">
                          <span className="font-medium">{autoclave.nome}</span>
                          <span className="text-[10px] opacity-75">
                            {autoclave.odl_inclusi.length} ODL
                          </span>
                        </div>
                      </TabsTrigger>
                    ))}
                    <TabsTrigger value="excluded" className="text-xs">
                      <div className="flex flex-col items-center">
                        <span className="font-medium">Esclusi</span>
                        <span className="text-[10px] opacity-75">
                          {odlEsclusi.length} ODL
                        </span>
                      </div>
                    </TabsTrigger>
                  </TabsList>

                  <div className="flex-1 overflow-auto">
                    {autoclavi.map((autoclave, autoclaveIndex) => (
                      <TabsContent key={autoclave.id} value={autoclaveIndex.toString()} className="h-full mt-4">
                        <Card className="h-full">
                          <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg">
                                {autoclave.nome} ({autoclave.codice})
                              </CardTitle>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">
                                  {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
                                </Badge>
                              </div>
                            </div>
                            
                            {/* Statistiche autoclave */}
                            <div className="grid grid-cols-2 gap-4 mt-3">
                              <div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm font-medium">Utilizzo Area</span>
                                  <Badge variant={getUsageBadgeVariant(getUsagePercent(autoclave.area_utilizzata_cm2, autoclave.area_totale_cm2))}>
                                    {getUsagePercent(autoclave.area_utilizzata_cm2, autoclave.area_totale_cm2)}%
                                  </Badge>
                                </div>
                                <Progress 
                                  value={getUsagePercent(autoclave.area_utilizzata_cm2, autoclave.area_totale_cm2)} 
                                  className="h-2"
                                />
                                <div className="text-xs text-muted-foreground mt-1">
                                  {autoclave.area_utilizzata_cm2.toFixed(1)} / {autoclave.area_totale_cm2.toFixed(1)} cm²
                                </div>
                              </div>
                              
                              <div>
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm font-medium">Utilizzo Valvole</span>
                                  <Badge variant={getUsageBadgeVariant(getUsagePercent(autoclave.valvole_utilizzate, autoclave.valvole_totali))}>
                                    {getUsagePercent(autoclave.valvole_utilizzate, autoclave.valvole_totali)}%
                                  </Badge>
                                </div>
                                <Progress 
                                  value={getUsagePercent(autoclave.valvole_utilizzate, autoclave.valvole_totali)} 
                                  className="h-2"
                                />
                                <div className="text-xs text-muted-foreground mt-1">
                                  {autoclave.valvole_utilizzate} / {autoclave.valvole_totali} valvole
                                </div>
                              </div>
                            </div>
                          </CardHeader>
                          
                          <CardContent className="flex-1">
                            <Droppable droppableId={`autoclave-${autoclaveIndex}`}>
                              {(provided: DroppableProvided, snapshot: DroppableStateSnapshot) => (
                                <div
                                  ref={provided.innerRef}
                                  {...provided.droppableProps}
                                  className={`min-h-[300px] p-4 border-2 border-dashed rounded-lg transition-colors ${
                                    snapshot.isDraggingOver 
                                      ? 'border-primary bg-primary/5' 
                                      : 'border-muted-foreground/25'
                                  }`}
                                >
                                  {autoclave.odl_inclusi.length === 0 ? (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                      <div className="text-center">
                                        <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                        <p>Nessun ODL assegnato</p>
                                        <p className="text-xs">Trascina qui gli ODL dalla sezione esclusi</p>
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="space-y-2">
                                      {autoclave.odl_inclusi.map((odl, odlIndex) => (
                                        <Draggable
                                          key={`odl-${odl.id}`}
                                          draggableId={`odl-${odl.id}`}
                                          index={odlIndex}
                                        >
                                          {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => (
                                            <div
                                              ref={provided.innerRef}
                                              {...provided.draggableProps}
                                              {...provided.dragHandleProps}
                                              className={`p-3 border rounded-lg bg-white shadow-sm transition-all ${
                                                snapshot.isDragging ? 'shadow-lg rotate-2' : 'hover:shadow-md'
                                              }`}
                                              style={{
                                                ...provided.draggableProps.style,
                                                borderColor: odl.color
                                              }}
                                            >
                                              <div className="flex items-center justify-between">
                                                <div className="flex-1">
                                                  <div className="font-medium text-sm">
                                                    ODL #{odl.id} - {odl.part_number}
                                                  </div>
                                                  <div className="text-xs text-muted-foreground">
                                                    {odl.descrizione}
                                                  </div>
                                                  <div className="flex gap-2 mt-1">
                                                    <Badge variant="outline" className="text-xs">
                                                      {odl.area_cm2} cm²
                                                    </Badge>
                                                    <Badge variant="outline" className="text-xs">
                                                      {odl.num_valvole} valvole
                                                    </Badge>
                                                    <Badge 
                                                      variant={odl.priorita <= 2 ? "destructive" : odl.priorita <= 4 ? "default" : "secondary"} 
                                                      className="text-xs"
                                                    >
                                                      P{odl.priorita}
                                                    </Badge>
                                                  </div>
                                                </div>
                                                
                                                <div className="flex items-center gap-1 ml-2">
                                                  <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleExcludeODL(autoclaveIndex, odlIndex)}
                                                    className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                                                  >
                                                    <Trash2 className="h-3 w-3" />
                                                  </Button>
                                                  <Move className="h-4 w-4 text-muted-foreground cursor-grab" />
                                                </div>
                                              </div>
                                            </div>
                                          )}
                                        </Draggable>
                                      ))}
                                    </div>
                                  )}
                                  {provided.placeholder}
                                </div>
                              )}
                            </Droppable>
                          </CardContent>
                        </Card>
                      </TabsContent>
                    ))}

                    {/* Tab ODL Esclusi */}
                    <TabsContent value="excluded" className="h-full mt-4">
                      <Card className="h-full">
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            <XCircle className="h-5 w-5 text-red-500" />
                            ODL Esclusi ({odlEsclusi.length})
                          </CardTitle>
                        </CardHeader>
                        
                        <CardContent>
                          <Droppable droppableId="excluded">
                            {(provided: DroppableProvided, snapshot: DroppableStateSnapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.droppableProps}
                                className={`min-h-[300px] p-4 border-2 border-dashed rounded-lg transition-colors ${
                                  snapshot.isDraggingOver 
                                    ? 'border-red-400 bg-red-50' 
                                    : 'border-red-200'
                                }`}
                              >
                                {odlEsclusi.length === 0 ? (
                                  <div className="flex items-center justify-center h-full text-muted-foreground">
                                    <div className="text-center">
                                      <CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-50 text-green-500" />
                                      <p>Tutti gli ODL sono stati assegnati!</p>
                                      <p className="text-xs">Nessun ODL escluso dal nesting</p>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="space-y-2">
                                    {odlEsclusi.map((odl, index) => (
                                      <div
                                        key={odl.id}
                                        className="p-3 border border-red-200 rounded-lg bg-red-50"
                                      >
                                        <div className="flex items-center justify-between">
                                          <div className="flex-1">
                                            <div className="font-medium text-sm">
                                              ODL #{odl.id} - {odl.part_number}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                              {odl.descrizione}
                                            </div>
                                            <div className="flex gap-2 mt-1">
                                              <Badge variant="outline" className="text-xs">
                                                {odl.num_valvole} valvole
                                              </Badge>
                                              <Badge 
                                                variant={odl.priorita <= 2 ? "destructive" : odl.priorita <= 4 ? "default" : "secondary"} 
                                                className="text-xs"
                                              >
                                                P{odl.priorita}
                                              </Badge>
                                            </div>
                                            <div className="text-xs text-red-600 mt-1 font-medium">
                                              Motivo: {odl.motivo}
                                            </div>
                                          </div>
                                          
                                          <div className="flex flex-col gap-1 ml-2">
                                            {autoclavi.map((autoclave, autoclaveIndex) => (
                                              <Button
                                                key={autoclave.id}
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleRestoreODL(index, autoclaveIndex)}
                                                className="h-6 text-xs"
                                              >
                                                → {autoclave.nome}
                                              </Button>
                                            ))}
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                )}
                                {provided.placeholder}
                              </div>
                            )}
                          </Droppable>
                        </CardContent>
                      </Card>
                    </TabsContent>
                  </div>
                </Tabs>
              </div>
            </DragDropContext>
          </div>
        )}

        <DialogFooter className="flex-shrink-0 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleRegenerateNesting}
              disabled={isRegenerating}
            >
              {isRegenerating ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Rigenera Nesting
            </Button>
            
            {isModified && (
              <Button
                variant="outline"
                onClick={handleSaveModifications}
                disabled={isSaving}
              >
                {isSaving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Salva Modifiche
              </Button>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onClose}>
              Annulla
            </Button>
            <Button 
              onClick={handleApproveNesting}
              disabled={!previewData.success}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approva Nesting
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 