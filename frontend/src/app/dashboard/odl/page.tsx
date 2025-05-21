'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ODLResponse, odlApi, tempoFasiApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import ODLModal from './components/odl-modal'
import { 
  CalendarClock, 
  Settings, 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2,
  ChevronDown,
  Play,
  ListFilter
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
  DialogTrigger,
  DialogClose
} from "@/components/ui/dialog"

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "primary" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "primary",
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

export default function ODLPage() {
  const [odls, setODLs] = useState<ODLResponse[]>([])
  const [odlsFiniti, setODLsFiniti] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{parte_id?: number, tool_id?: number, status?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ODLResponse | null>(null)
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

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ODLResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare l'ODL con ID ${id}?`)) {
      return
    }

    try {
      await odlApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `ODL con ID ${id} eliminato con successo.`,
      })
      fetchODLs()
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'ODL ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare l'ODL con ID ${id}.`,
      })
    }
  }
  
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
      
      // 2. Aggiorna lo stato dell'ODL
      await odlApi.update(odlToAdvance.id, {
        status: nextStatus
      })
      
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
      item.tool.codice.toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    ))
  }
  
  const filteredODLs = filterODLs(odls, searchQuery)
  const filteredODLsFiniti = filterODLs(odlsFiniti, searchQuery)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ordini di Lavoro</h1>
          <p className="text-muted-foreground">
            Gestisci gli ordini di lavoro in produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo ODL</Button>
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
            <h2 className="text-xl font-semibold mb-4">ODL Attivi</h2>
            <Table>
              <TableCaption>Lista degli ordini di lavoro in produzione</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Part Number</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead className="text-center">Priorità</TableHead>
                  <TableHead className="text-center">Stato</TableHead>
                  <TableHead>Note</TableHead>
                  <TableHead className="text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredODLs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      Nessun ordine di lavoro attivo trovato
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredODLs.map(item => (
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
                      <TableCell>{item.tool.codice}</TableCell>
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
                      <TableCell className="max-w-[200px] truncate">
                        {item.note || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end">
                          <Button 
                            variant="outline" 
                            size="icon"
                            className="mr-2"
                            onClick={() => handleAdvanceClick(item)}
                            disabled={item.status === "Finito"}
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleEditClick(item)}>
                                <Pencil className="mr-2 h-4 w-4" />
                                <span>Modifica</span>
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                onClick={() => handleDeleteClick(item.id)}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                <span>Elimina</span>
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
          
          <Accordion type="single" collapsible className="border rounded-md">
            <AccordionItem value="finished-odl">
              <AccordionTrigger className="px-4">
                <div className="flex items-center">
                  <h2 className="text-xl font-semibold">Storico ODL Completati</h2>
                  <Badge variant="outline" className="ml-2">
                    {filteredODLsFiniti.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Tool</TableHead>
                      <TableHead className="text-center">Priorità</TableHead>
                      <TableHead className="text-center">Stato</TableHead>
                      <TableHead>Note</TableHead>
                      <TableHead className="text-right">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredODLsFiniti.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-4">
                          Nessun ordine di lavoro completato trovato
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredODLsFiniti.map(item => (
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
                          <TableCell>{item.tool.codice}</TableCell>
                          <TableCell className="text-center">
                            <Badge variant="outline">
                              {item.priorita}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant={getStatusBadgeVariant(item.status)}>
                              {item.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate">
                            {item.note || '-'}
                          </TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleEditClick(item)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  <span>Dettagli</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleDeleteClick(item.id)}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  <span>Elimina</span>
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      )}

      <ODLModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        onSuccess={() => {
          fetchODLs()
          setModalOpen(false)
        }}
      />
      
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