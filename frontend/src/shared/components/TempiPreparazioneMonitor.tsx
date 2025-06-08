'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ODLResponse, odlApi, phaseTimesApi, TempoFaseResponse } from '@/lib/api'
import { Clock, AlertTriangle, RefreshCw, Timer } from 'lucide-react'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'

interface TempiPreparazioneMonitorProps {
  className?: string
  showTitle?: boolean
  maxItems?: number
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function TempiPreparazioneMonitor({
  className = '',
  showTitle = true,
  maxItems = 10,
  autoRefresh = true,
  refreshInterval = 30000 // 30 secondi
}: TempiPreparazioneMonitorProps) {
  const [odlPreparazione, setOdlPreparazione] = useState<ODLResponse[]>([])
  const [tempiPreparazione, setTempiPreparazione] = useState<Record<number, TempoFaseResponse>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const { toast } = useStandardToast()

  // Formatta la durata in formato leggibile
  const formatDurata = (tempoFase: TempoFaseResponse | undefined): string => {
    if (!tempoFase) return "N/A"
    
    // Se la fase è completata, usa la durata calcolata
    if (tempoFase.durata_minuti !== null && tempoFase.durata_minuti !== undefined) {
      const minuti = tempoFase.durata_minuti
      if (minuti < 60) return `${minuti}m`
      const ore = Math.floor(minuti / 60)
      const min = minuti % 60
      return min > 0 ? `${ore}h ${min}m` : `${ore}h`
    }
    
    // Se la fase è in corso, calcola il tempo trascorso
    if (tempoFase.inizio_fase && !tempoFase.fine_fase) {
      const inizio = new Date(tempoFase.inizio_fase)
      const ora = new Date()
      const diffMs = ora.getTime() - inizio.getTime()
      const minuti = Math.floor(diffMs / (1000 * 60))
      
      if (minuti < 60) return `${minuti}m`
      const ore = Math.floor(minuti / 60)
      const min = minuti % 60
      return min > 0 ? `${ore}h ${min}m` : `${ore}h`
    }
    
    return "N/A"
  }

  // Determina il colore del badge in base al tempo trascorso
  const getBadgeVariant = (tempoFase: TempoFaseResponse | undefined): "default" | "secondary" | "destructive" | "outline" | "warning" => {
    if (!tempoFase || !tempoFase.inizio_fase || tempoFase.fine_fase) return "secondary"
    
    const inizio = new Date(tempoFase.inizio_fase)
    const ora = new Date()
    const diffMs = ora.getTime() - inizio.getTime()
    const minuti = Math.floor(diffMs / (1000 * 60))
    
    // Soglie di allerta per i tempi di preparazione
    if (minuti > 480) return "destructive" // Oltre 8 ore
    if (minuti > 240) return "warning"     // Oltre 4 ore
    if (minuti > 120) return "outline"     // Oltre 2 ore
    return "default"
  }

  // Carica i dati degli ODL in preparazione
  const fetchData = async () => {
    try {
      setIsLoading(true)
      
      // Carica ODL in preparazione
      const allOdl = await odlApi.fetchODLs({ status: "Preparazione" })
      const odlLimitati = allOdl.slice(0, maxItems)
      setOdlPreparazione(odlLimitati)
      
      // Carica i tempi di preparazione per ogni ODL
      const tempiData: Record<number, TempoFaseResponse> = {}
      
      for (const odl of odlLimitati) {
        try {
          const tempoFasi = await phaseTimesApi.fetchPhaseTimes({ 
            odl_id: odl.id, 
            fase: "preparazione" 
          })
          
          // Trova la fase di preparazione attiva (senza fine_fase)
          const preparazioneAttiva = tempoFasi.find(tf => 
            tf.fase === "preparazione" && !tf.fine_fase
          )
          
          if (preparazioneAttiva) {
            tempiData[odl.id] = preparazioneAttiva
          }
        } catch (error) {
          console.error(`Errore nel caricamento tempo preparazione per ODL ${odl.id}:`, error)
        }
      }
      
      setTempiPreparazione(tempiData)
      setLastUpdate(new Date())
      
    } catch (error) {
      console.error('Errore nel caricamento dati preparazione:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile caricare i dati dei tempi di preparazione.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Effect per caricamento iniziale e auto-refresh
  useEffect(() => {
    fetchData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval, maxItems])

  if (isLoading && odlPreparazione.length === 0) {
    return (
      <Card className={className}>
        {showTitle && (
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Timer className="h-5 w-5 text-indigo-500" />
              Tempi Preparazione
            </CardTitle>
          </CardHeader>
        )}
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Caricamento...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      {showTitle && (
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Timer className="h-5 w-5 text-indigo-500" />
              Tempi Preparazione ({odlPreparazione.length})
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                Aggiornato: {lastUpdate.toLocaleTimeString()}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchData}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className="p-0">
        {odlPreparazione.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground px-6">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg font-medium">Nessun ODL in Preparazione</p>
            <p className="text-sm">Non ci sono ODL attualmente in fase di preparazione.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">ODL</TableHead>
                  <TableHead className="w-36">Part Number</TableHead>
                  <TableHead className="min-w-40">Descrizione</TableHead>
                  <TableHead className="w-24 text-center">Tempo</TableHead>
                  <TableHead className="w-16 text-center">Priorità</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {odlPreparazione.map(odl => {
                  const tempoPrep = tempiPreparazione[odl.id]
                  return (
                    <TableRow key={odl.id}>
                      <TableCell className="font-mono text-sm font-medium">
                        {odl.numero_odl}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {odl.parte?.part_number || 'N/A'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {odl.parte?.descrizione_breve || 'N/A'}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          <Badge variant={getBadgeVariant(tempoPrep)} className="text-xs">
                            {formatDurata(tempoPrep)}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge 
                          variant={odl.priorita > 5 ? "destructive" : odl.priorita > 3 ? "warning" : "secondary"}
                          className="text-xs"
                        >
                          {odl.priorita}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 