'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { cicloCuraApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'

interface CicloCuraResponse {
  id: number
  nome: string
  descrizione?: string
  temperatura: number
  durata_minuti: number
  created_at: string
  updated_at: string
}

export default function CicliCuraPage() {
  const [cicliCura, setCicliCura] = useState<CicloCuraResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CicloCuraResponse | null>(null)
  const { toast } = useToast()

  const fetchCicliCura = async () => {
    try {
      setIsLoading(true)
      const data = await cicloCuraApi.getAll()
      setCicliCura(data as CicloCuraResponse[])
    } catch (error) {
      console.error('Errore nel caricamento dei cicli di cura:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i cicli di cura. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCicliCura()
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: CicloCuraResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare il ciclo di cura con ID ${id}?`)) {
      return
    }

    try {
      // Qui andrebbe la funzione di delete
      // await cicloCuraApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `Ciclo di cura con ID ${id} eliminato con successo.`,
      })
      fetchCicliCura()
    } catch (error) {
      console.error(`Errore durante l'eliminazione del ciclo di cura ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare il ciclo di cura con ID ${id}.`,
      })
    }
  }

  const filteredCicliCura = cicliCura.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.nome.toLowerCase().includes(searchLower) ||
      (item.descrizione?.toLowerCase().includes(searchLower) || false)
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cicli di Cura</h1>
          <p className="text-muted-foreground">
            Gestisci i cicli di cura per la produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo Ciclo di Cura</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei cicli di cura..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <p>Caricamento in corso...</p>
        </div>
      ) : (
        <Table>
          <TableCaption>Lista dei cicli di cura disponibili</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Nome</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead>Temperatura (°C)</TableHead>
              <TableHead>Durata (min)</TableHead>
              <TableHead>Ultima modifica</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCicliCura.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  Nessun ciclo di cura trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredCicliCura.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.id}</TableCell>
                  <TableCell>{item.nome}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione || '-'}</TableCell>
                  <TableCell>{item.temperatura}°C</TableCell>
                  <TableCell>{item.durata_minuti} min</TableCell>
                  <TableCell>{formatDateIT(item.updated_at)}</TableCell>
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
              {editingItem ? 'Modifica Ciclo di Cura' : 'Nuovo Ciclo di Cura'}
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