'use client'

import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, CheckCircle, ArrowLeft, ArrowRight } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

// Import dei componenti step riutilizzabili
import { NestingStep1ODLSelection, ExtractedNestingData } from '../manual/NestingStep1ODLSelection'
import { AutomaticStep2AutoclaveSelection, AutoclaveSelectionData } from './AutomaticStep2AutoclaveSelection'
import { AutomaticStep3LayoutGeneration, LayoutGenerationData } from './AutomaticStep3LayoutGeneration'
import { AutomaticStep4Validation, ValidationResults } from './AutomaticStep4Validation'
import { AutomaticStep5Confirmation, ConfirmationResults } from './AutomaticStep5Confirmation'

// Tipi per il workflow
interface AutomaticNestingProgress {
  step1_odl_data?: ExtractedNestingData
  step2_autoclave_data?: AutoclaveSelectionData
  step3_layout_data?: LayoutGenerationData
  step4_validation_data?: ValidationResults
  step5_confirmation_data?: ConfirmationResults
}

interface AutomaticNestingOrchestratorProps {
  onComplete: (data: ConfirmationResults) => void
  onCancel: () => void
  className?: string
  initialData?: AutomaticNestingProgress
}

export function AutomaticNestingOrchestrator({
  onComplete,
  onCancel,
  className,
  initialData
}: AutomaticNestingOrchestratorProps) {
  const { toast } = useToast()
  
  // State del workflow
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<string[]>([])
  const [progress, setProgress] = useState<AutomaticNestingProgress>(initialData || {})

  // Configurazione degli step
  const steps = [
    { 
      id: 1, 
      title: 'Selezione ODL', 
      description: 'Seleziona gli ODL da processare automaticamente',
      isCompleted: !!progress.step1_odl_data
    },
    { 
      id: 2, 
      title: 'Selezione Autoclave', 
      description: 'Il sistema seleziona automaticamente l\'autoclave più adatta',
      isCompleted: !!progress.step2_autoclave_data
    },
    { 
      id: 3, 
      title: 'Generazione Layout', 
      description: 'Generazione automatica del layout ottimizzato',
      isCompleted: !!progress.step3_layout_data
    },
    { 
      id: 4, 
      title: 'Validazione', 
      description: 'Verifica automatica del layout generato',
      isCompleted: !!progress.step4_validation_data
    },
    { 
      id: 5, 
      title: 'Conferma', 
      description: 'Conferma finale e salvataggio del nesting',
      isCompleted: !!progress.step5_confirmation_data
    }
  ]

  // Calcola la percentuale di completamento
  const completionPercentage = (steps.filter(s => s.isCompleted).length / steps.length) * 100

  // Gestione errori
  const addError = useCallback((error: string) => {
    setErrors(prev => [...prev, error])
    toast({
      title: "Errore nel Workflow",
      description: error,
      variant: "destructive"
    })
  }, [toast])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  // Handler per il completamento dello Step 1
  const handleStep1Complete = useCallback(async (data: ExtractedNestingData) => {
    try {
      setIsLoading(true)
      clearErrors()

      // Validazione dati ODL
      if (!data.selected_odl_ids.length) {
        throw new Error("Nessun ODL selezionato")
      }

      setProgress(prev => ({ ...prev, step1_odl_data: data }))
      setCurrentStep(2)

      toast({
        title: "Step 1 Completato",
        description: `${data.selected_odl_ids.length} ODL selezionati per l'ottimizzazione automatica`
      })
    } catch (error: any) {
      addError(error.message || "Errore nello step di selezione ODL")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast])

  // Handler per il completamento dello Step 2
  const handleStep2Complete = useCallback(async (data: AutoclaveSelectionData) => {
    try {
      setIsLoading(true)
      clearErrors()

      setProgress(prev => ({ ...prev, step2_autoclave_data: data }))
      setCurrentStep(3)

      toast({
        title: "Step 2 Completato",
        description: `Autoclave ${data.selected_autoclave.nome} selezionata automaticamente`
      })
    } catch (error: any) {
      addError(error.message || "Errore nella selezione automatica dell'autoclave")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast])

  // Handler per il completamento dello Step 3
  const handleStep3Complete = useCallback(async (data: LayoutGenerationData) => {
    try {
      setIsLoading(true)
      clearErrors()

      setProgress(prev => ({ ...prev, step3_layout_data: data }))
      setCurrentStep(4)

      toast({
        title: "Step 3 Completato",
        description: `Layout automatico generato con efficienza ${data.efficiency_percent?.toFixed(1)}%`
      })
    } catch (error: any) {
      addError(error.message || "Errore nella generazione automatica del layout")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast])

  // Handler per il completamento dello Step 4
  const handleStep4Complete = useCallback(async (data: ValidationResults) => {
    try {
      setIsLoading(true)
      clearErrors()

      setProgress(prev => ({ ...prev, step4_validation_data: data }))
      setCurrentStep(5)

      toast({
        title: "Step 4 Completato",
        description: data.is_valid ? "Validazione superata con successo" : "Validazione completata con avvisi"
      })
    } catch (error: any) {
      addError(error.message || "Errore nella validazione automatica")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast])

  // Handler per il completamento finale
  const handleStep5Complete = useCallback(async (data: ConfirmationResults) => {
    try {
      setIsLoading(true)
      clearErrors()

      setProgress(prev => ({ ...prev, step5_confirmation_data: data }))
      
      toast({
        title: "Nesting Automatico Completato!",
        description: "Il nesting è stato generato e confermato automaticamente"
      })

      // Chiama il callback di completamento
      onComplete(data)
    } catch (error: any) {
      addError(error.message || "Errore nella conferma finale")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast, onComplete])

  // Navigation handlers
  const goToPreviousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
      clearErrors()
    }
  }, [currentStep, clearErrors])

  const goToNextStep = useCallback(() => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1)
      clearErrors()
    }
  }, [currentStep, clearErrors])

  // Render del contenuto dello step corrente
  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <NestingStep1ODLSelection
            onNext={handleStep1Complete}
            onBack={onCancel}
            isLoading={isLoading}
            savedProgress={progress.step1_odl_data ? {
              selected_odl_ids: progress.step1_odl_data.selected_odl_ids,
              filters: {
                status_filter: 'all',
                priorita_filter: 'all',
                search_filter: ''
              }
            } : undefined}
          />
        )

      case 2:
        return (
          <AutomaticStep2AutoclaveSelection
            onNext={handleStep2Complete}
            onBack={goToPreviousStep}
            isLoading={isLoading}
            odlData={progress.step1_odl_data!}
            savedData={progress.step2_autoclave_data}
          />
        )

      case 3:
        return (
          <AutomaticStep3LayoutGeneration
            onNext={handleStep3Complete}
            onBack={goToPreviousStep}
            isLoading={isLoading}
            odlData={progress.step1_odl_data!}
            autoclaveData={progress.step2_autoclave_data!}
            savedData={progress.step3_layout_data}
          />
        )

      case 4:
        return (
          <AutomaticStep4Validation
            onNext={handleStep4Complete}
            onBack={goToPreviousStep}
            isLoading={isLoading}
            odlData={progress.step1_odl_data!}
            autoclaveData={progress.step2_autoclave_data!}
            layoutData={progress.step3_layout_data!}
            savedData={progress.step4_validation_data}
          />
        )

      case 5:
        return (
          <AutomaticStep5Confirmation
            onNext={handleStep5Complete}
            onBack={goToPreviousStep}
            isLoading={isLoading}
            odlData={progress.step1_odl_data!}
            autoclaveData={progress.step2_autoclave_data!}
            layoutData={progress.step3_layout_data!}
            validationData={progress.step4_validation_data!}
            savedData={progress.step5_confirmation_data}
          />
        )

      default:
        return null
    }
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header del workflow */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Nesting Automatico - Workflow Guidato</span>
            <div className="text-sm text-muted-foreground">
              Step {currentStep} di {steps.length}
            </div>
          </CardTitle>
          <CardDescription>
            Processo automatizzato per la generazione ottimizzata del nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progresso Workflow</span>
              <span>{Math.round(completionPercentage)}%</span>
            </div>
            <Progress value={completionPercentage} className="w-full" />
          </div>

          {/* Step indicator */}
          <div className="mt-6 flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                  step.isCompleted ? "bg-green-600 text-white" :
                  currentStep === step.id ? "bg-blue-600 text-white" :
                  "bg-gray-200 text-gray-600"
                )}>
                  {step.isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    step.id
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={cn(
                    "w-12 h-1 mx-2 transition-colors",
                    step.isCompleted ? "bg-green-600" : "bg-gray-200"
                  )} />
                )}
              </div>
            ))}
          </div>

          {/* Step info */}
          <div className="mt-4 text-center">
            <h3 className="font-medium">{steps[currentStep - 1]?.title}</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {steps[currentStep - 1]?.description}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Errori */}
      {errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside">
              {errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Contenuto dello step corrente */}
      <div className="min-h-[400px]">
        {renderCurrentStep()}
      </div>

      {/* Pulsanti di navigazione (se non gestiti dal componente step) */}
      {currentStep > 1 && currentStep < 5 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={goToPreviousStep}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Step Precedente
              </Button>
              
              <Button
                onClick={goToNextStep}
                disabled={isLoading || !steps[currentStep - 1]?.isCompleted}
                className="flex items-center gap-2"
              >
                Step Successivo
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 