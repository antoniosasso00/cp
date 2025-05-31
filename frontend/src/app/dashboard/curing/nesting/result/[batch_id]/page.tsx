'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/components/ui/use-toast'
import { 
  Loader2, 
  ArrowLeft, 
  Package, 
  Flame, 
  CheckCircle2, 
  AlertTriangle,
  Download,
  RefreshCw
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface BatchNestingResult {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  odl_ids: number[]
  parametri: {
    padding_mm: number
    min_distance_mm: number
    priorita_area: boolean
    accorpamento_odl: boolean
  }
  created_at: string
  numero_nesting: number
  area_utilizzata?: number
  peso_totale_kg?: number
  valvole_utilizzate?: number
  valvole_totali?: number
  note?: string
}

interface Props {
  params: {
    batch_id: string
  }
}

export default function NestingResultPage({ params }: Props) {
  const { toast } = useToast()
  const router = useRouter()
  const [batchData, setBatchData] = useState<BatchNestingResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBatchData()
  }, [params.batch_id])

  const loadBatchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`/api/batch_nesting/${params.batch_id}`)
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Batch nesting non trovato')
        }
        throw new Error(`Errore ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      setBatchData(data)

    } catch (error) {
      console.error('Errore nel caricamento batch:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto'
      setError(errorMessage)
      
      toast({
        title: 'Errore di caricamento',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatoBadge = (stato: string) => {
    switch (stato) {
      case 'COMPLETATO':
        return <Badge className="bg-green-600 hover:bg-green-700">Completato</Badge>
      case 'IN_ELABORAZIONE':
        return <Badge className="bg-blue-600 hover:bg-blue-700">In Elaborazione</Badge>
      case 'ERRORE':
        return <Badge variant="destructive">Errore</Badge>
      case 'IN_SOSPESO':
        return <Badge variant="secondary">In Sospeso</Badge>
      default:
        return <Badge variant="outline">{stato}</Badge>
    }
  }

  const handleDownloadReport = () => {
    toast({
      title: 'Funzionalità in sviluppo',
      description: 'Il download del report sarà disponibile nella prossima versione.',
      variant: 'default'
    })
  }

  const handleRetry = () => {
    router.push('/dashboard/curing/nesting')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Caricamento risultati nesting...</span>
        </div>
      </div>
    )
  }

  if (error || !batchData) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center mb-6">
          <Link href="/dashboard/curing/nesting">
            <Button variant="ghost" className="mr-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Torna al Nesting
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-destructive">Errore</h1>
            <p className="text-muted-foreground">
              Impossibile caricare i risultati del nesting
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center py-8">
              <div className="text-center space-y-4">
                <AlertTriangle className="h-12 w-12 text-destructive mx-auto" />
                <div>
                  <h3 className="text-lg font-semibold">Nesting non trovato</h3>
                  <p className="text-muted-foreground">
                    {error || 'Il batch nesting richiesto non è stato trovato.'}
                  </p>
                </div>
                <div className="flex justify-center gap-2">
                  <Button onClick={handleRetry} variant="default">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Riprova
                  </Button>
                  <Button onClick={() => router.back()} variant="outline">
                    Torna Indietro
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link href="/dashboard/curing/nesting">
            <Button variant="ghost" className="mr-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Torna al Nesting
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Risultato Nesting</h1>
            <p className="text-muted-foreground">
              Batch ID: {batchData.id}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatoBadge(batchData.stato)}
        </div>
      </div>

      {/* Informazioni Generali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Informazioni Generali
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Nome Batch</p>
            <p className="font-semibold">{batchData.nome}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Data Creazione</p>
            <p className="font-semibold">
              {new Date(batchData.created_at).toLocaleDateString('it-IT', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">ODL Inclusi</p>
            <p className="font-semibold">{batchData.odl_ids.length}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Numero Nesting</p>
            <p className="font-semibold">{batchData.numero_nesting}</p>
          </div>
        </CardContent>
      </Card>

      {/* Parametri Utilizzati */}
      <Card>
        <CardHeader>
          <CardTitle>Parametri Utilizzati</CardTitle>
          <CardDescription>
            Configurazione dell'algoritmo di ottimizzazione
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Padding</p>
            <p className="font-semibold">{batchData.parametri.padding_mm} mm</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Distanza Minima</p>
            <p className="font-semibold">{batchData.parametri.min_distance_mm} mm</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Priorità Area</p>
            <p className="font-semibold">
              {batchData.parametri.priorita_area ? (
                <span className="text-green-600">✓ Attivata</span>
              ) : (
                <span className="text-gray-500">✗ Disattivata</span>
              )}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Accorpamento ODL</p>
            <p className="font-semibold">
              {batchData.parametri.accorpamento_odl ? (
                <span className="text-green-600">✓ Attivato</span>
              ) : (
                <span className="text-gray-500">✗ Disattivato</span>
              )}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Statistiche Risultato */}
      {(batchData.area_utilizzata || batchData.peso_totale_kg || batchData.valvole_utilizzate) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5" />
              Statistiche Risultato
            </CardTitle>
            <CardDescription>
              Risultati dell'ottimizzazione del nesting
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {batchData.area_utilizzata && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Area Utilizzata</p>
                <p className="font-semibold">{batchData.area_utilizzata.toFixed(2)} cm²</p>
              </div>
            )}
            {batchData.peso_totale_kg && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Peso Totale</p>
                <p className="font-semibold">{batchData.peso_totale_kg.toFixed(2)} kg</p>
              </div>
            )}
            {batchData.valvole_utilizzate && batchData.valvole_totali && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Valvole</p>
                <p className="font-semibold">
                  {batchData.valvole_utilizzate} / {batchData.valvole_totali}
                  <span className="text-sm text-muted-foreground ml-1">
                    ({Math.round((batchData.valvole_utilizzate / batchData.valvole_totali) * 100)}%)
                  </span>
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Note */}
      {batchData.note && (
        <Card>
          <CardHeader>
            <CardTitle>Note</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{batchData.note}</p>
          </CardContent>
        </Card>
      )}

      {/* ODL Inclusi */}
      <Card>
        <CardHeader>
          <CardTitle>ODL Inclusi nel Nesting</CardTitle>
          <CardDescription>
            Lista degli ordini di lavoro processati
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {batchData.odl_ids.map((odlId) => (
              <Badge key={odlId} variant="secondary" className="justify-center">
                ODL #{odlId}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Azioni */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="font-medium">
                  Nesting completato con successo
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Puoi ora procedere con la fase di caricamento o generare un nuovo nesting
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button onClick={handleDownloadReport} variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </Button>
              <Button onClick={handleRetry}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Nuovo Nesting
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder per Canvas Grafico */}
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-muted-foreground">Visualizzazione Grafica</CardTitle>
          <CardDescription>
            La visualizzazione canvas 2D del layout sarà implementata nella prossima versione
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-16 bg-muted/30 rounded-lg">
            <div className="text-center space-y-2">
              <Package className="h-12 w-12 text-muted-foreground mx-auto" />
              <p className="text-muted-foreground">Canvas Nesting 2D</p>
              <p className="text-sm text-muted-foreground">
                Prossimamente: visualizzazione interattiva del layout
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 