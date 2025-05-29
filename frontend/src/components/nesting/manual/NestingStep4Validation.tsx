'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  ArrowRight, 
  ArrowLeft,
  Package,
  Factory,
  Layers,
  Target,
  Clock,
  TrendingUp,
  AlertCircle,
  FileCheck
} from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { ExtractedNestingData } from './NestingStep1ODLSelection'
import { AutoclaveSelectionData } from './NestingStep2AutoclaveSelection'
import { LayoutCanvasData } from '../layout/NestingDragDropCanvas'

export interface ValidationResults {
  is_valid: boolean
  critical_errors: string[]
  warnings: string[]
  suggestions: string[]
  efficiency_metrics: {
    overall_score: number
    area_efficiency: number
    weight_efficiency: number
    cycle_separation_score: number
    time_optimization_score: number
  }
  ready_for_confirmation: boolean
}

interface NestingStep4ValidationProps {
  odlData: ExtractedNestingData
  autoclaveData: AutoclaveSelectionData
  layoutData: LayoutCanvasData
  onNext: (validation: ValidationResults) => void
  onBack: () => void
  isLoading?: boolean
}

// Funzione per calcolare i risultati di validazione
const performValidation = (
  odlData: ExtractedNestingData,
  autoclaveData: AutoclaveSelectionData,
  layoutData: LayoutCanvasData
): ValidationResults => {
  const critical_errors: string[] = []
  const warnings: string[] = []
  const suggestions: string[] = []
  
  // ✅ VALIDAZIONE CRITICA: Conflitti cicli di cura
  if (layoutData.validation_results.has_conflicts) {
    critical_errors.push("Conflitti tra ODL di cicli di cura diversi: separare fisicamente i tool")
  }
  
  // ✅ VALIDAZIONE: Efficienza area
  const area_efficiency = layoutData.validation_results.coverage_percentage
  if (area_efficiency < 30) {
    warnings.push(`Bassa efficienza area (${area_efficiency.toFixed(1)}%): considerare autoclave più piccola`)
  } else if (area_efficiency > 85) {
    warnings.push(`Efficienza area molto alta (${area_efficiency.toFixed(1)}%): verificare spazio manovra`)
  }
  
  // ✅ VALIDAZIONE: Peso autoclave
  const weight_efficiency = (odlData.peso_totale_kg / (autoclaveData.autoclave_data.max_load_kg || 1000)) * 100
  if (weight_efficiency > 80) {
    warnings.push(`Carico pesante (${weight_efficiency.toFixed(1)}%): verificare stabilità`)
  }
  
  // ✅ VALIDAZIONE: Valvole
  const valvole_utilizzate = odlData.valvole_richieste
  const valvole_totali = autoclaveData.autoclave_data.num_linee_vuoto
  if (valvole_utilizzate > valvole_totali) {
    critical_errors.push(`Valvole insufficienti: richieste ${valvole_utilizzate}, disponibili ${valvole_totali}`)
  } else if (valvole_utilizzate === valvole_totali) {
    warnings.push("Tutte le valvole utilizzate: nessun margine di sicurezza")
  }
  
  // ✅ SUGGERIMENTI
  if (area_efficiency < 50) {
    suggestions.push("Considerare di aggiungere altri ODL per ottimizzare l'autoclavata")
  }
  
  if (layoutData.final_positions.some(p => p.piano === 2)) {
    suggestions.push("Nesting su due piani: verificare stabilità e procedure di caricamento")
  }
  
  if (odlData.priorita_media >= 7) {
    suggestions.push("ODL ad alta priorità: considerare accelerazione del processo")
  }
  
  // ✅ CALCOLO METRICHE
  const efficiency_metrics = {
    overall_score: layoutData.validation_results.efficiency_score,
    area_efficiency: area_efficiency,
    weight_efficiency: weight_efficiency,
    cycle_separation_score: layoutData.validation_results.cycle_separation_ok ? 100 : 0,
    time_optimization_score: Math.min(100, (odlData.priorita_media / 10) * 100)
  }
  
  const is_valid = critical_errors.length === 0
  const ready_for_confirmation = is_valid && warnings.length <= 2
  
  return {
    is_valid,
    critical_errors,
    warnings,
    suggestions,
    efficiency_metrics,
    ready_for_confirmation
  }
}

