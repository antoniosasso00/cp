'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog'
import { tempoFasiApi, odlApi, CatalogoResponse } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface FiltriGlobali {
  periodo: string;
  partNumber: string;
  statoODL: string;
  dataInizio?: Date;
  dataFine?: Date;
}

interface TempiODLProps {
  filtri: FiltriGlobali;
  catalogo: CatalogoResponse[];
  onError: (message: string) => void;
}

// Funzione per formattare la durata in ore e minuti
const formatDuration = (minutes: number | null): string => {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

// Funzione per tradurre il tipo di fase
const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

// Badge varianti per i diversi tipi di fase
const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    "laminazione": "default",
    "attesa_cura": "secondary",
    "cura": "destructive",
  }
  return variants[fase] || "default"
}

export default function TempiODL({ filtri, catalogo, onError }: TempiODLProps) {
  const [tempiFasi, setTempiFasi] = useState<any[]>([])
  const [odlList, setOdlList] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Stati per il dialogo di modifica ODL
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingOdl, setEditingOdl] = useState<any>(null)
  const [editNote, setEditNote] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  
  const { toast } = useToast()
  const { confirm, ConfirmDialog } = useConfirmDialog()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica i dati dei tempi di fase
      const tempiData = await tempoFasiApi.getAll();
      
      // Carica i dati degli ODL per riferimento
      const odlData = await odlApi.getAll();
      
      // Applica i filtri globali
      let tempiFiltrati = tempiData;
      let odlFiltrati = odlData;
      
      // Filtra per periodo
      if (filtri.dataInizio && filtri.dataFine) {
        tempiFiltrati = tempiFiltrati.filter(tempo => {
          const dataInizio = new Date(tempo.inizio_fase);
          return dataInizio >= filtri.dataInizio! && dataInizio <= filtri.dataFine!;
        });
      }
      
      // Filtra per part number
      if (filtri.partNumber && filtri.partNumber !== 'all') {
        const odlConPartNumber = odlData.filter(odl => 
          odl.parte?.part_number === filtri.partNumber
        ).map(odl => odl.id);
        
        tempiFiltrati = tempiFiltrati.filter(tempo => 
          odlConPartNumber.includes(tempo.odl_id)
        );
      }
      
      // Filtra per stato ODL
      if (filtri.statoODL && filtri.statoODL !== 'all') {
        const odlConStato = odlData.filter(odl => 
          odl.status === filtri.statoODL
        ).map(odl => odl.id);
        
        tempiFiltrati = tempiFiltrati.filter(tempo => 
          odlConStato.includes(tempo.odl_id)
        );
      }
      
      setTempiFasi(tempiFiltrati);
      setOdlList(odlData);
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      onError('Impossibile caricare i dati di monitoraggio tempi. Riprova più tardi.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [filtri]) // Ricarica quando cambiano i filtri

  // Filtra i dati in base alla ricerca locale
  const filteredItems = tempiFasi.filter(item => {
    if (!searchQuery) return true;
    
    const searchLower = searchQuery.toLowerCase()
    const odlInfo = odlList.find(odl => odl.id === item.odl_id)
    
    return (
      (odlInfo?.parte?.part_number?.toLowerCase()?.includes(searchLower)) ||
      String(item.odl_id).includes(searchLower) ||
      translateFase(item.fase).toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    )
  })

  // Ottieni informazioni ODL tramite odl_id
  const getOdlInfo = (odlId: number) => {
    return odlList.find(odl => odl.id === odlId) || null;
  }

  // Funzione per aprire il dialogo di modifica ODL
  const handleEditOdl = (odlId: number) => {
    const odl = getOdlInfo(odlId);
    if (odl) {
      setEditingOdl(odl);
      setEditNote(odl.note || '');
      setEditDialogOpen(true);
    }
  }

  // Funzione per salvare le modifiche all'ODL
  const handleSaveOdl = async () => {
    if (!editingOdl) return;
    
    try {
      setIsUpdating(true);
      
      // Aggiorna solo le note dell'ODL
      await odlApi.update(editingOdl.id, {
        note: editNote
      });
      
      toast({
        title: "✅ ODL aggiornato correttamente",
        description: `Note dell'ODL ${editingOdl.id} aggiornate con successo`,
      });
      
      // Ricarica i dati
      await fetchData();
      setEditDialogOpen(false);
      
    } catch (error) {
      console.error('Errore durante l\'aggiornamento ODL:', error);
      toast({
        title: "❌ Errore",
        description: "Impossibile aggiornare l'ODL. Riprova più tardi.",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  }

  // Funzione per eliminare un ODL
  const handleDeleteOdl = async (odlId: number) => {
    const odl = getOdlInfo(odlId);
    if (!odl) return;
    
    const isFinished = odl.status === 'Finito';
    
    try {
      const confirmed = await confirm({
        title: isFinished ? "Elimina ODL Finito" : "Elimina ODL",
        description: isFinished 
          ? "Stai per eliminare un ODL in stato 'Finito'. Questa azione non può essere annullata e rimuoverà tutti i dati associati."
          : "Sei sicuro di voler eliminare questo ODL? Questa azione non può essere annullata.",
        confirmText: "Elimina",
        cancelText: "Annulla",
        variant: "danger",
        itemName: `ODL ${odlId} - ${odl.parte?.part_number || 'N/A'}`,
        onConfirm: async () => {
          // Elimina l'ODL con conferma se necessario
          await odlApi.delete(odlId, isFinished);
          
          toast({
            title: "🗑️ ODL eliminato con successo",
            description: `ODL ${odlId} rimosso dal sistema`,
          });
          
          // Ricarica i dati
          await fetchData();
        }
      });
      
    } catch (error) {
      console.error('Errore durante l\'eliminazione ODL:', error);
      toast({
        title: "❌ Errore",
        description: "Impossibile eliminare l'ODL. Riprova più tardi.",
        variant: "destructive",
      });
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Caricamento tempi ODL...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei tempi di produzione..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        
        <div className="text-sm text-muted-foreground">
          {filteredItems.length} record{filteredItems.length !== 1 ? 'i' : ''} trovati
        </div>
      </div>

      {filteredItems.length === 0 ? (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Nessun dato disponibile</AlertTitle>
          <AlertDescription>
            Nessun dato di monitoraggio tempi trovato per i filtri selezionati. 
            Prova a modificare i criteri di ricerca o il periodo temporale.
          </AlertDescription>
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Dettaglio Tempi di Produzione</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableCaption>Monitoraggio dei tempi di produzione per ODL</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ODL</TableHead>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Fase</TableHead>
                  <TableHead>Inizio</TableHead>
                  <TableHead>Fine</TableHead>
                  <TableHead>Durata</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map(item => {
                  const odlInfo = getOdlInfo(item.odl_id);
                  return (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.odl_id}</TableCell>
                      <TableCell>
                        {odlInfo?.parte?.part_number || 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getFaseBadgeVariant(item.fase)}>
                          {translateFase(item.fase)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {formatDateTime(item.inizio_fase)}
                      </TableCell>
                      <TableCell>
                        {item.fine_fase ? formatDateTime(item.fine_fase) : (
                          <Badge variant="outline">In corso</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`font-medium ${
                          item.durata_minuti && item.durata_minuti > 480 ? 'text-red-600' : 
                          item.durata_minuti && item.durata_minuti > 240 ? 'text-orange-600' : 'text-green-600'
                        }`}>
                          {formatDuration(item.durata_minuti)}
                        </span>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {item.note || '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-muted-foreground hover:text-blue-600"
                            onClick={() => handleEditOdl(item.odl_id)}
                            title="Modifica note ODL"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-muted-foreground hover:text-red-600"
                            onClick={() => handleDeleteOdl(item.odl_id)}
                            title="Elimina ODL"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Statistiche riassuntive */}
      {filteredItems.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Tempo Medio per Fase</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {['laminazione', 'attesa_cura', 'cura'].map(fase => {
                  const tempiFase = filteredItems.filter(item => item.fase === fase && item.durata_minuti);
                  const tempoMedio = tempiFase.length > 0 
                    ? tempiFase.reduce((sum, item) => sum + item.durata_minuti, 0) / tempiFase.length 
                    : 0;
                  
                  return (
                    <div key={fase} className="flex justify-between items-center">
                      <span className="text-sm">{translateFase(fase)}</span>
                      <span className="font-medium">{formatDuration(tempoMedio)}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Distribuzione Fasi</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {['laminazione', 'attesa_cura', 'cura'].map(fase => {
                  const count = filteredItems.filter(item => item.fase === fase).length;
                  const percentage = filteredItems.length > 0 ? (count / filteredItems.length) * 100 : 0;
                  
                  return (
                    <div key={fase} className="flex justify-between items-center">
                      <span className="text-sm">{translateFase(fase)}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{count}</span>
                        <span className="text-xs text-muted-foreground">({percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Stato Completamento</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Completate</span>
                  <span className="font-medium text-green-600">
                    {filteredItems.filter(item => item.fine_fase).length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">In Corso</span>
                  <span className="font-medium text-blue-600">
                    {filteredItems.filter(item => !item.fine_fase).length}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Totale</span>
                  <span className="font-medium">{filteredItems.length}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dialogo di modifica ODL */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Modifica ODL {editingOdl?.id}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Part Number</Label>
              <Input 
                value={editingOdl?.parte?.part_number || 'N/A'} 
                disabled 
                className="bg-muted"
              />
            </div>
            <div className="grid gap-2">
              <Label>Stato Attuale</Label>
              <Input 
                value={editingOdl?.status || 'N/A'} 
                disabled 
                className="bg-muted"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="note">Note</Label>
              <Textarea
                id="note"
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                placeholder="Inserisci note per l'ODL..."
                rows={3}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Annulla
            </Button>
            <Button onClick={handleSaveOdl} disabled={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                'Salva'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Componente di conferma per eliminazione */}
      <ConfirmDialog />
    </div>
  )
} 