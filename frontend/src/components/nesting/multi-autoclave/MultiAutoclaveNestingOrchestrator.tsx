'use client'

import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, CheckCircle, ArrowLeft, ArrowRight, Users, Server } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

// Import dei tab e componenti esistenti
import { MultiAutoclaveTab } from '../tabs/MultiAutoclaveTab'
import { NestingStep1ODLSelection, ExtractedNestingData } from '../manual/NestingStep1ODLSelection'

// Tipi per il workflow multi-autoclave
interface MultiAutoclaveProgress {
  step1_odl_data?: ExtractedNestingData
  step2_batch_parameters?: any
  step3_multi_generation?: any
  step4_batch_validation?: any
  step5_batch_confirmation?: any
}

interface MultiAutoclaveNestingOrchestratorProps {
  onComplete: (data: any) => void
  onCancel: () => void
  className?: string
  initialData?: MultiAutoclaveProgress
}

export function MultiAutoclaveNestingOrchestrator({
  onComplete,
  onCancel,
  className,
  initialData
}: MultiAutoclaveNestingOrchestratorProps) {
  const { toast } = useToast()
  
  // State del workflow
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<string[]>([])
  const [progress, setProgress] = useState<MultiAutoclaveProgress>(initialData || {})

  // Configurazione degli step
  const steps = [
    { 
      id: 1, 
      title: 'Selezione ODL Batch', 
      description: 'Seleziona gli ODL per il processamento multi-autoclave',
      isCompleted: !!progress.step1_odl_data
    },
    { 
      id: 2, 
      title: 'Configurazione Batch', 
      description: 'Definisci i parametri per l\'ottimizzazione batch',
      isCompleted: !!progress.step2_batch_parameters
    },
    { 
      id: 3, 
      title: 'Generazione Multi-Layout', 
      description: 'Genera automaticamente layout per più autoclavi',
      isCompleted: !!progress.step3_multi_generation
    },
    { 
      id: 4, 
      title: 'Validazione Batch', 
      description: 'Verifica la qualità dei layout generati',
      isCompleted: !!progress.step4_batch_validation
    },
    { 
      id: 5, 
      title: 'Conferma Multi-Nesting', 
      description: 'Conferma e salva tutti i nesting batch',
      isCompleted: !!progress.step5_batch_confirmation
    }
  ]

  // Calcola la percentuale di completamento
  const completionPercentage = (steps.filter(s => s.isCompleted).length / steps.length) * 100

  // Gestione errori
  const addError = useCallback((error: string) => {
    setErrors(prev => [...prev, error])
    toast({
      title: "Errore nel Workflow Multi-Autoclave",
      description: error,
      variant: "destructive"
    })
  }, [toast])

  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  // Handler per il completamento dello Step 1 (Selezione ODL)
  const handleStep1Complete = useCallback(async (data: ExtractedNestingData) => {
    try {
      setIsLoading(true)
      clearErrors()

      // Validazione per multi-autoclave: serve più ODL
      if (data.selected_odl_ids.length < 6) {
        throw new Error("Per il nesting multi-autoclave sono necessari almeno 6 ODL")
      }

      setProgress(prev => ({ ...prev, step1_odl_data: data }))
      setCurrentStep(2)

      toast({
        title: "Step 1 Completato",
        description: `${data.selected_odl_ids.length} ODL selezionati per processamento batch`
      })
    } catch (error: any) {
      addError(error.message || "Errore nella selezione ODL batch")
    } finally {
      setIsLoading(false)
    }
  }, [addError, clearErrors, toast])

  // Handler per completamento Step 2 (usa MultiAutoclaveTab esistente)
  const handleMultiAutoclaveComplete = useCallback(async (data: any) => {
    try {
      setIsLoading(true)
      clearErrors()

      setProgress(prev => ({ 
        ...prev, 
        step2_batch_parameters: data.parameters,
        step3_multi_generation: data.results,
        step4_batch_validation: { is_valid: true, score: 95 },
        step5_batch_confirmation: data.confirmation
      }))

      toast({
        title: "Multi-Autoclave Completato!",
        description: "Tutti i nesting batch sono stati generati e confermati"
      })

      // Simula un breve delay prima di chiamare onComplete
      setTimeout(() => {
        onComplete(data)
      }, 1000)

    } catch (error: any) {
      addError(error.message || "Errore nel processamento multi-autoclave")
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
      case 3:
      case 4:
      case 5:
        // Usa il MultiAutoclaveTab esistente per tutti gli step rimanenti
        return (
          <MultiAutoclaveTab
            currentStep={'generate-batch'}
            onStepComplete={handleMultiAutoclaveComplete}
            onStepError={(error) => addError(error)}
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
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              <span>Multi-Autoclave Nesting - Workflow Batch</span>
            </div>
            <div className="text-sm text-muted-foreground">
              Step {currentStep} di {steps.length}
            </div>
          </CardTitle>
          <CardDescription>
            Processo batch per la generazione ottimizzata di nesting su multiple autoclavi
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progresso Workflow Batch</span>
              <span>{Math.round(completionPercentage)}%</span>
            </div>
            <Progress value={completionPercentage} className="w-full" />
          </div>

          {/* Step indicator */}
          <div className="mt-6 flex items-center justify-between overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-shrink-0">
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
                    "w-8 h-1 mx-2 transition-colors flex-shrink-0",
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

      {/* Pulsanti di navigazione (solo per lo step 1) */}
      {currentStep === 1 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={onCancel}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Annulla
              </Button>
              
              <div className="text-sm text-muted-foreground">
                Continua con la selezione ODL per procedere al processamento batch
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 