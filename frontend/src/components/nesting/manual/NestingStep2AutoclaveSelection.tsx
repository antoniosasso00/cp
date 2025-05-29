'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { AlertCircle, Filter, CheckCircle2, Factory, AlertTriangle, ArrowRight, ArrowLeft } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { Autoclave, autoclaveApi } from '@/lib/api'
import { ExtractedNestingData } from './NestingStep1ODLSelection'

export interface AutoclaveSelectionData {
  autoclave_id: number
  autoclave_data: Autoclave
  compatibility_score: number
  weight_margin: number
  area_efficiency: number
  valvole_available: number
  compatibility_notes: string[]
}

interface NestingStep2AutoclaveSelectionProps {
  odlData: ExtractedNestingData
  onNext: (data: AutoclaveSelectionData) => void
  onBack: () => void
  isLoading?: boolean
  savedProgress?: {
    selected_autoclave_id?: number
  }
}

// Funzione per calcolare il punteggio di compatibilità
const calculateCompatibilityScore = (autoclave: Autoclave, odlData: ExtractedNestingData): {
  score: number
  weightMargin: number
  areaEfficiency: number
  valvoleAvailable: number
  notes: string[]
} => {
  const notes: string[] = []
  let score = 100

  // Calcolo margine peso
  const maxLoad = autoclave.max_load_kg || 1000 // Default se non specificato
  const weightMargin = ((maxLoad - odlData.peso_totale_kg) / maxLoad) * 100
  
  if (weightMargin < 10) {
    score -= 30
    notes.push("Carico molto vicino al limite")
  } else if (weightMargin < 30) {
    score -= 15
    notes.push("Carico elevato")
  }

  // Calcolo efficienza area
  const areaAutoclave = autoclave.area_piano || (autoclave.lunghezza * autoclave.larghezza_piano / 100)
  const areaEfficiency = (odlData.area_totale_cm2 / areaAutoclave) * 100
  
  if (areaEfficiency > 85) {
    score -= 20
    notes.push("Area molto sfruttata")
  } else if (areaEfficiency > 70) {
    notes.push("Buon utilizzo area")
  } else if (areaEfficiency < 40) {
    score -= 10
    notes.push("Basso utilizzo area")
  }

  // Verifica valvole
  const valvoleAvailable = autoclave.num_linee_vuoto - odlData.valvole_richieste
  if (valvoleAvailable < 0) {
    score = 0 // Non compatibile
    notes.push("INCOMPATIBILE: Valvole insufficienti")
  } else if (valvoleAvailable === 0) {
    score -= 10
    notes.push("Tutte le valvole utilizzate")
  }

  // Bonus per autoclavi disponibili
  if (autoclave.stato === 'DISPONIBILE') {
    notes.push("Autoclave disponibile")
  } else {
    score -= 50
    notes.push(`Autoclave ${autoclave.stato.toLowerCase()}`)
  }

  return {
    score: Math.max(0, score),
    weightMargin,
    areaEfficiency,
    valvoleAvailable,
    notes
  }
}

