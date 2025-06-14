'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Checkbox } from '@/shared/components/ui/checkbox'
import { Input } from '@/shared/components/ui/input'
import { Label } from '@/shared/components/ui/label'
import { Separator } from '@/shared/components/ui/separator'
import { Switch } from '@/shared/components/ui/switch'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  ChevronLeft,
  ChevronRight,
  Search,
  Check,
  Play,
  RefreshCw,
  Target,
  Shield,
  Zap
} from 'lucide-react'
import { batchNestingApi, api } from '@/shared/lib/api'

interface ODLItem {
  id: number
  numero_odl: string
  parte: {
    part_number: string
    descrizione_breve: string
  }
  tool: {
    part_number_tool: string
    larghezza_piano: number
    lunghezza_piano: number
  }
  priorita: number
}

interface AutoclaveItem {
  id: number
  nome: string
  codice: string
  lunghezza: number
  larghezza_piano: number
  stato: string
  usa_cavalletti?: boolean | number
  num_linee_vuoto?: number
  capacita_peso_kg?: number
  max_load_kg?: number
  altezza_cavalletto_standard?: number
  clearance_verticale?: number
  max_cavalletti?: number
}

interface NestingParams {
  padding_mm: number
  min_distance_mm: number
}

// Preset parametri - ottimizzati dal test stress aeronautico
const PARAMETRI_PRESET = {
  CONSERVATIVO: {
    padding_mm: 15,
    min_distance_mm: 12,
    nome: 'Conservativo',
    descrizione: 'Massima sicurezza, efficienza minore',
    icon: Shield
  },
  STANDARD: {
    padding_mm: 10,
    min_distance_mm: 8,
    nome: 'Standard',
    descrizione: 'Bilanciamento tra sicurezza ed efficienza',
    icon: Target
  },
  AEROSPACE_OPTIMIZED: {
    padding_mm: 5,
    min_distance_mm: 10,
    nome: 'Aerospace Ottimizzato',
    descrizione: 'Ottimizzato per componenti aeronautici',
    icon: Target
  },
  AGGRESSIVO: {
    padding_mm: 1,
    min_distance_mm: 2,
    nome: 'Ultra Aggressivo',
    descrizione: 'Massima efficienza - controllo accurato richiesto',
    icon: Zap
  },
}

const STEPS = [
  { id: 1, title: 'Selezione ODL', description: 'Seleziona gli ordini di lavoro da processare' },
  { id: 2, title: 'Autoclavi e 2L', description: 'Configura autoclavi e nesting 2 livelli' },
  { id: 3, title: 'Parametri', description: 'Imposta i parametri di nesting' },
  { id: 4, title: 'Riepilogo', description: 'Rivedi e genera nesting' }
]

// Funzione per ottenere il badge della priorità (priorità 1 = più bassa)
const getPriorityBadge = (priorita: number) => {
  if (priorita === 1) return { variant: 'secondary' as const, text: 'Bassa' }
  if (priorita === 2) return { variant: 'default' as const, text: 'Media' }
  if (priorita === 3) return { variant: 'destructive' as const, text: 'Alta' }
  return { variant: 'outline' as const, text: `${priorita}` }
}