// Componente per una metrica di efficienza
interface MetricCardProps {
  title: string
  value: number
  unit: string
  icon: React.ReactNode
  color: 'green' | 'yellow' | 'red' | 'blue'
  description?: string
}

function MetricCard({ title, value, unit, icon, color, description }: MetricCardProps) {
  const colorClasses = {
    green: 'bg-green-50 text-green-800 border-green-200',
    yellow: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    red: 'bg-red-50 text-red-800 border-red-200',
    blue: 'bg-blue-50 text-blue-800 border-blue-200'
  }
  
  return (
    <div className={cn("p-4 rounded-lg border-2", colorClasses[color])}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-sm">{title}</span>
        </div>
      </div>
      <div className="text-2xl font-bold mb-1">
        {value.toFixed(1)}{unit}
      </div>
      {description && (
        <div className="text-xs opacity-80">{description}</div>
      )}
    </div>
  )
}

export function NestingStep4Validation({ 
  odlData, 
  autoclaveData, 
  layoutData, 
  onNext, 
  onBack, 
  isLoading = false 
}: NestingStep4ValidationProps) {
  const { toast } = useToast()
  const [validationResults, setValidationResults] = useState<ValidationResults | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Esegui validazione all'avvio
  useEffect(() => {
    executeValidation()
  }, [odlData, autoclaveData, layoutData])

  const executeValidation = async () => {
    setIsValidating(true)
    
    // Simula elaborazione (in realtà potresti chiamare API backend)
    setTimeout(() => {
      const results = performValidation(odlData, autoclaveData, layoutData)
      setValidationResults(results)
      setIsValidating(false)
      
      if (results.critical_errors.length > 0) {
        toast({
          variant: "destructive",
          title: "Errori critici rilevati",
          description: "Correggere gli errori prima di procedere"
        })
      } else if (results.warnings.length > 0) {
        toast({
          title: "Validazione completata con avvisi",
          description: "Verificare i warnings evidenziati"
        })
      } else {
        toast({
          title: "Validazione superata",
          description: "Layout pronto per la conferma"
        })
      }
    }, 1500)
  }

  const handleNext = () => {
    if (validationResults && validationResults.ready_for_confirmation) {
      onNext(validationResults)
    }
  }

  if (isValidating || !validationResults) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Step 4: Validazione Finale</h2>
            <p className="text-gray-600 mt-1">
              Validazione in corso del layout e delle configurazioni...
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <Progress value={75} className="w-32" />
            <span className="text-sm text-gray-500">75%</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 animate-pulse" />
              Validazione in corso...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3">Analisi layout e compatibilità...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const getOverallStatusColor = () => {
    if (validationResults.critical_errors.length > 0) return 'red'
    if (validationResults.warnings.length > 2) return 'yellow'
    return 'green'
  }

  const getOverallStatusIcon = () => {
    if (validationResults.critical_errors.length > 0) return <AlertTriangle className="h-6 w-6" />
    if (validationResults.warnings.length > 0) return <AlertCircle className="h-6 w-6" />
    return <CheckCircle2 className="h-6 w-6" />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 4: Validazione Finale</h2>
          <p className="text-gray-600 mt-1">
            Verifica finale del layout prima della conferma del nesting
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={validationResults.ready_for_confirmation ? 100 : 85} className="w-32" />
          <span className="text-sm text-gray-500">
            {validationResults.ready_for_confirmation ? 100 : 85}%
          </span>
        </div>
      </div>

      {/* Stato generale validazione */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getOverallStatusIcon()}
            Stato Validazione
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={cn(
            "p-4 rounded-lg border-2",
            getOverallStatusColor() === 'green' && "bg-green-50 border-green-200",
            getOverallStatusColor() === 'yellow' && "bg-yellow-50 border-yellow-200", 
            getOverallStatusColor() === 'red' && "bg-red-50 border-red-200"
          )}>
            <div className="text-lg font-medium mb-2">
              {validationResults.ready_for_confirmation ? (
                "✅ Layout validato e pronto per conferma"
              ) : validationResults.is_valid ? (
                "⚠️ Layout valido con avvisi"
              ) : (
                "❌ Layout non valido - correzioni richieste"
              )}
            </div>
            <div className="text-sm opacity-80">
              {validationResults.critical_errors.length > 0 && (
                <span>Errori critici: {validationResults.critical_errors.length} • </span>
              )}
              Avvisi: {validationResults.warnings.length} • 
              Suggerimenti: {validationResults.suggestions.length}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metriche di efficienza */}
      <Card>
        <CardHeader>
          <CardTitle>Metriche di Efficienza</CardTitle>
          <CardDescription>
            Analisi delle prestazioni del layout configurato
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <MetricCard
              title="Punteggio Generale"
              value={validationResults.efficiency_metrics.overall_score}
              unit="%"
              icon={<TrendingUp className="h-4 w-4" />}
              color={validationResults.efficiency_metrics.overall_score >= 70 ? 'green' : 
                     validationResults.efficiency_metrics.overall_score >= 50 ? 'yellow' : 'red'}
              description="Efficienza complessiva"
            />
            
            <MetricCard
              title="Efficienza Area"
              value={validationResults.efficiency_metrics.area_efficiency}
              unit="%"
              icon={<Target className="h-4 w-4" />}
              color={validationResults.efficiency_metrics.area_efficiency >= 60 ? 'green' : 
                     validationResults.efficiency_metrics.area_efficiency >= 40 ? 'yellow' : 'red'}
              description="Utilizzo spazio autoclave"
            />
            
            <MetricCard
              title="Carico Peso"
              value={validationResults.efficiency_metrics.weight_efficiency}
              unit="%"
              icon={<Package className="h-4 w-4" />}
              color={validationResults.efficiency_metrics.weight_efficiency <= 80 ? 'green' : 
                     validationResults.efficiency_metrics.weight_efficiency <= 90 ? 'yellow' : 'red'}
              description="Utilizzo capacità peso"
            />
            
            <MetricCard
              title="Separazione Cicli"
              value={validationResults.efficiency_metrics.cycle_separation_score}
              unit="%"
              icon={<Layers className="h-4 w-4" />}
              color={validationResults.efficiency_metrics.cycle_separation_score === 100 ? 'green' : 'red'}
              description="Compatibilità cicli cura"
            />
            
            <MetricCard
              title="Ottimizzazione Tempi"
              value={validationResults.efficiency_metrics.time_optimization_score}
              unit="%"
              icon={<Clock className="h-4 w-4" />}
              color="blue"
              description="Priorità e tempistiche"
            />
          </div>
        </CardContent>
      </Card>

      {/* Errori critici */}
      {validationResults.critical_errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Errori Critici ({validationResults.critical_errors.length})
            </CardTitle>
            <CardDescription>
              Questi errori devono essere risolti prima di procedere
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {validationResults.critical_errors.map((error, index) => (
                <Alert key={index} variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Avvisi */}
      {validationResults.warnings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-600">
              <AlertCircle className="h-5 w-5" />
              Avvisi ({validationResults.warnings.length})
            </CardTitle>
            <CardDescription>
              Situazioni che richiedono attenzione
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {validationResults.warnings.map((warning, index) => (
                <Alert key={index}>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{warning}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Suggerimenti */}
      {validationResults.suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-600">
              <Info className="h-5 w-5" />
              Suggerimenti ({validationResults.suggestions.length})
            </CardTitle>
            <CardDescription>
              Raccomandazioni per ottimizzare il nesting
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {validationResults.suggestions.map((suggestion, index) => (
                <Alert key={index}>
                  <Info className="h-4 w-4" />
                  <AlertDescription>{suggestion}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pulsanti navigazione */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={onBack}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Torna al Layout Canvas
        </Button>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={executeValidation}
            disabled={isValidating}
          >
            Rivalida Layout
          </Button>
          
          <Button
            onClick={handleNext}
            disabled={!validationResults.ready_for_confirmation || isLoading}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Elaborazione...
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
    </div>
  )
} 