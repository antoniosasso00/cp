'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { toolApi } from '@/lib/api'
import { ToolModal } from './components/tool-modal'
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
import Link from 'next/link'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface Tool {
  id: number
  codice: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  disponibile: boolean
}

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<Tool | null>(null)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [itemToDelete, setItemToDelete] = useState<Tool | null>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const {
    data: tools = [],
    isLoading,
    isError
  } = useQuery<Tool[], Error>({
    queryKey: ['tools'],
    queryFn: () => toolApi.getAll()
  })

  const handleCreateClick = () => {
    setSelectedItem(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item: Tool) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleDeleteClick = (item: Tool) => {
    setItemToDelete(item)
    setIsDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!itemToDelete) return

    try {
      await toolApi.delete(itemToDelete.id)
      toast({
        variant: 'success',
        title: 'Tool eliminato',
        description: `Tool #${itemToDelete.id} eliminato con successo.`,
      })
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    } catch (error) {
      console.error('Errore nell\'eliminazione del tool:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare il tool. Riprova più tardi.',
      })
    } finally {
      setIsDeleteDialogOpen(false)
      setItemToDelete(null)
    }
  }

  const handleModalSuccess = () => {
    setIsModalOpen(false)
    setSelectedItem(null)
    queryClient.invalidateQueries({ queryKey: ['tools'] })
  }

  // Filtra i tools in base alla ricerca
  const filteredTools = tools.filter(tool => {
    const searchLower = searchQuery.toLowerCase()
    return (
      tool.codice.toLowerCase().includes(searchLower) ||
      (tool.descrizione && tool.descrizione.toLowerCase().includes(searchLower))
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tools/Stampi</h1>
          <p className="text-muted-foreground">
            Gestisci i tools e gli stampi disponibili
          </p>
        </div>
        <Button onClick={handleCreateClick}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Tool
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei tools..."
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
          Errore nel caricamento dei tools.
        </div>
      ) : (
        <Table>
          <TableCaption>Lista dei tools disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Codice</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Dimensioni (mm)</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTools.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  Nessun tool trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredTools.map(tool => (
                <TableRow key={tool.id}>
                  <TableCell>{tool.codice}</TableCell>
                  <TableCell>{tool.descrizione || '-'}</TableCell>
                  <TableCell className="text-center">
                    {tool.lunghezza_piano} x {tool.larghezza_piano}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={tool.disponibile ? "success" : "destructive"}>
                      {tool.disponibile ? "Disponibile" : "Non disponibile"}
                    </Badge>
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
                          <Link href={`/dashboard/tools/${tool.id}`}>
                            Dettagli
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleEditClick(tool)}>
                          Modifica
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(tool)}
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

      {/* Modal per creazione/modifica tool */}
      <ToolModal
        open={isModalOpen}
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
              Sei sicuro di voler eliminare il tool #{itemToDelete?.id}?
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