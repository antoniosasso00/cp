'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Edit, Trash2 } from 'lucide-react'
import { ConfirmDialog, useConfirmDialog } from '@/components/ui/confirm-dialog'
import { phaseTimesApi, odlApi, CatalogoResponse } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Switch } from '@/components/ui/switch'

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
  const [showOnlyValidODL, setShowOnlyValidODL] = useState(false)
  
  // Stati per il dialogo di modifica ODL
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingOdl, setEditingOdl] = useState<any>(null)
  const [editNote, setEditNote] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  
  const { toast } = useStandardToast()
  const { confirm, ConfirmDialog } = useConfirmDialog()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica i dati dei tempi di fase
      const tempiData = await phaseTimesApi.fetchPhaseTimes();
      
      // Carica i dati degli ODL per riferimento con filtro opzionale
      const odlParams = showOnlyValidODL ? { include_in_std: true } : {};
      const odlData = await odlApi.fetchODLs(odlParams);
      
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
  }, [filtri, showOnlyValidODL]) // Ricarica quando cambiano i filtri o il toggle

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
      await odlApi.updateODL(editingOdl.id, {
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
    const confirmed = await confirm({
      title: "Conferma eliminazione",
      description: `Sei sicuro di voler eliminare l'ODL ${odlId}? Questa azione non può essere annullata.`,
      confirmText: "Elimina",
      cancelText: "Annulla",
      onConfirm: async () => {
        // La logica di eliminazione sarà gestita dopo la conferma
      }
    });

    if (!confirmed) return;

    try {
      await odlApi.deleteODL(odlId);
      
      toast({
        title: "✅ ODL eliminato",
        description: `ODL ${odlId} eliminato con successo`,
      });
      
      // Ricarica i dati
      await fetchData();
      
    } catch (error) {
      console.error('Errore durante l\'eliminazione ODL:', error);
      toast({
        title: "❌ Errore",
        description: "Impossibile eliminare l'ODL. Riprova più tardi.",
        variant: "destructive",
      });
    }
  }

  // Funzione per gestire il toggle include_in_std
  const handleToggleIncludeInStd = async (odlId: number, currentValue: boolean) => {
    try {
      await odlApi.updateODL(odlId, {
        include_in_std: !currentValue
      });
      
      toast({
        title: "✅ ODL aggiornato",
        description: `ODL ${odlId} ${!currentValue ? 'incluso' : 'escluso'} dai tempi standard`,
      });
      
      // Ricarica i dati
      await fetchData();
      
    } catch (error) {
      console.error('Errore durante l\'aggiornamento include_in_std:', error);
      toast({
        title: "❌ Errore",
        description: "Impossibile aggiornare l'ODL. Riprova più tardi.",
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
      {/* Controlli e Filtri */}
      <Card>
        <CardHeader>
          <CardTitle>Filtri Tempi ODL</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Cerca per ODL ID, Part Number, Fase o Note..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="valid-odl"
                checked={showOnlyValidODL}
                onCheckedChange={setShowOnlyValidODL}
              />
              <Label htmlFor="valid-odl">Solo ODL validi per tempi standard</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabella Tempi */}
      <Card>
        <CardHeader>
          <CardTitle>Tempi di Fase ODL</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredItems.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato disponibile</AlertTitle>
              <AlertDescription>
                Non ci sono tempi di fase che corrispondono ai filtri selezionati.
                Prova a modificare i criteri di ricerca o i filtri globali.
              </AlertDescription>
            </Alert>
          ) : (
            <Table>
              <TableCaption>
                Mostrando {filteredItems.length} tempi di fase
              </TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ODL ID</TableHead>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Fase</TableHead>
                  <TableHead>Inizio</TableHead>
                  <TableHead>Fine</TableHead>
                  <TableHead>Durata</TableHead>
                  <TableHead>Valido per Std</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item) => {
                  const odlInfo = getOdlInfo(item.odl_id);
                  return (
                    <TableRow key={`${item.odl_id}-${item.fase}-${item.inizio_fase}`}>
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
                        {item.fine_fase ? formatDateTime(item.fine_fase) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {formatDuration(item.durata_minuti)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Checkbox
                          checked={odlInfo?.include_in_std || false}
                          onCheckedChange={() => handleToggleIncludeInStd(item.odl_id, odlInfo?.include_in_std || false)}
                        />
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {item.note || odlInfo?.note || '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditOdl(item.odl_id)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteOdl(item.odl_id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Dialog per modifica ODL */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Modifica ODL {editingOdl?.id}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit-note">Note</Label>
              <Textarea
                id="edit-note"
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                placeholder="Inserisci note per questo ODL..."
                rows={4}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setEditDialogOpen(false)}
                disabled={isUpdating}
              >
                Annulla
              </Button>
              <Button
                onClick={handleSaveOdl}
                disabled={isUpdating}
              >
                {isUpdating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Salvando...
                  </>
                ) : (
                  'Salva'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ConfirmDialog />
    </div>
  )
} 