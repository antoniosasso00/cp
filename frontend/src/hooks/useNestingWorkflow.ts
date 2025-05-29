import { useState, useCallback, useEffect } from 'react'
import { 
  NestingStep, 
  manualNestingSteps, 
  automaticNestingSteps, 
  multiAutoclaveSteps 
} from '@/components/nesting/NestingStepIndicator'

export type NestingWorkflowMode = 'manual' | 'automatic' | 'multi-autoclave'

interface NestingWorkflowState {
  mode: NestingWorkflowMode | null
  steps: NestingStep[]
  currentStepId: string
  currentStepIndex: number
  workflowData: Record<string, any>
  isCompleted: boolean
}

interface NestingWorkflowActions {
  startWorkflow: (mode: NestingWorkflowMode) => void
  resetWorkflow: () => void
  goToStep: (stepId: string) => boolean
  goToNextStep: () => boolean
  goToPreviousStep: () => boolean
  completeCurrentStep: (data?: any) => void
  markStepAsError: (stepId?: string, error?: string) => void
  updateStepData: (stepId: string, data: any) => void
  canAccessStep: (stepId: string) => boolean
  getStepData: (stepId: string) => any
}

export function useNestingWorkflow(): NestingWorkflowState & NestingWorkflowActions {
  const [state, setState] = useState<NestingWorkflowState>({
    mode: null,
    steps: [],
    currentStepId: '',
    currentStepIndex: -1,
    workflowData: {},
    isCompleted: false
  })

  // Ottieni gli step in base alla modalità
  const getStepsForMode = useCallback((mode: NestingWorkflowMode): NestingStep[] => {
    switch (mode) {
      case 'manual':
        return [...manualNestingSteps]
      case 'automatic':
        return [...automaticNestingSteps]
      case 'multi-autoclave':
        return [...multiAutoclaveSteps]
      default:
        return []
    }
  }, [])

  // Inizia un nuovo workflow
  const startWorkflow = useCallback((mode: NestingWorkflowMode) => {
    const steps = getStepsForMode(mode)
    if (steps.length > 0) {
      const initialSteps = steps.map((step, index) => ({
        ...step,
        status: index === 0 ? 'current' as const : 'pending' as const
      }))

      setState({
        mode,
        steps: initialSteps,
        currentStepId: steps[0].id,
        currentStepIndex: 0,
        workflowData: {},
        isCompleted: false
      })
    }
  }, [getStepsForMode])

  // Reset del workflow
  const resetWorkflow = useCallback(() => {
    setState({
      mode: null,
      steps: [],
      currentStepId: '',
      currentStepIndex: -1,
      workflowData: {},
      isCompleted: false
    })
  }, [])

  // Verifica se l'utente può accedere a un determinato step
  const canAccessStep = useCallback((stepId: string): boolean => {
    const stepIndex = state.steps.findIndex(step => step.id === stepId)
    if (stepIndex === -1) return false

    // Può accedere al primo step
    if (stepIndex === 0) return true

    // Verifica che tutti gli step obbligatori precedenti siano completati
    for (let i = 0; i < stepIndex; i++) {
      const step = state.steps[i]
      if (step.required && step.status !== 'completed') {
        return false
      }
    }

    return true
  }, [state.steps])

  // Vai a uno step specifico
  const goToStep = useCallback((stepId: string): boolean => {
    if (!canAccessStep(stepId)) {
      console.warn(`Impossibile accedere allo step ${stepId}. Step precedenti non completati.`)
      return false
    }

    const stepIndex = state.steps.findIndex(step => step.id === stepId)
    if (stepIndex === -1) return false

    setState(prev => ({
      ...prev,
      currentStepId: stepId,
      currentStepIndex: stepIndex,
      steps: prev.steps.map((step, index) => ({
        ...step,
        status: index === stepIndex ? 'current' : step.status
      }))
    }))

    return true
  }, [state.steps, canAccessStep])

  // Vai al prossimo step
  const goToNextStep = useCallback((): boolean => {
    const nextIndex = state.currentStepIndex + 1
    if (nextIndex >= state.steps.length) return false

    const nextStep = state.steps[nextIndex]
    return goToStep(nextStep.id)
  }, [state.currentStepIndex, state.steps, goToStep])

  // Vai allo step precedente
  const goToPreviousStep = useCallback((): boolean => {
    const prevIndex = state.currentStepIndex - 1
    if (prevIndex < 0) return false

    const prevStep = state.steps[prevIndex]
    return goToStep(prevStep.id)
  }, [state.currentStepIndex, state.steps, goToStep])

  // Completa lo step corrente
  const completeCurrentStep = useCallback((data?: any) => {
    if (state.currentStepIndex === -1) return

    setState(prev => {
      const newSteps = [...prev.steps]
      newSteps[prev.currentStepIndex] = {
        ...newSteps[prev.currentStepIndex],
        status: 'completed'
      }

      // Attiva il prossimo step se esiste
      if (prev.currentStepIndex + 1 < newSteps.length) {
        newSteps[prev.currentStepIndex + 1] = {
          ...newSteps[prev.currentStepIndex + 1],
          status: 'current'
        }
      }

      // Verifica se il workflow è completato
      const isCompleted = newSteps.every(step => !step.required || step.status === 'completed')

      return {
        ...prev,
        steps: newSteps,
        workflowData: data ? { ...prev.workflowData, [prev.currentStepId]: data } : prev.workflowData,
        isCompleted
      }
    })
  }, [state.currentStepIndex, state.currentStepId])

  // Marca uno step come errore
  const markStepAsError = useCallback((stepId?: string, error?: string) => {
    const targetStepId = stepId || state.currentStepId
    if (!targetStepId) return

    setState(prev => ({
      ...prev,
      steps: prev.steps.map(step =>
        step.id === targetStepId
          ? { ...step, status: 'error' as const }
          : step
      ),
      workflowData: error 
        ? { ...prev.workflowData, [`${targetStepId}_error`]: error }
        : prev.workflowData
    }))
  }, [state.currentStepId])

  // Aggiorna i dati di uno step
  const updateStepData = useCallback((stepId: string, data: any) => {
    setState(prev => ({
      ...prev,
      workflowData: { ...prev.workflowData, [stepId]: data }
    }))
  }, [])

  // Ottieni i dati di uno step
  const getStepData = useCallback((stepId: string): any => {
    return state.workflowData[stepId]
  }, [state.workflowData])

  return {
    ...state,
    startWorkflow,
    resetWorkflow,
    goToStep,
    goToNextStep,
    goToPreviousStep,
    completeCurrentStep,
    markStepAsError,
    updateStepData,
    canAccessStep,
    getStepData
  }
} 