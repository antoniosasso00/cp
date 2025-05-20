'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { CicloModal } from './components/ciclo-modal'
import { cicloCuraApi, type CicloCura } from '@/lib/api'

export default function CicliCuraPage() {
  const [cicli, setCicli] = useState<CicloCura[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CicloCura | null>(null)
  const { toast } = useToast()

  const fetchCicli = async () => {
    try {
      setIsLoading(true)
      const data = await cicloCuraApi.getAll()
      setCicli(data)
    } catch (error) {
      console.error('Errore nel caricamento dei cicli:', error)
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
    fetchCicli()
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: CicloCura) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo ciclo?')) {
      return
    }

    try {
      await cicloCuraApi.delete(id)
      
      toast({
        title: 'Ciclo eliminato',
        description: 'Il ciclo di cura è stato eliminato con successo.',
      })
      fetchCicli()
    } catch (error) {
      console.error('Errore durante l\'eliminazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare il ciclo. Potrebbe essere in uso.',
      })
    }
  }

  const filteredCicli = cicli.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return item.nome.toLowerCase().includes(searchLower)
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cicli di Cura</h1>
          <p className="text-muted-foreground">
            Gestisci i cicli di cura disponibili
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo Ciclo</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei cicli..."
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
              <TableHead>Nome</TableHead>
              <TableHead className="text-center">Temperatura Max</TableHead>
              <TableHead className="text-center">Pressione Max</TableHead>
              <TableHead className="text-center">Stasi 1</TableHead>
              <TableHead className="text-center">Stasi 2</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCicli.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Nessun ciclo trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredCicli.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.nome}</TableCell>
                  <TableCell className="text-center">{item.temperatura_max}°C</TableCell>
                  <TableCell className="text-center">{item.pressione_max} bar</TableCell>
                  <TableCell className="text-center">
                    {item.temperatura_stasi1}°C / {item.pressione_stasi1} bar / {item.durata_stasi1} min
                  </TableCell>
                  <TableCell className="text-center">
                    {item.attiva_stasi2 ? (
                      <>
                        {item.temperatura_stasi2}°C / {item.pressione_stasi2} bar / {item.durata_stasi2} min
                        <Badge variant="secondary" className="ml-2">Attiva</Badge>
                      </>
                    ) : (
                      <Badge variant="outline">Disattiva</Badge>
                    )}
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

      <CicloModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={fetchCicli}
      />
    </div>
  )
} 