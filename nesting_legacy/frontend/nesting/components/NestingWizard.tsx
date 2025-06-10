'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  Loader2, 
  Package, 
  Flame, 
  AlertCircle, 
  CheckCircle2, 
  Info, 
  ChevronRight,
  ChevronLeft,
  Zap,
  Settings,
  Weight,
  Gauge,
  Target,
  TrendingUp,
  AlertTriangle,
  Maximize2,
  Minimize2
} from 'lucide-react'
import { Progress } from '@/shared/components/ui/progress'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { batchNestingApi } from '@/lib/api'

interface ODLData {
  id: number
  status: string
  priorita: number
  note?: string
  parte: {
    id: number
    part_number: string
    descrizione_breve: string
    num_valvole_richieste: number
    ciclo_cura?: {
      id: number
      nome: string
      temperatura_stasi1: number
      pressione_stasi1: number
      durata_stasi1: number
    }
  }
  tool: {
    id: number
    part_number_tool: string
    descrizione?: string
    larghezza_piano: number
    lunghezza_piano: number
    peso?: number
  }
}

interface AutoclaveData {
  id: number
  nome: string
  codice: string
  stato: string
  lunghezza: number
  larghezza_piano: number
  temperatura_max: number
  pressione_max: number
  max_load_kg: number
  num_linee_vuoto: number
}

interface NestingWizardProps {
  onGenerate: (config: GenerationConfig) => Promise<void>
  generating: boolean
}

interface GenerationConfig {
  selectedOdl: number[]
  selectedAutoclavi: number[]
  parametri: {
    padding_mm: number
    min_distance_mm: number
  }
}

enum WizardStep {
  SELECT_ODL = 0,
  SELECT_AUTOCLAVI = 1,
  CONFIGURE_PARAMS = 2,
  REVIEW_GENERATE = 3
}

const STEP_CONFIG = [
  {
    id: WizardStep.SELECT_ODL,
    title: 'ODL',
    shortTitle: 'ODL',
    description: 'Seleziona ODL in attesa cura',
    icon: Package,
    color: 'text-blue-600'
  },
  {
    id: WizardStep.SELECT_AUTOCLAVI,
    title: 'Autoclavi',
    shortTitle: 'Autoclavi',
    description: 'Scegli autoclavi disponibili',
    icon: Flame,
    color: 'text-orange-600'
  },
  {
    id: WizardStep.CONFIGURE_PARAMS,
    title: 'Parametri',
    shortTitle: 'Config',
    description: 'Configura parametri nesting',
    icon: Settings,
    color: 'text-purple-600'
  },
  {
    id: WizardStep.REVIEW_GENERATE,
    title: 'Genera',
    shortTitle: 'Review',
    description: 'Rivedi e genera batch',
    icon: Zap,
    color: 'text-green-600'
  }
]

