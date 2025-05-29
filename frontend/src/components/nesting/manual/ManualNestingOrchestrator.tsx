'use client'

import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, RotateCcw, CheckCircle } from 'lucide-react'
import { useToast } from "@/hooks/use-toast"

// Import dei componenti step
import { NestingStep1ODLSelection, ExtractedNestingData } from './NestingStep1ODLSelection'
import { NestingStep2AutoclaveSelection, AutoclaveSelectionData } from './NestingStep2AutoclaveSelection'
import { NestingStep3LayoutCanvas, LayoutCanvasData } from '../layout/NestingDragDropCanvas'
import { NestingStep4Validation, ValidationResults } from './NestingStep4Validation'
import { NestingStep5Confirmation, ConfirmationResults } from './NestingStep5Confirmation'

// Tipi per il progresso del workflow
interface WorkflowProgress {
  step1_odl_data?: ExtractedNestingData
  step2_autoclave_data?: AutoclaveSelectionData
  step3_layout_data?: LayoutCanvasData
  step4_validation_data?: ValidationResults
  step5_confirmation_data?: ConfirmationResults
  saved_positions?: any[]
  saved_nesting_id?: number
}

type WorkflowStep = 'step1' | 'step2' | 'step3' | 'step4' | 'step5' | 'completed'

interface ManualNestingOrchestratorProps {
  onComplete?: (results: ConfirmationResults) => void
  onCancel?: () => void
  className?: string
}

