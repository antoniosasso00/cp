'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { NestingResponse, nestingApi, NestingPreview, NestingDraft } from '@/lib/api'
import { formatDateIT } from '@/lib/utils'
import { Loader2, RefreshCw, Info, Search, Filter, Download, Plus, AlertCircle, Settings } from 'lucide-react'
import { NestingDetails } from './components/nesting-details'
import NestingPreviewModal from './components/nesting-preview-modal'
import ExcludedODLManager from './components/excluded-odl-manager'
import ManualNestingSelector from './components/manual-nesting-selector'
import NestingAssignmentModal from './components/nesting-assignment-modal'
import { NestingStatusBadge } from '@/components/nesting/NestingStatusBadge'
import { NestingActions } from '@/components/nesting/NestingActions'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useUserRole } from '@/hooks/useUserRole'

export default function NestingPage() {
  const { role } = useUserRole()
  const [nestings, setNestings] = useState<NestingResponse[]>([])
  const [filteredNestings, setFilteredNestings] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedNesting, setSelectedNesting] = useState<NestingResponse | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'created_at' | 'area_utilizzata' | 'valvole_utilizzate'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // Nuovi stati per preview e bozze
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewData, setPreviewData] = useState<NestingPreview | null>(null)
  const [isLoadingPreview, setIsLoadingPreview] = useState(false)
  const [drafts, setDrafts] = useState<NestingDraft[]>([])
  const [draftsOpen, setDraftsOpen] = useState(false)
  
  // Stati per gestione ODL esclusi
  const [excludedODLOpen, setExcludedODLOpen] = useState(false)
  
  // Stati per nesting manuale
  const [manualNestingOpen, setManualNestingOpen] = useState(false)
  
  // Stati per assegnazione nesting
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false)
  
  const { toast } = useToast()

  // Funzione per caricare i nesting dal backend
  const fetchNestings = async (statusFilter?: string) => {
    try {
      setIsLoading(true)
      const data = await nestingApi.getAll({ 
        ruolo_utente: role || undefined,
        stato_filtro: statusFilter || undefined
      })
      setNestings(data)
      setFilteredNestings(data)
    } catch (error) {
      console.error('Errore nel caricamento dei nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore di caricamento',
        description: 'Impossibile caricare i nesting. Verifica la connessione al server.',
      })
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

  // Genera un nuovo nesting automatico
  const handleGenerateNesting = async () => {
    try {
      setIsGenerating(true)
      const newNesting = await nestingApi.generateAuto()
      
      toast({
        title: 'Nesting generato con successo!',
        description: `Nuovo nesting #${newNesting.id} creato per autoclave ${newNesting.autoclave.nome}`,
      })
      
      // Ricarica la lista
      fetchNestings()
      
      // Mostra automaticamente i dettagli del nuovo nesting
      setSelectedNesting(newNesting)
      setDetailsOpen(true)
      
    } catch (error) {
      console.error('Errore nella generazione del nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella generazione',
        description: 'Impossibile generare il nesting. Controlla che ci siano ODL in attesa di cura.',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  // Mostra i dettagli di un nesting
  const handleRowClick = (nesting: NestingResponse) => {
    setSelectedNesting(nesting)
    setDetailsOpen(true)
  }

  // Formatta il valore percentuale
  const formatPercent = (value: number, total: number) => {
    if (total === 0) return '0%'
    return `${Math.round((value / total) * 100)}%`
  }

  // Formatta la lista di ODL per la visualizzazione in tabella
  const formatODLList = (odl_list: NestingResponse['odl_list']) => {
    if (!odl_list || odl_list.length === 0) return <span className="text-muted-foreground text-sm">Nessun ODL</span>
    
    return (
      <div className="flex flex-wrap gap-1 max-w-xs">
        {odl_list.slice(0, 3).map(odl => (
          <Badge key={odl.id} variant="outline" className="whitespace-nowrap text-xs">
            #{odl.id}
          </Badge>
        ))}
        {odl_list.length > 3 && (
          <Badge variant="secondary" className="text-xs">
            +{odl_list.length - 3}
          </Badge>
        )}
      </div>
    )
  }

  // Lista delle autoclavi uniche per il filtro
  const uniqueAutoclaves = Array.from(
    new Set(nestings.map(n => JSON.stringify({ id: n.autoclave.id, nome: n.autoclave.nome })))
  ).map(str => JSON.parse(str))

  // Calcolo statistiche per le card informative
  const stats = {
    totalNestings: nestings.length,
    averageAreaUsage: nestings.length > 0 
      ? Math.round(nestings.reduce((sum, n) => sum + (n.area_utilizzata / n.area_totale) * 100, 0) / nestings.length)
      : 0,
    averageValveUsage: nestings.length > 0
      ? Math.round(nestings.reduce((sum, n) => sum + (n.valvole_utilizzate / n.valvole_totali) * 100, 0) / nestings.length)
      : 0,
    totalODLProcessed: nestings.reduce((sum, n) => sum + n.odl_list.length, 0)
  }

  // Callback per quando viene creato un nesting manuale
  const handleManualNestingCreated = (result: any) => {
    // Ricarica la lista dei nesting
    fetchNestings()
    
    // Chiudi il modal
    setManualNestingOpen(false)
    
    // Mostra un messaggio di successo aggiuntivo
    toast({
      title: 'Nesting manuale completato!',
      description: `${result.odl_pianificati.length} ODL pianificati in ${result.autoclavi.length} autoclave`,
    })
  }

  // Callback per quando viene completata un'assegnazione
  const handleAssignmentComplete = () => {
    console.log('Assegnazione nesting completata')
    
    // Ricarica la lista dei nesting per aggiornare gli stati
    fetchNestings()
    
    // Chiudi il modal
    setAssignmentModalOpen(false)
  }

  // Nuova funzione per generare preview
  const handleGeneratePreview = async () => {
    try {
      setIsLoadingPreview(true)
      const preview = await nestingApi.getPreview()
      setPreviewData(preview)
      setPreviewOpen(true)
      
      if (preview.success) {
        toast({
          title: 'Preview generata!',
          description: preview.message,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Nessun ODL disponibile',
          description: preview.message,
        })
      }
    } catch (error) {
      console.error('Errore nella generazione del preview:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella preview',
        description: 'Impossibile generare la preview del nesting.',
      })
    } finally {
      setIsLoadingPreview(false)
    }
  }

  // Funzione per salvare come bozza
  const handleSaveDraft = async () => {
    if (!previewData || !previewData.success) {
      toast({
        variant: 'destructive',
        title: 'Nessuna preview disponibile',
        description: 'Genera prima una preview per salvare come bozza.',
      })
      return
    }

    try {
      const draftData = {
        autoclavi: previewData.autoclavi,
        odl_esclusi: previewData.odl_esclusi.map(odl => odl.id)
      }
      
      const result = await nestingApi.saveDraft(draftData)
      
      if (result.success) {
        toast({
          title: 'Bozza salvata!',
          description: result.message,
        })
        setPreviewOpen(false)
        fetchDrafts() // Ricarica la lista delle bozze
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore nel salvataggio',
          description: result.message,
        })
      }
    } catch (error) {
      console.error('Errore nel salvataggio della bozza:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nel salvataggio',
        description: 'Impossibile salvare la bozza.',
      })
    }
  }

  // Funzione per caricare le bozze
  const fetchDrafts = async () => {
    try {
      const result = await nestingApi.listDrafts()
      if (result.success) {
        setDrafts(result.drafts)
      }
    } catch (error) {
      console.error('Errore nel caricamento delle bozze:', error)
    }
  }

  // Carica le bozze all'avvio
  useEffect(() => {
    fetchDrafts()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header con titolo e azioni principali */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nesting Ottimizzato</h1>
          <p className="text-muted-foreground mt-1">
            Sistema di ottimizzazione automatica per l'utilizzo delle autoclavi
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline"
            onClick={() => fetchNestings()}
            disabled={isLoading}
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
                      <Button 
              variant="outline"
              onClick={handleGeneratePreview}
              disabled={isLoadingPreview || isLoading}
              size="sm"
            >
              {isLoadingPreview ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Preview...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Preview Nesting
                </>
              )}
            </Button>
            <Button 
              variant="outline"
              onClick={() => setExcludedODLOpen(true)}
              disabled={isLoading}
              size="sm"
            >
              <AlertCircle className="h-4 w-4 mr-2" />
              ODL Esclusi
            </Button>
            <Button 
              variant="outline"
              onClick={() => setManualNestingOpen(true)}
              disabled={isLoading}
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nesting Manuale
            </Button>
            <Button 
              variant="outline"
              onClick={() => setAssignmentModalOpen(true)}
              disabled={isLoading}
              size="sm"
            >
              <Settings className="h-4 w-4 mr-2" />
              Assegna ad Autoclave
            </Button>
          <Button 
            onClick={handleGenerateNesting} 
            disabled={isGenerating || isLoading}
            className="flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generazione in corso...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                Genera Nesting Automatico
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Statistiche generali */}
      {!isLoading && nestings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Nesting Totali</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalNestings}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">ODL Processati</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalODLProcessed}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Utilizzo Area Medio</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.averageAreaUsage}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Utilizzo Valvole Medio</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.averageValveUsage}%</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filtri e ricerca */}
      {!isLoading && nestings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filtri e Ricerca
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">Ricerca</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Cerca per ID, autoclave, part number..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="sm:w-48">
                <label className="text-sm font-medium mb-2 block">Autoclave</label>
                <Select value={selectedAutoclave} onValueChange={setSelectedAutoclave}>
                  <SelectTrigger>
                    <SelectValue placeholder="Tutte le autoclavi" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tutte le autoclavi</SelectItem>
                    {uniqueAutoclaves
                      .filter(autoclave => autoclave?.id && autoclave?.nome)
                      .map(autoclave => (
                        <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                          {autoclave.nome}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="sm:w-40">
                <label className="text-sm font-medium mb-2 block">Ordina per</label>
                <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Data creazione</SelectItem>
                    <SelectItem value="area_utilizzata">Utilizzo area</SelectItem>
                    <SelectItem value="valvole_utilizzate">Utilizzo valvole</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="sm:w-32">
                <label className="text-sm font-medium mb-2 block">Direzione</label>
                <Select value={sortOrder} onValueChange={(value: any) => setSortOrder(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="desc">Decrescente</SelectItem>
                    <SelectItem value="asc">Crescente</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab per stati nesting */}
      {!isLoading && nestings.length > 0 && (
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">Tutti</TabsTrigger>
            <TabsTrigger value="In sospeso">In Sospeso</TabsTrigger>
            <TabsTrigger value="Confermato">Confermati</TabsTrigger>
            <TabsTrigger value="Completato">Completati</TabsTrigger>
          </TabsList>
        </Tabs>
      )}

      {/* Contenuto principale */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin" />
            <div className="text-center">
              <p className="text-lg font-medium">Caricamento nesting...</p>
              <p className="text-sm text-muted-foreground">
                Recupero i dati dal server
              </p>
            </div>
          </div>
        </div>
      ) : nestings.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <div className="text-center space-y-4">
              <div>
                <p className="text-xl font-medium">Nessun nesting generato</p>
                <p className="text-sm text-muted-foreground">
                  Genera il primo nesting automatico per ottimizzare l'uso delle autoclavi
                </p>
              </div>
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Il sistema analizzerà automaticamente gli ODL in stato "Attesa Cura" e genererà 
                  un layout ottimizzato per massimizzare l'utilizzo dell'autoclave.
                </AlertDescription>
              </Alert>
              <Button 
                onClick={handleGenerateNesting} 
                disabled={isGenerating}
                size="lg"
                className="mt-4"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Generazione in corso...
                  </>
                ) : (
                  <>
                    <Plus className="h-5 w-5 mr-2" />
                    Genera Primo Nesting
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : filteredNestings.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <Search className="h-8 w-8 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Nessun risultato trovato</p>
            <p className="text-sm text-muted-foreground">
              Prova a modificare i filtri di ricerca
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Lista Nesting</CardTitle>
                <CardDescription>
                  {filteredNestings.length} di {nestings.length} nesting
                  {searchTerm && ` corrispondenti a "${searchTerm}"`}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg overflow-hidden">
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
                        <div className="flex items-center justify-center gap-1">
                          <NestingActions 
                            nesting={nesting} 
                            onUpdate={() => fetchNestings(activeTab === 'all' ? undefined : activeTab)}
                          />
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

      {/* Dialog dettagli nesting */}
      {selectedNesting && (
        <NestingDetails
          nesting={selectedNesting}
          isOpen={detailsOpen}
          onClose={() => setDetailsOpen(false)}
        />
      )}

      {/* Modal preview nesting interattiva */}
      <NestingPreviewModal
        isOpen={previewOpen}
        onClose={() => setPreviewOpen(false)}
        previewData={previewData}
        onSaveDraft={handleSaveDraft}
        onApprove={async () => {
          try {
            // Genera il nesting finale basato sulla preview approvata
            const finalNesting = await nestingApi.generateAuto()
            
            toast({
              title: 'Nesting approvato e generato!',
              description: `Nesting #${finalNesting.id} creato per autoclave ${finalNesting.autoclave.nome}`,
            })
            
            // Ricarica la lista e chiudi il modal
            fetchNestings()
            setPreviewOpen(false)
            
            // Mostra automaticamente i dettagli del nuovo nesting
            setSelectedNesting(finalNesting)
            setDetailsOpen(true)
            
          } catch (error) {
            console.error('Errore nell\'approvazione del nesting:', error)
            toast({
              variant: 'destructive',
              title: 'Errore nell\'approvazione',
              description: 'Impossibile generare il nesting finale.',
            })
          }
        }}
      />

      {/* Modal gestione ODL esclusi */}
      <ExcludedODLManager
        isOpen={excludedODLOpen}
        onClose={() => setExcludedODLOpen(false)}
        onODLReintegrated={() => {
          fetchNestings()
          setExcludedODLOpen(false)
        }}
      />

      {/* Modal nesting manuale */}
      {manualNestingOpen && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="w-full max-w-6xl max-h-[90vh] overflow-auto">
              <ManualNestingSelector
                onNestingCreated={handleManualNestingCreated}
                onClose={() => setManualNestingOpen(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Modal assegnazione nesting */}
      <NestingAssignmentModal
        isOpen={assignmentModalOpen}
        onClose={() => setAssignmentModalOpen(false)}
        onAssignmentComplete={handleAssignmentComplete}
      />
    </div>
  )
} 