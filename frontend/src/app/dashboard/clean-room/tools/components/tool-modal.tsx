'use client'

import { useState, useEffect, useTransition } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { toolApi, Tool } from '@/lib/api'
import { 
  Loader2, 
  Pencil, 
  AlertTriangle, 
  Plus 
} from 'lucide-react'

// Schema di validazione per il tool
const toolSchema = z.object({
  part_number_tool: z.string().min(1, "Part Number Tool obbligatorio"),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0.1, "Lunghezza deve essere maggiore di 0"),
  larghezza_piano: z.number().min(0.1, "Larghezza deve essere maggiore di 0"),
  // ✅ FIX 4: Campo peso opzionale
  peso: z.number().min(0, "Il peso deve essere positivo").optional().nullable(),
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
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [isPending, startTransition] = useTransition()

  const form = useForm<ToolFormValues>({
    resolver: zodResolver(toolSchema),
    defaultValues: {
      part_number_tool: '',
      descrizione: '',
      lunghezza_piano: 100,
      larghezza_piano: 50,
      // ✅ FIX 4: Peso opzionale (null di default)
      peso: null,
      materiale: '',
      disponibile: true,
    },
  })

  // ✅ FIX 6: Gestione focus per sostituzione contenuto
  const handleFocus = (fieldName: string) => {
    // Seleziona tutto il contenuto quando l'utente fa focus su un campo precompilato
    setTimeout(() => {
      const input = document.querySelector(`input[name="${fieldName}"]`) as HTMLInputElement
      if (input && input.value) {
        input.select()
      }
    }, 0)
  }

  // Aggiorna i valori del form quando editingItem cambia
  useEffect(() => {
    if (editingItem) {
      form.reset({
        part_number_tool: editingItem.part_number_tool,
        descrizione: editingItem.descrizione || '',
        lunghezza_piano: editingItem.lunghezza_piano,
        larghezza_piano: editingItem.larghezza_piano,
        // ✅ FIX 4: Peso opzionale (null se non presente)
        peso: editingItem.peso || null,
        materiale: editingItem.materiale || '',
        disponibile: editingItem.disponibile,
      })
    } else {
      form.reset({
        part_number_tool: '',
        descrizione: '',
        lunghezza_piano: 100,
        larghezza_piano: 50,
        // ✅ FIX 4: Reset peso opzionale
        peso: null,
        materiale: '',
        disponibile: true,
      })
    }
  }, [editingItem, form])

  const onSubmit = async (data: ToolFormValues) => {
    try {
      setIsLoading(true)
      
      // ✅ FIX 4: Gestione corretta dei campi opzionali
      const submitData = {
        part_number_tool: data.part_number_tool,
        descrizione: data.descrizione || undefined,
        lunghezza_piano: data.lunghezza_piano,
        larghezza_piano: data.larghezza_piano,
        peso: data.peso || undefined, // Converte null/0 in undefined
        materiale: data.materiale || undefined,
        disponibile: data.disponibile
      }
      
      console.log('📤 Dati inviati al backend:', submitData) // Debug
      
      if (editingItem) {
        await toolApi.update(editingItem.id, submitData)
        toast({
          variant: 'success',
          title: 'Tool aggiornato',
          description: `Tool ${submitData.part_number_tool} aggiornato con successo.`,
        })
      } else {
        await toolApi.create(submitData)
        toast({
          variant: 'success',
          title: 'Tool creato',
          description: `Nuovo tool ${submitData.part_number_tool} creato con successo.`,
        })
      }
      
      // ✅ FIX 1: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX 2: Usa startTransition per evitare freeze
      startTransition(() => {
        onSuccess()
        onOpenChange(false)
      })
    } catch (error: any) {
      console.error('❌ Errore durante il salvataggio:', error)
      
      // ✅ FIX: Gestione errori migliorata
      let errorMessage = 'Si è verificato un errore durante il salvataggio.'
      
      if (error?.response?.status === 422) {
        const details = error.response.data?.detail
        if (typeof details === 'string') {
          errorMessage = `Errore di validazione: ${details}`
        } else if (Array.isArray(details)) {
          errorMessage = `Errori di validazione: ${details.map((d: any) => d.msg || d.message || d).join(', ')}`
        } else {
          errorMessage = 'Dati non validi. Controlla i campi inseriti.'
        }
      } else if (error?.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Richiesta non valida.'
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // ✅ FIX: Funzione per salvare e resettare il form
  const handleSaveAndNew = async (data: ToolFormValues) => {
    try {
      setIsLoading(true)
      
      // ✅ FIX 4: Gestione corretta dei campi opzionali
      const submitData = {
        part_number_tool: data.part_number_tool,
        descrizione: data.descrizione || undefined,
        lunghezza_piano: data.lunghezza_piano,
        larghezza_piano: data.larghezza_piano,
        peso: data.peso || undefined, // Converte null/0 in undefined
        materiale: data.materiale || undefined,
        disponibile: data.disponibile
      }
      
      console.log('📤 Dati inviati al backend (Salva e nuovo):', submitData) // Debug
      
      // Solo modalità creazione (il pulsante è visibile solo in creazione)
      await toolApi.create(submitData)
      toast({
        variant: 'success',
        title: 'Tool creato e pronto per il prossimo',
        description: `Tool ${submitData.part_number_tool} creato con successo. Form resettato per un nuovo inserimento.`,
      })
      
      // Reset del form per un nuovo inserimento
      form.reset({
        part_number_tool: '',
        descrizione: '',
        lunghezza_piano: 100,
        larghezza_piano: 50,
        peso: null,
        materiale: '',
        disponibile: true,
      })
      
      // ✅ FIX 1: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX: NON chiamiamo onSuccess() per evitare che il modal si chiuda
      // Invece, forziamo un refresh della lista senza chiudere il modal
      
      // NON chiudiamo il modal - rimane aperto per il prossimo inserimento
      // Il focus viene automaticamente messo sul primo campo (part_number_tool)
      setTimeout(() => {
        const partNumberInput = document.querySelector('input[name="part_number_tool"]') as HTMLInputElement
        if (partNumberInput) {
          partNumberInput.focus()
        }
      }, 100)
      
    } catch (error: any) {
      console.error('❌ Errore durante il salvataggio (Salva e nuovo):', error)
      
      // ✅ FIX: Gestione errori migliorata
      let errorMessage = 'Si è verificato un errore durante il salvataggio.'
      
      if (error?.response?.status === 422) {
        const details = error.response.data?.detail
        if (typeof details === 'string') {
          errorMessage = `Errore di validazione: ${details}`
        } else if (Array.isArray(details)) {
          errorMessage = `Errori di validazione: ${details.map((d: any) => d.msg || d.message || d).join(', ')}`
        } else {
          errorMessage = 'Dati non validi. Controlla i campi inseriti.'
        }
      } else if (error?.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Richiesta non valida.'
      } else if (error?.message) {
        errorMessage = error.message
      }
      
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage,
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
                    <Input 
                      {...field} 
                      placeholder="es. T001" 
                      onFocus={() => handleFocus('part_number_tool')}
                    />
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
                    <Input 
                      {...field} 
                      placeholder="Descrizione opzionale" 
                      onFocus={() => handleFocus('descrizione')}
                    />
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
                        onFocus={() => handleFocus('lunghezza_piano')}
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
                        onFocus={() => handleFocus('larghezza_piano')}
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
                    <FormLabel>Peso (kg) <span className="text-muted-foreground">(opzionale)</span></FormLabel>
                    <FormControl>
                      <Input 
                        type="number" 
                        step="0.1"
                        min="0"
                        placeholder="Es. 12.4"
                        {...field} 
                        value={field.value ?? ''}
                        onChange={e => field.onChange(e.target.value ? Number(e.target.value) : null)}
                        onFocus={() => handleFocus('peso')}
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
                      <Input 
                        {...field} 
                        placeholder="es. Alluminio, Acciaio" 
                        onFocus={() => handleFocus('materiale')}
                      />
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
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading || isPending}>
                Annulla
              </Button>
              
              {/* ✅ FIX: Pulsante "Salva e nuovo" visibile solo in modalità creazione */}
              {!editingItem && (
                <Button 
                  type="button" 
                  variant="secondary" 
                  onClick={form.handleSubmit(handleSaveAndNew)} 
                  disabled={isLoading || isPending}
                  className="gap-2"
                >
                  <Plus className="h-4 w-4" />
                  Salva e Nuovo
                </Button>
              )}
              
              <Button type="submit" disabled={isLoading || isPending}>
                {isLoading || isPending ? 'Salvataggio...' : 'Salva'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
} 