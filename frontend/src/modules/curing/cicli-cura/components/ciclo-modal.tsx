'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { curingCyclesApi } from '@/lib/api'
import { cicloSchema, type CicloFormValues } from '@/lib/types/form'

interface CicloModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingItem?: {
    id: number
    nome: string
    temperatura_stasi1: number
    pressione_stasi1: number
    durata_stasi1: number
    attiva_stasi2: boolean
    temperatura_stasi2?: number
    pressione_stasi2?: number
    durata_stasi2?: number
  } | null
  onSuccess: () => void
}

export function CicloModal({ open, onOpenChange, editingItem, onSuccess }: CicloModalProps) {
  const { toast } = useStandardToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<CicloFormValues>({
    resolver: zodResolver(cicloSchema),
    defaultValues: {
      nome: '',
      temperatura_stasi1: 180, // Valore default realistico
      pressione_stasi1: 6,     // Valore default realistico
      durata_stasi1: 120,      // Valore default realistico
      attiva_stasi2: false,
      temperatura_stasi2: 200, // Valore default per stasi 2
      pressione_stasi2: 8,     // Valore default per stasi 2
      durata_stasi2: 60,       // Valore default per stasi 2
    },
  })

  // Effect per aggiornare i valori del form quando editingItem cambia
  useEffect(() => {
    if (editingItem) {
      // Precompila il form con i valori dell'elemento da modificare
      form.reset({
        nome: editingItem.nome,
        temperatura_stasi1: editingItem.temperatura_stasi1,
        pressione_stasi1: editingItem.pressione_stasi1,
        durata_stasi1: editingItem.durata_stasi1,
        attiva_stasi2: editingItem.attiva_stasi2,
        temperatura_stasi2: editingItem.temperatura_stasi2 ?? 0,
        pressione_stasi2: editingItem.pressione_stasi2 ?? 0,
        durata_stasi2: editingItem.durata_stasi2 ?? 0,
      })
    } else {
      // Reset per nuovo elemento con valori default realistici
      form.reset({
        nome: '',
        temperatura_stasi1: 180,
        pressione_stasi1: 6,
        durata_stasi1: 120,
        attiva_stasi2: false,
        temperatura_stasi2: 200,
        pressione_stasi2: 8,
        durata_stasi2: 60,
      })
    }
  }, [editingItem, form])

  const onSubmit = async (data: CicloFormValues) => {
    try {
      setIsLoading(true)
      
      // Rimuovi i campi della stasi 2 se non è attiva
      const formData = { ...data };
      if (!formData.attiva_stasi2) {
        formData.temperatura_stasi2 = undefined;
        formData.pressione_stasi2 = undefined;
        formData.durata_stasi2 = undefined;
      }
      
      if (editingItem) {
        await curingCyclesApi.updateCuringCycle(editingItem.id, formData)
        toast({
          title: 'Aggiornato',
          description: 'Ciclo di cura aggiornato con successo.',
        })
      } else {
        await curingCyclesApi.createCuringCycle(formData)
        toast({
          title: 'Creato',
          description: 'Ciclo di cura creato con successo.',
        })
      }
      
      // Reset form dopo il successo
      form.reset({
        nome: '',
        temperatura_stasi1: 180,
        pressione_stasi1: 6,
        durata_stasi1: 120,
        attiva_stasi2: false,
        temperatura_stasi2: 200,
        pressione_stasi2: 8,
        durata_stasi2: 60,
      })
      
      onSuccess()
      onOpenChange(false)
    } catch (error) {
      console.error('Errore durante il salvataggio:', error)
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: 'Si è verificato un errore durante il salvataggio.',
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Calcola i valori massimi
  const temperaturaMax = form.watch('attiva_stasi2') 
    ? Math.max(form.watch('temperatura_stasi1'), form.watch('temperatura_stasi2') || 0)
    : form.watch('temperatura_stasi1')

  const pressioneMax = form.watch('attiva_stasi2')
    ? Math.max(form.watch('pressione_stasi1'), form.watch('pressione_stasi2') || 0)
    : form.watch('pressione_stasi1')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader className="shrink-0">
          <DialogTitle className="text-lg font-semibold">
            {editingItem ? 'Modifica Ciclo di Cura' : 'Nuovo Ciclo di Cura'}
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            Configura i parametri di temperatura, pressione e durata per le fasi di cura
          </p>
        </DialogHeader>
        
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Nome Ciclo - Campo principale */}
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="nome"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-base font-medium">Nome Ciclo</FormLabel>
                    <FormControl>
                      <Input 
                        {...field} 
                        placeholder="es. Ciclo Standard 180°C" 
                        className="text-base"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Sezione Parametri Massimi Calcolati */}
            <div className="bg-blue-50/50 border border-blue-200/50 p-5 rounded-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center justify-center w-6 h-6 bg-blue-100 rounded-full text-blue-600 text-xs font-medium">
                  📊
                </div>
                <h4 className="font-semibold text-blue-900">Parametri Massimi Calcolati</h4>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white rounded-md p-3 border border-blue-100">
                  <FormLabel className="text-sm font-medium text-gray-600">Temperatura Max</FormLabel>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-bold text-blue-600">{temperaturaMax}</span>
                    <span className="text-sm text-gray-500">°C</span>
                  </div>
                </div>
                <div className="bg-white rounded-md p-3 border border-blue-100">
                  <FormLabel className="text-sm font-medium text-gray-600">Pressione Max</FormLabel>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-2xl font-bold text-blue-600">{pressioneMax}</span>
                    <span className="text-sm text-gray-500">bar</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Sezione Stasi 1 - Obbligatoria */}
            <div className="bg-orange-50/50 border border-orange-200/50 p-5 rounded-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center justify-center w-6 h-6 bg-orange-100 rounded-full text-orange-600 text-xs font-medium">
                  🔥
                </div>
                <div>
                  <h3 className="font-semibold text-orange-900">Stasi 1 (Obbligatoria)</h3>
                  <p className="text-xs text-orange-700">Fase principale di cura</p>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="temperatura_stasi1"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Temperatura</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Input 
                            type="number" 
                            step="1"
                            min="0"
                            max="300"
                            placeholder="180"
                            {...field}
                            value={field.value || ''}
                            onChange={e => {
                              const value = e.target.value
                              if (value === '') {
                                field.onChange(null)
                              } else {
                                const numValue = Number(value)
                                if (!isNaN(numValue) && numValue >= 0) {
                                  field.onChange(numValue)
                                }
                              }
                            }}
                            className="pr-8"
                          />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">°C</span>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="pressione_stasi1"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Pressione</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Input 
                            type="number" 
                            step="0.1"
                            min="0"
                            max="20"
                            placeholder="6"
                            {...field}
                            value={field.value || ''}
                            onChange={e => {
                              const value = e.target.value
                              if (value === '') {
                                field.onChange(null)
                              } else {
                                const numValue = Number(value)
                                if (!isNaN(numValue) && numValue >= 0) {
                                  field.onChange(numValue)
                                }
                              }
                            }}
                            className="pr-10"
                          />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">bar</span>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="durata_stasi1"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Durata</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Input 
                            type="number" 
                            step="1"
                            min="0"
                            max="1440"
                            placeholder="120"
                            {...field}
                            value={field.value || ''}
                            onChange={e => {
                              const value = e.target.value
                              if (value === '') {
                                field.onChange(null)
                              } else {
                                const numValue = Number(value)
                                if (!isNaN(numValue) && numValue >= 0) {
                                  field.onChange(numValue)
                                }
                              }
                            }}
                            className="pr-10"
                          />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">min</span>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            {/* Toggle per Stasi 2 */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
              <div className="space-y-1">
                <FormLabel className="text-base font-medium">Attiva Stasi 2</FormLabel>
                <p className="text-sm text-muted-foreground">
                  Aggiungi una fase aggiuntiva di post-cura (opzionale)
                </p>
              </div>
              <FormField
                control={form.control}
                name="attiva_stasi2"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-end space-y-0">
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            {/* Sezione Stasi 2 - Opzionale */}
            {form.watch('attiva_stasi2') && (
              <div className="bg-purple-50/50 border border-purple-200/50 p-5 rounded-lg animate-in slide-in-from-top-2 duration-200">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex items-center justify-center w-6 h-6 bg-purple-100 rounded-full text-purple-600 text-xs font-medium">
                    🔥
                  </div>
                  <div>
                    <h3 className="font-semibold text-purple-900">Stasi 2 (Opzionale)</h3>
                    <p className="text-xs text-purple-700">Fase aggiuntiva di post-cura</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="temperatura_stasi2"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Temperatura</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input 
                              type="number" 
                              step="1"
                              min="0"
                              max="300"
                              placeholder="200"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 0) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                              className="pr-8"
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">°C</span>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="pressione_stasi2"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Pressione</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input 
                              type="number" 
                              step="0.1"
                              min="0"
                              max="20"
                              placeholder="8"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 0) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                              className="pr-10"
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">bar</span>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="durata_stasi2"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Durata</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input 
                              type="number" 
                              step="1"
                              min="0"
                              max="1440"
                              placeholder="60"
                              {...field}
                              value={field.value || ''}
                              onChange={e => {
                                const value = e.target.value
                                if (value === '') {
                                  field.onChange(null)
                                } else {
                                  const numValue = Number(value)
                                  if (!isNaN(numValue) && numValue >= 0) {
                                    field.onChange(numValue)
                                  }
                                }
                              }}
                              className="pr-10"
                            />
                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500">min</span>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>
            )}

            {/* Footer con pulsanti */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                Annulla
              </Button>
              <Button type="submit" disabled={isLoading} className="min-w-32">
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Salva...
                  </>
                ) : (
                  editingItem ? 'Aggiorna Ciclo' : 'Crea Ciclo'
                )}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 