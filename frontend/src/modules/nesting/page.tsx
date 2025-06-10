'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Button } from '@/shared/components/ui/button'
import { Badge } from '@/shared/components/ui/badge'
import { Checkbox } from '@/shared/components/ui/checkbox'
import { Input } from '@/shared/components/ui/input'
import { Label } from '@/shared/components/ui/label'
import { Separator } from '@/shared/components/ui/separator'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { 
  Loader2, 
  Package, 
  Settings, 
  PlayCircle, 
  RefreshCw,
  CheckCircle2,
  Clock,
  LayoutGrid,
  Zap,
  Shield,
  Target,
  RotateCcw
} from 'lucide-react'
import { batchNestingApi } from '@/shared/lib/api'

interface ODLItem {
  id: number
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
}

interface NestingParams {
  padding_mm: number
  min_distance_mm: number
}

// Preset parametri
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
  AGGRESSIVO: {
    padding_mm: 1,
    min_distance_mm: 1,
    nome: 'Aggressivo',
    descrizione: 'Massima efficienza, controllo accurato',
    icon: Zap
  },
}

export default function NestingPage() {
  const router = useRouter()
  const { toast } = useStandardToast()

  // Data states
  const [odls, setOdls] = useState<ODLItem[]>([])
  const [autoclavi, setAutoclavi] = useState<AutoclaveItem[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  // Selection states
  const [selectedOdls, setSelectedOdls] = useState<number[]>([])
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<number[]>([])

  // Parameters
  const [params, setParams] = useState<NestingParams>({
    padding_mm: 10,
    min_distance_mm: 8
  })

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

  const handlePresetChange = (preset: typeof PARAMETRI_PRESET.STANDARD) => {
    setParams({
      padding_mm: preset.padding_mm,
      min_distance_mm: preset.min_distance_mm
    })
    
    toast({
      title: `Preset ${preset.nome} applicato`,
      description: preset.descrizione
    })
  }

  const resetToDefault = () => {
    setParams({
      padding_mm: 10,
      min_distance_mm: 8
    })
    
    toast({
      title: 'Parametri ripristinati',
      description: 'Valori impostati a standard predefiniti'
    })
  }

  const handleGenerate = async () => {
    if (selectedOdls.length === 0) {
      toast({
        title: 'Selezione richiesta',
        description: 'Seleziona almeno un ODL',
        variant: 'destructive'
      })
      return
    }

    if (selectedAutoclavi.length === 0) {
      toast({
        title: 'Selezione richiesta', 
        description: 'Seleziona almeno un\'autoclave',
        variant: 'destructive'
      })
      return
    }

    // Validazione parametri più permissiva
    if (params.padding_mm < 0.1 || params.min_distance_mm < 0.1) {
      toast({
        title: 'Parametri non validi',
        description: 'I valori devono essere almeno 0.1mm',
        variant: 'destructive'
      })
      return
    }

    // Arrotondamento parametri per evitare problemi di precisione float
    const roundedParams = {
      padding_mm: Math.round(params.padding_mm * 10) / 10, // Arrotonda a 1 decimale
      min_distance_mm: Math.round(params.min_distance_mm * 10) / 10
    }

    console.log('🔧 Parametri originali:', params)
    console.log('🔧 Parametri arrotondati:', roundedParams)

    try {
      setGenerating(true)

      // Debug dettagliato
      console.log('🚀 Generazione nesting con parametri arrotondati:', roundedParams)
      if (roundedParams.padding_mm < 1 || roundedParams.min_distance_mm < 1) {
        console.warn('⚡ Modalità aggressiva attiva:', roundedParams)
        
        // Toast informativo per modalità aggressiva
        toast({
          title: 'Modalità aggressiva attivata',
          description: `Generazione con padding ${roundedParams.padding_mm}mm e distanza ${roundedParams.min_distance_mm}mm`,
          variant: 'warning'
        })
      }

      console.log('📤 Parametri da inviare:', JSON.stringify(roundedParams, null, 2))
      console.log('📤 ODL selezionati:', selectedOdls)
      console.log('📤 Autoclavi selezionate:', selectedAutoclavi)

      let response
      if (selectedAutoclavi.length === 1) {
        response = await batchNestingApi.genera({
          odl_ids: selectedOdls.map(String),
          autoclave_ids: selectedAutoclavi.map(String),
          parametri: roundedParams
        })
      } else {
        response = await batchNestingApi.generaMulti({
          odl_ids: selectedOdls.map(String),
          parametri: roundedParams
        })
      }

      console.log('✅ Risposta API nesting:', response)

      if (response.success && response.best_batch_id) {
        toast({
          title: 'Nesting generato',
          description: response.message
        })
        
        router.push(`/nesting/result/${response.best_batch_id}${selectedAutoclavi.length > 1 ? '?multi=true' : ''}`)
      } else {
        throw new Error(response.message || 'Generazione fallita')
      }

    } catch (error) {
      console.error('❌ Errore generazione nesting:', error)
      console.error('📤 Parametri che hanno causato l\'errore:', roundedParams)
      
      // Migliore gestione dell'errore per evitare [object Object]
      let errorMessage = 'Errore sconosciuto'
      let errorTitle = 'Errore generazione'
      
      if (error instanceof Error) {
        errorMessage = error.message
      } else if (typeof error === 'string') {
        errorMessage = error
      } else if (error && typeof error === 'object') {
        console.error('🔍 Dettaglio errore oggetto:', error)
        
        // Gestione errori API complessi
        if ('response' in error && error.response && typeof error.response === 'object') {
          const response = error.response as any
          console.error('🔍 Response error:', response)
          
          if (response.data && response.data.detail) {
            errorMessage = response.data.detail
          } else if (response.data && response.data.message) {
            errorMessage = response.data.message
          } else if (response.statusText) {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`
          }
        } else if ('detail' in error && typeof error.detail === 'string') {
          errorMessage = error.detail
        } else if ('message' in error && typeof error.message === 'string') {
          errorMessage = error.message
        } else {
          // Fallback per oggetti complessi - mostra le chiavi principali
          try {
            const errorKeys = Object.keys(error as object)
            errorMessage = `Errore con proprietà: ${errorKeys.join(', ')}. Controlla la console per dettagli.`
            console.error('🔍 Proprietà errore:', errorKeys)
            console.error('🔍 Valori errore:', error)
          } catch {
            errorMessage = 'Errore di tipo object non serializzabile'
          }
        }
      }

      // Messaggi specifici per parametri aggressivi
      if (roundedParams.padding_mm < 1 || roundedParams.min_distance_mm < 1) {
        errorTitle = 'Errore parametri aggressivi'
        errorMessage = `Parametri: padding ${roundedParams.padding_mm}mm, distanza ${roundedParams.min_distance_mm}mm. ${errorMessage}`
      }

      toast({
        title: errorTitle,
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Caricamento dati...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Generazione Nesting</h1>
          <p className="text-muted-foreground">
            Configura e genera layout ottimizzati per la cura delle parti
          </p>
        </div>
        <Button onClick={() => router.push('/nesting/list')} variant="outline">
          <LayoutGrid className="mr-2 h-4 w-4" />
          Lista Batch
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ODL Selection */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              ODL Disponibili ({odls.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                onClick={() => setSelectedOdls(odls.map(o => o.id))}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                Tutti
              </Button>
              <Button
                onClick={() => setSelectedOdls([])}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                Nessuno
              </Button>
            </div>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {odls.map((odl) => (
                <div key={odl.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50">
                  <Checkbox
                    checked={selectedOdls.includes(odl.id)}
                    onCheckedChange={(checked) => handleOdlToggle(odl.id, checked as boolean)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">ODL {odl.id}</span>
                      <Badge variant="outline" className="text-xs">P{odl.priorita}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">
                      {odl.parte.part_number}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Tool: {odl.tool.larghezza_piano}×{odl.tool.lunghezza_piano}mm
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Autoclavi Selection */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Autoclavi ({autoclavi.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                onClick={() => setSelectedAutoclavi(autoclavi.map(a => a.id))}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                Tutte
              </Button>
              <Button
                onClick={() => setSelectedAutoclavi([])}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                Nessuna
              </Button>
            </div>

            <div className="space-y-2">
              {autoclavi.map((autoclave) => (
                <div key={autoclave.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50">
                  <Checkbox
                    checked={selectedAutoclavi.includes(autoclave.id)}
                    onCheckedChange={(checked) => handleAutoclaveToggle(autoclave.id, checked as boolean)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{autoclave.nome}</span>
                      <Badge 
                        variant={autoclave.stato === 'DISPONIBILE' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {autoclave.stato}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {autoclave.codice}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {autoclave.lunghezza}×{autoclave.larghezza_piano}mm
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Parameters & Actions */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Parametri
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* Preset Parameters */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Preset Parametri</Label>
              <div className="grid grid-cols-1 gap-2">
                {Object.values(PARAMETRI_PRESET).map((preset) => {
                  const IconComponent = preset.icon
                  const isActive = params.padding_mm === preset.padding_mm && params.min_distance_mm === preset.min_distance_mm
                  
                  return (
                    <Button
                      key={preset.nome}
                      onClick={() => handlePresetChange(preset)}
                      variant={isActive ? "default" : "outline"}
                      size="sm"
                      className="justify-start h-auto p-3"
                    >
                      <div className="flex items-center gap-3 w-full">
                        <IconComponent className="h-4 w-4 flex-shrink-0" />
                        <div className="text-left flex-1">
                          <div className="font-medium text-sm">{preset.nome}</div>
                          <div className="text-xs opacity-70 line-clamp-1">
                            {preset.descrizione}
                          </div>
                        </div>
                        {preset.nome === 'Aggressivo' && (
                          <Badge variant="secondary" className="text-xs">
                            1mm
                          </Badge>
                        )}
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
                  className="h-8 px-2"
                >
                  <RotateCcw className="h-3 w-3" />
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="padding" className="text-sm font-medium">
                    Padding (mm)
                  </Label>
                  <div className="relative">
                    <Input
                      id="padding"
                      type="number"
                      value={params.padding_mm}
                      onChange={(e) => setParams(prev => ({ ...prev, padding_mm: Number(e.target.value) }))}
                      min="0.1"
                      max="200"
                      step="0.1"
                      placeholder="10"
                      className="pr-12"
                    />
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <span className="text-xs text-muted-foreground">mm</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Spazio aggiuntivo attorno ai tool
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="distance" className="text-sm font-medium">
                    Distanza minima (mm)
                  </Label>
                  <div className="relative">
                    <Input
                      id="distance"
                      type="number"
                      value={params.min_distance_mm}
                      onChange={(e) => setParams(prev => ({ ...prev, min_distance_mm: Number(e.target.value) }))}
                      min="0.1"
                      max="200"
                      step="0.1"
                      placeholder="8"
                      className="pr-12"
                    />
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <span className="text-xs text-muted-foreground">mm</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Distanza minima tra i tool
                  </p>
                </div>
              </div>

              {/* Parameter Validation */}
              {(params.padding_mm < 1 || params.min_distance_mm < 1) && (
                <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <Zap className="h-4 w-4 text-amber-600 flex-shrink-0" />
                  <div className="text-xs text-amber-800">
                    <strong>Modalità Aggressiva:</strong> Parametri molto bassi richiedono controllo accurato
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Summary */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>ODL selezionati:</span>
                <Badge variant="outline">{selectedOdls.length}</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Autoclavi selezionate:</span>
                <Badge variant="outline">{selectedAutoclavi.length}</Badge>
              </div>
              {selectedAutoclavi.length > 1 && (
                <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-2 rounded-lg">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Modalità multi-batch attiva</span>
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="space-y-2">
              <Button
                onClick={handleGenerate}
                disabled={generating || selectedOdls.length === 0 || selectedAutoclavi.length === 0}
                className="w-full"
                size="lg"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generazione...
                  </>
                ) : (
                  <>
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Genera Nesting
                  </>
                )}
              </Button>
              
              <Button
                onClick={loadData}
                variant="outline"
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Aggiorna Dati
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 