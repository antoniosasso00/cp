'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { 
  Loader2, 
  Clock, 
  AlertTriangle, 
  ArrowRight, 
  ChevronLeft, 
  CheckCircle2, 
  Timer, 
  ArrowRightCircle 
} from 'lucide-react'
import { formatDateIT, formatDateTime } from '@/lib/utils'
import { odlApi, tempoFasiApi } from '@/lib/api'
import Link from 'next/link'

// Sequenza degli stati ODL
const SEQUENZA_STATI = [
  "Preparazione",
  "Laminazione",
  "Attesa Cura",
  "Cura",
  "Finito"
] as const;

// Tipo per gli stati ODL
type StatoODL = typeof SEQUENZA_STATI[number];

// Funzione per ottenere il prossimo stato nella sequenza
const getProssimoStato = (statoCorrente: string): StatoODL | null => {
  const indexCorrente = SEQUENZA_STATI.indexOf(statoCorrente as StatoODL);
  if (indexCorrente < 0 || indexCorrente >= SEQUENZA_STATI.length - 1) {
    return null;
  }
  return SEQUENZA_STATI[indexCorrente + 1];
};

// Badge varianti per i diversi stati
const getStatusBadgeVariant = (status: string) => {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
    "Preparazione": "secondary",
    "Laminazione": "default",
    "Attesa Cura": "warning",
    "Cura": "destructive",
    "Finito": "success"
  }
  return variants[status] || "default"
}

// Traduzione tipo fase
const translateFase = (fase: string): string => {
  const map: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return map[fase] || fase;
}

