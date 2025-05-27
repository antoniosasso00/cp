'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
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
import { catalogoApi, tempoFasiApi, odlApi, CatalogoResponse } from '@/lib/api'
import { formatDuration, formatDateTime } from '@/lib/utils'
import TempoFaseModal from '../../clean-room/tempi/components/tempo-fase-modal'

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
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
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
  
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica tutti i dati necessari
      const [catalogoData, tempiData, odlData] = await Promise.all([
        catalogoApi.getAll(),
        tempoFasiApi.getAll(),
        odlApi.getAll()
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
      const fasi = ['laminazione', 'attesa_cura', 'cura']
      const previsioni: StatisticheFasi = {}
      
      for (const fase of fasi) {
        try {
          const previsione = await tempoFasiApi.getPrevisione(fase, selectedPartNumber)
          previsioni[fase] = previsione
        } catch (error) {
          console.warn(`Errore nel caricamento previsione per fase ${fase}:`, error)
          previsioni[fase] = {
            fase,
            media_minuti: 0,
            numero_osservazioni: 0
          }
        }
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
    const fasi = ['laminazione', 'attesa_cura', 'cura']
    
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
    
    const totaleODL = odlList.filter(odl => 
      !selectedPartNumber || odl.parte?.part_number === selectedPartNumber
    ).length
    
    return {
      totale_odl: totaleODL,
      previsioni
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (catalogo.length > 0 && tempiFasi.length > 0 && odlList.length > 0) {
      loadStatistiche()
    }
  }, [selectedPartNumber, selectedStatus, selectedPeriod])

  // Gestione azioni
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

  const handleRestoreStatus = async (odlId: number) => {
    if (!window.confirm(`Sei sicuro di voler ripristinare lo stato precedente dell'ODL ${odlId}?`)) {
      return
    }

    try {
      const result = await odlApi.restoreStatus(odlId)
      toast({
        title: 'Stato ripristinato',
        description: `✅ Stato ODL ${odlId} ripristinato a: ${result.status}`,
      })
      fetchData() // Ricarica i dati per mostrare le modifiche
    } catch (error) {
      console.error(`Errore durante il ripristino:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile ripristinare lo stato dell'ODL. ${error instanceof Error ? error.message : ''}`,
      })
    }
  }

  const handleDeleteODL = async (odlId: number) => {
    if (!window.confirm(`Sei sicuro di voler eliminare definitivamente l'ODL ${odlId}? Questa azione non può essere annullata.`)) {
      return
    }

    try {
      await odlApi.delete(odlId)
      toast({
        title: 'ODL eliminato',
        description: `ODL ${odlId} eliminato con successo.`,
      })
      fetchData()
    } catch (error) {
      console.error(`Errore durante l'eliminazione ODL:`, error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: `Impossibile eliminare l'ODL.`,
      })
    }
  }

  // Funzioni di calcolo per le statistiche
  const calcolaTotaleMedie = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    
    const medie = Object.values(statistiche.previsioni)
      .filter(p => p.media_minuti > 0)
      .map(p => p.media_minuti);
    
    return medie.length > 0 ? medie.reduce((sum, m) => sum + m, 0) : 0;
  }

  const calcolaFasiAttive = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    return Object.values(statistiche.previsioni).filter(p => p.numero_osservazioni > 0).length;
  }

  const calcolaScostamentoMedio = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    
    const tempiStandard = {
      'laminazione': 120,    // 2 ore
      'attesa_cura': 60,     // 1 ora
      'cura': 300            // 5 ore
    };
    
    let scostamentoTotale = 0;
    let fasiConDati = 0;
    
    try {
      Object.entries(statistiche.previsioni).forEach(([fase, dati]) => {
        if (dati && typeof dati === 'object' && 'media_minuti' in dati) {
          const mediaReale = dati.media_minuti || 0;
          const tempoStandard = tempiStandard[fase as keyof typeof tempiStandard] || 0;
          
          if (mediaReale > 0 && tempoStandard > 0) {
            const scostamento = ((mediaReale - tempoStandard) / tempoStandard) * 100;
            scostamentoTotale += Math.abs(scostamento);
            fasiConDati++;
          }
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo dello scostamento medio:', err);
    }
    
    return fasiConDati > 0 ? scostamentoTotale / fasiConDati : 0;
  }

  // Filtraggio dati
  const filteredItems = tempiFasi.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    const odlInfo = getOdlInfo(item.odl_id)
    
    // Filtro per ricerca
    const matchesSearch = (
      (odlInfo?.parte?.part_number?.toLowerCase()?.includes(searchLower)) ||
      String(item.odl_id).includes(searchLower) ||
      translateFase(item.fase).toLowerCase().includes(searchLower) ||
      (item.note && item.note.toLowerCase().includes(searchLower))
    )
    
    // Filtro per part number
    const matchesPartNumber = !selectedPartNumber || 
      odlInfo?.parte?.part_number === selectedPartNumber
    
    // Filtro per stato ODL
    const matchesStatus = !selectedStatus || 
      odlInfo?.status === selectedStatus
    
    return matchesSearch && matchesPartNumber && matchesStatus
  })

  const getOdlInfo = (odlId: number) => {
    return odlList.find(odl => odl.id === odlId) || null;
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
    if (!statistiche) return false;
    
    try {
      const totaleODL = statistiche.totale_odl || 0;
      return totaleODL > 0;
    } catch (err) {
      console.error('Errore nella verifica dei dati validi:', err);
      return false;
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Caricamento dati di monitoraggio...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoraggio & Performance</h1>
          <p className="text-muted-foreground">
            Dashboard unificata per statistiche, tempi di produzione e performance
          </p>
        </div>
        <Button onClick={handleCreateClick}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Nuovo Tempo
        </Button>
      </div>

      {/* Filtri globali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Filtri Globali
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Ricerca</Label>
              <Input
                id="search"
                placeholder="Cerca nei dati..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="part-number">Part Number</Label>
              <Select value={selectedPartNumber} onValueChange={setSelectedPartNumber}>
                <SelectTrigger id="part-number">
                  <SelectValue placeholder="Tutti i part number" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tutti i part number</SelectItem>
                  {getUniquePartNumbers().map(pn => (
                    <SelectItem key={pn} value={pn}>{pn}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status">Stato ODL</Label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger id="status">
                  <SelectValue placeholder="Tutti gli stati" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tutti gli stati</SelectItem>
                  {getUniqueStatuses().map(status => (
                    <SelectItem key={status} value={status}>{status}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="period">Periodo</Label>
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger id="period">
                  <SelectValue placeholder="Seleziona periodo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Ultimi 7 giorni</SelectItem>
                  <SelectItem value="30">Ultimi 30 giorni</SelectItem>
                  <SelectItem value="90">Ultimi 90 giorni</SelectItem>
                  <SelectItem value="365">Ultimo anno</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs principali */}
      <Tabs defaultValue="performance" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Performance Generale
          </TabsTrigger>
          <TabsTrigger value="statistiche" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Statistiche Catalogo
          </TabsTrigger>
          <TabsTrigger value="tempi" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Tempi per ODL
          </TabsTrigger>
        </TabsList>

        {/* Tab Performance Generale */}
        <TabsContent value="performance" className="space-y-6">
          {!hasDatiValidi() ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato disponibile</AlertTitle>
              <AlertDescription>
                Nessun dato disponibile per il filtro selezionato. Prova a modificare i filtri o aggiungi nuovi ODL.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold">
                    {statistiche?.totale_odl || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    ODL Totali
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold">
                    {formatDuration(calcolaTotaleMedie())}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Tempo Medio Totale
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-2xl font-bold">
                    {calcolaFasiAttive()}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Fasi Registrate
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6 text-center">
                  <div className={`text-2xl font-bold ${
                    calcolaScostamentoMedio() > 20 ? 'text-red-600' : 
                    calcolaScostamentoMedio() > 10 ? 'text-orange-600' : 'text-green-600'
                  }`}>
                    {calcolaScostamentoMedio().toFixed(1)}%
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Scostamento Medio
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Tab Statistiche Catalogo */}
        <TabsContent value="statistiche" className="space-y-6">
          {!hasDatiValidi() ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato disponibile</AlertTitle>
              <AlertDescription>
                Nessun dato disponibile per il filtro selezionato. Prova a modificare i filtri o aggiungi nuovi ODL.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Dettaglio tempi per fase</h3>
              
              {statistiche && statistiche.previsioni && Object.entries(statistiche.previsioni).map(([fase, dati]) => {
                if (!dati) return null;
                
                const tempiStandard = {
                  'laminazione': 120,
                  'attesa_cura': 60,
                  'cura': 300
                };
                
                const mediaReale = dati.media_minuti || 0;
                const tempoStandard = tempiStandard[fase as keyof typeof tempiStandard] || 0;
                const scostamento = tempoStandard > 0 ? ((mediaReale - tempoStandard) / tempoStandard) * 100 : 0;
                
                return (
                  <Card key={fase}>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-center">
                        <h4 className="font-medium">{translateFase(fase)}</h4>
                        <div className="text-right">
                          <div className="text-xl font-bold">{formatDuration(dati.media_minuti || 0)}</div>
                          {tempoStandard > 0 && (
                            <div className={`text-sm ${
                              Math.abs(scostamento) > 20 ? 'text-red-600' : 
                              Math.abs(scostamento) > 10 ? 'text-orange-600' : 'text-green-600'
                            }`}>
                              {scostamento > 0 ? '+' : ''}{scostamento.toFixed(1)}% vs standard
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <div className="text-sm text-muted-foreground">
                          Basato su {dati.numero_osservazioni || 0} osservazioni
                        </div>
                        {tempoStandard > 0 && (
                          <div className="text-sm text-muted-foreground">
                            Standard: {formatDuration(tempoStandard)}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
              
              {(!statistiche || !statistiche.previsioni || Object.keys(statistiche.previsioni).length === 0) && (
                <div className="text-center text-muted-foreground py-4">
                  Nessun dato disponibile per le fasi di produzione
                </div>
              )}
            </div>
          )}
        </TabsContent>

        {/* Tab Tempi per ODL */}
        <TabsContent value="tempi" className="space-y-6">
          {filteredItems.length === 0 ? (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Nessun dato disponibile</AlertTitle>
              <AlertDescription>
                Nessun dato di monitoraggio tempi trovato per il filtro selezionato.
              </AlertDescription>
            </Alert>
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
                {filteredItems.map(item => {
                  const odlInfo = getOdlInfo(item.odl_id);
                  const isOdlCompleted = odlInfo?.status === 'Finito';
                  
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
                        {formatDurationLocal(item.durata_minuti)}
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
                            {isOdlCompleted && (
                              <>
                                <DropdownMenuItem onClick={() => handleRestoreStatus(item.odl_id)}>
                                  <RotateCcw className="mr-2 h-4 w-4" />
                                  <span>Ripristina Stato</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleDeleteODL(item.odl_id)}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  <span>Elimina ODL</span>
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </TabsContent>
      </Tabs>

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