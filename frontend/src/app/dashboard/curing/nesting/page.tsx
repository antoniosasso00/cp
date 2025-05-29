'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RefreshCw, ArrowLeft, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { useRouter } from 'next/navigation'

// Import dei componenti per il nesting
import { NestingModeSelector } from '@/components/nesting/NestingModeSelector'
import { NestingStepIndicator } from '@/components/nesting/NestingStepIndicator'
import { useNestingWorkflow, NestingWorkflowMode } from '@/hooks/useNestingWorkflow'

// Import dei componenti per le diverse modalità
import { 
  ParametersTab, 
  ConfirmedLayoutsTab, 
  ReportsTab,
  PreviewOptimizationTab,
  MultiAutoclaveTab
} from '@/components/nesting/tabs'

// Import delle API
import { nestingApi, NestingResponse } from '@/lib/api'
import { NestingParameters } from '@/components/nesting/NestingParametersPanel'
import { ManualNestingOrchestrator } from '@/components/nesting/manual/ManualNestingOrchestrator'
import { AutomaticNestingOrchestrator } from '@/components/nesting/automatic/AutomaticNestingOrchestrator'
import { MultiAutoclaveNestingOrchestrator } from '@/components/nesting/multi-autoclave/MultiAutoclaveNestingOrchestrator'

// Tab aggiuntivi per funzionalità complete
import { ActiveNestingTable } from '@/components/nesting/ActiveNestingTable'
import { NestingVisualizationPage } from '@/components/nesting/NestingVisualizationPage'

