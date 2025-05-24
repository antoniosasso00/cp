'use client'

import { useState } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toolApi, ToolWithStatus } from '@/lib/api'
import { ToolModal } from './components/tool-modal'
import { ToolStatusBadge } from '@/components/ToolStatusBadge'
import { useToolsWithStatus } from '@/hooks/useToolsWithStatus'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2,
  RefreshCw,
  RotateCcw
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ToolWithStatus | null>(null)
  const [isSyncing, setIsSyncing] = useState(false)
  const { toast } = useToast()

  const { 
    tools, 
    loading, 
    error, 
    refresh, 
    syncStatus, 
    lastUpdated 
  } = useToolsWithStatus({
    autoRefresh: true,
    refreshInterval: 5000, // 5 secondi
    refreshOnFocus: true
  })

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ToolWithStatus) => {
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
        title: 'Eliminato',
        description: 'Tool eliminato con successo.',
      })
      refresh()
    } catch (error) {
      console.error('Errore durante l\'eliminazione del tool:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile eliminare il tool.',
      })
    }
  }

  const handleSyncStatus = async () => {
    try {
      setIsSyncing(true)
      await syncStatus()
      toast({
        title: 'Sincronizzazione completata',
        description: 'Stato dei tool aggiornato con successo.',
      })
    } catch (error) {
      console.error('Errore nella sincronizzazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile sincronizzare lo stato dei tool.',
      })
    } finally {
      setIsSyncing(false)
    }
  }

  const filteredTools = tools.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number_tool.toLowerCase().includes(searchLower) ||
      (item.descrizione?.toLowerCase().includes(searchLower) || false)
    )
  })

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
            <p className="text-muted-foreground">
              Gestisci i tools disponibili per la produzione
            </p>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="text-red-500 text-center">
            <h3 className="text-lg font-semibold">Errore nel caricamento</h3>
            <p className="text-sm">{error}</p>
          </div>
          <Button onClick={refresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Riprova
          </Button>
        </div>
      </div>
    )
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
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={handleSyncStatus}
            disabled={isSyncing}
          >
            {isSyncing ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RotateCcw className="h-4 w-4 mr-2" />
            )}
            Sincronizza Stato
          </Button>
          <Button 
            variant="outline" 
            onClick={refresh}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Aggiorna
          </Button>
          <Button onClick={handleCreateClick}>Nuovo Tool</Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei tools..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            Aggiornamento automatico ogni 5s
          </div>
          {lastUpdated && (
            <div>
              Ultimo aggiornamento: {lastUpdated.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {loading && tools.length === 0 ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <Table>
          <TableCaption>
            Lista dei tools disponibili ({filteredTools.length} di {tools.length})
          </TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Part Number Tool</TableHead>
              <TableHead>Descrizione</TableHead>
              <TableHead className="text-center">Dimensioni (mm)</TableHead>
              <TableHead className="text-center">Stato</TableHead>
              <TableHead className="text-center">ODL Associato</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTools.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  {searchQuery ? 'Nessun tool trovato per la ricerca' : 'Nessun tool disponibile'}
                </TableCell>
              </TableRow>
            ) : (
              filteredTools.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.part_number_tool}</TableCell>
                  <TableCell className="max-w-xs truncate">{item.descrizione || '-'}</TableCell>
                  <TableCell className="text-center">
                    {item.lunghezza_piano} x {item.larghezza_piano}
                  </TableCell>
                  <TableCell className="text-center">
                    <ToolStatusBadge status={item.status_display} />
                  </TableCell>
                  <TableCell className="text-center">
                    {item.current_odl ? (
                      <div className="text-sm">
                        <div className="font-medium">ODL #{item.current_odl.id}</div>
                        <div className="text-muted-foreground">
                          Parte ID: {item.current_odl.parte_id}
                        </div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
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

      <ToolModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        editingItem={editingItem}
        onSuccess={refresh}
      />
    </div>
  )
} 