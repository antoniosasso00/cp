'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Input } from '@/shared/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/components/ui/select'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  Loader2, 
  Package2, 
  Plus, 
  Search,
  Eye,
  RefreshCw,
  Filter,
  LayoutGrid
} from 'lucide-react'
import { batchNestingApi, BatchNestingList } from '@/shared/lib/api'
import { formatDateTime } from '@/shared/lib/utils'

interface BatchItem {
  id: string
  nome?: string
  stato: 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'terminato'
  autoclave_id: number
  autoclave?: {
    nome: string
    codice: string
  }
  numero_nesting: number
  peso_totale_kg: number
  created_at: string
  updated_at: string
  metrics?: {
    efficiency_percentage: number
    total_weight_kg: number
    positioned_tools: number
  }
}

const STATO_LABELS = {
  'sospeso': 'In Sospeso',
  'confermato': 'Confermato',
  'loaded': 'Caricato',
  'cured': 'In Cura',
  'terminato': 'Terminato'
}

const STATO_COLORS = {
  'sospeso': 'bg-yellow-100 text-yellow-800',
  'confermato': 'bg-green-100 text-green-800',
  'loaded': 'bg-blue-100 text-blue-800',
  'cured': 'bg-red-100 text-red-800',
  'terminato': 'bg-gray-100 text-gray-800'
}

export default function NestingListPage() {
  const router = useRouter()
  const { toast } = useStandardToast()

  const [batches, setBatches] = useState<BatchItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statoFilter, setStatoFilter] = useState<string>('all')
  const [autoclaveFilter, setAutoclaveFilter] = useState<string>('all')

  useEffect(() => {
    loadBatches()
  }, [])

  const loadBatches = async () => {
    try {
      setLoading(true)
      const response = await batchNestingApi.getAll({ limit: 100 })
      
      // Convert BatchNestingList to BatchItem
      const convertedBatches: BatchItem[] = response.map((batch: BatchNestingList) => ({
        ...batch,
        stato: batch.stato as BatchItem['stato'], // Cast to correct union type
        metrics: {
          efficiency_percentage: 85, // Mock data - replace with real calculation
          total_weight_kg: batch.peso_totale_kg,
          positioned_tools: 0 // Mock data - replace with real data
        }
      }))
      
      // Filtra batch terminati (nascondi quelli vecchi)
      const activeBatches = convertedBatches.filter((batch: BatchItem) => batch.stato !== 'terminato')
      setBatches(activeBatches)
      
      toast({
        title: 'Lista aggiornata',
        description: `Caricati ${activeBatches.length} batch attivi`
      })
    } catch (error) {
      toast({
        title: 'Errore caricamento',
        description: 'Impossibile caricare la lista batch',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  // Filtered data
  const filteredBatches = batches.filter(batch => {
    const matchesSearch = !searchQuery || 
      batch.nome?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      batch.autoclave?.nome?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      batch.id.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStato = statoFilter === 'all' || batch.stato === statoFilter
    const matchesAutoclave = autoclaveFilter === 'all' || batch.autoclave_id.toString() === autoclaveFilter

    return matchesSearch && matchesStato && matchesAutoclave
  })

  // Get unique autoclavi for filter
  const uniqueAutoclavi = Array.from(new Set(batches.map(b => b.autoclave_id)))
    .map(id => {
      const batch = batches.find(b => b.autoclave_id === id)
      return {
        id,
        nome: batch?.autoclave?.nome || `Autoclave ${id}`
      }
    })

  const handleViewBatch = (batchId: string) => {
    router.push(`/nesting/result/${batchId}`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Caricamento batch...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Lista Batch Nesting</h1>
          <p className="text-muted-foreground">
            Gestisci e visualizza i batch generati
          </p>
        </div>
        <Button onClick={() => router.push('/nesting')}>
          <Plus className="mr-2 h-4 w-4" />
          Nuovo Nesting
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center p-6">
            <Package2 className="h-8 w-8 text-muted-foreground" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Totale Batch</p>
              <p className="text-2xl font-bold">{batches.length}</p>
            </div>
          </CardContent>
        </Card>
        
        {['sospeso', 'confermato', 'cured'].map(stato => (
          <Card key={stato}>
            <CardContent className="flex items-center p-6">
              <LayoutGrid className="h-8 w-8 text-muted-foreground" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">{STATO_LABELS[stato as keyof typeof STATO_LABELS]}</p>
                <p className="text-2xl font-bold">
                  {batches.filter(b => b.stato === stato).length}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Cerca per nome, ID o autoclave..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={statoFilter} onValueChange={setStatoFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filtra per stato" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti gli stati</SelectItem>
                {Object.entries(STATO_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={autoclaveFilter} onValueChange={setAutoclaveFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filtra per autoclave" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutte le autoclavi</SelectItem>
                {uniqueAutoclavi.map((autoclave) => (
                  <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                    {autoclave.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button onClick={loadBatches} variant="outline">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            Batch ({filteredBatches.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredBatches.length === 0 ? (
            <div className="text-center py-8">
              <Package2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                {searchQuery || statoFilter !== 'all' || autoclaveFilter !== 'all'
                  ? 'Nessun batch corrisponde ai filtri'
                  : 'Nessun batch disponibile'
                }
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Autoclave</TableHead>
                  <TableHead>Efficienza</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Peso</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredBatches.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{batch.nome}</p>
                        <p className="text-sm text-muted-foreground font-mono">
                          {batch.id.slice(0, 8)}...
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={STATO_COLORS[batch.stato as keyof typeof STATO_COLORS] || 'bg-gray-100 text-gray-800'}>
                        {STATO_LABELS[batch.stato as keyof typeof STATO_LABELS] || batch.stato}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{batch.autoclave?.nome || `Autoclave ${batch.autoclave_id}`}</p>
                        <p className="text-sm text-muted-foreground">{batch.autoclave?.codice}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      {batch.metrics?.efficiency_percentage != null ? (
                        <Badge variant="outline">
                          {batch.metrics.efficiency_percentage.toFixed(1)}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {batch.metrics?.positioned_tools != null ? (
                        <Badge variant="secondary">
                          {batch.metrics.positioned_tools}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {batch.metrics?.total_weight_kg != null ? (
                        `${batch.metrics.total_weight_kg.toFixed(1)}kg`
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="text-sm">{formatDateTime(batch.created_at)}</p>
                        {batch.updated_at !== batch.created_at && (
                          <p className="text-xs text-muted-foreground">
                            Mod: {formatDateTime(batch.updated_at)}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button
                        onClick={() => handleViewBatch(batch.id)}
                        variant="outline"
                        size="sm"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 