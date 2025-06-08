'use client'

import { useState, useEffect } from 'react'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ODLResponse, odlApi, phaseTimesApi, TempoFaseResponse } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import { 
  Loader2, 
  RefreshCw,
  Activity,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  Wrench,
  Clock,
  Play,
  Timer,
  Undo2,
  AlertCircle
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

// Colori dei bottoni in base allo stato (aggiornato con arancione per Attesa Cura)
const getButtonColor = (status: string) => {
  const colors: Record<string, string> = {
    "Preparazione": "bg-blue-500 hover:bg-blue-600 text-white", // Blu per avviare laminazione
    "Laminazione": "bg-orange-500 hover:bg-orange-600 text-white", // Arancione per attesa cura
  }
  return colors[status] || "bg-gray-500 hover:bg-gray-600 text-white"
}

// Colore per pulsanti di rollback
const getRollbackButtonColor = () => "bg-gray-500 hover:bg-gray-600 text-white"

// Formatta la durata dal sistema tempo fasi
const formatDurataFase = (tempoFase: TempoFaseResponse | undefined): string => {
  if (!tempoFase) return "N/A"
  
  // Se la fase è completata, usa la durata calcolata
  if (tempoFase.durata_minuti !== null && tempoFase.durata_minuti !== undefined) {
    const minuti = tempoFase.durata_minuti
    if (minuti < 60) {
      return `${minuti}m`
    }
    const ore = Math.floor(minuti / 60)
    const min = minuti % 60
    return min > 0 ? `${ore}h ${min}m` : `${ore}h`
  }
  
  // Se la fase è in corso, calcola il tempo trascorso
  if (tempoFase.inizio_fase && !tempoFase.fine_fase) {
    const inizio = new Date(tempoFase.inizio_fase)
    const ora = new Date()
    const diffMs = ora.getTime() - inizio.getTime()
    const minuti = Math.floor(diffMs / (1000 * 60))
    
    if (minuti < 60) {
      return `${minuti}m`
    }
    const ore = Math.floor(minuti / 60)
    const min = minuti % 60
    return min > 0 ? `${ore}h ${min}m` : `${ore}h`
  }
  
  return "N/A"
}

export default function ProduzionePage() {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [tempoFasiMap, setTempoFasiMap] = useState<Record<number, TempoFaseResponse[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedODL, setSelectedODL] = useState<ODLResponse | null>(null)
  const [isAdvancing, setIsAdvancing] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [showRollbackDialog, setShowRollbackDialog] = useState(false)
  const [nextStatus, setNextStatus] = useState<"Laminazione" | "Attesa Cura" | null>(null)
  const [rollbackStatus, setRollbackStatus] = useState<"Preparazione" | "Laminazione" | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const { toast } = useStandardToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica solo ODL rilevanti per il Clean Room (Preparazione e Laminazione)
      const allOdl = await odlApi.fetchODLs()
      const relevantOdl = allOdl.filter(odl => 
        odl.status === "Preparazione" || odl.status === "Laminazione"
      )
      setOdlList(relevantOdl)
      
      // Carica i tempi fasi per ogni ODL
      const tempoFasiData: Record<number, TempoFaseResponse[]> = {}
      
      for (const odl of relevantOdl) {
        try {
          const tempoFasi = await phaseTimesApi.fetchPhaseTimes({ odl_id: odl.id })
          tempoFasiData[odl.id] = tempoFasi
        } catch (error) {
          console.error(`Errore nel caricamento tempo fasi per ODL ${odl.id}:`, error)
          tempoFasiData[odl.id] = []
        }
      }
      
      setTempoFasiMap(tempoFasiData)
      
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
    
    // Aggiornamento periodico del tempo ogni 30 secondi
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  // Filtra i dati in base alla ricerca migliorata
  const filteredOdl = odlList.filter(odl => {
    const searchLower = searchQuery.toLowerCase()
    return (
      // Ricerca per numero ODL
      odl.numero_odl?.toLowerCase()?.includes(searchLower) ||
      // Ricerca per part number
      odl.parte?.part_number?.toLowerCase()?.includes(searchLower) ||
      // Ricerca per descrizione breve
      odl.parte?.descrizione_breve?.toLowerCase()?.includes(searchLower) ||
      // Ricerca per ID ODL
      String(odl.id).includes(searchLower)
    )
  })

  // Separa gli ODL per stato
  const odlPreparazione = filteredOdl.filter(odl => odl.status === "Preparazione")
  const odlLaminazione = filteredOdl.filter(odl => odl.status === "Laminazione")

  // Ottieni il tempo della fase di preparazione per un ODL
  const getTempoPreparazione = (odlId: number): TempoFaseResponse | undefined => {
    const tempoFasi = tempoFasiMap[odlId] || []
    return tempoFasi.find(tf => tf.fase === "preparazione" && !tf.fine_fase)
  }

  // Ottieni il tempo della fase di laminazione per un ODL
  const getTempoLaminazione = (odlId: number): TempoFaseResponse | undefined => {
    const tempoFasi = tempoFasiMap[odlId] || []
    return tempoFasi.find(tf => tf.fase === "laminazione" && !tf.fine_fase)
  }

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

  // Determina lo stato precedente per rollback
  const getPreviousStatus = (currentStatus: string): "Preparazione" | "Laminazione" | null => {
    switch (currentStatus) {
      case "Laminazione":
        return "Preparazione"
      case "Attesa Cura":
        return "Laminazione"
      default:
        return null
    }
  }

  // Gestisce il cambio stato (avanzamento)
  const handleStatusChange = async (odl: ODLResponse, newStatus: "Laminazione" | "Attesa Cura") => {
    setIsAdvancing(true)
    try {
      await odlApi.updateStatusCleanRoom(odl.id, newStatus)
      
      toast({
        title: '✅ Stato aggiornato con successo',
        description: `ODL #${odl.numero_odl} è passato da "${odl.status}" a "${newStatus}"`,
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

  // Gestisce il rollback dello stato (compatibile con tempo fasi)
  const handleRollback = async (odl: ODLResponse, previousStatus: "Preparazione" | "Laminazione") => {
    setIsAdvancing(true)
    try {
      // Usa l'API admin che gestisce automaticamente il tempo fasi
      await odlApi.updateStatusAdmin(odl.id, previousStatus)
      
      toast({
        title: '🔄 Rollback completato',
        description: `ODL #${odl.numero_odl} è tornato da "${odl.status}" a "${previousStatus}"`,
      })
      
      // Ricarica i dati automaticamente
      await fetchData()
      
    } catch (error: any) {
      console.error('Errore nel rollback dello stato:', error)
      
      let errorMessage = 'Impossibile eseguire il rollback dello stato ODL.'
      
      if (error.response?.status === 404) {
        errorMessage = 'ODL non trovato. Potrebbe essere stato eliminato.'
      } else if (error.response?.status === 400) {
        errorMessage = error.response?.data?.detail || 'Rollback non consentito.'
      } else if (error.response?.status === 422) {
        errorMessage = 'Dati non validi per il rollback.'
      }
      
      toast({
        variant: 'destructive',
        title: '❌ Errore rollback',
        description: errorMessage,
      })
      
      await fetchData()
      
    } finally {
      setIsAdvancing(false)
      setShowRollbackDialog(false)
      setSelectedODL(null)
      setRollbackStatus(null)
    }
  }

  // Apre il dialog di conferma per avanzamento
  const openConfirmDialog = (odl: ODLResponse) => {
    const next = getNextStatus(odl.status)
    if (next) {
      setSelectedODL(odl)
      setNextStatus(next)
      setShowConfirmDialog(true)
    }
  }

  // Apre il dialog di conferma per rollback
  const openRollbackDialog = (odl: ODLResponse) => {
    const previous = getPreviousStatus(odl.status)
    if (previous) {
      setSelectedODL(odl)
      setRollbackStatus(previous)
      setShowRollbackDialog(true)
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

  // Ottiene il testo descrittivo per il rollback
  const getRollbackDescription = (currentStatus: string, previousStatus: string) => {
    const descriptions: Record<string, string> = {
      "Laminazione->Preparazione": "L'ODL tornerà dalla laminazione alla fase di preparazione. La fase di laminazione corrente verrà chiusa automaticamente.",
      "Attesa Cura->Laminazione": "L'ODL tornerà dall'attesa cura alla laminazione. Verrà riaperta una nuova fase di laminazione."
    }
    return descriptions[`${currentStatus}->${previousStatus}`] || "Rollback dello stato dell'ODL con gestione automatica delle fasi."
  }

  // Componente per la tabella degli ODL in Preparazione
  const PreparazioneTable = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play className="h-5 w-5 text-blue-500" />
          ODL in Preparazione ({odlPreparazione.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {odlPreparazione.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground px-6">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg font-medium">Nessun ODL in Preparazione</p>
            <p className="text-sm">Non ci sono ODL pronti per la laminazione al momento.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableCaption className="px-6">ODL pronti per avviare la laminazione</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24 px-3">ODL</TableHead>
                  <TableHead className="w-36 px-3">Part Number</TableHead>
                  <TableHead className="min-w-40 px-3">Descrizione</TableHead>
                  <TableHead className="w-36 px-3 hidden lg:table-cell">Tool</TableHead>
                  <TableHead className="w-32 px-3">Stato</TableHead>
                  <TableHead className="w-24 px-3 text-center">Tempo</TableHead>
                  <TableHead className="w-16 text-center px-2">Pr.</TableHead>
                  <TableHead className="w-40 text-center px-3">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlPreparazione.map(odl => (
                  <TableRow key={odl.id}>
                    <TableCell className="font-mono text-sm px-3 font-medium">
                      <div className="truncate" title={odl.numero_odl}>
                        {odl.numero_odl}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm px-3">
                      {odl.parte?.part_number ? (
                        <div className="text-foreground truncate" title={odl.parte.part_number}>
                          {odl.parte.part_number}
                        </div>
                      ) : (
                        <span className="text-red-500 font-medium text-sm">⚠️ N/A</span>
                      )}
                    </TableCell>
                    <TableCell className="px-3">
                      <div className="text-sm truncate" title={odl.parte?.descrizione_breve || "Descrizione non disponibile"}>
                        {odl.parte?.descrizione_breve ? (
                          <span className="text-foreground">{odl.parte.descrizione_breve}</span>
                        ) : (
                          <span className="text-red-500 font-medium">⚠️ N/A</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm px-3 hidden lg:table-cell">
                      {odl.tool?.part_number_tool ? (
                        <div className="text-foreground truncate" title={odl.tool.part_number_tool}>
                          {odl.tool.part_number_tool}
                        </div>
                      ) : (
                        <span className="text-red-500 font-medium text-sm">⚠️ N/A</span>
                      )}
                    </TableCell>
                    <TableCell className="px-3">
                      <Badge variant="secondary" className="text-sm px-3 py-1">
                        {odl.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center px-3">
                      <div className="flex items-center justify-center gap-1 text-sm font-mono">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-foreground font-medium" key={currentTime.getTime()}>
                          {formatDurataFase(getTempoPreparazione(odl.id))}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center px-2">
                      <Badge variant={odl.priorita > 5 ? "destructive" : odl.priorita > 3 ? "warning" : "secondary"} className="text-sm px-2 py-1">
                        {odl.priorita}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center px-3">
                      <Button
                        size="sm"
                        onClick={() => openConfirmDialog(odl)}
                        disabled={isAdvancing || !odl.parte || !odl.tool}
                        className={`flex items-center gap-2 w-full justify-center ${getButtonColor(odl.status)}`}
                        title={!odl.parte || !odl.tool ? "Dati ODL incompleti" : "Avvia Laminazione"}
                      >
                        {isAdvancing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <Play className="h-4 w-4" />
                            <span className="truncate">Laminazione</span>
                          </>
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )

  // Componente per la tabella degli ODL in Laminazione
  const LaminazioneTable = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timer className="h-5 w-5 text-green-500" />
          ODL in Laminazione ({odlLaminazione.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {odlLaminazione.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground px-6">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg font-medium">Nessun ODL in Laminazione</p>
            <p className="text-sm">Non ci sono ODL attualmente in laminazione.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableCaption className="px-6">ODL attualmente in laminazione con tempo trascorso dal sistema tempo fasi</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24 px-3">ODL</TableHead>
                  <TableHead className="w-36 px-3">Part Number</TableHead>
                  <TableHead className="min-w-40 px-3">Descrizione</TableHead>
                  <TableHead className="w-36 px-3 hidden lg:table-cell">Tool</TableHead>
                  <TableHead className="w-32 px-3">Stato</TableHead>
                  <TableHead className="w-24 px-3 text-center">Tempo</TableHead>
                  <TableHead className="w-16 text-center px-2">Pr.</TableHead>
                  <TableHead className="w-52 text-center px-3">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlLaminazione.map(odl => {
                  const tempoLaminazione = getTempoLaminazione(odl.id)
                  const previousStatus = getPreviousStatus(odl.status)
                  return (
                    <TableRow key={odl.id}>
                      <TableCell className="font-mono text-sm px-3 font-medium">
                        <div className="truncate" title={odl.numero_odl}>
                          {odl.numero_odl}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm px-3">
                        {odl.parte?.part_number ? (
                          <div className="text-foreground truncate" title={odl.parte.part_number}>
                            {odl.parte.part_number}
                          </div>
                        ) : (
                          <span className="text-red-500 font-medium text-sm">⚠️ N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="px-3">
                        <div className="text-sm truncate" title={odl.parte?.descrizione_breve || "Descrizione non disponibile"}>
                          {odl.parte?.descrizione_breve ? (
                            <span className="text-foreground">{odl.parte.descrizione_breve}</span>
                          ) : (
                            <span className="text-red-500 font-medium">⚠️ N/A</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm px-3 hidden lg:table-cell">
                        {odl.tool?.part_number_tool ? (
                          <div className="text-foreground truncate" title={odl.tool.part_number_tool}>
                            {odl.tool.part_number_tool}
                          </div>
                        ) : (
                          <span className="text-red-500 font-medium text-sm">⚠️ N/A</span>
                        )}
                      </TableCell>
                      <TableCell className="px-3">
                        <Badge variant="default" className="text-sm px-3 py-1">
                          {odl.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center px-3">
                        <div className="flex items-center justify-center gap-1 text-sm font-mono">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <span className="text-foreground font-medium" key={currentTime.getTime()}>
                            {formatDurataFase(tempoLaminazione)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center px-2">
                        <Badge variant={odl.priorita > 5 ? "destructive" : odl.priorita > 3 ? "warning" : "secondary"} className="text-sm px-2 py-1">
                          {odl.priorita}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center px-3">
                        <div className="flex gap-1">
                          {/* Pulsante Rollback */}
                          {previousStatus && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openRollbackDialog(odl)}
                              disabled={isAdvancing}
                              className={`flex items-center gap-1 ${getRollbackButtonColor()}`}
                              title={`Torna a ${previousStatus}`}
                            >
                              <Undo2 className="h-3 w-3" />
                            </Button>
                          )}
                          
                          {/* Pulsante Avanzamento */}
                          <Button
                            size="sm"
                            onClick={() => openConfirmDialog(odl)}
                            disabled={isAdvancing || !odl.parte || !odl.tool}
                            className={`flex items-center gap-2 flex-1 justify-center ${getButtonColor(odl.status)}`}
                            title={!odl.parte || !odl.tool ? "Dati ODL incompleti" : "Completa Laminazione"}
                          >
                            {isAdvancing ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <CheckCircle className="h-4 w-4" />
                                <span className="truncate">Attesa Cura</span>
                              </>
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )

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

      {/* Filtro di ricerca migliorato */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca per ODL, Part Number o Descrizione..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <div className="flex gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">Preparazione: {odlPreparazione.length}</Badge>
          <Badge variant="default">Laminazione: {odlLaminazione.length}</Badge>
        </div>
      </div>

      {/* Contenuto principale */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento ODL e tempi fasi...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Tabella ODL in Preparazione */}
          <PreparazioneTable />
          
          {/* Tabella ODL in Laminazione */}
          <LaminazioneTable />
        </div>
      )}

      {/* Dialog di conferma per avanzamento */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conferma Avanzamento ODL</DialogTitle>
            <DialogDescription>
              Stai per far avanzare l'ODL {selectedODL?.numero_odl} dallo stato "{selectedODL?.status}" a "{nextStatus}".
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

      {/* Dialog di conferma per rollback */}
      <Dialog open={showRollbackDialog} onOpenChange={setShowRollbackDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-500" />
              Conferma Rollback ODL
            </DialogTitle>
            <DialogDescription>
              Stai per fare il rollback dell'ODL {selectedODL?.numero_odl} dallo stato "{selectedODL?.status}" a "{rollbackStatus}".
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
            
            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-4 w-4 text-orange-600" />
                <p className="text-sm font-medium text-orange-800">Attenzione: Operazione di rollback</p>
              </div>
              <p className="text-sm text-orange-700">
                {selectedODL && rollbackStatus && getRollbackDescription(selectedODL.status, rollbackStatus)}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRollbackDialog(false)}>
              Annulla
            </Button>
            <Button 
              variant="destructive"
              onClick={() => selectedODL && rollbackStatus && handleRollback(selectedODL, rollbackStatus)}
              disabled={isAdvancing}
            >
              {isAdvancing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Rollback...
                </>
              ) : (
                <>
                  <Undo2 className="mr-2 h-4 w-4" />
                  Conferma Rollback
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 