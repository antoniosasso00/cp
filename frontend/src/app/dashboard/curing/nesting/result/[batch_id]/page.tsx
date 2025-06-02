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
  RefreshCw,
  Info
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import dynamic from 'next/dynamic'
import BatchNavigator from './BatchNavigator'

// Caricamento dinamico del canvas per evitare problemi SSR
const NestingCanvas = dynamic(() => import('./NestingCanvas'), {
  loading: () => <div className="flex items-center justify-center h-64"><span>Caricamento canvas...</span></div>,
  ssr: false
})

// Error Boundary semplificato
const CanvasErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  try {
    return <>{children}</>
  } catch (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg border border-red-200">
        <p className="text-red-600">Errore nel caricamento del canvas</p>
      </div>
    )
  }
}

// ✅ CORREZIONE: Interfacce corrette per i dati dal backend
interface ToolPosition {
  odl_id: number
  x: number
  y: number  
  width: number
  height: number
  peso: number
  rotated: boolean
  part_number?: string
  tool_nome?: string
}

interface AutoclaveInfo {
  id: number
  nome: string
  lunghezza: number
  larghezza_piano: number
  codice: string
  produttore?: string
}

interface BatchNestingResult {
  id: string
  nome: string
  stato: string
  autoclave_id: number
  autoclave?: AutoclaveInfo
  odl_ids: number[]
  // ✅ CORREZIONE: Struttura corretta della configurazione
  configurazione_json: {
    canvas_width: number
    canvas_height: number
    tool_positions: ToolPosition[]
    plane_assignments: Record<string, number>
  } | null
  parametri: {
    padding_mm: number
    min_distance_mm: number
    priorita_area: boolean
  }
  created_at: string
  numero_nesting: number
  peso_totale_kg?: number
  area_totale_utilizzata?: number
  valvole_totali_utilizzate?: number
  note?: string
  // 🎯 NUOVO v1.4.16-DEMO: Dati per motivi di esclusione
  odl_esclusi?: Array<{
    odl_id: number
    motivo: string
    dettagli?: string
    debug_reasons?: string[]
    motivi_dettagliati?: string
  }>
  excluded_reasons?: Record<string, number>
  metrics?: any
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

      // ✅ CORREZIONE: Usa URL relativo per sfruttare il proxy Next.js
      const response = await fetch(`/api/v1/batch_nesting/${params.batch_id}/full`)
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

      {/* ✅ NUOVO: Navigatore Batch - Solo se ci sono batch multipli */}
      <BatchNavigator 
        currentBatchId={batchData.id} 
        className="w-full"
      />

      {/* Contenuto principale con layout a griglia */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Colonna principale - Canvas e informazioni (3/4) */}
        <div className="lg:col-span-3 space-y-6">
          
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
                <p className="text-sm font-medium text-muted-foreground">ODL Posizionati</p>
                <p className="font-semibold">
                  {batchData.configurazione_json ? batchData.configurazione_json.tool_positions.length : 0}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Canvas Nesting */}
          {batchData.configurazione_json?.tool_positions && batchData.configurazione_json.tool_positions.length > 0 && batchData.autoclave ? (
            <CanvasErrorBoundary>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Visualizzazione Layout Nesting
                  </CardTitle>
                  <CardDescription>
                    Layout 2D interattivo del posizionamento degli ODL nell'autoclave
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <NestingCanvas 
                    batchData={{
                      configurazione_json: batchData.configurazione_json,
                      autoclave: batchData.autoclave,
                      odl_esclusi: batchData.odl_esclusi || [],
                      excluded_reasons: batchData.excluded_reasons || {},
                      metrics: batchData.metrics
                    }}
                    className="w-full"
                  />
                </CardContent>
              </Card>
            </CanvasErrorBoundary>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                  <div className="text-center text-gray-500">
                    <Package className="mx-auto h-12 w-12 mb-2 opacity-50" />
                    <p className="text-lg font-medium">Canvas non disponibile</p>
                    <p className="text-sm">Nessun tool posizionato nel nesting</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Status e Azioni Rapide */}
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
                  <Link href="/dashboard/curing/batch-monitoring">
                    <Button variant="outline">
                      <Package className="h-4 w-4 mr-2" />
                      Gestione Batch
                    </Button>
                  </Link>
                  <Button onClick={handleRetry}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Nuovo Nesting
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Colonna laterale - Dettagli e statistiche (1/4) */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Parametri Utilizzati */}
          <Card>
            <CardHeader>
              <CardTitle>Parametri Utilizzati</CardTitle>
              <CardDescription>
                Configurazione dell'algoritmo di ottimizzazione
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
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
                    <span className="text-blue-600">🎯 Massimizza ODL</span>
                  )}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Statistiche Risultato */}
          {(batchData.area_totale_utilizzata || batchData.peso_totale_kg || batchData.valvole_totali_utilizzate) && (
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
              <CardContent className="space-y-3">
                {batchData.area_totale_utilizzata && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Area Utilizzata</p>
                    <p className="font-semibold">{batchData.area_totale_utilizzata.toFixed(2)} cm²</p>
                  </div>
                )}
                {batchData.peso_totale_kg && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Peso Totale</p>
                    <p className="font-semibold">{batchData.peso_totale_kg.toFixed(2)} kg</p>
                  </div>
                )}
                {batchData.valvole_totali_utilizzate && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Valvole</p>
                    <p className="font-semibold">{batchData.valvole_totali_utilizzate}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Informazioni Autoclave */}
          {batchData.autoclave && (
            <Card>
              <CardHeader>
                <CardTitle>Autoclave</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Nome</p>
                  <p className="font-semibold">{batchData.autoclave.nome}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Dimensioni Piano</p>
                  <p className="font-semibold">
                    {batchData.autoclave.larghezza_piano} × {batchData.autoclave.lunghezza} mm
                  </p>
                </div>
                {batchData.autoclave.produttore && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Produttore</p>
                    <p className="font-semibold">{batchData.autoclave.produttore}</p>
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
        </div>
      </div>

      {/* Sezione ODL Inclusi */}
      <Card>
        <CardHeader>
          <CardTitle>ODL Inclusi nel Nesting</CardTitle>
          <CardDescription>
            Lista degli ordini di lavoro posizionati nel layout
          </CardDescription>
        </CardHeader>
        <CardContent>
          {batchData.configurazione_json?.tool_positions && batchData.configurazione_json.tool_positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">ODL ID</th>
                    <th className="text-left p-2">Posizione (X, Y)</th>
                    <th className="text-left p-2">Dimensioni (L × H)</th>
                    <th className="text-left p-2">Peso</th>
                    <th className="text-left p-2">Ruotato</th>
                  </tr>
                </thead>
                <tbody>
                  {batchData.configurazione_json.tool_positions.map((tool, index) => (
                    <tr key={index} className="border-b">
                      <td className="p-2 font-medium">ODL #{tool.odl_id}</td>
                      <td className="p-2">{tool.x.toFixed(0)}, {tool.y.toFixed(0)} mm</td>
                      <td className="p-2">{tool.width.toFixed(0)} × {tool.height.toFixed(0)} mm</td>
                      <td className="p-2">{tool.peso.toFixed(1)} kg</td>
                      <td className="p-2">{tool.rotated ? 'Sì' : 'No'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted-foreground">Nessun tool posizionato nel nesting.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 