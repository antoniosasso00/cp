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
import { toolApi } from '@/lib/api'
import { toolSchema, type ToolFormValues } from '@/lib/types/form'

interface ToolModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingItem?: {
    id: number
    codice: string
    descrizione?: string
    lunghezza_piano: number
    larghezza_piano: number
    disponibile: boolean
    in_manutenzione: boolean
  } | null
  onSuccess: () => void
}

export function ToolModal({ open, onOpenChange, editingItem, onSuccess }: ToolModalProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<ToolFormValues>({
    resolver: zodResolver(toolSchema),
    defaultValues: {
      codice: editingItem?.codice || '',
      descrizione: editingItem?.descrizione || '',
      lunghezza_piano: editingItem?.lunghezza_piano || 0,
      larghezza_piano: editingItem?.larghezza_piano || 0,
      disponibile: editingItem?.disponibile ?? true,
      in_manutenzione: editingItem?.in_manutenzione ?? false,
    },
  })

  const onSubmit = async (data: ToolFormValues) => {
    try {
      setIsLoading(true)
      if (editingItem) {
        await toolApi.update(editingItem.id, data)
        toast({
          title: 'Tool aggiornato',
          description: 'Il tool è stato aggiornato con successo.',
        })
      } else {
        await toolApi.create(data)
        toast({
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
              name="codice"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Codice</FormLabel>
                  <FormControl>
                    <Input {...field} />
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
                    <Input {...field} />
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
                        {...field} 
                        onChange={e => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
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

              <FormField
                control={form.control}
                name="in_manutenzione"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel>In Manutenzione</FormLabel>
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
            </div>

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