'use client'

import { useState, useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { catalogoApi, tempoFasiApi, CatalogoResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { Loader2, AlertCircle } from 'lucide-react'
import { formatDuration } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Label } from '@/components/ui/label'

// Funzione per tradurre il tipo di fase
const translateFase = (fase: string): string => {
  const translations: Record<string, string> = {
    'laminazione': 'Laminazione',
    'attesa_cura': 'Attesa Cura',
    'cura': 'Cura'
  };
  return translations[fase] || fase;
}

// Colori per le fasi
const colors: Record<string, string> = {
  'Laminazione': '#3b82f6',  // primary
  'Attesa Cura': '#f59e0b',  // warning
  'Cura': '#ef4444'          // destructive
}

// Componente per il tooltip personalizzato del grafico
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-2 border rounded shadow-sm">
        <p className="font-semibold">{data.name}</p>
        <p>Media: {formatDuration(data.media)}</p>
        <p className="text-xs text-muted-foreground">
          Deviazione std: ±{Math.round(data.deviazione)} min
        </p>
        <p className="text-xs text-muted-foreground">
          Basata su {data.osservazioni} osservazioni
        </p>
      </div>
    );
  }
  return null;
};

export default function StatisticheCatalogo() {
  const [catalogo, setCatalogo] = useState<CatalogoResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPartNumber, setSelectedPartNumber] = useState<string>('')
  const [rangeTempo, setRangeTempo] = useState<string>('30')
  const [statistiche, setStatistiche] = useState<any>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const { toast } = useToast()

  // Carica il catalogo al caricamento della pagina
  useEffect(() => {
    const fetchCatalogo = async () => {
      try {
        setIsLoading(true)
        const data = await catalogoApi.getAll()
        setCatalogo(data.filter(item => item.attivo)) // Solo parti attive
      } catch (error) {
        console.error('Errore nel caricamento del catalogo:', error)
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
    const fetchStatistiche = async () => {
      if (!selectedPartNumber) {
        setStatistiche(null)
        return
      }
      
      try {
        setLoadingStats(true)
        
        // Chiamata all'API per recuperare le statistiche
        const giorni = parseInt(rangeTempo)
        const result = await tempoFasiApi.getStatisticheByPartNumber(selectedPartNumber, giorni)
        setStatistiche(result)
      } catch (error) {
        console.error('Errore nel caricamento delle statistiche:', error)
        toast({
          variant: 'destructive',
          title: 'Errore',
          description: 'Impossibile caricare le statistiche. Riprova più tardi.',
        })
      } finally {
        setLoadingStats(false)
      }
    }
    
    if (selectedPartNumber) {
      fetchStatistiche()
    }
  }, [selectedPartNumber, rangeTempo, toast])

  // Filtra il catalogo in base alla ricerca
  const filteredCatalogo = catalogo.filter(item => {
    const searchLower = searchQuery.toLowerCase()
    return (
      item.part_number.toLowerCase().includes(searchLower) ||
      item.descrizione.toLowerCase().includes(searchLower) ||
      (item.categoria && item.categoria.toLowerCase().includes(searchLower))
    )
  })

  // Prepara i dati per il grafico
  const prepareChartData = () => {
    if (!statistiche) return []
    
    const data: any[] = []
    
    // Aggiungi dati per ogni fase
    Object.entries(statistiche.previsioni).forEach(([fase, stats]: [string, any]) => {
      // Calcola una deviazione standard fittizia (10% della media)
      const deviazione = stats.media_minuti * 0.1
      
      data.push({
        name: translateFase(fase),
        media: stats.media_minuti,
        deviazione: deviazione,
        osservazioni: stats.numero_osservazioni,
        color: colors[translateFase(fase)] || '#888888'
      })
    })
    
    return data
  }

  const chartData = prepareChartData()
  const nonHaODLCompletati = statistiche && statistiche.totale_odl === 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Statistiche Catalogo</h1>
        <p className="text-muted-foreground">
          Analisi dei tempi di produzione per part number
        </p>
      </div>

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
              ) : nonHaODLCompletati ? (
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
                        {statistiche.totale_odl}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        ODL Completati
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {formatDuration(
                          Object.values(statistiche.previsioni).reduce(
                            (acc: number, curr: any) => acc + curr.media_minuti, 
                            0
                          )
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Tempo Totale Medio
                      </div>
                    </div>
                    
                    <div className="p-4 bg-muted rounded-lg text-center">
                      <div className="text-2xl font-bold">
                        {Math.round(
                          Object.values(statistiche.previsioni).reduce(
                            (acc: number, curr: any) => curr.media_minuti > 0 ? acc + 1 : acc, 
                            0
                          )
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Fasi Registrate
                      </div>
                    </div>
                  </div>
                  
                  <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={chartData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis 
                          label={{ 
                            value: 'Minuti', 
                            angle: -90, 
                            position: 'insideLeft', 
                            style: { textAnchor: 'middle' } 
                          }} 
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Bar 
                          dataKey="media" 
                          name="Tempo Medio (min)" 
                          radius={[4, 4, 0, 0]}
                        >
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
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