'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/hooks/use-toast'
import { 
  ArrowLeft, 
  RefreshCw, 
  Download, 
  Eye, 
  Package, 
  Wrench, 
  Calendar, 
  BarChart3,
  CheckCircle,
  Clock,
  Play,
  AlertTriangle,
  FileText,
  Layers,
  Settings
} from 'lucide-react'
import { 
  nestingApi, 
  NestingDetailResponse, 
  NestingLayoutData,
  NestingLayoutResponse 
} from '@/lib/api'

export default function NestingDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  
  const nestingId = parseInt(params.id as string)
  
  const [nestingDetails, setNestingDetails] = useState<NestingDetailResponse | null>(null)
  const [layoutData, setLayoutData] = useState<NestingLayoutData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingLayout, setIsLoadingLayout] = useState(false)
  const [downloadingReport, setDownloadingReport] = useState(false)

  // Carica i dettagli del nesting
  const loadNestingDetails = async () => {
    try {
      setIsLoading(true)
      const details = await nestingApi.getDetails(nestingId)
      setNestingDetails(details)
    } catch (error: any) {
      toast({
        title: "Errore",
        description: `Impossibile caricare i dettagli del nesting #${nestingId}`,
        variant: "destructive",
      })
      // Torna alla pagina principale se il nesting non esiste
      router.push('/dashboard/curing/nesting')
    } finally {
      setIsLoading(false)
    }
  }

  // Carica il layout grafico del nesting
  const loadNestingLayout = async () => {
    try {
      setIsLoadingLayout(true)
      const layoutResponse: NestingLayoutResponse = await nestingApi.getLayout(nestingId, {
        padding_mm: 20,
        borda_mm: 15,
        rotazione_abilitata: true
      })
      
      if (layoutResponse.success && layoutResponse.layout_data) {
        setLayoutData(layoutResponse.layout_data)
      }
    } catch (error: any) {
      console.warn('Layout non disponibile per questo nesting:', error.message)
      // Non mostrare errore per layout non disponibile
    } finally {
      setIsLoadingLayout(false)
    }
  }

  // Scarica il report del nesting
  const handleDownloadReport = async () => {
    if (!nestingDetails) return
    
    try {
      setDownloadingReport(true)
      
      // Genera il report
      const reportInfo = await nestingApi.generateReport(nestingId)
      
      // Scarica il report
      const blob = await nestingApi.downloadReport(nestingId)
      
      // Crea link per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = reportInfo.filename || `nesting_${nestingId}_report.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Report Scaricato",
        description: `Report del nesting #${nestingId} scaricato con successo`,
      })
    } catch (error: any) {
      toast({
        title: "Errore Download",
        description: error.message || "Impossibile scaricare il report",
        variant: "destructive",
      })
    } finally {
      setDownloadingReport(false)
    }
  }

  // Carica i dati al primo render
  useEffect(() => {
    if (nestingId && !isNaN(nestingId)) {
      loadNestingDetails()
      loadNestingLayout()
    }
  }, [nestingId])

  // Funzione per ottenere l'icona dello stato
  const getStatusIcon = (stato: string) => {
    switch (stato.toLowerCase()) {
      case 'bozza':
        return <FileText className="h-5 w-5 text-gray-600" />
      case 'confermato':
      case 'in sospeso':
        return <Clock className="h-5 w-5 text-yellow-600" />
      case 'cura':
        return <Play className="h-5 w-5 text-blue-600" />
      case 'finito':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'errore':
        return <AlertTriangle className="h-5 w-5 text-red-600" />
      default:
        return <Eye className="h-5 w-5 text-gray-600" />
    }
  }

  // Funzione per ottenere il colore del badge
  const getStatusBadgeVariant = (stato: string) => {
    switch (stato.toLowerCase()) {
      case 'bozza':
        return 'outline'
      case 'confermato':
      case 'in sospeso':
        return 'secondary'
      case 'cura':
        return 'default'
      case 'finito':
        return 'default'
      case 'errore':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  // Componente per il layout grafico semplificato
  const NestingLayoutVisualization = ({ layout }: { layout: NestingLayoutData }) => {
    const scaleX = 400 / layout.autoclave.lunghezza // Scala per adattare alla larghezza del container
    const scaleY = 300 / layout.autoclave.larghezza_piano // Scala per adattare all'altezza del container
    
    return (
      <div className="relative bg-gray-50 border rounded-lg p-4">
        <div className="text-sm text-muted-foreground mb-2">
          Layout Autoclave: {layout.autoclave.nome} ({layout.autoclave.lunghezza} x {layout.autoclave.larghezza_piano} mm)
        </div>
        
        {/* Rappresentazione dell'autoclave */}
        <div 
          className="relative border-2 border-gray-400 bg-white mx-auto"
          style={{
            width: `${layout.autoclave.lunghezza * scaleX}px`,
            height: `${layout.autoclave.larghezza_piano * scaleY}px`,
            maxWidth: '400px',
            maxHeight: '300px'
          }}
        >
          {/* Posizioni dei tool */}
          {layout.posizioni_tool.map((pos, index) => (
            <div
              key={`${pos.odl_id}-${index}`}
              className="absolute border border-blue-500 bg-blue-100 opacity-80 flex items-center justify-center text-xs font-medium"
              style={{
                left: `${pos.x * scaleX}px`,
                top: `${pos.y * scaleY}px`,
                width: `${pos.width * scaleX}px`,
                height: `${pos.height * scaleY}px`,
                transform: pos.rotated ? 'rotate(90deg)' : 'none',
                transformOrigin: 'center'
              }}
              title={`ODL #${pos.odl_id} - Piano ${pos.piano}${pos.rotated ? ' (Ruotato)' : ''}`}
            >
              <span className="text-blue-700">
                {pos.odl_id}
              </span>
            </div>
          ))}
        </div>
        
        <div className="mt-2 text-xs text-muted-foreground text-center">
          Efficienza: {((layout.area_utilizzata / layout.area_totale) * 100).toFixed(1)}% 
          • Valvole: {layout.valvole_utilizzate}/{layout.valvole_totali}
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="flex justify-between">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  if (!nestingDetails) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-2xl font-bold mb-2">Nesting non trovato</h2>
          <p className="text-muted-foreground mb-4">
            Il nesting #{nestingId} non esiste o non è accessibile.
          </p>
          <Button onClick={() => router.push('/dashboard/curing/nesting')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Torna alla lista
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/dashboard/curing/nesting')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Indietro
          </Button>
          
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              {getStatusIcon(nestingDetails.stato)}
              Nesting #{nestingId}
            </h1>
            <p className="text-muted-foreground">
              Dettagli completi del layout di nesting per {nestingDetails.autoclave.nome}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              loadNestingDetails()
              loadNestingLayout()
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          
          {['finito', 'completato'].includes(nestingDetails.stato.toLowerCase()) && (
            <Button
              onClick={handleDownloadReport}
              disabled={downloadingReport}
            >
              {downloadingReport ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {downloadingReport ? 'Generando...' : 'Scarica Report'}
            </Button>
          )}
        </div>
      </div>

      {/* Contenuto principale */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Colonna principale - Dettagli e Layout */}
        <div className="lg:col-span-2 space-y-6">
          {/* Informazioni generali */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Informazioni Generali
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Stato</label>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={getStatusBadgeVariant(nestingDetails.stato)}>
                        {nestingDetails.stato}
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Autoclave</label>
                    <p className="font-medium">{nestingDetails.autoclave.nome}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Data Creazione</label>
                    <p className="font-medium">
                      {new Date(nestingDetails.created_at).toLocaleString('it-IT')}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">ODL Inclusi</label>
                    <p className="font-medium text-green-600">{nestingDetails.odl_inclusi.length}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">ODL Esclusi</label>
                    <p className="font-medium text-orange-600">{nestingDetails.odl_esclusi.length}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Efficienza</label>
                    <p className="font-medium">
                      {(nestingDetails.statistiche.efficienza * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
              
              {nestingDetails.note && (
                <div className="mt-4 pt-4 border-t">
                  <label className="text-sm font-medium text-muted-foreground">Note</label>
                  <p className="mt-1">{nestingDetails.note}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Layout grafico */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Layout Grafico
                {isLoadingLayout && <RefreshCw className="h-4 w-4 animate-spin ml-2" />}
              </CardTitle>
              <CardDescription>
                Visualizzazione del posizionamento dei tool nell'autoclave
              </CardDescription>
            </CardHeader>
            <CardContent>
              {layoutData ? (
                <NestingLayoutVisualization layout={layoutData} />
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Layers className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Layout grafico non disponibile</p>
                  <p className="text-sm">Il layout potrebbe non essere stato ancora generato</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ODL Inclusi */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                ODL Inclusi ({nestingDetails.odl_inclusi.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {nestingDetails.odl_inclusi.map((odl) => (
                  <div key={odl.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline">ODL #{odl.id}</Badge>
                      <div>
                        <p className="font-medium">{odl.parte_codice || 'Parte non specificata'}</p>
                        <p className="text-sm text-muted-foreground">
                          Tool: {odl.tool_nome || 'Tool non specificato'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <p className="font-medium">Priorità: {odl.priorita}</p>
                      <p className="text-muted-foreground">
                        {odl.dimensioni.larghezza}×{odl.dimensioni.lunghezza} mm
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Statistiche e ODL Esclusi */}
        <div className="space-y-6">
          {/* Statistiche */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistiche
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Area Utilizzata</span>
                  <span className="font-medium">
                    {nestingDetails.statistiche.area_utilizzata.toFixed(0)} cm²
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Area Totale</span>
                  <span className="font-medium">
                    {nestingDetails.statistiche.area_totale.toFixed(0)} cm²
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Efficienza</span>
                  <span className="font-medium text-green-600">
                    {(nestingDetails.statistiche.efficienza * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Peso Totale</span>
                  <span className="font-medium">
                    {nestingDetails.statistiche.peso_totale.toFixed(1)} kg
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Valvole</span>
                  <span className="font-medium">
                    {nestingDetails.statistiche.valvole_utilizzate}/{nestingDetails.statistiche.valvole_totali}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Autoclave Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Autoclave
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Nome</label>
                  <p className="font-medium">{nestingDetails.autoclave.nome}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Dimensioni Piano</label>
                  <p className="font-medium">
                    {nestingDetails.autoclave.area_piano.toFixed(0)} cm²
                  </p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Stato</label>
                  <p className="font-medium">{nestingDetails.autoclave.stato}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ODL Esclusi */}
          {nestingDetails.odl_esclusi.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  ODL Esclusi ({nestingDetails.odl_esclusi.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {nestingDetails.odl_esclusi.slice(0, 5).map((odl) => (
                    <div key={odl.id} className="p-3 border border-orange-200 rounded-lg bg-orange-50">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-orange-600">
                          ODL #{odl.id}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium">{odl.parte_codice || 'Parte non specificata'}</p>
                      <p className="text-xs text-muted-foreground">
                        {odl.tool_nome || 'Tool non specificato'}
                      </p>
                    </div>
                  ))}
                  
                  {nestingDetails.odl_esclusi.length > 5 && (
                    <p className="text-sm text-muted-foreground text-center">
                      ... e altri {nestingDetails.odl_esclusi.length - 5} ODL esclusi
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Motivi Esclusione */}
          {nestingDetails.motivi_esclusione.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  Motivi Esclusione
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {nestingDetails.motivi_esclusione.map((motivo, index) => (
                    <div key={index} className="p-2 bg-red-50 border border-red-200 rounded text-sm">
                      {motivo}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
} 