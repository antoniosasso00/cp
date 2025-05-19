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

export default function PartiPage() {
  const [parti, setParti] = useState<ParteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{part_number?: string; cliente?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ParteResponse | null>(null)
  const { toast } = useToast()

  const fetchParti = async () => {
    try {
      setIsLoading(true)
      const data = await partiApi.getAll(filter)
      setParti(data)
    } catch (error) {
      console.error('Errore nel caricamento delle parti:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare le parti. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchParti()
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ParteResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare la parte con ID ${id}?`)) {
      return
    }

    try {
      await partiApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminata',
        description: `Parte con ID ${id} eliminata con successo.`,
      })
      fetchParti()
    } catch (error) {
      console.error(`Errore durante l'eliminazione della parte ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare la parte con ID ${id}.`,
      })
    }
  }

  const filteredParti = parti.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number.toLowerCase().includes(searchLower) ||
      item.descrizione_breve.toLowerCase().includes(searchLower) ||
      (item.cliente && item.cliente.toLowerCase().includes(searchLower))
    )
  })

  const uniqueClienti = Array.from(new Set(parti.map(item => item.cliente).filter(Boolean))) as string[]

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
        
        <div className="flex flex-wrap gap-2">
          <select 
            className="px-3 py-2 rounded-md border text-sm"
            value={filter.cliente || ''}
            onChange={e => setFilter({...filter, cliente: e.target.value || undefined})}
          >
            <option value="">Tutti i clienti</option>
            {uniqueClienti.map(cliente => (
              <option key={cliente} value={cliente}>{cliente}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <p>Caricamento in corso...</p>
        </div>
      ) : (
        <Table>
          <TableCaption>Lista delle parti in produzione</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Part Number</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead className="text-center">Valvole</TableHead>
              <TableHead>Tools</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredParti.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  Nessuna parte trovata
                </TableCell>
              </TableRow>
            ) : (
              filteredParti.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.id}</TableCell>
                  <TableCell>{item.part_number}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione_breve}</TableCell>
                  <TableCell>{item.cliente || '-'}</TableCell>
                  <TableCell className="text-center">
                    {item.num_valvole_richieste}
                  </TableCell>
                  <TableCell>
                    {item.tools.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {item.tools.map(tool => (
                          <Badge key={tool.id} variant="secondary" className="mr-1">
                            {tool.codice}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      '-'
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

      <ParteModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        onSuccess={() => {
          fetchParti()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 