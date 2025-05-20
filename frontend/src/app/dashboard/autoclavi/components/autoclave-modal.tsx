'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { autoclaveApi } from '@/lib/api'

const autoclaveSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  codice: z.string().min(1, 'Il codice è obbligatorio'),
  lunghezza: z.number().min(0, 'La lunghezza deve essere positiva'),
  larghezza_piano: z.number().min(0, 'La larghezza deve essere positiva'),
  num_linee_vuoto: z.number().min(0, 'Il numero di linee deve essere positivo'),
  stato: z.enum(['DISPONIBILE', 'IN_USO', 'GUASTO', 'MANUTENZIONE', 'SPENTA']),
  temperatura_max: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_max: z.number().min(0, 'La pressione deve essere positiva'),
  produttore: z.string().optional(),
  anno_produzione: z.number().optional(),
  note: z.string().optional(),
})

type AutoclaveFormValues = z.infer<typeof autoclaveSchema>

interface AutoclaveModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingItem?: {
    id: number
    nome: string
    codice: string
    lunghezza: number
    larghezza_piano: number
    num_linee_vuoto: number
    stato: 'DISPONIBILE' | 'IN_USO' | 'GUASTO' | 'MANUTENZIONE' | 'SPENTA'
    temperatura_max: number
    pressione_max: number
    produttore?: string
    anno_produzione?: number
    note?: string
  } | null
  onSuccess: () => void
}

export function AutoclaveModal({ open, onOpenChange, editingItem, onSuccess }: AutoclaveModalProps) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const form = useForm<AutoclaveFormValues>({
    resolver: zodResolver(autoclaveSchema),
    defaultValues: {
      nome: editingItem?.nome || '',
      codice: editingItem?.codice || '',
      lunghezza: editingItem?.lunghezza || 0,
      larghezza_piano: editingItem?.larghezza_piano || 0,
      num_linee_vuoto: editingItem?.num_linee_vuoto || 0,
      stato: editingItem?.stato || 'DISPONIBILE',
      temperatura_max: editingItem?.temperatura_max || 0,
      pressione_max: editingItem?.pressione_max || 0,
      produttore: editingItem?.produttore || '',
      anno_produzione: editingItem?.anno_produzione || undefined,
      note: editingItem?.note || '',
    },
  })

  const onSubmit = async (data: AutoclaveFormValues) => {
    try {
      setIsLoading(true)
      if (editingItem) {
        await autoclaveApi.update(editingItem.id, data)
        toast({
          title: 'Autoclave aggiornata',
          description: 'L\'autoclave è stata aggiornata con successo.',
        })
      } else {
        await autoclaveApi.create(data)
        toast({
          title: 'Autoclave creata',
          description: 'La nuova autoclave è stata creata con successo.',
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
          <DialogTitle>{editingItem ? 'Modifica Autoclave' : 'Nuova Autoclave'}</DialogTitle>
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

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="lunghezza"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Lunghezza (mm)</FormLabel>
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

            <FormField
              control={form.control}
              name="num_linee_vuoto"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Numero Linee Vuoto</FormLabel>
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
              name="stato"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Stato</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleziona lo stato" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="DISPONIBILE">Disponibile</SelectItem>
                      <SelectItem value="IN_USO">In Uso</SelectItem>
                      <SelectItem value="GUASTO">Guasto</SelectItem>
                      <SelectItem value="MANUTENZIONE">In Manutenzione</SelectItem>
                      <SelectItem value="SPENTA">Spenta</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="temperatura_max"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Temperatura Max (°C)</FormLabel>
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
                name="pressione_max"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pressione Max (bar)</FormLabel>
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

            <FormField
              control={form.control}
              name="produttore"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Produttore</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="anno_produzione"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Anno Produzione</FormLabel>
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
              name="note"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Note</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

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