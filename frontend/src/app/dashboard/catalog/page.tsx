'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { CatalogoResponse, catalogoApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import CatalogoModal from './components/catalogo-modal'

export default function CatalogoPage() {
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{categoria?: string; attivo?: boolean}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CatalogoResponse | null>(null)
  const { toast } = useToast()

  const fetchCatalogo = async () => {
    try {
      setIsLoading(true)
      const data = await catalogoApi.getAll(filter)
      setCatalogo(data)
    } catch (error) {
      console.error('Errore nel caricamento del catalogo:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare il catalogo. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCatalogo()
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: CatalogoResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (partNumber: string) => {
    if (!window.confirm(`Sei sicuro di voler eliminare ${partNumber}?`)) {
      return
    }

    try {
      await catalogoApi.delete(partNumber)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `Part number ${partNumber} eliminato con successo.`,
      })
      fetchCatalogo()
    } catch (error) {
      console.error(`Errore durante l'eliminazione di ${partNumber}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare ${partNumber}. Potrebbe essere utilizzato in altre parti.`,
      })
    }
  }

  const filteredCatalogo = catalogo.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number.toLowerCase().includes(searchLower) ||
      item.descrizione.toLowerCase().includes(searchLower) ||
      (item.categoria && item.categoria.toLowerCase().includes(searchLower))
    )
  })

  const uniqueCategories = Array.from(new Set(catalogo.map(item => item.categoria).filter(Boolean))) as string[]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Catalogo</h1>
          <p className="text-muted-foreground">
            Gestisci i part number disponibili nel catalogo
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo Part Number</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nel catalogo..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        
        <div className="flex flex-wrap gap-2">
          <select 
            className="px-3 py-2 rounded-md border text-sm"
            value={filter.categoria || ''}
            onChange={e => setFilter({...filter, categoria: e.target.value || undefined})}
          >
            <option value="">Tutte le categorie</option>
            {uniqueCategories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          <select 
            className="px-3 py-2 rounded-md border text-sm"
            value={filter.attivo === undefined ? '' : filter.attivo ? 'true' : 'false'}
            onChange={e => {
              const value = e.target.value
              setFilter({
                ...filter, 
                attivo: value === '' ? undefined : value === 'true'
              })
            }}
          >
            <option value="">Tutti gli stati</option>
            <option value="true">Attivi</option>
            <option value="false">Non attivi</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <p>Caricamento in corso...</p>
        </div>
      ) : (
        <Table>
          <TableCaption>Lista dei part number nel catalogo</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Part Number</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead>Ultima modifica</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCatalogo.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Nessun part number trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredCatalogo.map(item => (
                <TableRow key={item.part_number}>
                  <TableCell className="font-medium">{item.part_number}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione}</TableCell>
                  <TableCell>{item.categoria || '-'}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant={item.attivo ? 'success' : 'outline'}>
                      {item.attivo ? 'Attivo' : 'Non attivo'}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDateIT(item.updated_at)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEditClick(item)}>
                        Modifica
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteClick(item.part_number)}>
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

      <CatalogoModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        onSuccess={() => {
          fetchCatalogo()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 