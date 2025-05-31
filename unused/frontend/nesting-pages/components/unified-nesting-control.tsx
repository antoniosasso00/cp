'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Play, Settings, Info, AlertCircle } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { nestingApi, autoclaveApi, odlApi, Autoclave, ODLResponse, ManualNestingResponse, ManualNestingRequest, UnifiedNestingResponse, NestingResponse } from '@/lib/api'
import { AutoMultipleNestingButton } from '@/components/nesting/AutoMultipleNestingButton'

interface UnifiedNestingControlProps {
  onNestingGenerated: () => void
  onPreviewRequested: () => void
}



export function UnifiedNestingControl({ onNestingGenerated, onPreviewRequested }: UnifiedNestingControlProps) {
  const [isAutomatic, setIsAutomatic] = useState(true)
  const [usePianoSupplementare, setUsePianoSupplementare] = useState(false)
  const [selectedAutoclave, setSelectedAutoclave] = useState<string>('')
  const [selectedODLs, setSelectedODLs] = useState<number[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(true)
  
  // Dati per la modalità manuale
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([])
  const [odlDisponibili, setODLDisponibili] = useState<ODLResponse[]>([])
  const [stats, setStats] = useState({
    odlInAttesa: 0,
    autoclaveLibere: 0,
    capacitaTotale: 0
  })

  const { toast } = useToast()

  // Carica i dati iniziali
  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setIsLoadingData(true)
      
      // Carica autoclavi disponibili
      const autoclaveData = await autoclaveApi.getAll()
      const autoclaveLibere = autoclaveData.filter((a: Autoclave) => a.stato === 'DISPONIBILE')
      setAutoclavi(autoclaveLibere)
      
      // Carica ODL in attesa di cura
      const odlData = await odlApi.getAll()
      const odlInAttesa = odlData.filter((o: ODLResponse) => o.status === 'Attesa Cura')
      setODLDisponibili(odlInAttesa)
      
      // Calcola statistiche
      setStats({
        odlInAttesa: odlInAttesa.length,
        autoclaveLibere: autoclaveLibere.length,
        capacitaTotale: autoclaveLibere.reduce((sum: number, a: Autoclave) => sum + (a.num_linee_vuoto || 0), 0)
      })
      
    } catch (error) {
      console.error('Errore nel caricamento dati:', error)
      toast({
        variant: 'destructive',
        title: 'Errore di caricamento',
        description: 'Impossibile caricare i dati per il nesting.',
      })
    } finally {
      setIsLoadingData(false)
    }
  }

  // ✅ SEZIONE 2: Gestisce la generazione del nesting unificata
  const handleGenerateNesting = async () => {
    try {
      setIsGenerating(true)
      
      if (isAutomatic) {
        // Modalità automatica - considera l'opzione piano supplementare
        const result: NestingResponse = await nestingApi.generateAuto()
        
        toast({
          title: 'Nesting automatico completato!',
          description: `Nuovo nesting #${result.id} creato per autoclave ${result.autoclave.nome}`,
        })
        
      } else {
        // Modalità manuale
        if (!selectedAutoclave || selectedODLs.length === 0) {
          toast({
            variant: 'destructive',
            title: 'Selezione incompleta',
            description: 'Seleziona un\'autoclave e almeno un ODL per il nesting manuale.',
          })
          return
        }
        
        // ✅ SEZIONE 2: Unifica la creazione manuale con opzione piano supplementare
        const noteComplete = `Nesting manuale - Piano supplementare: ${usePianoSupplementare ? 'Abilitato' : 'Disabilitato'}`
        
        const result: ManualNestingResponse = await nestingApi.generateManual({
          odl_ids: selectedODLs,
          note: noteComplete
        })
        
        toast({
          title: 'Nesting manuale completato!',
          description: `${result.odl_pianificati?.length || 0} ODL pianificati su ${result.autoclavi?.length || 0} autoclavi`,
        })
        
        // Reset selezioni per modalità manuale
        setSelectedODLs([])
        setSelectedAutoclave('')
      }
      
      // Ricarica i dati e notifica il parent
      await loadInitialData()
      onNestingGenerated()
      
    } catch (error) {
      console.error('Errore nella generazione del nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella generazione',
        description: 'Impossibile generare il nesting. Verifica i dati selezionati.',
      })
    } finally {
      setIsGenerating(false)
    }
  }

  // Gestisce la preview del nesting
  const handlePreview = async () => {
    try {
      await nestingApi.getPreview()
      onPreviewRequested()
    } catch (error) {
      console.error('Errore nella preview:', error)
      toast({
        variant: 'destructive',
        title: 'Errore nella preview',
        description: 'Impossibile generare la preview del nesting.',
      })
    }
  }

  // Gestisce la selezione/deselezione di un ODL
  const handleODLToggle = (odlId: number) => {
    setSelectedODLs(prev => 
      prev.includes(odlId) 
        ? prev.filter(id => id !== odlId)
        : [...prev, odlId]
    )
  }

  if (isLoadingData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Caricamento dati...</span>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Statistiche rapide */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">{stats.odlInAttesa}</div>
            <div className="text-sm text-muted-foreground">ODL in attesa</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">{stats.autoclaveLibere}</div>
            <div className="text-sm text-muted-foreground">Autoclavi libere</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-purple-600">{stats.capacitaTotale}</div>
            <div className="text-sm text-muted-foreground">Valvole totali</div>
          </CardContent>
        </Card>
      </div>

      {/* Controlli principali */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configurazione Nesting
          </CardTitle>
          <CardDescription>
            Configura le opzioni per la generazione del nesting
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Toggle modalità automatica/manuale */}
          <div className="flex items-center space-x-2">
            <Switch
              id="automatic-mode"
              checked={isAutomatic}
              onCheckedChange={setIsAutomatic}
            />
            <Label htmlFor="automatic-mode" className="text-sm font-medium">
              {isAutomatic ? 'Modalità Automatica' : 'Modalità Manuale'}
            </Label>
            <Badge variant={isAutomatic ? 'default' : 'secondary'}>
              {isAutomatic ? 'AUTO' : 'MANUALE'}
            </Badge>
          </div>

          {/* Opzione piano supplementare */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="piano-supplementare"
              checked={usePianoSupplementare}
              onCheckedChange={(checked) => setUsePianoSupplementare(checked === true)}
            />
            <Label htmlFor="piano-supplementare" className="text-sm">
              Utilizza piano supplementare (se disponibile)
            </Label>
          </div>

          {/* Controlli modalità manuale */}
          {!isAutomatic && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-medium">Selezione Manuale</h4>
              
              {/* Selezione autoclave */}
              <div className="space-y-2">
                <Label>Autoclave</Label>
                <Select value={selectedAutoclave} onValueChange={setSelectedAutoclave}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona un'autoclave" />
                  </SelectTrigger>
                  <SelectContent>
                    {autoclavi.map(autoclave => (
                      <SelectItem key={autoclave.id} value={autoclave.id.toString()}>
                        {autoclave.nome} - {autoclave.num_linee_vuoto} valvole
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Selezione ODL */}
              <div className="space-y-2">
                <Label>ODL da includere ({selectedODLs.length} selezionati)</Label>
                <div className="max-h-40 overflow-y-auto border rounded-md p-2 space-y-2">
                  {odlDisponibili.map(odl => (
                    <div key={odl.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={`odl-${odl.id}`}
                        checked={selectedODLs.includes(odl.id)}
                        onCheckedChange={() => handleODLToggle(odl.id)}
                      />
                                             <Label htmlFor={`odl-${odl.id}`} className="text-sm flex-1">
                         ODL #{odl.id} - {odl.parte.descrizione_breve}
                         <Badge variant="outline" className="ml-2">
                           {odl.parte.num_valvole_richieste} valvole
                         </Badge>
                       </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Alert informativi */}
          {stats.odlInAttesa === 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Non ci sono ODL in attesa di cura. Il nesting non può essere generato.
              </AlertDescription>
            </Alert>
          )}

          {stats.autoclaveLibere === 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Non ci sono autoclavi disponibili. Verifica lo stato delle autoclavi.
              </AlertDescription>
            </Alert>
          )}

          {/* Pulsanti di azione */}
          <div className="space-y-3 pt-4">
            {/* Pulsanti per nesting singolo */}
            <div className="flex gap-2">
              <Button
                onClick={handlePreview}
                variant="outline"
                disabled={stats.odlInAttesa === 0 || stats.autoclaveLibere === 0}
              >
                <Info className="h-4 w-4 mr-2" />
                Preview
              </Button>
              
              <Button
                onClick={handleGenerateNesting}
                disabled={
                  isGenerating || 
                  stats.odlInAttesa === 0 || 
                  stats.autoclaveLibere === 0 ||
                  (!isAutomatic && (selectedODLs.length === 0 || !selectedAutoclave))
                }
                className="flex-1"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generazione...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    {isAutomatic ? 'Genera Nesting Automatico' : 'Genera Nesting Manuale'}
                  </>
                )}
              </Button>
            </div>

            {/* Separatore e pulsante automazione multipla */}
            <div className="border-t pt-3">
              <div className="text-sm text-muted-foreground mb-2">
                Automazione Avanzata (Solo Responsabili)
              </div>
              <AutoMultipleNestingButton 
                onUpdate={() => {
                  loadInitialData()
                  onNestingGenerated()
                }}
                className="w-full"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 