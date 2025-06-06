'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useToast } from '@/components/ui/use-toast'
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
  const { toast } = useToast()
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
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{editingItem ? 'Modifica Ciclo' : 'Nuovo Ciclo'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="nome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome Ciclo</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="es. Ciclo Standard 180°C" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Sezione Riepilogo Parametri Massimi */}
            <div className="bg-muted/50 p-4 rounded-lg">
              <h4 className="font-medium mb-3 text-sm text-muted-foreground">📊 Parametri Massimi Calcolati</h4>
              <div className="grid grid-cols-2 gap-4">
                <FormItem>
                  <FormLabel>Temperatura Max (°C)</FormLabel>
                  <FormControl>
                    <Input 
                      type="number" 
                      value={temperaturaMax}
                      readOnly
                      className="bg-muted"
                    />
                  </FormControl>
                </FormItem>

                <FormItem>
                  <FormLabel>Pressione Max (bar)</FormLabel>
                  <FormControl>
                    <Input 
                      type="number" 
                      value={pressioneMax}
                      readOnly
                      className="bg-muted"
                    />
                  </FormControl>
                </FormItem>
              </div>
            </div>

            {/* Sezione Stasi 1 */}
            <div className="space-y-4 border rounded-lg p-4 bg-blue-50/50">
              <div className="flex items-center gap-2">
                <h3 className="font-medium">🔥 Stasi 1 (Obbligatoria)</h3>
                <span className="text-xs text-muted-foreground">Fase principale di cura</span>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="temperatura_stasi1"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Temperatura (°C)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="0"
                          max="300"
                          placeholder="180"
                          {...field} 
                          onChange={e => field.onChange(Number(e.target.value))}
                        />
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
                      <FormLabel>Pressione (bar)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="0.1"
                          min="0"
                          max="20"
                          placeholder="6.0"
                          {...field} 
                          onChange={e => field.onChange(Number(e.target.value))}
                        />
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
                      <FormLabel>Durata (min)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="1"
                          min="1"
                          max="600"
                          placeholder="120"
                          {...field} 
                          onChange={e => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <FormField
              control={form.control}
              name="attiva_stasi2"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel>Attiva Stasi 2</FormLabel>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {form.watch('attiva_stasi2') && (
              <div className="space-y-4 border rounded-lg p-4 bg-orange-50/50">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium">🔥 Stasi 2 (Opzionale)</h3>
                  <span className="text-xs text-muted-foreground">Fase aggiuntiva di post-cura</span>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="temperatura_stasi2"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Temperatura (°C)</FormLabel>
                        <FormControl>
                          <Input 
                            type="number" 
                            step="1"
                            min="0"
                            max="300"
                            placeholder="200"
                            {...field} 
                            onChange={e => field.onChange(Number(e.target.value))}
                          />
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
                        <FormLabel>Pressione (bar)</FormLabel>
                        <FormControl>
                          <Input 
                            type="number" 
                            step="0.1"
                            min="0"
                            max="20"
                            placeholder="8.0"
                            {...field} 
                            onChange={e => field.onChange(Number(e.target.value))}
                          />
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
                        <FormLabel>Durata (min)</FormLabel>
                        <FormControl>
                          <Input 
                            type="number" 
                            step="1"
                            min="1"
                            max="600"
                            placeholder="60"
                            {...field} 
                            onChange={e => field.onChange(Number(e.target.value))}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>
            )}

            <DialogFooter>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Salvataggio...' : editingItem ? 'Aggiorna' : 'Crea'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 