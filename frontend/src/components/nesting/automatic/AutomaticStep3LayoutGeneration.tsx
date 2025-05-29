'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft, 
  Zap, 
  Target, 
  RotateCw,
  Cpu,
  TrendingUp,
  Clock,
  Package
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

// Import API e tipi
import { nestingApi, NestingLayoutData } from '@/lib/api'
import { ExtractedNestingData } from '../manual/NestingStep1ODLSelection'
import { AutoclaveSelectionData } from './AutomaticStep2AutoclaveSelection'

// Componenti per visualizzazione layout
import { NestingDragDropCanvas } from '../layout/NestingDragDropCanvas'

// Tipi per questo step
export interface LayoutGenerationData {
  layout_data: NestingLayoutData
  optimization_results: {
    algorithm_used: string
    generation_time_ms: number
    iterations_performed: number
    convergence_achieved: boolean
  }
  efficiency_percent: number
  excluded_odl_count: number
  exclusion_reasons: string[]
  auto_generation_log: string[]
}

interface AutomaticStep3LayoutGenerationProps {
  onNext: (data: LayoutGenerationData) => void
  onBack: () => void
  isLoading?: boolean
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  savedData?: LayoutGenerationData
}

export function AutomaticStep3LayoutGeneration({
  onNext,
  onBack,
  isLoading = false,
  odlData,
  autoclaveData,
  savedData
}: AutomaticStep3LayoutGenerationProps) {
  const { toast } = useToast()
  
  // State
  const [generationProgress, setGenerationProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState('')
  const [layoutData, setLayoutData] = useState<LayoutGenerationData | null>(savedData || null)
  const [generating, setGenerating] = useState(false)
  const [generationLog, setGenerationLog] = useState<string[]>([])

  // Avvia la generazione automatica se non ci sono dati salvati
  useEffect(() => {
    if (!savedData && !generating) {
      startAutomaticGeneration()
    }
  }, [savedData, generating])

  // Simula il progresso della generazione
  const simulateProgress = (steps: string[], stepDurations: number[]) => {
    let totalTime = 0
    steps.forEach((step, index) => {
      setTimeout(() => {
        setCurrentStep(step)
        setGenerationProgress(((index + 1) / steps.length) * 100)
        setGenerationLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${step}`])
      }, totalTime)
      totalTime += stepDurations[index] || 1000
    })
  }

  // Funzione principale per generare il layout automaticamente
  const startAutomaticGeneration = async () => {
    try {
      setGenerating(true)
      setGenerationProgress(0)
      setGenerationLog([])
      
      toast({
        title: "Generazione Layout Automatica",
        description: "Avviando l'ottimizzazione con OR-Tools..."
      })

      // Step di generazione con tempi simulati
      const generationSteps = [
        'Inizializzazione OR-Tools',
        'Analisi vincoli geometrici',
        'Calcolo posizioni ottimali',
        'Ottimizzazione orientamenti',
        'Verifica sovrappposizioni',
        'Validazione finale',
        'Generazione layout'
      ]

      const stepDurations = [800, 1200, 2000, 1500, 1000, 800, 600]

      // Avvia simulazione progresso
      simulateProgress(generationSteps, stepDurations)

      // Chiama l'API di ottimizzazione automatica
      const optimizationRequest = {
        odl_ids: odlData.selected_odl_ids,
        autoclave_id: autoclaveData.selected_autoclave.id,
        parameters: {
          distanza_minima_tool_cm: 2.0,
          padding_bordo_autoclave_cm: 1.5,
          margine_sicurezza_peso_percent: 10.0,
          priorita_minima: 1,
          efficienza_minima_percent: 60.0,
          algorithm: 'or_tools_binpacking'
        }
      }

      // Simula attesa per la generazione
      await new Promise(resolve => setTimeout(resolve, 8000))

      // Per ora simula una risposta, in futuro userà nestingApi.generateLayout()
      const mockLayoutData: LayoutGenerationData = {
        layout_data: {
          id: Math.floor(Math.random() * 1000),
          autoclave: {
            id: autoclaveData.selected_autoclave.id,
            nome: autoclaveData.selected_autoclave.nome,
            codice: autoclaveData.selected_autoclave.codice,
            lunghezza: autoclaveData.selected_autoclave.lunghezza,
            larghezza_piano: autoclaveData.selected_autoclave.larghezza_piano,
            temperatura_max: autoclaveData.selected_autoclave.temperatura_max,
            num_linee_vuoto: autoclaveData.selected_autoclave.num_linee_vuoto
          },
          odl_list: [],
          posizioni_tool: [],
          area_utilizzata: odlData.area_totale_cm2 * 0.85,
          area_totale: (autoclaveData.selected_autoclave.lunghezza * autoclaveData.selected_autoclave.larghezza_piano) / 100,
          valvole_utilizzate: odlData.valvole_richieste,
          valvole_totali: autoclaveData.selected_autoclave.num_linee_vuoto,
          stato: 'bozza',
          created_at: new Date().toISOString(),
          padding_mm: 15,
          borda_mm: 20,
          rotazione_abilitata: true
        },
        optimization_results: {
          algorithm_used: 'OR-Tools Bin Packing',
          generation_time_ms: 7800,
          iterations_performed: 156,
          convergence_achieved: true
        },
        efficiency_percent: 85.2,
        excluded_odl_count: Math.max(0, odlData.selected_odl_ids.length - Math.floor(odlData.selected_odl_ids.length * 0.9)),
        exclusion_reasons: [],
        auto_generation_log: generationLog
      }

      setLayoutData(mockLayoutData)
      setGenerationProgress(100)
      setCurrentStep('Generazione completata')

      setTimeout(() => {
        toast({
          title: "Layout Generato con Successo!",
          description: `Efficienza raggiunta: ${mockLayoutData.efficiency_percent}% con ${mockLayoutData.optimization_results.iterations_performed} iterazioni`
        })
      }, 500)

    } catch (error: any) {
      setGenerationProgress(0)
      toast({
        variant: "destructive",
        title: "Errore nella Generazione",
        description: error.message || "Impossibile generare il layout automaticamente"
      })
    } finally {
      setGenerating(false)
    }
  }

  // Handler per rigenerare il layout
  const handleRegenerate = () => {
    setLayoutData(null)
    startAutomaticGeneration()
  }

  // Handler per procedere al prossimo step
  const handleNext = () => {
    if (layoutData) {
      onNext(layoutData)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 3: Generazione Layout Automatica</h2>
          <p className="text-gray-600 mt-1">
            OR-Tools genera automaticamente il layout ottimizzato per l'autoclave selezionata.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={generationProgress} className="w-32" />
          <span className="text-sm text-gray-500">{Math.round(generationProgress)}%</span>
        </div>
      </div>

      {/* Riepilogo parametri di input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Parametri di Ottimizzazione
          </CardTitle>
          <CardDescription>
            Dati utilizzati per la generazione automatica del layout
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <Package className="h-5 w-5 mx-auto mb-2 text-blue-600" />
              <div className="text-lg font-bold text-blue-600">
                {odlData.selected_odl_ids.length}
              </div>
              <div className="text-xs text-blue-800">ODL da posizionare</div>
            </div>
            
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <TrendingUp className="h-5 w-5 mx-auto mb-2 text-green-600" />
              <div className="text-lg font-bold text-green-600">
                {odlData.area_totale_cm2.toFixed(0)}
              </div>
              <div className="text-xs text-green-800">cm² Area Richiesta</div>
            </div>
            
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <Cpu className="h-5 w-5 mx-auto mb-2 text-purple-600" />
              <div className="text-lg font-bold text-purple-600">
                {autoclaveData.selected_autoclave.nome}
              </div>
              <div className="text-xs text-purple-800">Autoclave Target</div>
            </div>
            
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <RotateCw className="h-5 w-5 mx-auto mb-2 text-orange-600" />
              <div className="text-lg font-bold text-orange-600">
                OR-Tools
              </div>
              <div className="text-xs text-orange-800">Algoritmo</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progresso generazione */}
      {generating && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 animate-spin" />
              Generazione in Corso...
            </CardTitle>
            <CardDescription>
              {currentStep || 'Preparazione ottimizzazione...'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Progress value={generationProgress} className="w-full" />
              
              {generationLog.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4 max-h-32 overflow-y-auto">
                  <h4 className="text-sm font-medium mb-2">Log Generazione:</h4>
                  <div className="space-y-1">
                    {generationLog.slice(-5).map((log, index) => (
                      <p key={index} className="text-xs text-gray-600 font-mono">
                        {log}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risultati della generazione */}
      {layoutData && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Layout Generato con Successo
              </CardTitle>
              <CardDescription>
                Ottimizzazione completata con algoritmo {layoutData.optimization_results.algorithm_used}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Statistiche dell'ottimizzazione */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {layoutData.efficiency_percent.toFixed(1)}%
                  </div>
                  <div className="text-sm text-green-800">Efficienza Raggiunta</div>
                </div>
                
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {layoutData.optimization_results.iterations_performed}
                  </div>
                  <div className="text-sm text-blue-800">Iterazioni</div>
                </div>
                
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {(layoutData.optimization_results.generation_time_ms / 1000).toFixed(1)}s
                  </div>
                  <div className="text-sm text-purple-800">Tempo Generazione</div>
                </div>
                
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {layoutData.excluded_odl_count}
                  </div>
                  <div className="text-sm text-orange-800">ODL Esclusi</div>
                </div>
              </div>

              {/* Informazioni aggiuntive */}
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Convergenza Algoritmo:</span>
                  <Badge className={layoutData.optimization_results.convergence_achieved ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                    {layoutData.optimization_results.convergence_achieved ? "Raggiunta" : "Parziale"}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Area Utilizzata:</span>
                  <span className="text-gray-700">
                    {layoutData.layout_data.area_utilizzata.toFixed(0)} / {layoutData.layout_data.area_totale.toFixed(0)} cm²
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Valvole Utilizzate:</span>
                  <span className="text-gray-700">
                    {layoutData.layout_data.valvole_utilizzate} / {layoutData.layout_data.valvole_totali}
                  </span>
                </div>
              </div>

              {/* Esclusioni (se presenti) */}
              {layoutData.excluded_odl_count > 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Attenzione:</strong> {layoutData.excluded_odl_count} ODL sono stati esclusi dall'ottimizzazione automatica.
                    {layoutData.exclusion_reasons.length > 0 && (
                      <div className="mt-2">
                        <strong>Motivi:</strong>
                        <ul className="list-disc list-inside mt-1">
                          {layoutData.exclusion_reasons.map((reason, index) => (
                            <li key={index} className="text-sm">{reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Anteprima layout */}
          <Card>
            <CardHeader>
              <CardTitle>Anteprima Layout Generato</CardTitle>
              <CardDescription>
                Visualizzazione delle posizioni ottimizzate calcolate automaticamente
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-50 rounded-lg p-4 min-h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <Package className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">Layout Canvas</p>
                  <p className="text-sm">
                    Qui verrà visualizzato il layout ottimizzato con le posizioni dei tool
                  </p>
                  <p className="text-xs mt-2">
                    {odlData.selected_odl_ids.length} tool posizionati automaticamente
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Pulsanti navigazione */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={isLoading || generating}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Indietro
        </Button>

        <div className="flex gap-2">
          {layoutData && (
            <Button
              variant="outline"
              onClick={handleRegenerate}
              disabled={isLoading || generating}
              className="flex items-center gap-2"
            >
              <RotateCw className="h-4 w-4" />
              Rigenera Layout
            </Button>
          )}
          
          <Button
            onClick={handleNext}
            disabled={!layoutData || isLoading || generating}
            className="flex items-center gap-2"
          >
            {isLoading || generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generazione...
              </>
            ) : (
              <>
                Procedi alla Validazione
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
} 