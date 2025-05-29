'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  CheckCircle, 
  Circle, 
  ArrowLeft, 
  ArrowRight,
  AlertCircle 
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface NestingStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'current' | 'completed' | 'error'
  required: boolean
}

interface NestingStepIndicatorProps {
  steps: NestingStep[]
  currentStepId: string
  onStepClick?: (stepId: string) => void
  onPrevious?: () => void
  onNext?: () => void
  className?: string
  showNavigation?: boolean
}

export function NestingStepIndicator({ 
  steps, 
  currentStepId, 
  onStepClick,
  onPrevious,
  onNext,
  className,
  showNavigation = true
}: NestingStepIndicatorProps) {
  const currentStepIndex = steps.findIndex(step => step.id === currentStepId)
  const currentStep = steps[currentStepIndex]
  
  const canGoToPrevious = currentStepIndex > 0 && onPrevious
  const canGoToNext = currentStepIndex < steps.length - 1 && onNext
  
  // Verifica se l'utente può accedere a uno step specifico
  const canAccessStep = (stepIndex: number) => {
    // Può accedere solo agli step completati o al prossimo step disponibile
    for (let i = 0; i < stepIndex; i++) {
      if (steps[i].required && steps[i].status !== 'completed') {
        return false
      }
    }
    return true
  }

  const getStepIcon = (step: NestingStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'current':
        return <Circle className="h-5 w-5 text-blue-600 fill-blue-600" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <Circle className="h-5 w-5 text-gray-400" />
    }
  }

  const getStepStatus = (step: NestingStep, index: number) => {
    if (step.status === 'completed') return 'bg-green-100 text-green-800'
    if (step.status === 'current') return 'bg-blue-100 text-blue-800'
    if (step.status === 'error') return 'bg-red-100 text-red-800'
    if (canAccessStep(index)) return 'bg-gray-100 text-gray-600'
    return 'bg-gray-50 text-gray-400'
  }

  return (
    <div 
      className={cn("space-y-4", className)}
      data-step-indicator
    >
      {/* Progress Bar */}
      <div className="relative">
        <div className="flex items-center">
          {steps.map((step, index) => {
            const isClickable = canAccessStep(index) && onStepClick
            const isLast = index === steps.length - 1

            return (
              <React.Fragment key={step.id}>
                {/* Step Circle */}
                <div
                  className={cn(
                    "relative flex items-center justify-center",
                    "w-10 h-10 rounded-full border-2 transition-all duration-200",
                    isClickable && "cursor-pointer hover:scale-110",
                    step.status === 'completed' && "border-green-600 bg-green-50",
                    step.status === 'current' && "border-blue-600 bg-blue-50",
                    step.status === 'error' && "border-red-600 bg-red-50",
                    step.status === 'pending' && "border-gray-300 bg-gray-50"
                  )}
                  onClick={() => isClickable && onStepClick(step.id)}
                >
                  {getStepIcon(step)}
                  
                  {/* Step Number Badge */}
                  <Badge 
                    variant="secondary" 
                    className={cn(
                      "absolute -top-2 -right-2 w-5 h-5 p-0 text-xs",
                      getStepStatus(step, index)
                    )}
                  >
                    {index + 1}
                  </Badge>
                </div>

                {/* Connection Line */}
                {!isLast && (
                  <div className={cn(
                    "flex-1 h-0.5 mx-4 transition-colors duration-200",
                    steps[index + 1].status === 'completed' || 
                    steps[index + 1].status === 'current' 
                      ? "bg-blue-600" 
                      : "bg-gray-300"
                  )} />
                )}
              </React.Fragment>
            )
          })}
        </div>

        {/* Step Labels */}
        <div className="flex items-start mt-4">
          {steps.map((step, index) => {
            const isLast = index === steps.length - 1
            
            return (
              <React.Fragment key={`label-${step.id}`}>
                <div className="w-10 text-center">
                  <div className={cn(
                    "text-xs font-medium transition-colors duration-200",
                    step.status === 'current' && "text-blue-600",
                    step.status === 'completed' && "text-green-600",
                    step.status === 'error' && "text-red-600",
                    step.status === 'pending' && "text-gray-500"
                  )}>
                    {step.title}
                  </div>
                  {step.required && (
                    <Badge variant="outline" className="mt-1 text-xs">
                      Obbligatorio
                    </Badge>
                  )}
                </div>
                
                {!isLast && <div className="flex-1 mx-4" />}
              </React.Fragment>
            )
          })}
        </div>
      </div>

      {/* Current Step Info */}
      {currentStep && (
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold">
                Step {currentStepIndex + 1}: {currentStep.title}
              </h3>
              <p className="text-sm text-muted-foreground">
                {currentStep.description}
              </p>
              {currentStep.required && (
                <Badge variant="secondary" className="text-xs">
                  Passaggio Obbligatorio
                </Badge>
              )}
            </div>
            
            {currentStep.status === 'error' && (
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      {showNavigation && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={onPrevious}
            disabled={!canGoToPrevious}
            className="flex items-center gap-2"
            data-nesting-action="back"
          >
            <ArrowLeft className="h-4 w-4" />
            Precedente
          </Button>

          <div className="text-center">
            <Badge variant="outline">
              {currentStepIndex + 1} di {steps.length}
            </Badge>
          </div>

          <Button
            onClick={onNext}
            disabled={!canGoToNext}
            className="flex items-center gap-2"
          >
            Successivo
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

// Preset di step comuni per diversi tipi di nesting
export const manualNestingSteps: NestingStep[] = [
  {
    id: 'select-odl',
    title: 'Selezione ODL',
    description: '📋 Seleziona gli ODL in attesa di cura e estrai dati automaticamente',
    status: 'pending',
    required: true
  },
  {
    id: 'select-autoclave',
    title: 'Autoclave',
    description: '🏭 Seleziona l\'autoclave più compatibile con gli ODL scelti',
    status: 'pending',
    required: true
  },
  {
    id: 'arrange-layout',
    title: 'Layout Canvas',
    description: '🎨 Posiziona i tool tramite drag&drop con prevenzione conflitti',
    status: 'pending',
    required: true
  },
  {
    id: 'validate',
    title: 'Validazione',
    description: '✅ Verifica efficienza, compatibilità e vincoli di sicurezza',
    status: 'pending',
    required: true
  },
  {
    id: 'confirm',
    title: 'Conferma',
    description: '🚀 Carica in autoclave e aggiorna stati ODL automaticamente',
    status: 'pending',
    required: true
  }
]

export const automaticNestingSteps: NestingStep[] = [
  {
    id: 'select-odl',
    title: 'ODL',
    description: '📋 Seleziona tutti gli ODL in attesa di cura da processare automaticamente',
    status: 'pending',
    required: true
  },
  {
    id: 'select-autoclave',
    title: 'Autoclave',
    description: '🏭 Seleziona l\'autoclave target per l\'ottimizzazione automatica',
    status: 'pending',
    required: true
  },
  {
    id: 'configure-parameters',
    title: 'Parametri',
    description: '⚙️ Configura parametri di ottimizzazione (distanze, efficienza, priorità)',
    status: 'pending',
    required: false
  },
  {
    id: 'generate-preview',
    title: 'Preview',
    description: '🔄 Genera anteprima automatica con algoritmo OR-Tools',
    status: 'pending',
    required: true
  },
  {
    id: 'review',
    title: 'Revisione',
    description: '👁️ Esamina risultati e layout generato automaticamente',
    status: 'pending',
    required: true
  },
  {
    id: 'confirm',
    title: 'Conferma',
    description: '✅ Conferma e salva il nesting ottimizzato',
    status: 'pending',
    required: true
  }
]

export const multiAutoclaveSteps: NestingStep[] = [
  {
    id: 'select-autoclaves',
    title: 'Autoclavi',
    description: '🏭 Seleziona le autoclavi disponibili per la distribuzione batch',
    status: 'pending',
    required: true
  },
  {
    id: 'select-odl-batch',
    title: 'Batch ODL',
    description: '📦 Scegli il gruppo di ODL da distribuire automaticamente',
    status: 'pending',
    required: true
  },
  {
    id: 'configure-distribution',
    title: 'Distribuzione',
    description: '⚖️ Configura logica di bilanciamento e distribuzione intelligente',
    status: 'pending',
    required: false
  },
  {
    id: 'generate-batch',
    title: 'Generazione',
    description: '🔄 Genera batch di nesting multipli ottimizzati',
    status: 'pending',
    required: true
  },
  {
    id: 'review-batch',
    title: 'Revisione Batch',
    description: '👁️ Esamina tutti i nesting generati e le distribuzioni',
    status: 'pending',
    required: true
  },
  {
    id: 'confirm-batch',
    title: 'Conferma Batch',
    description: '✅ Conferma l\'intero batch e avvia produzione',
    status: 'pending',
    required: true
  }
] 