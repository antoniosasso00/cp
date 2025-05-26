'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from '@/components/ui/form'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { AlertTriangle, CheckCircle, Package, Weight, Layers } from 'lucide-react'
import { nestingApi, TwoLevelNestingRequest, TwoLevelNestingResponse } from '@/lib/api'

// Schema di validazione per la richiesta di nesting su due piani
const twoLevelNestingSchema = z.object({
  superficie_piano_2_max_cm2: z.number().min(0, "La superficie deve essere positiva").optional(),
  note: z.string().optional(),
})

type TwoLevelNestingFormValues = z.infer<typeof twoLevelNestingSchema>

interface TwoLevelNestingModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function TwoLevelNestingModal({ open, onOpenChange, onSuccess }: TwoLevelNestingModalProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [nestingResult, setNestingResult] = useState<TwoLevelNestingResponse | null>(null)

  const form = useForm<TwoLevelNestingFormValues>({
    resolver: zodResolver(twoLevelNestingSchema),
    defaultValues: {
      superficie_piano_2_max_cm2: 5000, // Default 5000 cm²
      note: '',
    },
  })

  const onSubmit = async (data: TwoLevelNestingFormValues) => {
    try {
      setIsLoading(true)
      console.log('🔄 Avvio nesting su due piani con parametri:', data)
      
      const result = await nestingApi.generateTwoLevel(data)
      console.log('✅ Risultato nesting su due piani:', result)
      
      setNestingResult(result)
      
      if (result.success) {
        toast({
          variant: 'success',
          title: 'Nesting su due piani completato',
          description: `Generato con successo per autoclave ${result.autoclave.nome}`,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Nesting non riuscito',
          description: result.message,
        })
      }
    } catch (error) {
      console.error('❌ Errore durante il nesting su due piani:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Si è verificato un errore durante la generazione del nesting.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setNestingResult(null)
    form.reset()
    onOpenChange(false)
  }

  const handleConfirm = () => {
    if (nestingResult?.success) {
      onSuccess()
      handleClose()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Nesting su Due Piani
          </DialogTitle>
        </DialogHeader>

        {!nestingResult ? (
          // Form di configurazione
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid gap-4">
                <FormField
                  control={form.control}
                  name="superficie_piano_2_max_cm2"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Superficie Massima Piano 2 (cm²)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="0"
                          placeholder="5000"
                          {...field} 
                          onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                        />
                      </FormControl>
                      <FormDescription>
                        Superficie massima utilizzabile del piano superiore. Lascia vuoto per usare l'intera superficie dell'autoclave.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="note"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Note</FormLabel>
                      <FormControl>
                        <Textarea 
                          {...field} 
                          placeholder="Note aggiuntive per il nesting..."
                          rows={3}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Come funziona il nesting su due piani:</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• I pezzi più pesanti e grandi vengono posizionati nel <strong>piano inferiore</strong></li>
                  <li>• I pezzi più leggeri e piccoli vengono posizionati nel <strong>piano superiore</strong></li>
                  <li>• Il sistema verifica automaticamente che il carico totale non superi il limite dell'autoclave</li>
                  <li>• Viene ottimizzata l'efficienza di utilizzo di entrambi i piani</li>
                </ul>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleClose}>
                  Annulla
                </Button>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Generazione in corso...' : 'Genera Nesting'}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        ) : (
          // Risultati del nesting
          <div className="space-y-6">
            {/* Header con stato */}
            <div className="flex items-center gap-3">
              {nestingResult.success ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-red-600" />
              )}
              <div>
                <h3 className="font-semibold">
                  {nestingResult.success ? 'Nesting Completato' : 'Nesting Non Riuscito'}
                </h3>
                <p className="text-sm text-muted-foreground">{nestingResult.message}</p>
              </div>
            </div>

            {nestingResult.success && (
              <>
                {/* Informazioni autoclave */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Autoclave Assegnata</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="font-medium">{nestingResult.autoclave.nome}</p>
                        <p className="text-sm text-muted-foreground">Codice: {nestingResult.autoclave.codice}</p>
                      </div>
                      <div>
                        <p className="text-sm">Carico massimo: <span className="font-medium">{nestingResult.autoclave.max_load_kg} kg</span></p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Statistiche */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Weight className="h-5 w-5" />
                      Statistiche Carico
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">{nestingResult.statistiche.peso_totale_kg.toFixed(1)}</p>
                        <p className="text-sm text-muted-foreground">Peso Totale (kg)</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">{nestingResult.statistiche.peso_piano_1_kg.toFixed(1)}</p>
                        <p className="text-sm text-muted-foreground">Piano 1 (kg)</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-orange-600">{nestingResult.statistiche.peso_piano_2_kg.toFixed(1)}</p>
                        <p className="text-sm text-muted-foreground">Piano 2 (kg)</p>
                      </div>
                      <div className="text-center">
                        <Badge variant={nestingResult.statistiche.carico_valido ? "success" : "destructive"}>
                          {nestingResult.statistiche.carico_valido ? "Valido" : "Sovraccarico"}
                        </Badge>
                        <p className="text-sm text-muted-foreground">Stato Carico</p>
                      </div>
                    </div>
                    
                    {!nestingResult.statistiche.carico_valido && nestingResult.statistiche.motivo_invalidita && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">
                          <AlertTriangle className="h-4 w-4 inline mr-1" />
                          {nestingResult.statistiche.motivo_invalidita}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Piano 1 - Pezzi pesanti */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Package className="h-5 w-5 text-green-600" />
                      Piano 1 - Inferiore ({nestingResult.piano_1.length} pezzi)
                    </CardTitle>
                    <CardDescription>Pezzi più pesanti e grandi</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {nestingResult.piano_1.map((item, index) => (
                        <div key={item.odl_id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                          <div>
                            <p className="font-medium">{item.part_number}</p>
                            <p className="text-sm text-muted-foreground">{item.descrizione}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm">
                              <span className="font-medium">{item.peso_kg.toFixed(1)} kg</span> • 
                              <span className="ml-1">{item.area_cm2.toFixed(0)} cm²</span>
                            </p>
                                                         <Badge variant="outline">Priorità {item.priorita}</Badge>
                           </div>
                         </div>
                       ))}
                       {nestingResult.piano_1.length === 0 && (
                        <p className="text-center text-muted-foreground py-4">Nessun pezzo assegnato al piano 1</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Piano 2 - Pezzi leggeri */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Package className="h-5 w-5 text-orange-600" />
                      Piano 2 - Superiore ({nestingResult.piano_2.length} pezzi)
                    </CardTitle>
                    <CardDescription>Pezzi più leggeri e piccoli</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {nestingResult.piano_2.map((item, index) => (
                        <div key={item.odl_id} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                          <div>
                            <p className="font-medium">{item.part_number}</p>
                            <p className="text-sm text-muted-foreground">{item.descrizione}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm">
                              <span className="font-medium">{item.peso_kg.toFixed(1)} kg</span> • 
                              <span className="ml-1">{item.area_cm2.toFixed(0)} cm²</span>
                            </p>
                                                         <Badge variant="outline">Priorità {item.priorita}</Badge>
                           </div>
                         </div>
                       ))}
                       {nestingResult.piano_2.length === 0 && (
                        <p className="text-center text-muted-foreground py-4">Nessun pezzo assegnato al piano 2</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* ODL non pianificabili */}
                {nestingResult.odl_non_pianificabili.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2 text-red-600">
                        <AlertTriangle className="h-5 w-5" />
                        ODL Non Pianificabili ({nestingResult.odl_non_pianificabili.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {nestingResult.odl_non_pianificabili.map((item, index) => (
                          <div key={item.odl_id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                            <div>
                              <p className="font-medium">{item.part_number}</p>
                              <p className="text-sm text-muted-foreground">{item.descrizione}</p>
                            </div>
                            <div className="text-right">
                                                             <Badge variant="destructive">{item.motivo}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Chiudi
              </Button>
              {nestingResult.success && nestingResult.statistiche.carico_valido && (
                <Button onClick={handleConfirm}>
                  Conferma Nesting
                </Button>
              )}
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
} 