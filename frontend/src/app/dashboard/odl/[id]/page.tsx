'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Loader2, Clock, AlertTriangle, TimerOff, Check, ChevronLeft, Timer } from 'lucide-react'
import { formatDateIT, formatDateTime } from '@/lib/utils'
import { odlApi, tempoFasiApi, PrevisioneTempo } from '@/lib/api'
import Link from 'next/link'

// Per i problemi di tipo, definiamo alcune costanti tipizzate
const STATI_ODL = {
  "Preparazione": "Preparazione",
  "Laminazione": "Laminazione",
  "Attesa Cura": "Attesa Cura",
  "Cura": "Cura",
  "Finito": "Finito"
} as const;

type StatoODL = keyof typeof STATI_ODL;

const TIPI_FASE = {
  "laminazione": "laminazione",
  "attesa_cura": "attesa_cura", 
  "cura": "cura"
} as const;

type TipoFase = keyof typeof TIPI_FASE;

// Funzione per tradurre il tipo di fase
const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

// Funzione per formattare la durata in ore e minuti
const formatDuration = (minutes: number | null): string => {
  if (minutes === null) return '-';
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min`;
  }
  
  return `${hours}h ${mins}m`;
}

// Badge varianti per i diversi tipi di fase
const getFaseBadgeVariant = (fase: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "primary" | "success" | "warning"> = {
    "laminazione": "primary",
    "attesa_cura": "warning",
    "cura": "destructive",
  }
  return variants[fase] || "default"
}

export default function ODLDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const [odl, setOdl] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [tempoFasi, setTempoFasi] = useState<any[]>([])
  const [previsioni, setPrevisioni] = useState<Record<string, PrevisioneTempo>>({})
  const [faseCorrente, setFaseCorrente] = useState<string | null>(null)
  
  // Ottieni l'id dall'URL
  const odlId = params.id as string

  // Fetch dati ODL
  useEffect(() => {
    const fetchODL = async () => {
      try {
        setLoading(true)
        const odlData = await odlApi.getOne(Number(odlId))
        setOdl(odlData)
        
        // Determina la fase corrente in base allo stato dell'ODL
        const faseMap: Record<string, string> = {
          'Laminazione': 'laminazione',
          'Attesa Cura': 'attesa_cura',
          'Cura': 'cura'
        }
        setFaseCorrente(faseMap[odlData.status] || null)
        
        // Fetch tempi fasi associati a questo ODL
        const tempiData = await tempoFasiApi.getAll({ odl_id: Number(odlId) })
        setTempoFasi(tempiData)
        
        // Fetch previsioni per tutte le fasi
        const fasi = ['laminazione', 'attesa_cura', 'cura']
        const previsioniObj: Record<string, PrevisioneTempo> = {}
        
        for (const fase of fasi) {
          try {
            const previsione = await tempoFasiApi.getPrevisione(fase, odlData.parte.part_number)
            previsioniObj[fase] = previsione
          } catch (error) {
            console.error(`Errore nel caricamento previsione per ${fase}:`, error)
          }
        }
        
        setPrevisioni(previsioniObj)
      } catch (error) {
        console.error('Errore nel caricamento ODL:', error)
        toast({
          variant: 'destructive',
          title: 'Errore',
          description: `Impossibile caricare l'ODL con ID ${odlId}`,
        })
      } finally {
        setLoading(false)
      }
    }

    if (odlId) {
      fetchODL()
    }
  }, [odlId, toast])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin mr-2" />
        <span>Caricamento dettagli ODL...</span>
      </div>
    )
  }

  if (!odl) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Errore</AlertTitle>
        <AlertDescription>Non è stato possibile trovare l'ODL richiesto.</AlertDescription>
      </Alert>
    )
  }
  
  // Trova la fase attiva (senza fine_fase)
  const faseAttiva = tempoFasi.find(tf => tf.fine_fase === null)
  
  // Funzione per avviare una nuova fase
  const avviaFase = async (fase: TipoFase) => {
    if (!window.confirm(`Sei sicuro di voler avviare la fase di ${translateFase(fase)}?`)) {
      return
    }
    
    try {
      const data = {
        odl_id: Number(odlId),
        fase: fase,
        inizio_fase: new Date().toISOString(),
      }
      
      await tempoFasiApi.create(data)
      toast({
        title: 'Fase avviata',
        description: `Fase di ${translateFase(fase)} avviata con successo`,
      })
      
      // Aggiorna lo stato dell'ODL
      const statoMap: Record<TipoFase, StatoODL> = {
        'laminazione': 'Laminazione',
        'attesa_cura': 'Attesa Cura',
        'cura': 'Cura'
      }
      
      await odlApi.update(Number(odlId), { status: statoMap[fase] })
      
      // Ricarica i dati
      window.location.reload()
    } catch (error) {
      console.error('Errore durante l\'avvio della fase:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile avviare la fase',
      })
    }
  }
  
  // Funzione per completare una fase attiva
  const completaFase = async (tempoFaseId: number, faseName: TipoFase) => {
    if (!window.confirm(`Sei sicuro di voler completare la fase di ${translateFase(faseName)}?`)) {
      return
    }
    
    try {
      const data = {
        fine_fase: new Date().toISOString(),
      }
      
      await tempoFasiApi.update(tempoFaseId, data)
      toast({
        title: 'Fase completata',
        description: `Fase di ${translateFase(faseName)} completata con successo`,
      })
      
      // Aggiorna lo stato dell'ODL alla fase successiva
      const nextState: Record<TipoFase, StatoODL> = {
        'laminazione': 'Attesa Cura',
        'attesa_cura': 'Cura',
        'cura': 'Finito'
      }
      
      await odlApi.update(Number(odlId), { status: nextState[faseName] })
      
      // Ricarica i dati
      window.location.reload()
    } catch (error) {
      console.error('Errore durante il completamento della fase:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile completare la fase',
      })
    }
  }
  
  // Determina la prossima fase in base alla fase attiva
  const getNextFase = (currentFase: string | null) => {
    const sequenza = ['laminazione', 'attesa_cura', 'cura']
    if (!currentFase) return 'laminazione'
    
    const currentIndex = sequenza.indexOf(currentFase)
    if (currentIndex < 0 || currentIndex >= sequenza.length - 1) return null
    
    return sequenza[currentIndex + 1]
  }
  
  // Verifica se la fase corrente ha una previsione
  const getPrevisioneForFase = (fase: string) => {
    return previsioni[fase] || null
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link href="/dashboard/odl">
            <ChevronLeft className="h-4 w-4 mr-1" />
            Torna alla lista
          </Link>
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>Dettagli ODL #{odl.id}</CardTitle>
            <CardDescription>
              Creato il {formatDateIT(odl.created_at)}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Parte</h3>
                <p className="font-medium">{odl.parte.part_number}</p>
                <p className="text-sm">{odl.parte.descrizione_breve}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Tool</h3>
                <p className="font-medium">{odl.tool.codice}</p>
                <p className="text-sm">{odl.tool.descrizione || 'Nessuna descrizione'}</p>
              </div>
            </div>
            
            <Separator />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Stato</h3>
                <Badge 
                  variant={odl.status === 'Finito' ? 'success' : 'secondary'} 
                  className="mt-1"
                >
                  {odl.status}
                </Badge>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Priorità</h3>
                <Badge 
                  variant={odl.priorita > 5 ? 'destructive' : (odl.priorita > 2 ? 'warning' : 'outline')} 
                  className="mt-1"
                >
                  {odl.priorita}
                </Badge>
              </div>
            </div>
            
            {odl.note && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground">Note</h3>
                  <p className="text-sm mt-1">{odl.note}</p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="flex-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Avanzamento Fasi
            </CardTitle>
            <CardDescription>
              Monitoraggio dei tempi di produzione
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {tempoFasi.length === 0 ? (
              <div className="text-center py-6">
                <TimerOff className="h-12 w-12 mx-auto text-muted-foreground" />
                <p className="mt-2 text-muted-foreground">Nessuna fase registrata per questo ODL</p>
                
                {odl.status !== 'Finito' && (
                  <Button 
                    onClick={() => avviaFase('laminazione')} 
                    className="mt-4"
                  >
                    <Timer className="h-4 w-4 mr-2" />
                    Avvia fase Laminazione
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Fasi registrate */}
                {tempoFasi.map(fase => {
                  const previsione = getPrevisioneForFase(fase.fase)
                  const showVariazione = fase.durata_minuti && previsione?.media_minuti
                  
                  let variazione = 0
                  let variazionePercentuale = 0
                  
                  if (showVariazione) {
                    variazione = fase.durata_minuti - previsione.media_minuti
                    variazionePercentuale = (variazione / previsione.media_minuti) * 100
                  }
                  
                  return (
                    <div key={fase.id} className="border rounded-lg p-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <Badge variant={getFaseBadgeVariant(fase.fase)}>
                            {translateFase(fase.fase)}
                          </Badge>
                          <div className="text-sm mt-2">
                            <div>Inizio: {formatDateTime(fase.inizio_fase)}</div>
                            {fase.fine_fase ? (
                              <div>Fine: {formatDateTime(fase.fine_fase)}</div>
                            ) : (
                              <div className="font-medium text-amber-500">In corso</div>
                            )}
                          </div>
                          
                          {fase.durata_minuti ? (
                            <div className="mt-2">
                              <span className="text-sm font-medium">Durata: </span>
                              <span className="font-bold">
                                {formatDuration(fase.durata_minuti)}
                              </span>
                              
                              {showVariazione && (
                                <div className="text-xs mt-1">
                                  <span>Vs Media: </span>
                                  <span className={variazione > 0 ? "text-red-500" : "text-green-500"}>
                                    {variazione > 0 ? '+' : ''}{formatDuration(variazione)} 
                                    ({variazionePercentuale > 0 ? '+' : ''}{variazionePercentuale.toFixed(0)}%)
                                  </span>
                                </div>
                              )}
                            </div>
                          ) : (
                            previsione && (
                              <div className="mt-2 text-sm">
                                <span className="font-medium">Previsione: </span>
                                <span>{formatDuration(previsione.media_minuti)}</span>
                                <span className="text-xs text-muted-foreground ml-1">
                                  (basata su {previsione.numero_osservazioni} osservazioni)
                                </span>
                              </div>
                            )
                          )}
                        </div>
                        
                        {!fase.fine_fase && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => completaFase(fase.id, fase.fase as TipoFase)}
                          >
                            <Check className="h-4 w-4 mr-1" />
                            Completa
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
                
                {/* Pulsante per avviare la prossima fase */}
                {faseAttiva ? (
                  <div className="text-center">
                    <Badge variant="outline" className="mb-2">
                      Fase {translateFase(faseAttiva.fase)} in corso
                    </Badge>
                  </div>
                ) : (
                  odl.status !== 'Finito' && (
                    <div className="text-center">
                      {getNextFase(faseCorrente) && (
                        <Button 
                          onClick={() => avviaFase(getNextFase(faseCorrente) as TipoFase)} 
                          className="mt-2"
                        >
                          <Timer className="h-4 w-4 mr-2" />
                          Avvia fase {translateFase(getNextFase(faseCorrente) as string)}
                        </Button>
                      )}
                    </div>
                  )
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 