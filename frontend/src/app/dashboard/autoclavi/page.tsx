'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { AutoclaveModal } from './components/autoclave-modal'
import { autoclaveApi, type Autoclave } from '@/lib/api'

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
      await autoclaveApi.delete(id)
      
      toast({
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
      item.reparto.toLowerCase().includes(searchLower)
    )
  })

  const getStatoBadgeVariant = (stato: string) => {
    switch (stato) {
      case 'DISPONIBILE': return 'success'
      case 'IN_USO': return 'secondary'
      case 'GUASTO': return 'destructive'
      case 'MANUTENZIONE': return 'warning'
      default: return 'outline'
    }
  }

  const getStatoLabel = (stato: string) => {
    switch (stato) {
      case 'DISPONIBILE': return 'Disponibile'
      case 'IN_USO': return 'In Uso'
      case 'GUASTO': return 'Guasto'
      case 'MANUTENZIONE': return 'In Manutenzione'
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
          <p>Caricamento in corso...</p>
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
              <TableHead>Reparto</TableHead>
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
                    {item.lunghezza_piano} x {item.larghezza_piano}
                  </TableCell>
                  <TableCell className="text-center">{item.numero_linee_vuoto}</TableCell>
                  <TableCell>{item.reparto}</TableCell>
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

      <AutoclaveModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={fetchAutoclavi}
      />
    </div>
  )
} 