'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ODLResponse, odlApi, tempoFasiApi, TempoFaseResponse } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { 
  Loader2, 
  MoreHorizontal, 
  Play,
  Square,
  ListFilter,
  Activity,
  Clock,
  ChevronLeft,
  RefreshCw
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose
} from "@/components/ui/dialog"
import Link from 'next/link'

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "default",
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

// Mappa degli stati ODL per l'avanzamento fase
const STATI_ODL = ["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito"]

// Mappa stato a fase
const STATO_A_FASE: Record<string, "laminazione" | "attesa_cura" | "cura"> = {
  "Laminazione": "laminazione",
  "Attesa Cura": "attesa_cura",
  "Cura": "cura"
}

// Funzione per calcolare la durata
const calcolaDurata = (inizio: string, fine?: string | null) => {
  const inizioDate = new Date(inizio)
  const fineDate = fine ? new Date(fine) : new Date()
  const diffMinuti = Math.floor((fineDate.getTime() - inizioDate.getTime()) / (1000 * 60))
  
  if (diffMinuti < 60) {
    return `${diffMinuti} min`
  } else {
    const ore = Math.floor(diffMinuti / 60)
    const minuti = diffMinuti % 60
    return `${ore}h ${minuti}m`
  }
}

export default function MonitoraggioODLPage() {
  const [odls, setODLs] = useState<ODLResponse[]>([])
  const [odlsFiniti, setODLsFiniti] = useState<ODLResponse[]>([])
  const [tempiFasi, setTempiFasi] = useState<Record<number, TempoFaseResponse[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{parte_id?: number, tool_id?: number, status?: string}>({})
  const [advanceDialogOpen, setAdvanceDialogOpen] = useState(false)
  const [odlToAdvance, setOdlToAdvance] = useState<ODLResponse | null>(null)
  const [processingAdvance, setProcessingAdvance] = useState(false)
  const { toast } = useToast()

  const fetchODLs = async () => {
    try {
      setIsLoading(true)
      const data = await odlApi.getAll(filter)
      
      // Separa gli ODL in corso da quelli finiti
      const odlAttivi = data.filter(odl => odl.status !== "Finito")
      const odlFiniti = data.filter(odl => odl.status === "Finito")
      
      setODLs(odlAttivi)
      setODLsFiniti(odlFiniti)
      
      // Carica i tempi delle fasi per ogni ODL
      const tempiFasiData: Record<number, TempoFaseResponse[]> = {}
      for (const odl of data) {
        try {
          const fasi = await tempoFasiApi.getAll({ odl_id: odl.id })
          tempiFasiData[odl.id] = fasi
        } catch (error) {
          console.warn(`Errore nel caricamento delle fasi per ODL ${odl.id}:`, error)
          tempiFasiData[odl.id] = []
        }
      }
      setTempiFasi(tempiFasiData)
    } catch (error) {
      console.error('Errore nel caricamento degli ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare gli ordini di lavoro. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchODLs()
  }, [filter])

  const handleAdvanceClick = (item: ODLResponse) => {
    setOdlToAdvance(item)
    setAdvanceDialogOpen(true)
  }
  
  const advanceODLStatus = async () => {
    if (!odlToAdvance) return
    
    // Determina il prossimo stato
    const currentIndex = STATI_ODL.indexOf(odlToAdvance.status)
    if (currentIndex === -1 || currentIndex === STATI_ODL.length - 1) {
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile avanzare lo stato: stato attuale non valido o già finale.',
      })
      return
    }
    
    const nextStatus = STATI_ODL[currentIndex + 1] as "Preparazione" | "Laminazione" | "Attesa Cura" | "Cura" | "Finito"
    
    try {
      setProcessingAdvance(true)
      
      // 1. Chiudi la fase corrente se esiste
      if (odlToAdvance.status in STATO_A_FASE) {
        const currentFase = STATO_A_FASE[odlToAdvance.status as keyof typeof STATO_A_FASE]
        
        // Recupera la fase attuale non completata
        const tempiFasiResponse = await tempoFasiApi.getAll({
          odl_id: odlToAdvance.id,
          fase: currentFase
        })
        
        const faseAttiva = tempiFasiResponse.find(fase => fase.fine_fase === null)
        
        if (faseAttiva) {
          // Chiudi la fase corrente
          await tempoFasiApi.update(faseAttiva.id, {
            fine_fase: new Date().toISOString()
          })
        }
      }
      
      // 2. Aggiorna lo stato dell'ODL usando la nuova funzione generica
              await odlApi.updateStatus(odlToAdvance.id, nextStatus)
      
      // 3. Crea una nuova fase se il nuovo stato è monitorato
      if (nextStatus in STATO_A_FASE) {
        const nuovaFase = STATO_A_FASE[nextStatus as keyof typeof STATO_A_FASE]
        
        await tempoFasiApi.create({
          odl_id: odlToAdvance.id,
          fase: nuovaFase,
          inizio_fase: new Date().toISOString(),
          note: `Fase ${nuovaFase} iniziata automaticamente`
        })
      }
      
      toast({
        title: 'Stato aggiornato',
        description: `ODL ${odlToAdvance.id} avanzato a "${nextStatus}"`,
      })
      
      // Ricarica i dati
      fetchODLs()
      setAdvanceDialogOpen(false)
      setOdlToAdvance(null)
    } catch (error) {
      console.error('Errore durante l\'avanzamento dello stato:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile avanzare lo stato dell\'ODL. Riprova più tardi.',
      })
    } finally {
      setProcessingAdvance(false)
    }
  }

  const filterODLs = (items: ODLResponse[], query: string) => {
    if (!query) return items
    
    const searchLower = query.toLowerCase()
    return items.filter(item => (
      item.id.toString().includes(searchLower) ||
      item.parte.part_number.toLowerCase().includes(searchLower) ||
      item.tool.part_number_tool.toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    ))
  }
  
  const filteredODLs = filterODLs(odls, searchQuery)
  const filteredODLsFiniti = filterODLs(odlsFiniti, searchQuery)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link href="/dashboard/shared/odl">
              <Button variant="ghost" size="sm" className="flex items-center gap-2">
                <ChevronLeft className="h-4 w-4" />
                Torna agli ODL
              </Button>
            </Link>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio ODL</h1>
          <p className="text-muted-foreground">
            Monitora lo stato in tempo reale degli ordini di lavoro e gestisci l'avanzamento delle fasi
          </p>
        </div>
        <Button onClick={fetchODLs} variant="outline" className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Aggiorna
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full max-w-sm">
          <ListFilter className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Cerca negli ODL..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5" />
              ODL in Produzione
            </h2>
            <Table>
              <TableCaption>Ordini di lavoro attualmente in produzione</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead className="text-center">Priorità</TableHead>
                  <TableHead className="text-center">Stato</TableHead>
                  <TableHead>Fase Attuale</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead className="text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredODLs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      Nessun ordine di lavoro in produzione trovato
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredODLs.map(item => {
                    const fasiODL = tempiFasi[item.id] || []
                    const faseAttiva = fasiODL.find(fase => fase.fine_fase === null)
                    
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.id}</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span>{item.parte.part_number}</span>
                            <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                              {item.parte.descrizione_breve}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{item.tool.part_number_tool}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant={item.priorita > 5 ? "destructive" : (item.priorita > 2 ? "warning" : "secondary")}>
                            {item.priorita}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant={getStatusBadgeVariant(item.status)}>
                            {item.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {faseAttiva ? (
                            <div className="flex flex-col gap-1">
                              <div className="flex items-center gap-2">
                                <Clock className="h-3 w-3 text-blue-600" />
                                <span className="text-sm font-medium">{faseAttiva.fase}</span>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                Durata: {calcolaDurata(faseAttiva.inizio_fase, faseAttiva.fine_fase)}
                              </span>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {item.note || '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleAdvanceClick(item)}
                              disabled={item.status === "Finito"}
                              className="flex items-center gap-1"
                            >
                              <Play className="h-3 w-3" />
                              Avanza
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>
          
          <Accordion type="single" collapsible className="border rounded-md">
            <AccordionItem value="finished-odl">
              <AccordionTrigger className="px-4">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-semibold">Storico ODL Completati</h2>
                  <Badge variant="outline">
                    {filteredODLsFiniti.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4">
                  {filteredODLsFiniti.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      Nessun ordine di lavoro completato trovato
                    </div>
                  ) : (
                    filteredODLsFiniti.map(item => {
                      const fasiODL = tempiFasi[item.id] || []
                      
                      return (
                        <div key={item.id} className="border rounded-lg p-4 space-y-3">
                          <div className="flex justify-between items-start">
                            <div>
                              <h3 className="font-semibold">ODL #{item.id} - {item.parte.part_number}</h3>
                              <p className="text-sm text-muted-foreground">{item.parte.descrizione_breve}</p>
                              <p className="text-sm text-muted-foreground">Tool: {item.tool.part_number_tool}</p>
                            </div>
                            <Badge variant={getStatusBadgeVariant(item.status)}>
                              {item.status}
                            </Badge>
                          </div>
                          
                          {fasiODL.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium mb-2">Storico Fasi:</h4>
                              <div className="space-y-2">
                                {fasiODL.map(fase => (
                                  <div key={fase.id} className="flex justify-between items-center text-sm p-2 bg-muted rounded">
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium capitalize">{fase.fase.replace('_', ' ')}</span>
                                      {fase.fine_fase ? (
                                        <Square className="h-3 w-3 text-gray-600" />
                                      ) : (
                                        <Activity className="h-3 w-3 text-blue-600" />
                                      )}
                                    </div>
                                    <div className="text-muted-foreground">
                                      <span>{formatDateIT(fase.inizio_fase)}</span>
                                      {fase.fine_fase && (
                                        <>
                                          <span> → {formatDateIT(fase.fine_fase)}</span>
                                          <span className="ml-2 font-medium">
                                            ({calcolaDurata(fase.inizio_fase, fase.fine_fase)})
                                          </span>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      )}
      
      <Dialog open={advanceDialogOpen} onOpenChange={setAdvanceDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Avanza Fase ODL</DialogTitle>
            <DialogDescription>
              {odlToAdvance && (
                <>
                  Vuoi avanzare l'ODL #{odlToAdvance.id} ({odlToAdvance.parte.part_number}) 
                  dallo stato <Badge variant={getStatusBadgeVariant(odlToAdvance.status)}>{odlToAdvance.status}</Badge> a{' '}
                  <Badge variant={getStatusBadgeVariant(STATI_ODL[STATI_ODL.indexOf(odlToAdvance.status) + 1])}>
                    {STATI_ODL[STATI_ODL.indexOf(odlToAdvance.status) + 1]}
                  </Badge>?
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Annulla</Button>
            </DialogClose>
            <Button 
              onClick={advanceODLStatus} 
              disabled={processingAdvance}
            >
              {processingAdvance && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Conferma
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 