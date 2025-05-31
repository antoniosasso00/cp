'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Zap, 
  Eye, 
  Settings, 
  CheckCircle, 
  Play, 
  RefreshCw, 
  AlertTriangle,
  Package,
  Factory,
  Gauge
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { NestingParameters } from '@/components/Nesting/NestingParametersPanel'
import { nestingApi, odlApi, autoclaveApi, NestingResponse } from '@/lib/api'
import { SimpleNestingCanvas } from '@/components/Nesting/SimpleNestingCanvas'

interface PreviewOptimizationTabProps {
  onRefresh: () => Promise<void>
  onViewDetails: (nestingId: number) => Promise<void>
  onNestingConfirmed: () => Promise<void>
  parameters?: NestingParameters
  currentStep?: string
}

interface AutomaticNestingResult {
  nesting_id: number
  nesting_data: NestingResponse
  statistics: {
    odl_processed: number
    odl_included: number
    odl_excluded: number
    efficiency: number
    area_used: number
    area_total: number
    weight_total: number
    valves_used: number
  }
  layout_data?: any
}

export function PreviewOptimizationTab({ 
  onRefresh, 
  onViewDetails, 
  onNestingConfirmed,
  parameters,
  currentStep 
}: PreviewOptimizationTabProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [generatedNesting, setGeneratedNesting] = useState<AutomaticNestingResult | null>(null)
  const [availableODL, setAvailableODL] = useState<any[]>([])
  const [availableAutoclaves, setAvailableAutoclaves] = useState<any[]>([])
  const [selectedAutoclave, setSelectedAutoclave] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const { toast } = useToast()

  // Carica dati iniziali
  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Carica ODL in attesa di cura
      const odlResponse = await odlApi.getAll()
      const waitingODL = odlResponse.filter(odl => odl.status === 'Attesa Cura')
      setAvailableODL(waitingODL)
      
      // Carica autoclavi disponibili
      const autoclaveResponse = await autoclaveApi.getAll()
      const availableAutoclaves = autoclaveResponse.filter(autoclave => 
        autoclave.stato === 'DISPONIBILE'
      )
      setAvailableAutoclaves(availableAutoclaves)
      
      // Seleziona automaticamente la prima autoclave se disponibile
      if (availableAutoclaves.length > 0) {
        setSelectedAutoclave(availableAutoclaves[0].id)
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore nel caricamento dati'
      setError(errorMessage)
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateAutomaticNesting = async () => {
    if (availableODL.length === 0) {
      toast({
        title: "Nessun ODL disponibile",
        description: "Non ci sono ODL in attesa di cura da processare",
        variant: "destructive",
      })
      return
    }

    try {
      setIsGenerating(true)
      setError(null)
      
      // Prepara i parametri per la richiesta con valori ottimizzati
      const requestParams = {
        force_regenerate: true,
        parameters: parameters || {
          distanza_minima_tool_cm: 1.0,
          padding_bordo_autoclave_cm: 1.0,
          margine_sicurezza_peso_percent: 5.0,
          priorita_minima: 1,
          efficienza_minima_percent: 30.0
        }
      }
      
      // Chiama l'API per il nesting automatico
      const response = await nestingApi.generateAutomatic(requestParams)
      
      if (response.success && response.nesting_results && response.nesting_results.length > 0) {
        // Trova il nesting per l'autoclave selezionata o prendi il primo
        const targetNesting = response.nesting_results.find(nr => 
          selectedAutoclave ? nr.autoclave_id === selectedAutoclave : true
        ) || response.nesting_results[0]
        
        // Se non era selezionata un'autoclave, seleziona quella del nesting generato
        if (!selectedAutoclave && targetNesting.autoclave_id) {
          setSelectedAutoclave(targetNesting.autoclave_id)
        }
        
        // Carica i dettagli del nesting generato
        const nestingDetails = await nestingApi.getDetails(targetNesting.id)
        
        const result: AutomaticNestingResult = {
          nesting_id: targetNesting.id,
          nesting_data: nestingDetails as any,
          statistics: {
            odl_processed: response.summary?.total_odl_processed || 0,
            odl_included: targetNesting.odl_inclusi || 0,
            odl_excluded: targetNesting.odl_esclusi || 0,
            efficiency: (targetNesting.efficienza || 0) / 100,
            area_used: targetNesting.area_utilizzata || 0,
            area_total: targetNesting.area_utilizzata || 0,
            weight_total: targetNesting.peso_totale || 0,
            valves_used: 0 // Da implementare se necessario
          },
          layout_data: nestingDetails
        }
        
        setGeneratedNesting(result)
        
        toast({
          title: "Nesting Automatico Generato! 🎉",
          description: `${result.statistics.odl_included} ODL inclusi con ${(result.statistics.efficiency * 100).toFixed(1)}% di efficienza`,
        })
        
      } else {
        const message = response.message || 'Nessun nesting generato con i parametri specificati'
        toast({
          title: "Nessun Nesting Generato",
          description: message,
          variant: "destructive",
        })
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore nella generazione'
      setError(errorMessage)
      toast({
        title: "Errore Generazione",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const handleConfirmNesting = async () => {
    if (!generatedNesting) {
      toast({
        title: "Nessun nesting da confermare",
        description: "Genera prima un nesting automatico",
        variant: "destructive",
      })
      return
    }

    try {
      // Conferma il nesting tramite API
      await nestingApi.confirm(generatedNesting.nesting_id, {
        confermato_da_ruolo: localStorage.getItem('user_role') || 'operatore',
        note_conferma: 'Nesting automatico confermato'
      })
      
      await onNestingConfirmed()
      
      toast({
        title: "Nesting Confermato! ✅",
        description: "Il nesting automatico è stato confermato e sarà disponibile per la produzione",
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore nella conferma'
      toast({
        title: "Errore Conferma",
        description: errorMessage,
        variant: "destructive",
      })
    }
  }

  const handleRegenerateNesting = async () => {
    if (generatedNesting) {
      // Elimina il nesting precedente se esiste
      try {
        await nestingApi.delete(generatedNesting.nesting_id)
      } catch (error) {
        // Ignora errori di eliminazione
      }
    }
    
    setGeneratedNesting(null)
    await handleGenerateAutomaticNesting()
  }

  // Render del contenuto specifico per ogni step
  const renderStepContent = () => {
    switch (currentStep) {
      case 'select-odl':
        return (
          <Alert>
            <Package className="h-4 w-4" />
            <AlertTitle>Step: Selezione ODL</AlertTitle>
            <AlertDescription>
              Tutti gli ODL in attesa di cura ({availableODL.length}) verranno processati automaticamente.
            </AlertDescription>
          </Alert>
        )
        
      case 'select-autoclave':
        return (
          <div className="space-y-4">
            <Alert>
              <Factory className="h-4 w-4" />
              <AlertTitle>Step: Selezione Autoclave</AlertTitle>
              <AlertDescription>
                Seleziona l'autoclave target per l'ottimizzazione automatica.
              </AlertDescription>
            </Alert>
            
            <div className="grid gap-3">
              {availableAutoclaves.map(autoclave => (
                <Card 
                  key={autoclave.id}
                  className={`cursor-pointer transition-all ${
                    selectedAutoclave === autoclave.id 
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedAutoclave(autoclave.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">{autoclave.nome}</div>
                        <div className="text-sm text-gray-500">
                          Area: {autoclave.area_piano?.toFixed(0) || '-'} cm² | 
                          Valvole: {autoclave.num_linee_vuoto}
                        </div>
                      </div>
                      <Badge variant="secondary">{autoclave.stato}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )
        
      case 'configure-parameters':
        return (
          <Alert>
            <Settings className="h-4 w-4" />
            <AlertTitle>Step: Parametri</AlertTitle>
            <AlertDescription>
              I parametri di ottimizzazione sono stati configurati e verranno applicati automaticamente.
            </AlertDescription>
          </Alert>
        )
        
      case 'generate-preview':
        return (
          <div className="space-y-4">
            <Alert>
              <Play className="h-4 w-4" />
              <AlertTitle>Step: Genera Preview</AlertTitle>
              <AlertDescription>
                Genera l'anteprima automatica del nesting usando l'algoritmo OR-Tools.
              </AlertDescription>
            </Alert>
            <Button
              onClick={handleGenerateAutomaticNesting}
              disabled={isGenerating || availableODL.length === 0}
              className="flex items-center gap-2"
            >
              <Zap className="h-4 w-4" />
              {isGenerating ? 'Generazione...' : 'Genera Automatico'}
            </Button>
          </div>
        )
        
      case 'review':
        return (
          <div className="space-y-4">
            <Alert>
              <Eye className="h-4 w-4" />
              <AlertTitle>Step: Revisione</AlertTitle>
              <AlertDescription>
                Esamina il risultato del nesting automatico e verifica che soddisfi i tuoi requisiti.
              </AlertDescription>
            </Alert>
            {generatedNesting && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button
                  onClick={() => onViewDetails(generatedNesting.nesting_id)}
                  variant="outline"
                  data-nesting-action="view"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  Visualizza Dettagli
                </Button>
                <Button
                  onClick={handleRegenerateNesting}
                  variant="outline"
                  disabled={isGenerating}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Rigenera
                </Button>
              </div>
            )}
          </div>
        )
        
      case 'confirm':
        return (
          <div className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Step: Conferma Finale</AlertTitle>
              <AlertDescription>
                Conferma il nesting automatico. Una volta confermato, sarà disponibile per la produzione.
              </AlertDescription>
            </Alert>
            <Button
              onClick={handleConfirmNesting}
              disabled={!generatedNesting}
              className="flex items-center gap-2"
              data-nesting-action="confirm"
            >
              <CheckCircle className="h-4 w-4" />
              Conferma Nesting Automatico
            </Button>
          </div>
        )
        
      default:
        return null
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Caricamento dati per nesting automatico...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Errori */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Errore</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Controlli principali per modalità non-step */}
      {!currentStep && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              onClick={handleGenerateAutomaticNesting}
              disabled={isGenerating || availableODL.length === 0}
              className="flex items-center gap-2"
            >
              <Zap className="h-4 w-4" />
              {isGenerating ? 'Generazione...' : 'Genera Automatico'}
            </Button>
            
            {generatedNesting && (
              <Button
                onClick={handleRegenerateNesting}
                variant="outline"
                disabled={isGenerating}
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Rigenera
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Contenuto del workflow step */}
      {currentStep && renderStepContent()}

      {/* Stato dei dati */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Package className="h-8 w-8 mx-auto mb-2 text-blue-600" />
            <div className="text-2xl font-bold">{availableODL.length}</div>
            <div className="text-sm text-muted-foreground">ODL in Attesa</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <Factory className="h-8 w-8 mx-auto mb-2 text-green-600" />
            <div className="text-2xl font-bold">{availableAutoclaves.length}</div>
            <div className="text-sm text-muted-foreground">Autoclavi Disponibili</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <Gauge className="h-8 w-8 mx-auto mb-2 text-purple-600" />
            <div className="text-2xl font-bold">
              {generatedNesting ? `${(generatedNesting.statistics.efficiency * 100).toFixed(1)}%` : '-'}
            </div>
            <div className="text-sm text-muted-foreground">Efficienza</div>
          </CardContent>
        </Card>
      </div>

      {/* Parametri di ottimizzazione */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Parametri di Ottimizzazione
          </CardTitle>
        </CardHeader>
        <CardContent>
          {parameters ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Distanza minima:</span>
                <div className="font-medium">{parameters.distanza_minima_tool_cm} cm</div>
              </div>
              <div>
                <span className="text-muted-foreground">Padding autoclave:</span>
                <div className="font-medium">{parameters.padding_bordo_autoclave_cm} cm</div>
              </div>
              <div>
                <span className="text-muted-foreground">Efficienza minima:</span>
                <div className="font-medium">{parameters.efficienza_minima_percent}%</div>
              </div>
              <div>
                <span className="text-muted-foreground">Priorità minima:</span>
                <div className="font-medium">{parameters.priorita_minima}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Margine peso:</span>
                <div className="font-medium">{parameters.margine_sicurezza_peso_percent}%</div>
              </div>
            </div>
          ) : (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Parametri non configurati - verranno usati i valori di default
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Risultati del nesting generato */}
      {generatedNesting && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Nesting Automatico Generato
            </CardTitle>
            <CardDescription>
              Risultati dell'ottimizzazione automatica
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Statistiche */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-lg font-bold text-blue-600">
                  {generatedNesting.statistics.odl_included}
                </div>
                <div className="text-xs text-blue-800">ODL Inclusi</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded">
                <div className="text-lg font-bold text-green-600">
                  {(generatedNesting.statistics.efficiency * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-green-800">Efficienza</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-lg font-bold text-purple-600">
                  {generatedNesting.statistics.area_used.toFixed(0)}
                </div>
                <div className="text-xs text-purple-800">cm² Utilizzati</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded">
                <div className="text-lg font-bold text-orange-600">
                  {generatedNesting.statistics.weight_total.toFixed(1)}
                </div>
                <div className="text-xs text-orange-800">kg Totali</div>
              </div>
            </div>

            {/* Canvas di preview */}
            <div className="border rounded-lg p-4">
              <h4 className="font-medium mb-3">Layout Generato</h4>
              <div className="bg-gray-50 rounded p-8">
                {generatedNesting.layout_data && (
                  <SimpleNestingCanvas 
                    data={{
                      autoclave: {
                        id: generatedNesting.layout_data.autoclave?.id || 0,
                        nome: generatedNesting.layout_data.autoclave?.nome || 'Autoclave',
                        lunghezza: generatedNesting.layout_data.autoclave?.lunghezza || 2000,
                        larghezza_piano: generatedNesting.layout_data.autoclave?.larghezza_piano || 1200,
                        max_load_kg: generatedNesting.layout_data.autoclave?.max_load_kg || 1000
                      },
                      odl_list: (generatedNesting.layout_data.odl_list || []).map((odl: any) => ({
                        id: odl.id,
                        numero_odl: odl.numero_odl || `ODL-${odl.id}`,
                        parte_nome: odl.parte?.part_number || 'N/A',
                        tool_nome: odl.tool?.part_number_tool || 'N/A',
                        peso_kg: odl.peso_kg || 0,
                        valvole_richieste: odl.parte?.num_valvole_richieste || 1
                      })),
                      posizioni_tool: generatedNesting.layout_data.posizioni_tool || [],
                      statistiche: {
                        efficienza_piano_1: (generatedNesting.statistics.efficiency * 100) || 0,
                        efficienza_piano_2: 0,
                        peso_totale_kg: generatedNesting.statistics.weight_total,
                        area_utilizzata_cm2: generatedNesting.statistics.area_used,
                        area_totale_cm2: generatedNesting.statistics.area_total || generatedNesting.statistics.area_used
                      }
                    }}
                    height={650}
                    showControls={true}
                  />
                )}
                {!generatedNesting.layout_data && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Caricamento layout in corso...</p>
                  </div>
                )}
              </div>
            </div>

            {/* Azioni */}
            {!currentStep && (
              <div className="flex gap-2">
                <Button
                  onClick={() => onViewDetails(generatedNesting.nesting_id)}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Eye className="h-4 w-4" />
                  Visualizza Dettagli
                </Button>
                <Button
                  onClick={handleConfirmNesting}
                  className="flex items-center gap-2"
                  data-nesting-action="confirm"
                >
                  <CheckCircle className="h-4 w-4" />
                  Conferma Nesting
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Progresso generazione */}
      {isGenerating && (
        <Card>
          <CardContent className="p-6">
            <div className="text-center space-y-4">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600" />
              <div>
                <h3 className="font-semibold">Generazione Nesting Automatico</h3>
                <p className="text-sm text-muted-foreground">
                  L'algoritmo OR-Tools sta ottimizzando il layout...
                </p>
              </div>
              <Progress value={undefined} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 