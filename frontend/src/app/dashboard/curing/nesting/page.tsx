'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RefreshCw, ArrowLeft, AlertCircle, CheckCircle, Loader2, Zap, Play } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { useRouter } from 'next/navigation'

// Import dei componenti per il nesting
import { NestingModeSelector } from '@/components/Nesting/NestingModeSelector'
import { NestingStepIndicator } from '@/components/Nesting/NestingStepIndicator'
import { useNestingWorkflow, NestingWorkflowMode } from '@/hooks/useNestingWorkflow'

// Import dei componenti per le diverse modalità
import { 
  ParametersTab, 
  ConfirmedLayoutsTab, 
  ReportsTab,
  PreviewOptimizationTab,
  MultiAutoclaveTab
} from '@/components/Nesting/tabs'

// Import delle API
import { nestingApi, NestingResponse } from '@/lib/api'
import { NestingParameters } from '@/components/Nesting/NestingParametersPanel'
import { ManualNestingOrchestrator } from '@/components/Nesting/manual/ManualNestingOrchestrator'
import { AutomaticNestingOrchestrator } from '@/components/Nesting/automatic/AutomaticNestingOrchestrator'
import { MultiAutoclaveNestingOrchestrator } from '@/components/Nesting/multi-autoclave/MultiAutoclaveNestingOrchestrator'

// Tab aggiuntivi per funzionalità complete
import { ActiveNestingTable } from '@/components/Nesting/ActiveNestingTable'
import { NestingVisualizationPage } from '@/components/Nesting/NestingVisualizationPage'

// Nuovo componente per i batch automatici
import { AutoMultiBatchTable } from '@/components/Nesting/auto-multi/AutoMultiBatchTable'

// Interfacce per i batch automatici
interface BatchAutomatico {
  id: number;
  nome: string;
  stato: string;
  numero_autoclavi: number;
  numero_odl_totali: number;
  peso_totale_kg: number;
  efficienza_media: number;
  data_inizio_pianificata: string | null;
  autoclavi: Array<{
    id: number;
    nome: string;
    efficienza: number;
    stato_nesting: string;
  }>;
  created_at: string;
}

export default function NestingPage() {
  const [nestingList, setNestingList] = useState<NestingResponse[]>([])
  const [batchAutomatici, setBatchAutomatici] = useState<BatchAutomatico[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'workflow' | 'confirmed' | 'active' | 'auto-multi' | 'reports'>('workflow')
  
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

  // Carica i batch automatici
  const loadBatchAutomatici = async () => {
    try {
      const response = await fetch('/api/v1/nesting/auto-multi/batch-attivi')
      if (!response.ok) throw new Error('Errore nel caricamento dei batch')
      
      const data = await response.json()
      setBatchAutomatici(data.data || [])
    } catch (error) {
      setBatchAutomatici([])
      console.error('Errore nel caricamento batch automatici:', error)
    }
  }

  // Carica tutti i dati
  const loadAllData = async () => {
    await Promise.all([
      loadNestingList(),
      loadBatchAutomatici()
    ])
  }

  // Carica la lista al primo render
  useEffect(() => {
    loadAllData()
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

  // Funzione per terminare un batch automatico
  const handleTerminateBatch = async (batchId: number) => {
    try {
      const response = await fetch(`/api/v1/nesting/auto-multi/termina-ciclo/${batchId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ruolo_utente: "Operatore"
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella terminazione del batch')
      }

      const result = await response.json()
      
      if (result.success) {
        await loadBatchAutomatici()
        toast({
          title: "Batch terminato",
          description: result.message,
        })
      } else {
        throw new Error(result.error || 'Errore nella terminazione del batch')
      }
    } catch (error) {
      toast({
        title: "Errore",
        description: error instanceof Error ? error.message : "Impossibile terminare il batch.",
        variant: "destructive",
      })
    }
  }

  // Funzione per navigare al nesting automatico
  const handleCreateAutoMulti = () => {
    router.push('/dashboard/curing/nesting/auto-multi')
  }

  // Render del contenuto del workflow
  const renderWorkflowContent = () => {
    if (!workflow.mode) {
      return (
        <div className="space-y-6">
          <NestingModeSelector 
            onModeSelect={handleModeSelect}
            className="max-w-6xl mx-auto"
          />
          
          {/* Sezione Nesting Automatico Multi-Autoclave */}
          <Card className="max-w-6xl mx-auto border-2 border-blue-200 bg-blue-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-800">
                <Zap className="h-6 w-6" />
                Nesting Multi-Autoclave Automatico
              </CardTitle>
              <CardDescription className="text-blue-700">
                Genera automaticamente il nesting ottimale distribuendo gli ODL su più autoclavi disponibili.
                Ideale per grandi volumi di produzione e massimizzazione dell'efficienza.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-4 text-sm text-blue-700">
                    <span>✓ Ottimizzazione automatica</span>
                    <span>✓ Multi-autoclave</span>
                    <span>✓ Separazione cicli di cura</span>
                    <span>✓ Preview completo</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Seleziona gli ODL, configura i parametri e lascia che l'algoritmo generi il layout ottimale.
                  </p>
                </div>
                <Button 
                  onClick={handleCreateAutoMulti}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Avvia Nesting Automatico
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
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

    if (activeTab === 'auto-multi') {
      return (
        <AutoMultiBatchTable
          batches={batchAutomatici}
          onRefresh={loadBatchAutomatici}
          onTerminateBatch={handleTerminateBatch}
          onCreateNew={handleCreateAutoMulti}
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
              : activeTab === 'auto-multi' ? 'Nesting Automatico Multi-Autoclave'
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
            onClick={loadAllData}
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
            onClick={() => setActiveTab('auto-multi')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'auto-multi'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
            }`}
          >
            <Zap className="h-4 w-4 mr-1 inline" />
            Automatico Multi
            {batchAutomatici.filter(b => b.stato === 'Pronto' || b.stato === 'In Esecuzione').length > 0 && (
              <span className="ml-2 bg-blue-600 text-white rounded-full px-2 py-0.5 text-xs">
                {batchAutomatici.filter(b => b.stato === 'Pronto' || b.stato === 'In Esecuzione').length}
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
              Errore nel Workflow
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {workflow.steps
                .filter(step => step.status === 'error')
                .map(step => (
                  <p key={step.id} className="text-red-700 text-sm">
                    <strong>{step.title}:</strong> {workflow.workflowData[`${step.id}_error`] || 'Errore sconosciuto'}
                  </p>
                ))}
            </div>
            <Button 
              variant="outline" 
              onClick={handleBackToModeSelection}
              className="mt-4"
            >
              Ricomincia
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 