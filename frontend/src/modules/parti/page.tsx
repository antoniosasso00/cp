'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useCrudToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ParteResponse, partsApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import ParteModal from './components/parte-modal'
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

export default function PartiPage() {
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{part_number?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ParteResponse | null>(null)
  const router = useRouter()
  const crud = useCrudToast()

  const loadData = async () => {
    try {
      setIsLoading(true)
      const data = await partsApi.fetchParts(filter)
      setParti(data)
    } catch (error) {
      console.error('Errore nel caricamento delle parti:', error)
      crud.error('Caricamento', 'parti', undefined, 'Verificare la connessione')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ParteResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  // ✅ FIX: Funzione per chiudere modal con refresh completo della pagina
  const handleModalClose = () => {
    setModalOpen(false)
    // Refresh completo ma gentile che preserva lo stato React
    router.refresh()
    // Reload dei dati per assicurarsi che siano aggiornati
    setTimeout(() => loadData(), 100)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questa parte?')) {
      return
    }

    try {
      await partsApi.deletePart(id)
      crud.success('Eliminazione', 'parte', id)
      loadData()
    } catch (error) {
      console.error('Errore durante l\'eliminazione della parte:', error)
      crud.error('Eliminazione', 'parte', id)
    }
  }

  const filteredParti = parti.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number.toLowerCase().includes(searchLower) ||
      item.descrizione_breve.toLowerCase().includes(searchLower)
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
        <Button onClick={handleCreateClick}>Nuova Parte</Button>
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
      ) : (
        <Table>
          <TableCaption>Lista delle parti in produzione</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Part Number</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Valvole</TableHead>
              <TableHead>Ciclo di Cura</TableHead>
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
              filteredParti.map(item => (
                <TableRow key={item.id}>
                  <TableCell>{item.part_number}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione_breve}</TableCell>
                  <TableCell className="text-center">
                    {item.num_valvole_richieste}
                  </TableCell>
                  <TableCell>
                    {item.ciclo_cura ? (
                      <Badge variant="outline">
                        {item.ciclo_cura.nome}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {item.tools.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {item.tools.map(tool => (
                          <Badge key={tool.id} variant="secondary" className="mr-1">
                            {tool.part_number_tool}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      '-'
                    )}
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

      <ParteModal 
        isOpen={modalOpen} 
        onClose={handleModalClose}
        item={editingItem} 
        onSuccess={() => {
          loadData()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 