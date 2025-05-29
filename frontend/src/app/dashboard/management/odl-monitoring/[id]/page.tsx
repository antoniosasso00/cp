'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowLeft, AlertCircle, RefreshCw, Clock, Calendar } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { ODLTimelineEnhanced } from '@/components/odl-monitoring/ODLTimelineEnhanced'

// Tipi per i dati dell'ODL dettagliato
interface ODLDettaglio {
  id: number
  status: string
  priorita: number
  parte_nome: string
  tool_nome: string
  created_at: string
  updated_at: string
  nesting_id?: number
  autoclave_nome?: string
  ciclo_cura_nome?: string
  tempo_in_stato_corrente?: number
  tempo_totale_produzione?: number
}

interface TimelineEvent {
  id: number
  evento: string
  stato_precedente?: string
  stato_nuovo: string
  descrizione?: string
  timestamp: string
  nesting_stato?: string
  autoclave_nome?: string
}

interface ODLProgressData {
  id: number
  status: string
  created_at: string
  updated_at: string
  timestamps: Array<{
    stato: string
    inizio: string
    fine?: string
    durata_minuti: number
  }>
  tempo_totale_stimato: number
  has_timeline_data: boolean
  data_source: string
}

// Tipo per i timestamp individuali
interface TimestampData {
  stato: string
  inizio: string
  fine?: string
  durata_minuti: number
}

