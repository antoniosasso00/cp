'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, TrendingUp, Clock, Activity } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

interface TempoFaseStatistiche {
  fase: string
  media_minuti: number
  numero_osservazioni: number
  tempo_minimo_minuti?: number
  tempo_massimo_minuti?: number
}

// Mappa i nomi delle fasi per la visualizzazione
const FASE_LABELS: Record<string, string> = {
  'laminazione': 'Laminazione',
  'attesa_cura': 'Attesa Cura',
  'cura': 'Cura'
}

// Colori per il grafico
const FASE_COLORS: Record<string, string> = {
  'laminazione': '#10b981', // green-500
  'attesa_cura': '#f59e0b', // amber-500
  'cura': '#ef4444' // red-500
}

export default function TempoFasiPage() {
  const [statistiche, setStatistiche] = useState<TempoFaseStatistiche[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Funzione per caricare i dati
  const fetchTempoFasi = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('/api/tempo-fasi/tempo-fasi')
      
      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`)
      }
      
      const data = await response.json()
      setStatistiche(data)
    } catch (err) {
      console.error('Errore nel caricamento dei dati:', err)
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTempoFasi()
  }, [])

  // Prepara i dati per il grafico
  const chartData = statistiche.map(stat => ({
    fase: FASE_LABELS[stat.fase] || stat.fase,
    tempo_medio: Math.round(stat.media_minuti * 100) / 100, // Arrotonda a 2 decimali
    osservazioni: stat.numero_osservazioni,
    min: stat.tempo_minimo_minuti ? Math.round(stat.tempo_minimo_minuti * 100) / 100 : 0,
    max: stat.tempo_massimo_minuti ? Math.round(stat.tempo_massimo_minuti * 100) / 100 : 0
  }))

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Caricamento statistiche tempi fasi...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Errore nel caricamento</CardTitle>
            <CardDescription>
              Si è verificato un errore durante il caricamento dei dati delle fasi.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">{error}</p>
            <button 
              onClick={fetchTempoFasi}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Riprova
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <Clock className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tempo Fasi Produzione</h1>
          <p className="text-muted-foreground">
            Analisi dei tempi medi per ogni fase del processo produttivo
          </p>
        </div>
      </div>

      {/* Statistiche riassuntive */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {statistiche.map((stat) => (
          <Card key={stat.fase}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {FASE_LABELS[stat.fase] || stat.fase}
              </CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.round(stat.media_minuti)} min
              </div>
              <p className="text-xs text-muted-foreground">
                {stat.numero_osservazioni} osservazioni
              </p>
              {stat.tempo_minimo_minuti && stat.tempo_massimo_minuti && (
                <p className="text-xs text-muted-foreground mt-1">
                  Range: {Math.round(stat.tempo_minimo_minuti)}-{Math.round(stat.tempo_massimo_minuti)} min
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Grafico principale */}
      {chartData.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Tempi Medi per Fase
            </CardTitle>
            <CardDescription>
              Visualizzazione grafica dei tempi medi di ogni fase di produzione (in minuti)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="fase" 
                    tick={{ fontSize: 12 }}
                    interval={0}
                  />
                  <YAxis 
                    label={{ value: 'Tempo (minuti)', angle: -90, position: 'insideLeft' }}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip 
                    formatter={(value: any, name: any) => {
                      const nameStr = String(name)
                      if (nameStr === 'tempo_medio') return [`${value} min`, 'Tempo Medio']
                      if (nameStr === 'min') return [`${value} min`, 'Minimo']
                      if (nameStr === 'max') return [`${value} min`, 'Massimo']
                      return [value, nameStr]
                    }}
                    labelFormatter={(label) => `Fase: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="tempo_medio" 
                    stroke="#2563eb" 
                    strokeWidth={3}
                    dot={{ fill: '#2563eb', strokeWidth: 2, r: 6 }}
                    name="Tempo Medio"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="min" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ fill: '#10b981', strokeWidth: 1, r: 4 }}
                    name="Tempo Minimo"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="max" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ fill: '#ef4444', strokeWidth: 1, r: 4 }}
                    name="Tempo Massimo"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Nessun dato disponibile</CardTitle>
            <CardDescription>
              Non sono ancora disponibili dati sui tempi delle fasi di produzione.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              I dati saranno disponibili dopo aver registrato alcuni tempi di fase negli ODL.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 