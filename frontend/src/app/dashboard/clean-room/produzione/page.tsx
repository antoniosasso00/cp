'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ODLResponse, odlApi } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { 
  Loader2, 
  RefreshCw,
  Activity,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  Wrench
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "default",
    "Attesa Cura": "warning"
  }
  return variants[status] || "default"
}

export default function ProduzionePage() {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedODL, setSelectedODL] = useState<ODLResponse | null>(null)
  const [isAdvancing, setIsAdvancing] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [nextStatus, setNextStatus] = useState<"Laminazione" | "Attesa Cura" | null>(null)
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica solo ODL rilevanti per il Clean Room (Preparazione e Laminazione)
      const allOdl = await odlApi.fetchODLs()
      const relevantOdl = allOdl.filter(odl => 
        odl.status === "Preparazione" || odl.status === "Laminazione"
      )
      setOdlList(relevantOdl)
      
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati di produzione. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Filtra i dati in base alla ricerca
  const filteredOdl = odlList.filter(odl => {
    const searchLower = searchQuery.toLowerCase()
    return (
      odl.parte?.part_number?.toLowerCase()?.includes(searchLower) ||
      String(odl.id).includes(searchLower) ||
      odl.status.toLowerCase().includes(searchLower) ||
      (odl.note && odl.note.toLowerCase().includes(searchLower))
    )
  })

  // Determina il prossimo stato possibile per un ODL
  const getNextStatus = (currentStatus: string): "Laminazione" | "Attesa Cura" | null => {
    switch (currentStatus) {
      case "Preparazione":
        return "Laminazione"
      case "Laminazione":
        return "Attesa Cura"
      default:
        return null
    }
  }

  // Gestisce il cambio stato
  const handleStatusChange = async (odl: ODLResponse, newStatus: "Laminazione" | "Attesa Cura") => {
    setIsAdvancing(true)
    try {
      await odlApi.updateStatusCleanRoom(odl.id, newStatus)
      
      toast({
        title: '✅ Stato aggiornato con successo',
        description: `ODL #${odl.id} è passato da "${odl.status}" a "${newStatus}"`,
      })
      
      // Ricarica i dati automaticamente
      await fetchData()
      
    } catch (error: any) {
      console.error('Errore nell\'aggiornamento dello stato:', error)
      
      // Gestione errori più dettagliata
      let errorMessage = 'Impossibile aggiornare lo stato dell\'ODL.'
      
      if (error.response?.status === 404) {
        errorMessage = 'ODL non trovato. Potrebbe essere stato eliminato.'
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || 'Transizione di stato non consentita.'
      } else if (error.response?.status === 422) {
        errorMessage = 'Dati non validi. Verifica i parametri della richiesta.'
      } else if (error.message?.includes('connessione')) {
        errorMessage = 'Errore di connessione al server. Verifica che il backend sia attivo.'
      }
      
      toast({
        variant: 'destructive',
        title: '❌ Errore aggiornamento stato',
        description: errorMessage,
      })
      
      // Ricarica i dati anche in caso di errore per sincronizzare lo stato
      await fetchData()
      
    } finally {
      setIsAdvancing(false)
      setShowConfirmDialog(false)
      setSelectedODL(null)
      setNextStatus(null)
    }
  }

  // Apre il dialog di conferma
  const openConfirmDialog = (odl: ODLResponse) => {
    const next = getNextStatus(odl.status)
    if (next) {
      setSelectedODL(odl)
      setNextStatus(next)
      setShowConfirmDialog(true)
    }
  }

  // Ottiene il testo descrittivo per la transizione
  const getTransitionDescription = (currentStatus: string, nextStatus: string) => {
    const descriptions: Record<string, string> = {
      "Preparazione->Laminazione": "L'ODL passerà dalla fase di preparazione alla laminazione attiva.",
      "Laminazione->Attesa Cura": "L'ODL sarà completato e passerà in attesa del processo di cura."
    }
    return descriptions[`${currentStatus}->${nextStatus}`] || "Cambio di stato dell'ODL."
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Wrench className="h-8 w-8 text-green-500" />
            Produzione Clean Room
          </h1>
          <p className="text-muted-foreground">
            Gestione ODL in Preparazione e Laminazione - Avanzamento stati di produzione
          </p>
        </div>
        <Button onClick={fetchData} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Ricarica
        </Button>
      </div>

      {/* Filtro di ricerca */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca ODL per codice, part number o stato..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <div className="flex gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">Preparazione: {odlList.filter(o => o.status === "Preparazione").length}</Badge>
          <Badge variant="default">Laminazione: {odlList.filter(o => o.status === "Laminazione").length}</Badge>
        </div>
      </div>

      {/* Contenuto principale */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento ODL...</span>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
                              ODL Clean Room ({filteredOdl.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredOdl.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-lg font-medium">Nessun ODL trovato</p>
                <p className="text-sm">Non ci sono ODL in Preparazione o Laminazione al momento.</p>
              </div>
            ) : (
              <Table>
                                  <TableCaption>ODL gestibili dal ruolo Clean Room</TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>ODL</TableHead>
                    <TableHead>Part Number</TableHead>
                    <TableHead>Descrizione</TableHead>
                    <TableHead>Tool</TableHead>
                    <TableHead>Stato Attuale</TableHead>
                    <TableHead>Priorità</TableHead>
                    <TableHead>Ultimo Aggiornamento</TableHead>
                    <TableHead className="text-center">Azioni</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOdl.map(odl => {
                    const nextStatus = getNextStatus(odl.status)
                    return (
                      <TableRow key={odl.id}>
                        <TableCell className="font-medium">#{odl.id}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {odl.parte?.part_number ? (
                            <span className="text-foreground">{odl.parte.part_number}</span>
                          ) : (
                            <span className="text-red-500 font-medium">⚠️ Mancante</span>
                          )}
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="truncate" title={odl.parte?.descrizione_breve || "Descrizione non disponibile"}>
                            {odl.parte?.descrizione_breve ? (
                              <span className="text-foreground">{odl.parte.descrizione_breve}</span>
                            ) : (
                              <span className="text-red-500 font-medium">⚠️ Mancante</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {odl.tool?.part_number_tool ? (
                            <span className="text-foreground">{odl.tool.part_number_tool}</span>
                          ) : (
                            <span className="text-red-500 font-medium">⚠️ Mancante</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(odl.status)}>
                            {odl.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={odl.priorita > 5 ? "destructive" : odl.priorita > 3 ? "warning" : "secondary"}>
                            {odl.priorita}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDateTime(odl.updated_at)}
                        </TableCell>
                        <TableCell className="text-center">
                          {nextStatus ? (
                            <Button
                              size="sm"
                              onClick={() => openConfirmDialog(odl)}
                              disabled={isAdvancing || !odl.parte || !odl.tool}
                              className="flex items-center gap-2"
                              title={!odl.parte || !odl.tool ? "Dati ODL incompleti" : `Avanza a ${nextStatus}`}
                            >
                              {isAdvancing ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <>
                                  <ArrowRight className="h-3 w-3" />
                                  {nextStatus}
                                </>
                              )}
                            </Button>
                          ) : (
                            <span className="text-sm text-muted-foreground">
                              <CheckCircle className="h-4 w-4 inline mr-1" />
                              Completato
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {/* Dialog di conferma */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conferma Avanzamento ODL</DialogTitle>
            <DialogDescription>
              Stai per far avanzare l'ODL #{selectedODL?.id} dallo stato "{selectedODL?.status}" a "{nextStatus}".
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Dettagli ODL:</h4>
              <div className="space-y-1 text-sm">
                <p><strong>Part Number:</strong> {selectedODL?.parte?.part_number}</p>
                <p><strong>Descrizione:</strong> {selectedODL?.parte?.descrizione_breve}</p>
                <p><strong>Tool:</strong> {selectedODL?.tool?.part_number_tool}</p>
                <p><strong>Priorità:</strong> {selectedODL?.priorita}</p>
              </div>
            </div>
            
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                {selectedODL && nextStatus && getTransitionDescription(selectedODL.status, nextStatus)}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              Annulla
            </Button>
            <Button 
              onClick={() => selectedODL && nextStatus && handleStatusChange(selectedODL, nextStatus)}
              disabled={isAdvancing}
            >
              {isAdvancing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Aggiornamento...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Conferma Avanzamento
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 