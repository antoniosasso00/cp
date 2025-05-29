'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  CheckCircle2, 
  ArrowLeft, 
  Save, 
  FileCheck,
  Calendar,
  User,
  Clock,
  Target
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

// Import dei tipi
import { ExtractedNestingData } from '../manual/NestingStep1ODLSelection'
import { AutoclaveSelectionData } from './AutomaticStep2AutoclaveSelection'
import { LayoutGenerationData } from './AutomaticStep3LayoutGeneration'
import { ValidationResults } from './AutomaticStep4Validation'

// Tipi per questo step
export interface ConfirmationResults {
  nesting_id: number
  confirmed_at: string
  confirmed_by: string
  confirmation_notes: string
  final_status: string
  summary: {
    total_odl_included: number
    total_odl_excluded: number
    final_efficiency: number
    autoclave_assigned: string
    estimated_cure_time: string
  }
}

interface AutomaticStep5ConfirmationProps {
  onNext: (data: ConfirmationResults) => void
  onBack: () => void
  isLoading?: boolean
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  layoutData: LayoutGenerationData
  validationData: ValidationResults
  savedData?: ConfirmationResults
}

export function AutomaticStep5Confirmation({
  onNext,
  onBack,
  isLoading = false,
  odlData,
  autoclaveData,
  layoutData,
  validationData,
  savedData
}: AutomaticStep5ConfirmationProps) {
  const { toast } = useToast()
  
  // State
  const [notes, setNotes] = useState(savedData?.confirmation_notes || '')
  const [confirming, setConfirming] = useState(false)

  // Calcola il riepilogo finale
  const finalSummary = {
    total_odl_included: odlData.selected_odl_ids.length - layoutData.excluded_odl_count,
    total_odl_excluded: layoutData.excluded_odl_count,
    final_efficiency: layoutData.efficiency_percent,
    autoclave_assigned: autoclaveData.selected_autoclave.nome,
    estimated_cure_time: '4h 30m' // Mockup - da calcolare in base al ciclo di cura
  }

  const handleConfirm = async () => {
    try {
      setConfirming(true)
      
      toast({
        title: "Conferma Nesting",
        description: "Salvando il nesting automatico generato..."
      })

      // Simula il salvataggio (in futuro userà nestingApi.confirm())
      await new Promise(resolve => setTimeout(resolve, 2000))

      const confirmationResult: ConfirmationResults = {
        nesting_id: Math.floor(Math.random() * 10000) + 1000,
        confirmed_at: new Date().toISOString(),
        confirmed_by: 'Sistema Automatico',
        confirmation_notes: notes,
        final_status: 'confermato',
        summary: finalSummary
      }

      toast({
        title: "Nesting Confermato!",
        description: `Nesting #${confirmationResult.nesting_id} salvato con successo`
      })

      onNext(confirmationResult)

    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Errore Conferma",
        description: error.message || "Impossibile confermare il nesting"
      })
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 5: Conferma Finale</h2>
          <p className="text-gray-600 mt-1">
            Riepilogo e conferma del nesting automatico generato.
          </p>
        </div>
        
        <Badge className="bg-green-100 text-green-800">
          Pronto per la Conferma
        </Badge>
      </div>

      {/* Riepilogo finale */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCheck className="h-5 w-5" />
            Riepilogo Nesting Automatico
          </CardTitle>
          <CardDescription>
            Tutti i controlli sono stati superati con successo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Statistiche principali */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {finalSummary.total_odl_included}
              </div>
              <div className="text-sm text-blue-800">ODL Inclusi</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {finalSummary.final_efficiency.toFixed(1)}%
              </div>
              <div className="text-sm text-green-800">Efficienza Finale</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {validationData.validation_score.toFixed(0)}
              </div>
              <div className="text-sm text-purple-800">Punteggio Validazione</div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {finalSummary.estimated_cure_time}
              </div>
              <div className="text-sm text-orange-800">Tempo Stimato</div>
            </div>
          </div>

          {/* Dettagli configurazione */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Configurazione Nesting</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Autoclave Assegnata:</span>
                  <span className="text-sm text-gray-700">{finalSummary.autoclave_assigned}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Algoritmo Utilizzato:</span>
                  <span className="text-sm text-gray-700">{layoutData.optimization_results.algorithm_used}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Tempo Generazione:</span>
                  <span className="text-sm text-gray-700">
                    {(layoutData.optimization_results.generation_time_ms / 1000).toFixed(1)}s
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Iterazioni OR-Tools:</span>
                  <span className="text-sm text-gray-700">{layoutData.optimization_results.iterations_performed}</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Risultati Ottimizzazione</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Area Utilizzata:</span>
                  <span className="text-sm text-gray-700">
                    {layoutData.layout_data.area_utilizzata.toFixed(0)} / {layoutData.layout_data.area_totale.toFixed(0)} cm²
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Valvole Utilizzate:</span>
                  <span className="text-sm text-gray-700">
                    {layoutData.layout_data.valvole_utilizzate} / {layoutData.layout_data.valvole_totali}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Cicli di Cura:</span>
                  <span className="text-sm text-gray-700">
                    {odlData.cicli_cura_coinvolti.join(', ')}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Convergenza:</span>
                  <Badge className={layoutData.optimization_results.convergence_achieved ? 
                    "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                    {layoutData.optimization_results.convergence_achieved ? "Raggiunta" : "Parziale"}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Avvisi finali */}
          {(validationData.warnings.length > 0 || layoutData.excluded_odl_count > 0) && (
            <Alert>
              <Target className="h-4 w-4" />
              <AlertDescription>
                <strong>Note Finali:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  {layoutData.excluded_odl_count > 0 && (
                    <li className="text-sm">
                      {layoutData.excluded_odl_count} ODL esclusi dall'ottimizzazione automatica
                    </li>
                  )}
                  {validationData.warnings.map((warning, index) => (
                    <li key={index} className="text-sm">{warning}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Note di conferma */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Note di Conferma
          </CardTitle>
          <CardDescription>
            Aggiungi note opzionali per la conferma del nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="Inserisci note aggiuntive per questo nesting automatico (opzionale)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="w-full"
          />
        </CardContent>
      </Card>

      {/* Informazioni timestamp */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>Generato automaticamente il {new Date().toLocaleString('it-IT')}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <span>Tempo totale: {(layoutData.optimization_results.generation_time_ms / 1000 + 6).toFixed(1)}s</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pulsanti navigazione */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={confirming}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Indietro
        </Button>

        <Button
          onClick={handleConfirm}
          disabled={confirming}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
        >
          {confirming ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Confermando...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Conferma Nesting Automatico
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 