export default function NestingPage() {
  const router = useRouter()
  const { toast } = useStandardToast()

  // Workflow state
  const [currentStep, setCurrentStep] = useState(1)

  // Data states
  const [odls, setOdls] = useState<ODLItem[]>([])
  const [autoclavi, setAutoclavi] = useState<AutoclaveItem[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  // Selection states
  const [selectedOdls, setSelectedOdls] = useState<number[]>([])
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<number[]>([])
  const [autoclaviWith2L, setAutoclaviWith2L] = useState<number[]>([])

  // Search states
  const [searchQuery, setSearchQuery] = useState('')

  // Parameters - inizializzato con preset aerospace ottimizzato
  const [params, setParams] = useState<NestingParams>({
    padding_mm: 5,
    min_distance_mm: 10
  })

  // New state for 2L configuration (rimozione campo altezza cavalletti)
  const [nesting2LSettings, setNesting2LSettings] = useState<Record<number, { enabled: boolean }>>({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const data = await batchNestingApi.getData()
      
      setOdls(data.odl_in_attesa_cura || [])
      setAutoclavi(data.autoclavi_disponibili || [])
      
      toast({
        title: 'Dati caricati',
        description: `${data.odl_in_attesa_cura?.length || 0} ODL e ${data.autoclavi_disponibili?.length || 0} autoclavi disponibili`
      })
    } catch (error) {
      toast({
        title: 'Errore caricamento',
        description: 'Impossibile caricare i dati',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  // Filter ODLs based on search query
  const filteredOdls = odls.filter((odl) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      (odl.numero_odl && odl.numero_odl.toLowerCase().includes(query)) ||
      odl.parte.part_number.toLowerCase().includes(query) ||
      odl.parte.descrizione_breve.toLowerCase().includes(query)
    )
  })

  const handleOdlToggle = (odlId: number, checked: boolean) => {
    setSelectedOdls(prev => 
      checked 
        ? [...prev, odlId]
        : prev.filter(id => id !== odlId)
    )
  }

  const handleAutoclaveToggle = (autoclaveId: number, checked: boolean) => {
    setSelectedAutoclavi(prev =>
      checked
        ? [...prev, autoclaveId]
        : prev.filter(id => id !== autoclaveId)
    )
  }

  const handleAutoclave2LToggle = (autoclaveId: number, checked: boolean) => {
    setAutoclaviWith2L(prev =>
      checked
        ? [...prev, autoclaveId]
        : prev.filter(id => id !== autoclaveId)
    )
  }

  // Funzione per selezionare 2L su tutte le autoclavi compatibili selezionate
  const handleSelectAll2L = () => {
    const autoclaviCompatibili = selectedAutoclavi.filter(autoclaveId => {
      const autoclave = autoclavi.find((a: AutoclaveItem) => a.id === autoclaveId)
      return Boolean(autoclave?.usa_cavalletti)
    })
    
    setAutoclaviWith2L(autoclaviCompatibili)
    
    // Aggiorna anche il nesting2LSettings
    const newSettings = { ...nesting2LSettings }
    autoclaviCompatibili.forEach(id => {
      newSettings[id] = { enabled: true }
    })
    setNesting2LSettings(newSettings)
    
    toast({
      title: '2L Abilitato',
      description: `Nesting 2 livelli attivato su ${autoclaviCompatibili.length} autoclavi compatibili`
    })
  }

  const handleDeselectAll2L = () => {
    setAutoclaviWith2L([])
    
    // Disabilita anche nel nesting2LSettings
    const newSettings = { ...nesting2LSettings }
    Object.keys(newSettings).forEach(key => {
      newSettings[parseInt(key)] = { enabled: false }
    })
    setNesting2LSettings(newSettings)
  }

  const handlePresetChange = (preset: typeof PARAMETRI_PRESET.STANDARD) => {
    setParams({
      padding_mm: preset.padding_mm,
      min_distance_mm: preset.min_distance_mm
    })
    
    toast({
      title: 'Preset applicato',
      description: `Parametri impostati: ${preset.nome}`
    })
  }

  const resetToDefault = () => {
    setParams({
      padding_mm: 5,
      min_distance_mm: 10
    })
  }

  const nextStep = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const canProceedFromStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return selectedOdls.length > 0
      case 2:
        return selectedAutoclavi.length > 0
      case 3:
        return params.padding_mm > 0 && params.min_distance_mm > 0
      case 4:
        return true
      default:
        return false
    }
  }

  const handleGenerate = async () => {
    try {
      setGenerating(true)

      const roundedParams = {
        padding_mm: Math.round(params.padding_mm * 100) / 100,
        min_distance_mm: Math.round(params.min_distance_mm * 100) / 100
      }

      // ✅ FIX TIMEOUT: Usa batchNestingApi.generaMulti che ha timeout esteso (10 minuti)
      console.log('🚀 NESTING GENERATION START:', {
        selectedOdls: selectedOdls.length,
        selectedAutoclavi: selectedAutoclavi.length,
        autoclaviWith2L: autoclaviWith2L.length,
        params: roundedParams
      })

      const requestData = {
        odl_ids: selectedOdls.map(String),
        autoclave_ids: selectedAutoclavi.map(String),
        parametri: roundedParams
      }

      console.log('📡 Calling unified endpoint with EXTENDED TIMEOUT:', requestData)

      // ✅ FIX CRITICO: Usa API wrapper con timeout esteso invece di chiamata diretta
      const responseData = await batchNestingApi.generaMulti(requestData)
      
      console.log('✅ Response received:', responseData)

      // ✅ GESTIONE RISPOSTA SEMPLIFICATA
      if (responseData.success && responseData.best_batch_id) {
        // Successo garantito
        toast({
          title: 'Nesting generato con successo',
          description: responseData.message || `Batch generato: ${responseData.best_batch_id}`
        })
        
        // Redirect semplice
        const redirectUrl = `/nesting/result/${responseData.best_batch_id}${
          selectedAutoclavi.length > 1 ? '?multi=true' : ''
        }`
        
        console.log(`🚀 Redirecting to: ${redirectUrl}`)
        router.push(redirectUrl)
        
      } else {
        // Fallimento
        throw new Error(responseData.message || 'Generazione fallita - nessun batch ID ricevuto')
      }

    } catch (error: any) {
      console.error('❌ GENERATION ERROR:', error)
      
      let errorMessage = 'Errore di generazione'
      
      // ✅ MIGLIORE GESTIONE ERRORI TIMEOUT
      if (error.message?.includes('timeout') || error.name === 'AbortError') {
        errorMessage = 'Timeout generazione - L\'algoritmo sta richiedendo più tempo del previsto. Prova con meno ODL o riprova più tardi.'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }

      toast({
        title: 'Errore generazione',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setGenerating(false)
    }
  }

  // Callback functions removed for simplification

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Caricamento dati...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Generazione Nesting</h1>
          <p className="text-muted-foreground">
            Configura e genera layout ottimizzati per la cura delle parti
          </p>
        </div>
        <Button onClick={() => router.push('/nesting/list')} variant="outline">
          Lista Batch
        </Button>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center space-y-2">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    currentStep > step.id 
                      ? 'bg-green-500 border-green-500 text-white' 
                      : currentStep === step.id 
                        ? 'bg-blue-500 border-blue-500 text-white' 
                        : 'bg-white border-gray-300 text-gray-500'
                  }`}>
                    {currentStep > step.id ? <Check className="h-5 w-5" /> : step.id}
                  </div>
                  <div className="text-center">
                    <p className={`text-sm font-medium ${
                      currentStep >= step.id ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500">{step.description}</p>
                  </div>
                </div>
                {index < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    currentStep > step.id ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Indicatore Generazione con Timeout Info */}
      {generating && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-blue-800">
              <RefreshCw className="h-5 w-5 animate-spin" />
              Generazione in Corso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-blue-700">
              <p>Elaborazione di {selectedOdls.length} ODL per {selectedAutoclavi.length} autoclave...</p>
              <p className="text-xs text-blue-600">
                ⏱️ Timeout esteso: 10 minuti - Attendere completamento...
              </p>
              <div className="text-xs text-blue-500 bg-blue-100 p-2 rounded">
                💡 <strong>Suggerimento:</strong> Se la generazione richiede troppo tempo, 
                prova a ridurre il numero di ODL selezionati o usa parametri meno aggressivi.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step Content */}
      <Card>
        <CardContent className="pt-6">
          {/* Step 1: Selezione ODL */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Selezione ODL</h3>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedOdls(filteredOdls.map(o => o.id))}
                  >
                    Seleziona Tutti
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedOdls([])}
                  >
                    Deseleziona Tutti
                  </Button>
                </div>
              </div>
              
              {/* Ricerca ODL */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Cerca per numero ODL, part number o descrizione..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              {/* Tabella ODL - Layout ottimizzato per evitare sovrapposizioni */}
              <div className="border rounded-lg">
                <div className="p-4 bg-muted/50 border-b">
                  <div className="grid grid-cols-6 gap-4 text-sm font-semibold text-gray-900">
                    <div className="col-span-1 flex items-center">
                      <span className="ml-8">Numero ODL</span>
                    </div>
                    <div className="col-span-2">Part Number</div>
                    <div className="col-span-2">Descrizione</div>
                    <div className="col-span-1">Dimensioni Tool</div>
                  </div>
                </div>
                
                <div className="divide-y max-h-96 overflow-y-auto">
                  {filteredOdls.map((item) => (
                    <div key={item.id} className="p-4 hover:bg-muted/30 transition-colors">
                      <div className="grid grid-cols-6 gap-4 items-center">
                        <div className="col-span-1 flex items-center gap-3">
                          <Checkbox
                            checked={selectedOdls.includes(item.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedOdls([...selectedOdls, item.id])
                              } else {
                                setSelectedOdls(selectedOdls.filter(id => id !== item.id))
                              }
                            }}
                          />
                          <Badge variant="secondary" className="font-mono text-sm font-bold">
                            {item.numero_odl || `ID-${item.id}`}
                          </Badge>
                        </div>
                        
                        <div className="col-span-2">
                          <div className="font-medium text-sm">{item.parte.part_number}</div>
                          <div className="flex gap-1 mt-1">
                            {(() => {
                              const priority = getPriorityBadge(item.priorita)
                              return (
                                <Badge variant={priority.variant} className="text-xs">
                                  {priority.text}
                                </Badge>
                              )
                            })()}
                          </div>
                        </div>
                        
                        <div className="col-span-2">
                          <div className="text-sm text-muted-foreground">{item.parte.descrizione_breve}</div>
                        </div>
                        
                        <div className="col-span-1">
                          <div className="text-xs text-muted-foreground">
                            {item.tool.larghezza_piano && item.tool.lunghezza_piano ? (
                              <span className="font-mono">
                                {item.tool.larghezza_piano}×{item.tool.lunghezza_piano}mm
                              </span>
                            ) : (
                              'N/A'
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground">
                {selectedOdls.length} di {filteredOdls.length} ODL selezionati
              </div>
            </div>
          )}

          {/* Step 2: Autoclavi e Nesting 2L */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Selezione Autoclavi e Configurazione 2L</h3>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedAutoclavi(autoclavi.map(a => a.id))}
                  >
                    Seleziona Tutte
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedAutoclavi([])}
                  >
                    Deseleziona Tutte
                  </Button>
                </div>
              </div>

              {/* Pulsante selezione rapida 2L */}
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                <div>
                  <h4 className="font-medium text-green-900">Selezione Rapida 2L</h4>
                  <p className="text-sm text-green-700">Attiva il nesting a 2 livelli su tutte le autoclavi compatibili selezionate</p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    onClick={handleSelectAll2L}
                    variant="default"
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Abilita 2L su Tutte
                  </Button>
                  <Button 
                    onClick={handleDeselectAll2L}
                    variant="outline"
                    size="sm"
                  >
                    Disabilita Tutte
                  </Button>
                </div>
              </div>
              
              <div className="border rounded-lng">
                <div className="p-4 bg-muted/50 border-b">
                  <div className="grid grid-cols-12 gap-4 text-sm font-semibold text-gray-900">
                    <div className="col-span-1"></div>
                    <div className="col-span-2">Nome</div>
                    <div className="col-span-1">Codice</div>
                    <div className="col-span-2">Dimensioni (mm)</div>
                    <div className="col-span-1">Stato</div>
                    <div className="col-span-2">Specifiche Tecniche</div>
                    <div className="col-span-2">Sistema 2L</div>
                    <div className="col-span-1">Nesting 2L</div>
                  </div>
                </div>
                
                <div className="divide-y max-h-96 overflow-y-auto">
                  {autoclavi.map((autoclave) => (
                    <div key={autoclave.id} className="p-4 hover:bg-muted/30 transition-colors">
                      <div className="grid grid-cols-12 gap-4 items-center">
                        <div className="col-span-1">
                          <Checkbox
                            checked={selectedAutoclavi.includes(autoclave.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedAutoclavi([...selectedAutoclavi, autoclave.id])
                              } else {
                                setSelectedAutoclavi(selectedAutoclavi.filter(id => id !== autoclave.id))
                              }
                            }}
                          />
                        </div>
                        
                        <div className="col-span-2">
                          <div className="font-medium">{autoclave.nome}</div>
                        </div>
                        
                        <div className="col-span-1">
                          <Badge variant="secondary" className="text-xs font-mono">
                            {autoclave.codice}
                          </Badge>
                        </div>
                        
                        <div className="col-span-2 text-sm">
                          <div>{autoclave.lunghezza?.toLocaleString() || 'N/A'} × {autoclave.larghezza_piano?.toLocaleString() || 'N/A'}</div>
                          <div className="text-xs text-muted-foreground">
                            {autoclave.lunghezza && autoclave.larghezza_piano 
                              ? `${((autoclave.lunghezza * autoclave.larghezza_piano) / 1000000).toFixed(1)} m²`
                              : 'Area N/A'
                            }
                          </div>
                        </div>
                        
                        <div className="col-span-1">
                          <Badge 
                            variant={autoclave.stato === 'DISPONIBILE' ? 'default' : 'secondary'}
                            className={`text-xs ${
                              autoclave.stato === 'DISPONIBILE' 
                                ? 'bg-blue-100 text-blue-800 hover:bg-blue-100' 
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {autoclave.stato === 'DISPONIBILE' ? 'DISPONIBILE' : autoclave.stato}
                          </Badge>
                        </div>
                        
                        <div className="col-span-2">
                          <div className="flex flex-wrap gap-1">
                            {/* Linee Vuoto */}
                            {autoclave.num_linee_vuoto && (
                              <Badge variant="outline" className="text-xs">
                                <div className="flex items-center gap-1" title="Numero di linee vuoto disponibili">
                                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                                  {autoclave.num_linee_vuoto} Linee
                                </div>
                              </Badge>
                            )}
                            
                            {/* Carico Massimo */}
                            {autoclave.max_load_kg && (
                              <Badge variant="outline" className="text-xs">
                                <div className="flex items-center gap-1" title="Carico massimo supportato">
                                  <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                                  {autoclave.max_load_kg}kg
                                </div>
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <div className="col-span-2">
                          <div className="flex flex-wrap gap-1">
                            {/* Supporto Cavalletti */}
                            {autoclave.usa_cavalletti ? (
                              <>
                                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                  <div className="flex items-center gap-1" title="Supporta sistema nesting a 2 livelli">
                                    <Check className="w-3 h-3" />
                                    2 Livelli
                                  </div>
                                </Badge>
                                {autoclave.max_cavalletti && (
                                  <Badge variant="outline" className="text-xs">
                                    <div className="flex items-center gap-1" title="Numero massimo di cavalletti supportati">
                                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                      {autoclave.max_cavalletti} Cavalletti
                                    </div>
                                  </Badge>
                                )}
                              </>
                            ) : (
                              <Badge variant="outline" className="text-xs bg-gray-50 text-gray-600 border-gray-200">
                                <div className="flex items-center gap-1" title="Solo piano base - nessun cavalletto supportato">
                                  <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                                  Piano Base
                                </div>
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <div className="col-span-1">
                          <Switch
                            checked={Boolean(autoclave.usa_cavalletti && nesting2LSettings[autoclave.id]?.enabled)}
                            onCheckedChange={(checked) => {
                              setNesting2LSettings(prev => ({
                                ...prev,
                                [autoclave.id]: {
                                  enabled: Boolean(checked && autoclave.usa_cavalletti)
                                }
                              }))
                            }}
                            disabled={!autoclave.usa_cavalletti}
                            className={!autoclave.usa_cavalletti ? 'opacity-50' : ''}
                          />
                        </div>
                      </div>
                      
                      {/* Configurazione 2L espansa se abilitata */}
                      {autoclave.usa_cavalletti && nesting2LSettings[autoclave.id]?.enabled && (
                        <div className="mt-4 p-4 bg-muted/30 rounded-lg border-l-4 border-l-green-500">
                          <h4 className="text-sm font-medium mb-3 text-green-800">
                            Configurazione Nesting 2 Livelli - {autoclave.nome}
                          </h4>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <div className="font-medium mb-1">Configurazione Base:</div>
                              <ul className="space-y-1 text-muted-foreground">
                                <li>• Livello 0: Piano base autoclave (riempito per primo)</li>
                                <li>• Livello 1: Cavalletti ({autoclave.altezza_cavalletto_standard || 100}mm)</li>
                                <li>• Max cavalletti: {autoclave.max_cavalletti || 'N/A'}</li>
                                {autoclave.clearance_verticale && (
                                  <li>• Clearance verticale: {autoclave.clearance_verticale}mm</li>
                                )}
                              </ul>
                            </div>
                            <div>
                              <div className="font-medium mb-1">Specifiche Tecniche:</div>
                              <ul className="space-y-1 text-muted-foreground">
                                <li>• Linee vuoto: {autoclave.num_linee_vuoto} disponibili</li>
                                <li>• Carico max: {autoclave.max_load_kg || 'N/A'}kg totali</li>
                                <li>• Area piano: {autoclave.lunghezza && autoclave.larghezza_piano 
                                  ? `${((autoclave.lunghezza * autoclave.larghezza_piano) / 1000000).toFixed(1)} m²`
                                  : 'N/A'
                                }</li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="text-sm text-muted-foreground">
                {selectedAutoclavi.length} di {autoclavi.length} autoclavi selezionate
              </div>
            </div>
          )}

          {/* Step 3: Parameters */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Parametri di Nesting</h2>

              {/* Preset Parameters */}
              <div className="space-y-4">
                <Label className="text-sm font-medium">Preset Parametri</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.values(PARAMETRI_PRESET).map((preset) => {
                    const IconComponent = preset.icon
                    const isActive = params.padding_mm === preset.padding_mm && params.min_distance_mm === preset.min_distance_mm
                    
                    return (
                      <Button
                        key={preset.nome}
                        onClick={() => handlePresetChange(preset)}
                        variant={isActive ? "default" : "outline"}
                        className="justify-start h-auto p-4"
                      >
                        <div className="flex items-center gap-3 w-full">
                          <IconComponent className="h-5 w-5 flex-shrink-0" />
                          <div className="text-left flex-1">
                            <div className="font-medium">{preset.nome}</div>
                            <div className="text-sm opacity-70">{preset.descrizione}</div>
                          </div>
                        </div>
                      </Button>
                    )
                  })}
                </div>
              </div>

              <Separator />

              {/* Manual Parameters */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Parametri Manuali</Label>
                  <Button
                    onClick={resetToDefault}
                    variant="ghost"
                    size="sm"
                  >
                    Reset
                  </Button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="padding">Padding (mm)</Label>
                    <Input
                      id="padding"
                      type="number"
                      value={params.padding_mm}
                      onChange={(e) => setParams(prev => ({ ...prev, padding_mm: Number(e.target.value) }))}
                      min="0.1"
                      max="200"
                      step="0.1"
                    />
                    <p className="text-xs text-muted-foreground">
                      Spazio aggiuntivo attorno ai tool
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="minDistance">Distanza Minima (mm)</Label>
                    <Input
                      id="minDistance"
                      type="number"
                      value={params.min_distance_mm}
                      onChange={(e) => setParams(prev => ({ ...prev, min_distance_mm: Number(e.target.value) }))}
                      min="0.1"
                      max="200"
                      step="0.1"
                    />
                    <p className="text-xs text-muted-foreground">
                      Distanza minima tra tool adiacenti
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900 mb-2">
                  ℹ️ Informazioni Algoritmo Nesting
                </h4>
                <div className="text-xs text-blue-800 space-y-1">
                  <p><strong>Piano Base:</strong> L'algoritmo riempie sempre per primo il piano base dell'autoclave</p>
                  <p><strong>Cavalletti:</strong> Utilizzati solo quando il piano base è pieno o per ottimizzare l'efficienza</p>
                  <p><strong>Parametri:</strong> Padding e distanza minima applicati a tutti i livelli</p>
                  <p><strong>Ottimizzazione:</strong> Sistema aerospace-grade per massima efficienza di spazio</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Summary */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Riepilogo Configurazione</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* ODL Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">ODL Selezionati</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-blue-600 mb-2">
                      {selectedOdls.length}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      ordini di lavoro pronti per la cura
                    </div>
                  </CardContent>
                </Card>

                {/* Autoclavi Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Autoclavi</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600 mb-2">
                      {selectedAutoclavi.length}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {Object.values(nesting2LSettings).filter(s => s.enabled).length} con nesting 2L
                    </div>
                  </CardContent>
                </Card>

                {/* Parameters Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Parametri</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Padding:</span>
                        <span className="text-sm font-mono">{params.padding_mm}mm</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Distanza minima:</span>
                        <span className="text-sm font-mono">{params.min_distance_mm}mm</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Generation Button */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Generazione</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={handleGenerate}
                      disabled={generating || !canProceedFromStep(4)}
                      className="w-full"
                      size="lg"
                    >
                      {generating ? (
                        <div className="flex items-center gap-2">
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          Generazione...
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <Play className="h-4 w-4" />
                          Genera Nesting
                        </div>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          onClick={prevStep}
          disabled={currentStep === 1}
          variant="outline"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Indietro
        </Button>

        <Button
          onClick={nextStep}
          disabled={currentStep === STEPS.length || !canProceedFromStep(currentStep)}
        >
          Avanti
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>
    </div>
  )
} 