export default function NestingPage() {
  const [nestingList, setNestingList] = useState<NestingResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'workflow' | 'confirmed' | 'active' | 'reports'>('workflow')
  
  // Parametri per il nesting
  const [nestingParameters, setNestingParameters] = useState<NestingParameters>({
    distanza_minima_tool_cm: 2.0,
    padding_bordo_autoclave_cm: 1.5,
    margine_sicurezza_peso_percent: 10.0,
    priorita_minima: 1,
    efficienza_minima_percent: 60.0
  })

  const { toast } = useToast()
  const router = useRouter()
  
  // Hook per gestire il workflow guidato
  const workflow = useNestingWorkflow()

  // Carica la lista dei nesting
  const loadNestingList = async () => {
    try {
      setIsLoading(true)
      const data = await nestingApi.getAll()
      setNestingList(data || [])
    } catch (error) {
      setNestingList([])
      toast({
        title: "Errore",
        description: "Impossibile caricare la lista dei nesting.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Carica la lista al primo render
  useEffect(() => {
    loadNestingList()
  }, [])

  // Handler per la selezione della modalità
  const handleModeSelect = (mode: string) => {
    workflow.startWorkflow(mode as NestingWorkflowMode)
  }

  // Handler per il reset del workflow
  const handleBackToModeSelection = () => {
    workflow.resetWorkflow()
    setActiveTab('workflow')
  }

  // Handler per i passaggi del workflow
  const handleStepComplete = (stepData?: any) => {
    workflow.completeCurrentStep(stepData)
    
    // Auto-advance al prossimo step se possibile
    if (!workflow.isCompleted) {
      setTimeout(() => {
        workflow.goToNextStep()
      }, 500)
    }
  }

  // Handler per la gestione degli errori negli step
  const handleStepError = (error: string) => {
    workflow.markStepAsError(undefined, error)
    toast({
      title: "Errore nello step",
      description: error,
      variant: "destructive",
    })
  }

  // Funzione per gestire la visualizzazione dei dettagli
  const handleViewDetails = async (nestingId: number) => {
    try {
      router.push(`/dashboard/curing/nesting/${nestingId}`)
    } catch (error) {
      toast({
        title: "Errore",
        description: `Impossibile aprire i dettagli del nesting #${nestingId}`,
        variant: "destructive",
      })
    }
  }

  // Funzione per gestire la conferma di un nesting
  const handleNestingConfirmed = async () => {
    try {
      await loadNestingList()
      handleStepComplete({ confirmed: true })
      toast({
        title: "Nesting confermato",
        description: "Il nesting è stato confermato con successo.",
      })
      
      // Mostra i layout confermati dopo la conferma
      if (workflow.isCompleted) {
        setActiveTab('confirmed')
      }
    } catch (error) {
      handleStepError("Errore durante la conferma del nesting")
    }
  }

  // Funzione per gestire l'aggiornamento dei parametri
  const handleParametersUpdate = (params: NestingParameters) => {
    setNestingParameters(params)
    handleStepComplete({ parameters: params })
    toast({
      title: "Parametri aggiornati",
      description: "I parametri di ottimizzazione sono stati salvati.",
    })
  }

  // Funzione per terminare un ciclo di cura
  const handleTerminateCure = async (nestingId: number) => {
    try {
      await nestingApi.updateStatus(nestingId, { 
        stato: 'completato',
        note: 'Ciclo di cura terminato manualmente'
      })
      
      await loadNestingList()
      
      toast({
        title: "Ciclo terminato",
        description: "Il ciclo di cura è stato terminato con successo.",
      })
    } catch (error) {
      toast({
        title: "Errore",
        description: "Impossibile terminare il ciclo di cura.",
        variant: "destructive",
      })
    }
  }

  // Render del contenuto del workflow
  const renderWorkflowContent = () => {
    if (!workflow.mode) {
      return (
        <NestingModeSelector 
          onModeSelect={handleModeSelect}
          className="max-w-6xl mx-auto"
        />
      )
    }

    // Contenuto specifico per ogni step in base alla modalità
    const currentStep = workflow.steps[workflow.currentStepIndex]
    if (!currentStep) return null

    switch (workflow.mode) {
      case 'manual':
        return (
          <ManualNestingOrchestrator
            onComplete={handleNestingConfirmed}
            onCancel={handleBackToModeSelection}
            className="max-w-7xl mx-auto"
          />
        )
      
      case 'automatic':
        return (
          <AutomaticNestingOrchestrator
            onComplete={handleNestingConfirmed}
            onCancel={handleBackToModeSelection}
            className="max-w-7xl mx-auto"
          />
        )
      
      case 'multi-autoclave':
        return (
          <MultiAutoclaveNestingOrchestrator
            onComplete={handleNestingConfirmed}
            onCancel={handleBackToModeSelection}
            className="max-w-7xl mx-auto"
          />
        )
      
      default:
        return null
    }
  }

  // Render step per nesting automatico
  const renderAutomaticNestingStep = (stepId: string) => {
    switch (stepId) {
      case 'configure-parameters':
        return (
          <ParametersTab
            parameters={nestingParameters}
            onParametersChange={handleParametersUpdate}
            isLoading={isLoading}
            onPreview={() => handleStepComplete({ parameters: nestingParameters })}
          />
        )
      
      case 'generate-preview':
      case 'review':
      case 'confirm':
        return (
          <PreviewOptimizationTab
            onRefresh={loadNestingList}
            onViewDetails={handleViewDetails}
            onNestingConfirmed={handleNestingConfirmed}
            parameters={nestingParameters}
            currentStep={stepId}
          />
        )
      
      default:
        return null
    }
  }

  // Render del contenuto principale in base al tab attivo
  const renderMainContent = () => {
    if (activeTab === 'workflow') {
      return (
        <>
          {/* Indicatore di progresso del workflow */}
          {workflow.mode && workflow.steps.length > 0 && workflow.mode !== 'manual' && (
            <NestingStepIndicator
              steps={workflow.steps}
              currentStepId={workflow.currentStepId}
              onStepClick={workflow.goToStep}
              onPrevious={workflow.goToPreviousStep}
              onNext={workflow.goToNextStep}
            />
          )}

          {/* Contenuto del workflow */}
          <div className="min-h-[500px]">
            {renderWorkflowContent()}
          </div>

          {/* Workflow completato */}
          {workflow.isCompleted && (
            <Card className="bg-green-50 border-green-200">
              <CardHeader>
                <CardTitle className="text-green-800 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Workflow Completato!
                </CardTitle>
                <CardDescription className="text-green-700">
                  Il processo di nesting è stato completato con successo.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Button 
                    onClick={() => setActiveTab('confirmed')}
                    data-nesting-action="view"
                  >
                    Visualizza Layout Confermati
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={handleBackToModeSelection}
                  >
                    Crea Nuovo Nesting
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )
    }

    if (activeTab === 'confirmed') {
      return (
        <ConfirmedLayoutsTab
          onRefresh={loadNestingList}
          onViewDetails={handleViewDetails}
        />
      )
    }

    if (activeTab === 'active') {
      return (
        <ActiveNestingTable
          onRefresh={loadNestingList}
          onTerminateCure={handleTerminateCure}
        />
      )
    }

    if (activeTab === 'reports') {
      return (
        <ReportsTab
          onRefresh={loadNestingList}
        />
      )
    }

    return null
  }

  return (
    <div className="container mx-auto p-6 space-y-6" data-api-status={isLoading ? 'loading' : 'ready'}>
      {/* Header della pagina */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestione Nesting</h1>
          <p className="text-muted-foreground">
            {workflow.mode && activeTab === 'workflow'
              ? `Modalità: ${workflow.mode === 'manual' ? 'Manuale' : 
                           workflow.mode === 'automatic' ? 'Automatico' : 
                           'Multi-Autoclave'}`
              : activeTab === 'confirmed' ? 'Layout Confermati'
              : activeTab === 'active' ? 'Nesting Attivi'
              : activeTab === 'reports' ? 'Report Nesting'
              : 'Seleziona una modalità di nesting'
            }
          </p>
        </div>
        
        <div className="flex gap-2">
          {workflow.mode && activeTab === 'workflow' && (
            <Button
              variant="outline"
              onClick={handleBackToModeSelection}
              className="flex items-center gap-2"
              data-nesting-action="back"
            >
              <ArrowLeft className="h-4 w-4" />
              Cambia Modalità
            </Button>
          )}
          
          <Button
            variant="outline"
            onClick={loadNestingList}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
        </div>
      </div>

      {/* Tab di navigazione */}
      <div className="border-b">
        <nav className="-mb-px flex gap-6">
          <button
            onClick={() => setActiveTab('workflow')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'workflow'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
            }`}
          >
            Crea Nesting
          </button>
          <button
            onClick={() => setActiveTab('confirmed')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'confirmed'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
            }`}
          >
            Layout Confermati
            {nestingList.filter(n => n.stato === 'In sospeso').length > 0 && (
              <span className="ml-2 bg-primary text-primary-foreground rounded-full px-2 py-0.5 text-xs">
                {nestingList.filter(n => n.stato === 'In sospeso').length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('active')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'active'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
            }`}
          >
            Nesting Attivi
            {nestingList.filter(n => n.stato === 'Caricato').length > 0 && (
              <span className="ml-2 bg-green-600 text-white rounded-full px-2 py-0.5 text-xs">
                {nestingList.filter(n => n.stato === 'Caricato').length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('reports')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'reports'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
            }`}
          >
            Report
          </button>
        </nav>
      </div>

      {/* Contenuto principale */}
      {isLoading && activeTab !== 'workflow' ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        renderMainContent()
      )}

      {/* Stato di errore */}
      {workflow.steps.some(step => step.status === 'error') && activeTab === 'workflow' && (
        <Card className="bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-800 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Errori nel Workflow
            </CardTitle>
            <CardDescription className="text-red-700">
              Si sono verificati errori durante il processo. Verifica e riprova.
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  )
} 