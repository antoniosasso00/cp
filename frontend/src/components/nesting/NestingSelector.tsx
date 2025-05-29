'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  Package, 
  Search, 
  Filter, 
  Calendar,
  Gauge,
  Users,
  Eye
} from 'lucide-react'
import { EmptyState } from '@/components/ui/EmptyState'
import { 
  nestingApi, 
  NestingResult, 
  NestingListResponse 
} from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingSelectorProps {
  onNestingSelected: (nestingId: number) => void
  selectedNestingId?: number | null
  className?: string
}

export function NestingSelector({ 
  onNestingSelected, 
  selectedNestingId,
  className = "" 
}: NestingSelectorProps) {
  const [nestingList, setNestingList] = useState<NestingResult[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [autoclaveFilter, setAutoclaveFilter] = useState<string>('all')
  
  const { toast } = useToast()

  // Carica la lista dei nesting
  const loadNestingList = async () => {
    try {
      setIsLoading(true)
      const response = await nestingApi.getList({
        page: 1,
        per_page: 100, // Carica molti nesting per la selezione
        stato: statusFilter === 'all' ? undefined : statusFilter,
        autoclave_id: autoclaveFilter === 'all' ? undefined : parseInt(autoclaveFilter)
      })
      
      if (response.success && response.nesting_list) {
        setNestingList(response.nesting_list)
      } else {
        throw new Error(response.message || 'Errore nel caricamento della lista')
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare la lista dei nesting",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadNestingList()
  }, [statusFilter, autoclaveFilter])

  // Filtra i nesting in base al termine di ricerca
  const filteredNesting = nestingList.filter(nesting => {
    if (!searchTerm) return true
    
    const searchLower = searchTerm.toLowerCase()
    return (
      nesting.autoclave?.nome?.toLowerCase().includes(searchLower) ||
      nesting.autoclave?.codice?.toLowerCase().includes(searchLower) ||
      nesting.note?.toLowerCase().includes(searchLower) ||
      nesting.id.toString().includes(searchLower)
    )
  })

  // Raggruppa per autoclave
  const nestingByAutoclave = filteredNesting.reduce((acc, nesting) => {
    const autoclaveKey = nesting.autoclave?.nome || 'Senza Autoclave'
    if (!acc[autoclaveKey]) {
      acc[autoclaveKey] = []
    }
    acc[autoclaveKey].push(nesting)
    return acc
  }, {} as Record<string, NestingResult[]>)

  // Ottieni lista autoclavi uniche per il filtro
  const uniqueAutoclaves = Array.from(
    new Set(nestingList.map(n => n.autoclave?.nome).filter(Boolean))
  )

  const getStatusColor = (stato: string) => {
    switch (stato.toLowerCase()) {
      case 'bozza': return 'bg-yellow-100 text-yellow-800'
      case 'confermato': return 'bg-green-100 text-green-800'
      case 'in_corso': return 'bg-blue-100 text-blue-800'
      case 'completato': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Seleziona Nesting
          </CardTitle>
          <CardDescription>
            Caricamento lista nesting...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Seleziona Nesting per Canvas
        </CardTitle>
        <CardDescription>
          Scegli un nesting esistente da visualizzare nel canvas interattivo
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Filtri e ricerca */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="search">Ricerca</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Cerca per autoclave, ID, note..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="status-filter">Stato</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tutti gli stati" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti gli stati</SelectItem>
                <SelectItem value="bozza">Bozza</SelectItem>
                <SelectItem value="confermato">Confermato</SelectItem>
                <SelectItem value="in_corso">In Corso</SelectItem>
                <SelectItem value="completato">Completato</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="autoclave-filter">Autoclave</Label>
            <Select value={autoclaveFilter} onValueChange={setAutoclaveFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Tutte le autoclavi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutte le autoclavi</SelectItem>
                {uniqueAutoclaves.filter((autoclave): autoclave is string => autoclave !== undefined).map(autoclave => (
                  <SelectItem key={autoclave} value={autoclave}>
                    {autoclave}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Lista nesting raggruppati per autoclave */}
        {Object.keys(nestingByAutoclave).length === 0 ? (
          <EmptyState
            message="🛠 Nessun nesting trovato"
            description="Prova a modificare i filtri di ricerca o crea un nuovo nesting"
            icon="🔍"
            size="sm"
          />
        ) : (
          <div className="space-y-6 max-h-96 overflow-y-auto">
            {Object.entries(nestingByAutoclave).map(([autoclaveName, nestings]) => (
              <div key={autoclaveName} className="space-y-3">
                <h4 className="font-semibold text-sm text-muted-foreground border-b pb-1">
                  {autoclaveName} ({nestings.length})
                </h4>
                
                <div className="space-y-2">
                  {nestings.map((nesting) => (
                    <div
                      key={nesting.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                        selectedNestingId === nesting.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => onNestingSelected(nesting.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">Nesting #{nesting.id}</span>
                            <Badge className={getStatusColor(nesting.stato)}>
                              {nesting.stato}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Package className="h-3 w-3" />
                              {nesting.odl_count || 0} ODL
                            </div>
                            <div className="flex items-center gap-1">
                              <Gauge className="h-3 w-3" />
                              {Math.round((nesting.area_utilizzata || 0) / (nesting.area_totale || 1) * 100)}%
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {nesting.valvole_utilizzate || 0}V
                            </div>
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(nesting.created_at)}
                            </div>
                          </div>
                          
                          {nesting.note && (
                            <div className="text-xs text-muted-foreground mt-1 truncate">
                              {nesting.note}
                            </div>
                          )}
                        </div>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          className="ml-2"
                          onClick={(e) => {
                            e.stopPropagation()
                            onNestingSelected(nesting.id)
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {!isLoading && (!nestingList || nestingList.length === 0) && (
          <div className="text-center py-8 text-gray-500">
            <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Nessun nesting trovato</p>
            <p className="text-sm">Modifica i filtri o crea un nuovo nesting per iniziare.</p>
          </div>
        )}

        {/* Statistiche */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{nestingList.length}</div>
              <div className="text-xs text-muted-foreground">Totale</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {nestingList.filter(n => n.stato === 'confermato').length}
              </div>
              <div className="text-xs text-muted-foreground">Confermati</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">
                {nestingList.filter(n => n.stato === 'bozza').length}
              </div>
              <div className="text-xs text-muted-foreground">Bozze</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {uniqueAutoclaves.length}
              </div>
              <div className="text-xs text-muted-foreground">Autoclavi</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 