export default function ODLTimelineDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  
  const [odlId, setOdlId] = useState<number | null>(null)
  const [odlDettaglio, setOdlDettaglio] = useState<ODLDettaglio | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [progressData, setProgressData] = useState<ODLProgressData | null>(null)
  const [isLoadingDettaglio, setIsLoadingDettaglio] = useState(true)
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Valida e imposta l'ID dall'URL
  useEffect(() => {
    if (params?.id) {
      const id = Array.isArray(params.id) ? params.id[0] : params.id
      const parsedId = parseInt(id, 10)
      
      if (isNaN(parsedId) || parsedId <= 0) {
        setError('ID ODL non valido. Deve essere un numero positivo.')
        return
      }
      
      setOdlId(parsedId)
    } else {
      setError('ID ODL mancante nell\'URL.')
    }
  }, [params])

  // Carica i dettagli ODL
  const fetchODLDettaglio = async (id: number) => {
    try {
      setIsLoadingDettaglio(true)
      setError(null)
      
      const response = await fetch(`/api/v1/odl-monitoring/monitoring/${id}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`ODL con ID ${id} non trovato`)
        }
        throw new Error(`Errore ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setOdlDettaglio(data)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto nel caricamento dettagli ODL'
      console.error('Errore nel caricamento dettagli ODL:', err)
      setError(errorMessage)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
      })
    } finally {
      setIsLoadingDettaglio(false)
    }
  }

  // Carica la timeline dell'ODL
  const fetchODLTimeline = async (id: number) => {
    try {
      setIsLoadingTimeline(true)
      
      const response = await fetch(`/api/v1/odl-monitoring/monitoring/${id}/timeline`)
      
      if (!response.ok) {
        if (response.status === 404) {
          // Se la timeline non è disponibile, usa i dati di progresso come fallback
          console.warn(`Timeline non disponibile per ODL ${id}, uso dati progresso`)
          return fetchODLProgress(id)
        }
        throw new Error(`Errore ${response.status}: ${response.statusText}`)
      }
      
      const timelineData = await response.json()
      
      // ✅ CORREZIONE: Estrai correttamente la proprietà logs dal backend
      if (timelineData && timelineData.logs && Array.isArray(timelineData.logs)) {
        setTimeline(timelineData.logs)
        console.log(`✅ Timeline caricata per ODL ${id}: ${timelineData.logs.length} eventi`)
      } else {
        console.warn(`Timeline ODL ${id}: formato dati non valido, tentativo fallback`)
        // Se il formato non è quello atteso, prova il fallback
        await fetchODLProgress(id)
      }
      
    } catch (err) {
      console.warn('Timeline non disponibile, provo con dati progresso:', err)
      // Fallback ai dati di progresso
      await fetchODLProgress(id)
    } finally {
      setIsLoadingTimeline(false)
    }
  }

  // Fallback: carica i dati di progresso
  const fetchODLProgress = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/odl-monitoring/monitoring/${id}/progress`)
      
      if (!response.ok) {
        throw new Error(`Errore ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      setProgressData(data)
      
      // ✅ MIGLIORAMENTO: Converte i dati di progresso in formato timeline più ricco
      if (data.timestamps && data.timestamps.length > 0) {
        const timelineFromProgress: TimelineEvent[] = data.timestamps.map((t: TimestampData, index: number) => ({
          id: index + 1,
          evento: `Cambio stato: ${index > 0 ? 'Precedente' : 'Creazione'} → ${t.stato}`,
          stato_precedente: index > 0 ? data.timestamps[index - 1]?.stato : undefined,
          stato_nuovo: t.stato,
          timestamp: t.inizio,
          descrizione: `Durata in ${t.stato}: ${Math.floor(t.durata_minuti / 60)}h ${t.durata_minuti % 60}m${!t.fine ? ' (in corso)' : ''}`
        }))
        setTimeline(timelineFromProgress)
        console.log(`✅ Timeline da progresso caricata per ODL ${id}: ${timelineFromProgress.length} eventi (fonte: ${data.data_source})`)
      } else {
        // ✅ FALLBACK FINALE: Crea timeline minima con stato corrente se disponibile
        if (data.status) {
          const fallbackTimeline: TimelineEvent[] = [{
            id: 1,
            evento: `Stato corrente: ${data.status}`,
            stato_nuovo: data.status,
            timestamp: data.updated_at || data.created_at,
            descrizione: `ODL attualmente in stato "${data.status}". Timeline dettagliata non disponibile.`
          }]
          setTimeline(fallbackTimeline)
          console.log(`⚠️ Timeline fallback minima per ODL ${id}: stato ${data.status}`)
        } else {
          setTimeline([])
          console.warn(`❌ Nessun dato timeline disponibile per ODL ${id}`)
        }
      }
      
    } catch (err) {
      console.error('Errore nel caricamento dati progresso:', err)
      // Se anche il progresso fallisce, mostra timeline vuota con messaggio
      setTimeline([])
    }
  }

  // Carica tutti i dati dell'ODL
  const loadODLData = async () => {
    if (!odlId) return
    
    setIsRefreshing(true)
    await Promise.all([
      fetchODLDettaglio(odlId),
      fetchODLTimeline(odlId)
    ])
    setIsRefreshing(false)
  }

  // Carica i dati quando l'ID è disponibile
  useEffect(() => {
    if (odlId) {
      loadODLData()
    }
  }, [odlId])

  // Gestione refresh
  const handleRefresh = () => {
    if (odlId) {
      loadODLData()
    }
  }

  // Gestione stato di errore grave
  if (error && !odlDettaglio) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-between">
          <Button 
            variant="outline" 
            onClick={() => router.back()}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Indietro
          </Button>
        </div>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>ODL non valido</AlertTitle>
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">ODL non trovato</h3>
            <p className="text-gray-500 text-center mb-4">
              L'ODL richiesto non esiste o l'ID non è valido.
            </p>
            <Button onClick={() => router.push('/dashboard/management/odl-monitoring')}>
              Torna all'elenco ODL
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header con navigazione */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            onClick={() => router.back()}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Indietro
          </Button>
          
          <div>
            <h1 className="text-2xl font-bold">
              {odlDettaglio ? `ODL #${odlDettaglio.id}` : 'Caricamento...'}
            </h1>
            {odlDettaglio && (
              <p className="text-muted-foreground">
                {odlDettaglio.parte_nome} • {odlDettaglio.tool_nome}
              </p>
            )}
          </div>
        </div>

        <Button 
          variant="outline" 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Aggiorna
        </Button>
      </div>

      {/* Dettagli ODL */}
      {isLoadingDettaglio ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      ) : odlDettaglio ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Dettagli ODL
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Stato Attuale</p>
                  <Badge variant={odlDettaglio.status === 'Finito' ? 'default' : 'secondary'}>
                    {odlDettaglio.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Priorità</p>
                  <p className="text-sm">{odlDettaglio.priorita}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Creato il</p>
                  <p className="text-sm">{new Date(odlDettaglio.created_at).toLocaleString('it-IT')}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Autoclave</p>
                  <p className="text-sm">{odlDettaglio.autoclave_nome || 'Non assegnata'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Ciclo di Cura</p>
                  <p className="text-sm">{odlDettaglio.ciclo_cura_nome || 'Non definito'}</p>
                </div>
                {odlDettaglio.nesting_id && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Nesting ID</p>
                    <p className="text-sm">#{odlDettaglio.nesting_id}</p>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {odlDettaglio.tempo_in_stato_corrente !== undefined && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Tempo nello stato attuale</p>
                    <p className="text-sm">{Math.floor(odlDettaglio.tempo_in_stato_corrente / 60)}h {odlDettaglio.tempo_in_stato_corrente % 60}m</p>
                  </div>
                )}
                {odlDettaglio.tempo_totale_produzione !== undefined && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Tempo totale produzione</p>
                    <p className="text-sm">{Math.floor(odlDettaglio.tempo_totale_produzione / 60)}h {odlDettaglio.tempo_totale_produzione % 60}m</p>
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Ultimo aggiornamento</p>
                  <p className="text-sm">{new Date(odlDettaglio.updated_at).toLocaleString('it-IT')}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {/* Timeline */}
      <div className="space-y-4">
        {isLoadingTimeline ? (
          <Card>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ) : (
          <>
            {progressData && !progressData.has_timeline_data && (
              <Alert>
                <Clock className="h-4 w-4" />
                <AlertTitle>Dati timeline limitati</AlertTitle>
                <AlertDescription>
                  I dati della timeline sono basati su stime ({progressData.data_source}). 
                  Per dati più precisi, potrebbero essere necessari più log di sistema.
                </AlertDescription>
              </Alert>
            )}
            
            <ODLTimelineEnhanced 
              logs={Array.isArray(timeline) ? timeline : []} 
              currentStatus={odlDettaglio?.status || 'Unknown'} 
            />
          </>
        )}
      </div>
    </div>
  )
} 