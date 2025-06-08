'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { ODLResponse, odlApi } from '@/lib/api'
import ODLModal from './components/odl-modal'
import { BarraAvanzamentoODL, getPriorityInfo } from '@/shared/components/BarraAvanzamentoODL'
import { OdlProgressWrapper } from '@/shared/components/ui/OdlProgressWrapper'
// import { ConnectionHealthChecker } from '@/components/ui/ConnectionHealthChecker'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2,
  ListFilter,
  Activity,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  WifiOff
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import Link from 'next/link'

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "default", 
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

// Funzione per ottenere l'icona di priorità
const getPriorityIcon = (priorita: number) => {
  if (priorita >= 8) return "🔴"
  if (priorita >= 5) return "🟠"
  if (priorita >= 3) return "🟡"
  return "🟢"
}

// Funzione per ottenere il colore del badge di priorità
const getPriorityBadgeVariant = (priorita: number) => {
  if (priorita >= 8) return "destructive"
  if (priorita >= 5) return "warning"
  if (priorita >= 3) return "secondary"
  return "outline"
}

export default function ODLPage() {
  const [odls, setODLs] = useState<ODLResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{parte_id?: number, tool_id?: number, status?: string}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ODLResponse | null>(null)
  
  // Stati per selezione multipla
  const [selectedODLs, setSelectedODLs] = useState<Set<number>>(new Set())
  const [isDeleting, setIsDeleting] = useState(false)
  
  const router = useRouter()
  const { toast } = useStandardToast()
  
  // Ref per prevenire chiamate multiple simultanee
  const fetchingRef = useRef(false)
  const componentMountedRef = useRef(true)

  // Funzione per caricare i dati ODL
  const loadODLs = useCallback(async () => {
    // Previeni chiamate multiple simultanee
    if (fetchingRef.current) {
      console.log('⏭️ Fetch già in corso, salto questa chiamata')
      return
    }

    fetchingRef.current = true
    setIsLoading(true)
    setError(null)

    try {
      console.log('🔄 Inizio caricamento ODL...')
      const data = await odlApi.fetchODLs(filter)
      
      // Verifica se il componente è ancora montato
      if (!componentMountedRef.current) {
        console.log('⚠️ Componente non montato, ignoro la risposta')
        return
      }

      // Mostra solo gli ODL attivi (non finiti) e ordina cronologicamente
      const odlAttivi = data
        .filter(odl => odl.status !== "Finito")
        .sort((a, b) => {
          const dateA = a.created_at ? new Date(a.created_at).getTime() : a.id
          const dateB = b.created_at ? new Date(b.created_at).getTime() : b.id
          return dateB - dateA
        })
      
      setODLs(odlAttivi)
      console.log(`✅ Caricati ${odlAttivi.length} ODL attivi (totali: ${data.length})`)
      
    } catch (error) {
      console.error('❌ Errore nel caricamento degli ODL:', error)
      
      if (!componentMountedRef.current) return
      
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto'
      setError(errorMessage)
      
      toast({
        variant: 'destructive',
        title: 'Errore nel caricamento',
        description: 'Impossibile caricare gli ordini di lavoro. Verifica la connessione di rete.',
      })
    } finally {
      fetchingRef.current = false
      setIsLoading(false)
    }
  }, [filter]) // Rimosso toast dalle dipendenze per prevenire il loop

  // Effect per il caricamento iniziale e quando cambia il filtro
  useEffect(() => {
    loadODLs()
  }, [loadODLs])

  // Cleanup on unmount - gestisce solo lo stato di mount
  useEffect(() => {
    componentMountedRef.current = true
    return () => {
      componentMountedRef.current = false
    }
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: ODLResponse) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    // Ricarica solo i dati ODL, senza refresh della pagina
    loadODLs()
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare l'ODL con ID ${id}?`)) {
      return
    }

    try {
      await odlApi.deleteODL(id)
      toast({
        variant: 'success',
        title: 'Eliminato',
        description: `ODL con ID ${id} eliminato con successo.`,
      })
      loadODLs()
    } catch (error) {
      console.error(`Errore durante l'eliminazione dell'ODL ${id}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare l'ODL con ID ${id}.`,
      })
    }
  }

  // Funzioni per selezione multipla
  const handleSelectODL = (id: number, checked: boolean) => {
    setSelectedODLs(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(id)
      } else {
        newSet.delete(id)
      }
      return newSet
    })
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedODLs(new Set(filteredODLs.map(odl => odl.id)))
    } else {
      setSelectedODLs(new Set())
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedODLs.size === 0) return

    const confirmMessage = `Sei sicuro di voler eliminare ${selectedODLs.size} ODL selezionati?`
    if (!window.confirm(confirmMessage)) {
      return
    }

    setIsDeleting(true)

    try {
      // Usa il nuovo endpoint per eliminazione multipla
      const result = await odlApi.deleteMultipleODL(Array.from(selectedODLs))

      // Toast di risultato basato sulla risposta del server
      if (result.deleted_count === result.total_requested) {
        toast({
          variant: 'success',
          title: 'Eliminazione completata',
          description: `${result.deleted_count} ODL eliminati con successo.`,
        })
      } else if (result.deleted_count > 0) {
        toast({
          variant: 'default',
          title: 'Eliminazione parziale',
          description: `${result.deleted_count}/${result.total_requested} ODL eliminati. ${result.errors.length} errori.`,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore eliminazione',
          description: `Impossibile eliminare gli ODL selezionati.`,
        })
      }

      // Pulisce la selezione e aggiorna la lista
      setSelectedODLs(new Set())
      loadODLs()

    } catch (error) {
      console.error('Errore eliminazione multipla:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Si è verificato un errore durante l\'eliminazione.',
      })
    } finally {
      setIsDeleting(false)
    }
  }

  const handleRetry = () => {
    setRetryCount(0)
    loadODLs() // Reset del retry count
  }

  const filterODLs = (items: ODLResponse[], query: string) => {
    if (!query) return items
    
    const searchLower = query.toLowerCase()
    return items.filter(item => (
      item.numero_odl.toLowerCase().includes(searchLower) ||
      item.id.toString().includes(searchLower) ||
      item.parte.part_number.toLowerCase().includes(searchLower) ||
      item.tool.part_number_tool.toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    ))
  }
  
  const filteredODLs = filterODLs(odls, searchQuery)

  // Render dello stato di errore
  if (error && !isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Ordini di Lavoro</h1>
            <p className="text-muted-foreground">
              Gestisci gli ordini di lavoro attivi in produzione
            </p>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <WifiOff className="h-16 w-16 text-muted-foreground" />
          <div className="text-center space-y-2">
            <h3 className="text-lg font-semibold">Errore di connessione</h3>
            <p className="text-muted-foreground max-w-md">
              Non è possibile caricare gli ordini di lavoro. 
              Verifica la connessione di rete e riprova.
            </p>
            {retryCount > 0 && (
              <p className="text-sm text-muted-foreground">
                Tentativi effettuati: {retryCount}/3
              </p>
            )}
          </div>
          <Button onClick={handleRetry} className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
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
          <h1 className="text-3xl font-bold tracking-tight">Ordini di Lavoro</h1>
          <p className="text-muted-foreground">
            Gestisci gli ordini di lavoro attivi in produzione
          </p>
        </div>
        <div className="flex gap-3">
          {selectedODLs.size > 0 && (
            <Button 
              variant="destructive" 
              onClick={handleDeleteSelected}
              disabled={isDeleting}
              className="flex items-center gap-2"
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Elimina {selectedODLs.size} selezionati
            </Button>
          )}
          <Button onClick={handleCreateClick} disabled={isLoading}>
            Nuovo ODL
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full max-w-sm">
          <ListFilter className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Cerca negli ODL attivi..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-8"
            disabled={isLoading}
          />
        </div>
        <div className="flex items-center gap-4">
          {selectedODLs.size > 0 && (
            <div className="flex items-center gap-2 text-sm text-primary">
              <CheckCircle2 className="h-4 w-4" />
              <span>{selectedODLs.size} ODL selezionati</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <AlertCircle className="h-4 w-4" />
            <span>Mostrando solo ODL attivi</span>
          </div>
          {/* <ConnectionHealthChecker showLabel={true} className="ml-2" /> */}
          {!isLoading && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => loadODLs()}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Aggiorna
            </Button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <div className="space-y-6">
          <Table>
            <TableCaption>Lista degli ordini di lavoro attivi in produzione</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedODLs.size === filteredODLs.length && filteredODLs.length > 0}
                    onCheckedChange={handleSelectAll}
                    aria-label="Seleziona tutti gli ODL"
                  />
                </TableHead>
                <TableHead>Numero ODL</TableHead>
                <TableHead>Part Number</TableHead>
                <TableHead>Tool</TableHead>
                <TableHead className="text-center">Priorità</TableHead>
                <TableHead className="w-64">Avanzamento</TableHead>
                <TableHead>Note</TableHead>
                <TableHead className="text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredODLs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    {searchQuery ? 
                      'Nessun ordine di lavoro trovato con i criteri di ricerca' : 
                      'Nessun ordine di lavoro attivo trovato'
                    }
                  </TableCell>
                </TableRow>
              ) : (
                filteredODLs.map(item => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedODLs.has(item.id)}
                        onCheckedChange={(checked) => handleSelectODL(item.id, checked as boolean)}
                        aria-label={`Seleziona ODL ${item.numero_odl}`}
                      />
                    </TableCell>
                    <TableCell>
                      <span className="font-mono font-medium text-primary">
                        {item.numero_odl}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{item.parte.part_number}</span>
                        <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {item.parte.descrizione_breve}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{item.tool.part_number_tool}</span>
                        {item.tool.descrizione && (
                          <span className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {item.tool.descrizione}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-lg">{getPriorityIcon(item.priorita)}</span>
                        <Badge variant={getPriorityBadgeVariant(item.priorita)}>
                          Priorità {item.priorita}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="w-64">
                      <OdlProgressWrapper 
                        odlId={item.id}
                        showDetails={false}
                        className="min-h-[40px]"
                      />
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {item.note || '-'}
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
        </div>
      )}

            <ODLModal
        isOpen={modalOpen}
        onClose={handleModalClose}
        item={editingItem}
        onSuccess={() => {
          loadODLs()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 