export function ManualNestingOrchestrator({ 
  onComplete,
  onCancel,
  className 
}: ManualNestingOrchestratorProps) {
  const { toast } = useToast()
  
  // State del workflow
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('step1')
  const [progress, setProgress] = useState<WorkflowProgress>({})
  const [isLoading, setIsLoading] = useState(false)

  // Calcola la percentuale di completamento
  const getStepProgress = () => {
    switch (currentStep) {
      case 'step1': return 0
      case 'step2': return 20
      case 'step3': return 40
      case 'step4': return 60
      case 'step5': return 80
      case 'completed': return 100
      default: return 0
    }
  }

  // Gestori completamento step
  const handleStep1Complete = useCallback((data: ExtractedNestingData) => {
    setProgress(prev => ({ ...prev, step1_odl_data: data }))
    setCurrentStep('step2')
    
    toast({
      title: "Step 1 completato",
      description: `${data.compatibilita_summary.total_odl} ODL selezionati con successo`
    })
  }, [toast])

  const handleStep2Complete = useCallback((data: AutoclaveSelectionData) => {
    setProgress(prev => ({ ...prev, step2_autoclave_data: data }))
    setCurrentStep('step3')
    
    toast({
      title: "Step 2 completato", 
      description: `Autoclave "${data.autoclave_data.nome}" selezionata`
    })
  }, [toast])

  const handleStep3Complete = useCallback((data: LayoutCanvasData) => {
    setProgress(prev => ({ 
      ...prev, 
      step3_layout_data: data,
      saved_positions: data.final_positions,
      saved_nesting_id: data.nesting_id
    }))
    setCurrentStep('step4')
    
    toast({
      title: "Step 3 completato",
      description: "Layout configurato con successo"
    })
  }, [toast])

  const handleStep4Complete = useCallback((data: ValidationResults) => {
    setProgress(prev => ({ ...prev, step4_validation_data: data }))
    setCurrentStep('step5')
    
    toast({
      title: "Step 4 completato",
      description: data.ready_for_confirmation ? 
        "Validazione superata" : "Validazione completata con avvisi"
    })
  }, [toast])

  const handleStep5Complete = useCallback((data: ConfirmationResults) => {
    setProgress(prev => ({ ...prev, step5_confirmation_data: data }))
    setCurrentStep('completed')
    
    toast({
      title: "Nesting completato! 🎉",
      description: `${data.odl_status_changed} ODL caricati in autoclave`
    })

    // Notifica il completamento al componente padre
    if (onComplete) {
      onComplete(data)
    }
  }, [toast, onComplete])

  // Gestori navigazione
  const handleBack = useCallback(() => {
    switch (currentStep) {
      case 'step2':
        setCurrentStep('step1')
        break
      case 'step3':
        setCurrentStep('step2')
        break
      case 'step4':
        setCurrentStep('step3')
        break
      case 'step5':
        setCurrentStep('step4')
        break
      default:
        break
    }
  }, [currentStep])

  const handleReset = useCallback(() => {
    setCurrentStep('step1')
    setProgress({})
    
    toast({
      title: "Workflow resettato",
      description: "Puoi ricominciare da capo"
    })
  }, [toast])

  // Render del contenuto dello step corrente
  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'step1':
        return (
          <NestingStep1ODLSelection
            onNext={handleStep1Complete}
            isLoading={isLoading}
            savedProgress={{
              selected_odl_ids: [],
              filters: {
                status_filter: 'all',
                priorita_filter: 'all',
                search_filter: ''
              }
            }}
          />
        )

      case 'step2':
        if (!progress.step1_odl_data) {
          return <div>Errore: Dati Step 1 mancanti</div>
        }
        return (
          <NestingStep2AutoclaveSelection
            odlData={progress.step1_odl_data}
            onNext={handleStep2Complete}
            onBack={handleBack}
            isLoading={isLoading}
            savedProgress={{
              selected_autoclave_id: undefined
            }}
          />
        )

      case 'step3':
        if (!progress.step1_odl_data || !progress.step2_autoclave_data) {
          return <div>Errore: Dati Step 1 o 2 mancanti</div>
        }
        return (
          <NestingStep3LayoutCanvas
            odlData={progress.step1_odl_data}
            autoclaveData={progress.step2_autoclave_data}
            onNext={handleStep3Complete}
            onBack={handleBack}
            isLoading={isLoading}
            savedProgress={{
              saved_positions: progress.saved_positions,
              saved_nesting_id: progress.saved_nesting_id
            }}
          />
        )

      case 'step4':
        if (!progress.step1_odl_data || !progress.step2_autoclave_data || !progress.step3_layout_data) {
          return <div>Errore: Dati Step precedenti mancanti</div>
        }
        return (
          <NestingStep4Validation
            odlData={progress.step1_odl_data}
            autoclaveData={progress.step2_autoclave_data}
            layoutData={progress.step3_layout_data}
            onNext={handleStep4Complete}
            onBack={handleBack}
            isLoading={isLoading}
          />
        )

      case 'step5':
        if (!progress.step1_odl_data || !progress.step2_autoclave_data || 
            !progress.step3_layout_data || !progress.step4_validation_data) {
          return <div>Errore: Dati Step precedenti mancanti</div>
        }
        return (
          <NestingStep5Confirmation
            odlData={progress.step1_odl_data}
            autoclaveData={progress.step2_autoclave_data}
            layoutData={progress.step3_layout_data}
            validationData={progress.step4_validation_data}
            onComplete={handleStep5Complete}
            onBack={handleBack}
          />
        )

      case 'completed':
        return (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-900 mb-2">
              Nesting Completato con Successo! 🎉
            </h2>
            <p className="text-gray-600 mb-6">
              Il nesting è stato confermato e caricato in autoclave.
            </p>
            
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                onClick={handleReset}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Nuovo Nesting
              </Button>
              
              {onCancel && (
                <Button onClick={onCancel}>
                  Torna alla Dashboard
                </Button>
              )}
            </div>
          </div>
        )

      default:
        return <div>Step non riconosciuto</div>
    }
  }

  const getStepTitle = () => {
    switch (currentStep) {
      case 'step1': return 'Step 1: Selezione ODL'
      case 'step2': return 'Step 2: Selezione Autoclave'
      case 'step3': return 'Step 3: Layout Canvas'
      case 'step4': return 'Step 4: Validazione Finale'
      case 'step5': return 'Step 5: Conferma e Caricamento'
      case 'completed': return 'Nesting Completato'
      default: return 'Nesting Manuale'
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header con progresso */}
      {currentStep !== 'completed' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{getStepTitle()}</CardTitle>
                <CardDescription>
                  Workflow guidato per nesting manuale
                </CardDescription>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-gray-600">Progresso</div>
                  <div className="text-2xl font-bold">{getStepProgress()}%</div>
                </div>
                <Progress value={getStepProgress()} className="w-32" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>Step corrente:</span>
              <span className="font-medium">{currentStep.replace('step', '')}/5</span>
              {currentStep !== 'step1' && (
                <>
                  <span>•</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBack}
                    className="h-6 px-2 text-xs"
                  >
                    <ArrowLeft className="h-3 w-3 mr-1" />
                    Indietro
                  </Button>
                </>
              )}
              <span>•</span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                className="h-6 px-2 text-xs"
              >
                <RotateCcw className="h-3 w-3 mr-1" />
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Contenuto step corrente */}
      <div className="min-h-[600px]">
        {renderCurrentStep()}
      </div>
    </div>
  )
} 