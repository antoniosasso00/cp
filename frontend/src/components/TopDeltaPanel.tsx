'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Loader2, AlertCircle, TrendingUp } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { standardTimesApi, TopDeltaVariance } from '@/lib/api'

interface TopDeltaPanelProps {
  limit?: number;
  days?: number;
  className?: string;
}

export default function TopDeltaPanel({ limit = 5, days = 30, className }: TopDeltaPanelProps) {
  const [data, setData] = useState<TopDeltaVariance[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch dei dati
  useEffect(() => {
    const fetchTopDelta = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        const response = await standardTimesApi.getTopDelta(limit, days)
        setData(response.data)
        
      } catch (err) {
        console.error('Errore nel caricamento top delta:', err)
        const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto'
        setError(`Impossibile caricare i dati di scostamento: ${errorMessage}`)
      } finally {
        setIsLoading(false)
      }
    }

    fetchTopDelta()
  }, [limit, days])

  // Determina il variant del badge in base al colore
  const getBadgeVariant = (colore: "verde" | "giallo" | "rosso") => {
    switch (colore) {
      case 'verde':
        return 'default' // Verde per scostamenti accettabili
      case 'giallo':
        return 'secondary' // Giallo per scostamenti moderati
      case 'rosso':
        return 'destructive' // Rosso per scostamenti critici
      default:
        return 'outline'
    }
  }

  // Formatta il delta percentuale con segno
  const formatDelta = (delta: number) => {
    const sign = delta >= 0 ? '+' : ''
    return `${sign}${delta.toFixed(1)}%`
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            📈 Top 5 Part con maggiore scostamento (%)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Caricamento dati scostamento...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            📈 Top 5 Part con maggiore scostamento (%)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            📈 Top 5 Part con maggiore scostamento (%)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Nessun dato di scostamento disponibile per gli ultimi {days} giorni.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            📈 Top 5 Part con maggiore scostamento (%)
          </div>
          <Badge variant="outline" className="text-xs">
            Ultimi {days} giorni
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Part Number</TableHead>
              <TableHead>Fase</TableHead>
              <TableHead className="text-center">Scostamento %</TableHead>
              <TableHead className="text-right">Tempo Oss.</TableHead>
              <TableHead className="text-right">Tempo Std.</TableHead>
              <TableHead className="text-center">Oss.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item, index) => (
              <TableRow key={`${item.part_number}-${item.fase}`}>
                <TableCell className="font-medium">{item.part_number}</TableCell>
                <TableCell className="capitalize">{item.fase}</TableCell>
                <TableCell className="text-center">
                  <Badge variant={getBadgeVariant(item.colore_delta)}>
                    {formatDelta(item.delta_percent)}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {item.tempo_osservato.toFixed(1)}min
                </TableCell>
                <TableCell className="text-right">
                  {item.tempo_standard.toFixed(1)}min
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className="text-xs">
                    {item.numero_osservazioni}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {data.length > 0 && (
          <div className="mt-4 text-xs text-muted-foreground">
            <p>
              <strong>Legenda colori:</strong> Verde ≤ 5% | Giallo 5-10% | Rosso &gt; 10%
            </p>
            <p>
              <strong>Oss.:</strong> Numero di osservazioni utilizzate per il calcolo
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 