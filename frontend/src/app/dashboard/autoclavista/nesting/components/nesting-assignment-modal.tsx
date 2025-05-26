'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { 
  Loader2, 
  CheckCircle, 
  AlertTriangle,
  Settings,
  Package,
  Gauge,
  Clock,
  User,
  FileText
} from 'lucide-react'
import { nestingApi, autoclaveApi, type NestingResponse, type Autoclave, type NestingAssignmentRequest } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'

interface NestingAssignmentModalProps {
  isOpen: boolean
  onClose: () => void
  onAssignmentComplete: () => void
}

export default function NestingAssignmentModal({
  isOpen,
  onClose,
  onAssignmentComplete
}: NestingAssignmentModalProps) {
  const { toast } = useToast()
  
  // Stati per i dati
  const [availableNestings, setAvailableNestings] = useState<NestingResponse[]>([])
  const [availableAutoclavi, setAvailableAutoclavi] = useState<Autoclave[]>([])
  const [selectedNesting, setSelectedNesting] = useState<number | null>(null)
  const [selectedAutoclave, setSelectedAutoclave] = useState<number | null>(null)
  const [note, setNote] = useState('')
  
  // Stati per il caricamento
  const [isLoading, setIsLoading] = useState(true)
  const [isAssigning, setIsAssigning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Carica i dati quando il modal si apre
  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  const loadData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Carica nesting disponibili e autoclavi disponibili in parallelo
      const [nestingsData, autoclaviData] = await Promise.all([
        nestingApi.getAvailableForAssignment(),
        autoclaveApi.getAvailable()
      ])
      
      setAvailableNestings(nestingsData)
      setAvailableAutoclavi(autoclaviData)
      
      // Reset selezioni
      setSelectedNesting(null)
      setSelectedAutoclave(null)
      setNote('')
      
    } catch (err: any) {
      console.error('Errore nel caricamento dei dati:', err)
      setError(
        err.message || 'Errore di connessione – verifica che il backend sia attivo e l\'endpoint esista'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleAssignment = async () => {
    if (!selectedNesting || !selectedAutoclave) {
      toast({
        title: "Selezione incompleta",
        description: "Seleziona sia un nesting che un'autoclave",
        variant: "destructive"
      })
      return
    }

    try {
      setIsAssigning(true)
      
      const assignmentRequest: NestingAssignmentRequest = {
        nesting_id: selectedNesting,
        autoclave_id: selectedAutoclave,
        note: note.trim() || undefined
      }
      
      await nestingApi.assignToAutoclave(assignmentRequest)
      
      toast({
        title: "Assegnazione completata",
        description: "Il nesting è stato assegnato con successo all'autoclave",
        variant: "default"
      })
      
      onAssignmentComplete()
      onClose()
      
    } catch (err: any) {
      console.error('Errore nell\'assegnazione:', err)
      
      let errorMessage = 'Errore durante l\'assegnazione'
      
      if (err.response?.status === 404) {
        errorMessage = 'Nesting o autoclave non trovati'
      } else if (err.response?.status === 400) {
        errorMessage = err.response.data?.detail || 'Richiesta non valida'
      } else if (err.response?.status >= 500) {
        errorMessage = 'Errore interno del server. Riprova più tardi.'
      } else if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        errorMessage = 'Impossibile connettersi al server. Verifica che il backend sia in esecuzione.'
      }
      
      toast({
        title: "Errore nell'assegnazione",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setIsAssigning(false)
    }
  }

  const selectedNestingData = availableNestings.find(n => n.id === selectedNesting)
  const selectedAutoclaveData = availableAutoclavi.find(a => a.id === selectedAutoclave)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Assegna Nesting ad Autoclave
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
              <p className="text-muted-foreground">Caricamento dati...</p>
            </div>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button 
                variant="outline" 
                size="sm" 
                className="ml-2" 
                onClick={loadData}
              >
                Riprova
              </Button>
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-6">
            {/* Statistiche */}
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Package className="h-4 w-4 text-blue-500" />
                    <div>
                      <div className="text-2xl font-bold">{availableNestings.length}</div>
                      <div className="text-xs text-muted-foreground">Nesting Disponibili</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Settings className="h-4 w-4 text-green-500" />
                    <div>
                      <div className="text-2xl font-bold">{availableAutoclavi.length}</div>
                      <div className="text-xs text-muted-foreground">Autoclavi Disponibili</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Selezione Nesting */}
            <div className="space-y-3">
              <Label htmlFor="nesting-select">Seleziona Nesting Confermato</Label>
              <Select value={selectedNesting?.toString() || ""} onValueChange={(value) => setSelectedNesting(parseInt(value))}>
                <SelectTrigger id="nesting-select">
                  <SelectValue placeholder="Scegli un nesting..." />
                </SelectTrigger>
                <SelectContent>
                  {availableNestings.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground">
                      Nessun nesting disponibile
                    </div>
                  ) : (
                    availableNestings
                      .filter((nesting) => nesting?.id && nesting?.autoclave?.nome)
                      .map((nesting) => (
                        <SelectItem key={nesting.id} value={nesting.id.toString()}>
                          <div className="flex items-center justify-between w-full">
                            <span>Nesting #{nesting.id} - {nesting.autoclave.nome}</span>
                            <div className="flex items-center gap-2 ml-2">
                              <Badge variant="secondary">{nesting.odl_list.length} ODL</Badge>
                              <Badge variant="outline">{Math.round((nesting.area_utilizzata / nesting.area_totale) * 100)}% area</Badge>
                            </div>
                          </div>
                        </SelectItem>
                      ))
                  )}
                </SelectContent>
              </Select>
              
              {availableNestings.length === 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Nessun nesting confermato disponibile per l'assegnazione.
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Dettagli Nesting Selezionato */}
            {selectedNestingData && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Dettagli Nesting Selezionato</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium">Autoclave Originale</div>
                      <div className="text-sm text-muted-foreground">{selectedNestingData.autoclave.nome}</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium">Data Creazione</div>
                      <div className="text-sm text-muted-foreground">{formatDateIT(selectedNestingData.created_at)}</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Utilizzo Area</span>
                        <Badge variant="secondary">
                          {Math.round((selectedNestingData.area_utilizzata / selectedNestingData.area_totale) * 100)}%
                        </Badge>
                      </div>
                      <Progress value={(selectedNestingData.area_utilizzata / selectedNestingData.area_totale) * 100} className="h-2" />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Utilizzo Valvole</span>
                        <Badge variant="secondary">
                          {Math.round((selectedNestingData.valvole_utilizzate / selectedNestingData.valvole_totali) * 100)}%
                        </Badge>
                      </div>
                      <Progress value={(selectedNestingData.valvole_utilizzate / selectedNestingData.valvole_totali) * 100} className="h-2" />
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium mb-2">ODL Inclusi ({selectedNestingData.odl_list.length})</div>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {selectedNestingData.odl_list.map((odl) => (
                        <div key={odl.id} className="flex items-center justify-between text-xs p-2 bg-muted rounded">
                          <span>ODL #{odl.id} - {odl.parte.part_number}</span>
                          <Badge variant="outline" className="text-xs">P{odl.priorita}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Selezione Autoclave */}
            <div className="space-y-3">
              <Label htmlFor="autoclave-select">Seleziona Autoclave Disponibile</Label>
              <Select value={selectedAutoclave?.toString() || ""} onValueChange={(value) => setSelectedAutoclave(parseInt(value))}>
                <SelectTrigger id="autoclave-select">
                  <SelectValue placeholder="Scegli un'autoclave..." />
                </SelectTrigger>
                <SelectContent>
                  {availableAutoclavi.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground">
                      Nessuna autoclave disponibile
                    </div>
                  ) : (
                    availableAutoclavi
                      .filter((autoclave) => autoclave?.id && autoclave?.nome)
                      .map((autoclave) => (
                        <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                          <div className="flex items-center justify-between w-full">
                            <span>{autoclave.nome} ({autoclave.codice})</span>
                            <div className="flex items-center gap-2 ml-2">
                              <Badge variant="outline">{autoclave.num_linee_vuoto} valvole</Badge>
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                {autoclave.stato}
                              </Badge>
                            </div>
                          </div>
                        </SelectItem>
                      ))
                  )}
                </SelectContent>
              </Select>
              
              {availableAutoclavi.length === 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Nessuna autoclave disponibile per l'assegnazione.
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Dettagli Autoclave Selezionata */}
            {selectedAutoclaveData && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Dettagli Autoclave Selezionata</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="font-medium">Dimensioni</div>
                      <div className="text-muted-foreground">
                        {selectedAutoclaveData.lunghezza} × {selectedAutoclaveData.larghezza_piano} mm
                      </div>
                    </div>
                    <div>
                      <div className="font-medium">Valvole</div>
                      <div className="text-muted-foreground">{selectedAutoclaveData.num_linee_vuoto} linee</div>
                    </div>
                    <div>
                      <div className="font-medium">Temperatura Max</div>
                      <div className="text-muted-foreground">{selectedAutoclaveData.temperatura_max}°C</div>
                    </div>
                  </div>
                  
                  {selectedAutoclaveData.note && (
                    <div>
                      <div className="text-sm font-medium">Note</div>
                      <div className="text-sm text-muted-foreground">{selectedAutoclaveData.note}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Note Assegnazione */}
            <div className="space-y-3">
              <Label htmlFor="assignment-note">Note Assegnazione (opzionale)</Label>
              <Textarea
                id="assignment-note"
                placeholder="Aggiungi note per l'assegnazione..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
              />
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isAssigning}>
            Annulla
          </Button>
          <Button 
            onClick={handleAssignment} 
            disabled={!selectedNesting || !selectedAutoclave || isAssigning || isLoading}
            className="flex items-center gap-2"
          >
            {isAssigning ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Assegnazione in corso...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4" />
                Assegna Nesting
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 