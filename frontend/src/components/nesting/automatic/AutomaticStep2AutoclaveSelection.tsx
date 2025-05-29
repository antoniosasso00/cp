'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft, 
  Cpu, 
  Gauge, 
  Thermometer,
  Scale,
  Zap,
  Clock
} from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

// Import API e tipi
import { autoclaveApi, Autoclave } from '@/lib/api'
import { ExtractedNestingData } from '../manual/NestingStep1ODLSelection'

// Tipi per questo step
export interface AutoclaveSelectionData {
  selected_autoclave: Autoclave
  compatibility_score: number
  selection_criteria: {
    peso_compatibile: boolean
    area_compatibile: boolean
    valvole_compatibili: boolean
    cicli_compatibili: boolean
  }
  alternative_autoclaves: Autoclave[]
  auto_selection_reason: string
}

interface AutomaticStep2AutoclaveSelectionProps {
  onNext: (data: AutoclaveSelectionData) => void
  onBack: () => void
  isLoading?: boolean
  odlData: ExtractedNestingData
  savedData?: AutoclaveSelectionData
}

export function AutomaticStep2AutoclaveSelection({
  onNext,
  onBack,
  isLoading = false,
  odlData,
  savedData
}: AutomaticStep2AutoclaveSelectionProps) {
  const { toast } = useToast()
  
  // State
  const [autoclaveList, setAutoclaveList] = useState<Autoclave[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAutoclave, setSelectedAutoclave] = useState<Autoclave | null>(savedData?.selected_autoclave || null)
  const [compatibilityAnalysis, setCompatibilityAnalysis] = useState<AutoclaveSelectionData | null>(savedData || null)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  // Carica le autoclavi disponibili
  useEffect(() => {
    loadAutoclaveData()
  }, [])

  // Avvia l'analisi automatica quando i dati sono caricati
  useEffect(() => {
    if (autoclaveList.length > 0 && !savedData) {
      performAutomaticSelection()
    }
  }, [autoclaveList, savedData])

  const loadAutoclaveData = async () => {
    try {
      setLoading(true)
      const response = await autoclaveApi.getAll()
      
      // Filtra solo autoclavi disponibili
      const availableAutoclaves = response.filter(autoclave => 
        autoclave.stato === 'DISPONIBILE'
      )
      
      setAutoclaveList(availableAutoclaves)
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore caricamento autoclavi",
        description: "Non è stato possibile caricare la lista delle autoclavi disponibili"
      })
    } finally {
      setLoading(false)
    }
  }

  // Logica di selezione automatica
  const performAutomaticSelection = async () => {
    try {
      setAnalysisProgress(10)
      toast({
        title: "Analisi Automatica in Corso",
        description: "Sto analizzando la compatibilità delle autoclavi..."
      })

      // Simula progresso dell'analisi
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => Math.min(prev + 15, 90))
      }, 300)

      // Analizza ogni autoclave per compatibilità
      const analysisResults = autoclaveList.map(autoclave => {
        const analysis = analyzeCompatibility(autoclave, odlData)
        return {
          autoclave,
          ...analysis
        }
      })

      // Ordina per punteggio di compatibilità (decrescente)
      analysisResults.sort((a, b) => b.compatibility_score - a.compatibility_score)

      // Seleziona la migliore
      const bestAutoclave = analysisResults[0]
      
      if (!bestAutoclave || bestAutoclave.compatibility_score < 60) {
        throw new Error("Nessuna autoclave compatibile trovata con i requisiti minimi")
      }

      clearInterval(progressInterval)
      setAnalysisProgress(100)

      const selectionData: AutoclaveSelectionData = {
        selected_autoclave: bestAutoclave.autoclave,
        compatibility_score: bestAutoclave.compatibility_score,
        selection_criteria: bestAutoclave.selection_criteria,
        alternative_autoclaves: analysisResults.slice(1, 4).map(r => r.autoclave),
        auto_selection_reason: generateSelectionReason(bestAutoclave)
      }

      setSelectedAutoclave(bestAutoclave.autoclave)
      setCompatibilityAnalysis(selectionData)

      setTimeout(() => {
        toast({
          title: "Selezione Automatica Completata",
          description: `Autoclave ${bestAutoclave.autoclave.nome} selezionata automaticamente (Compatibilità: ${bestAutoclave.compatibility_score}%)`
        })
      }, 500)

    } catch (error: any) {
      setAnalysisProgress(0)
      toast({
        variant: "destructive",
        title: "Errore nell'Analisi Automatica",
        description: error.message || "Impossibile completare l'analisi automatica"
      })
    }
  }

  // Analizza la compatibilità di un'autoclave con gli ODL
  const analyzeCompatibility = (autoclave: Autoclave, odlData: ExtractedNestingData) => {
    let score = 0
    const criteria = {
      peso_compatibile: false,
      area_compatibile: false,
      valvole_compatibili: false,
      cicli_compatibili: false
    }

    // Controllo peso (30% del punteggio)
    const peso_max = autoclave.max_load_kg || 1000 // Fallback per peso massimo
    if (peso_max >= odlData.peso_totale_kg) {
      criteria.peso_compatibile = true
      score += 30
      
      // Bonus se il peso è nell'80% della capacità (utilizzo ottimale)
      const utilizzo_peso = (odlData.peso_totale_kg / peso_max) * 100
      if (utilizzo_peso >= 60 && utilizzo_peso <= 85) {
        score += 10
      }
    }

    // Controllo area piano (25% del punteggio)
    const area_autoclave_cm2 = (autoclave.lunghezza * autoclave.larghezza_piano) / 100
    if (area_autoclave_cm2 >= odlData.area_totale_cm2) {
      criteria.area_compatibile = true
      score += 25
      
      // Bonus per efficienza area
      const utilizzo_area = (odlData.area_totale_cm2 / area_autoclave_cm2) * 100
      if (utilizzo_area >= 50 && utilizzo_area <= 90) {
        score += 15
      }
    }

    // Controllo valvole (20% del punteggio)
    const valvole_disponibili = autoclave.num_linee_vuoto || 0
    if (valvole_disponibili >= odlData.valvole_richieste) {
      criteria.valvole_compatibili = true
      score += 20
    }

    // Controllo cicli di cura (25% del punteggio)
    // Per ora, consideriamo tutti i cicli compatibili (da migliorare in futuro)
    // TODO: Implementare logica di compatibilità cicli quando sarà disponibile nel backend
    if (odlData.cicli_cura_coinvolti.length > 0) {
      criteria.cicli_compatibili = true
      score += 25
    }

    return {
      compatibility_score: Math.min(score, 100),
      selection_criteria: criteria
    }
  }

  // Genera la ragione della selezione automatica
  const generateSelectionReason = (analysis: any): string => {
    const reasons = []
    
    if (analysis.selection_criteria.peso_compatibile) {
      reasons.push("capacità di peso adeguata")
    }
    if (analysis.selection_criteria.area_compatibile) {
      reasons.push("piano di lavoro sufficiente")
    }
    if (analysis.selection_criteria.valvole_compatibili) {
      reasons.push("valvole sufficienti")
    }
    if (analysis.selection_criteria.cicli_compatibili) {
      reasons.push("cicli di cura compatibili")
    }

    return `Selezionata per: ${reasons.join(", ")}. Punteggio di compatibilità: ${analysis.compatibility_score}%`
  }

  // Handler per procedere al prossimo step
  const handleNext = () => {
    if (compatibilityAnalysis) {
      onNext(compatibilityAnalysis)
    }
  }

  // Render indicatori di compatibilità
  const renderCompatibilityIndicator = (criterion: boolean, label: string, icon: React.ReactNode) => (
    <div className={cn(
      "flex items-center gap-2 p-3 rounded-lg border",
      criterion ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
    )}>
      <div className={cn(
        "p-2 rounded-full",
        criterion ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"
      )}>
        {icon}
      </div>
      <div className="flex-1">
        <p className={cn(
          "font-medium",
          criterion ? "text-green-800" : "text-red-800"
        )}>
          {label}
        </p>
        <p className={cn(
          "text-sm",
          criterion ? "text-green-600" : "text-red-600"
        )}>
          {criterion ? "Compatibile" : "Non compatibile"}
        </p>
      </div>
      {criterion ? (
        <CheckCircle2 className="h-5 w-5 text-green-600" />
      ) : (
        <AlertCircle className="h-5 w-5 text-red-600" />
      )}
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 2: Selezione Automatica Autoclave</h2>
          <p className="text-gray-600 mt-1">
            Il sistema analizza automaticamente le autoclavi per trovare la migliore compatibilità.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={compatibilityAnalysis ? 100 : analysisProgress} className="w-32" />
          <span className="text-sm text-gray-500">
            {compatibilityAnalysis ? '100%' : `${analysisProgress}%`}
          </span>
        </div>
      </div>

      {/* Riepilogo ODL selezionati */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Requisiti Rilevati dagli ODL
          </CardTitle>
          <CardDescription>
            Dati estrapolati dai {odlData.selected_odl_ids.length} ODL selezionati per la ricerca automatica
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Scale className="h-6 w-6 mx-auto mb-2 text-blue-600" />
              <div className="text-xl font-bold text-blue-600">
                {odlData.peso_totale_kg.toFixed(1)}kg
              </div>
              <div className="text-sm text-blue-800">Peso Totale</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <Gauge className="h-6 w-6 mx-auto mb-2 text-green-600" />
              <div className="text-xl font-bold text-green-600">
                {odlData.area_totale_cm2.toFixed(0)}
              </div>
              <div className="text-sm text-green-800">cm² Area</div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <Zap className="h-6 w-6 mx-auto mb-2 text-orange-600" />
              <div className="text-xl font-bold text-orange-600">
                {odlData.valvole_richieste}
              </div>
              <div className="text-sm text-orange-800">Valvole</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <Thermometer className="h-6 w-6 mx-auto mb-2 text-purple-600" />
              <div className="text-xl font-bold text-purple-600">
                {odlData.cicli_cura_coinvolti.length}
              </div>
              <div className="text-sm text-purple-800">Cicli Cura</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analisi in corso */}
      {!compatibilityAnalysis && analysisProgress > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 animate-spin" />
              Analisi Automatica in Corso...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Progress value={analysisProgress} className="w-full" />
              <p className="text-sm text-muted-foreground">
                Sto confrontando {autoclaveList.length} autoclavi disponibili con i requisiti rilevati.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risultato della selezione automatica */}
      {compatibilityAnalysis && selectedAutoclave && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Autoclave Selezionata Automaticamente
            </CardTitle>
            <CardDescription>
              {compatibilityAnalysis.auto_selection_reason}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Dettagli autoclave selezionata */}
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-green-800">
                    {selectedAutoclave.nome}
                  </h3>
                  <p className="text-sm text-green-600">
                    {selectedAutoclave.codice} - {selectedAutoclave.produttore || 'Autoclave'} 
                  </p>
                </div>
                <Badge className="bg-green-100 text-green-800">
                  Compatibilità: {compatibilityAnalysis.compatibility_score}%
                </Badge>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-green-700">Capacità Peso</p>
                  <p className="font-medium text-green-800">
                    {selectedAutoclave.max_load_kg}kg
                  </p>
                </div>
                <div>
                  <p className="text-sm text-green-700">Piano Lavoro</p>
                  <p className="font-medium text-green-800">
                    {selectedAutoclave.lunghezza}×{selectedAutoclave.larghezza_piano}mm
                  </p>
                </div>
                <div>
                  <p className="text-sm text-green-700">Valvole</p>
                  <p className="font-medium text-green-800">
                    {selectedAutoclave.num_linee_vuoto}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-green-700">Stato</p>
                  <Badge className="bg-green-100 text-green-800">
                    {selectedAutoclave.stato}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Analisi di compatibilità */}
            <div>
              <h4 className="font-medium mb-4">Analisi di Compatibilità</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {renderCompatibilityIndicator(
                  compatibilityAnalysis.selection_criteria.peso_compatibile,
                  "Capacità Peso",
                  <Scale className="h-4 w-4" />
                )}
                {renderCompatibilityIndicator(
                  compatibilityAnalysis.selection_criteria.area_compatibile,
                  "Area Piano Lavoro",
                  <Gauge className="h-4 w-4" />
                )}
                {renderCompatibilityIndicator(
                  compatibilityAnalysis.selection_criteria.valvole_compatibili,
                  "Valvole Disponibili",
                  <Zap className="h-4 w-4" />
                )}
                {renderCompatibilityIndicator(
                  compatibilityAnalysis.selection_criteria.cicli_compatibili,
                  "Cicli di Cura",
                  <Thermometer className="h-4 w-4" />
                )}
              </div>
            </div>

            {/* Alternative suggerite */}
            {compatibilityAnalysis.alternative_autoclaves.length > 0 && (
              <div>
                <h4 className="font-medium mb-4">Alternative Disponibili</h4>
                <div className="space-y-2">
                  {compatibilityAnalysis.alternative_autoclaves.slice(0, 3).map((autoclave, index) => (
                    <div key={autoclave.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{autoclave.nome}</p>
                        <p className="text-sm text-gray-600">{autoclave.codice}</p>
                      </div>
                      <Badge variant="secondary">
                        #{index + 2}° Opzione
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Errore se nessuna autoclave compatibile */}
      {!loading && autoclaveList.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Nessuna autoclave disponibile al momento. Verifica lo stato delle autoclavi o riprova più tardi.
          </AlertDescription>
        </Alert>
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
          Indietro
        </Button>

        <Button
          onClick={handleNext}
          disabled={!compatibilityAnalysis || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Elaborazione...
            </>
          ) : (
            <>
              Procedi alla Generazione Layout
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 