'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { toolApi, Tool } from '@/lib/api'

// Schema di validazione per il tool
const toolSchema = z.object({
  part_number_tool: z.string().min(1, "Part Number Tool obbligatorio"),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0.1, "Lunghezza deve essere maggiore di 0"),
  larghezza_piano: z.number().min(0.1, "Larghezza deve essere maggiore di 0"),
  // ✅ NUOVO: Campi per nesting su due piani
  peso: z.number().min(0, "Il peso deve essere positivo").optional(),
  materiale: z.string().optional(),
  disponibile: z.boolean()
})

type ToolFormValues = z.infer<typeof toolSchema>

interface ToolModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingItem?: Tool | null
  onSuccess: () => void
}

export function ToolModal({ open, onOpenChange, editingItem, onSuccess }: ToolModalProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<ToolFormValues>({
    resolver: zodResolver(toolSchema),
    defaultValues: {
      part_number_tool: '',
      descrizione: '',
      lunghezza_piano: 100,
      larghezza_piano: 50,
      // ✅ NUOVO: Valori di default per nesting su due piani
      peso: 0,
      materiale: '',
      disponibile: true,
    },
  })

  // Aggiorna i valori del form quando editingItem cambia
  useEffect(() => {
    if (editingItem) {
      form.reset({
        part_number_tool: editingItem.part_number_tool,
        descrizione: editingItem.descrizione || '',
        lunghezza_piano: editingItem.lunghezza_piano,
        larghezza_piano: editingItem.larghezza_piano,
        // ✅ NUOVO: Campi per nesting su due piani
        peso: editingItem.peso || 0,
        materiale: editingItem.materiale || '',
        disponibile: editingItem.disponibile,
      })
    } else {
      form.reset({
        part_number_tool: '',
        descrizione: '',
        lunghezza_piano: 100,
        larghezza_piano: 50,
        // ✅ NUOVO: Reset per nesting su due piani
        peso: 0,
        materiale: '',
        disponibile: true,
      })
    }
  }, [editingItem, form])

  const onSubmit = async (data: ToolFormValues) => {
    try {
      setIsLoading(true)
      if (editingItem) {
        await toolApi.update(editingItem.id, data)
        toast({
          variant: 'success',
          title: 'Tool aggiornato',
          description: 'Il tool è stato aggiornato con successo.',
        })
      } else {
        await toolApi.create(data)
        toast({
          variant: 'success',
          title: 'Tool creato',
          description: 'Il nuovo tool è stato creato con successo.',
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{editingItem ? 'Modifica Tool' : 'Nuovo Tool'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="part_number_tool"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Part Number Tool</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="es. T001" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="descrizione"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descrizione</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Descrizione opzionale" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="lunghezza_piano"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Lunghezza Piano (mm)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.1"
                        min="0.1"
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
                name="larghezza_piano"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Larghezza Piano (mm)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.1"
                        min="0.1"
                        {...field} 
                        onChange={e => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* ✅ NUOVO: Campi per nesting su due piani */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="peso"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Peso (kg)</FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.1"
                        min="0"
                        placeholder="0.0"
                        {...field} 
                        onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="materiale"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Materiale</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="es. Alluminio, Acciaio" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="disponibile"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel>Disponibile</FormLabel>
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

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Annulla
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Salvataggio...' : 'Salva'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 