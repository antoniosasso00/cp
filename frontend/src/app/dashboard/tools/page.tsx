'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { toolApi } from '@/lib/api'
import { ToolModal } from './components/tool-modal'

interface Tool {
  id: number
  codice: string
  descrizione?: string
  lunghezza_piano: number
  larghezza_piano: number
  disponibile: boolean
  in_manutenzione: boolean
  created_at: string
  updated_at: string
}

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Tool | null>(null)
  const { toast } = useToast()

  const fetchTools = async () => {
    try {
      setIsLoading(true)
      const data = await toolApi.getAll()
      setTools(data as Tool[])
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
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: Tool) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo tool?')) {
      return
    }

    try {
      await toolApi.delete(id)
      toast({
        title: 'Tool eliminato',
        description: 'Il tool è stato eliminato con successo.',
      })
      fetchTools()
    } catch (error) {
      console.error('Errore durante l\'eliminazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare il tool. Potrebbe essere in uso.',
      })
    }
  }

  const filteredTools = tools.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.codice.toLowerCase().includes(searchLower) ||
      (item.descrizione?.toLowerCase().includes(searchLower) || false)
    )
  })

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
              <TableHead>Codice</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Dimensioni (mm)</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTools.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  Nessun tool trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredTools.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.codice}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione || '-'}</TableCell>
                  <TableCell className="text-center">
                    {item.lunghezza_piano} x {item.larghezza_piano}
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex justify-center gap-2">
                      <Badge variant={item.disponibile ? 'success' : 'destructive'}>
                        {item.disponibile ? 'Disponibile' : 'Non Disponibile'}
                      </Badge>
                      {item.in_manutenzione && (
                        <Badge variant="warning">In Manutenzione</Badge>
                      )}
                    </div>
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

      <ToolModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={fetchTools}
      />
    </div>
  )
} 