// Funzione per il colore del badge di stato
const getStatoBadgeColor = (stato: string) => {
  switch (stato) {
    case 'DISPONIBILE': return 'bg-green-100 text-green-800 border-green-200'
    case 'IN_USO': return 'bg-red-100 text-red-800 border-red-200'
    case 'MANUTENZIONE': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'GUASTO': return 'bg-red-100 text-red-800 border-red-200'
    case 'SPENTA': return 'bg-gray-100 text-gray-800 border-gray-200'
    default: return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

// Funzione per il colore del punteggio
const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-600 bg-green-50'
  if (score >= 60) return 'text-yellow-600 bg-yellow-50'
  if (score >= 40) return 'text-orange-600 bg-orange-50'
  return 'text-red-600 bg-red-50'
}

export function NestingStep2AutoclaveSelection({ 
  odlData, 
  onNext, 
  onBack, 
  isLoading = false,
  savedProgress 
}: NestingStep2AutoclaveSelectionProps) {
  const { toast } = useToast()
  
  // State per autoclavi
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([])
  const [selectedAutoclaveId, setSelectedAutoclaveId] = useState<number | null>(
    savedProgress?.selected_autoclave_id || null
  )
  const [autoclaveCompatibility, setAutoclaveCompatibility] = useState<Map<number, ReturnType<typeof calculateCompatibilityScore>>>(new Map())
  const [loading, setLoading] = useState(true)

  // Carica le autoclavi all'avvio
  useEffect(() => {
    loadAutoclaveData()
  }, [])

  // Calcola compatibilità quando cambiano i dati
  useEffect(() => {
    if (autoclavi.length > 0) {
      calculateAllCompatibility()
    }
  }, [autoclavi, odlData])

  const loadAutoclaveData = async () => {
    try {
      setLoading(true)
      const response = await autoclaveApi.getAll()
      
      // Ordina per stato (disponibili prima) e poi per nome
      const sortedAutoclavi = response.sort((a, b) => {
        if (a.stato === 'DISPONIBILE' && b.stato !== 'DISPONIBILE') return -1
        if (b.stato === 'DISPONIBILE' && a.stato !== 'DISPONIBILE') return 1
        return a.nome.localeCompare(b.nome)
      })
      
      setAutoclavi(sortedAutoclavi)
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore caricamento autoclavi",
        description: "Non è stato possibile caricare la lista delle autoclavi"
      })
    } finally {
      setLoading(false)
    }
  }

  const calculateAllCompatibility = () => {
    const compatibilityMap = new Map()
    autoclavi.forEach(autoclave => {
      const compatibility = calculateCompatibilityScore(autoclave, odlData)
      compatibilityMap.set(autoclave.id, compatibility)
    })
    setAutoclaveCompatibility(compatibilityMap)
  }

  const getCompatibleAutoclavi = () => {
    return autoclavi.filter(autoclave => {
      const compatibility = autoclaveCompatibility.get(autoclave.id)
      return compatibility && compatibility.score > 0
    })
  }

  const handleAutoclaveSelection = (autoclave: Autoclave) => {
    const compatibility = autoclaveCompatibility.get(autoclave.id)
    if (!compatibility || compatibility.score === 0) {
      toast({
        variant: "destructive",
        title: "Autoclave non compatibile",
        description: "Questa autoclave non è compatibile con gli ODL selezionati"
      })
      return
    }

    setSelectedAutoclaveId(autoclave.id)
  }

  const handleNext = () => {
    if (!selectedAutoclaveId) return

    const selectedAutoclave = autoclavi.find(a => a.id === selectedAutoclaveId)
    const compatibility = autoclaveCompatibility.get(selectedAutoclaveId)
    
    if (!selectedAutoclave || !compatibility) return

    const selectionData: AutoclaveSelectionData = {
      autoclave_id: selectedAutoclaveId,
      autoclave_data: selectedAutoclave,
      compatibility_score: compatibility.score,
      weight_margin: compatibility.weightMargin,
      area_efficiency: compatibility.areaEfficiency,
      valvole_available: compatibility.valvoleAvailable,
      compatibility_notes: compatibility.notes
    }

    onNext(selectionData)
  }

  const compatibleAutoclavi = getCompatibleAutoclavi()
  const selectedAutoclave = autoclavi.find(a => a.id === selectedAutoclaveId)
  const selectedCompatibility = selectedAutoclaveId ? autoclaveCompatibility.get(selectedAutoclaveId) : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 2: Selezione Autoclave</h2>
          <p className="text-gray-600 mt-1">
            Seleziona l'autoclave più adatta per i {odlData.compatibilita_summary.total_odl} ODL scelti
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={selectedAutoclaveId ? 100 : 50} className="w-32" />
          <span className="text-sm text-gray-500">{selectedAutoclaveId ? 100 : 50}%</span>
        </div>
      </div>

      {/* Riepilogo ODL selezionati */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Riepilogo Requisiti
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded">
              <div className="text-lg font-bold text-blue-600">{odlData.compatibilita_summary.total_odl}</div>
              <div className="text-xs text-blue-800">ODL</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded">
              <div className="text-lg font-bold text-green-600">{odlData.peso_totale_kg.toFixed(1)}kg</div>
              <div className="text-xs text-green-800">Peso</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded">
              <div className="text-lg font-bold text-purple-600">{odlData.area_totale_cm2.toFixed(0)}</div>
              <div className="text-xs text-purple-800">cm² Area</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded">
              <div className="text-lg font-bold text-orange-600">{odlData.valvole_richieste}</div>
              <div className="text-xs text-orange-800">Valvole</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded">
              <div className="text-lg font-bold text-yellow-600">{odlData.cicli_cura_coinvolti.length}</div>
              <div className="text-xs text-yellow-800">Cicli</div>
            </div>
          </div>
          
          {/* Alert per conflitti cicli */}
          {odlData.conflitti_cicli && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Attenzione:</strong> Gli ODL selezionati hanno cicli di cura diversi: {odlData.cicli_cura_coinvolti.join(', ')}. 
                Considera di creare nesting separati per ogni ciclo.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Autoclavi compatibili */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Factory className="h-5 w-5" />
            Autoclavi Compatibili ({compatibleAutoclavi.length}/{autoclavi.length})
          </CardTitle>
          <CardDescription>
            {loading ? 'Caricamento...' : 'Autoclavi ordinate per punteggio di compatibilità'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : compatibleAutoclavi.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Nessuna autoclave compatibile trovata</p>
                <p className="text-sm mt-2">Modifica la selezione ODL o contatta l'amministratore</p>
              </div>
            ) : (
              compatibleAutoclavi
                .sort((a, b) => {
                  const scoreA = autoclaveCompatibility.get(a.id)?.score || 0
                  const scoreB = autoclaveCompatibility.get(b.id)?.score || 0
                  return scoreB - scoreA
                })
                .map(autoclave => {
                  const compatibility = autoclaveCompatibility.get(autoclave.id)!
                  const isSelected = selectedAutoclaveId === autoclave.id
                  
                  return (
                    <div
                      key={autoclave.id}
                      className={cn(
                        "p-4 border rounded-lg cursor-pointer transition-all",
                        isSelected 
                          ? "border-blue-500 bg-blue-50 shadow-md" 
                          : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
                      )}
                      onClick={() => handleAutoclaveSelection(autoclave)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold text-lg">{autoclave.nome}</h3>
                            <Badge className={getStatoBadgeColor(autoclave.stato)}>
                              {autoclave.stato}
                            </Badge>
                            <div className={cn("px-2 py-1 rounded text-sm font-medium", getScoreColor(compatibility.score))}>
                              {compatibility.score}% compatibile
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Dimensioni:</span>
                              <p className="font-medium">{autoclave.lunghezza}x{autoclave.larghezza_piano}mm</p>
                            </div>
                            <div>
                              <span className="text-gray-600">Carico max:</span>
                              <p className="font-medium">{autoclave.max_load_kg || '-'}kg</p>
                              {compatibility.weightMargin >= 0 && (
                                <p className="text-xs text-gray-500">
                                  {compatibility.weightMargin.toFixed(1)}% margine
                                </p>
                              )}
                            </div>
                            <div>
                              <span className="text-gray-600">Valvole:</span>
                              <p className="font-medium">{autoclave.num_linee_vuoto} linee</p>
                              <p className="text-xs text-gray-500">
                                {compatibility.valvoleAvailable} disponibili
                              </p>
                            </div>
                            <div>
                              <span className="text-gray-600">Efficienza area:</span>
                              <p className="font-medium">{compatibility.areaEfficiency.toFixed(1)}%</p>
                            </div>
                          </div>
                          
                          {compatibility.notes.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              {compatibility.notes.map((note, index) => (
                                <Badge 
                                  key={index}
                                  variant={note.includes('INCOMPATIBILE') ? 'destructive' : 'secondary'}
                                  className="text-xs"
                                >
                                  {note}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        {isSelected && (
                          <CheckCircle2 className="h-6 w-6 text-blue-600 flex-shrink-0 ml-4" />
                        )}
                      </div>
                    </div>
                  )
                })
            )}
          </div>
        </CardContent>
      </Card>

      {/* Dettagli autoclave selezionata */}
      {selectedAutoclave && selectedCompatibility && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Autoclave Selezionata: {selectedAutoclave.nome}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Specifiche Tecniche</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Codice:</span>
                    <span className="font-medium">{selectedAutoclave.codice}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Temperatura max:</span>
                    <span className="font-medium">{selectedAutoclave.temperatura_max}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pressione max:</span>
                    <span className="font-medium">{selectedAutoclave.pressione_max} bar</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Area piano:</span>
                    <span className="font-medium">
                      {(selectedAutoclave.area_piano || (selectedAutoclave.lunghezza * selectedAutoclave.larghezza_piano / 100)).toFixed(0)} cm²
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Analisi Compatibilità</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Punteggio totale:</span>
                    <span className={cn("font-medium", getScoreColor(selectedCompatibility.score).split(' ')[0])}>
                      {selectedCompatibility.score}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Margine peso:</span>
                    <span className="font-medium">{selectedCompatibility.weightMargin.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Efficienza area:</span>
                    <span className="font-medium">{selectedCompatibility.areaEfficiency.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Valvole libere:</span>
                    <span className="font-medium">{selectedCompatibility.valvoleAvailable}</span>
                  </div>
                </div>
              </div>
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
          Torna alla Selezione ODL
        </Button>

        <Button
          onClick={handleNext}
          disabled={!selectedAutoclaveId || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Elaborazione...
            </>
          ) : (
            <>
              Procedi al Layout Canvas
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 