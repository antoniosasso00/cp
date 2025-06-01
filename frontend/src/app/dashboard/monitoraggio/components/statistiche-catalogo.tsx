'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { AlertCircle, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { CatalogoResponse, standardTimesApi, TimesComparisonResponse } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

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

// ✅ NUOVO: Tipi per il confronto tempi standard v1.4.5-DEMO
interface TimesComparisonData extends TimesComparisonResponse {}

export default function StatisticheCatalogo({ filtri, catalogo, onError }: StatisticheCatalogoProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')
  const [comparisonData, setComparisonData] = useState<TimesComparisonData | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)

  // Carica le statistiche quando cambia il part number selezionato o i filtri
  useEffect(() => {
    let isMounted = true;

    const fetchComparison = async () => {
      if (!selectedPartNumber) {
        setComparisonData(null)
        return
      }
      
      try {
        setLoadingStats(true)
        
        // ✅ NUOVO: Utilizza la nuova API standardTimesApi.getComparison
        const giorni = parseInt(filtri.periodo)
        const result = await standardTimesApi.getComparison(selectedPartNumber, giorni)
        
        if (isMounted) {
          setComparisonData(result)
        }
      } catch (err) {
        console.error('Errore nel caricamento del confronto tempi:', err)
        if (isMounted) {
          onError('Impossibile caricare il confronto con i tempi standard. Riprova più tardi.')
        }
      } finally {
        if (isMounted) {
          setLoadingStats(false)
        }
      }
    }
    
    if (selectedPartNumber) {
      fetchComparison()
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

  // ✅ NUOVO: Calcola il totale delle medie osservate
  const calcolaTotaleMedieOsservate = (): number => {
    if (!comparisonData || !comparisonData.fasi) return 0;
    
    let totale = 0;
    
    try {
      Object.values(comparisonData.fasi).forEach(fase => {
        if (fase && fase.tempo_osservato_minuti > 0) {
          totale += fase.tempo_osservato_minuti;
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo del totale medie osservate:', err);
    }
    
    return totale;
  }

  // ✅ NUOVO: Calcola il totale delle medie standard
  const calcolaTotaleMedieStandard = (): number => {
    if (!comparisonData || !comparisonData.fasi) return 0;
    
    let totale = 0;
    
    try {
      Object.values(comparisonData.fasi).forEach(fase => {
        if (fase && fase.tempo_standard_minuti > 0) {
          totale += fase.tempo_standard_minuti;
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo del totale medie standard:', err);
    }
    
    return totale;
  }

  // Calcola il numero di fasi con dati
  const calcolaFasiConDati = (): number => {
    if (!comparisonData || !comparisonData.fasi) return 0;
    
    let fasiConDati = 0;
    
    try {
      Object.values(comparisonData.fasi).forEach(fase => {
        if (fase && (fase.tempo_osservato_minuti > 0 || fase.tempo_standard_minuti > 0)) {
          fasiConDati++;
        }
      });
    } catch (err) {
      console.error('Errore nel calcolo delle fasi con dati:', err);
    }
    
    return fasiConDati;
  }

  // ✅ NUOVO: Usa lo scostamento medio calcolato dal backend
  const getScostamentoMedio = (): number => {
    return comparisonData?.scostamento_medio_percentuale || 0;
  }

  // ✅ NUOVO: Verifica se ci sono dati validi dal backend
  const hasDatiValidi = (): boolean => {
    if (!comparisonData) return false;
    return comparisonData.odl_totali_periodo > 0;
  }

  // ✅ NUOVO: Funzione per ottenere l'icona del trend
  const getTrendIcon = (delta: number) => {
    if (Math.abs(delta) < 1) return <Minus className="h-4 w-4" />;
    return delta > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />;
  }

  // ✅ NUOVO: Funzione per ottenere la classe CSS del colore
  const getColorClass = (colore: string) => {
    switch (colore) {
      case 'rosso': return 'text-red-600';
      case 'giallo': return 'text-orange-600';
      case 'verde': return 'text-green-600';
      default: return 'text-gray-600';
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
              <CardTitle className="text-lg flex items-center gap-2">
                {selectedPartNumber 
                  ? `Confronto Tempi - ${selectedPartNumber}`
                  : 'Seleziona un part number'}
                {comparisonData?.dati_limitati_globale && (
                  <Badge variant="destructive" className="text-xs">
                    Dati limitati
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedPartNumber ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Seleziona un part number dalla lista per visualizzare il confronto con i tempi standard
                  </p>
                </div>
              ) : loadingStats ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin" />
                  <span className="ml-2">Caricamento confronto...</span>
                </div>
              ) : !hasDatiValidi() ? (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Nessun dato disponibile</AlertTitle>
                  <AlertDescription>
                    Non ci sono ODL completati per il part number selezionato nel periodo specificato.
                    Le statistiche saranno disponibili quando verranno completati degli ordini di lavoro.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-6">
                  {/* ✅ NUOVO: Summary cards aggiornate */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {comparisonData?.odl_totali_periodo || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ODL Analizzati
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {formatDuration(calcolaTotaleMedieOsservate())}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Tempo Totale Osservato
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {formatDuration(calcolaTotaleMedieStandard())}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Tempo Totale Standard
                      </div>
                    </div>

                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className={`text-2xl font-bold ${getScostamentoMedio() > 20 ? 'text-red-600' : getScostamentoMedio() > 10 ? 'text-orange-600' : 'text-green-600'}`}>
                        {getScostamentoMedio().toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Scostamento Medio
                      </div>
                    </div>
                  </div>
                  
                  {/* ✅ NUOVO: Dettaglio tempi per fase con confronto standard */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">Confronto Tempi per Fase</h3>
                    
                    {comparisonData && comparisonData.fasi && Object.entries(comparisonData.fasi).map(([fase, dati]) => {
                      if (!dati) return null;
                      
                      return (
                        <div key={fase} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium">{translateFase(fase)}</h4>
                              {dati.dati_limitati && (
                                <Badge variant="outline" className="text-xs">
                                  &lt; 5 ODL
                                </Badge>
                              )}
                            </div>
                            
                            <div className="text-right">
                              <div className={`flex items-center gap-1 text-lg font-bold ${getColorClass(dati.colore_delta)}`}>
                                {getTrendIcon(dati.delta_percentuale)}
                                {dati.delta_percentuale > 0 ? '+' : ''}{dati.delta_percentuale.toFixed(1)}%
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div>
                              <div className="text-muted-foreground">Tempo Osservato</div>
                              <div className="font-medium">{formatDuration(dati.tempo_osservato_minuti)}</div>
                              <div className="text-xs text-muted-foreground">
                                {dati.numero_osservazioni} osservazioni
                              </div>
                            </div>
                            
                            <div>
                              <div className="text-muted-foreground">Tempo Standard</div>
                              <div className="font-medium">{formatDuration(dati.tempo_standard_minuti)}</div>
                              {dati.note_standard && (
                                <div className="text-xs text-muted-foreground truncate">
                                  {dati.note_standard}
                                </div>
                              )}
                            </div>
                            
                            <div>
                              <div className="text-muted-foreground">Delta</div>
                              <div className={`font-medium ${getColorClass(dati.colore_delta)}`}>
                                {Math.abs(dati.tempo_osservato_minuti - dati.tempo_standard_minuti).toFixed(1)} min
                              </div>
                              <div className={`text-xs ${getColorClass(dati.colore_delta)}`}>
                                {dati.delta_percentuale > 0 ? 'Più lento' : dati.delta_percentuale < 0 ? 'Più veloce' : 'Conforme'}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    
                    {(!comparisonData || !comparisonData.fasi || Object.keys(comparisonData.fasi).length === 0) && (
                      <div className="text-center text-muted-foreground py-4">
                        Nessun dato disponibile per il confronto delle fasi
                      </div>
                    )}
                  </div>
                  
                  {/* ✅ NUOVO: Info aggiuntive */}
                  {comparisonData && (
                    <div className="text-xs text-muted-foreground border-t pt-4">
                      <p>
                        <strong>Periodo analizzato:</strong> Ultimi {comparisonData.periodo_giorni} giorni 
                        | <strong>Ultima analisi:</strong> {new Date(comparisonData.ultima_analisi).toLocaleString('it-IT')}
                      </p>
                      {comparisonData.dati_limitati_globale && (
                        <p className="text-orange-600 mt-1">
                          ⚠️ Attenzione: Il dataset contiene meno di 5 ODL completati. I risultati potrebbero non essere rappresentativi.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 