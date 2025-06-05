'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { AutoclaveModal } from './components/autoclave-modal'
import { autoclavesApi, type Autoclave } from '@/lib/api'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2 
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function AutoclaviPage() {
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Autoclave | null>(null)
  const { toast } = useToast()

  const fetchAutoclavi = async () => {
    try {
      setIsLoading(true)
      const data = await autoclavesApi.fetchAutoclaves()
      setAutoclavi(data)
    } catch (error) {
      console.error('Errore nel caricamento delle autoclavi:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare le autoclavi. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchAutoclavi()
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: Autoclave) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa autoclave?')) {
      return
    }

    try {
      await autoclavesApi.deleteAutoclave(id)
      
      toast({
        variant: 'success',
        title: 'Autoclave eliminata',
        description: 'L\'autoclave è stata eliminata con successo.',
      })
      fetchAutoclavi()
    } catch (error) {
      console.error('Errore durante l\'eliminazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare l\'autoclave. Potrebbe essere in uso.',
      })
    }
  }

  const filteredAutoclavi = autoclavi.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.nome.toLowerCase().includes(searchLower) ||
      item.codice.toLowerCase().includes(searchLower) ||
      (item.produttore?.toLowerCase().includes(searchLower) || false)
    )
  })

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'DISPONIBILE': return 'success'
      case 'IN_USO': return 'secondary'
      case 'GUASTO': return 'destructive'
      case 'MANUTENZIONE': return 'warning'
      case 'SPENTA': return 'outline'
      default: return 'outline'
    }
  }

  const getStatoLabel = (stato: string) => {
    switch (stato) {
      case 'DISPONIBILE': return 'Disponibile'
      case 'IN_USO': return 'In Uso'
      case 'GUASTO': return 'Guasto'
      case 'MANUTENZIONE': return 'In Manutenzione'
      case 'SPENTA': return 'Spenta'
      default: return stato
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Autoclavi</h1>
          <p className="text-muted-foreground">
            Gestisci le autoclavi disponibili
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuova Autoclave</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nelle autoclavi..."
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
      ) : (
        <Table>
          <TableCaption>Lista delle autoclavi disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Codice</TableHead>
              <TableHead className="text-center">Dimensioni (mm)</TableHead>
              <TableHead className="text-center">Linee Vuoto</TableHead>
              <TableHead>Produttore</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAutoclavi.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  Nessuna autoclave trovata
                </TableCell>
              </TableRow>
            ) : (
              filteredAutoclavi.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.nome}</TableCell>
                  <TableCell>{item.codice}</TableCell>
                  <TableCell className="text-center">
                    {item.lunghezza} x {item.larghezza_piano}
                  </TableCell>
                  <TableCell className="text-center">{item.num_linee_vuoto}</TableCell>
                  <TableCell>{item.produttore || '-'}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant={getStatoBadgeVariant(item.stato)}>
                      {getStatoLabel(item.stato)}
                    </Badge>
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
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}

      <AutoclaveModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={fetchAutoclavi}
      />
    </div>
  )
} 