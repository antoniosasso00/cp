'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { cn } from '@/shared/lib/utils'
import { Check, Circle, ChevronRight } from 'lucide-react'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'

export interface StepItem {
  /** ID univoco dello step */
  id: string
  /** Titolo dello step */
  title: string
  /** Descrizione opzionale */
  description?: string
  /** Stato dello step */
  status: 'pending' | 'current' | 'completed' | 'error'
  /** Se lo step è cliccabile */
  clickable?: boolean
  /** Badge opzionale */
  badge?: string
  /** Variante del badge */
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
}

export interface StepSidebarProps {
  /** Lista degli step */
  steps: StepItem[]
  /** Step attualmente attivo */
  currentStepId?: string
  /** Callback quando si clicca su uno step */
  onStepClick?: (stepId: string) => void
  /** Se permettere navigazione libera */
  allowNavigation?: boolean
  /** Orientamento della sidebar */
  orientation?: 'vertical' | 'horizontal'
  /** Classname aggiuntive */
  className?: string
  /** Titolo della sidebar */
  title?: string
  /** Se mostrare i numeri degli step */
  showNumbers?: boolean
  /** Se abilitare scroll automatico */
  enableAutoScroll?: boolean
}

const getStepStyles = (status: StepItem['status'], isCurrent: boolean) => {
  const baseStyles = 'transition-all duration-200'
  
  switch (status) {
    case 'completed':
      return cn(baseStyles, 'text-green-700 bg-green-50 border-green-200')
    case 'current':
      return cn(baseStyles, 'text-blue-700 bg-blue-50 border-blue-200 ring-2 ring-blue-200')
    case 'error':
      return cn(baseStyles, 'text-red-700 bg-red-50 border-red-200')
    case 'pending':
    default:
      return cn(baseStyles, 'text-gray-600 bg-gray-50 border-gray-200')
  }
}

const getStepIcon = (status: StepItem['status'], stepNumber: number, showNumbers: boolean) => {
  switch (status) {
    case 'completed':
      return <Check className="h-4 w-4" />
    case 'current':
      return showNumbers ? (
        <span className="text-sm font-bold">{stepNumber}</span>
      ) : (
        <Circle className="h-4 w-4" />
      )
    case 'error':
      return <span className="text-sm font-bold">!</span>
    case 'pending':
    default:
      return showNumbers ? (
        <span className="text-sm text-muted-foreground">{stepNumber}</span>
      ) : (
        <Circle className="h-4 w-4" />
      )
  }
}

export const StepSidebar: React.FC<StepSidebarProps> = ({
  steps,
  currentStepId,
  onStepClick,
  allowNavigation = true,
  orientation = 'vertical',
  className,
  title,
  showNumbers = true,
  enableAutoScroll = true
}) => {
  const [activeStepId, setActiveStepId] = useState<string | undefined>(currentStepId)

  // Auto-scroll to current step
  const scrollToStep = useCallback((stepId: string) => {
    if (!enableAutoScroll) return
    
    const element = document.getElementById(`step-${stepId}`)
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'nearest'
      })
    }
  }, [enableAutoScroll])

  // Update active step when currentStepId changes
  useEffect(() => {
    if (currentStepId && currentStepId !== activeStepId) {
      setActiveStepId(currentStepId)
      scrollToStep(currentStepId)
    }
  }, [currentStepId, activeStepId, scrollToStep])

  const handleStepClick = useCallback((step: StepItem) => {
    if (!allowNavigation || (!step.clickable && step.status === 'pending')) {
      return
    }

    setActiveStepId(step.id)
    scrollToStep(step.id)
    onStepClick?.(step.id)
  }, [allowNavigation, onStepClick, scrollToStep])

  const containerClasses = cn(
    'space-y-2',
    orientation === 'horizontal' && 'flex space-y-0 space-x-2 overflow-x-auto',
    className
  )

  const stepClasses = (step: StepItem) => cn(
    'p-3 rounded-lg border cursor-pointer hover:shadow-sm',
    getStepStyles(step.status, step.id === activeStepId),
    (!allowNavigation || (!step.clickable && step.status === 'pending')) && 'cursor-not-allowed opacity-75'
  )

  return (
    <div className={cn('w-full', className)}>
      {title && (
        <div className="mb-4 pb-2 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}

      <div className={containerClasses}>
        {steps.map((step, index) => (
          <div
            key={step.id}
            id={`step-${step.id}`}
            className={stepClasses(step)}
            onClick={() => handleStepClick(step)}
          >
            <div className="flex items-center gap-3">
              {/* Step icon/number */}
              <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full border bg-white">
                {getStepIcon(step.status, index + 1, showNumbers)}
              </div>

              {/* Step content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-medium truncate">
                    {step.title}
                  </h4>
                  
                  {step.badge && (
                    <Badge 
                      variant={step.badgeVariant || 'secondary'} 
                      className="text-xs flex-shrink-0"
                    >
                      {step.badge}
                    </Badge>
                  )}
                </div>

                {step.description && (
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {step.description}
                  </p>
                )}
              </div>

              {/* Navigation arrow */}
              {orientation === 'vertical' && step.id === activeStepId && (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Hook per gestire lo stato degli step
export const useStepNavigation = (initialSteps: StepItem[]) => {
  const [steps, setSteps] = useState<StepItem[]>(initialSteps)
  const [currentStepId, setCurrentStepId] = useState<string>(
    initialSteps.find(s => s.status === 'current')?.id || initialSteps[0]?.id
  )

  const updateStepStatus = useCallback((stepId: string, status: StepItem['status']) => {
    setSteps(prev => 
      prev.map(step => 
        step.id === stepId ? { ...step, status } : step
      )
    )
  }, [])

  const goToStep = useCallback((stepId: string) => {
    setCurrentStepId(stepId)
    updateStepStatus(stepId, 'current')
  }, [updateStepStatus])

  const completeStep = useCallback((stepId: string) => {
    updateStepStatus(stepId, 'completed')
  }, [updateStepStatus])

  const goToNextStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === currentStepId)
    if (currentIndex < steps.length - 1) {
      const nextStep = steps[currentIndex + 1]
      goToStep(nextStep.id)
    }
  }, [steps, currentStepId, goToStep])

  const goToPreviousStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === currentStepId)
    if (currentIndex > 0) {
      const prevStep = steps[currentIndex - 1]
      goToStep(prevStep.id)
    }
  }, [steps, currentStepId, goToStep])

  return {
    steps,
    currentStepId,
    setSteps,
    updateStepStatus,
    goToStep,
    completeStep,
    goToNextStep,
    goToPreviousStep
  }
}

export default StepSidebar 