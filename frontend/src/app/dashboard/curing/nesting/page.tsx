'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { NestingResponse, nestingApi, reportsApi } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { Loader2, RefreshCw, Info, Search, Filter, Download, AlertCircle, Settings } from 'lucide-react'
import { NestingDetails } from './components/nesting-details'
import { NestingStatusBadge } from '@/components/nesting/NestingStatusBadge'
import { NestingActions } from '@/components/nesting/NestingActions'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useUserRole } from '@/hooks/useUserRole'
import { UnifiedNestingControl } from './components/unified-nesting-control'
import { TwoPlaneNestingPreview } from '@/components/nesting/TwoPlaneNestingPreview'

export default function NestingPage() {
  const { role } = useUserRole()
  const [nestings, setNestings] = useState<NestingResponse[]>([])
  const [filteredNestings, setFilteredNestings] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedNesting, setSelectedNesting] = useState<NestingResponse | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'created_at' | 'area_utilizzata' | 'valvole_utilizzate'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // Stati per preview nesting a due piani
  const [showTwoPlanePreview, setShowTwoPlanePreview] = useState(false)
  const [twoPlaneData, setTwoPlaneData] = useState<any>(null)

  const { toast } = useToast()

  // Funzione per caricare i nesting dal backend
  const fetchNestings = async (statusFilter?: string) => {
    try {
      setIsLoading(true)
      console.log('🔍 Caricamento nesting...', { role, statusFilter })
      const data = await nestingApi.getAll({ 
        ruolo_utente: role || undefined,
        stato_filtro: statusFilter || undefined
      })
      console.log('✅ Nesting caricati:', data.length)
      setNestings(data)
      setFilteredNestings(data)
      
      if (data.length === 0) {
        toast({
          title: 'Nessun nesting trovato',
          description: 'Non ci sono nesting disponibili per i criteri selezionati.',
        })
      }
    } catch (error) {
      console.error('❌ Errore nel caricamento dei nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore di caricamento',
        description: 'Impossibile caricare i nesting. Verifica la connessione al server.',
      })
      setNestings([])
      setFilteredNestings([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchNestings()
  }, [role])

  // Gestione cambio tab
  const handleTabChange = (value: string) => {
    setActiveTab(value)
    if (value === 'all') {
      fetchNestings()
    } else {
      fetchNestings(value)
    }
  }

  // Effetto per filtrare e ordinare i nesting
  useEffect(() => {
    let filtered = [...nestings]

    // Filtro per termine di ricerca
    if (searchTerm) {
      filtered = filtered.filter(nesting => 
        nesting.id.toString().includes(searchTerm) ||
        nesting.autoclave.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        nesting.autoclave.codice.toLowerCase().includes(searchTerm.toLowerCase()) ||
        nesting.odl_list.some(odl => 
          odl.parte.part_number.toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }

    // Filtro per autoclave
    if (selectedAutoclave !== 'all') {
      filtered = filtered.filter(nesting => 
        nesting.autoclave.id.toString() === selectedAutoclave
      )
    }

    // Filtro per stato (se non stiamo usando i tab)
    if (selectedStatus !== 'all' && activeTab === 'all') {
      filtered = filtered.filter(nesting => nesting.stato === selectedStatus)
    }

    // Ordinamento
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy]
      let bValue: any = b[sortBy]
      
      if (sortBy === 'created_at') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    setFilteredNestings(filtered)
  }, [nestings, searchTerm, selectedAutoclave, selectedStatus, activeTab, sortBy, sortOrder])

  // Mostra i dettagli di un nesting
  const handleRowClick = (nesting: NestingResponse) => {
    setSelectedNesting(nesting)
    setDetailsOpen(true)
    
    // ✅ SEZIONE 2: Se il nesting ha dati per due piani, mostra la preview
    if ((nesting.area_piano_1 && nesting.area_piano_1 > 0) || (nesting.area_piano_2 && nesting.area_piano_2 > 0)) {
      // Prepara i dati per la preview a due piani
      setTwoPlaneData({
        nesting_id: nesting.id,
        autoclave: nesting.autoclave,
        posizioni_tool: nesting.posizioni_tool || [],
        area_piano_1: nesting.area_piano_1 || 0,
        area_piano_2: nesting.area_piano_2 || 0,
        peso_totale_kg: nesting.peso_totale_kg || 0,
        odl_list: nesting.odl_list
      })
      setShowTwoPlanePreview(true)
    }
  }

  // Formatta il valore percentuale
  const formatPercent = (value: number, total: number) => {
    if (total === 0) return '0%'
    return `${Math.round((value / total) * 100)}%`
  }

  // Formatta la lista degli ODL per la visualizzazione
  const formatODLList = (odl_list: NestingResponse['odl_list']) => {
    if (odl_list.length === 0) return <span className="text-muted-foreground">Nessun ODL</span>
    
    const firstThree = odl_list.slice(0, 3)
    const remaining = odl_list.length - 3
    
    return (
      <div className="flex flex-wrap gap-1">
        {firstThree.map(odl => (
          <Badge key={odl.id} variant="outline" className="text-xs">
            #{odl.id}
          </Badge>
        ))}
        {remaining > 0 && (
          <Badge variant="secondary" className="text-xs">
            +{remaining}
          </Badge>
        )}
      </div>
    )
  }

  // Gestisce la preview globale del nesting
  const handlePreview = async () => {
    try {
      const preview = await nestingApi.getPreview()
      toast({
        title: 'Preview generata',
        description: `Preview disponibile per ${preview.autoclavi.length} autoclavi`,
      })
    } catch (error) {
      console.error('Errore nella preview:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella preview',
        description: 'Impossibile generare la preview del nesting.',
      })
    }
  }

  // Gestisce il download del report
  const handleDownloadReport = async (nesting: NestingResponse, e: React.MouseEvent) => {
    e.stopPropagation()
    
    try {
      toast({
        title: '🔄 Download in corso...',
        description: `Download report per nesting #${nesting.id}`,
      })
      
      const blob = await reportsApi.downloadNestingReport(nesting.id)
      
      // Crea un URL temporaneo per il blob
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `nesting_report_${nesting.id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: '✅ Download completato',
        description: `Report per nesting #${nesting.id} scaricato con successo`,
      })
      
    } catch (error: any) {
      console.error('Errore nel download del report:', error)
      
      let errorMessage = 'Impossibile scaricare il report.'
      if (error.status === 404) {
        errorMessage = 'Report non trovato. Prova a generarlo prima.'
      } else if (error.message) {
        errorMessage = error.message
      }
      
      toast({
        variant: 'destructive',
        title: '❌ Errore download',
        description: errorMessage,
      })
    }
  }

  // Calcola statistiche per la dashboard
  const stats = {
    totalNestings: nestings.length,
    totalODLProcessed: nestings.reduce((sum, n) => sum + n.odl_list.length, 0),
    averageAreaUsage: nestings.length > 0 
      ? Math.round(nestings.reduce((sum, n) => sum + (n.area_utilizzata / n.area_totale * 100), 0) / nestings.length)
      : 0,
    averageValveUsage: nestings.length > 0 
      ? Math.round(nestings.reduce((sum, n) => sum + (n.valvole_utilizzate / n.valvole_totali * 100), 0) / nestings.length)
      : 0
  }

  return (
    <div className="space-y-6">
      {/* 🎨 Header ottimizzato con design migliorato */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Settings className="h-4 w-4 text-white" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Nesting Ottimizzato
            </h1>
          </div>
          <p className="text-muted-foreground">
            Sistema di ottimizzazione automatica per l'utilizzo delle autoclavi
          </p>
          {/* 📊 Indicatori di stato rapidi */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-muted-foreground">Sistema attivo</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="font-medium">{stats.totalNestings}</span>
              <span className="text-muted-foreground">nesting totali</span>
            </div>
          </div>
        </div>
        
        {/* 🔄 Controlli azione migliorati */}
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            variant="outline"
            onClick={() => fetchNestings()}
            disabled={isLoading}
            size="sm"
            className="transition-all duration-200 hover:scale-105"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          <Button 
            onClick={handlePreview}
            size="sm"
            className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transition-all duration-200 hover:scale-105"
          >
            <Info className="h-4 w-4 mr-2" />
            Preview Globale
          </Button>
        </div>
      </div>

      {/* ✅ SEZIONE 1: Controllo Unificato per Nesting */}
      <UnifiedNestingControl
        onNestingGenerated={() => {
          fetchNestings()
          toast({
            title: 'Lista aggiornata',
            description: 'La lista dei nesting è stata aggiornata con successo.',
          })
        }}
        onPreviewRequested={async () => {
          try {
            const preview = await nestingApi.getPreview()
            toast({
              title: 'Preview generata',
              description: `Preview disponibile per ${preview.autoclavi.length} autoclavi`,
            })
          } catch (error) {
            console.error('Errore nella preview:', error)
            toast({
              variant: 'destructive',
              title: 'Errore nella preview',
              description: 'Impossibile generare la preview del nesting.',
            })
          }
        }}
      />

      {/* ✅ SEZIONE 2: Preview Nesting a Due Piani */}
      {showTwoPlanePreview && twoPlaneData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Preview Nesting a Due Piani - #{twoPlaneData.nesting_id}</span>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowTwoPlanePreview(false)}
              >
                Chiudi Preview
              </Button>
            </CardTitle>
            <CardDescription>
              Visualizzazione interattiva del nesting su due piani per autoclave {twoPlaneData.autoclave.nome}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TwoPlaneNestingPreview
              nestingData={twoPlaneData}
              isEditable={false}
              onConfirm={() => {
                toast({
                  title: 'Nesting confermato',
                  description: `Nesting #${twoPlaneData.nesting_id} confermato con successo`,
                })
                setShowTwoPlanePreview(false)
                fetchNestings()
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* 📊 Statistiche generali ottimizzate */}
      {!isLoading && nestings.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500 hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Nesting Totali</CardTitle>
                <div className="h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Settings className="h-4 w-4 text-blue-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.totalNestings}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats.totalNestings > 0 ? 'Sistema operativo' : 'Nessun dato'}
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-green-500 hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">ODL Processati</CardTitle>
                <div className="h-8 w-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <Badge className="h-4 w-4 text-green-600" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.totalODLProcessed}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Media: {stats.totalNestings > 0 ? Math.round(stats.totalODLProcessed / stats.totalNestings) : 0} per nesting
              </p>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-orange-500 hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Utilizzo Area Medio</CardTitle>
                <div className="h-8 w-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <div className="h-4 w-4 bg-orange-600 rounded-sm"></div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats.averageAreaUsage}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-orange-500 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${stats.averageAreaUsage}%` }}
                ></div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-purple-500 hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Utilizzo Valvole Medio</CardTitle>
                <div className="h-8 w-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <div className="h-4 w-4 bg-purple-600 rounded-full"></div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{stats.averageValveUsage}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-purple-500 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${stats.averageValveUsage}%` }}
                ></div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 🏷️ Tabs ottimizzati per filtrare per stato */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <TabsList className="grid w-full sm:w-auto grid-cols-2 sm:grid-cols-5 h-auto p-1">
            <TabsTrigger value="all" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-current rounded-full"></div>
                <span className="hidden sm:inline">Tutti</span>
                <span className="sm:hidden">All</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="In sospeso" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-white">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-current rounded-full"></div>
                <span className="hidden sm:inline">In Sospeso</span>
                <span className="sm:hidden">Sospeso</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="Confermato" className="data-[state=active]:bg-green-500 data-[state=active]:text-white">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-current rounded-full"></div>
                <span className="hidden sm:inline">Confermati</span>
                <span className="sm:hidden">OK</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="In corso" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-current rounded-full animate-pulse"></div>
                <span className="hidden sm:inline">In Corso</span>
                <span className="sm:hidden">Corso</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="Completato" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-current rounded-full"></div>
                <span className="hidden sm:inline">Completati</span>
                <span className="sm:hidden">Done</span>
              </div>
            </TabsTrigger>
          </TabsList>
          
          {/* 📊 Contatori per ogni stato */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Risultati: </span>
            <Badge variant="outline" className="font-mono">
              {filteredNestings.length}/{nestings.length}
            </Badge>
          </div>
        </div>

        <TabsContent value={activeTab} className="space-y-4">
          {/* 🔍 Filtri e ricerca ottimizzati */}
          {!isLoading && nestings.length > 0 && (
            <Card className="border-dashed border-2 hover:border-solid transition-all duration-200">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <div className="h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Filter className="h-4 w-4 text-blue-600" />
                    </div>
                    Filtri e Ricerca
                  </CardTitle>
                  {(searchTerm || selectedAutoclave !== 'all') && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        setSearchTerm('')
                        setSelectedAutoclave('all')
                      }}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      Cancella filtri
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  {/* 🔍 Campo ricerca migliorato */}
                  <div className="lg:col-span-2">
                    <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                      <Search className="h-4 w-4" />
                      Ricerca globale
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Cerca per ID, autoclave, part number..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 transition-all duration-200 focus:ring-2 focus:ring-blue-500"
                      />
                      {searchTerm && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSearchTerm('')}
                          className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                        >
                          ×
                        </Button>
                      )}
                    </div>
                    {searchTerm && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {filteredNestings.length} risultati trovati
                      </p>
                    )}
                  </div>
                  
                  {/* 🏭 Filtro autoclave migliorato */}
                  <div>
                    <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                      <div className="h-3 w-3 bg-green-500 rounded-sm"></div>
                      Autoclave
                    </label>
                    <Select value={selectedAutoclave} onValueChange={setSelectedAutoclave}>
                      <SelectTrigger className="transition-all duration-200 focus:ring-2 focus:ring-blue-500">
                        <SelectValue placeholder="Tutte le autoclavi" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                            Tutte le autoclavi
                          </div>
                        </SelectItem>
                        {Array.from(new Set(nestings.map(n => n.autoclave.id))).map(autoclaveId => {
                          const autoclave = nestings.find(n => n.autoclave.id === autoclaveId)?.autoclave
                          const count = nestings.filter(n => n.autoclave.id === autoclaveId).length
                          return autoclave ? (
                            <SelectItem key={autoclaveId} value={autoclaveId.toString()}>
                              <div className="flex items-center justify-between w-full">
                                <div className="flex items-center gap-2">
                                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                                  {autoclave.nome}
                                </div>
                                <Badge variant="secondary" className="ml-2 text-xs">
                                  {count}
                                </Badge>
                              </div>
                            </SelectItem>
                          ) : null
                        })}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {/* 📊 Indicatori filtri attivi */}
                {(searchTerm || selectedAutoclave !== 'all') && (
                  <div className="flex items-center gap-2 pt-2 border-t">
                    <span className="text-sm text-muted-foreground">Filtri attivi:</span>
                    {searchTerm && (
                      <Badge variant="outline" className="gap-1">
                        Ricerca: "{searchTerm}"
                        <button onClick={() => setSearchTerm('')} className="ml-1 hover:text-red-500">×</button>
                      </Badge>
                    )}
                    {selectedAutoclave !== 'all' && (
                      <Badge variant="outline" className="gap-1">
                        Autoclave: {nestings.find(n => n.autoclave.id.toString() === selectedAutoclave)?.autoclave.nome}
                        <button onClick={() => setSelectedAutoclave('all')} className="ml-1 hover:text-red-500">×</button>
                      </Badge>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Lista nesting */}
          {isLoading ? (
            <Card>
              <CardContent className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin mr-3" />
                <span className="text-lg">Caricamento nesting...</span>
              </CardContent>
            </Card>
          ) : filteredNestings.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-8 text-center">
                <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Nessun nesting trovato</h3>
                <p className="text-muted-foreground mb-4">
                  {searchTerm || selectedAutoclave !== 'all' 
                    ? 'Prova a modificare i filtri di ricerca.' 
                    : 'Non ci sono nesting disponibili per questo stato.'}
                </p>
                {searchTerm || selectedAutoclave !== 'all' ? (
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setSearchTerm('')
                      setSelectedAutoclave('all')
                    }}
                  >
                    Cancella filtri
                  </Button>
                ) : null}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <div className="h-6 w-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
                        <span className="text-white text-xs font-bold">{filteredNestings.length}</span>
                      </div>
                      Lista Nesting
                    </CardTitle>
                    <CardDescription>
                      {filteredNestings.length} di {nestings.length} nesting
                      {searchTerm && ` corrispondenti a "${searchTerm}"`}
                    </CardDescription>
                  </div>
                  
                  {/* 📱 Toggle vista mobile/desktop */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="sm:hidden"
                      onClick={() => {/* Toggle vista mobile */}}
                    >
                      Vista compatta
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* 📱 Vista mobile - Cards */}
                <div className="block sm:hidden space-y-4">
                  {filteredNestings.map(nesting => (
                    <Card 
                      key={nesting.id} 
                      className="cursor-pointer hover:shadow-md transition-all duration-200 border-l-4 border-l-blue-500"
                      onClick={() => handleRowClick(nesting)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="font-bold text-lg">#{nesting.id}</div>
                            <div className="text-sm text-muted-foreground">
                              {formatDateIT(new Date(nesting.created_at))}
                            </div>
                          </div>
                          <NestingStatusBadge 
                            stato={nesting.stato} 
                            confermato_da_ruolo={nesting.confermato_da_ruolo}
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Autoclave:</span>
                            <span className="text-sm">{nesting.autoclave.nome}</span>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">ODL:</span>
                            <Badge variant="secondary" className="text-xs">
                              {nesting.odl_list.length}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 pt-2">
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Area</div>
                              <Badge 
                                variant={
                                  (nesting.area_utilizzata / nesting.area_totale) > 0.8 ? "default" : 
                                  (nesting.area_utilizzata / nesting.area_totale) > 0.6 ? "secondary" : "outline"
                                }
                                className="text-xs"
                              >
                                {formatPercent(nesting.area_utilizzata, nesting.area_totale)}
                              </Badge>
                            </div>
                            <div className="text-center">
                              <div className="text-xs text-muted-foreground">Valvole</div>
                              <Badge 
                                variant={
                                  (nesting.valvole_utilizzate / nesting.valvole_totali) > 0.8 ? "default" : 
                                  (nesting.valvole_utilizzate / nesting.valvole_totali) > 0.6 ? "secondary" : "outline"
                                }
                                className="text-xs"
                              >
                                {formatPercent(nesting.valvole_utilizzate, nesting.valvole_totali)}
                              </Badge>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between pt-2 border-t">
                            <div className="flex gap-1">
                              <NestingActions 
                                nesting={nesting} 
                                onUpdate={() => fetchNestings(activeTab === 'all' ? undefined : activeTab)}
                              />
                            </div>
                            <div className="flex gap-1">
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                onClick={(e) => handleDownloadReport(nesting, e)}
                                className="h-8 w-8 hover:bg-green-100 hover:text-green-700"
                              >
                                <Download className="h-3 w-3" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleRowClick(nesting)
                                }}
                                className="h-8 w-8 hover:bg-primary/10"
                              >
                                <Info className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                {/* 🖥️ Vista desktop - Tabella */}
                <div className="hidden sm:block border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-20">ID</TableHead>
                        <TableHead>Data Creazione</TableHead>
                        <TableHead>Autoclave</TableHead>
                        <TableHead>ODL Inclusi</TableHead>
                        <TableHead className="text-center">Stato</TableHead>
                        <TableHead className="text-center">Area Utilizzata</TableHead>
                        <TableHead className="text-center">Valvole Utilizzate</TableHead>
                        <TableHead className="text-center">Piani</TableHead>
                        <TableHead className="text-center w-20">Azioni</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredNestings.map(nesting => (
                        <TableRow 
                          key={nesting.id} 
                          className="hover:bg-muted/50 cursor-pointer"
                          onClick={() => handleRowClick(nesting)}
                        >
                          <TableCell className="font-bold">#{nesting.id}</TableCell>
                          <TableCell>
                            <div className="flex flex-col">
                              <span className="font-medium">{formatDateIT(new Date(nesting.created_at))}</span>
                              <span className="text-xs text-muted-foreground">
                                {new Date(nesting.created_at).toLocaleTimeString('it-IT', { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{nesting.autoclave.nome}</div>
                              <div className="text-xs text-muted-foreground">{nesting.autoclave.codice}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {formatODLList(nesting.odl_list)}
                              <Badge variant="secondary" className="text-xs">
                                {nesting.odl_list.length}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <NestingStatusBadge 
                              stato={nesting.stato} 
                              confermato_da_ruolo={nesting.confermato_da_ruolo}
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex flex-col items-center">
                              <Badge 
                                variant={
                                  (nesting.area_utilizzata / nesting.area_totale) > 0.8 ? "default" : 
                                  (nesting.area_utilizzata / nesting.area_totale) > 0.6 ? "secondary" : "outline"
                                }
                              >
                                {formatPercent(nesting.area_utilizzata, nesting.area_totale)}
                              </Badge>
                              <span className="text-xs text-muted-foreground mt-1">
                                {nesting.area_utilizzata.toFixed(1)} / {nesting.area_totale.toFixed(1)} m²
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex flex-col items-center">
                              <Badge 
                                variant={
                                  (nesting.valvole_utilizzate / nesting.valvole_totali) > 0.8 ? "default" : 
                                  (nesting.valvole_utilizzate / nesting.valvole_totali) > 0.6 ? "secondary" : "outline"
                                }
                              >
                                {formatPercent(nesting.valvole_utilizzate, nesting.valvole_totali)}
                              </Badge>
                              <span className="text-xs text-muted-foreground mt-1">
                                {nesting.valvole_utilizzate} / {nesting.valvole_totali}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            {/* ✅ SEZIONE 2: Indicatore piani utilizzati */}
                            <div className="flex flex-col items-center">
                              {nesting.area_piano_1 && nesting.area_piano_1 > 0 && (
                                <Badge variant="outline" className="text-xs mb-1">
                                  Piano 1: {nesting.area_piano_1.toFixed(0)}cm²
                                </Badge>
                              )}
                              {nesting.area_piano_2 && nesting.area_piano_2 > 0 && (
                                <Badge variant="secondary" className="text-xs">
                                  Piano 2: {nesting.area_piano_2.toFixed(0)}cm²
                                </Badge>
                              )}
                              {(!nesting.area_piano_1 || nesting.area_piano_1 === 0) && (!nesting.area_piano_2 || nesting.area_piano_2 === 0) && (
                                <Badge variant="outline" className="text-xs">
                                  ⚠️ Non assegnato
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-1">
                              <NestingActions 
                                nesting={nesting} 
                                onUpdate={() => fetchNestings(activeTab === 'all' ? undefined : activeTab)}
                              />
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                onClick={(e) => handleDownloadReport(nesting, e)}
                                className="hover:bg-green-100 hover:text-green-700"
                                title={`Scarica report per nesting #${nesting.id}`}
                              >
                                <Download className="h-4 w-4" />
                                <span className="sr-only">Scarica report nesting #{nesting.id}</span>
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleRowClick(nesting)
                                }}
                                className="hover:bg-primary/10"
                              >
                                <Info className="h-4 w-4" />
                                <span className="sr-only">Dettagli nesting #{nesting.id}</span>
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Dialog dettagli nesting */}
      {selectedNesting && (
        <NestingDetails
          nesting={selectedNesting}
          isOpen={detailsOpen}
          onClose={() => setDetailsOpen(false)}
        />
      )}
    </div>
  )
} 