export default function AvanzaODLPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const [odl, setOdl] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [processingAction, setProcessingAction] = useState(false)
  const [prossimoStato, setProssimoStato] = useState<StatoODL | null>(null)
  const [tempoFasi, setTempoFasi] = useState<any[]>([])
  
  // Ottieni l'id dall'URL
  const odlId = params.id as string

  // Fetch dati ODL
  useEffect(() => {
    const fetchODL = async () => {
      try {
        setLoading(true)
        const odlData = await odlApi.getOne(Number(odlId))
        setOdl(odlData)
        
        // Determina il prossimo stato
        setProssimoStato(getProssimoStato(odlData.status))
        
        // Carica le fasi di tempo correnti
        const tempiData = await tempoFasiApi.getAll({ odl_id: Number(odlId) })
        setTempoFasi(tempiData)
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

  // Funzione per avanzare lo stato ODL
  const avanzaStato = async () => {
    if (!prossimoStato) {
      return
    }

    try {
      setProcessingAction(true)
      
      // Conferma dall'utente
      if (!window.confirm(`Sei sicuro di voler avanzare l'ODL dallo stato "${odl.status}" a "${prossimoStato}"?`)) {
        setProcessingAction(false)
        return
      }
      
      // Aggiorna lo stato dell'ODL
      const updatedOdl = await odlApi.update(Number(odlId), { 
        status: prossimoStato 
      })
      
      // Mostra notifica di successo
      toast({
        title: 'Stato aggiornato',
        description: `ODL avanzato con successo a "${prossimoStato}"`,
      })
      
      // Aggiorna stato locale
      setOdl(updatedOdl)
      setProssimoStato(getProssimoStato(updatedOdl.status))
      
      // Ricarica le fasi di tempo con gestione errori
      try {
        const tempiData = await tempoFasiApi.getAll({ odl_id: Number(odlId) })
        setTempoFasi(tempiData)
      } catch (tempiError) {
        console.warn('Errore nel caricamento tempi fasi:', tempiError)
        // Non bloccare il flusso per questo errore
      }
      
      // Forza il refresh della pagina per aggiornare tutte le liste ODL
      setTimeout(() => {
        window.location.reload()
      }, 1500)
      
      // Se lo stato è "Finito", redireziona alla pagina di dettaglio dopo 3 secondi
      if (updatedOdl.status === "Finito") {
        setTimeout(() => {
          router.push(`/dashboard/odl/${odlId}`)
        }, 3000)
      }
    } catch (error) {
      console.error('Errore durante l\'avanzamento dello stato:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Impossibile avanzare lo stato dell\'ODL. Riprova più tardi.',
      })
    } finally {
      setProcessingAction(false)
    }
  }

  // Determina la fase attualmente attiva
  const getFaseAttiva = () => {
    return tempoFasi.find(fase => fase.fine_fase === null);
  }

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
  
  const faseAttiva = getFaseAttiva();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/dashboard/odl/${odlId}`}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            Torna ai dettagli ODL
          </Link>
        </Button>
        
        <Button variant="outline" size="sm" asChild>
          <Link href="/dashboard/odl">
            <ChevronLeft className="h-4 w-4 mr-1" />
            Torna alla lista ODL
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <ArrowRightCircle className="h-5 w-5" />
            Avanzamento ODL - {odl.parte.part_number}
          </CardTitle>
          <CardDescription>
            Gestisci il flusso di lavoro dell'ordine e registra i tempi delle fasi
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Stato corrente</h3>
              <div className="border rounded-md p-4 flex items-center gap-4">
                <Badge 
                  variant={getStatusBadgeVariant(odl.status)} 
                  className="text-lg px-3 py-1"
                >
                  {odl.status}
                </Badge>
                <div>
                  <p className="text-sm text-muted-foreground">Parte: {odl.parte.part_number}</p>
                  <p className="text-sm text-muted-foreground">Tool: {odl.tool.codice}</p>
                </div>
              </div>
              
              {faseAttiva && (
                <div className="border rounded-md p-4 bg-muted/50">
                  <h4 className="text-sm font-medium text-muted-foreground">Fase attiva</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="h-4 w-4 text-primary" />
                    <span className="font-medium">{translateFase(faseAttiva.fase)}</span>
                    <span className="text-sm text-muted-foreground">
                      iniziata il {formatDateTime(faseAttiva.inizio_fase)}
                    </span>
                  </div>
                </div>
              )}
              
              {prossimoStato && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Avanza stato a</h3>
                  <div className="border rounded-md p-4 flex items-center gap-4">
                    <Badge 
                      variant={getStatusBadgeVariant(prossimoStato)} 
                      className="text-lg px-3 py-1"
                    >
                      {prossimoStato}
                    </Badge>
                    
                    <Button 
                      onClick={avanzaStato}
                      disabled={processingAction}
                      className="ml-auto"
                    >
                      {processingAction ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Aggiornamento...
                        </>
                      ) : (
                        <>
                          <ArrowRight className="h-4 w-4 mr-2" />
                          Avanza a {prossimoStato}
                        </>
                      )}
                    </Button>
                  </div>
                  
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Attenzione</AlertTitle>
                    <AlertDescription>
                      Avanzando lo stato dell'ODL, verrà automaticamente completata 
                      la fase attuale (se presente) e iniziata quella successiva.
                      Questa operazione non può essere annullata.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
              
              {!prossimoStato && odl.status === "Finito" && (
                <Alert className="bg-green-50">
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertTitle>ODL completato</AlertTitle>
                  <AlertDescription>
                    Questo ODL è già nello stato finale. Non sono disponibili ulteriori 
                    avanzamenti.
                  </AlertDescription>
                </Alert>
              )}
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Storico stato</h3>
              <div className="border rounded-md p-4">
                <div className="space-y-3">
                  {SEQUENZA_STATI.map((stato, index) => {
                    const isCurrent = odl.status === stato;
                    const isPassed = SEQUENZA_STATI.indexOf(odl.status as StatoODL) >= index;
                    const faseTempo = tempoFasi.find(tf => {
                      const fasiMap: Record<string, string> = {
                        "Laminazione": "laminazione",
                        "Attesa Cura": "attesa_cura",
                        "Cura": "cura"
                      };
                      return tf.fase === fasiMap[stato];
                    });
                    
                    return (
                      <div key={stato} className="flex items-center gap-4">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          isPassed 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {isPassed ? (
                            <CheckCircle2 className="h-5 w-5" />
                          ) : (
                            index + 1
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center">
                            <span className={`font-medium ${isCurrent ? 'text-primary' : ''}`}>
                              {stato}
                            </span>
                            {isCurrent && (
                              <Badge variant="outline" className="ml-2">
                                Corrente
                              </Badge>
                            )}
                          </div>
                          
                          {faseTempo && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {faseTempo.inizio_fase && (
                                <div>Iniziato: {formatDateTime(faseTempo.inizio_fase)}</div>
                              )}
                              {faseTempo.fine_fase && (
                                <div>Completato: {formatDateTime(faseTempo.fine_fase)}</div>
                              )}
                              {faseTempo.durata_minuti && (
                                <div className="font-medium">
                                  Durata: {Math.floor(faseTempo.durata_minuti / 60)}h {faseTempo.durata_minuti % 60}m
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Button variant="outline" asChild>
            <Link href={`/dashboard/odl/${odlId}`}>
              Annulla
            </Link>
          </Button>
          {prossimoStato && (
            <Button 
              onClick={avanzaStato}
              disabled={processingAction}
            >
              {processingAction ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Aggiornamento...
                </>
              ) : (
                <>
                  <ArrowRight className="h-4 w-4 mr-2" />
                  Avanza a {prossimoStato}
                </>
              )}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  )
} 