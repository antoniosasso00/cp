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
import { Loader2, Package, Flame, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react'
import { useRouter } from 'next/navigation'

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
  use_secondary_plane: boolean
}

interface NestingParams {
  padding_mm: number
  min_distance_mm: number
  priorita_area: boolean
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
  const [parametri, setParametri] = useState<NestingParams>({
    padding_mm: 20,
    min_distance_mm: 15,
    priorita_area: true
  })

  // Caricamento dati iniziali
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Caricamento dati per nesting...')

      // Carica ODL in attesa di cura - URL corretto con encoding
      const statusParam = encodeURIComponent('Attesa Cura')
      const odlResponse = await fetch(`/api/odl?status=${statusParam}`)
      
      if (!odlResponse.ok) {
        throw new Error(`Errore nel caricamento degli ODL: ${odlResponse.status} ${odlResponse.statusText}`)
      }
      const odlData = await odlResponse.json()
      console.log('✅ ODL caricati:', odlData.length)
      setOdlList(odlData)

      // Carica autoclavi disponibili - utilizzando l'enum corretto
      const autoclaveResponse = await fetch('/api/autoclavi?stato=DISPONIBILE')
      if (!autoclaveResponse.ok) {
        throw new Error(`Errore nel caricamento delle autoclavi: ${autoclaveResponse.status} ${autoclaveResponse.statusText}`)
      }
      const autoclaveData = await autoclaveResponse.json()
      console.log('✅ Autoclavi caricate:', autoclaveData.length)
      setAutoclaveList(autoclaveData)

      toast({
        title: 'Dati caricati',
        description: `Trovati ${odlData.length} ODL e ${autoclaveData.length} autoclavi disponibili.`,
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
          priorita_area: parametri.priorita_area
        }
      }

      console.log('📤 Payload inviato:', payload)

      const response = await fetch('/api/nesting/genera', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorDetail = errorData.detail || errorData.message || `Errore HTTP ${response.status}`
        throw new Error(errorDetail)
      }

      const result = await response.json()
      console.log('✅ Nesting generato:', result)

      if (result.success && result.batch_id) {
        toast({
          title: 'Nesting generato con successo!',
          description: `${result.message || 'Il nesting è stato creato correttamente.'} Reindirizzamento in corso...`,
        })
        
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
                          {autoclave.use_secondary_plane && (
                            <p className="text-xs text-blue-600">✓ Piano secondario disponibile</p>
                          )}
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
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="padding">Padding (mm)</Label>
              <Input
                id="padding"
                type="number"
                value={parametri.padding_mm}
                onChange={(e) => setParametri(prev => ({ 
                  ...prev, 
                  padding_mm: Number(e.target.value) 
                }))}
                min={0}
                max={100}
              />
              <p className="text-xs text-muted-foreground">
                Spazio aggiuntivo attorno a ciascun tool
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="distance">Distanza minima (mm)</Label>
              <Input
                id="distance"
                type="number"
                value={parametri.min_distance_mm}
                onChange={(e) => setParametri(prev => ({ 
                  ...prev, 
                  min_distance_mm: Number(e.target.value) 
                }))}
                min={0}
                max={100}
              />
              <p className="text-xs text-muted-foreground">
                Distanza minima tra i tool nell'autoclave
              </p>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Switch
                checked={parametri.priorita_area}
                onCheckedChange={(checked) => setParametri(prev => ({ 
                  ...prev, 
                  priorita_area: checked 
                }))}
              />
              <Label>Priorità per area utilizzata</Label>
            </div>
            <p className="text-sm text-muted-foreground">
              Se attivo, l'algoritmo privilegia l'utilizzo ottimale dello spazio. 
              Se disattivo, privilegia il numero massimo di ODL posizionati.
            </p>
          </div>

          <Separator />

          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            <span className="text-sm text-green-800">
              Pronto per generare nesting con {selectedOdl.length} ODL e {selectedAutoclavi.length} autoclave/i
            </span>
          </div>

          <Button 
            onClick={handleGenerateNesting} 
            disabled={generating || selectedOdl.length === 0 || selectedAutoclavi.length === 0}
            className="w-full"
            size="lg"
          >
            {generating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generazione in corso...
              </>
            ) : (
              'Genera Nesting'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
} 