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
import { Loader2, Package, Flame, AlertCircle, CheckCircle2 } from 'lucide-react'
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
  accorpamento_odl: boolean
}

export default function NestingPage() {
  const { toast } = useToast()
  const router = useRouter()
  
  // Stati per i dati
  const [odlList, setOdlList] = useState<ODLData[]>([])
  const [autoclaveList, setAutoclaveList] = useState<AutoclaveData[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  
  // Stati per le selezioni
  const [selectedOdl, setSelectedOdl] = useState<number[]>([])
  const [selectedAutoclavi, setSelectedAutoclavi] = useState<number[]>([])
  
  // Stati per i parametri
  const [parametri, setParametri] = useState<NestingParams>({
    padding_mm: 20,
    min_distance_mm: 15,
    priorita_area: true,
    accorpamento_odl: false
  })

  // Caricamento dati iniziali
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Carica ODL in attesa di cura
      const odlResponse = await fetch('/api/odl?status=Attesa Cura')
      if (!odlResponse.ok) {
        throw new Error('Errore nel caricamento degli ODL')
      }
      const odlData = await odlResponse.json()
      setOdlList(odlData)

      // Carica autoclavi disponibili
      const autoclaveResponse = await fetch('/api/autoclavi?stato=DISPONIBILE')
      if (!autoclaveResponse.ok) {
        throw new Error('Errore nel caricamento delle autoclavi')
      }
      const autoclaveData = await autoclaveResponse.json()
      setAutoclaveList(autoclaveData)

    } catch (error) {
      console.error('Errore nel caricamento dati:', error)
      toast({
        title: 'Errore di caricamento',
        description: 'Non è stato possibile caricare i dati. Riprova più tardi.',
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
        title: 'Generazione in corso',
        description: 'Sto elaborando il nesting. Attendere...',
      })

      const payload = {
        odl_ids: selectedOdl.map(id => id.toString()),
        autoclave_ids: selectedAutoclavi.map(id => id.toString()),
        parametri: parametri
      }

      console.log('Payload inviato:', payload)

      const response = await fetch('/api/nesting/genera', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Errore ${response.status}`)
      }

      const result = await response.json()
      console.log('Risultato nesting:', result)

      if (result.batch_id) {
        toast({
          title: 'Nesting generato!',
          description: 'Il nesting è stato creato con successo.',
          variant: 'default'
        })
        
        // Naviga alla pagina del risultato
        router.push(`/dashboard/curing/nesting/result/${result.batch_id}`)
      } else {
        throw new Error('Batch ID non ricevuto dal server')
      }

    } catch (error) {
      console.error('Errore nella generazione nesting:', error)
      toast({
        title: 'Errore di generazione',
        description: error instanceof Error ? error.message : 'Errore sconosciuto durante la generazione del nesting.',
        variant: 'destructive'
      })
    } finally {
      setGenerating(false)
    }
  }

  // Rendering componente loading
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Caricamento dati...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nuovo Nesting Automatico</h1>
          <p className="text-muted-foreground">
            Seleziona ODL e autoclavi per generare un nesting ottimizzato
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAllOdl}
                disabled={odlList.length === 0}
              >
                Seleziona Tutti
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeselectAllOdl}
                disabled={selectedOdl.length === 0}
              >
                Deseleziona Tutti
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {odlList.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <AlertCircle className="h-5 w-5 mr-2" />
                Nessun ODL in attesa di cura
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {odlList.map((odl) => (
                  <div
                    key={odl.id}
                    className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <Checkbox
                      checked={selectedOdl.includes(odl.id)}
                      onCheckedChange={(checked) => handleOdlSelection(odl.id, checked as boolean)}
                    />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">ODL #{odl.id}</span>
                        <Badge variant="outline">Priorità {odl.priorita}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <div><strong>Part Number:</strong> {odl.parte.part_number}</div>
                        <div><strong>Descrizione:</strong> {odl.parte.descrizione_breve}</div>
                        <div><strong>Tool:</strong> {odl.tool.part_number_tool}</div>
                        <div><strong>Dimensioni Tool:</strong> {odl.tool.lunghezza_piano}×{odl.tool.larghezza_piano} mm</div>
                        {odl.parte.ciclo_cura && (
                          <div><strong>Ciclo Cura:</strong> {odl.parte.ciclo_cura.nome}</div>
                        )}
                        <div><strong>Valvole:</strong> {odl.parte.num_valvole_richieste}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAllAutoclavi}
                disabled={autoclaveList.length === 0}
              >
                Seleziona Tutti
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeselectAllAutoclavi}
                disabled={selectedAutoclavi.length === 0}
              >
                Deseleziona Tutti
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {autoclaveList.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <AlertCircle className="h-5 w-5 mr-2" />
                Nessuna autoclave disponibile
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {autoclaveList.map((autoclave) => (
                  <div
                    key={autoclave.id}
                    className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <Checkbox
                      checked={selectedAutoclavi.includes(autoclave.id)}
                      onCheckedChange={(checked) => handleAutoclaveSelection(autoclave.id, checked as boolean)}
                    />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{autoclave.nome}</span>
                        <Badge variant="secondary">{autoclave.codice}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <div><strong>Dimensioni:</strong> {autoclave.lunghezza}×{autoclave.larghezza_piano} mm</div>
                        <div><strong>Max Temperatura:</strong> {autoclave.temperatura_max}°C</div>
                        <div><strong>Max Pressione:</strong> {autoclave.pressione_max} bar</div>
                        <div><strong>Carico Max:</strong> {autoclave.max_load_kg} kg</div>
                        <div><strong>Linee Vuoto:</strong> {autoclave.num_linee_vuoto}</div>
                        {autoclave.use_secondary_plane && (
                          <div className="text-green-600">✓ Piano secondario disponibile</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Parametri Nesting */}
      <Card>
        <CardHeader>
          <CardTitle>Parametri Nesting</CardTitle>
          <CardDescription>
            Configura i parametri per l'algoritmo di ottimizzazione
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="padding">Padding (mm)</Label>
              <Input
                id="padding"
                type="number"
                min="0"
                max="100"
                value={parametri.padding_mm}
                onChange={(e) => setParametri(prev => ({ ...prev, padding_mm: Number(e.target.value) }))}
              />
              <p className="text-xs text-muted-foreground">
                Spazio minimo attorno a ogni tool
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="distance">Distanza Minima (mm)</Label>
              <Input
                id="distance"
                type="number"
                min="0"
                max="100"
                value={parametri.min_distance_mm}
                onChange={(e) => setParametri(prev => ({ ...prev, min_distance_mm: Number(e.target.value) }))}
              />
              <p className="text-xs text-muted-foreground">
                Distanza minima tra i tool
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Priorità Area</Label>
                <p className="text-xs text-muted-foreground">
                  Ottimizza per utilizzo massimo dell'area
                </p>
              </div>
              <Switch
                checked={parametri.priorita_area}
                onCheckedChange={(checked) => setParametri(prev => ({ ...prev, priorita_area: checked }))}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Accorpamento ODL</Label>
                <p className="text-xs text-muted-foreground">
                  Raggruppa ODL con caratteristiche simili
                </p>
              </div>
              <Switch
                checked={parametri.accorpamento_odl}
                onCheckedChange={(checked) => setParametri(prev => ({ ...prev, accorpamento_odl: checked }))}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Riepilogo e Pulsante Generazione */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="font-medium">
                  {selectedOdl.length} ODL selezionati, {selectedAutoclavi.length} autoclavi selezionate
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                Verifica la selezione e clicca "Genera Nesting" per avviare l'algoritmo
              </p>
            </div>
            
            <Button
              onClick={handleGenerateNesting}
              disabled={selectedOdl.length === 0 || selectedAutoclavi.length === 0 || generating}
              size="lg"
              className="min-w-40"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generando...
                </>
              ) : (
                'Genera Nesting'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 