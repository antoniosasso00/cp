'use client'

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { 
  RefreshCw, 
  Eye, 
  Edit, 
  Trash2, 
  Play, 
  CheckCircle, 
  RotateCcw, 
  Download,
  FileText,
  Loader2
} from 'lucide-react'
import { NestingResponse, nestingApi, NestingLoadRequest } from '@/lib/api'

interface NestingTableProps {
  data: NestingResponse[]
  isLoading: boolean
  onRefresh: () => void
}

// Funzione per ottenere il colore del badge in base allo stato
const getStatoBadgeVariant = (stato: string) => {
  switch (stato.toLowerCase()) {
    case 'creato':
      return 'secondary'
    case 'bozza':
      return 'outline'
    case 'in sospeso':
      return 'default'
    case 'confermato':
      return 'default'
    case 'caricato':
    case 'cura':
      return 'destructive'
    case 'completato':
    case 'finito':
      return 'default'
    case 'errore':
      return 'destructive'
    default:
      return 'outline'
  }
}

// Funzione per formattare la data in formato italiano
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

export function NestingTable({ data, isLoading, onRefresh }: NestingTableProps) {
  const [selectedNesting, setSelectedNesting] = useState<string | null>(null)
  const [loadDialogOpen, setLoadDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [nestingToLoad, setNestingToLoad] = useState<NestingResponse | null>(null)
  const [nestingToDelete, setNestingToDelete] = useState<NestingResponse | null>(null)
  const [loadNotes, setLoadNotes] = useState('')
  const [loadingActions, setLoadingActions] = useState<Record<string, string>>({})
  const { toast } = useToast()

  // Funzione per gestire azioni con loading state
  const handleActionWithLoading = async (
    nestingId: string, 
    actionType: string, 
    actionFunction: () => Promise<void>
  ) => {
    try {
      setLoadingActions(prev => ({ ...prev, [nestingId]: actionType }))
      await actionFunction()
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Errore",
        description: error.message || `Errore durante ${actionType}`
      })
    } finally {
      setLoadingActions(prev => {
        const newState = { ...prev }
        delete newState[nestingId]
        return newState
      })
    }
  }

  // Azione: Conferma nesting (Bozza -> In sospeso)
  const handleConfirmNesting = async (nesting: NestingResponse) => {
    await handleActionWithLoading(nesting.id, 'conferma', async () => {
      // ✅ COLLEGATO A: POST /nesting/{id}/confirm
      await nestingApi.confirm(parseInt(nesting.id), {
        confermato_da_ruolo: 'operatore',
        note_conferma: 'Confermato dalla tabella nesting'
      })
      
      toast({
        variant: "default",
        title: "Nesting Confermato",
        description: `Il nesting ${nesting.id.substring(0, 8)}... è stato confermato e messo in sospeso.`
      })
      
      onRefresh()
    })
  }

  // ✅ NUOVO: Azione Rigenera nesting (Bozza)
  const handleRegenerateNesting = async (nesting: NestingResponse) => {
    await handleActionWithLoading(nesting.id, 'rigenera', async () => {
      // 🔗 COLLEGATO A: POST /nesting/{id}/regenerate
      await nestingApi.regenerate(parseInt(nesting.id), true)
      
      toast({
        variant: "default",
        title: "Nesting Rigenerato",
        description: `Il nesting ${nesting.id.substring(0, 8)}... è stato rigenerato con successo.`
      })
      
      onRefresh()
    })
  }

  // ✅ NUOVO: Azione Elimina nesting con conferma modale
  const handleDeleteNesting = async (nesting: NestingResponse) => {
    await handleActionWithLoading(nesting.id, 'elimina', async () => {
      // 🔗 COLLEGATO A: DELETE /nesting/{id}
      await nestingApi.delete(parseInt(nesting.id))
      
      toast({
        variant: "default",
        title: "Nesting Eliminato",
        description: `Il nesting ${nesting.id.substring(0, 8)}... è stato eliminato con successo.`
      })
      
      setDeleteDialogOpen(false)
      setNestingToDelete(null)
      onRefresh()
    })
  }

  // Azione: Carica nesting (In sospeso -> Cura)
  const handleLoadNesting = async (nesting: NestingResponse) => {
    try {
      setLoadingActions(prev => ({ ...prev, [nesting.id]: 'carica' }))
      
      const loadData: NestingLoadRequest = {
        caricato_da_ruolo: 'curing',
        note_caricamento: loadNotes.trim() || undefined
      }
      
      // ✅ COLLEGATO A: POST /nesting/{id}/load
      await nestingApi.load(parseInt(nesting.id), loadData)
      
      toast({
        variant: "default",
        title: "Nesting Caricato",
        description: `Il nesting ${nesting.id.substring(0, 8)}... è stato caricato nell'autoclave.`
      })
      
      setLoadDialogOpen(false)
      setLoadNotes('')
      setNestingToLoad(null)
      onRefresh()
      
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Errore Caricamento",
        description: error.message || 'Errore nel caricamento del nesting'
      })
    } finally {
      setLoadingActions(prev => {
        const newState = { ...prev }
        delete newState[nesting.id]
        return newState
      })
    }
  }

  // Azione: Completa nesting (Cura -> Finito)
  const handleCompleteNesting = async (nesting: NestingResponse) => {
    await handleActionWithLoading(nesting.id, 'completa', async () => {
      // ✅ COLLEGATO A: PUT /nesting/{id}/status (usando updateStatus)
      await nestingApi.updateStatus(parseInt(nesting.id), {
        stato: 'finito',
        note: 'Completato dalla tabella nesting'
      })
      
      toast({
        variant: "default",
        title: "Nesting Completato",
        description: `Il nesting ${nesting.id.substring(0, 8)}... è stato completato con successo.`
      })
      
      onRefresh()
    })
  }

  // Azione: Scarica report (Finito)
  const handleDownloadReport = async (nesting: NestingResponse) => {
    await handleActionWithLoading(nesting.id, 'report', async () => {
      try {
        // ✅ COLLEGATO A: POST /nesting/{id}/generate-report + GET /reports/nesting/{id}/download
        const reportInfo = await nestingApi.generateReport(parseInt(nesting.id))
        
        // Poi scarica il report
        const blob = await nestingApi.downloadReport(parseInt(nesting.id))
        
        // Crea un link per il download
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = reportInfo.filename || `nesting_${nesting.id}_report.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        toast({
          variant: "default",
          title: "Report Scaricato",
          description: `Il report del nesting ${nesting.id.substring(0, 8)}... è stato scaricato.`
        })
      } catch (error: any) {
        // Se il report non è disponibile, mostra messaggio informativo
        if (error.status === 404) {
          toast({
            variant: "default",
            title: "Report non disponibile",
            description: "Il report per questo nesting non è ancora stato generato."
          })
        } else {
          throw error // Rilancia l'errore per la gestione generale
        }
      }
    })
  }

  // Funzione per aprire il dialog di caricamento
  const openLoadDialog = (nesting: NestingResponse) => {
    setNestingToLoad(nesting)
    setLoadDialogOpen(true)
  }

  // Funzione per aprire il dialog di eliminazione
  const openDeleteDialog = (nesting: NestingResponse) => {
    setNestingToDelete(nesting)
    setDeleteDialogOpen(true)
  }

  // Verifica se un nesting può essere caricato
  const canLoadNesting = (stato: string) => {
    return ['in sospeso', 'confermato'].includes(stato.toLowerCase())
  }

  // Funzione per renderizzare i pulsanti smart in base allo stato
  const renderSmartActions = (nesting: NestingResponse) => {
    const stato = nesting.stato.toLowerCase()
    const isLoading = loadingActions[nesting.id]
    
    return (
      <div className="flex items-center gap-1">
        {/* Pulsante Visualizza - sempre presente */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedNesting(
            selectedNesting === nesting.id ? null : nesting.id
          )}
          className="h-8 w-8 p-0"
          title="Visualizza dettagli"
        >
          <Eye className="h-4 w-4" />
        </Button>

        {/* Azioni specifiche per stato BOZZA */}
        {stato === 'bozza' && (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleConfirmNesting(nesting)}
              disabled={isLoading === 'conferma'}
              className="h-8 px-2 text-green-600 hover:text-green-700 hover:bg-green-50"
              title="Conferma nesting"
            >
              {isLoading === 'conferma' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              <span className="ml-1 text-xs">Conferma</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleRegenerateNesting(nesting)}
              disabled={isLoading === 'rigenera'}
              className="h-8 px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
              title="Rigenera nesting"
            >
              {isLoading === 'rigenera' ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
              <span className="ml-1 text-xs">Rigenera</span>
            </Button>
          </>
        )}

        {/* Azioni specifiche per stato IN SOSPESO */}
        {(stato === 'in sospeso' || stato === 'confermato') && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openLoadDialog(nesting)}
            disabled={isLoading === 'carica'}
            className="h-8 px-2 text-orange-600 hover:text-orange-700 hover:bg-orange-50"
            title="Carica nesting"
          >
            {isLoading === 'carica' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span className="ml-1 text-xs">Carica</span>
          </Button>
        )}

        {/* Azioni specifiche per stato CURA */}
        {stato === 'cura' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleCompleteNesting(nesting)}
            disabled={isLoading === 'completa'}
            className="h-8 px-2 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
            title="Completa nesting"
          >
            {isLoading === 'completa' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            <span className="ml-1 text-xs">Completa</span>
          </Button>
        )}

        {/* Azioni specifiche per stato FINITO */}
        {stato === 'finito' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDownloadReport(nesting)}
            disabled={isLoading === 'report'}
            className="h-8 px-2 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
            title="Scarica report"
          >
            {isLoading === 'report' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            <span className="ml-1 text-xs">Report</span>
          </Button>
        )}

        {/* Pulsante Elimina - sempre presente ma con conferma */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => openDeleteDialog(nesting)}
          disabled={isLoading === 'elimina'}
          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
          title="Elimina nesting"
        >
          {isLoading === 'elimina' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
        </Button>
      </div>
    )
  }

  // Componente per le righe di caricamento
  const LoadingRows = () => (
    <>
      {Array.from({ length: 3 }).map((_, index) => (
        <TableRow key={index}>
          <TableCell><Skeleton className="h-4 w-20" /></TableCell>
          <TableCell><Skeleton className="h-4 w-32" /></TableCell>
          <TableCell><Skeleton className="h-6 w-24" /></TableCell>
          <TableCell><Skeleton className="h-4 w-16" /></TableCell>
          <TableCell><Skeleton className="h-4 w-20" /></TableCell>
          <TableCell><Skeleton className="h-4 w-32" /></TableCell>
          <TableCell><Skeleton className="h-4 w-40" /></TableCell>
          <TableCell><Skeleton className="h-8 w-32" /></TableCell>
        </TableRow>
      ))}
    </>
  )

  // Componente per riga vuota quando non ci sono dati
  const EmptyRow = () => (
    <TableRow>
      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
        <div className="flex flex-col items-center gap-2">
          <p>Nessun nesting trovato</p>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Ricarica
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )

  return (
    <div className="space-y-4">
      {/* Tabella principale */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px]">ID</TableHead>
              <TableHead className="w-[140px]">Autoclave</TableHead>
              <TableHead className="w-[120px]">Stato</TableHead>
              <TableHead className="w-[80px]">ODL</TableHead>
              <TableHead className="w-[100px]">Efficienza</TableHead>
              <TableHead className="w-[180px]">Data Creazione</TableHead>
              <TableHead>Note</TableHead>
              <TableHead className="w-[200px]">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <LoadingRows />
            ) : data.length === 0 ? (
              <EmptyRow />
            ) : (
              data.map((nesting) => (
                <TableRow 
                  key={nesting.id}
                  className={selectedNesting === nesting.id ? 'bg-muted/50' : ''}
                >
                  <TableCell className="font-mono text-sm">
                    {nesting.id.substring(0, 8)}...
                  </TableCell>
                  <TableCell>
                    {nesting.autoclave_nome || "—"}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatoBadgeVariant(nesting.stato)}>
                      {nesting.stato}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    {nesting.odl_inclusi !== undefined ? (
                      <span className="font-medium">
                        {nesting.odl_inclusi}
                        {nesting.odl_esclusi !== undefined && nesting.odl_esclusi > 0 && (
                          <span className="text-muted-foreground text-xs ml-1">
                            (+{nesting.odl_esclusi})
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {nesting.efficienza !== undefined ? (
                      <span className={`font-medium ${
                        nesting.efficienza >= 70 ? 'text-green-600' : 
                        nesting.efficienza >= 50 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {nesting.efficienza.toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {formatDate(nesting.created_at)}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {nesting.note || 'Nessuna nota'}
                  </TableCell>
                  <TableCell>
                    {renderSmartActions(nesting)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Dialog per caricamento nesting */}
      <Dialog open={loadDialogOpen} onOpenChange={setLoadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Carica Nesting</DialogTitle>
            <DialogDescription>
              Conferma il caricamento del nesting nell'autoclave. Questo cambierà lo stato degli ODL a "Cura" e dell'autoclave a "IN_USO".
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {nestingToLoad && (
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm">
                  <strong>Nesting ID:</strong> {nestingToLoad.id.substring(0, 8)}...
                </p>
                <p className="text-sm">
                  <strong>Stato attuale:</strong> {nestingToLoad.stato}
                </p>
              </div>
            )}
            
            <div>
              <Label htmlFor="load-notes">Note di caricamento (opzionale)</Label>
              <Textarea
                id="load-notes"
                placeholder="Inserisci eventuali note sul caricamento..."
                value={loadNotes}
                onChange={(e) => setLoadNotes(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setLoadDialogOpen(false)
                setLoadNotes('')
                setNestingToLoad(null)
              }}
            >
              Annulla
            </Button>
            <Button
              onClick={() => nestingToLoad && handleLoadNesting(nestingToLoad)}
              disabled={loadingActions[nestingToLoad?.id || ''] === 'carica'}
              className="flex items-center gap-2"
            >
              {loadingActions[nestingToLoad?.id || ''] === 'carica' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Caricamento...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Carica Nesting
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog per eliminazione nesting */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Elimina Nesting</DialogTitle>
            <DialogDescription>
              Sei sicuro di voler eliminare definitivamente questo nesting? Questa azione non può essere annullata.
            </DialogDescription>
          </DialogHeader>
          
          {nestingToDelete && (
            <div className="p-3 bg-muted rounded-lg space-y-2">
              <p className="text-sm">
                <strong>ID Nesting:</strong> {nestingToDelete.id.substring(0, 8)}...
              </p>
              <p className="text-sm">
                <strong>Stato:</strong> {nestingToDelete.stato}
              </p>
              <p className="text-sm">
                <strong>Autoclave:</strong> {nestingToDelete.autoclave_nome || "Non specificata"}
              </p>
              {nestingToDelete.odl_inclusi !== undefined && (
                <p className="text-sm">
                  <strong>ODL inclusi:</strong> {nestingToDelete.odl_inclusi}
                </p>
              )}
              <p className="text-sm">
                <strong>Creato il:</strong> {formatDate(nestingToDelete.created_at)}
              </p>
            </div>
          )}
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false)
                setNestingToDelete(null)
              }}
              disabled={loadingActions[nestingToDelete?.id || ''] === 'elimina'}
            >
              Annulla
            </Button>
            <Button
              variant="destructive"
              onClick={() => nestingToDelete && handleDeleteNesting(nestingToDelete)}
              disabled={loadingActions[nestingToDelete?.id || ''] === 'elimina'}
              className="flex items-center gap-2"
            >
              {loadingActions[nestingToDelete?.id || ''] === 'elimina' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Eliminazione...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4" />
                  Elimina Definitivamente
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Informazioni aggiuntive */}
      {!isLoading && data.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <p>
            Totale: {data.length} nesting
          </p>
          <p>
            Ultimo aggiornamento: {new Date().toLocaleTimeString('it-IT')}
          </p>
        </div>
      )}
    </div>
  )
} 