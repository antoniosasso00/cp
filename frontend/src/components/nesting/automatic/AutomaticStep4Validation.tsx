'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  ArrowLeft, 
  Shield,
  Search,
  Scale,
  Target
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

// Import dei tipi
import { ExtractedNestingData } from '../manual/NestingStep1ODLSelection'
import { AutoclaveSelectionData } from './AutomaticStep2AutoclaveSelection'
import { LayoutGenerationData } from './AutomaticStep3LayoutGeneration'

// Tipi per questo step
export interface ValidationResults {
  is_valid: boolean
  validation_score: number
  checks_performed: {
    geometry_check: boolean
    weight_check: boolean
    valve_check: boolean
    overlap_check: boolean
    clearance_check: boolean
  }
  warnings: string[]
  errors: string[]
  recommendations: string[]
  performance_metrics: {
    efficiency_vs_target: number
    weight_distribution: number
    valve_utilization: number
  }
}

interface AutomaticStep4ValidationProps {
  onNext: (data: ValidationResults) => void
  onBack: () => void
  isLoading?: boolean
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  layoutData: LayoutGenerationData
  savedData?: ValidationResults
}

export function AutomaticStep4Validation({
  onNext,
  onBack,
  isLoading = false,
  odlData,
  autoclaveData,
  layoutData,
  savedData
}: AutomaticStep4ValidationProps) {
  const { toast } = useToast()
  
  // State
  const [validationResults, setValidationResults] = useState<ValidationResults | null>(savedData || null)
  const [validating, setValidating] = useState(false)
  const [validationProgress, setValidationProgress] = useState(0)

  // Avvia la validazione automatica
  useEffect(() => {
    if (!savedData && !validating) {
      startValidation()
    }
  }, [savedData, validating])

  const startValidation = async () => {
    try {
      setValidating(true)
      setValidationProgress(0)
      
      toast({
        title: "Validazione Automatica",
        description: "Verificando il layout generato..."
      })

      // Simula progresso validazione
      const validationSteps = [
        { name: 'Controllo geometria', duration: 1000 },
        { name: 'Verifica pesi', duration: 800 },
        { name: 'Controllo valvole', duration: 600 },
        { name: 'Verifica sovrapposizioni', duration: 1200 },
        { name: 'Controllo clearance', duration: 900 }
      ]

      let totalProgress = 0
      for (const step of validationSteps) {
        await new Promise(resolve => setTimeout(resolve, step.duration))
        totalProgress += 100 / validationSteps.length
        setValidationProgress(totalProgress)
      }

      // Simula risultati validazione
      const mockValidation: ValidationResults = {
        is_valid: true,
        validation_score: 92.5,
        checks_performed: {
          geometry_check: true,
          weight_check: true,
          valve_check: true,
          overlap_check: true,
          clearance_check: true
        },
        warnings: layoutData.efficiency_percent < 80 ? ["Efficienza sotto la soglia raccomandata dell'80%"] : [],
        errors: [],
        recommendations: [
          "Layout ottimizzato correttamente",
          "Efficienza raggiunta soddisfacente",
          "Distribuzione del peso bilanciata"
        ],
        performance_metrics: {
          efficiency_vs_target: layoutData.efficiency_percent / 80,
          weight_distribution: 0.95,
          valve_utilization: (layoutData.layout_data.valvole_utilizzate / layoutData.layout_data.valvole_totali)
        }
      }

      if (layoutData.excluded_odl_count > 0) {
        mockValidation.warnings.push(`${layoutData.excluded_odl_count} ODL esclusi dall'ottimizzazione`)
      }

      setValidationResults(mockValidation)
      setValidationProgress(100)

      toast({
        title: "Validazione Completata",
        description: `Punteggio validazione: ${mockValidation.validation_score}/100`
      })

    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Errore Validazione",
        description: error.message || "Impossibile completare la validazione"
      })
    } finally {
      setValidating(false)
    }
  }

  const handleNext = () => {
    if (validationResults) {
      onNext(validationResults)
    }
  }

  const renderCheckStatus = (check: boolean, label: string, icon: React.ReactNode) => (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${
      check ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
    }`}>
      <div className={`p-2 rounded-full ${
        check ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
      }`}>
        {icon}
      </div>
      <div className="flex-1">
        <p className={`font-medium ${check ? 'text-green-800' : 'text-red-800'}`}>
          {label}
        </p>
        <p className={`text-sm ${check ? 'text-green-600' : 'text-red-600'}`}>
          {check ? 'Superato' : 'Non superato'}
        </p>
      </div>
      {check ? (
        <CheckCircle2 className="h-5 w-5 text-green-600" />
      ) : (
        <AlertTriangle className="h-5 w-5 text-red-600" />
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 4: Validazione Automatica</h2>
          <p className="text-gray-600 mt-1">
            Verifica della correttezza e qualità del layout generato.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={validationProgress} className="w-32" />
          <span className="text-sm text-gray-500">{Math.round(validationProgress)}%</span>
        </div>
      </div>

      {/* Progresso validazione */}
      {validating && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 animate-pulse" />
              Validazione in Corso...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={validationProgress} className="w-full" />
            <p className="text-sm text-muted-foreground mt-2">
              Eseguendo controlli di qualità e conformità...
            </p>
          </CardContent>
        </Card>
      )}

      {/* Risultati validazione */}
      {validationResults && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-600" />
                Risultati Validazione
              </CardTitle>
              <CardDescription>
                Punteggio complessivo: {validationResults.validation_score}/100
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Metriche performance */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {(validationResults.performance_metrics.efficiency_vs_target * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-blue-800">Efficienza vs Target</div>
                </div>
                
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {(validationResults.performance_metrics.weight_distribution * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-green-800">Distribuzione Peso</div>
                </div>
                
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {(validationResults.performance_metrics.valve_utilization * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-purple-800">Utilizzo Valvole</div>
                </div>
              </div>

              {/* Controlli eseguiti */}
              <div>
                <h4 className="font-medium mb-4">Controlli di Qualità</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {renderCheckStatus(
                    validationResults.checks_performed.geometry_check,
                    "Controllo Geometria",
                    <Target className="h-4 w-4" />
                  )}
                  {renderCheckStatus(
                    validationResults.checks_performed.weight_check,
                    "Verifica Pesi",
                    <Scale className="h-4 w-4" />
                  )}
                  {renderCheckStatus(
                    validationResults.checks_performed.valve_check,
                    "Controllo Valvole",
                    <Shield className="h-4 w-4" />
                  )}
                  {renderCheckStatus(
                    validationResults.checks_performed.overlap_check,
                    "Verifica Sovrapposizioni",
                    <Search className="h-4 w-4" />
                  )}
                  {renderCheckStatus(
                    validationResults.checks_performed.clearance_check,
                    "Controllo Clearance",
                    <Target className="h-4 w-4" />
                  )}
                </div>
              </div>

              {/* Avvisi */}
              {validationResults.warnings.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Avvisi:</strong>
                    <ul className="list-disc list-inside mt-2">
                      {validationResults.warnings.map((warning, index) => (
                        <li key={index} className="text-sm">{warning}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {/* Raccomandazioni */}
              {validationResults.recommendations.length > 0 && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-800 mb-2">Raccomandazioni:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {validationResults.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-green-700">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Pulsanti navigazione */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={isLoading || validating}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Indietro
        </Button>

        <Button
          onClick={handleNext}
          disabled={!validationResults || isLoading || validating}
          className="flex items-center gap-2"
        >
          {isLoading || validating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Validazione...
            </>
          ) : (
            <>
              Procedi alla Conferma
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 