'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ODLResponse, odlApi, produzioneApi } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { 
  Loader2, 
  RefreshCw,
  Activity,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  Flame,
  Grid3X3
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import Link from 'next/link'

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

export default function ProduzioneCuringPage() {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedODL, setSelectedODL] = useState<ODLResponse | null>(null)
  const [isAdvancing, setIsAdvancing] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [nextStatus, setNextStatus] = useState<"Cura" | "Finito" | null>(null)
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // ✅ NUOVO: Usa le nuove API dedicate per la produzione
      try {
        // Prova prima con l'API dedicata produzione
        const data = await produzioneApi.getODL()
        const allOdl = [...data.attesa_cura, ...data.in_cura]
        setOdlList(allOdl)
        
        toast({
          title: '✅ Dati caricati',
          description: `${data.statistiche.totale_attesa_cura} ODL in attesa, ${data.statistiche.totale_in_cura} in cura`,
        })
        
        return // Successo, esci dalla funzione
      } catch (error) {
        console.warn('⚠️ API produzione non disponibile, fallback su API standard:', error)
      }
      
      // ✅ FALLBACK: Se l'API produzione non funziona, usa l'API standard con gestione robusta
      console.log('🔄 Fallback: caricamento con API standard...')
      
      const allOdl = await odlApi.fetchODLs()
      const relevantOdl = allOdl.filter(odl => 
        odl.status === "Attesa Cura" || odl.status === "Cura"
      )
      setOdlList(relevantOdl)
      
      const attesaCura = relevantOdl.filter(odl => odl.status === "Attesa Cura").length
      const inCura = relevantOdl.filter(odl => odl.status === "Cura").length
      
      toast({
        title: '✅ Dati caricati (fallback)',
        description: `${attesaCura} ODL in attesa, ${inCura} in cura`,
      })
      
    } catch (error: any) {
      console.error('❌ Errore nel caricamento dei dati:', error)
      
      // ✅ NUOVO: Gestione errori più robusta
      let errorMessage = 'Impossibile caricare i dati di produzione.'
      
      if (error.message?.includes('connessione') || error.code === 'ECONNREFUSED') {
        errorMessage = 'Errore di connessione al server. Verifica che il backend sia attivo.'
      } else if (error.message?.includes('404') || error.response?.status === 404) {
        errorMessage = 'Endpoint non trovato. Verifica la configurazione del backend.'
      } else if (error.response?.status >= 500) {
        errorMessage = 'Errore interno del server. Riprova più tardi.'
      }
      
      toast({
        variant: 'destructive',
        title: '❌ Errore caricamento',
        description: errorMessage,
      })
      
      // ✅ NUOVO: In caso di errore, mostra comunque una lista vuota invece di bloccare l'interfaccia
      setOdlList([])
      
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

  // Separa ODL per stato
  const odlAttesaCura = filteredOdl.filter(odl => odl.status === "Attesa Cura")
  const odlInCura = filteredOdl.filter(odl => odl.status === "Cura")

  // Determina il prossimo stato possibile per un ODL
  const getNextStatus = (currentStatus: string): "Cura" | "Finito" | null => {
    switch (currentStatus) {
      case "Attesa Cura":
        return "Cura"
      case "Cura":
        return "Finito"
      default:
        return null
    }
  }

  // Gestisce il cambio stato
  const handleStatusChange = async (odl: ODLResponse, newStatus: "Cura" | "Finito") => {
    setIsAdvancing(true)
    try {
      await odlApi.updateStatusCuring(odl.id, newStatus)
      
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
      "Attesa Cura->Cura": "L'ODL passerà dalla fase di attesa al processo di cura attivo in autoclave.",
      "Cura->Finito": "L'ODL sarà completato e il processo di produzione sarà terminato."
    }
    return descriptions[`${currentStatus}->${nextStatus}`] || "Cambio di stato dell'ODL."
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Flame className="h-8 w-8 text-orange-500" />
            Produzione Curing
          </h1>
          <p className="text-muted-foreground">
            Gestione ODL in Attesa Cura e Cura - Controllo processi di cura
          </p>
        </div>
        <div className="flex gap-2">
                          <Link href="/dashboard/curing/nesting">
            <Button variant="outline">
              <Grid3X3 className="mr-2 h-4 w-4" />
              Gestione Nesting
            </Button>
          </Link>
          <Button onClick={fetchData} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Ricarica
          </Button>
        </div>
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
          <Badge variant="warning">Attesa Cura: {odlAttesaCura.length}</Badge>
          <Badge variant="destructive">In Cura: {odlInCura.length}</Badge>
        </div>
      </div>

      {/* Contenuto principale */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento ODL...</span>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* ODL in Attesa Cura */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-orange-500" />
                ODL in Attesa Cura ({odlAttesaCura.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {odlAttesaCura.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="text-lg font-medium">Nessun ODL in attesa</p>
                  <p className="text-sm">Non ci sono ODL pronti per la cura al momento.</p>
                </div>
              ) : (
                <Table>
                  <TableCaption>ODL pronti per il processo di cura</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ODL</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Priorità</TableHead>
                      <TableHead className="text-center">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {odlAttesaCura.map(odl => (
                      <TableRow key={odl.id}>
                        <TableCell className="font-medium">#{odl.id}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {odl.parte?.part_number || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={odl.priorita > 5 ? "destructive" : odl.priorita > 3 ? "warning" : "secondary"}>
                            {odl.priorita}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            size="sm"
                            onClick={() => openConfirmDialog(odl)}
                            disabled={isAdvancing}
                            className="flex items-center gap-2"
                          >
                            {isAdvancing ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <>
                                <ArrowRight className="h-3 w-3" />
                                Avvia Cura
                              </>
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* ODL in Cura */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-red-500" />
                ODL in Cura ({odlInCura.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {odlInCura.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="text-lg font-medium">Nessun ODL in cura</p>
                  <p className="text-sm">Non ci sono processi di cura attivi al momento.</p>
                </div>
              ) : (
                <Table>
                  <TableCaption>ODL attualmente in processo di cura</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ODL</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Priorità</TableHead>
                      <TableHead>Inizio Cura</TableHead>
                      <TableHead className="text-center">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {odlInCura.map(odl => (
                      <TableRow key={odl.id}>
                        <TableCell className="font-medium">#{odl.id}</TableCell>
                        <TableCell className="font-mono text-sm">
                          {odl.parte?.part_number || 'N/A'}
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
                          <Button
                            size="sm"
                            onClick={() => openConfirmDialog(odl)}
                            disabled={isAdvancing}
                            className="flex items-center gap-2"
                            variant="outline"
                          >
                            {isAdvancing ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <>
                                <CheckCircle className="h-3 w-3" />
                                Completa Cura
                              </>
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
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
                <p><strong>Valvole richieste:</strong> {selectedODL?.parte?.num_valvole_richieste}</p>
              </div>
            </div>
            
            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-sm text-orange-800">
                {selectedODL && nextStatus && getTransitionDescription(selectedODL.status, nextStatus)}
              </p>
            </div>

            {selectedODL?.status === "Attesa Cura" && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Nota:</strong> Assicurati che l'ODL sia stato incluso in un nesting confermato prima di avviare la cura.
                </p>
              </div>
            )}
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
                  Conferma {nextStatus === "Cura" ? "Avvio Cura" : "Completamento"}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 