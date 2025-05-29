'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Layers, CheckCircle, Settings, Database, Play, Eye } from 'lucide-react'
import { MultiBatchNesting } from '@/components/nesting/MultiBatchNesting'
import { useToast } from '@/hooks/use-toast'

interface MultiAutoclaveTabProps {
  currentStep?: string
  onStepComplete?: (stepData?: any) => void
  onStepError?: (error: string) => void
}

export function MultiAutoclaveTab({ 
  currentStep, 
  onStepComplete, 
  onStepError 
}: MultiAutoclaveTabProps) {
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const { toast } = useToast()

  // Funzione per completare uno step manualmente
  const handleCompleteStep = (stepData?: any) => {
    if (onStepComplete) {
      onStepComplete(stepData)
    }
  }

  // Funzione per gestire errori negli step
  const handleStepError = (errorMessage: string) => {
    setError(errorMessage)
    if (onStepError) {
      onStepError(errorMessage)
    }
  }

  // Simulazione processo per i vari step
  const handleProcessStep = async (stepName: string, stepData: any) => {
    try {
      setIsProcessing(true)
      setError(null)
      
      // Simula un processo asincrono
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      toast({
        title: `Step Completato`,
        description: `${stepName} completato con successo.`,
      })
      
      handleCompleteStep(stepData)
    } catch (error) {
      const errorMessage = `Errore durante ${stepName}`
      handleStepError(errorMessage)
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsProcessing(false)
    }
  }

  // Render del contenuto specifico per ogni step
  const renderStepContent = () => {
    switch (currentStep) {
      case 'select-autoclaves':
        return (
          <div className="space-y-4">
            <Alert>
              <Layers className="h-4 w-4" />
              <AlertTitle>Step 1: Selezione Autoclavi</AlertTitle>
              <AlertDescription>
                Seleziona le autoclavi disponibili per il batch multi-autoclave.
              </AlertDescription>
            </Alert>
            <Button
              onClick={() => handleProcessStep('selezione autoclavi', { autoclaves: ['A1', 'A2', 'A3'] })}
              disabled={isProcessing}
              className="flex items-center gap-2"
              data-nesting-action="confirm"
            >
              <Layers className="h-4 w-4" />
              {isProcessing ? 'Selezione in corso...' : 'Seleziona Autoclavi Disponibili'}
            </Button>
          </div>
        )
        
      case 'select-odl-batch':
        return (
          <div className="space-y-4">
            <Alert>
              <Database className="h-4 w-4" />
              <AlertTitle>Step 2: Selezione Batch ODL</AlertTitle>
              <AlertDescription>
                Scegli il gruppo di ODL da distribuire tra le autoclavi selezionate.
              </AlertDescription>
            </Alert>
            <Button
              onClick={() => handleProcessStep('selezione batch ODL', { odlCount: 15, priority: 'high' })}
              disabled={isProcessing}
              className="flex items-center gap-2"
              data-nesting-action="confirm"
            >
              <Database className="h-4 w-4" />
              {isProcessing ? 'Analisi ODL...' : 'Seleziona Batch ODL'}
            </Button>
          </div>
        )
        
      case 'configure-distribution':
        return (
          <div className="space-y-4">
            <Alert>
              <Settings className="h-4 w-4" />
              <AlertTitle>Step 3: Configurazione Distribuzione</AlertTitle>
              <AlertDescription>
                Configura la logica di distribuzione dei tool tra le autoclavi (step opzionale).
              </AlertDescription>
            </Alert>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={() => handleProcessStep('configurazione distribuzione', { strategy: 'balanced' })}
                disabled={isProcessing}
                variant="outline"
                data-nesting-action="confirm"
              >
                <Settings className="h-4 w-4 mr-2" />
                Distribuzione Bilanciata
              </Button>
              <Button
                onClick={() => handleCompleteStep({ strategy: 'default' })}
                variant="outline"
              >
                Usa Impostazioni Default
              </Button>
            </div>
          </div>
        )
        
      case 'generate-batch':
        return (
          <div className="space-y-4">
            <Alert>
              <Play className="h-4 w-4" />
              <AlertTitle>Step 4: Generazione Batch</AlertTitle>
              <AlertDescription>
                Genera tutti i nesting per il batch multi-autoclave utilizzando gli algoritmi di ottimizzazione.
              </AlertDescription>
            </Alert>
            <Button
              onClick={() => handleProcessStep('generazione batch', { batchId: 'BATCH_001', nestingCount: 3 })}
              disabled={isProcessing}
              className="flex items-center gap-2"
              data-nesting-action="confirm"
            >
              <Play className="h-4 w-4" />
              {isProcessing ? 'Generazione in corso...' : 'Genera Batch Multi-Autoclave'}
            </Button>
          </div>
        )
        
      case 'review-batch':
        return (
          <div className="space-y-4">
            <Alert>
              <Eye className="h-4 w-4" />
              <AlertTitle>Step 5: Revisione Batch</AlertTitle>
              <AlertDescription>
                Esamina tutti i nesting generati e verifica la distribuzione tra le autoclavi.
              </AlertDescription>
            </Alert>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={() => handleProcessStep('revisione batch', { reviewed: true })}
                disabled={isProcessing}
                variant="outline"
                data-nesting-action="view"
              >
                <Eye className="h-4 w-4 mr-2" />
                Visualizza Tutti i Nesting
              </Button>
              <Button
                onClick={() => handleCompleteStep({ approved: true })}
                variant="outline"
                data-nesting-action="confirm"
              >
                Approva Batch
              </Button>
            </div>
          </div>
        )
        
      case 'confirm-batch':
        return (
          <div className="space-y-4">
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Step 6: Conferma Batch</AlertTitle>
              <AlertDescription>
                Conferma l'intero batch multi-autoclave. Tutti i nesting saranno attivati per la produzione.
              </AlertDescription>
            </Alert>
            <Button
              onClick={() => handleProcessStep('conferma batch', { confirmed: true, batchId: 'BATCH_001' })}
              disabled={isProcessing}
              className="flex items-center gap-2"
              data-nesting-action="confirm"
            >
              <CheckCircle className="h-4 w-4" />
              {isProcessing ? 'Conferma in corso...' : 'Conferma Batch Completo'}
            </Button>
          </div>
        )
        
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Multi-Autoclave {currentStep && `- ${currentStep}`}
        </CardTitle>
        <CardDescription>
          {currentStep 
            ? 'Segui il workflow guidato per completare il nesting multi-autoclave.'
            : 'Gestisci nesting complessi che utilizzano multiple autoclavi simultaneamente.'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Contenuto del workflow step */}
          {currentStep && renderStepContent()}
          
          {/* Errori */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>
                Errore nel sistema multi-autoclave: {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Informazioni sui vantaggi (solo se non in modalità workflow) */}
          {!currentStep && (
            <>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-900 mb-2">🚀 Vantaggi Multi-Autoclave</h4>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• <strong>Maggiore throughput:</strong> Utilizza più autoclavi contemporaneamente</li>
                  <li>• <strong>Ottimizzazione globale:</strong> Distribuzione intelligente dei carichi</li>
                  <li>• <strong>Riduzione tempi:</strong> Parallelizzazione dei processi di curing</li>
                  <li>• <strong>Flessibilità:</strong> Adattamento automatico alle autoclavi disponibili</li>
                </ul>
              </div>

              {/* Componente Multi-Batch */}
              <MultiBatchNesting />

              {/* Note operative */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📋 Note Operative</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Verifica che tutte le autoclavi selezionate siano disponibili</li>
                  <li>• Controlla i parametri di temperatura e pressione per ogni autoclave</li>
                  <li>• Assicurati che i tool siano compatibili con le autoclavi assegnate</li>
                  <li>• Monitora i tempi di ciclo per sincronizzare le operazioni</li>
                </ul>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
} 