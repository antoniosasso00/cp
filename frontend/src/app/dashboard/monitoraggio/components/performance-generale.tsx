'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, TrendingUp, TrendingDown, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { odlApi, phaseTimesApi, CatalogoResponse } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

interface FiltriGlobali {
  periodo: string;
  partNumber: string;
  statoODL: string;
  dataInizio?: Date;
  dataFine?: Date;
}

interface PerformanceGeneraleProps {
  filtri: FiltriGlobali;
  catalogo: CatalogoResponse[];
  onError: (message: string) => void;
}

interface StatisticheGenerali {
  totaleODL: number;
  odlCompletati: number;
  odlInCorso: number;
  odlBloccati: number;
  tempoMedioCompletamento: number;
  efficienza: number;
  tendenzaSettimanale: number;
}

export default function PerformanceGenerale({ filtri, catalogo, onError }: PerformanceGeneraleProps) {
  const [statistiche, setStatistiche] = useState<StatisticheGenerali | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchStatistiche = async () => {
      try {
        setIsLoading(true)
        
        // Carica tutti gli ODL
        const odlData = await odlApi.fetchODLs()
        
        // Filtra gli ODL in base ai filtri globali
        let odlFiltrati = odlData
        
        if (filtri.partNumber && filtri.partNumber !== 'all') {
          odlFiltrati = odlFiltrati.filter(odl => 
            odl.parte?.part_number === filtri.partNumber
          )
        }
        
        if (filtri.statoODL && filtri.statoODL !== 'all') {
          odlFiltrati = odlFiltrati.filter(odl => odl.status === filtri.statoODL)
        }
        
        if (filtri.dataInizio && filtri.dataFine) {
          odlFiltrati = odlFiltrati.filter(odl => {
            const dataCreazione = new Date(odl.created_at)
            return dataCreazione >= filtri.dataInizio! && dataCreazione <= filtri.dataFine!
          })
        }
        
        // Calcola le statistiche
        const totaleODL = odlFiltrati.length
        const odlCompletati = odlFiltrati.filter(odl => odl.status === 'Finito').length
        const odlInCorso = odlFiltrati.filter(odl => 
          ['Preparazione', 'Laminazione', 'Attesa Cura', 'Cura'].includes(odl.status)
        ).length
        const odlBloccati = 0 // Non esiste stato "Bloccato" nel sistema
        
        // Calcola tempo medio di completamento (solo per ODL completati)
        let tempoMedioCompletamento = 0
        if (odlCompletati > 0) {
          try {
            // Qui dovresti implementare la logica per calcolare il tempo medio
            // basandoti sui dati di TempoFase
            const tempiData = await phaseTimesApi.fetchPhaseTimes()
            const tempiCompletati = tempiData.filter(tempo => 
              odlFiltrati.some(odl => odl.id === tempo.odl_id && odl.status === 'Finito')
            )
            
            if (tempiCompletati.length > 0) {
              const sommaTempi = tempiCompletati.reduce((sum, tempo) => 
                sum + (tempo.durata_minuti || 0), 0
              )
              tempoMedioCompletamento = sommaTempi / tempiCompletati.length
            }
          } catch (err) {
            console.warn('Errore nel calcolo del tempo medio:', err)
          }
        }
        
        // Calcola efficienza (% di ODL completati vs totali)
        const efficienza = totaleODL > 0 ? (odlCompletati / totaleODL) * 100 : 0
        
        // Calcola tendenza settimanale (semplificata)
        const settimanaScorsa = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        const odlSettimanaScorsa = odlFiltrati.filter(odl => 
          new Date(odl.created_at) >= settimanaScorsa
        ).length
        const tendenzaSettimanale = odlSettimanaScorsa
        
        setStatistiche({
          totaleODL,
          odlCompletati,
          odlInCorso,
          odlBloccati,
          tempoMedioCompletamento,
          efficienza,
          tendenzaSettimanale
        })
        
      } catch (error) {
        console.error('Errore nel caricamento delle statistiche generali:', error)
        onError('Impossibile caricare le statistiche generali. Riprova più tardi.')
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchStatistiche()
  }, [filtri]) // ✅ FIX: Rimosso onError dalle dipendenze per evitare loop infiniti

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Caricamento performance...</span>
      </div>
    )
  }

  if (!statistiche) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Nessun dato disponibile</AlertTitle>
        <AlertDescription>
          Nessun dato disponibile per i filtri selezionati. Prova a modificare i criteri di ricerca.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Totale ODL</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statistiche.totaleODL}</div>
            <p className="text-xs text-muted-foreground">
              {statistiche.tendenzaSettimanale > 0 && (
                <span className="text-green-600">
                  +{statistiche.tendenzaSettimanale} questa settimana
                </span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ODL Completati</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{statistiche.odlCompletati}</div>
            <p className="text-xs text-muted-foreground">
              {statistiche.totaleODL > 0 && (
                <span>
                  {((statistiche.odlCompletati / statistiche.totaleODL) * 100).toFixed(1)}% del totale
                </span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ODL In Corso</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{statistiche.odlInCorso}</div>
            <p className="text-xs text-muted-foreground">
              In lavorazione
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ODL Bloccati</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{statistiche.odlBloccati}</div>
            <p className="text-xs text-muted-foreground">
              Richiedono attenzione
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Metriche Avanzate */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Efficienza Produzione</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tasso di Completamento</span>
                <Badge variant={statistiche.efficienza >= 80 ? "default" : statistiche.efficienza >= 60 ? "secondary" : "destructive"}>
                  {statistiche.efficienza.toFixed(1)}%
                </Badge>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    statistiche.efficienza >= 80 ? 'bg-green-600' : 
                    statistiche.efficienza >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}
                  style={{ width: `${Math.min(statistiche.efficienza, 100)}%` }}
                ></div>
              </div>
              
              <p className="text-xs text-muted-foreground">
                {statistiche.efficienza >= 80 ? 'Eccellente' : 
                 statistiche.efficienza >= 60 ? 'Buona' : 'Necessita miglioramento'}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tempo Medio Completamento</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-3xl font-bold">
                {formatDuration(statistiche.tempoMedioCompletamento)}
              </div>
              
              <div className="flex items-center gap-2">
                {statistiche.tempoMedioCompletamento <= 480 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span className="text-sm text-muted-foreground">
                  {statistiche.tempoMedioCompletamento <= 480 ? 'Sotto la media' : 'Sopra la media'}
                </span>
              </div>
              
              <p className="text-xs text-muted-foreground">
                Basato su {statistiche.odlCompletati} ODL completati
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Distribuzione Stati */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Distribuzione Stati ODL</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{statistiche.odlCompletati}</div>
              <div className="text-sm text-green-700">Completati</div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{statistiche.odlInCorso}</div>
              <div className="text-sm text-blue-700">In Corso</div>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{statistiche.odlBloccati}</div>
              <div className="text-sm text-red-700">Bloccati</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {statistiche.totaleODL - statistiche.odlCompletati - statistiche.odlInCorso - statistiche.odlBloccati}
              </div>
              <div className="text-sm text-gray-700">Altri</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 