'use client'

import { useState, useEffect, useTransition } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Switch } from '@/components/ui/switch'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FormField as UIFormField, FormControl, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { toolsApi, Tool } from '@/lib/api'
import { FormField, FormWrapper } from '@/shared/components/form'
import { toolSchema, ToolFormValues, toolDefaultValues } from '../schema'
import { 
  Loader2, 
  Pencil, 
  AlertTriangle, 
  Plus 
} from 'lucide-react'

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
    defaultValues: toolDefaultValues,
  })



  // Aggiorna i valori del form quando editingItem cambia
  useEffect(() => {
    if (editingItem) {
      form.reset({
        part_number_tool: editingItem.part_number_tool,
        descrizione: editingItem.descrizione || '',
        lunghezza_piano: editingItem.lunghezza_piano,
        larghezza_piano: editingItem.larghezza_piano,
        peso: editingItem.peso || null,
        materiale: editingItem.materiale || '',
        disponibile: editingItem.disponibile,
      })
    } else {
      form.reset(toolDefaultValues)
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
        await toolsApi.updateTool(editingItem.id, submitData)
        toast({
          variant: 'success',
          title: 'Tool aggiornato',
          description: `Tool ${submitData.part_number_tool} aggiornato con successo.`,
        })
      } else {
        await toolsApi.createTool(submitData)
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
      await toolsApi.createTool(submitData)
      toast({
        variant: 'success',
        title: 'Tool creato e pronto per il prossimo',
        description: `Tool ${submitData.part_number_tool} creato con successo. Form resettato per un nuovo inserimento.`,
      })
      
      // Reset del form per un nuovo inserimento
      form.reset(toolDefaultValues)
      
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
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editingItem ? 'Modifica Tool' : 'Nuovo Tool'}</DialogTitle>
        </DialogHeader>
        
        <FormWrapper
          form={form}
          onSubmit={onSubmit}
          isLoading={isLoading}
          submitText={editingItem ? "Aggiorna" : "Crea Tool"}
          showCancel={true}
          onCancel={() => onOpenChange(false)}
          showSaveAndNew={!editingItem}
          onSaveAndNew={handleSaveAndNew}
          saveAndNewText="Salva e Nuovo"
          cardClassName="border-0 shadow-none"
          headerClassName="hidden"
        >
          <FormField
            label="Part Number Tool"
            name="part_number_tool"
            value={form.watch('part_number_tool')}
            onChange={(value) => form.setValue('part_number_tool', value as string)}
            placeholder="es. T001"
            required
            error={form.formState.errors.part_number_tool?.message}
          />

          <FormField
            label="Descrizione"
            name="descrizione"
            value={form.watch('descrizione')}
            onChange={(value) => form.setValue('descrizione', value as string)}
            placeholder="Descrizione opzionale"
            error={form.formState.errors.descrizione?.message}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Lunghezza Piano (mm)"
              name="lunghezza_piano"
              type="number"
              value={form.watch('lunghezza_piano')}
              onChange={(value) => form.setValue('lunghezza_piano', value as number)}
              min={0.1}
              step={0.1}
              required
              error={form.formState.errors.lunghezza_piano?.message}
            />

            <FormField
              label="Larghezza Piano (mm)"
              name="larghezza_piano"
              type="number"
              value={form.watch('larghezza_piano')}
              onChange={(value) => form.setValue('larghezza_piano', value as number)}
              min={0.1}
              step={0.1}
              required
              error={form.formState.errors.larghezza_piano?.message}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Peso (kg)"
              name="peso"
              type="number"
              value={form.watch('peso') ?? ''}
              onChange={(value) => form.setValue('peso', value ? value as number : null)}
              placeholder="Es. 12.4"
              min={0}
              step={0.1}
              description="Campo opzionale"
              error={form.formState.errors.peso?.message}
            />

            <FormField
              label="Materiale"
              name="materiale"
              value={form.watch('materiale')}
              onChange={(value) => form.setValue('materiale', value as string)}
              placeholder="es. Alluminio, Acciaio"
              error={form.formState.errors.materiale?.message}
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Disponibile</label>
            </div>
            <Switch
              checked={form.watch('disponibile')}
              onCheckedChange={(checked) => form.setValue('disponibile', checked)}
            />
          </div>
        </FormWrapper>
      </DialogContent>
    </Dialog>
  )
} 