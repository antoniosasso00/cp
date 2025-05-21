'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CalendarClock, Loader2, PlusCircle, MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { tempoFasiApi, odlApi } from '@/lib/api'
import { formatDateIT, formatDateTime } from '@/lib/utils'
import TempoFaseModal from './components/tempo-fase-modal'

// Funzione per formattare la durata in ore e minuti
const formatDuration = (minutes: number | null): string => {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

// Funzione per tradurre il tipo di fase
const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

// Badge varianti per i diversi tipi di fase
const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "primary" | "success" | "warning"> = {
    "laminazione": "primary",
    "attesa_cura": "warning",
    "cura": "destructive",
  }
  return variants[fase] || "default"
}

export default function TempiPage() {
  const [tempiFasi, setTempiFasi] = useState<any[]>([])
  const [odlList, setOdlList] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<any | null>(null)
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica i dati dei tempi di fase
      const tempiData = await tempoFasiApi.getAll();
      setTempiFasi(tempiData);
      
      // Carica i dati degli ODL per riferimento
      const odlData = await odlApi.getAll();
      setOdlList(odlData);
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati di monitoraggio tempi. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: any) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare questo record di tempo?`)) {
      return
    }

    try {
      await tempoFasiApi.delete(id)
      toast({
        title: 'Eliminato',
        description: `Record eliminato con successo.`,
      })
      fetchData()
    } catch (error) {
      console.error(`Errore durante l'eliminazione:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare il record.`,
      })
    }
  }

  // Filtra i dati in base alla ricerca
  const filteredItems = tempiFasi.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    const odlInfo = odlList.find(odl => odl.id === item.odl_id)
    
    return (
      (odlInfo?.parte?.part_number?.toLowerCase()?.includes(searchLower)) ||
      String(item.odl_id).includes(searchLower) ||
      translateFase(item.fase).toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    )
  })

  // Ottieni informazioni ODL tramite odl_id
  const getOdlInfo = (odlId: number) => {
    return odlList.find(odl => odl.id === odlId) || null;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio Tempi di Produzione</h1>
          <p className="text-muted-foreground">
            Monitora i tempi delle diverse fasi di produzione e visualizza le previsioni
          </p>
        </div>
        <Button onClick={handleCreateClick}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Nuovo Tempo
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <Input
          placeholder="Cerca nei tempi di produzione..."
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
          <TableCaption>Monitoraggio dei tempi di produzione per ODL</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>ODL</TableHead>
              <TableHead>Part Number</TableHead>
              <TableHead>Fase</TableHead>
              <TableHead>Inizio</TableHead>
              <TableHead>Fine</TableHead>
              <TableHead>Durata</TableHead>
              <TableHead>Note</TableHead>
              <TableHead className="text-right">Azioni</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8">
                  Nessun dato di monitoraggio tempi trovato
                </TableCell>
              </TableRow>
            ) : (
              filteredItems.map(item => {
                const odlInfo = getOdlInfo(item.odl_id);
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.odl_id}</TableCell>
                    <TableCell>
                      {odlInfo?.parte?.part_number || 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getFaseBadgeVariant(item.fase)}>
                        {translateFase(item.fase)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {formatDateTime(item.inizio_fase)}
                    </TableCell>
                    <TableCell>
                      {item.fine_fase ? formatDateTime(item.fine_fase) : 'In corso'}
                    </TableCell>
                    <TableCell>
                      {formatDuration(item.durata_minuti)}
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
                )
              })
            )}
          </TableBody>
        </Table>
      )}

      <TempoFaseModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        odlList={odlList}
        onSuccess={() => {
          fetchData()
          setModalOpen(false)
        }}
      />
    </div>
  )
} 