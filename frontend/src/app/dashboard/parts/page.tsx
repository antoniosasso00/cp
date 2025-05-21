'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ParteResponse, partiApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import ParteModal from './components/parte-modal'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2,
  Plus
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useQuery, useQueryClient } from '@tanstack/react-query'
import debounce from 'lodash.debounce'
import Link from 'next/link'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

export default function PartiPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ParteResponse | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [itemToDelete, setItemToDelete] = useState<ParteResponse | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const {
    data: parti = [],
    isLoading,
    isError
  } = useQuery<ParteResponse[], Error>({
    queryKey: ['parti'],
    queryFn: () => partiApi.getAll()
  })

  const handleCreateClick = () => {
    setSelectedItem(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item: ParteResponse) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleDeleteClick = (item: ParteResponse) => {
    setItemToDelete(item)
    setIsDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!itemToDelete) return

    try {
      await partiApi.delete(itemToDelete.id)
      toast({
        variant: 'success',
        title: 'Parte eliminata',
        description: `Parte #${itemToDelete.id} eliminata con successo.`,
      })
      queryClient.invalidateQueries({ queryKey: ['parti'] })
    } catch (error) {
      console.error('Errore nell\'eliminazione della parte:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare la parte. Riprova più tardi.',
      })
    } finally {
      setIsDeleteDialogOpen(false)
      setItemToDelete(null)
    }
  }

  const handleModalSuccess = () => {
    setIsModalOpen(false)
    setSelectedItem(null)
    queryClient.invalidateQueries({ queryKey: ['parti'] })
  }

  // Filtra le parti in base alla ricerca
  const filteredParti = parti.filter(parte => {
    const searchLower = searchQuery.toLowerCase()
    return (
      parte.part_number.toLowerCase().includes(searchLower) ||
      parte.descrizione_breve.toLowerCase().includes(searchLower)
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Parti</h1>
          <p className="text-muted-foreground">
            Gestisci le parti in produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>
          <Plus className="mr-2 h-4 w-4" />
          Nuova Parte
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nelle parti..."
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
          Errore nel caricamento delle parti.
        </div>
      ) : (
        <Table>
          <TableCaption>Lista delle parti in produzione</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Part Number</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Valvole</TableHead>
              <TableHead>Tools</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredParti.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Nessuna parte trovata
                </TableCell>
              </TableRow>
            ) : (
              filteredParti.map(parte => (
                <TableRow key={parte.id}>
                  <TableCell>{parte.id}</TableCell>
                  <TableCell>{parte.part_number}</TableCell>
                  <TableCell>{parte.descrizione_breve}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant="outline">
                      {parte.num_valvole_richieste}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {parte.tools && parte.tools.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {parte.tools.map(tool => (
                          <Badge key={tool.id} variant="secondary">
                            {tool.codice}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">Nessun tool</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/dashboard/parts/${parte.id}`}>
                            Dettagli
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleEditClick(parte)}>
                          Modifica
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(parte)}
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
      )}

      {/* Modal per creazione/modifica parte */}
      <ParteModal
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
              Sei sicuro di voler eliminare la parte #{itemToDelete?.id}?
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