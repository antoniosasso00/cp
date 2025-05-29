'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { AlertCircle, Search, Filter, CheckCircle2, Package, Wrench, Clock, ArrowRight } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"
import { ODLResponse, odlApi } from '@/lib/api'

// ✅ NUOVO: Dati estrapolati dalla selezione ODL
export interface ExtractedNestingData {
  selected_odl_ids: number[]
  cicli_cura_coinvolti: string[]
  peso_totale_kg: number
  area_totale_cm2: number
  valvole_richieste: number
  priorita_media: number
  is_single_cycle: boolean
  ciclo_cura_dominante?: string
  conflitti_cicli: boolean
  compatibilita_summary: {
    total_odl: number
    cycles_count: number
    weight_ok: boolean
    area_estimated: number
  }
}

interface NestingStep1ODLSelectionProps {
  onNext: (data: ExtractedNestingData) => void
  onBack?: () => void
  isLoading?: boolean
  savedProgress?: {
    selected_odl_ids: number[]
    filters: {
      status_filter: string
      priorita_filter: string
      search_filter: string
    }
  }
}

// Funzione per ottenere il colore del badge di stato
const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'Attesa Cura': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'Preparazione': return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'Laminazione': return 'bg-purple-100 text-purple-800 border-purple-200'
    case 'In Coda': return 'bg-orange-100 text-orange-800 border-orange-200'
    default: return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

// Funzione per ottenere il colore del badge di priorità
const getPriorityBadgeColor = (priorita: number) => {
  if (priorita >= 9) return 'bg-red-100 text-red-800 border-red-200'
  if (priorita >= 7) return 'bg-orange-100 text-orange-800 border-orange-200'
  if (priorita >= 5) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  if (priorita >= 3) return 'bg-blue-100 text-blue-800 border-blue-200'
  return 'bg-green-100 text-green-800 border-green-200'
}

