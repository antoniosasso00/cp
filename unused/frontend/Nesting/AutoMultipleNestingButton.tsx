'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { nestingApi, AutoMultipleNestingResponse } from '@/lib/api'
import { useUserRole } from '@/hooks/useUserRole'
import { 
  Zap, 
  Loader2,
  CheckCircle,
  AlertTriangle,
  BarChart3
} from 'lucide-react'

interface AutoMultipleNestingButtonProps {
  onUpdate: () => void
  className?: string
}

export function AutoMultipleNestingButton({ onUpdate, className }: AutoMultipleNestingButtonProps) {
  const { role } = useUserRole()
  const { toast } = useToast()
  
  const [isLoading, setIsLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [result, setResult] = useState<AutoMultipleNestingResponse | null>(null)

  // Solo Management può utilizzare l'automazione
  const canUseAutomation = role === 'Management'

  const handleAutoGenerate = async () => {
    if (!canUseAutomation) {
      toast({
        variant: 'destructive',
        title: 'Accesso negato',
        description: 'Solo i responsabili possono utilizzare l\'automazione nesting.',
      })
      return
    }

    setIsLoading(true)
    try {
      console.log('🤖 Avvio automazione nesting multiplo...')
      const response = await nestingApi.generateAutoMultiple()
      
      setResult(response)
      setIsDialogOpen(true)
      
      // Mostra toast di successo
      toast({
        title: 'Automazione completata',
        description: `Creati ${response.nesting_creati.length} nesting automatici per ${response.statistiche.autoclavi_utilizzate} autoclavi`,
      })

      // Aggiorna la lista dei nesting
      onUpdate()
      
    } catch (error) {
      console.error('❌ Errore nell\'automazione nesting:', error)
      toast({
        variant: 'destructive',
        title: 'Errore automazione',
        description: error instanceof Error ? error.message : 'Errore sconosciuto durante l\'automazione',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCloseDialog = () => {
    setIsDialogOpen(false)
    setResult(null)
  }

  if (!canUseAutomation) {
    return null
  }

  return (
    <>
      <Button 
        onClick={handleAutoGenerate}
        disabled={isLoading}
        className={className}
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Generazione automatica...
          </>
        ) : (
          <>
            <Zap className="h-4 w-4 mr-2" />
            Genera Nesting Automatico
          </>
        )}
      </Button>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Automazione Nesting Completata
            </DialogTitle>
            <DialogDescription>
              Risultati dell'automazione per autoclavi multiple
            </DialogDescription>
          </DialogHeader>
          
          {result && (
            <div className="space-y-6">
              {/* Statistiche generali */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Statistiche Generali
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700 font-medium">Autoclavi utilizzate:</span>
                    <div className="text-lg font-bold text-blue-900">{result.statistiche.autoclavi_utilizzate}</div>
                  </div>
                  <div>
                    <span className="text-green-700 font-medium">ODL pianificati:</span>
                    <div className="text-lg font-bold text-green-900">{result.statistiche.odl_pianificati}</div>
                  </div>
                  <div>
                    <span className="text-orange-700 font-medium">ODL non pianificabili:</span>
                    <div className="text-lg font-bold text-orange-900">{result.statistiche.odl_non_pianificabili}</div>
                  </div>
                  <div>
                    <span className="text-purple-700 font-medium">Nesting creati:</span>
                    <div className="text-lg font-bold text-purple-900">{result.statistiche.nesting_creati}</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mt-3">
                  <div>
                    <span className="text-gray-700 font-medium">ODL totali:</span>
                    <div className="text-lg font-bold text-gray-900">{result.statistiche.odl_totali}</div>
                  </div>
                  <div>
                    <span className="text-gray-700 font-medium">Autoclavi disponibili:</span>
                    <div className="text-lg font-bold text-gray-900">{result.statistiche.autoclavi_disponibili}</div>
                  </div>
                  <div>
                    <span className="text-gray-700 font-medium">Cicli compatibili:</span>
                    <div className="text-lg font-bold text-gray-900">{result.statistiche.cicli_compatibili}</div>
                  </div>
                </div>
              </div>

              {/* Nesting creati */}
              {result.nesting_creati.length > 0 && (
                <div>
                  <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    Nesting Creati ({result.nesting_creati.length})
                  </h3>
                  <div className="space-y-3">
                    {result.nesting_creati.map((nesting, index) => (
                      <div key={nesting.id} className="border rounded-lg p-4 bg-green-50">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-medium text-green-900">
                              Nesting #{nesting.id} - {nesting.autoclave_nome}
                            </h4>
                            <p className="text-sm text-green-700">
                              Ciclo: {nesting.ciclo_cura_nome} | Stato: {nesting.stato}
                            </p>
                          </div>
                          <div className="text-right text-sm">
                            <div className="text-green-700">
                              Peso: <span className="font-medium">{nesting.peso_kg.toFixed(1)} kg</span>
                            </div>
                            {nesting.use_secondary_plane && (
                              <div className="text-blue-700 text-xs">
                                ✓ Secondo piano utilizzato
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-green-700 font-medium">Area utilizzata:</span>
                            <div>{nesting.area_utilizzata.toFixed(0)} cm²</div>
                          </div>
                          <div>
                            <span className="text-gray-700 font-medium">Area totale:</span>
                            <div>{nesting.area_totale.toFixed(0)} cm²</div>
                          </div>
                          <div>
                            <span className="text-blue-700 font-medium">Valvole:</span>
                            <div>{nesting.valvole_utilizzate}/{nesting.valvole_totali}</div>
                          </div>
                          <div>
                            <span className="text-purple-700 font-medium">Efficienza:</span>
                            <div>{((nesting.area_utilizzata / nesting.area_totale) * 100).toFixed(1)}%</div>
                          </div>
                        </div>

                        <div className="mt-3">
                          <span className="text-green-700 font-medium text-sm">
                            ODL Assegnati ({nesting.odl_count}):
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {nesting.odl_ids.map((odlId) => (
                              <span 
                                key={odlId}
                                className="inline-block bg-green-200 text-green-800 text-xs px-2 py-1 rounded"
                              >
                                ODL #{odlId}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ODL non pianificabili */}
              {result.odl_non_pianificabili.length > 0 && (
                <div>
                  <h3 className="font-semibold text-orange-900 mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    ODL Non Pianificabili ({result.odl_non_pianificabili.length})
                  </h3>
                  <div className="space-y-2">
                    {result.odl_non_pianificabili.map((odl) => (
                      <div key={odl.id} className="border rounded-lg p-3 bg-orange-50">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium text-orange-900">
                              ODL #{odl.id} - {odl.tool_part_number}
                            </h4>
                            <p className="text-sm text-orange-700">{odl.parte_descrizione}</p>
                          </div>
                          <div className="text-right">
                            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                              {odl.motivo}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Messaggio finale */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>Nota:</strong> I nesting sono stati creati in stato "SOSPESO". 
                  Gli autoclavisti possono ora confermarli per procedere con la produzione.
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button onClick={handleCloseDialog}>
              Chiudi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
} 