'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { cicloCuraApi } from '@/lib/api'
import { cicloSchema, type CicloFormValues } from '@/lib/types/form'
import { Info } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import type { CreateCicloCuraDto } from '@/lib/api'

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
      nome: editingItem?.nome || '',
      temperatura_stasi1: editingItem?.temperatura_stasi1 || 0,
      pressione_stasi1: editingItem?.pressione_stasi1 || 0,
      durata_stasi1: editingItem?.durata_stasi1 || 0,
      attiva_stasi2: editingItem?.attiva_stasi2 ?? false,
      temperatura_stasi2: editingItem?.temperatura_stasi2 || null,
      pressione_stasi2: editingItem?.pressione_stasi2 || null,
      durata_stasi2: editingItem?.durata_stasi2 || null,
    },
  })

  const onSubmit = async (data: CicloFormValues) => {
    try {
      setIsLoading(true)
      
      // Se la stasi 2 non è attiva, imposta i suoi campi a null
      const dataToSubmit: CreateCicloCuraDto = {
        nome: data.nome,
        temperatura_stasi1: data.temperatura_stasi1,
        pressione_stasi1: data.pressione_stasi1,
        durata_stasi1: data.durata_stasi1,
        attiva_stasi2: data.attiva_stasi2,
        temperatura_stasi2: data.attiva_stasi2 ? Number(data.temperatura_stasi2) : null,
        pressione_stasi2: data.attiva_stasi2 ? Number(data.pressione_stasi2) : null,
        durata_stasi2: data.attiva_stasi2 ? Number(data.durata_stasi2) : null,
      }

      if (editingItem) {
        await cicloCuraApi.update(editingItem.id, dataToSubmit)
        toast({
          title: 'Ciclo aggiornato',
          description: 'Il ciclo di cura è stato aggiornato con successo.',
        })
      } else {
        await cicloCuraApi.create(dataToSubmit)
        toast({
          title: 'Ciclo creato',
          description: 'Il nuovo ciclo di cura è stato creato con successo.',
        })
      }
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
                  <FormLabel>Nome</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

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

            <div className="space-y-4 border-t pt-4">
              <h3 className="font-medium">Stasi 1</h3>
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
                    <div className="flex items-center gap-2">
                      <FormLabel>Attiva Stasi 2</FormLabel>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-4 w-4 text-muted-foreground" />
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>La Stasi 2 è opzionale e può essere utilizzata per cicli di cura più complessi.</p>
                            <p>Se attivata, tutti i suoi campi (temperatura, pressione e durata) saranno obbligatori.</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {field.value 
                        ? "La Stasi 2 è attiva. Compila tutti i campi richiesti."
                        : "La Stasi 2 è disattivata. I suoi campi non saranno utilizzati."}
                    </p>
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
              <div className="space-y-4 border-t pt-4">
                <h3 className="font-medium">Stasi 2</h3>
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
                            {...field} 
                            value={field.value ?? ''}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : null)}
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
                            {...field} 
                            value={field.value ?? ''}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : null)}
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
                            {...field} 
                            value={field.value ?? ''}
                            onChange={e => field.onChange(e.target.value ? Number(e.target.value) : null)}
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