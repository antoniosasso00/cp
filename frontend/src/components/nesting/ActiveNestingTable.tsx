'use client'

import { useState, useEffect } from 'react'
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { RefreshCw, Play, Eye, Clock, Zap, Package } from 'lucide-react'
import { nestingApi, NestingDetailResponse, NestingLoadRequest } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface ActiveNestingTableProps {
  onRefresh?: () => void
}

// Funzione per ottenere il colore del badge in base allo stato
const getStatoBadgeVariant = (stato: string) => {
  switch (stato.toLowerCase()) {
    case 'caricato':
      return 'default' as const
    case 'in sospeso':
      return 'secondary' as const
    case 'confermato':
      return 'outline' as const
    default:
      return 'outline' as const
  }
}

// Funzione per ottenere il colore del badge dell'autoclave
const getAutostaveBadgeVariant = (stato: string) => {
  switch (stato.toUpperCase()) {
    case 'IN_USO':
      return 'destructive' as const
    case 'DISPONIBILE':
      return 'default' as const
    case 'MANUTENZIONE':
      return 'secondary' as const
    case 'GUASTO':
      return 'destructive' as const
    default:
      return 'outline' as const
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

export function ActiveNestingTable({ onRefresh }: ActiveNestingTableProps) {
  const [data, setData] = useState<NestingDetailResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedNesting, setSelectedNesting] = useState<NestingDetailResponse | null>(null)
  const [loadingNestingId, setLoadingNestingId] = useState<number | null>(null)
  const [loadDialogOpen, setLoadDialogOpen] = useState(false)
  const [loadNotes, setLoadNotes] = useState('')
  const { toast } = useToast()

  // Funzione per caricare i dati
  const fetchActiveNesting = async () => {
    try {
      setIsLoading(true)
      const response = await nestingApi.getActive()
      setData(response)
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare i nesting attivi",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Carica i dati al mount
  useEffect(() => {
    fetchActiveNesting()
  }, [])

  // Funzione per ricaricare i dati
  const handleRefresh = () => {
    fetchActiveNesting()
    onRefresh?.()
  }

  // Funzione per caricare un nesting
  const handleLoadNesting = async (nestingId: number) => {
    try {
      setLoadingNestingId(nestingId)
      
      const loadData: NestingLoadRequest = {
        caricato_da_ruolo: 'curing',
        note_caricamento: loadNotes.trim() || undefined
      }
      
      await nestingApi.load(nestingId, loadData)
      
      toast({
        title: "Successo",
        description: "Nesting caricato con successo!",
      })
      setLoadDialogOpen(false)
      setLoadNotes('')
      setSelectedNesting(null)
      
      // Ricarica i dati
      await fetchActiveNesting()
      
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare il nesting",
        variant: "destructive",
      })
    } finally {
      setLoadingNestingId(null)
    }
  }

  // Componente per le righe di caricamento
  const LoadingRows = () => (
    <>
      {Array.from({ length: 3 }).map((_, index) => (
        <TableRow key={index}>
          <TableCell><Skeleton className="h-4 w-16" /></TableCell>
          <TableCell><Skeleton className="h-4 w-32" /></TableCell>
          <TableCell><Skeleton className="h-6 w-24" /></TableCell>
          <TableCell><Skeleton className="h-6 w-20" /></TableCell>
          <TableCell><Skeleton className="h-4 w-16" /></TableCell>
          <TableCell><Skeleton className="h-4 w-20" /></TableCell>
          <TableCell><Skeleton className="h-4 w-40" /></TableCell>
          <TableCell><Skeleton className="h-8 w-24" /></TableCell>
        </TableRow>
      ))}
    </>
  )

  // Componente per riga vuota quando non ci sono dati
  const EmptyRow = () => (
    <TableRow>
      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
        <div className="flex flex-col items-center gap-2">
          <Package className="h-8 w-8 text-muted-foreground/50" />
          <p>Nessun nesting attivo trovato</p>
          <p className="text-sm">I nesting caricati appariranno qui</p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
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
      {/* Header con statistiche */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nesting Attivi</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.length}</div>
            <p className="text-xs text-muted-foreground">
              Attualmente in cura
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ODL in Cura</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.reduce((total, nesting) => total + nesting.odl_inclusi.length, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Totale ODL attivi
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Autoclavi Occupate</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(data.map(n => n.autoclave.id)).size}
            </div>
            <p className="text-xs text-muted-foreground">
              In uso
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabella principale */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Nesting Attivi</CardTitle>
              <CardDescription>
                Nesting attualmente caricati nelle autoclavi
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Ricarica
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">ID</TableHead>
                  <TableHead className="w-[140px]">Autoclave</TableHead>
                  <TableHead className="w-[100px]">Stato</TableHead>
                  <TableHead className="w-[120px]">Stato Autoclave</TableHead>
                  <TableHead className="w-[80px]">ODL</TableHead>
                  <TableHead className="w-[100px]">Efficienza</TableHead>
                  <TableHead>Data Caricamento</TableHead>
                  <TableHead className="w-[120px]">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <LoadingRows />
                ) : data.length === 0 ? (
                  <EmptyRow />
                ) : (
                  data.map((nesting) => (
                    <TableRow key={nesting.id}>
                      <TableCell className="font-mono text-sm">
                        #{nesting.id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {nesting.autoclave.nome}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatoBadgeVariant(nesting.stato)}>
                          {nesting.stato}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getAutostaveBadgeVariant(nesting.autoclave.stato)}>
                          {nesting.autoclave.stato}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="font-medium">{nesting.odl_inclusi.length}</span>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">
                          {nesting.statistiche.efficienza.toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(nesting.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedNesting(
                              selectedNesting?.id === nesting.id ? null : nesting
                            )}
                            className="h-8 w-8 p-0"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Dettagli nesting selezionato */}
      {selectedNesting && (
        <Card>
          <CardHeader>
            <CardTitle>Dettagli Nesting #{selectedNesting.id}</CardTitle>
            <CardDescription>
              Autoclave: {selectedNesting.autoclave.nome} - {selectedNesting.odl_inclusi.length} ODL in cura
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Statistiche</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Area utilizzata:</span>
                    <span>{selectedNesting.statistiche.area_utilizzata.toFixed(1)} cm²</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Efficienza:</span>
                    <span>{selectedNesting.statistiche.efficienza.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Peso totale:</span>
                    <span>{selectedNesting.statistiche.peso_totale.toFixed(1)} kg</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Valvole utilizzate:</span>
                    <span>{selectedNesting.statistiche.valvole_utilizzate}/{selectedNesting.statistiche.valvole_totali}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">ODL Inclusi</h4>
                <div className="space-y-1 text-sm max-h-32 overflow-y-auto">
                  {selectedNesting.odl_inclusi.map((odl) => (
                    <div key={odl.id} className="flex justify-between items-center">
                      <span>ODL #{odl.id}</span>
                      <Badge variant="outline" className="text-xs">
                        {odl.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {selectedNesting.note && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Note</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {selectedNesting.note}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
                setSelectedNesting(null)
              }}
            >
              Annulla
            </Button>
            <Button
              onClick={() => selectedNesting && handleLoadNesting(selectedNesting.id)}
              disabled={loadingNestingId !== null}
              className="flex items-center gap-2"
            >
              {loadingNestingId !== null ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
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

      {/* Informazioni aggiuntive */}
      {!isLoading && data.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <p>
            Totale: {data.length} nesting attivi
          </p>
          <p>
            Ultimo aggiornamento: {new Date().toLocaleTimeString('it-IT')}
          </p>
        </div>
      )}
    </div>
  )
} 