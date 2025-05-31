'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, RefreshCw, Eye, Calendar, Download, FileText, Clock, Play, CheckSquare, Wrench, Package } from 'lucide-react'
import { ActiveNestingTable } from '@/components/Nesting/ActiveNestingTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { nestingApi, NestingResponse, NestingDetailResponse } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface ConfirmedLayoutsTabProps {
  onViewDetails: (nestingId: number) => Promise<void>
  onRefresh?: () => Promise<void>
}

// ✅ NUOVO: Interfaccia per i dati arricchiti del nesting
interface EnrichedNestingData extends NestingResponse {
  dettagli?: NestingDetailResponse;
  tool_principale?: string;
  odl_count?: number;
}

export function ConfirmedLayoutsTab({ onViewDetails, onRefresh }: ConfirmedLayoutsTabProps) {
  const [confirmedNestings, setConfirmedNestings] = useState<EnrichedNestingData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set())
  const [loadingDetails, setLoadingDetails] = useState<Set<string>>(new Set())
  const { toast } = useToast()

  // ✅ NUOVO: Funzione per arricchire i dati del nesting con dettagli aggiuntivi
  const enrichNestingData = async (nesting: NestingResponse): Promise<EnrichedNestingData> => {
    try {
      setLoadingDetails(prev => new Set(prev).add(nesting.id))
      
      // Carica i dettagli del nesting per ottenere informazioni sui tool
      const dettagli = await nestingApi.getDetails(parseInt(nesting.id))
      
      // Estrae il tool principale (primo tool degli ODL inclusi)
      const tool_principale = dettagli.odl_inclusi?.[0]?.tool_nome || 
                             dettagli.odl_inclusi?.[0]?.parte_codice || 
                             undefined
      
      const enrichedData: EnrichedNestingData = {
        ...nesting,
        dettagli,
        tool_principale,
        odl_count: dettagli.odl_inclusi?.length || nesting.odl_inclusi || 0
      }
      
      return enrichedData
    } catch (error) {
      // Gestisce silenziosamente gli errori di caricamento dettagli
      return {
        ...nesting,
        odl_count: nesting.odl_inclusi || 0
      }
    } finally {
      setLoadingDetails(prev => {
        const newSet = new Set(prev)
        newSet.delete(nesting.id)
        return newSet
      })
    }
  }

  // Funzione per caricare i nesting confermati
  const loadConfirmedNestings = async () => {
    try {
      setIsLoading(true)
      const allNestings = await nestingApi.getAll()
      
      // Filtra solo i nesting confermati (stato diverso da 'bozza')
      const confirmed = allNestings.filter(nesting => 
        ['sospeso', 'cura', 'finito', 'confermato', 'in_corso', 'completato'].includes(nesting.stato.toLowerCase())
      )
      
      // ✅ NUOVO: Arricchisce i primi 5 nesting con dettagli aggiuntivi
      // Per evitare troppe chiamate API, carichiamo i dettagli solo per i primi elementi
      const enrichedNestings: EnrichedNestingData[] = []
      
      for (let i = 0; i < confirmed.length; i++) {
        if (i < 5) {
          // Carica dettagli per i primi 5 nesting
          const enriched = await enrichNestingData(confirmed[i])
          enrichedNestings.push(enriched)
        } else {
          // Per gli altri, usa solo i dati base
          enrichedNestings.push({
            ...confirmed[i],
            odl_count: confirmed[i].odl_inclusi || 0
          })
        }
      }
      
      setConfirmedNestings(enrichedNestings)
      
      // Chiama onRefresh se fornito
      if (onRefresh) {
        await onRefresh()
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare i layout confermati",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // ✅ NUOVO: Funzione per caricare dettagli on-demand
  const loadNestingDetails = async (nestingId: string) => {
    const currentNesting = confirmedNestings.find(n => n.id === nestingId)
    if (!currentNesting || currentNesting.dettagli) return // Già caricato
    
    try {
      const enriched = await enrichNestingData(currentNesting)
      setConfirmedNestings(prev => 
        prev.map(n => n.id === nestingId ? enriched : n)
      )
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile caricare i dettagli del nesting",
        variant: "destructive",
      })
    } finally {
      setLoadingDetails(prev => {
        const newSet = new Set(prev)
        newSet.delete(nestingId)
        return newSet
      })
    }
  }

  // Funzione per scaricare il report di un nesting
  const handleDownloadReport = async (nesting: EnrichedNestingData) => {
    const nestingId = parseInt(nesting.id)
    
    try {
      setDownloadingReports(prev => new Set(prev).add(nesting.id))
      
      // Prima genera il report se non esiste
      const reportInfo = await nestingApi.generateReport(nestingId)
      
      // Poi scarica il report
      const blob = await nestingApi.downloadReport(nestingId)
      
      // Crea un link per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = reportInfo.filename || `nesting_${nesting.id}_report.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      toast({
        title: "Report Scaricato",
        description: `Report del nesting ${nesting.id.substring(0, 8)}... scaricato con successo`,
      })
    } catch (error) {
      toast({
        title: "Errore Download",
        description: "Impossibile scaricare il report",
        variant: "destructive",
      })
    } finally {
      setDownloadingReports(prev => {
        const newSet = new Set(prev)
        newSet.delete(nesting.id)
        return newSet
      })
    }
  }

  // ✅ NUOVO: Funzione per formattare il peso
  const formatPeso = (peso?: number): string => {
    if (peso === undefined || peso === null) return 'Peso non disponibile'
    return `${peso.toFixed(1)} kg`
  }

  // ✅ NUOVO: Funzione per ottenere il nome dell'autoclave
  const getAutoclaveName = (nesting: EnrichedNestingData): string => {
    return nesting.autoclave_nome || 
           nesting.dettagli?.autoclave?.nome || 
           'Autoclave non assegnata'
  }

  // ✅ NUOVO: Funzione per ottenere il tool principale
  const getToolName = (nesting: EnrichedNestingData): string => {
    // Prima controlla se abbiamo dettagli caricati
    if (nesting.dettagli?.odl_inclusi && nesting.dettagli.odl_inclusi.length > 0) {
      const primoOdl = nesting.dettagli.odl_inclusi[0]
      return primoOdl.tool_nome || primoOdl.parte_codice || 'Tool non specificato'
    }
    
    // Poi controlla i dati base del nesting
    if (nesting.tool_principale) {
      return nesting.tool_principale
    }
    
    // Se non abbiamo dettagli, suggerisci di caricarli
    return 'Carica dettagli per vedere il tool'
  }

  // ✅ NUOVO: Funzione per ottenere il numero di ODL
  const getOdlCount = (nesting: EnrichedNestingData): string => {
    const count = nesting.odl_count || nesting.odl_inclusi || 0
    return count > 0 ? `${count} ODL` : 'Nessun ODL'
  }

  // ✅ NUOVO: Funzione per ottenere informazioni sul ciclo di cura
  const getCicloInfo = (nesting: EnrichedNestingData): string => {
    if (nesting.ciclo_cura) {
      return nesting.ciclo_cura
    }
    
    // Usa le proprietà disponibili dal dettaglio autoclave
    if (nesting.dettagli?.autoclave?.nome) {
      return `Autoclave ${nesting.dettagli.autoclave.nome}`
    }
    
    return 'Ciclo non assegnato'
  }

  // ✅ NUOVO: Funzione per ottenere informazioni sui piani utilizzati
  const getPlaneInfo = (nesting: EnrichedNestingData): string => {
    // Prova a ottenere info dalle statistiche del nesting
    if (nesting.valvole_utilizzate && nesting.valvole_totali) {
      return `${nesting.valvole_utilizzate}/${nesting.valvole_totali} valvole`
    }
    
    // Usa informazioni generiche se disponibili  
    if (nesting.dettagli?.autoclave) {
      return `Autoclave: ${nesting.dettagli.autoclave.nome}`
    }
    
    return 'Info piani non disponibili'
  }

  // ✅ NUOVO: Funzione per verificare se un nesting ha dati completi
  const hasCompleteData = (nesting: EnrichedNestingData): boolean => {
    return !!(nesting.dettagli || 
             (nesting.peso_totale && nesting.ciclo_cura && nesting.valvole_utilizzate))
  }

  // Carica i dati al primo render
  useEffect(() => {
    loadConfirmedNestings()
  }, [])

  // Statistiche sui layout confermati
  const stats = {
    total: confirmedNestings.length,
    sospeso: confirmedNestings.filter(n => n.stato.toLowerCase() === 'sospeso').length,
    cura: confirmedNestings.filter(n => ['cura', 'in_corso'].includes(n.stato.toLowerCase())).length,
    finito: confirmedNestings.filter(n => ['finito', 'completato'].includes(n.stato.toLowerCase())).length,
    confermato: confirmedNestings.filter(n => n.stato.toLowerCase() === 'confermato').length
  }

  // Funzione per ottenere l'icona dello stato
  const getStatusIcon = (stato: string) => {
    const statusLower = stato.toLowerCase()
    switch (statusLower) {
      case 'confermato':
        return <CheckCircle className="h-4 w-4 text-orange-600" />
      case 'sospeso':
        return <Clock className="h-4 w-4 text-yellow-600" />
      case 'cura':
      case 'in_corso':
        return <Play className="h-4 w-4 text-blue-600" />
      case 'finito':
      case 'completato':
        return <CheckSquare className="h-4 w-4 text-green-600" />
      default:
        return <Eye className="h-4 w-4 text-gray-600" />
    }
  }

  // Funzione per ottenere il colore del badge dello stato
  const getStatusBadgeVariant = (stato: string) => {
    const statusLower = stato.toLowerCase()
    switch (statusLower) {
      case 'confermato':
        return 'default'
      case 'sospeso':
        return 'secondary'
      case 'cura':
      case 'in_corso':
        return 'default'
      case 'finito':
      case 'completato':
        return 'default'
      default:
        return 'outline'
    }
  }

  return (
    <div className="space-y-6">
      {/* Statistiche */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Totale Confermati</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Confermati</p>
                <p className="text-2xl font-bold text-orange-600">{stats.confermato}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">In Sospeso</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.sospeso}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Play className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">In Cura</p>
                <p className="text-2xl font-bold text-blue-600">{stats.cura}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completati</p>
                <p className="text-2xl font-bold text-green-600">{stats.finito}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabella dei layout confermati con azioni */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Layout Confermati
              </CardTitle>
              <CardDescription>
                Visualizza e gestisci tutti i layout di nesting confermati. Scarica i report per i nesting completati.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={loadConfirmedNestings}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Aggiorna
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {confirmedNestings.length > 0 ? (
            <div className="space-y-4">
              {/* Lista dei nesting confermati */}
              <div className="grid gap-4">
                {confirmedNestings.map((nesting) => (
                  <Card key={nesting.id} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(nesting.stato)}
                            <div>
                              <h4 className="font-semibold">Nesting #{nesting.id.substring(0, 8)}...</h4>
                              <p className="text-sm text-muted-foreground flex items-center gap-1">
                                <Package className="h-3 w-3" />
                                {getAutoclaveName(nesting)}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant={getStatusBadgeVariant(nesting.stato)}>
                              {nesting.stato}
                            </Badge>
                            {/* ✅ NUOVO: Badge per efficienza se disponibile */}
                            {nesting.efficienza && (
                              <Badge variant="outline" className="text-xs">
                                {(nesting.efficienza * 100).toFixed(1)}% efficienza
                              </Badge>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {/* Pulsante Visualizza Dettagli */}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onViewDetails(parseInt(nesting.id))}
                            className="flex items-center gap-2"
                          >
                            <Eye className="h-4 w-4" />
                            Dettagli
                          </Button>

                          {/* ✅ NUOVO: Pulsante per caricare dettagli se non disponibili */}
                          {!nesting.dettagli && !loadingDetails.has(nesting.id) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => loadNestingDetails(nesting.id)}
                              className="flex items-center gap-2"
                            >
                              <RefreshCw className="h-4 w-4" />
                              Carica Info
                            </Button>
                          )}

                          {/* Pulsante Genera Report (solo per nesting completati) */}
                          {['finito', 'completato'].includes(nesting.stato.toLowerCase()) && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => handleDownloadReport(nesting)}
                              disabled={downloadingReports.has(nesting.id)}
                              className="flex items-center gap-2"
                            >
                              {downloadingReports.has(nesting.id) ? (
                                <RefreshCw className="h-4 w-4 animate-spin" />
                              ) : (
                                <Download className="h-4 w-4" />
                              )}
                              {downloadingReports.has(nesting.id) ? 'Generando...' : 'Genera Report'}
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* ✅ AGGIORNATO: Informazioni reali dal backend con fallback informativi */}
                      <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <FileText className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">ODL:</span>
                          <span className="ml-1 font-medium">{getOdlCount(nesting)}</span>
                          {loadingDetails.has(nesting.id) && (
                            <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Wrench className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">Tool:</span>
                          <span className={`ml-1 ${
                            getToolName(nesting).includes('Carica dettagli') 
                              ? 'text-blue-600 hover:underline cursor-pointer'
                              : 'font-medium'
                          }`}
                          onClick={() => {
                            if (getToolName(nesting).includes('Carica dettagli')) {
                              loadNestingDetails(nesting.id)
                            }
                          }}
                          >
                            {getToolName(nesting)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Package className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">Peso:</span>
                          <span className="ml-1 font-medium">{formatPeso(nesting.peso_totale)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">Data:</span>
                          <span className="ml-1 font-medium">
                            {new Date(nesting.created_at).toLocaleDateString('it-IT')}
                          </span>
                        </div>
                      </div>

                      {/* ✅ MIGLIORATO: Informazioni aggiuntive con fallback intelligenti */}
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <span>🔄 Ciclo:</span>
                            <span className="ml-1 font-medium text-foreground">
                              {getCicloInfo(nesting)}
                            </span>
                          </div>
                          
                          {(nesting.area_utilizzata || nesting.dettagli?.statistiche?.area_totale) && (
                            <div className="flex items-center gap-1">
                              <span>📐 Area:</span>
                              <span className="ml-1 font-medium text-foreground">
                                {nesting.area_utilizzata && nesting.statistiche?.area_totale 
                                  ? `${nesting.area_utilizzata.toFixed(0)}/${nesting.statistiche.area_totale.toFixed(0)} cm²`
                                  : `${nesting.dettagli?.statistiche?.area_totale?.toFixed(0) || '-'} cm²`}
                              </span>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-1">
                            <span>🏭 Piani:</span>
                            <span className="ml-1 font-medium text-foreground">
                              {getPlaneInfo(nesting)}
                            </span>
                          </div>
                        </div>
                        
                        {/* ✅ NUOVO: Indicatore stato caricamento dati */}
                        {!hasCompleteData(nesting) && !loadingDetails.has(nesting.id) && (
                          <div className="mt-2 text-xs text-blue-600 flex items-center gap-1">
                            <RefreshCw className="h-3 w-3" />
                            <span>Alcuni dettagli sono limitati - </span>
                            <button 
                              onClick={() => loadNestingDetails(nesting.id)}
                              className="underline hover:text-blue-800"
                            >
                              carica informazioni complete
                            </button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Nessun layout confermato</p>
              <p className="text-sm">I layout confermati appariranno qui dopo la conferma degli operatori.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Informazioni sui stati */}
      <Card>
        <CardHeader>
          <CardTitle>Legenda Stati</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <div>
                <p className="font-medium">Confermato</p>
                <p className="text-sm text-muted-foreground">Layout approvato, pronto per la produzione</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <div>
                <p className="font-medium">In Sospeso</p>
                <p className="text-sm text-muted-foreground">In attesa di essere caricato in autoclave</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <div>
                <p className="font-medium">In Cura</p>
                <p className="text-sm text-muted-foreground">Produzione attualmente in esecuzione</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div>
                <p className="font-medium">Completato</p>
                <p className="text-sm text-muted-foreground">Produzione terminata, report disponibile</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 