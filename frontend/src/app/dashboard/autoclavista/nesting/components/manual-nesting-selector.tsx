'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
// import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  Loader2, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Package, 
  Plus,
  Search,
  Filter,
  X,
  Info,
  ChevronDown,
  ChevronUp,
  Bug,
  AlertCircle,
  Clock,
  Wrench
} from 'lucide-react'
import { odlApi, nestingApi, type ODLResponse, type ManualNestingRequest, type ManualNestingResponse } from '@/lib/api'

interface ManualNestingSelectorProps {
  onNestingCreated?: (result: ManualNestingResponse) => void
  onClose?: () => void
}

interface ErrorDetails {
  timestamp: string
  error: any
  request?: ManualNestingRequest
  response?: any
  userAction: string
}

export default function ManualNestingSelector({ onNestingCreated, onClose }: ManualNestingSelectorProps) {
  // Stati per i dati
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [selectedOdlIds, setSelectedOdlIds] = useState<number[]>([])
  const [note, setNote] = useState('')
  
  // Stati per UI e caricamento
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Stati per filtri e ricerca
  const [searchTerm, setSearchTerm] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<number | null>(null)
  const [filteredOdl, setFilteredOdl] = useState<ODLResponse[]>([])
  
  // Stati per dialog di conferma
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false)
  
  // Stati per debug avanzato
  const [debugMode, setDebugMode] = useState(false)
  const [errorHistory, setErrorHistory] = useState<ErrorDetails[]>([])
  const [lastRequest, setLastRequest] = useState<ManualNestingRequest | null>(null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  
  const { toast } = useToast()

  // Funzione per loggare errori dettagliati
  const logError = (error: any, userAction: string, request?: ManualNestingRequest, response?: any) => {
    const errorDetail: ErrorDetails = {
      timestamp: new Date().toISOString(),
      error,
      request,
      response,
      userAction
    }
    
    setErrorHistory(prev => [errorDetail, ...prev.slice(0, 9)]) // Mantieni solo gli ultimi 10 errori
    
    // Log dettagliato in console per sviluppatori
    console.group(`🔍 [${userAction}] Errore dettagliato - ${errorDetail.timestamp}`)
    console.error('Error object:', error)
    if (request) console.log('Request data:', request)
    if (response) console.log('Response data:', response)
    console.log('Error type:', typeof error)
    console.log('Error constructor:', error?.constructor?.name)
    if (error?.response) {
      console.log('HTTP Status:', error.response.status)
      console.log('HTTP Headers:', error.response.headers)
      console.log('Response Data:', error.response.data)
    }
    console.groupEnd()
  }

  // Validazione avanzata lato client
  const validateSelectionAdvanced = (): string[] => {
    const errors: string[] = []
    
    if (selectedOdlIds.length === 0) {
      errors.push('Deve essere selezionato almeno un ODL per creare il nesting')
    }
    
    if (selectedOdlIds.length > 50) {
      errors.push('Non è possibile selezionare più di 50 ODL per volta')
    }
    
    // Verifica che tutti gli ODL selezionati esistano ancora nella lista
    const missingOdl = selectedOdlIds.filter(id => !odlList.find(odl => odl.id === id))
    if (missingOdl.length > 0) {
      errors.push(`ODL non più disponibili: ${missingOdl.join(', ')}`)
    }
    
    // Verifica stato degli ODL
    const selectedOdl = odlList.filter(odl => selectedOdlIds.includes(odl.id))
    const invalidStatusOdl = selectedOdl.filter(odl => odl.status !== 'Attesa Cura')
    if (invalidStatusOdl.length > 0) {
      errors.push(`ODL non in stato "Attesa Cura": ${invalidStatusOdl.map(odl => `#${odl.id} (${odl.status})`).join(', ')}`)
    }
    
    // Calcola totale valvole e verifica limiti ragionevoli
    const totalValvole = selectedOdl.reduce((sum, odl) => sum + odl.parte.num_valvole_richieste, 0)
    if (totalValvole > 100) {
      errors.push(`Troppe valvole richieste (${totalValvole}). Considera di ridurre la selezione.`)
    }
    
    return errors
  }

  // Carica gli ODL in attesa di nesting
  const fetchOdlPending = async () => {
    try {
      setIsLoading(true)
      setError(null)
      setValidationErrors([])
      
      console.log('🔄 Caricamento ODL in attesa di nesting...')
      const data = await odlApi.getPendingNesting()
      
      console.log('✅ ODL caricati:', data.length)
      setOdlList(data)
      
      if (data.length === 0) {
        setError('Nessun ODL in attesa di nesting disponibile')
      }
      
      // Rimuovi dalla selezione eventuali ODL che non sono più disponibili
      setSelectedOdlIds(prev => prev.filter(id => data.find(odl => odl.id === id)))
      
    } catch (err: any) {
      console.error('❌ Errore nel caricamento ODL:', err)
      logError(err, 'Caricamento ODL')
      
      // Gestione errori dettagliata
      let errorMessage = 'Errore nel caricamento degli ODL'
      
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        errorMessage = 'Impossibile connettersi al server. Verifica che il backend sia in esecuzione su http://localhost:8000'
      } else if (err.response?.status === 404) {
        errorMessage = 'Endpoint non trovato. Verifica che l\'API /odl/pending-nesting sia disponibile.'
      } else if (err.response?.status >= 500) {
        errorMessage = 'Errore interno del server. Controlla i log del backend.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      
      toast({
        variant: 'destructive',
        title: 'Errore di caricamento',
        description: errorMessage,
      })
      
    } finally {
      setIsLoading(false)
    }
  }

  // Effetto per caricare i dati iniziali
  useEffect(() => {
    fetchOdlPending()
  }, [])

  // Effetto per filtrare gli ODL
  useEffect(() => {
    let filtered = [...odlList]

    // Filtro per termine di ricerca
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(odl => 
        odl.id.toString().includes(term) ||
        odl.parte.part_number.toLowerCase().includes(term) ||
        odl.parte.descrizione_breve.toLowerCase().includes(term) ||
        odl.tool.part_number_tool.toLowerCase().includes(term)
      )
    }

    // Filtro per priorità
    if (priorityFilter !== null) {
      filtered = filtered.filter(odl => odl.priorita === priorityFilter)
    }

    // Ordina per priorità decrescente, poi per ID
    filtered.sort((a, b) => {
      if (a.priorita !== b.priorita) {
        return b.priorita - a.priorita
      }
      return a.id - b.id
    })

    setFilteredOdl(filtered)
    
    // Aggiorna validazione quando cambiano i filtri
    const errors = validateSelectionAdvanced()
    setValidationErrors(errors)
  }, [odlList, searchTerm, priorityFilter, selectedOdlIds])

  // Gestione selezione ODL
  const handleOdlSelection = (odlId: number, selected: boolean) => {
    if (selected) {
      setSelectedOdlIds(prev => [...prev, odlId])
    } else {
      setSelectedOdlIds(prev => prev.filter(id => id !== odlId))
    }
  }

  // Selezione/deselezione tutti
  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedOdlIds(filteredOdl.map(odl => odl.id))
    } else {
      setSelectedOdlIds([])
    }
  }

  // Validazione prima della creazione (legacy per compatibilità)
  const validateSelection = (): string | null => {
    const errors = validateSelectionAdvanced()
    return errors.length > 0 ? errors[0] : null
  }

  // Crea il nesting manuale
  const handleCreateNesting = async () => {
    try {
      // Validazione lato client avanzata
      const validationErrors = validateSelectionAdvanced()
      if (validationErrors.length > 0) {
        setValidationErrors(validationErrors)
        toast({
          variant: 'destructive',
          title: 'Selezione non valida',
          description: validationErrors[0],
        })
        return
      }

      setIsCreating(true)
      setError(null)
      setValidationErrors([])
      
      const request: ManualNestingRequest = {
        odl_ids: selectedOdlIds,
        note: note.trim() || undefined
      }
      
      setLastRequest(request)
      
      console.log('🔄 Creazione nesting manuale...', request)

      const result = await nestingApi.generateManual(request)
      
      console.log('✅ Nesting manuale creato:', result)

      // Mostra messaggio di successo dettagliato
      const successMessage = `${result.message}\n• Autoclavi utilizzate: ${result.autoclavi.length}\n• ODL pianificati: ${result.odl_pianificati.length}\n• ODL esclusi: ${result.odl_non_pianificabili.length}`
      
      toast({
        title: 'Nesting creato con successo!',
        description: result.message,
      })

      // Callback per notificare il componente padre
      if (onNestingCreated) {
        onNestingCreated(result)
      }

      // Reset del form
      setSelectedOdlIds([])
      setNote('')
      setConfirmDialogOpen(false)
      setLastRequest(null)

      // Ricarica la lista ODL
      fetchOdlPending()

    } catch (err: any) {
      console.error('❌ Errore nella creazione del nesting:', err)
      logError(err, 'Creazione Nesting Manuale', lastRequest || undefined, err.response)
      
      // Gestione errori dettagliata con codici specifici
      let errorTitle = 'Errore nella creazione del nesting'
      let errorMessage = 'Si è verificato un errore imprevisto'
      
      if (err.response?.status === 422) {
        // Errori di validazione
        errorTitle = 'Dati non validi'
        errorMessage = err.response.data?.detail || 'I dati forniti non sono validi'
        
        // Aggiungi suggerimenti specifici per errori 422
        if (errorMessage.includes('già assegnato')) {
          errorMessage += '\n\nSuggerimento: Ricarica la lista ODL per vedere gli aggiornamenti più recenti.'
        } else if (errorMessage.includes('Attesa Cura')) {
          errorMessage += '\n\nSuggerimento: Verifica che tutti gli ODL selezionati siano ancora in stato "Attesa Cura".'
        }
        
      } else if (err.response?.status === 400) {
        // Errori di business logic
        errorTitle = 'Operazione non consentita'
        errorMessage = err.response.data?.detail || 'Non è possibile creare il nesting con i parametri specificati'
        
      } else if (err.response?.status >= 500) {
        // Errori del server
        errorTitle = 'Errore del server'
        errorMessage = 'Errore interno del server. Controlla i log del backend e riprova.'
        
      } else if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        // Errori di connessione
        errorTitle = 'Errore di connessione'
        errorMessage = 'Impossibile connettersi al server. Verifica che il backend sia in esecuzione.'
        
      } else if (err.response?.data?.detail) {
        // Altri errori con dettaglio
        errorMessage = err.response.data.detail
        
      } else if (err.message) {
        // Errori generici
        errorMessage = err.message
      }

      setError(errorMessage)
      
      toast({
        variant: 'destructive',
        title: errorTitle,
        description: errorMessage,
      })
      
    } finally {
      setIsCreating(false)
    }
  }

  // Ottieni le priorità uniche per il filtro
  const uniquePriorities = Array.from(new Set(odlList.map(odl => odl.priorita))).sort((a, b) => b - a)

  // Calcola statistiche di selezione
  const selectedOdl = odlList.filter(odl => selectedOdlIds.includes(odl.id))
  const totalValvole = selectedOdl.reduce((sum, odl) => sum + odl.parte.num_valvole_richieste, 0)

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            <CardTitle>Selezione ODL per Nesting Manuale</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDebugMode(!debugMode)}
              className="text-xs"
            >
              <Bug className="h-4 w-4 mr-1" />
              Debug {debugMode ? 'ON' : 'OFF'}
            </Button>
          </div>
        </div>
        <CardDescription>
          Seleziona gli ODL da includere nel nesting manuale. Tutti gli ODL devono essere in stato "Attesa Cura".
          {debugMode && (
            <div className="mt-2 text-xs text-muted-foreground">
              🔧 Modalità debug attiva - Informazioni dettagliate disponibili
            </div>
          )}
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Debug Panel */}
        {debugMode && (
          <div className="border rounded-lg p-4 bg-muted/50 space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <Bug className="h-4 w-4" />
              <strong className="text-sm">Informazioni Debug</strong>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>ODL Totali:</strong> {odlList.length}
              </div>
              <div>
                <strong>ODL Filtrati:</strong> {filteredOdl.length}
              </div>
              <div>
                <strong>ODL Selezionati:</strong> {selectedOdlIds.length}
              </div>
              <div>
                <strong>Valvole Totali:</strong> {totalValvole}
              </div>
            </div>
            
            {lastRequest && (
              <div>
                <strong>Ultima Richiesta:</strong>
                <pre className="text-xs bg-background p-2 rounded mt-1 overflow-auto">
                  {JSON.stringify(lastRequest, null, 2)}
                </pre>
              </div>
            )}
            
            {errorHistory.length > 0 && (
              <div>
                <strong>Cronologia Errori ({errorHistory.length}):</strong>
                <div className="max-h-32 overflow-auto mt-1">
                  {errorHistory.slice(0, 3).map((error, index) => (
                    <div key={index} className="text-xs bg-destructive/10 p-2 rounded mb-1">
                      <div className="font-medium">{error.userAction}</div>
                      <div className="text-muted-foreground">{error.timestamp}</div>
                      <div className="truncate">{error.error?.message || 'Errore sconosciuto'}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Controlli di ricerca e filtri */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Cerca per ID, Part Number, descrizione..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          <div className="flex gap-2">
            <select
              value={priorityFilter?.toString() || ''}
              onChange={(e) => setPriorityFilter(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="">Tutte le priorità</option>
              {uniquePriorities.map(priority => (
                <option key={priority} value={priority}>
                  Priorità {priority}
                </option>
              ))}
            </select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={fetchOdlPending}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Statistiche di selezione */}
        {selectedOdlIds.length > 0 && (
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              <strong>{selectedOdlIds.length} ODL selezionati</strong> - 
              Totale valvole richieste: <strong>{totalValvole}</strong>
              {totalValvole > 50 && (
                <span className="text-amber-600 ml-2">⚠️ Molte valvole richieste</span>
              )}
            </AlertDescription>
          </Alert>
        )}

        {/* Errori di validazione */}
        {validationErrors.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-1">
                <strong>Problemi di validazione:</strong>
                {validationErrors.map((error, index) => (
                  <div key={index} className="text-sm">• {error}</div>
                ))}
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Gestione errori */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium mb-1">Errore di sistema</div>
                <div className="text-sm whitespace-pre-line">{error}</div>
                {debugMode && errorHistory.length > 0 && (
                  <div className="mt-2 text-xs">
                    <strong>Ultimo errore:</strong> {errorHistory[0]?.timestamp}
                  </div>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setError(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Tabella ODL */}
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Caricamento ODL...</span>
          </div>
        ) : filteredOdl.length === 0 ? (
          <div className="text-center py-8">
            <Package className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              {odlList.length === 0 ? 'Nessun ODL in attesa di nesting' : 'Nessun ODL corrisponde ai filtri'}
            </p>
            {odlList.length === 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={fetchOdlPending}
                className="mt-2"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Ricarica
              </Button>
            )}
          </div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedOdlIds.length === filteredOdl.length && filteredOdl.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead>ODL</TableHead>
                  <TableHead>Parte</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Priorità</TableHead>
                  <TableHead>Valvole</TableHead>
                  <TableHead>Creato</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOdl.map((odl) => {
                  const isSelected = selectedOdlIds.includes(odl.id)
                  const isInvalidStatus = odl.status !== 'Attesa Cura'
                  
                  return (
                    <TableRow 
                      key={odl.id}
                      className={`${isSelected ? 'bg-muted/50' : ''} ${isInvalidStatus ? 'opacity-50' : ''}`}
                    >
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={(checked) => handleOdlSelection(odl.id, checked as boolean)}
                          disabled={isInvalidStatus}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">#{odl.id}</div>
                        <div className="text-xs text-muted-foreground flex items-center gap-1">
                          {odl.status}
                          {isInvalidStatus && <AlertCircle className="h-3 w-3 text-amber-500" />}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{odl.parte.part_number}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {odl.parte.descrizione_breve}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{odl.tool.part_number_tool}</div>
                        {odl.tool.descrizione && (
                          <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {odl.tool.descrizione}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={odl.priorita >= 3 ? "default" : "secondary"}>
                          P{odl.priorita}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">{odl.parte.num_valvole_richieste}</span>
                      </TableCell>
                      <TableCell>
                        <div className="text-xs text-muted-foreground">
                          {new Date(odl.created_at).toLocaleDateString('it-IT')}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Controlli inferiori */}
        <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t">
          <div className="flex-1">
            <Label htmlFor="note" className="text-sm font-medium">
              Note (opzionale)
            </Label>
            <Textarea
              id="note"
              placeholder="Aggiungi note per questo nesting manuale..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="mt-1"
              rows={3}
            />
          </div>
          
          <div className="flex flex-col gap-2 sm:w-auto">
            <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  disabled={selectedOdlIds.length === 0 || isCreating || validationErrors.length > 0}
                  className="w-full sm:w-auto"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Crea Nesting ({selectedOdlIds.length})
                </Button>
              </DialogTrigger>
              
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Conferma Creazione Nesting</DialogTitle>
                  <DialogDescription>
                    Stai per creare un nesting manuale con {selectedOdlIds.length} ODL selezionati.
                    Questa operazione cambierà lo stato degli ODL da "Attesa Cura" a "Cura".
                  </DialogDescription>
                </DialogHeader>
                
                <div className="py-4">
                  <div className="space-y-2">
                    <div className="text-sm">
                      <strong>ODL selezionati:</strong> {selectedOdlIds.length}
                    </div>
                    <div className="text-sm">
                      <strong>Totale valvole:</strong> {totalValvole}
                    </div>
                    {note && (
                      <div className="text-sm">
                        <strong>Note:</strong> {note}
                      </div>
                    )}
                    {debugMode && lastRequest && (
                      <div className="text-xs">
                        <strong>Richiesta:</strong>
                        <pre className="bg-muted p-2 rounded mt-1 text-xs overflow-auto">
                          {JSON.stringify(lastRequest, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
                
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setConfirmDialogOpen(false)}
                    disabled={isCreating}
                  >
                    Annulla
                  </Button>
                  <Button
                    onClick={handleCreateNesting}
                    disabled={isCreating}
                  >
                    {isCreating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creazione...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Conferma
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            
            {onClose && (
              <Button variant="outline" onClick={onClose} className="w-full sm:w-auto">
                Chiudi
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 