'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, AlertTriangle, Loader2, Package, Wrench, Clock, ArrowRight } from 'lucide-react'
import { odlApi, nestingApi, ODLResponse } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { Checkbox } from '@/components/ui/checkbox'

interface NestingStep2ODLSelectionProps {
  nestingId: number
  onStepComplete: (data: { selected_odl_ids: number[]; odl_count: number }) => void
  onStepError?: (error: string) => void
  disabled?: boolean
}

export function NestingStep2ODLSelection({ 
  nestingId, 
  onStepComplete, 
  onStepError,
  disabled = false 
}: NestingStep2ODLSelectionProps) {
  const [odlInAttesa, setOdlInAttesa] = useState<ODLResponse[]>([])
  const [selectedOdlIds, setSelectedOdlIds] = useState<Set<number>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isAssigning, setIsAssigning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Carica gli ODL in attesa di cura
  useEffect(() => {
    const loadODLInAttesa = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        // Carica ODL con status "Attesa Cura"
        const odlList = await odlApi.getByStatus('Attesa Cura')
        setOdlInAttesa(odlList)
        
        if (odlList.length === 0) {
          setError('Nessun ODL in attesa di cura al momento')
          if (onStepError) {
            onStepError('Nessun ODL in attesa di cura al momento')
          }
        }
        
      } catch (error) {
        console.error('❌ Errore nel caricamento ODL in attesa:', error)
        const errorMessage = error instanceof Error ? error.message : 'Errore nel caricamento ODL'
        setError(errorMessage)
        if (onStepError) {
          onStepError(errorMessage)
        }
      } finally {
        setIsLoading(false)
      }
    }

    loadODLInAttesa()
  }, [onStepError])

  // Gestisce la selezione/deselezione di un ODL
  const handleOdlToggle = (odlId: number) => {
    if (disabled || isAssigning) return
    
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

  // Seleziona/deseleziona tutti gli ODL
  const handleSelectAll = () => {
    if (disabled || isAssigning) return
    
    if (selectedOdlIds.size === odlInAttesa.length) {
      // Deseleziona tutti
      setSelectedOdlIds(new Set())
    } else {
      // Seleziona tutti
      setSelectedOdlIds(new Set(odlInAttesa.map(odl => odl.id)))
    }
  }

  // Assegna gli ODL selezionati al nesting
  const handleAssignODL = async () => {
    if (selectedOdlIds.size === 0) {
      toast({
        title: "Selezione richiesta",
        description: "Seleziona almeno un ODL prima di continuare",
        variant: "destructive",
      })
      return
    }

    try {
      setIsAssigning(true)
      setError(null)
      
      // Per ora salviamo la selezione e procediamo al prossimo step
      // In futuro potremmo avere un endpoint specifico per associare ODL al nesting
      const selectedOdlArray = Array.from(selectedOdlIds)
      
      toast({
        title: "ODL Selezionati",
        description: `${selectedOdlArray.length} ODL selezionati per il nesting`,
      })
      
      // Notifica il completamento dello step
      onStepComplete({
        selected_odl_ids: selectedOdlArray,
        odl_count: selectedOdlArray.length
      })
      
    } catch (error) {
      console.error('❌ Errore nella selezione ODL:', error)
      const errorMessage = error instanceof Error ? error.message : 'Errore nella selezione ODL'
      setError(errorMessage)
      
      if (onStepError) {
        onStepError(errorMessage)
      }
      
      toast({
        title: "Errore",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsAssigning(false)
    }
  }

  // Calcola statistiche della selezione
  const getSelectionStats = () => {
    const selectedOdl = odlInAttesa.filter(odl => selectedOdlIds.has(odl.id))
    
    // Siccome ToolInODLResponse ha solo id, part_number_tool e descrizione,
    // usiamo valori di default per peso e dimensioni
    const totalWeight = selectedOdl.length * 5.0 // Peso stimato 5kg per tool
    const totalArea = selectedOdl.length * 1000 // Area stimata 1000 cm² per tool
    
    return {
      count: selectedOdl.length,
      weight: totalWeight,
      area: totalArea
    }
  }

  const stats = getSelectionStats()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Step 2: Selezione ODL
          </CardTitle>
          <CardDescription>
            Seleziona gli ODL in attesa di cura da includere nel nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Caricamento ODL in attesa...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Step 2: Selezione ODL
          </CardTitle>
          <CardDescription>
            Seleziona gli ODL in attesa di cura da includere nel nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Errore</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package className="h-5 w-5" />
          Step 2: Selezione ODL
        </CardTitle>
        <CardDescription>
          Seleziona gli ODL in attesa di cura da includere nel nesting. Solo gli ODL selezionati verranno processati.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Statistiche selezione */}
        {selectedOdlIds.size > 0 && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Selezione Corrente</h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-blue-700 font-medium">{stats.count}</span>
                <span className="text-blue-600"> ODL selezionati</span>
              </div>
              <div>
                <span className="text-blue-700 font-medium">{stats.weight.toFixed(1)} kg</span>
                <span className="text-blue-600"> peso totale</span>
              </div>
              <div>
                <span className="text-blue-700 font-medium">{stats.area.toFixed(0)} cm²</span>
                <span className="text-blue-600"> area totale</span>
              </div>
            </div>
          </div>
        )}

        {odlInAttesa.length > 0 ? (
          <>
            {/* Controlli selezione */}
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">
                ODL in Attesa di Cura ({odlInAttesa.length})
              </Label>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                disabled={disabled || isAssigning}
              >
                {selectedOdlIds.size === odlInAttesa.length ? 'Deseleziona Tutti' : 'Seleziona Tutti'}
              </Button>
            </div>

            {/* Lista ODL */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {odlInAttesa.map((odl) => (
                <Card 
                  key={odl.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedOdlIds.has(odl.id)
                      ? 'ring-2 ring-blue-500 bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => handleOdlToggle(odl.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <Checkbox
                        checked={selectedOdlIds.has(odl.id)}
                        onChange={() => handleOdlToggle(odl.id)}
                        disabled={disabled || isAssigning}
                        className="mt-1"
                      />
                      
                      {/* Contenuto principale */}
                      <div className="flex-1 space-y-2">
                        {/* Header con ODL ID e priorità */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">ODL #{odl.id}</span>
                            <Badge variant="outline">Priorità {odl.priorita}</Badge>
                          </div>
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {odl.status}
                          </Badge>
                        </div>

                        {/* Informazioni parte */}
                        <div className="flex items-center gap-2 text-sm">
                          <Package className="h-4 w-4 text-gray-500" />
                          <span className="font-medium">{odl.parte.part_number}</span>
                          <span className="text-gray-600">- {odl.parte.descrizione_breve}</span>
                        </div>

                        {/* Informazioni tool */}
                        <div className="flex items-center gap-2 text-sm">
                          <Wrench className="h-4 w-4 text-gray-500" />
                          <span className="font-medium">{odl.tool.part_number_tool}</span>
                          {odl.tool.descrizione && (
                            <span className="text-gray-600">- {odl.tool.descrizione}</span>
                          )}
                        </div>

                        {/* Dettagli tecnici */}
                        <div className="grid grid-cols-3 gap-4 text-xs text-gray-600 bg-gray-50 rounded p-2">
                          <div>
                            <span className="font-medium">Valvole:</span> {odl.parte.num_valvole_richieste}
                          </div>
                          <div>
                            <span className="font-medium">Creato:</span> {new Date(odl.created_at).toLocaleDateString()}
                          </div>
                          <div>
                            <span className="font-medium">Aggiornato:</span> {new Date(odl.updated_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Pulsante conferma */}
            <Button
              onClick={handleAssignODL}
              disabled={selectedOdlIds.size === 0 || disabled || isAssigning}
              className="w-full flex items-center gap-2"
              data-nesting-action="confirm"
            >
              {isAssigning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Elaborazione in corso...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Conferma Selezione ({selectedOdlIds.size} ODL) <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </>
        ) : (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Nessun ODL Disponibile</AlertTitle>
            <AlertDescription>
              Non ci sono ODL in attesa di cura al momento. Verifica che ci siano ODL nello stato "Attesa Cura" prima di procedere con il nesting manuale.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
} 