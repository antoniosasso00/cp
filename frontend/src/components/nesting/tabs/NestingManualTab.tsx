'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, CheckCircle } from 'lucide-react'
import { NestingTable } from '@/components/nesting/NestingTable'
import { EmptyState } from '@/components/ui/EmptyState'
import { nestingApi, NestingResponse } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import { Package } from 'lucide-react'
import { NestingStep1Autoclave } from '@/components/nesting/manual/NestingStep1Autoclave'
import { NestingStep2ODLSelection } from '@/components/nesting/manual/NestingStep2ODLSelection'
import { ManualNestingOrchestrator } from '../manual/ManualNestingOrchestrator'
import { ConfirmationResults } from '../manual/NestingStep5Confirmation'

interface NestingManualTabProps {
  nestingList: NestingResponse[]
  isLoading: boolean
  onRefresh: () => Promise<void>
  onStepComplete?: (data: any) => void
  onStepError?: (error: string) => void
  currentStep?: string
}

export function NestingManualTab({ 
  nestingList, 
  isLoading, 
  onRefresh,
  onStepComplete,
  onStepError,
  currentStep 
}: NestingManualTabProps) {
  const [isInWorkflow, setIsInWorkflow] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Gestisce l'avvio del workflow di nesting manuale
  const handleStartManualWorkflow = () => {
    setIsInWorkflow(true)
    setError(null)
    
    toast({
      title: "Nesting Manuale Avviato",
      description: "Segui i 5 step guidati per completare il nesting"
    })
  }

  // Gestisce il completamento del workflow
  const handleWorkflowComplete = async (results: ConfirmationResults) => {
    try {
      // Aggiorna la lista dei nesting
      await onRefresh()
      
      // Torna alla vista principale
      setIsInWorkflow(false)
      
      // Notifica il completamento del workflow se siamo in modalità step
      if (onStepComplete) {
        onStepComplete({
          workflow_completed: true,
          nesting_id: results.nesting_id,
          odl_processed: results.odl_status_changed,
          autoclave_loaded: true
        })
      }
      
      toast({
        title: "Workflow Completato!",
        description: `Nesting #${results.nesting_id} confermato e caricato in autoclave`
      })
    } catch (error) {
      console.error('❌ Errore completamento workflow:', error)
      setError('Errore durante il completamento del workflow')
      
      if (onStepError) {
        onStepError('Errore durante il completamento del workflow')
      }
    }
  }

  // Gestisce la cancellazione del workflow
  const handleWorkflowCancel = () => {
    setIsInWorkflow(false)
    
    toast({
      title: "Workflow Annullato",
      description: "Puoi ricominciare quando vuoi"
    })
  }

  // Se siamo nel workflow, mostra l'orchestratore
  if (isInWorkflow) {
    return (
      <ManualNestingOrchestrator
        onComplete={handleWorkflowComplete}
        onCancel={handleWorkflowCancel}
        className="container mx-auto max-w-7xl"
      />
    )
  }

  // Altrimenti mostra la vista principale con la lista dei nesting
  return (
    <Card data-tab-content="nesting-manual">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Nesting Manuale
        </CardTitle>
        <CardDescription>
          Crea nesting personalizzati tramite workflow guidato in 5 step.
          Controllo completo su selezione ODL, autoclave e layout finale.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Errori */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Errore</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Workflow Step Integration */}
        {currentStep && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Modalità Workflow Attiva</AlertTitle>
            <AlertDescription>
              Step corrente: {currentStep}. Utilizza il pulsante qui sotto per procedere con il nesting manuale.
            </AlertDescription>
          </Alert>
        )}

        {/* Azione principale */}
        <div className="flex items-center justify-between p-6 border border-dashed border-gray-300 rounded-lg bg-gray-50">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Nuovo Nesting Manuale
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Workflow guidato in 5 step: ODL → Autoclave → Layout → Validazione → Caricamento
            </p>
            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
              <span>✅ Controllo completo</span>
              <span>✅ Prevenzione conflitti</span>
              <span>✅ Validazione automatica</span>
              <span>✅ Salvataggio progresso</span>
            </div>
          </div>
          
          <Button
            onClick={handleStartManualWorkflow}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
            size="lg"
            data-nesting-action="start-manual"
          >
            <Plus className="h-5 w-5" />
            Avvia Nesting Manuale
          </Button>
        </div>

        {/* Lista nesting esistenti */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Nesting Esistenti</h3>
          
          {!isLoading && nestingList.length === 0 ? (
            <div className="text-center py-8 text-gray-500" data-odl-list>
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Nessun nesting disponibile</p>
              <p className="text-sm">Crea il primo nesting manuale utilizzando il pulsante sopra.</p>
            </div>
          ) : (
            <div data-odl-list>
              <NestingTable 
                data={nestingList} 
                isLoading={isLoading}
                onRefresh={onRefresh}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
} 