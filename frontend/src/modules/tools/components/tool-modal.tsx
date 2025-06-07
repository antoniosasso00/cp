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
  Plus,
  X,
  Save
} from 'lucide-react'
import { Button } from '@/components/ui/button'

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
      
      // Reset del form PRIMA del toast per evitare interferenze
      form.reset(toolDefaultValues)
      
      // Focus immediato sul primo campo
      setTimeout(() => {
        const partNumberInput = document.querySelector('input[name="part_number_tool"]') as HTMLInputElement
        if (partNumberInput) {
          partNumberInput.focus()
        }
      }, 50)
      
      // NON chiamare refresh o onSuccess() qui per evitare re-render che chiudono il dialog
      
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
      <DialogContent className="sm:max-w-[500px] h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b shrink-0">
          <DialogTitle>{editingItem ? 'Modifica Tool' : 'Nuovo Tool'}</DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto px-6">
          <FormWrapper
            form={form}
            onSubmit={onSubmit}
            isLoading={isLoading}
            submitText={editingItem ? "Aggiorna" : "Crea Tool"}
            showCancel={false}
            showSaveAndNew={false}
            cardClassName="border-0 shadow-none"
            headerClassName="hidden"
            contentClassName="py-6"
            footerClassName="hidden"
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
                placeholder="100"
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
                placeholder="50"
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
                value={form.watch('peso')}
                onChange={(value) => form.setValue('peso', value as number | null)}
                placeholder="Es. 12.4"
                min={0}
                step={0.1}
                allowEmpty={true}
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
                <p className="text-xs text-muted-foreground">
                  Tool disponibile per il nesting
                </p>
              </div>
              <Switch
                checked={form.watch('disponibile') || false}
                onCheckedChange={(checked) => form.setValue('disponibile', Boolean(checked))}
              />
            </div>
          </FormWrapper>
        </div>
        
        {/* Footer con pulsanti fissi */}
        <div className="px-6 py-4 border-t shrink-0 bg-background">
          <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
              className="w-full sm:w-auto"
            >
              <X className="h-4 w-4 mr-2" />
              Annulla
            </Button>
            
            {!editingItem && (
              <Button
                type="button"
                variant="outline"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  form.handleSubmit(handleSaveAndNew)(e)
                }}
                disabled={isLoading}
                className="w-full sm:w-auto"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Salva e Nuovo
              </Button>
            )}
            
            <Button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                form.handleSubmit(onSubmit)(e)
              }}
              disabled={isLoading}
              className="w-full sm:w-auto"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {editingItem ? "Aggiorna" : "Crea Tool"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
} 