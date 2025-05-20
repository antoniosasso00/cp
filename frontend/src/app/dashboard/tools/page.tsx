'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { toolApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'

interface ToolResponse {
  id: number
  codice: string
  descrizione?: string
  num_cavita: number
  posizione_magazzino?: string
  stato: 'disponibile' | 'in_uso' | 'manutenzione'
  created_at: string
  updated_at: string
}

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{stato?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ToolResponse | null>(null)
  const { toast } = useToast()

  const fetchTools = async () => {
    try {
      setIsLoading(true)
      const data = await toolApi.getAll()
      setTools(data as ToolResponse[])
    } catch (error) {
      console.error('Errore nel caricamento dei tools:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i tools. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTools()
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ToolResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare il tool con ID ${id}?`)) {
      return
    }

    try {
      // Qui andrebbe la funzione di delete
      // await toolApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `Tool con ID ${id} eliminato con successo.`,
      })
      fetchTools()
    } catch (error) {
      console.error(`Errore durante l'eliminazione del tool ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare il tool con ID ${id}. Potrebbe essere assegnato a una parte.`,
      })
    }
  }

  const filteredTools = tools.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    const matchesSearch = 
      item.codice.toLowerCase().includes(searchLower) ||
      (item.descrizione?.toLowerCase().includes(searchLower) || false) ||
      (item.posizione_magazzino?.toLowerCase().includes(searchLower) || false)
    
    // Applica filtro per stato se impostato
    const matchesFilter = !filter.stato || item.stato === filter.stato
    
    return matchesSearch && matchesFilter
  })

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'disponibile': return 'success'
      case 'in_uso': return 'secondary'
      case 'manutenzione': return 'destructive'
      default: return 'outline'
    }
  }

  const getStatoLabel = (stato: string) => {
    switch (stato) {
      case 'disponibile': return 'Disponibile'
      case 'in_uso': return 'In Uso'
      case 'manutenzione': return 'In Manutenzione'
      default: return stato
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
          <p className="text-muted-foreground">
            Gestisci i tools disponibili per la produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo Tool</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei tools..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        
        <div className="flex flex-wrap gap-2">
          <select 
            className="px-3 py-2 rounded-md border text-sm"
            value={filter.stato || ''}
            onChange={e => setFilter({stato: e.target.value || undefined})}
          >
            <option value="">Tutti gli stati</option>
            <option value="disponibile">Disponibili</option>
            <option value="in_uso">In Uso</option>
            <option value="manutenzione">In Manutenzione</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <p>Caricamento in corso...</p>
        </div>
      ) : (
        <Table>
          <TableCaption>Lista dei tools disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Codice</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Cavità</TableHead>
              <TableHead>Posizione</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTools.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  Nessun tool trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredTools.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.id}</TableCell>
                  <TableCell>{item.codice}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione || '-'}</TableCell>
                  <TableCell className="text-center">{item.num_cavita}</TableCell>
                  <TableCell>{item.posizione_magazzino || '-'}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant={getStatoBadgeVariant(item.stato)}>
                      {getStatoLabel(item.stato)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEditClick(item)}>
                        Modifica
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteClick(item.id)}>
                        Elimina
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}

      {/* Placeholder per la modale */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingItem ? 'Modifica Tool' : 'Nuovo Tool'}
            </h2>
            <p className="text-gray-500 mb-4">Implementazione modale in corso...</p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setModalOpen(false)}>Chiudi</Button>
              <Button onClick={() => setModalOpen(false)}>Salva</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 