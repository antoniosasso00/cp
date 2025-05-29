'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Zap, Eye, Settings, Table, Package, AlertTriangle, RefreshCw } from 'lucide-react'
import { NestingPreview } from '@/components/nesting/NestingPreview'
import { NestingCanvas } from '@/components/nesting/NestingCanvas'
import { NestingSelector } from '@/components/nesting/NestingSelector'
import { AutomaticNestingResults } from '@/components/nesting/AutomaticNestingResults'
import { EmptyState } from '@/components/ui/EmptyState'
import { 
  nestingApi, 
  AutomaticNestingResponse,
  AutomaticNestingRequest,
  ODLLayoutInfo,
  NestingResult
} from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { useNestingParameters } from '@/hooks/useNestingParameters'
import { NestingParameters } from '@/components/nesting/NestingParametersPanel'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface PreviewOptimizationTabProps {
  onRefresh: () => Promise<void>
  onViewDetails: (nestingId: number) => Promise<void>
  onNestingConfirmed: () => Promise<void>
  parameters?: NestingParameters
}

export function PreviewOptimizationTab({ 
  onRefresh, 
  onViewDetails, 
  onNestingConfirmed,
  parameters 
}: PreviewOptimizationTabProps) {
  const [isGeneratingAutomatic, setIsGeneratingAutomatic] = useState(false)
  const [automaticResults, setAutomaticResults] = useState<AutomaticNestingResponse | null>(null)
  const [showPreview, setShowPreview] = useState(true)
  const [viewMode, setViewMode] = useState<'table' | 'canvas'>('table')
  const [selectedNestingId, setSelectedNestingId] = useState<number | null>(null)
  const [availableNestings, setAvailableNestings] = useState<Array<{id: number, title: string}>>([])
  const [isLoadingNestings, setIsLoadingNestings] = useState(false)
  const [nestingError, setNestingError] = useState<string | null>(null)
  
  // Opzioni per il nesting automatico
  const [automaticOptions, setAutomaticOptions] = useState<AutomaticNestingRequest>({
    force_regenerate: false,
    max_autoclaves: undefined,
    priority_threshold: undefined
  })

  const { toast } = useToast()
  const { generatePreviewWithParameters, generateAutomaticNesting } = useNestingParameters()

  // Carica la lista dei nesting disponibili
  const loadAvailableNestings = async () => {
    setIsLoadingNestings(true)
    setNestingError(null)
    try {
      const response = await nestingApi.getList({ per_page: 100 })
      if (response.success) {
        // Gestisce correttamente sia lista vuota che lista con elementi
        const nestingList = (response.nesting_list || []).map((n: NestingResult) => ({
          id: n.id,
          title: `${n.autoclave?.nome || `Nesting #${n.id}`} - ${n.stato}`
        }))
        setAvailableNestings(nestingList)
        
        // Se la lista è vuota, non considerarlo un errore ma un stato normale
        if (nestingList.length === 0) {
          console.log('ℹ️ Nessun nesting disponibile al momento')
        }
      } else {
        // Solo se la response non è successful, allora è un errore
        throw new Error(response.message || 'Errore nel caricamento dei nesting')
      }
    } catch (error) {
      console.error('❌ Errore nel caricamento nesting:', error)
      setNestingError(error instanceof Error ? error.message : 'Errore sconosciuto')
      toast({
        title: "Errore",
        description: "Impossibile caricare i nesting disponibili. Verifica la connessione al backend.",
        variant: "destructive",
      })
    } finally {
      setIsLoadingNestings(false)
    }
  }

  useEffect(() => {
    loadAvailableNestings()
  }, [])

  // Funzione per generare nesting automatico con parametri
  const handleGenerateAutomatic = async () => {
    if (!parameters) {
      toast({
        title: "Parametri mancanti",
        description: "È necessario configurare i parametri prima di avviare l'ottimizzazione",
        variant: "destructive",
      })
      return
    }

    try {
      setIsGeneratingAutomatic(true)
      setAutomaticResults(null)
      
      // Usa l'hook per generare il nesting con i parametri
      const result = await generateAutomaticNesting(parameters, automaticOptions.force_regenerate)
      
      if (result) {
        setAutomaticResults(result)
        toast({
          title: "Nesting Automatico Generato",
          description: `Generato con successo: ${result.nesting_results?.length || 0} nesting`,
        })
        setShowPreview(false)
        await onRefresh()
        await loadAvailableNestings() // Ricarica la lista
      }
    } catch (error) {
      toast({
        title: "Errore Generazione",
        description: "Impossibile generare il nesting automatico",
        variant: "destructive",
      })
    } finally {
      setIsGeneratingAutomatic(false)
    }
  }

  // Genera preview con parametri personalizzati
  const handleGeneratePreview = async () => {
    if (!parameters) {
      toast({
        title: "Parametri mancanti",
        description: "È necessario configurare i parametri prima di generare la preview",
        variant: "destructive",
      })
      return
    }

    try {
      const previewResult = await generatePreviewWithParameters(parameters)
      if (previewResult) {
        toast({
          title: "Preview generata",
          description: `Preview generata con ${previewResult.total_odl_pending} ODL in attesa`,
        })
        await onRefresh()
      }
    } catch (error) {
      toast({
        title: "Errore Preview",
        description: "Impossibile generare la preview",
        variant: "destructive",
      })
    }
  }

  // Gestisce il click su un tool nel canvas
  const handleToolClick = (odl: ODLLayoutInfo) => {
    // Mostra un toast con le informazioni del tool selezionato
  }

  return (
    <div className="space-y-6">
      {/* Controlli per passare tra Preview e Risultati */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant={showPreview ? "default" : "outline"}
            onClick={() => setShowPreview(true)}
            className="flex items-center gap-2"
          >
            <Eye className="h-4 w-4" />
            Preview
          </Button>
          <Button
            variant={!showPreview ? "default" : "outline"}
            onClick={() => setShowPreview(false)}
            className="flex items-center gap-2"
            disabled={!automaticResults}
          >
            <Zap className="h-4 w-4" />
            Risultati Ottimizzazione
          </Button>
        </div>

        {/* Toggle modalità visualizzazione (solo in preview) */}
        {showPreview && (
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === 'table' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode('table')}
              className="flex items-center gap-2"
            >
              <Table className="h-4 w-4" />
              Tabella
            </Button>
            <Button
              variant={viewMode === 'canvas' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode('canvas')}
              className="flex items-center gap-2"
            >
              <Package className="h-4 w-4" />
              Canvas
            </Button>
          </div>
        )}
      </div>

      {showPreview ? (
        <div className="space-y-6">
          {/* Sezione Preview */}
          {viewMode === 'table' ? (
            <div className="space-y-4">
              {/* Preview con parametri personalizzati */}
              {parameters && (
                <Card>
                  <CardHeader>
                    <CardTitle>Preview con Parametri Personalizzati</CardTitle>
                    <CardDescription>
                      Genera una preview utilizzando i parametri configurati nella tab Parametri
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={handleGeneratePreview}
                      className="flex items-center gap-2"
                      variant="outline"
                    >
                      <Eye className="h-4 w-4" />
                      Genera Preview con Parametri
                    </Button>
                  </CardContent>
                </Card>
              )}
              
              <NestingPreview onRefresh={onRefresh} />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Selezione nesting per canvas */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Visualizzazione Canvas
                  </CardTitle>
                  <CardDescription>
                    Seleziona un nesting per visualizzarlo nel canvas interattivo
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Gestione errori di caricamento */}
                  {nestingError && (
                    <Alert variant="destructive" className="mb-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        {nestingError}
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {/* Stato di caricamento */}
                  {isLoadingNestings ? (
                    <EmptyState
                      message="Caricamento nesting disponibili..."
                      description="Sto cercando i nesting disponibili per la visualizzazione"
                      icon="⏳"
                      size="sm"
                    />
                  ) : availableNestings.length === 0 ? (
                    <div className="space-y-4">
                      <EmptyState
                        message="Nessun nesting disponibile"
                        description="Non sono stati trovati nesting da visualizzare. Crea prima un nesting nella tab Preview o genera un'ottimizzazione automatica."
                        icon="📋"
                        size="sm"
                      />
                      <div className="flex gap-2">
                        <Button
                          onClick={loadAvailableNestings}
                          variant="outline"
                          size="sm"
                          className="flex items-center gap-2"
                        >
                          <RefreshCw className="h-4 w-4" />
                          Ricarica
                        </Button>
                        {parameters && (
                          <Button
                            onClick={handleGeneratePreview}
                            variant="outline"
                            size="sm"
                            className="flex items-center gap-2"
                          >
                            <Eye className="h-4 w-4" />
                            Genera Preview
                          </Button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <NestingSelector
                        onNestingSelected={setSelectedNestingId}
                        selectedNestingId={selectedNestingId}
                      />
                      
                      {selectedNestingId && (
                        <div className="space-y-4">
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              onClick={() => setSelectedNestingId(null)}
                              className="flex items-center gap-2"
                            >
                              <Package className="h-4 w-4" />
                              Cambia Nesting
                            </Button>
                            <span className="text-sm text-muted-foreground">
                              Visualizzando Nesting #{selectedNestingId}
                            </span>
                          </div>

                          <Card>
                            <CardContent className="p-0">
                              <NestingCanvas
                                nestingId={selectedNestingId}
                                onToolClick={handleToolClick}
                                showControls={true}
                                height={700}
                              />
                            </CardContent>
                          </Card>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* Sezione Ottimizzazione Automatica */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Ottimizzazione Automatica
              </CardTitle>
              <CardDescription>
                Genera automaticamente il nesting ottimale per tutti gli ODL in attesa utilizzando l'algoritmo di ottimizzazione e i parametri configurati.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Verifica parametri */}
              {!parameters && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Configura i parametri nella tab "Parametri" prima di avviare l'ottimizzazione automatica.
                  </AlertDescription>
                </Alert>
              )}

              {/* Opzioni di configurazione */}
              <div className="space-y-4">
                <h4 className="font-medium">Opzioni di Generazione</h4>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="force-regenerate"
                    checked={automaticOptions.force_regenerate}
                    onCheckedChange={(checked) => 
                      setAutomaticOptions(prev => ({ ...prev, force_regenerate: checked }))
                    }
                  />
                  <Label htmlFor="force-regenerate">
                    Forza rigenerazione (sovrascrive nesting in bozza esistenti)
                  </Label>
                </div>
              </div>

              {/* Pulsanti di azione */}
              <div className="flex gap-4">
                <Button
                  onClick={async () => {
                    await handleGenerateAutomatic()
                    if (viewMode === 'canvas' && automaticResults?.nesting_results && automaticResults.nesting_results.length > 0) {
                      setSelectedNestingId(automaticResults.nesting_results[0].id)
                    }
                  }}
                  disabled={isGeneratingAutomatic || !parameters}
                  className="flex items-center gap-2"
                  size="lg"
                >
                  <Zap className="h-5 w-5" />
                  {isGeneratingAutomatic ? 'Ottimizzazione in corso...' : 'Avvia Ottimizzazione'}
                </Button>

                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="lg">
                      <Settings className="h-4 w-4 mr-2" />
                      Opzioni Avanzate
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Opzioni Avanzate Ottimizzazione</DialogTitle>
                      <DialogDescription>
                        Configura parametri avanzati per l'algoritmo di ottimizzazione
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="max-autoclaves">Numero massimo autoclavi da utilizzare</Label>
                        <input
                          id="max-autoclaves"
                          type="number"
                          min="1"
                          max="10"
                          value={automaticOptions.max_autoclaves || ''}
                          onChange={(e) => setAutomaticOptions(prev => ({
                            ...prev,
                            max_autoclaves: e.target.value ? parseInt(e.target.value) : undefined
                          }))}
                          className="w-full mt-1 px-3 py-2 border rounded-md"
                          placeholder="Lascia vuoto per nessun limite"
                        />
                      </div>
                      <div>
                        <Label htmlFor="priority-threshold">Soglia minima priorità ODL</Label>
                        <input
                          id="priority-threshold"
                          type="number"
                          min="1"
                          max="10"
                          value={automaticOptions.priority_threshold || ''}
                          onChange={(e) => setAutomaticOptions(prev => ({
                            ...prev,
                            priority_threshold: e.target.value ? parseInt(e.target.value) : undefined
                          }))}
                          className="w-full mt-1 px-3 py-2 border rounded-md"
                          placeholder="Lascia vuoto per includere tutti"
                        />
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Sezione Risultati */
        automaticResults ? (
          <AutomaticNestingResults 
            results={automaticResults}
            onViewDetails={(nestingId) => {
              if (viewMode === 'canvas') {
                setSelectedNestingId(nestingId)
                setShowPreview(true)
              } else {
                onViewDetails(nestingId)
              }
            }}
            onNestingConfirmed={onNestingConfirmed}
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Risultati Ottimizzazione</CardTitle>
              <CardDescription>
                I risultati dell'ultima ottimizzazione automatica appariranno qui
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Nessun risultato disponibile</p>
                <p className="text-sm">Avvia un'ottimizzazione automatica per vedere i risultati</p>
              </div>
            </CardContent>
          </Card>
        )
      )}
    </div>
  )
} 