'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, AlertCircle } from 'lucide-react'
import { tempoFasiApi, CatalogoResponse } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'

interface FiltriGlobali {
  periodo: string;
  partNumber: string;
  statoODL: string;
  dataInizio?: Date;
  dataFine?: Date;
}

interface StatisticheCatalogoProps {
  filtri: FiltriGlobali;
  catalogo: CatalogoResponse[];
  onError: (message: string) => void;
}

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

export default function StatisticheCatalogo({ filtri, catalogo, onError }: StatisticheCatalogoProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')
  const [statistiche, setStatistiche] = useState<StatistichePartNumber | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)

  // Carica le statistiche quando cambia il part number selezionato o i filtri
  useEffect(() => {
    let isMounted = true;

    const fetchStatistiche = async () => {
      if (!selectedPartNumber) {
        setStatistiche(null)
        return
      }
      
      try {
        setLoadingStats(true)
        
        // Chiamata all'API per recuperare le statistiche
        const giorni = parseInt(filtri.periodo)
        const result = await tempoFasiApi.getStatisticheByPartNumber(selectedPartNumber, giorni)
        
        if (isMounted) {
          setStatistiche(result)
        }
      } catch (err) {
        console.error('❌ StatisticheCatalogo: Errore nel caricamento delle statistiche:', err)
        if (isMounted) {
          onError('Impossibile caricare le statistiche del catalogo. Riprova più tardi.')
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
  }, [selectedPartNumber, filtri.periodo, onError])

  // Applica il filtro part number dai filtri globali
  useEffect(() => {
    if (filtri.partNumber && filtri.partNumber !== 'all' && filtri.partNumber !== selectedPartNumber) {
      setSelectedPartNumber(filtri.partNumber)
    }
  }, [filtri.partNumber, selectedPartNumber])

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

  // Calcola lo scostamento medio rispetto ai tempi standard
  const calcolaScostamentoMedio = (): number => {
    if (!statistiche || !statistiche.previsioni) return 0;
    
    // Tempi standard di riferimento (in minuti)
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

  // Verifica se ci sono dati validi da mostrare
  const hasDatiValidi = (): boolean => {
    if (!statistiche) return false;
    
    try {
      const totaleODL = statistiche.totale_odl || 0;
      const hasPrevisioni = statistiche.previsioni && Object.keys(statistiche.previsioni).length > 0;
      
      // Considera validi i dati se:
      // 1. Ci sono ODL completati (totaleODL > 0) OPPURE
      // 2. Ci sono previsioni disponibili (anche se nessun ODL completato)
      return totaleODL > 0 || hasPrevisioni;
    } catch (err) {
      console.error('Errore nella verifica dei dati validi:', err);
      return false;
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-4">
        <div className="md:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Seleziona Part Number</CardTitle>
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
              
              <div className="pt-4">
                <h3 className="text-sm font-medium mb-2">Part Numbers</h3>
                <div className="max-h-[400px] overflow-y-auto space-y-1">
                  {filteredCatalogo.length === 0 ? (
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
                  ? `Statistiche ODL per Part Number: ${selectedPartNumber}`
                  : 'Seleziona un part number per visualizzare le statistiche ODL'}
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
                  <AlertTitle>Nessun dato disponibile</AlertTitle>
                  <AlertDescription>
                    Non ci sono ODL completati per il part number selezionato nel periodo specificato.
                    Le statistiche saranno disponibili quando verranno completati degli ordini di lavoro.
                    {/* Debug info */}
                    {statistiche && (
                      <div className="mt-2 text-xs">
                        <strong>Debug:</strong> Totale ODL: {statistiche.totale_odl || 0}, 
                        Previsioni: {statistiche.previsioni ? Object.keys(statistiche.previsioni).length : 0}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                        Tempo Medio Completamento
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

                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className={`text-2xl font-bold ${calcolaScostamentoMedio() > 20 ? 'text-red-600' : calcolaScostamentoMedio() > 10 ? 'text-orange-600' : 'text-green-600'}`}>
                        {calcolaScostamentoMedio().toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Scostamento Medio
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Dettaglio tempi per fase</h3>
                    
                    {statistiche && statistiche.previsioni && Object.entries(statistiche.previsioni).map(([fase, dati]) => {
                      if (!dati) return null;
                      
                      // Calcola scostamento per questa fase
                      const tempiStandard = {
                        'laminazione': 120,    // 2 ore
                        'attesa_cura': 60,     // 1 ora
                        'cura': 300            // 5 ore
                      };
                      
                      const mediaReale = dati.media_minuti || 0;
                      const tempoStandard = tempiStandard[fase as keyof typeof tempiStandard] || 0;
                      const scostamento = tempoStandard > 0 ? ((mediaReale - tempoStandard) / tempoStandard) * 100 : 0;
                      
                      return (
                        <div key={fase} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-center">
                            <h4 className="font-medium">{translateFase(fase)}</h4>
                            <div className="text-right">
                              <div className="text-xl font-bold">{formatDuration(dati.media_minuti || 0)}</div>
                              {tempoStandard > 0 && (
                                <div className={`text-sm ${Math.abs(scostamento) > 20 ? 'text-red-600' : Math.abs(scostamento) > 10 ? 'text-orange-600' : 'text-green-600'}`}>
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