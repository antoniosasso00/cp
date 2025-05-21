'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ODLResponse, odlApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import ODLModal from './components/odl-modal'
import { CalendarClock, Settings, Loader2 } from 'lucide-react'

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "primary" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "primary",
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

export default function ODLPage() {
  const [odls, setODLs] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{parte_id?: number, tool_id?: number, status?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ODLResponse | null>(null)
  const { toast } = useToast()

  const fetchODLs = async () => {
    try {
      setIsLoading(true)
      const data = await odlApi.getAll(filter)
      setODLs(data)
    } catch (error) {
      console.error('Errore nel caricamento degli ODL:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare gli ordini di lavoro. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchODLs()
  }, [filter])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ODLResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare l'ODL con ID ${id}?`)) {
      return
    }

    try {
      await odlApi.delete(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `ODL con ID ${id} eliminato con successo.`,
      })
      fetchODLs()
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'ODL ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare l'ODL con ID ${id}.`,
      })
    }
  }

  const filteredODLs = odls.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.parte.part_number.toLowerCase().includes(searchLower) ||
      item.tool.codice.toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ordini di Lavoro</h1>
          <p className="text-muted-foreground">
            Gestisci gli ordini di lavoro in produzione
          </p>
        </div>
        <Button onClick={handleCreateClick}>Nuovo ODL</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca negli ODL..."
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
          <TableCaption>Lista degli ordini di lavoro in produzione</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Part Number</TableHead>
              <TableHead>Tool</TableHead>
              <TableHead className="text-center">Priorità</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead>Note</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredODLs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  Nessun ordine di lavoro trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredODLs.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.id}</TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span>{item.parte.part_number}</span>
                      <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                        {item.parte.descrizione_breve}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{item.tool.codice}</TableCell>
                  <TableCell className="text-center">
                    <Badge variant={item.priorita > 5 ? "destructive" : (item.priorita > 2 ? "warning" : "secondary")}>
                      {item.priorita}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={getStatusBadgeVariant(item.status)}>
                      {item.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {item.note || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEditClick(item)}>
                        <Settings className="h-4 w-4 mr-1" />
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

      <ODLModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        onSuccess={() => {
          fetchODLs()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 