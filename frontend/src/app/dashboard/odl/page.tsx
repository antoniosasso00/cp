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
  ListFilter,
  Plus
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
import { useQuery, useQueryClient } from '@tanstack/react-query'
import debounce from 'lodash.debounce'
import Link from 'next/link'

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
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ODLResponse | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [itemToDelete, setItemToDelete] = useState<ODLResponse | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const {
    data: odls = [],
    isLoading,
    isError
  } = useQuery<ODLResponse[], Error>({
    queryKey: ['odl'],
    queryFn: () => odlApi.getAll()
  })

  const handleCreateClick = () => {
    setSelectedItem(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item: ODLResponse) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleDeleteClick = (item: ODLResponse) => {
    setItemToDelete(item)
    setIsDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!itemToDelete) return

    try {
      await odlApi.delete(itemToDelete.id)
      toast({
        variant: 'success',
        title: 'ODL eliminato',
        description: `ODL #${itemToDelete.id} eliminato con successo.`,
      })
      queryClient.invalidateQueries({ queryKey: ['odl'] })
    } catch (error) {
      console.error('Errore nell\'eliminazione dell\'ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare l\'ODL. Riprova più tardi.',
      })
    } finally {
      setIsDeleteDialogOpen(false)
      setItemToDelete(null)
    }
  }

  const handleModalSuccess = () => {
    setIsModalOpen(false)
    setSelectedItem(null)
    queryClient.invalidateQueries({ queryKey: ['odl'] })
  }

  // Filtra gli ODL in base alla ricerca
  const filteredODLs = odls.filter(odl => {
    const searchLower = searchQuery.toLowerCase()
    return (
      odl.parte.part_number.toLowerCase().includes(searchLower) ||
      odl.tool.codice.toLowerCase().includes(searchLower) ||
      (odl.note && odl.note.toLowerCase().includes(searchLower))
    )
  })

  // Separa gli ODL attivi da quelli completati
  const activeODLs = filteredODLs.filter(odl => odl.status !== "Finito")
  const finishedODLs = filteredODLs.filter(odl => odl.status === "Finito")

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ordini di Lavoro</h1>
          <p className="text-muted-foreground">
            Gestisci gli ordini di lavoro in produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo ODL
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca negli ODL..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : isError ? (
        <div className="text-center text-destructive py-8">
          Errore nel caricamento degli ODL.
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
                {activeODLs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      Nessun ODL attivo trovato
                    </TableCell>
                  </TableRow>
                ) : (
                  activeODLs.map(odl => (
                    <TableRow key={odl.id}>
                      <TableCell>{odl.id}</TableCell>
                      <TableCell>{odl.parte.part_number}</TableCell>
                      <TableCell>{odl.tool.codice}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline">Priorità: {odl.priorita}</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant={getStatusBadgeVariant(odl.status)}>
                          {odl.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{odl.note || '-'}</TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link href={`/dashboard/odl/${odl.id}`}>
                                Dettagli
                              </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleEditClick(odl)}>
                              Modifica
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDeleteClick(odl)}
                              className="text-destructive"
                            >
                              Elimina
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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
                    {finishedODLs.length}
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
                    {finishedODLs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8">
                          Nessun ODL completato trovato
                        </TableCell>
                      </TableRow>
                    ) : (
                      finishedODLs.map(odl => (
                        <TableRow key={odl.id}>
                          <TableCell>{odl.id}</TableCell>
                          <TableCell>{odl.parte.part_number}</TableCell>
                          <TableCell>{odl.tool.codice}</TableCell>
                          <TableCell className="text-center">
                            <Badge variant="outline">Priorità: {odl.priorita}</Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant={getStatusBadgeVariant(odl.status)}>
                              {odl.status}
                            </Badge>
                          </TableCell>
                          <TableCell>{odl.note || '-'}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem asChild>
                                  <Link href={`/dashboard/odl/${odl.id}`}>
                                    Dettagli
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleEditClick(odl)}>
                                  Modifica
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleDeleteClick(odl)}
                                  className="text-destructive"
                                >
                                  Elimina
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

      {/* Modal per creazione/modifica ODL */}
      <ODLModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        item={selectedItem}
        onSuccess={handleModalSuccess}
      />

      {/* Dialog di conferma eliminazione */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conferma eliminazione</DialogTitle>
            <DialogDescription>
              Sei sicuro di voler eliminare l'ODL #{itemToDelete?.id}?
              Questa azione non può essere annullata.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Annulla
            </Button>
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              Elimina
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 