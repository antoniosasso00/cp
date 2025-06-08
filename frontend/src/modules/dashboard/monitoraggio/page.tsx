'use client'

import { useState, useEffect } from 'react'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { catalogApi, phaseTimesApi, odlApi, CatalogoResponse } from '@/lib/api'
import { Loader2, AlertCircle, BarChart3, Clock, TrendingUp } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'

// Importo i componenti specifici per ogni tab
import PerformanceGenerale from './components/performance-generale'
import StatisticheCatalogo from './components/statistiche-catalogo'
import TempiODL from './components/tempi-odl'
// ✅ NUOVO: Componente Top Delta per v1.4.6-DEMO
import TopDeltaPanel from '@/components/TopDeltaPanel'

// Tipi per i filtri globali
interface FiltriGlobali {
  periodo: string;
  partNumber: string;
  statoODL: string;
  dataInizio?: Date;
  dataFine?: Date;
}

export default function MonitoraggioPage() {
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('performance')
  const [error, setError] = useState<string | null>(null)
  const { toast } = useStandardToast()

  // Filtri globali condivisi tra tutti i tabs
  const [filtri, setFiltri] = useState<FiltriGlobali>({
    periodo: '30',
    partNumber: 'all',
    statoODL: 'all'
  })

  // Carica il catalogo al caricamento della pagina
  useEffect(() => {
    const fetchCatalogo = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await catalogApi.fetchCatalogItems()
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

  // Aggiorna i filtri
  const updateFiltri = (nuoviFiltri: Partial<FiltriGlobali>) => {
    setFiltri(prev => ({ ...prev, ...nuoviFiltri }))
  }

  // Calcola le date di inizio e fine basate sul periodo selezionato
  useEffect(() => {
    const oggi = new Date()
    const giorni = parseInt(filtri.periodo)
    const dataInizio = new Date(oggi.getTime() - (giorni * 24 * 60 * 60 * 1000))
    
    setFiltri(prev => ({
      ...prev,
      dataInizio,
      dataFine: oggi
    }))
  }, [filtri.periodo])

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Caricamento dashboard...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard Monitoraggio</h1>
        <p className="text-muted-foreground">
          Analisi completa delle performance, statistiche catalogo e tempi ODL
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Errore</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filtri Globali */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filtri Globali</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="periodo">Periodo</Label>
              <Select
                value={filtri.periodo}
                onValueChange={(value) => updateFiltri({ periodo: value })}
              >
                <SelectTrigger>
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

            <div className="space-y-2">
              <Label htmlFor="partNumber">Part Number</Label>
              <Select
                value={filtri.partNumber}
                onValueChange={(value) => updateFiltri({ partNumber: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti i part number" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i part number</SelectItem>
                  {catalogo.map(item => (
                    <SelectItem key={item.part_number} value={item.part_number}>
                      {item.part_number} - {item.descrizione?.substring(0, 30)}...
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="statoODL">Stato ODL</Label>
              <Select
                value={filtri.statoODL}
                onValueChange={(value) => updateFiltri({ statoODL: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutti gli stati" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli stati</SelectItem>
                  <SelectItem value="Preparazione">Preparazione</SelectItem>
                  <SelectItem value="Laminazione">Laminazione</SelectItem>
                  <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                  <SelectItem value="Cura">Cura</SelectItem>
                  <SelectItem value="Completato">Completato</SelectItem>
                  <SelectItem value="Bloccato">Bloccato</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs principali */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Performance Generale
          </TabsTrigger>
          <TabsTrigger value="statistiche" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Statistiche Catalogo
          </TabsTrigger>
          <TabsTrigger value="tempi" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Tempi ODL
          </TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6">
          <PerformanceGenerale 
            filtri={filtri}
            catalogo={catalogo}
            onError={(message: string) => {
              setError(message)
              toast({
                variant: 'destructive',
                title: 'Errore',
                description: message,
              })
            }}
          />
        </TabsContent>

        <TabsContent value="statistiche" className="space-y-6">
          <StatisticheCatalogo 
            filtri={filtri}
            catalogo={catalogo}
            onError={(message: string) => {
              setError(message)
              toast({
                variant: 'destructive',
                title: 'Errore',
                description: message,
              })
            }}
          />
        </TabsContent>

        <TabsContent value="tempi" className="space-y-6">
          <TempiODL 
            filtri={filtri}
            catalogo={catalogo}
            onError={(message: string) => {
              setError(message)
              toast({
                variant: 'destructive',
                title: 'Errore',
                description: message,
              })
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Top Delta Panel */}
      <TopDeltaPanel />
    </div>
  )
} 