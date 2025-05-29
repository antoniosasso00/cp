'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { CheckCircle, AlertTriangle, Loader2, Factory } from 'lucide-react'
import { autoclaveApi, nestingApi, Autoclave } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface NestingStep1AutoclaveProps {
  nestingId: number
  onStepComplete: (data: { autoclave_id: number; autoclave_nome: string }) => void
  onStepError?: (error: string) => void
  disabled?: boolean
}

export function NestingStep1Autoclave({ 
  nestingId, 
  onStepComplete, 
  onStepError,
  disabled = false 
}: NestingStep1AutoclaveProps) {
  const [autoclavi, setAutoclavi] = useState<Autoclave[]>([])
  const [selectedAutoclave, setSelectedAutoclave] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAssigning, setIsAssigning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  // Carica le autoclavi disponibili
  useEffect(() => {
    const loadAutoclavi = async () => {
      try {
        setIsLoading(true)
        setError(null)
        
        // Carica tutte le autoclavi e filtra quelle disponibili
        const allAutoclavi = await autoclaveApi.getAll()
        const autoclaveDisponibili = allAutoclavi.filter(
          autoclave => autoclave.stato === 'DISPONIBILE'
        )
        
        setAutoclavi(autoclaveDisponibili)
        
        if (autoclaveDisponibili.length === 0) {
          setError('Nessuna autoclave disponibile al momento')
          if (onStepError) {
            onStepError('Nessuna autoclave disponibile al momento')
          }
        }
        
      } catch (error) {
        console.error('❌ Errore nel caricamento autoclavi:', error)
        const errorMessage = error instanceof Error ? error.message : 'Errore nel caricamento autoclavi'
        setError(errorMessage)
        if (onStepError) {
          onStepError(errorMessage)
        }
      } finally {
        setIsLoading(false)
      }
    }

    loadAutoclavi()
  }, [onStepError])

  // Assegna l'autoclave selezionata al nesting
  const handleAssignAutoclave = async () => {
    if (!selectedAutoclave) {
      toast({
        title: "Selezione richiesta",
        description: "Seleziona un'autoclave prima di continuare",
        variant: "destructive",
      })
      return
    }

    try {
      setIsAssigning(true)
      setError(null)
      
      const result = await nestingApi.assignAutoclave(nestingId, { autoclave_id: selectedAutoclave })
      
      toast({
        title: "Autoclave Assegnata",
        description: result.message,
      })
      
      // Notifica il completamento dello step
      onStepComplete({
        autoclave_id: result.autoclave_assegnata.id,
        autoclave_nome: result.autoclave_assegnata.nome
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Errore nell\'assegnazione autoclave'
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

  // Validazione automatica per sviluppo
  useEffect(() => {
    if (!autoclavi?.length) {
      // Validazione silenziosa - nessun log in produzione
    }
  }, [autoclavi])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Factory className="h-5 w-5" />
            Step 1: Selezione Autoclave
          </CardTitle>
          <CardDescription>
            Seleziona l'autoclave da utilizzare per questo nesting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Caricamento autoclavi...</span>
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
            <Factory className="h-5 w-5" />
            Step 1: Selezione Autoclave
          </CardTitle>
          <CardDescription>
            Seleziona l'autoclave da utilizzare per questo nesting
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
          <Factory className="h-5 w-5" />
          Step 1: Selezione Autoclave
        </CardTitle>
        <CardDescription>
          Seleziona l'autoclave da utilizzare per questo nesting. Solo le autoclavi disponibili sono mostrate.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>Primo Step Obbligatorio</AlertTitle>
          <AlertDescription>
            La selezione dell'autoclave è necessaria per procedere con gli step successivi del nesting manuale.
          </AlertDescription>
        </Alert>

        {autoclavi.length > 0 ? (
          <>
            <div className="space-y-3">
              <Label className="text-sm font-medium">Autoclavi Disponibili ({autoclavi.length})</Label>
              <div className="grid gap-3">
                {autoclavi.map((autoclave) => (
                  <Card 
                    key={autoclave.id} 
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedAutoclave === autoclave.id 
                        ? 'ring-2 ring-blue-500 bg-blue-50' 
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => !disabled && !isAssigning && setSelectedAutoclave(autoclave.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full border-2 ${
                              selectedAutoclave === autoclave.id 
                                ? 'bg-blue-500 border-blue-500' 
                                : 'border-gray-300'
                            }`}>
                              {selectedAutoclave === autoclave.id && (
                                <CheckCircle className="w-4 h-4 text-white" />
                              )}
                            </div>
                            <div className="font-medium">{autoclave.nome}</div>
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            Codice: {autoclave.codice} | 
                            Area: {autoclave.area_piano?.toFixed(0) || '-'} cm² | 
                            Linee vuoto: {autoclave.num_linee_vuoto}
                          </div>
                          {autoclave.max_load_kg && (
                            <div className="text-sm text-gray-500">
                              Carico max: {autoclave.max_load_kg} kg
                            </div>
                          )}
                        </div>
                        <div className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          {autoclave.stato}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Button
              onClick={handleAssignAutoclave}
              disabled={!selectedAutoclave || disabled || isAssigning}
              className="w-full flex items-center gap-2"
              data-nesting-action="confirm"
            >
              {isAssigning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Assegnazione in corso...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Assegna e Continua →
                </>
              )}
            </Button>
          </>
        ) : (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Nessuna Autoclave Disponibile</AlertTitle>
            <AlertDescription>
              Non ci sono autoclavi disponibili al momento. Verifica che almeno un'autoclave sia nello stato "DISPONIBILE".
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
} 