'use client'

import { useState, useEffect } from 'react'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  CalendarClock, 
  Loader2, 
  PlusCircle, 
  MoreHorizontal, 
  Pencil, 
  Trash2, 
  RotateCcw,
  BarChart3,
  Clock,
  TrendingUp,
  AlertCircle
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'
import { catalogApi, phaseTimesApi, odlApi, CatalogoResponse } from '@/lib/api'
import { formatDuration, formatDateTime } from '@/lib/utils'
import TempoFaseModal from '../../clean-room/tempi/components/tempo-fase-modal'
import TempiPreparazioneMonitor from '@/shared/components/TempiPreparazioneMonitor'

// Tipi per le statistiche
interface StatisticheFasi {
  [key: string]: {
    fase: string;
    media_minuti: number;
    numero_osservazioni: number;
  };
}

interface StatisticheResponse {
  totale_odl: number;
  previsioni: StatisticheFasi;
}

// Funzioni di utilità
const formatDurationLocal = (minutes: number | null): string => {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'preparazione': 'Preparazione',
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "preparazione": "secondary",
    "laminazione": "default",
    "attesa_cura": "warning",
    "cura": "destructive",
  }
  return variants[fase] || "default"
}

export default function MonitoraggioPage() {
  // Stati per i dati
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [tempiFasi, setTempiFasi] = useState<any[]>([])
  const [odlList, setOdlList] = useState<any[]>([])
  const [statistiche, setStatistiche] = useState<StatisticheResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  // Stati per i filtri
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [selectedPeriod, setSelectedPeriod] = useState<string>('30') // giorni
  
  // Stati per i modali
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<any | null>(null)
  
  const { toast } = useStandardToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica tutti i dati necessari
      const [catalogoData, tempiData, odlData] = await Promise.all([
        catalogApi.fetchCatalogItems(),
        phaseTimesApi.fetchPhaseTimes(),
        odlApi.fetchODLs()
      ])
      
      setCatalogo(catalogoData)
      setTempiFasi(tempiData)
      setOdlList(odlData)
      
      // Carica statistiche per il part number selezionato
      await loadStatistiche()
      
    } catch (error) {
      console.error('Errore nel caricamento dei dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati di monitoraggio. Riprova più tardi.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const loadStatistiche = async () => {
    try {
      if (!selectedPartNumber) {
        // Se non c'è un part number selezionato, calcola statistiche generali
        const stats = calcolaStatisticheGenerali()
        setStatistiche(stats)
        return
      }

      // Carica statistiche per il part number specifico
      let previsioni: StatisticheFasi = {}
      
      try {
        const statistichePartNumber = await phaseTimesApi.fetchPhaseTimeStatsByPartNumber(selectedPartNumber)
        // Converte le previsioni dal formato API al formato locale
        Object.entries(statistichePartNumber.previsioni).forEach(([fase, dati]) => {
          previsioni[fase] = {
            fase: dati.fase,
            media_minuti: dati.media_minuti,
            numero_osservazioni: dati.numero_osservazioni
          }
        })
      } catch (error) {
        console.warn(`Errore nel caricamento previsioni per ${selectedPartNumber}:`, error)
        // Fallback con dati vuoti
        const fasi = ['laminazione', 'attesa_cura', 'cura']
        fasi.forEach(fase => {
          previsioni[fase] = {
            fase,
            media_minuti: 0,
            numero_osservazioni: 0
          }
        })
      }
      
      const totaleODL = odlList.filter(odl => 
        !selectedPartNumber || odl.parte?.part_number === selectedPartNumber
      ).length
      
      setStatistiche({
        totale_odl: totaleODL,
        previsioni
      })
      
    } catch (error) {
      console.error('Errore nel caricamento delle statistiche:', error)
    }
  }

  const calcolaStatisticheGenerali = (): StatisticheResponse => {
    const previsioni: StatisticheFasi = {}
    const fasi = ['preparazione', 'laminazione', 'attesa_cura', 'cura']
    
    fasi.forEach(fase => {
      const tempiPerFase = tempiFasi.filter(t => 
        t.fase === fase && 
        t.durata_minuti !== null &&
        (!selectedPartNumber || getOdlInfo(t.odl_id)?.parte?.part_number === selectedPartNumber)
      )
      
      if (tempiPerFase.length > 0) {
        const mediaMinuti = tempiPerFase.reduce((sum, t) => sum + t.durata_minuti, 0) / tempiPerFase.length
        previsioni[fase] = {
          fase,
          media_minuti: mediaMinuti,
          numero_osservazioni: tempiPerFase.length
        }
      } else {
        previsioni[fase] = {
          fase,
          media_minuti: 0,
          numero_osservazioni: 0
        }
      }
    })
    
    return {
      totale_odl: odlList.length,
      previsioni
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (catalogo.length > 0 && odlList.length > 0) {
      loadStatistiche()
    }
  }, [selectedPartNumber, selectedPeriod])

  // Gestori degli eventi
  const handleCreateClick = () => {
    setEditingItem(null)
    setModalOpen(true)
  }

  const handleEditClick = (item: any) => {
    setEditingItem(item)
    setModalOpen(true)
  }

  const handleDeleteClick = async (id: number) => {
    try {
      await phaseTimesApi.deletePhaseTime(id)
      toast({
        title: '✅ Tempo fase eliminato',
        description: 'Il tempo di fase è stato eliminato con successo.',
      })
      await fetchData()
    } catch (error) {
      console.error('Errore durante l\'eliminazione:', error)
      toast({
        variant: 'destructive',
        title: '❌ Errore',
        description: 'Impossibile eliminare il tempo di fase. Riprova più tardi.',
      })
    }
  }

  const handleRestoreStatus = async (odlId: number) => {
    try {
      await odlApi.updateODL(odlId, { status: 'Preparazione' })
      toast({
        title: '✅ Stato ripristinato',
        description: `ODL ${odlId} riportato in stato Preparazione`,
      })
      await fetchData()
    } catch (error) {
      console.error('Errore durante il ripristino:', error)
      toast({
        variant: 'destructive',
        title: '❌ Errore',
        description: 'Impossibile ripristinare lo stato dell\'ODL.',
      })
    }
  }

  const handleDeleteODL = async (odlId: number) => {
    try {
      await odlApi.deleteODL(odlId)
      toast({
        title: '✅ ODL eliminato',
        description: `ODL ${odlId} eliminato con successo`,
      })
      await fetchData()
    } catch (error) {
      console.error('Errore durante l\'eliminazione ODL:', error)
      toast({
        variant: 'destructive',
        title: '❌ Errore',
        description: 'Impossibile eliminare l\'ODL.',
      })
    }
  }

  // Funzioni di calcolo per le statistiche
  const calcolaTotaleMedie = (): number => {
    if (!statistiche?.previsioni) return 0
    
    return Object.values(statistiche.previsioni)
      .reduce((sum, fase) => sum + fase.media_minuti, 0)
  }

  const calcolaFasiAttive = (): number => {
    if (!statistiche?.previsioni) return 0
    
    return Object.values(statistiche.previsioni)
      .filter(fase => fase.numero_osservazioni > 0).length
  }

  const calcolaScostamentoMedio = (): number => {
    if (!statistiche?.previsioni) return 0
    
    // Calcolo semplificato dello scostamento percentuale
    // In un caso reale, dovresti confrontare con tempi standard
    const fasiConDati = Object.values(statistiche.previsioni)
      .filter(fase => fase.numero_osservazioni > 0)
    
    if (fasiConDati.length === 0) return 0
    
    // Simula uno scostamento basato sulla variabilità dei tempi
    const mediaGenerale = calcolaTotaleMedie() / fasiConDati.length
    let scostamenti = 0
    
    fasiConDati.forEach(fase => {
      if (mediaGenerale > 0) {
        scostamenti += Math.abs(fase.media_minuti - mediaGenerale) / mediaGenerale
      }
    })
    
    return (scostamenti / fasiConDati.length) * 100
  }

  // Filtri e ricerca
  const filteredItems = tempiFasi.filter(item => {
    const odlInfo = getOdlInfo(item.odl_id)
    const matchesSearch = !searchQuery || 
      String(item.odl_id).includes(searchQuery) ||
      (odlInfo?.parte?.part_number?.toLowerCase().includes(searchQuery.toLowerCase())) ||
      translateFase(item.fase).toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesPartNumber = !selectedPartNumber || 
      odlInfo?.parte?.part_number === selectedPartNumber
    
    const matchesStatus = !selectedStatus || 
      odlInfo?.status === selectedStatus
    
    // Filtro per periodo (se implementato)
    let matchesPeriod = true
    if (selectedPeriod !== 'all') {
      const days = parseInt(selectedPeriod)
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days)
      const itemDate = new Date(item.inizio_fase)
      matchesPeriod = itemDate >= cutoffDate
    }
    
    return matchesSearch && matchesPartNumber && matchesStatus && matchesPeriod
  })

  const getOdlInfo = (odlId: number) => {
    return odlList.find(odl => odl.id === odlId) || null
  }

  const getUniquePartNumbers = () => {
    const partNumbers = new Set<string>()
    odlList.forEach(odl => {
      if (odl.parte?.part_number) {
        partNumbers.add(odl.parte.part_number)
      }
    })
    return Array.from(partNumbers).sort()
  }

  const getUniqueStatuses = () => {
    const statuses = new Set<string>()
    odlList.forEach(odl => {
      if (odl.status) {
        statuses.add(odl.status)
      }
    })
    return Array.from(statuses).sort()
  }

  const hasDatiValidi = (): boolean => {
    return statistiche !== null && 
           Object.values(statistiche.previsioni).some(fase => fase.numero_osservazioni > 0)
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Caricamento dashboard management...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard Management</h1>
        <p className="text-muted-foreground">
          Monitoraggio e gestione completa dei processi produttivi
        </p>
      </div>

      {/* Filtri Globali */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtri e Ricerca</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Ricerca</Label>
              <Input
                id="search"
                placeholder="ODL, Part Number, Fase..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="partNumber">Part Number</Label>
              <Select
                value={selectedPartNumber}
                onValueChange={setSelectedPartNumber}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti i part number" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tutti</SelectItem>
                  {getUniquePartNumbers().map(pn => (
                    <SelectItem key={pn} value={pn}>{pn}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status">Stato ODL</Label>
              <Select
                value={selectedStatus}
                onValueChange={setSelectedStatus}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti gli stati" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tutti</SelectItem>
                  {getUniqueStatuses().map(status => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="period">Periodo</Label>
              <Select
                value={selectedPeriod}
                onValueChange={setSelectedPeriod}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona periodo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Ultimi 7 giorni</SelectItem>
                  <SelectItem value="30">Ultimi 30 giorni</SelectItem>
                  <SelectItem value="90">Ultimi 90 giorni</SelectItem>
                  <SelectItem value="all">Tutti</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Monitoraggio Tempi Preparazione */}
      <TempiPreparazioneMonitor 
        maxItems={8}
        autoRefresh={true}
        refreshInterval={45000}
      />

      {/* Tabs principali */}
      <Tabs defaultValue="statistiche" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="statistiche" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Statistiche
          </TabsTrigger>
          <TabsTrigger value="tempi" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Tempi di Fase
          </TabsTrigger>
          <TabsTrigger value="gestione" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Gestione ODL
          </TabsTrigger>
        </TabsList>

        <TabsContent value="statistiche" className="space-y-6">
          {/* Riepilogo Statistiche */}
          {hasDatiValidi() ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Totale ODL</CardTitle>
                    <CalendarClock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{statistiche?.totale_odl || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      {selectedPartNumber ? `per ${selectedPartNumber}` : 'totali'}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Tempo Totale Medio</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatDurationLocal(calcolaTotaleMedie())}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      somma delle fasi
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Fasi Attive</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{calcolaFasiAttive()}</div>
                    <p className="text-xs text-muted-foreground">
                      con dati disponibili
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Variabilità</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {calcolaScostamentoMedio().toFixed(1)}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      scostamento medio
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Dettaglio per Fase */}
              <Card>
                <CardHeader>
                  <CardTitle>Dettaglio Tempi per Fase</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(statistiche?.previsioni || {}).map(([nomeFase, dati]) => (
                      <div key={nomeFase} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold">{translateFase(nomeFase)}</h4>
                          <Badge variant={getFaseBadgeVariant(nomeFase)}>
                            {translateFase(nomeFase)}
                          </Badge>
                        </div>
                        
                        <div className="space-y-2">
                          <div>
                            <div className="text-sm text-muted-foreground">Tempo Medio</div>
                            <div className="text-lg font-semibold">
                              {formatDurationLocal(dati.media_minuti)}
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-sm text-muted-foreground">Osservazioni</div>
                            <div className="text-lg font-semibold">
                              {dati.numero_osservazioni}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato disponibile</AlertTitle>
              <AlertDescription>
                Non ci sono dati sufficienti per calcolare le statistiche. 
                Seleziona un part number diverso o amplia il periodo di ricerca.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="tempi" className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium">Tempi di Fase</h3>
              <p className="text-sm text-muted-foreground">
                {filteredItems.length} record trovati
              </p>
            </div>
            <Button onClick={handleCreateClick}>
              <PlusCircle className="h-4 w-4 mr-2" />
              Nuovo Tempo
            </Button>
          </div>

          {filteredItems.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato trovato</AlertTitle>
              <AlertDescription>
                Non ci sono tempi di fase che corrispondono ai filtri selezionati.
              </AlertDescription>
            </Alert>
          ) : (
            <Card>
              <CardContent>
                <Table>
                  <TableCaption>
                    Monitoraggio tempi di produzione per fase
                  </TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ODL</TableHead>
                      <TableHead>Part Number</TableHead>
                      <TableHead>Fase</TableHead>
                      <TableHead>Inizio</TableHead>
                      <TableHead>Fine</TableHead>
                      <TableHead>Durata</TableHead>
                      <TableHead>Note</TableHead>
                      <TableHead>Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredItems.map(item => {
                      const odlInfo = getOdlInfo(item.odl_id)
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
                            {item.fine_fase ? formatDateTime(item.fine_fase) : (
                              <Badge variant="outline">In corso</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <span className={`font-medium ${
                              item.durata_minuti && item.durata_minuti > 480 ? 'text-red-600' : 
                              item.durata_minuti && item.durata_minuti > 240 ? 'text-orange-600' : 'text-green-600'
                            }`}>
                              {formatDurationLocal(item.durata_minuti)}
                            </span>
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate">
                            {item.note || '-'}
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleEditClick(item)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Modifica
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleDeleteClick(item.id)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Elimina
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="gestione" className="space-y-6">
          <div>
            <h3 className="text-lg font-medium">Gestione ODL</h3>
            <p className="text-sm text-muted-foreground">
              Gestisci lo stato e le operazioni sugli ODL
            </p>
          </div>

          <Card>
            <CardContent>
              <Table>
                <TableCaption>
                  Lista degli ODL con azioni di gestione
                </TableCaption>
                <TableHeader>
                  <TableRow>
                    <TableHead>ODL ID</TableHead>
                    <TableHead>Part Number</TableHead>
                    <TableHead>Stato</TableHead>
                    <TableHead>Creato</TableHead>
                    <TableHead>Note</TableHead>
                    <TableHead>Azioni</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {odlList
                    .filter(odl => {
                      const matchesSearch = !searchQuery || 
                        String(odl.id).includes(searchQuery) ||
                        (odl.parte?.part_number?.toLowerCase().includes(searchQuery.toLowerCase()))
                      
                      const matchesPartNumber = !selectedPartNumber || 
                        odl.parte?.part_number === selectedPartNumber
                      
                      const matchesStatus = !selectedStatus || 
                        odl.status === selectedStatus
                      
                      return matchesSearch && matchesPartNumber && matchesStatus
                    })
                    .map(odl => (
                      <TableRow key={odl.id}>
                        <TableCell className="font-medium">{odl.id}</TableCell>
                        <TableCell>{odl.parte?.part_number || 'N/A'}</TableCell>
                        <TableCell>
                          <Badge variant={
                            odl.status === 'Finito' ? 'default' :
                            odl.status === 'Cura' ? 'destructive' :
                            odl.status === 'Laminazione' ? 'secondary' : 'outline'
                          }>
                            {odl.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {formatDateTime(odl.created_at)}
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {odl.note || '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {odl.status !== 'Preparazione' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRestoreStatus(odl.id)}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteODL(odl.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal per tempo fase - TODO: Fix props */}
      {/* {modalOpen && (
        <TempoFaseModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          editingItem={editingItem}
          onSave={fetchData}
        />
      )} */}
    </div>
  )
} 