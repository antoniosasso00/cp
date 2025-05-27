'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CatalogoResponse, catalogoApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { useDebounce } from '@/hooks/useDebounce'
import CatalogoModal from './components/catalogo-modal'
import { 
  Loader2, 
  MoreHorizontal, 
  Pencil, 
  Trash2,
  Search,
  AlertCircle,
  BarChart3
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { buttonVariants } from '@/components/ui/button'
import Link from 'next/link'

export default function CatalogoPage() {
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<{categoria?: string; sotto_categoria?: string; attivo?: boolean}>({})
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<CatalogoResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const { toast } = useToast()

  // Debounce della ricerca per ottimizzare le chiamate API
  const debouncedSearchQuery = useDebounce(searchQuery, 300)

  const fetchCatalogo = async (searchTerm?: string) => {
    try {
      setIsLoading(!searchTerm) // Solo loading completo se non è una ricerca
      setIsSearching(!!searchTerm) // Indicatore di ricerca in corso
      setError(null)
      
      const params = {
        ...filter,
        ...(searchTerm && { search: searchTerm })
      }
      
      const data = await catalogoApi.getAll(params)
      setCatalogo(data)
    } catch (error: any) {
      console.error('Errore nel caricamento del catalogo:', error)
      const errorMessage = error?.message || 'Impossibile caricare il catalogo. Verifica la connessione al server.'
      setError(errorMessage)
      toast({
        variant: 'destructive',
        title: 'Errore di connessione',
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
      setIsSearching(false)
    }
  }

  // Effetto per il caricamento iniziale e filtri
  useEffect(() => {
    fetchCatalogo()
  }, [filter])

  // Effetto per la ricerca debounced
  useEffect(() => {
    if (debouncedSearchQuery !== searchQuery) return // Evita chiamate duplicate
    fetchCatalogo(debouncedSearchQuery)
  }, [debouncedSearchQuery])

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
      fetchCatalogo(debouncedSearchQuery)
    } catch (error) {
      console.error(`Errore durante l'eliminazione di ${partNumber}:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare ${partNumber}. Potrebbe essere utilizzato in altre parti.`,
      })
    }
  }

  // Estrai categorie e sotto-categorie uniche per i filtri
  const uniqueCategories = Array.from(new Set(catalogo.map(item => item.categoria).filter(Boolean))) as string[]
  const uniqueSottoCategories = Array.from(new Set(catalogo.map(item => item.sotto_categoria).filter(Boolean))) as string[]

  return (
    <div className="space-y-6">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Catalogo Parti</h1>
          <p className="text-muted-foreground">
            Gestisci il catalogo dei part number disponibili
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link 
                          href="/dashboard/management/statistiche" 
            className={buttonVariants({ variant: "outline" })}
          >
            <BarChart3 className="mr-2 h-4 w-4" />
            Statistiche
          </Link>
          <Button onClick={handleCreateClick}>Nuovo Part Number</Button>
        </div>
      </div>

      {/* Sezione ricerca e filtri */}
      <div className="flex flex-col space-y-4">
        {/* Barra di ricerca */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="Cerca nel catalogo..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin" />
          )}
        </div>
        
        {/* Filtri */}
        <div className="flex flex-wrap gap-2">
          <Select 
            value={filter.categoria || 'all'}
            onValueChange={(value) => setFilter({...filter, categoria: value === 'all' ? undefined : value})}
          >
            <SelectTrigger className="min-w-[150px]">
              <SelectValue placeholder="Tutte le categorie" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le categorie</SelectItem>
              {uniqueCategories.map(cat => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select 
            value={filter.sotto_categoria || 'all'}
            onValueChange={(value) => setFilter({...filter, sotto_categoria: value === 'all' ? undefined : value})}
          >
            <SelectTrigger className="min-w-[150px]">
              <SelectValue placeholder="Tutte le sotto-categorie" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le sotto-categorie</SelectItem>
              {uniqueSottoCategories.map(sottoCat => (
                <SelectItem key={sottoCat} value={sottoCat}>{sottoCat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select 
            value={filter.attivo === undefined ? 'all' : filter.attivo ? 'true' : 'false'}
            onValueChange={(value) => {
              setFilter({
                ...filter, 
                attivo: value === 'all' ? undefined : value === 'true'
              })
            }}
          >
            <SelectTrigger className="min-w-[120px]">
              <SelectValue placeholder="Tutti gli stati" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutti gli stati</SelectItem>
              <SelectItem value="true">Attivi</SelectItem>
              <SelectItem value="false">Non attivi</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Gestione errori */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button 
              variant="outline" 
              size="sm" 
              className="ml-2"
              onClick={() => fetchCatalogo(debouncedSearchQuery)}
            >
              Riprova
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Tabella risultati */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Caricamento in corso...</span>
        </div>
      ) : (
        <div className="rounded-md border overflow-x-auto">
          <Table>
            <TableCaption>
              {catalogo.length === 0 
                ? "Nessun part number trovato" 
                : `${catalogo.length} part number trovati`
              }
            </TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[120px]">Part Number</TableHead>
                <TableHead className="min-w-[200px]">Descrizione</TableHead>
                <TableHead className="min-w-[120px]">Categoria</TableHead>
                <TableHead className="min-w-[140px]">Sotto Categoria</TableHead>
                <TableHead className="text-center min-w-[80px]">Stato</TableHead>
                <TableHead className="min-w-[120px]">Ultima modifica</TableHead>
                <TableHead className="text-right min-w-[100px]">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {catalogo.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    {searchQuery || Object.keys(filter).some(key => filter[key as keyof typeof filter]) 
                      ? "Nessun risultato trovato per i criteri di ricerca" 
                      : "Nessun part number presente nel catalogo"
                    }
                  </TableCell>
                </TableRow>
              ) : (
                catalogo.map(item => (
                  <TableRow key={item.part_number}>
                    <TableCell className="font-medium">{item.part_number}</TableCell>
                    <TableCell className="max-w-xs truncate" title={item.descrizione}>
                      {item.descrizione}
                    </TableCell>
                    <TableCell>{item.categoria || '-'}</TableCell>
                    <TableCell>{item.sotto_categoria || '-'}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant={item.attivo ? 'success' : 'outline'}>
                        {item.attivo ? 'Attivo' : 'Non attivo'}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDateIT(item.updated_at)}</TableCell>
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
                            onClick={() => handleDeleteClick(item.part_number)}
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

      <CatalogoModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        item={editingItem} 
        onSuccess={() => {
          fetchCatalogo(debouncedSearchQuery)
          setModalOpen(false)
        }}
      />
    </div>
  )
} 