export function NestingStep1ODLSelection({ 
  onNext, 
  onBack, 
  isLoading = false,
  savedProgress 
}: NestingStep1ODLSelectionProps) {
  const { toast } = useToast()
  
  // State per ODL e selezione
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [selectedOdlIds, setSelectedOdlIds] = useState<Set<number>>(
    new Set(savedProgress?.selected_odl_ids || [])
  )
  const [loading, setLoading] = useState(true)
  
  // State per filtri
  const [searchFilter, setSearchFilter] = useState(savedProgress?.filters?.search_filter || '')
  const [statusFilter, setStatusFilter] = useState(savedProgress?.filters?.status_filter || 'all')
  const [prioritaFilter, setPrioritaFilter] = useState(savedProgress?.filters?.priorita_filter || 'all')
  
  // State per dati estrapolati
  const [extractedData, setExtractedData] = useState<ExtractedNestingData | null>(null)

  // Carica gli ODL all'avvio
  useEffect(() => {
    loadODLData()
  }, [])

  // Ricalcola i dati estrapolati quando cambia la selezione
  useEffect(() => {
    if (selectedOdlIds.size > 0) {
      calculateExtractedData()
    } else {
      setExtractedData(null)
    }
  }, [selectedOdlIds, odlList])

  const loadODLData = async () => {
    try {
      setLoading(true)
      const response = await odlApi.getAll()
      
      // Filtra solo ODL disponibili per nesting
      const availableODL = response.filter(odl => 
        ['Attesa Cura', 'In Coda'].includes(odl.status)
      )
      
      setOdlList(availableODL)
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Errore caricamento ODL",
        description: "Non è stato possibile caricare la lista degli ODL disponibili"
      })
    } finally {
      setLoading(false)
    }
  }

  // ✅ CHIAVE: Calcola tutti i dati necessari dalla selezione ODL
  const calculateExtractedData = () => {
    const selectedODL = odlList.filter(odl => selectedOdlIds.has(odl.id))
    
    if (selectedODL.length === 0) {
      setExtractedData(null)
      return
    }

    // Estrapola cicli di cura
    const cicliCura = new Set<string>()
    let pesoTotale = 0
    let areaTotale = 0
    let valvoleTotali = 0
    let prioritaMedia = 0

    selectedODL.forEach(odl => {
      // Ciclo cura: estrai dalla parte
      if (odl.parte?.ciclo_cura?.nome) {
        cicliCura.add(odl.parte.ciclo_cura.nome)
      }
      
      // Peso: estrai dal tool
      if (odl.tool && odl.tool.peso) {
        pesoTotale += odl.tool.peso
      }
      
      // Area: calcola da dimensioni tool (mm² -> cm²)
      if (odl.tool?.lunghezza_piano && odl.tool?.larghezza_piano) {
        const areaToolCm2 = (odl.tool.lunghezza_piano * odl.tool.larghezza_piano) / 100
        areaTotale += areaToolCm2
      }
      
      // Valvole: estrai dalla parte
      if (odl.parte?.num_valvole_richieste) {
        valvoleTotali += odl.parte.num_valvole_richieste
      }
      
      // Priorità
      prioritaMedia += odl.priorita
    })

    const cicliCuraArray = Array.from(cicliCura)
    const isSingleCycle = cicliCuraArray.length === 1
    const conflittiCicli = cicliCuraArray.length > 1

    // Determina ciclo dominante se ci sono conflitti
    const cicloDominante = isSingleCycle 
      ? cicliCuraArray[0] 
      : cicliCuraArray.length > 0 
        ? cicliCuraArray.reduce((a, b) => 
            selectedODL.filter(odl => odl.parte?.ciclo_cura?.nome === a).length >
            selectedODL.filter(odl => odl.parte?.ciclo_cura?.nome === b).length ? a : b
          )
        : undefined // Valore di fallback se l'array è vuoto

    const extracted: ExtractedNestingData = {
      selected_odl_ids: Array.from(selectedOdlIds),
      cicli_cura_coinvolti: cicliCuraArray,
      peso_totale_kg: pesoTotale,
      area_totale_cm2: areaTotale,
      valvole_richieste: valvoleTotali,
      priorita_media: prioritaMedia / selectedODL.length,
      is_single_cycle: isSingleCycle,
      ciclo_cura_dominante: cicloDominante,
      conflitti_cicli: conflittiCicli,
      compatibilita_summary: {
        total_odl: selectedODL.length,
        cycles_count: cicliCuraArray.length,
        weight_ok: pesoTotale > 0,
        area_estimated: areaTotale
      }
    }

    setExtractedData(extracted)
  }

  // Gestione selezione ODL
  const toggleODLSelection = (odlId: number) => {
    setSelectedOdlIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(odlId)) {
        newSet.delete(odlId)
      } else {
        newSet.add(odlId)
      }
      return newSet
    })
  }

  const selectAllVisible = () => {
    const visibleODL = getFilteredODL()
    setSelectedOdlIds(prev => {
      const newSet = new Set(prev)
      visibleODL.forEach(odl => newSet.add(odl.id))
      return newSet
    })
  }

  const clearSelection = () => {
    setSelectedOdlIds(new Set())
  }

  // Filtraggio ODL
  const getFilteredODL = () => {
    return odlList.filter(odl => {
      // Filtro status
      if (statusFilter !== 'all' && odl.status !== statusFilter) return false
      
      // Filtro priorità
      if (prioritaFilter !== 'all') {
        const minPriority = parseInt(prioritaFilter)
        if (odl.priorita < minPriority) return false
      }
      
      // Filtro ricerca
      if (searchFilter) {
        const searchLower = searchFilter.toLowerCase()
        return (
          odl.id.toString().includes(searchLower) ||
          odl.parte?.part_number?.toLowerCase().includes(searchLower) ||
          odl.tool?.part_number_tool?.toLowerCase().includes(searchLower) ||
          odl.parte?.descrizione_breve?.toLowerCase().includes(searchLower)
        )
      }
      
      return true
    })
  }

  const filteredODL = getFilteredODL()
  const progressPercentage = extractedData ? 100 : selectedOdlIds.size > 0 ? 50 : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Step 1: Selezione ODL</h2>
          <p className="text-gray-600 mt-1">
            Seleziona gli ODL da includere nel nesting. I dati necessari verranno estrapolati automaticamente.
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={progressPercentage} className="w-32" />
          <span className="text-sm text-gray-500">{progressPercentage}%</span>
        </div>
      </div>

      {/* Filtri di ricerca */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtri ODL Disponibili
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Ricerca</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="ID, Part Number, Tool..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Stato</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli stati</SelectItem>
                  <SelectItem value="Attesa Cura">Attesa Cura</SelectItem>
                  <SelectItem value="In Coda">In Coda</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Priorità minima</label>
              <Select value={prioritaFilter} onValueChange={setPrioritaFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le priorità</SelectItem>
                  <SelectItem value="1">1+ (Tutte)</SelectItem>
                  <SelectItem value="3">3+ (Media-Alta)</SelectItem>
                  <SelectItem value="5">5+ (Alta)</SelectItem>
                  <SelectItem value="7">7+ (Critica)</SelectItem>
                  <SelectItem value="9">9+ (Urgente)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex items-center gap-2 mt-4 pt-4 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={selectAllVisible}
              disabled={filteredODL.length === 0}
            >
              Seleziona tutti visibili ({filteredODL.length})
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearSelection}
              disabled={selectedOdlIds.size === 0}
            >
              Deseleziona tutto ({selectedOdlIds.size})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista ODL con selezione */}
      <Card>
        <CardHeader>
          <CardTitle>ODL Disponibili per Nesting</CardTitle>
          <CardDescription>
            {loading ? 'Caricamento...' : `${filteredODL.length} ODL disponibili`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : filteredODL.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Package className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Nessun ODL disponibile con i filtri selezionati</p>
              </div>
            ) : (
              filteredODL.map(odl => {
                const isSelected = selectedOdlIds.has(odl.id)
                return (
                  <div
                    key={odl.id}
                    className={cn(
                      "flex items-center gap-4 p-4 border rounded-lg cursor-pointer transition-colors",
                      isSelected 
                        ? "border-blue-500 bg-blue-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                    onClick={() => toggleODLSelection(odl.id)}
                  >
                    <Checkbox
                      checked={isSelected}
                      onChange={() => toggleODLSelection(odl.id)}
                    />
                    
                    <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="font-medium">ODL #{odl.id}</p>
                        <Badge className={getStatusBadgeColor(odl.status)}>
                          {odl.status}
                        </Badge>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-600">Parte</p>
                        <p className="font-medium">{odl.parte?.part_number || '-'}</p>
                        <p className="text-xs text-gray-500">{odl.parte?.descrizione_breve}</p>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-600">Tool</p>
                        <p className="font-medium">{odl.tool?.part_number_tool || '-'}</p>
                        {odl.tool?.lunghezza_piano && odl.tool?.larghezza_piano && (
                          <p className="text-xs text-gray-500">
                            {odl.tool.lunghezza_piano}x{odl.tool.larghezza_piano}mm
                          </p>
                        )}
                      </div>
                      
                      <div className="text-right">
                        <Badge className={getPriorityBadgeColor(odl.priorita)}>
                          Priorità {odl.priorita}
                        </Badge>
                        {odl.tool?.peso && (
                          <p className="text-xs text-gray-500 mt-1">{odl.tool.peso}kg</p>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </CardContent>
      </Card>

      {/* Dati estrapolati dalla selezione */}
      {extractedData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Dati Estrapolati dalla Selezione
            </CardTitle>
            <CardDescription>
              Questi dati verranno utilizzati per filtrare le autoclavi compatibili
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {extractedData.compatibilita_summary.total_odl}
                </div>
                <div className="text-sm text-blue-800">ODL Selezionati</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {extractedData.peso_totale_kg.toFixed(1)}kg
                </div>
                <div className="text-sm text-green-800">Peso Totale</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {extractedData.area_totale_cm2.toFixed(0)}
                </div>
                <div className="text-sm text-purple-800">cm² Area Stimata</div>
              </div>
              
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {extractedData.valvole_richieste}
                </div>
                <div className="text-sm text-orange-800">Valvole Richieste</div>
              </div>
            </div>

            {/* Cicli di cura con alert per conflitti */}
            <div className="mt-6">
              <h4 className="font-medium mb-3">Cicli di Cura Coinvolti</h4>
              
              {extractedData.conflitti_cicli && (
                <Alert className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Attenzione:</strong> Sono stati selezionati ODL con cicli di cura diversi. 
                    Questo richiederà multiple autoclavate separate.
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="flex flex-wrap gap-2">
                {extractedData.cicli_cura_coinvolti.map(ciclo => (
                  <Badge 
                    key={ciclo}
                    variant={extractedData.is_single_cycle ? "default" : "secondary"}
                    className="text-sm"
                  >
                    {ciclo}
                    {ciclo === extractedData.ciclo_cura_dominante && !extractedData.is_single_cycle && (
                      <span className="ml-1 text-xs">(dominante)</span>
                    )}
                  </Badge>
                ))}
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
        >
          Indietro
        </Button>

        <Button
          onClick={() => extractedData && onNext(extractedData)}
          disabled={!extractedData || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Elaborazione...
            </>
          ) : (
            <>
              Procedi alla Selezione Autoclave
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  )
} 