export default function NestingWizard({ onGenerate, generating }: NestingWizardProps) {
  const { toast } = useStandardToast()
  
  // Stato wizard
  const [currentStep, setCurrentStep] = useState(WizardStep.SELECT_ODL)
  const [completedSteps, setCompletedSteps] = useState<Set<WizardStep>>(new Set())
  
  // Dati
  const [odlList, setOdlList] = useState<ODLData[]>([])
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([])
  const [loading, setLoading] = useState(true)
  
  // Selezioni
  const [selectedOdl, setSelectedOdl] = useState<number[]>([])
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<number[]>([])
  
  // Parametri
  const [parametri, setParametri] = useState({
    padding_mm: 10,
    min_distance_mm: 8
  })

  // UI State
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Caricamento dati iniziali
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const nestingData = await batchNestingApi.getData()
      
      const odlInAttesaCura = nestingData.odl_in_attesa_cura || []
      const autoclaveDisponibili = nestingData.autoclavi_disponibili || []
      
      setOdlList(odlInAttesaCura)
      setAutoclaveList(autoclaveDisponibili)
      
      toast({
        title: 'Wizard pronto',
        description: `${odlInAttesaCura.length} ODL e ${autoclaveDisponibili.length} autoclavi caricate.`,
      })
    } catch (error) {
      console.error('❌ Errore nel caricamento dati:', error)
      toast({
        title: 'Errore di caricamento',
        description: 'Impossibile caricare i dati necessari',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  // Validazione step
  const canProceedToNext = () => {
    switch (currentStep) {
      case WizardStep.SELECT_ODL:
        return selectedOdl.length > 0
      case WizardStep.SELECT_AUTOCLAVI:
        return selectedAutoclavi.length > 0
      case WizardStep.CONFIGURE_PARAMS:
        return parametri.padding_mm >= 3 && parametri.min_distance_mm >= 3
      case WizardStep.REVIEW_GENERATE:
        return true
      default:
        return false
    }
  }

  const getStepValidationMessage = () => {
    switch (currentStep) {
      case WizardStep.SELECT_ODL:
        return selectedOdl.length === 0 ? 'Seleziona almeno un ODL per continuare' : null
      case WizardStep.SELECT_AUTOCLAVI:
        return selectedAutoclavi.length === 0 ? 'Seleziona almeno un\'autoclave per continuare' : null
      case WizardStep.CONFIGURE_PARAMS:
        if (parametri.padding_mm < 3) return 'Il padding deve essere almeno 3mm'
        if (parametri.min_distance_mm < 3) return 'La distanza minima deve essere almeno 3mm'
        return null
      default:
        return null
    }
  }

  // Navigazione wizard
  const handleNext = () => {
    if (canProceedToNext()) {
      setCompletedSteps(prev => new Set(Array.from(prev).concat([currentStep])))
      setCurrentStep(prev => Math.min(prev + 1, WizardStep.REVIEW_GENERATE))
    }
  }

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, WizardStep.SELECT_ODL))
  }

  const handleStepClick = (step: WizardStep) => {
    // Permetti di andare solo a step completati o al prossimo step valido
    if (completedSteps.has(step) || (step === currentStep + 1 && canProceedToNext())) {
      if (step === currentStep + 1 && canProceedToNext()) {
        setCompletedSteps(prev => new Set(Array.from(prev).concat([currentStep])))
      }
      setCurrentStep(step)
    }
  }

  // Gestione selezioni ODL
  const handleOdlSelection = (odlId: number, checked: boolean) => {
    if (checked) {
      setSelectedOdl(prev => [...prev, odlId])
    } else {
      setSelectedOdl(prev => prev.filter(id => id !== odlId))
    }
  }

  const handleSelectAllOdl = () => setSelectedOdl(odlList.map(odl => odl.id))
  const handleDeselectAllOdl = () => setSelectedOdl([])

  // Gestione selezioni autoclavi
  const handleAutoclaveSelection = (autoclaveId: number, checked: boolean) => {
    if (checked) {
      setSelectedAutoclavi(prev => [...prev, autoclaveId])
    } else {
      setSelectedAutoclavi(prev => prev.filter(id => id !== autoclaveId))
    }
  }

  const handleSelectAllAutoclavi = () => setSelectedAutoclavi(autoclaveList.map(a => a.id))
  const handleDeselectAllAutoclavi = () => setSelectedAutoclavi([])

  // Generazione
  const handleGenerate = async () => {
    try {
      await onGenerate({
        selectedOdl,
        selectedAutoclavi,
        parametri
      })
    } catch (error) {
      console.error('Errore generazione:', error)
    }
  }

  // Calcoli per summary laterale
  const getTotalWeight = () => {
    return selectedOdl.reduce((total, odlId) => {
      const odl = odlList.find(o => o.id === odlId)
      return total + (odl?.tool.peso || 0)
    }, 0)
  }

  const getTotalValves = () => {
    return selectedOdl.reduce((total, odlId) => {
      const odl = odlList.find(o => o.id === odlId)
      return total + (odl?.parte.num_valvole_richieste || 0)
    }, 0)
  }

  const getTotalAutoclaveCapacity = () => {
    return selectedAutoclavi.reduce((total, autoclaveId) => {
      const autoclave = autoclaveList.find(a => a.id === autoclaveId)
      return total + (autoclave?.max_load_kg || 0)
    }, 0)
  }

  const getCapacityUtilization = () => {
    const totalCapacity = getTotalAutoclaveCapacity()
    const totalWeight = getTotalWeight()
    return totalCapacity > 0 ? (totalWeight / totalCapacity) * 100 : 0
  }

  const getProgressPercentage = () => {
    const totalSteps = Object.keys(WizardStep).length / 2 // enum has both numeric and string keys
    const completedCount = completedSteps.size + (canProceedToNext() ? 1 : 0)
    return Math.min((completedCount / totalSteps) * 100, 100)
  }

  // Componente Step Indicator Orizzontale
  const StepIndicator = () => (
    <div className="flex items-center justify-between mb-6 px-4 py-3 bg-gray-50 rounded-lg">
      {STEP_CONFIG.map((step, index) => {
        const isActive = currentStep === step.id
        const isCompleted = completedSteps.has(step.id)
        const canAccess = isActive || isCompleted || (step.id === currentStep + 1 && canProceedToNext())
        
        const Icon = step.icon
        
        return (
          <React.Fragment key={step.id}>
            <div 
              className={`flex items-center gap-3 cursor-pointer transition-all duration-200 px-3 py-2 rounded-md ${
                canAccess ? 'hover:bg-white hover:shadow-sm' : 'cursor-not-allowed'
              }`}
              onClick={() => canAccess && handleStepClick(step.id)}
            >
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-200
                ${isActive 
                  ? 'border-blue-500 bg-blue-100 text-blue-600' 
                  : isCompleted 
                    ? 'border-green-500 bg-green-100 text-green-600' 
                    : 'border-gray-300 bg-white text-gray-400'
                }
              `}>
                {isCompleted ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>
              
              <div className="hidden sm:block">
                <p className={`text-sm font-medium ${
                  isActive ? 'text-blue-900' : isCompleted ? 'text-green-900' : 'text-gray-500'
                }`}>
                  {step.shortTitle}
                </p>
              </div>
            </div>
            
            {index < STEP_CONFIG.length - 1 && (
              <div className={`flex-1 h-px ${
                completedSteps.has(step.id) ? 'bg-green-300' : 'bg-gray-300'
              }`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )

  // Componente Summary Compatto
  const CompactSummary = () => {
    const capacityUtilization = getCapacityUtilization()
    const totalWeight = getTotalWeight()
    const totalValves = getTotalValves()
    
    if (sidebarCollapsed) {
      return (
        <div className="space-y-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSidebarCollapsed(false)}
            className="w-full"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
          <div className="text-center space-y-1">
            <div className="text-lg font-bold text-blue-600">{selectedOdl.length}</div>
            <div className="text-lg font-bold text-orange-600">{selectedAutoclavi.length}</div>
            {totalWeight > 0 && (
              <div className="text-sm font-medium">{totalWeight.toFixed(0)}kg</div>
            )}
          </div>
        </div>
      )
    }

    return (
      <Card className="sticky top-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-600" />
              Configurazione
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(true)}
              className="h-6 w-6 p-0"
            >
              <Minimize2 className="h-3 w-3" />
            </Button>
          </div>
          <Progress value={getProgressPercentage()} className="h-1.5" />
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Metriche Essenziali */}
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-blue-50 rounded-md">
              <div className="text-xl font-bold text-blue-600">{selectedOdl.length}</div>
              <div className="text-xs text-blue-700">ODL</div>
            </div>
            <div className="text-center p-2 bg-orange-50 rounded-md">
              <div className="text-xl font-bold text-orange-600">{selectedAutoclavi.length}</div>
              <div className="text-xs text-orange-700">Autoclavi</div>
            </div>
          </div>

          {/* Metriche Avanzate */}
          {selectedOdl.length > 0 && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Peso:</span>
                <span className="font-medium">{totalWeight.toFixed(1)} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Valvole:</span>
                <span className="font-medium">{totalValves}</span>
              </div>
              
              {selectedAutoclavi.length > 0 && (
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Utilizzo:</span>
                    <span className={`font-medium ${
                      capacityUtilization > 90 ? 'text-red-600' : 
                      capacityUtilization > 70 ? 'text-yellow-600' : 
                      'text-green-600'
                    }`}>
                      {capacityUtilization.toFixed(0)}%
                    </span>
                  </div>
                  <Progress 
                    value={Math.min(capacityUtilization, 100)} 
                    className={`h-1.5 ${
                      capacityUtilization > 90 ? '[&>div]:bg-red-500' : 
                      capacityUtilization > 70 ? '[&>div]:bg-yellow-500' : 
                      '[&>div]:bg-green-500'
                    }`}
                  />
                </div>
              )}
            </div>
          )}

          {/* Avvisi Critici */}
          {capacityUtilization > 90 && (
            <div className="p-2 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-3 w-3 text-red-600" />
                <span className="text-xs font-medium text-red-800">Capacità Critica</span>
              </div>
            </div>
          )}

          {/* Parametri (solo se configurati) */}
          {currentStep >= WizardStep.CONFIGURE_PARAMS && (
            <div className="pt-2 border-t space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Padding:</span>
                <span className="font-medium">{parametri.padding_mm}mm</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Distanza:</span>
                <span className="font-medium">{parametri.min_distance_mm}mm</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-600" />
            <div>
              <p className="font-medium">Caricamento Wizard</p>
              <p className="text-sm text-muted-foreground">Preparazione dati per il nesting...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Step Indicator Orizzontale */}
      <StepIndicator />

      <div className={`grid gap-6 ${sidebarCollapsed ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-4'}`}>
        {/* Contenuto principale wizard */}
        <div className={sidebarCollapsed ? 'col-span-1' : 'lg:col-span-3'}>
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {React.createElement(STEP_CONFIG[currentStep].icon, { 
                      className: `h-5 w-5 ${STEP_CONFIG[currentStep].color}` 
                    })}
                    {STEP_CONFIG[currentStep].title}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {STEP_CONFIG[currentStep].description}
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-xs">
                  {currentStep + 1} di {STEP_CONFIG.length}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Step 1: Selezione ODL */}
              {currentStep === WizardStep.SELECT_ODL && (
                <div className="space-y-4">
                  {odlList.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                      <p>Nessun ODL in attesa di cura</p>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={handleSelectAllOdl}>
                            Tutti ({odlList.length})
                          </Button>
                          <Button variant="outline" size="sm" onClick={handleDeselectAllOdl}>
                            Nessuno
                          </Button>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {selectedOdl.length} selezionati
                        </span>
                      </div>
                      
                      <div className="space-y-2 max-h-96 overflow-y-auto border rounded-lg">
                        {odlList.map((odl) => (
                          <div key={odl.id} className="flex items-center space-x-3 p-3 hover:bg-gray-50 border-b last:border-b-0">
                            <Checkbox
                              checked={selectedOdl.includes(odl.id)}
                              onCheckedChange={(checked) => handleOdlSelection(odl.id, !!checked)}
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm">ODL #{odl.id}</span>
                                <Badge variant="outline" className="text-xs">P{odl.priorita}</Badge>
                                {odl.tool.peso && (
                                  <Badge variant="secondary" className="text-xs">{odl.tool.peso}kg</Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mb-1 line-clamp-1">
                                {odl.parte.descrizione_breve}
                              </p>
                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <span>Tool: {odl.tool.part_number_tool}</span>
                                <span>•</span>
                                <span>{odl.parte.num_valvole_richieste} valvole</span>
                                <span>•</span>
                                <span>{odl.parte.ciclo_cura?.nome || 'Ciclo N/A'}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Step 2: Selezione Autoclavi */}
              {currentStep === WizardStep.SELECT_AUTOCLAVI && (
                <div className="space-y-4">
                  {autoclaveList.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                      <p>Nessuna autoclave disponibile</p>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={handleSelectAllAutoclavi}>
                            Tutte ({autoclaveList.length})
                          </Button>
                          <Button variant="outline" size="sm" onClick={handleDeselectAllAutoclavi}>
                            Nessuna
                          </Button>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {selectedAutoclavi.length} selezionate
                        </span>
                      </div>
                      
                      <div className="space-y-2 max-h-96 overflow-y-auto border rounded-lg">
                        {autoclaveList.map((autoclave) => (
                          <div key={autoclave.id} className="flex items-center space-x-3 p-3 hover:bg-gray-50 border-b last:border-b-0">
                            <Checkbox
                              checked={selectedAutoclavi.includes(autoclave.id)}
                              onCheckedChange={(checked) => handleAutoclaveSelection(autoclave.id, !!checked)}
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm">{autoclave.nome}</span>
                                <Badge variant="outline" className="text-xs">{autoclave.codice}</Badge>
                                <Badge variant="secondary" className="text-xs">{autoclave.max_load_kg}kg</Badge>
                              </div>
                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <span>{autoclave.lunghezza}×{autoclave.larghezza_piano}mm</span>
                                <span>•</span>
                                <span>{autoclave.num_linee_vuoto} linee</span>
                                <span>•</span>
                                <span>{autoclave.temperatura_max}°C</span>
                                <span>•</span>
                                <span>{autoclave.pressione_max}bar</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Step 3: Configurazione Parametri */}
              {currentStep === WizardStep.CONFIGURE_PARAMS && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="padding" className="flex items-center gap-2 text-sm">
                        Padding (mm)
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Info className="h-3 w-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="text-xs">Spazio di sicurezza attorno a ogni tool</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </Label>
                      <Input
                        id="padding"
                        type="number"
                        min="3"
                        max="50"
                        value={parametri.padding_mm}
                        onChange={(e) => setParametri(prev => ({ 
                          ...prev, 
                          padding_mm: parseInt(e.target.value) || 10 
                        }))}
                        className={`${parametri.padding_mm < 3 ? 'border-red-500' : ''} text-sm`}
                      />
                      {parametri.padding_mm < 3 && (
                        <p className="text-xs text-red-600">Minimo 3mm richiesto</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="distance" className="flex items-center gap-2 text-sm">
                        Distanza Minima (mm)
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Info className="h-3 w-3 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent>
                              <p className="text-xs">Distanza minima tra tool adiacenti</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </Label>
                      <Input
                        id="distance"
                        type="number"
                        min="3"
                        max="30"
                        value={parametri.min_distance_mm}
                        onChange={(e) => setParametri(prev => ({ 
                          ...prev, 
                          min_distance_mm: parseInt(e.target.value) || 8 
                        }))}
                        className={`${parametri.min_distance_mm < 3 ? 'border-red-500' : ''} text-sm`}
                      />
                      {parametri.min_distance_mm < 3 && (
                        <p className="text-xs text-red-600">Minimo 3mm richiesto</p>
                      )}
                    </div>
                  </div>

                  {/* Anteprima Impatto Parametri */}
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2 text-sm">Impatto Configurazione</h4>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-blue-700 font-medium">Padding {parametri.padding_mm}mm:</span>
                        <p className="text-blue-600">
                          {parametri.padding_mm <= 5 ? '🎯 Massima densità' : 
                           parametri.padding_mm <= 10 ? '⚖️ Bilanciato' : 
                           '🛡️ Sicurezza elevata'}
                        </p>
                      </div>
                      <div>
                        <span className="text-blue-700 font-medium">Distanza {parametri.min_distance_mm}mm:</span>
                        <p className="text-blue-600">
                          {parametri.min_distance_mm <= 5 ? '📦 Compatto' : 
                           parametri.min_distance_mm <= 10 ? '📏 Standard' : 
                           '🔒 Conservativo'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Review e Generazione */}
              {currentStep === WizardStep.REVIEW_GENERATE && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Riepilogo ODL */}
                    <div className="p-4 border rounded-lg bg-blue-50">
                      <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        ODL Selezionati ({selectedOdl.length})
                      </h4>
                      <div className="space-y-1 text-sm max-h-32 overflow-y-auto">
                        {selectedOdl.slice(0, 6).map(odlId => {
                          const odl = odlList.find(o => o.id === odlId)
                          return odl ? (
                            <div key={odl.id} className="flex justify-between">
                              <span>ODL #{odl.id}</span>
                              <span className="text-muted-foreground">{odl.tool.peso || 0}kg</span>
                            </div>
                          ) : null
                        })}
                        {selectedOdl.length > 6 && (
                          <p className="text-xs text-muted-foreground">
                            ...e altri {selectedOdl.length - 6} ODL
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Riepilogo Autoclavi */}
                    <div className="p-4 border rounded-lg bg-orange-50">
                      <h4 className="font-medium text-orange-900 mb-2 flex items-center gap-2">
                        <Flame className="h-4 w-4" />
                        Autoclavi Selezionate ({selectedAutoclavi.length})
                      </h4>
                      <div className="space-y-1 text-sm">
                        {selectedAutoclavi.map(autoclaveId => {
                          const autoclave = autoclaveList.find(a => a.id === autoclaveId)
                          return autoclave ? (
                            <div key={autoclave.id} className="flex justify-between">
                              <span>{autoclave.nome}</span>
                              <span className="text-muted-foreground">{autoclave.max_load_kg}kg</span>
                            </div>
                          ) : null
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Parametri e Generazione */}
                  <div className="p-4 border rounded-lg bg-green-50">
                    <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Configurazione Finale
                    </h4>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div className="flex justify-between">
                        <span>Padding:</span>
                        <span className="font-medium">{parametri.padding_mm}mm</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Distanza minima:</span>
                        <span className="font-medium">{parametri.min_distance_mm}mm</span>
                      </div>
                    </div>
                    
                    <Button 
                      onClick={handleGenerate}
                      disabled={generating}
                      className="w-full"
                      size="lg"
                    >
                      {generating ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Generazione in corso...
                        </>
                      ) : (
                        <>
                          <Zap className="h-4 w-4 mr-2" />
                          Genera Nesting Batch
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}

              {/* Messaggio di validazione */}
              {getStepValidationMessage() && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium text-yellow-800">
                      {getStepValidationMessage()}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>

            {/* Navigation Footer */}
            <div className="border-t px-6 py-4">
              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={handlePrevious}
                  disabled={currentStep === WizardStep.SELECT_ODL}
                  size="sm"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Indietro
                </Button>

                {currentStep < WizardStep.REVIEW_GENERATE ? (
                  <Button
                    onClick={handleNext}
                    disabled={!canProceedToNext()}
                    size="sm"
                  >
                    Avanti
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                ) : null}
              </div>
            </div>
          </Card>
        </div>

        {/* Summary Sidebar Compatto */}
        {!sidebarCollapsed && (
          <div className="lg:col-span-1">
            <CompactSummary />
          </div>
        )}
      </div>
    </div>
  )
} 