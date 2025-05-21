'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { catalogoApi, tempoFasiApi, CatalogoResponse } from '@/lib/api'
import { Loader2, AlertCircle } from 'lucide-react'
import { formatDuration } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'

// Definizione di tipi per le statistiche
interface StatisticheFasi {
  [key: string]: {
    fase: string;
    media_minuti: number;
    numero_osservazioni: number;
  };
}

interface StatistichePartNumber {
  part_number: string;
  previsioni: StatisticheFasi;
  totale_odl: number;
}

export default function StatisticheCatalogo() {
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')
  const [rangeTempo, setRangeTempo] = useState<string>('30')
  const [statistiche, setStatistiche] = useState<StatistichePartNumber | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Carica il catalogo al caricamento della pagina
  useEffect(() => {
    const fetchCatalogo = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await catalogoApi.getAll()
        setCatalogo(data.filter(item => item.attivo)) // Solo parti attive
      } catch (err) {
        console.error('Errore nel caricamento del catalogo:', err)
        setError('Impossibile caricare il catalogo. Riprova più tardi.')
        toast({
          variant: 'destructive',
          title: 'Errore',
          description: 'Impossibile caricare il catalogo. Riprova più tardi.',
        })
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchCatalogo()
  }, [toast])

  // Carica le statistiche quando cambia il part number selezionato o il range temporale
  useEffect(() => {
    let isMounted = true;

    const fetchStatistiche = async () => {
      if (!selectedPartNumber) {
        setStatistiche(null)
        return
      }
      
      try {
        setLoadingStats(true)
        setError(null)
        
        // Chiamata all'API per recuperare le statistiche
        const giorni = parseInt(rangeTempo)
        const result = await tempoFasiApi.getStatisticheByPartNumber(selectedPartNumber, giorni)
        
        if (isMounted) {
          setStatistiche(result)
        }
      } catch (err) {
        console.error('Errore nel caricamento delle statistiche:', err)
        if (isMounted) {
          setError('Impossibile caricare le statistiche. Riprova più tardi.')
          toast({
            variant: 'destructive',
            title: 'Errore',
            description: 'Impossibile caricare le statistiche. Riprova più tardi.',
          })
        }
      } finally {
        if (isMounted) {
          setLoadingStats(false)
        }
      }
    }
    
    if (selectedPartNumber) {
      fetchStatistiche()
    }

    return () => {
      isMounted = false;
    };
  }, [selectedPartNumber, rangeTempo, toast])

  // Filtra il catalogo in base alla ricerca
  const filteredCatalogo = catalogo.filter(item => {
    if (!searchQuery) return true;
    
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number.toLowerCase().includes(searchLower) ||
      (item.descrizione && item.descrizione.toLowerCase().includes(searchLower)) ||
      (item.categoria && item.categoria.toLowerCase().includes(searchLower))
    )
  })

  // Traduci i nomi delle fasi
  const translateFase = (fase: string): string => {
    const translations: Record<string, string> = {
      'laminazione': 'Laminazione',
      'attesa_cura': 'Attesa Cura',
      'cura': 'Cura'
    };
    return translations[fase] || fase;
  }

  // Calcola il totale delle medie per tutte le fasi
  const calcolaTotaleMedie = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    
    let totale = 0;
    
    try {
      Object.values(statistiche.previsioni).forEach(fase => {
        if (fase && typeof fase === 'object' && 'media_minuti' in fase) {
          totale += typeof fase.media_minuti === 'number' ? fase.media_minuti : 0;
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo del totale medie:', err);
    }
    
    return totale;
  }

  // Calcola il numero di fasi attive
  const calcolaFasiAttive = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    
    let fasiAttive = 0;
    
    try {
      Object.values(statistiche.previsioni).forEach(fase => {
        if (fase && typeof fase === 'object' && 'media_minuti' in fase) {
          if (typeof fase.media_minuti === 'number' && fase.media_minuti > 0) {
            fasiAttive++;
          }
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo delle fasi attive:', err);
    }
    
    return fasiAttive;
  }

  // Verifica se ci sono ODL completati
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Statistiche Catalogo</h1>
        <p className="text-muted-foreground">
          Analisi dei tempi di produzione per part number
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Errore</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-4">
        <div className="md:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Filtra</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="search">Cerca Part Number</Label>
                <Input
                  id="search"
                  placeholder="Cerca nel catalogo..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="range">Range Temporale</Label>
                <Select
                  value={rangeTempo}
                  onValueChange={setRangeTempo}
                  disabled={!selectedPartNumber}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona range" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">Ultimi 7 giorni</SelectItem>
                    <SelectItem value="30">Ultimi 30 giorni</SelectItem>
                    <SelectItem value="90">Ultimi 90 giorni</SelectItem>
                    <SelectItem value="365">Ultimo anno</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="pt-4">
                <h3 className="text-sm font-medium mb-2">Part Numbers</h3>
                <div className="max-h-[300px] overflow-y-auto space-y-1">
                  {isLoading ? (
                    <div className="flex justify-center p-4">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : filteredCatalogo.length === 0 ? (
                    <div className="text-sm text-muted-foreground p-2">
                      Nessun part number trovato
                    </div>
                  ) : (
                    filteredCatalogo.map(item => (
                      <div 
                        key={item.part_number}
                        className={`p-2 rounded-md cursor-pointer text-sm ${
                          selectedPartNumber === item.part_number 
                            ? 'bg-primary text-primary-foreground'
                            : 'hover:bg-muted'
                        }`}
                        onClick={() => setSelectedPartNumber(item.part_number)}
                      >
                        <div className="font-medium">{item.part_number}</div>
                        <div className="text-xs truncate">{item.descrizione}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="md:col-span-3">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="text-lg">
                {selectedPartNumber 
                  ? `Statistiche per ${selectedPartNumber}`
                  : 'Seleziona un part number'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedPartNumber ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Seleziona un part number dalla lista per visualizzare le statistiche
                  </p>
                </div>
              ) : loadingStats ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin" />
                  <span className="ml-2">Caricamento statistiche...</span>
                </div>
              ) : !hasDatiValidi() ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Dati insufficienti</AlertTitle>
                  <AlertDescription>
                    Non ci sono ODL completati per il part number selezionato.
                    Le statistiche saranno disponibili quando verranno completati degli ordini di lavoro.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {statistiche?.totale_odl || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ODL Completati
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {formatDuration(calcolaTotaleMedie())}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Tempo Totale Medio
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {calcolaFasiAttive()}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Fasi Registrate
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Dettaglio tempi per fase</h3>
                    
                    {statistiche && statistiche.previsioni && Object.entries(statistiche.previsioni).map(([fase, dati]) => {
                      if (!dati) return null;
                      
                      return (
                        <div key={fase} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-center">
                            <h4 className="font-medium">{translateFase(fase)}</h4>
                            <div className="text-xl font-bold">{formatDuration(dati.media_minuti || 0)}</div>
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            Basato su {dati.numero_osservazioni || 0} osservazioni
                          </div>
                        </div>
                      );
                    })}
                    
                    {(!statistiche || !statistiche.previsioni || Object.keys(statistiche.previsioni).length === 0) && (
                      <div className="text-center text-muted-foreground py-4">
                        Nessun dato disponibile per le fasi di produzione
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 