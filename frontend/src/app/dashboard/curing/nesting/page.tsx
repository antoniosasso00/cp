'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
import { Loader2, Package, Flame, AlertCircle, CheckCircle2, RefreshCw, Info, ChevronUp, ChevronDown, Eye, Zap, PlayCircle, Clock } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import BatchListWithControls from '@/components/batch-nesting/BatchListWithControls'
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

interface NestingParams {
  padding_mm: number
  min_distance_mm: number
}

export default function NestingPage() {
  const { toast } = useToast()
  const router = useRouter()
  
  // Stati per i dati
  const [odlList, setOdlList] = useState<ODLData[]>([])
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Stati per le selezioni
  const [selectedOdl, setSelectedOdl] = useState<number[]>([])
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<number[]>([])
  
  // Stati per i parametri
  const [parametri, setParametri] = useState({
    padding_mm: 10,
    min_distance_mm: 8
  })

  // ✅ NUOVO: State per gestire batch recenti
  const [recentBatches, setRecentBatches] = useState<any[]>([])
  const [showRecentBatches, setShowRecentBatches] = useState(false)

  // Caricamento dati iniziali
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Caricamento dati per nesting...')

      // ✅ RISOLTO: Usa la libreria API invece di fetch diretto
      const [nestingData, batchesData] = await Promise.all([
        batchNestingApi.getData(),
        batchNestingApi.getAll({ limit: 10 })
      ])

      console.log('📊 Dati nesting ricevuti:', nestingData)
      
      // I dati sono già filtrati lato server
      const odlInAttesaCura = nestingData.odl_in_attesa_cura || []
      const autoclaveDisponibili = nestingData.autoclavi_disponibili || []
      
      setOdlList(odlInAttesaCura)
      setAutoclaveList(autoclaveDisponibili)

      // ✅ NUOVO: Carica batch recenti
      setRecentBatches(batchesData.slice(0, 5))

      toast({
        title: 'Dati caricati',
        description: `Trovati ${odlInAttesaCura.length} ODL in attesa cura e ${autoclaveDisponibili.length} autoclavi disponibili.`,
      })

    } catch (error) {
      console.error('❌ Errore nel caricamento dati:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto nel caricamento dati'
      setError(errorMessage)
      toast({
        title: 'Errore di caricamento',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  // Gestione selezione ODL
  const handleOdlSelection = (odlId: number, checked: boolean) => {
    if (checked) {
      setSelectedOdl(prev => [...prev, odlId])
    } else {
      setSelectedOdl(prev => prev.filter(id => id !== odlId))
    }
  }

  const handleSelectAllOdl = () => {
    setSelectedOdl(odlList.map(odl => odl.id))
  }

  const handleDeselectAllOdl = () => {
    setSelectedOdl([])
  }

  // Gestione selezione autoclavi
  const handleAutoclaveSelection = (autoclaveId: number, checked: boolean) => {
    if (checked) {
      setSelectedAutoclavi(prev => [...prev, autoclaveId])
    } else {
      setSelectedAutoclavi(prev => prev.filter(id => id !== autoclaveId))
    }
  }

  const handleSelectAllAutoclavi = () => {
    setSelectedAutoclavi(autoclaveList.map(autoclave => autoclave.id))
  }

  const handleDeselectAllAutoclavi = () => {
    setSelectedAutoclavi([])
  }

  // Generazione nesting
  const handleGenerateNesting = async () => {
    if (selectedOdl.length === 0) {
      toast({
        title: 'Selezione richiesta',
        description: 'Seleziona almeno un ODL per procedere.',
        variant: 'destructive'
      })
      return
    }

    if (selectedAutoclavi.length === 0) {
      toast({
        title: 'Selezione richiesta',
        description: 'Seleziona almeno un\'autoclave per procedere.',
        variant: 'destructive'
      })
      return
    }

    try {
      setGenerating(true)
      
      toast({
        title: 'Generazione nesting in corso...',
        description: `Elaborazione di ${selectedOdl.length} ODL su ${selectedAutoclavi.length} autoclave/i.`,
      })

      const payload = {
        odl_ids: selectedOdl.map(id => id.toString()),
        autoclave_ids: selectedAutoclavi.map(id => id.toString()),
        parametri: {
          padding_mm: parametri.padding_mm,
          min_distance_mm: parametri.min_distance_mm,
          priorita_area: false
        }
      }

      console.log('📤 Payload inviato:', payload)

      // ✅ RISOLTO: Usa la libreria API invece di fetch diretto
      const result = await batchNestingApi.genera(payload)
      console.log('✅ Nesting generato:', result)

      if (result.success && result.batch_id) {
        toast({
          title: 'Nesting generato con successo!',
          description: `${result.message || 'Il nesting è stato creato correttamente.'} Reindirizzamento in corso...`,
        })
        
        // ✅ AGGIORNA: Ricarica batch recenti prima del redirect
        try {
          const batchesData = await batchNestingApi.getAll({ limit: 10 })
          setRecentBatches(batchesData.slice(0, 5))
        } catch (error) {
          console.error('Errore nel ricaricamento batch:', error)
        }
        
        router.push(`/dashboard/curing/nesting/result/${result.batch_id}`)
      } else {
        const errorMsg = result.message || 'Il nesting non è stato generato correttamente'
        throw new Error(errorMsg)
      }

    } catch (error) {
      console.error('❌ Errore generazione nesting:', error)
      
      const errorMessage = error instanceof Error ? error.message : 'Errore sconosciuto durante la generazione'
      
      toast({
        title: 'Errore nella generazione del nesting',
        description: errorMessage,
        variant: 'destructive'
      })
    } finally {
      setGenerating(false)
    }
  }

  // Mostra errore se presente
  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Errore di Caricamento
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button onClick={loadData} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Riprova
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Nuovo Nesting Automatico</h1>
        <p className="text-muted-foreground">
          Seleziona ODL e autoclavi per generare un nesting ottimizzato
        </p>
      </div>

      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin mr-2" />
            <span>Caricamento dati...</span>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Sezione ODL */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                ODL in Attesa di Cura
                <Badge variant="secondary">{odlList.length}</Badge>
              </CardTitle>
              <CardDescription>
                Seleziona gli ODL da includere nel nesting
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {odlList.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  Nessun ODL in attesa di cura
                </div>
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleSelectAllOdl}>
                      Seleziona Tutti
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDeselectAllOdl}>
                      Deseleziona Tutti
                    </Button>
                  </div>
                  
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {odlList.map((odl) => (
                      <div key={odl.id} className="flex items-center space-x-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={selectedOdl.includes(odl.id)}
                          onCheckedChange={(checked) => handleOdlSelection(odl.id, !!checked)}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">ODL #{odl.id}</span>
                            <Badge variant="outline">P{odl.priorita}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {odl.parte.descrizione_breve}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Tool: {odl.tool.part_number_tool} | 
                            Valvole: {odl.parte.num_valvole_richieste} |
                            Ciclo: {odl.parte.ciclo_cura?.nome || 'N/A'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Sezione Autoclavi */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5" />
                Autoclavi Disponibili
                <Badge variant="secondary">{autoclaveList.length}</Badge>
              </CardTitle>
              <CardDescription>
                Seleziona le autoclavi da utilizzare per il nesting
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {autoclaveList.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  Nessuna autoclave disponibile
                </div>
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleSelectAllAutoclavi}>
                      Seleziona Tutte
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDeselectAllAutoclavi}>
                      Deseleziona Tutte
                    </Button>
                  </div>
                  
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {autoclaveList.map((autoclave) => (
                      <div key={autoclave.id} className="flex items-center space-x-3 p-3 border rounded-lg">
                        <Checkbox
                          checked={selectedAutoclavi.includes(autoclave.id)}
                          onCheckedChange={(checked) => handleAutoclaveSelection(autoclave.id, !!checked)}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{autoclave.nome}</span>
                            <Badge variant="outline">{autoclave.codice}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {autoclave.lunghezza}×{autoclave.larghezza_piano}mm | 
                            {autoclave.max_load_kg}kg max |
                            {autoclave.num_linee_vuoto} linee vuoto
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Parametri di nesting */}
      <Card>
        <CardHeader>
          <CardTitle>Parametri di Nesting</CardTitle>
          <CardDescription>
            Configura i parametri per l'ottimizzazione del nesting
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Parametri essenziali di nesting */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Parametri di Nesting</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="padding">
                  Padding (mm)
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="inline h-4 w-4 ml-1 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Spazio di sicurezza attorno a ogni tool. Valori bassi massimizzano il numero di ODL.</p>
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
                  onChange={(e) => setParametri(prev => ({ ...prev, padding_mm: parseInt(e.target.value) || 10 }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="distance">
                  Distanza Minima (mm)
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="inline h-4 w-4 ml-1 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Distanza minima tra tool adiacenti. Valori bassi permettono maggiore densità.</p>
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
                  onChange={(e) => setParametri(prev => ({ ...prev, min_distance_mm: parseInt(e.target.value) || 8 }))}
                />
              </div>
            </div>
          </div>

          {/* ✅ NUOVO: Sezione batch recenti */}
          {recentBatches.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Batch Recenti</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRecentBatches(!showRecentBatches)}
                >
                  {showRecentBatches ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {showRecentBatches ? 'Nascondi' : 'Mostra'}
                </Button>
              </div>
              
              {showRecentBatches && (
                <div className="space-y-2">
                  {recentBatches.map((batch) => (
                    <div key={batch.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50">
                      <div className="flex-1">
                        <div className="font-medium">{batch.nome}</div>
                        <div className="text-sm text-muted-foreground">
                          {new Date(batch.created_at).toLocaleDateString('it-IT', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })} • {batch.numero_nesting || 0} ODL
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={batch.stato === 'confermato' ? 'default' : 'secondary'}>
                          {batch.stato}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/dashboard/curing/nesting/result/${batch.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Pulsante di generazione */}
          <div className="flex justify-end gap-4">
            {/* ✅ NUOVO: Pulsante per la preview semplificata */}
            <Button 
              variant="outline"
              onClick={() => router.push('/dashboard/curing/nesting/preview')}
              className="min-w-[200px]"
              size="lg"
            >
              <Eye className="h-4 w-4 mr-2" />
              Preview Semplificata
            </Button>
            
            <Button 
              onClick={handleGenerateNesting}
              disabled={generating || selectedOdl.length === 0 || selectedAutoclavi.length === 0}
              className="min-w-[200px]"
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
                  Genera Nesting
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ✅ NUOVO: Sezione Gestione Batch Esistenti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Gestione Batch Esistenti
          </CardTitle>
          <CardDescription>
            Controlla e gestisci i batch di nesting già creati
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BatchListWithControls
            title="Batch di Nesting"
            editableOnly={false}
            onBatchUpdated={(batchId, newData) => {
              console.log(`✅ Batch ${batchId} aggiornato:`, newData)
              // Ricarica la lista dei batch recenti
              loadData()
            }}
            userInfo={{ userId: 'utente_frontend', userRole: 'Curing' }}
          />
        </CardContent>
      </Card>
    </div>
  )
} 