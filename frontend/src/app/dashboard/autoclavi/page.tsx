'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { formatDateIT } from '@/lib/utils'

interface AutoclaveResponse {
  id: number
  codice: string
  descrizione?: string
  dimensioni: string
  capacita_kg: number
  stato: 'operativa' | 'ferma' | 'manutenzione'
  posizione: string
  created_at: string
  updated_at: string
}

// API placeholder in assenza di un'API reale per le autoclavi
const autoclaveApi = {
  getAll: async () => {
    // Dati di esempio
    return [
      {
        id: 1,
        codice: 'AUTO-001',
        descrizione: 'Autoclave principale',
        dimensioni: '3m x 2m x 2m',
        capacita_kg: 500,
        stato: 'operativa',
        posizione: 'Reparto 1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 2,
        codice: 'AUTO-002',
        descrizione: 'Autoclave secondaria',
        dimensioni: '2m x 1.5m x 1.5m',
        capacita_kg: 300,
        stato: 'ferma',
        posizione: 'Reparto 2',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      {
        id: 3,
        codice: 'AUTO-003',
        descrizione: 'Autoclave piccola',
        dimensioni: '1.5m x 1m x 1m',
        capacita_kg: 150,
        stato: 'manutenzione',
        posizione: 'Reparto 3',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ] as AutoclaveResponse[];
  }
};

export default function AutoclaviPage() {
  const [autoclavi, setAutoclavi] = useState<AutoclaveResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{stato?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<AutoclaveResponse | null>(null)
  const { toast } = useToast()

  const fetchAutoclavi = async () => {
    try {
      setIsLoading(true)
      const data = await autoclaveApi.getAll()
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
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: AutoclaveResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare l'autoclave con ID ${id}?`)) {
      return
    }

    try {
      // Qui andrebbe la funzione di delete
      // await autoclaveApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `Autoclave con ID ${id} eliminata con successo.`,
      })
      fetchAutoclavi()
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'autoclave ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare l'autoclave con ID ${id}.`,
      })
    }
  }

  const filteredAutoclavi = autoclavi.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    const matchesSearch = 
      item.codice.toLowerCase().includes(searchLower) ||
      (item.descrizione?.toLowerCase().includes(searchLower) || false) ||
      item.posizione.toLowerCase().includes(searchLower)
    
    // Applica filtro per stato se impostato
    const matchesFilter = !filter.stato || item.stato === filter.stato
    
    return matchesSearch && matchesFilter
  })

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'operativa': return 'success'
      case 'ferma': return 'secondary'
      case 'manutenzione': return 'destructive'
      default: return 'outline'
    }
  }

  const getStatoLabel = (stato: string) => {
    switch (stato) {
      case 'operativa': return 'Operativa'
      case 'ferma': return 'Ferma'
      case 'manutenzione': return 'In Manutenzione'
      default: return stato
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Autoclavi</h1>
          <p className="text-muted-foreground">
            Gestisci le autoclavi disponibili per la produzione
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
        
        <div className="flex flex-wrap gap-2">
          <select 
            className="px-3 py-2 rounded-md border text-sm"
            value={filter.stato || ''}
            onChange={e => setFilter({stato: e.target.value || undefined})}
          >
            <option value="">Tutti gli stati</option>
            <option value="operativa">Operative</option>
            <option value="ferma">Ferme</option>
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
          <TableCaption>Lista delle autoclavi disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Codice</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead>Dimensioni</TableHead>
              <TableHead className="text-center">Capacità (kg)</TableHead>
              <TableHead>Posizione</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAutoclavi.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8">
                  Nessuna autoclave trovata
                </TableCell>
              </TableRow>
            ) : (
              filteredAutoclavi.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.id}</TableCell>
                  <TableCell>{item.codice}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione || '-'}</TableCell>
                  <TableCell>{item.dimensioni}</TableCell>
                  <TableCell className="text-center">{item.capacita_kg}</TableCell>
                  <TableCell>{item.posizione}</TableCell>
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
              {editingItem ? 'Modifica Autoclave' : 'Nuova Autoclave'}
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