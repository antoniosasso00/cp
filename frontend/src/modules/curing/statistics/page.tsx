'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  BarChart3, 
  Clock, 
  TrendingUp, 
  Package, 
  Flame,
  Calendar,
  Target,
  Activity
} from 'lucide-react'
import { batchNestingApi } from '@/lib/api'

interface BatchStatistics {
  batch_id: string
  nome: string
  stato: string
  autoclave_id: number
  numero_odl: number
  numero_nesting: number
  peso_totale_kg: number
  area_totale_utilizzata: number
  valvole_totali_utilizzate: number
  efficienza_media: number
  created_at: string
  updated_at: string
  data_conferma: string
  data_completamento?: string
  durata_ciclo_minuti?: number
}

export default function StatisticsPage() {
  const [batchesTerminati, setBatchesTerminati] = useState<BatchStatistics[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBatchesTerminati()
  }, [])

  const loadBatchesTerminati = async () => {
    try {
      setLoading(true)
      // Carica tutti i batch terminati
      const response = await batchNestingApi.getAll({ stato: 'terminato', limit: 100 })
      
      // Carica statistiche dettagliate per ogni batch
      const batchesWithStats = await Promise.all(
        response.map(async (batch) => {
          try {
            const stats = await batchNestingApi.getStatistics(batch.id)
            return stats
          } catch (err) {
            console.error(`Errore caricamento statistiche batch ${batch.id}:`, err)
            return null
          }
        })
      )
      
      setBatchesTerminati(batchesWithStats.filter(Boolean))
    } catch (err) {
      console.error('Errore caricamento batch terminati:', err)
      setError('Errore nel caricamento delle statistiche')
    } finally {
      setLoading(false)
    }
  }

  // Calcola metriche aggregate
  const calculateMetrics = () => {
    if (batchesTerminati.length === 0) return null

    const totalBatches = batchesTerminati.length
    const totalODL = batchesTerminati.reduce((sum, b) => sum + b.numero_odl, 0)
    const totalPeso = batchesTerminati.reduce((sum, b) => sum + b.peso_totale_kg, 0)
    const avgEfficienza = batchesTerminati.reduce((sum, b) => sum + b.efficienza_media, 0) / totalBatches
    
    // Calcola durata media cicli (se disponibile)
    const batchesConDurata = batchesTerminati.filter(b => b.durata_ciclo_minuti)
    const avgDurataCiclo = batchesConDurata.length > 0 
      ? batchesConDurata.reduce((sum, b) => sum + (b.durata_ciclo_minuti || 0), 0) / batchesConDurata.length
      : 0

    return {
      totalBatches,
      totalODL,
      totalPeso,
      avgEfficienza,
      avgDurataCiclo
    }
  }

  const metrics = calculateMetrics()

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}m`
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-muted-foreground">Caricamento statistiche...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              <p>{error}</p>
              <Button onClick={loadBatchesTerminati} className="mt-4">
                Riprova
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Statistiche Produzione</h1>
          <p className="text-muted-foreground">
            Analisi delle performance dei batch completati
          </p>
        </div>
        <Button onClick={loadBatchesTerminati} variant="outline">
          <Activity className="h-4 w-4 mr-2" />
          Aggiorna
        </Button>
      </div>

      {/* Metriche Principali */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Batch Completati</p>
                  <p className="text-2xl font-bold">{metrics.totalBatches}</p>
                </div>
                <Package className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">ODL Processati</p>
                  <p className="text-2xl font-bold">{metrics.totalODL}</p>
                </div>
                <Target className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Peso Totale</p>
                  <p className="text-2xl font-bold">{metrics.totalPeso.toFixed(1)} kg</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Efficienza Media</p>
                  <p className="text-2xl font-bold">{metrics.avgEfficienza.toFixed(1)}%</p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Durata Media</p>
                  <p className="text-2xl font-bold">
                    {metrics.avgDurataCiclo > 0 ? formatDuration(metrics.avgDurataCiclo) : 'N/A'}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Dettagli Batch */}
      <Tabs defaultValue="recent" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recent">Batch Recenti</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="trends">Tendenze</TabsTrigger>
        </TabsList>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Batch Completati di Recente</CardTitle>
              <CardDescription>
                Ultimi batch terminati con dettagli di performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {batchesTerminati.slice(0, 10).map((batch) => (
                  <div key={batch.batch_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold">{batch.nome}</h3>
                        <Badge variant="secondary">
                          {batch.numero_odl} ODL
                        </Badge>
                        <Badge variant="outline">
                          Autoclave {batch.autoclave_id}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                        <span>Peso: {batch.peso_totale_kg.toFixed(1)} kg</span>
                        <span>Efficienza: {batch.efficienza_media.toFixed(1)}%</span>
                        {batch.durata_ciclo_minuti && (
                          <span>Durata: {formatDuration(batch.durata_ciclo_minuti)}</span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {new Date(batch.updated_at).toLocaleDateString('it-IT')}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(batch.updated_at).toLocaleTimeString('it-IT', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Performer per Efficienza */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Top Performance - Efficienza
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {batchesTerminati
                    .sort((a, b) => b.efficienza_media - a.efficienza_media)
                    .slice(0, 5)
                    .map((batch, index) => (
                      <div key={batch.batch_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold">
                            {index + 1}
                          </div>
                          <span className="font-medium">{batch.nome}</span>
                        </div>
                        <Badge variant="secondary">
                          {batch.efficienza_media.toFixed(1)}%
                        </Badge>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Performer per Velocità */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Top Performance - Velocità
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {batchesTerminati
                    .filter(b => b.durata_ciclo_minuti)
                    .sort((a, b) => (a.durata_ciclo_minuti || 0) - (b.durata_ciclo_minuti || 0))
                    .slice(0, 5)
                    .map((batch, index) => (
                      <div key={batch.batch_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                            {index + 1}
                          </div>
                          <span className="font-medium">{batch.nome}</span>
                        </div>
                        <Badge variant="secondary">
                          {batch.durata_ciclo_minuti ? formatDuration(batch.durata_ciclo_minuti) : 'N/A'}
                        </Badge>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Analisi Tendenze</CardTitle>
              <CardDescription>
                Tendenze di produzione negli ultimi batch completati
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4" />
                <p>Grafici di tendenza in sviluppo</p>
                <p className="text-sm">Questa sezione includerà grafici interattivi per analizzare le tendenze di produzione</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 