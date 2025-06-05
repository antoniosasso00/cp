'use client'

import { useState, useEffect, useTransition } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CatalogoResponse, CatalogoCreate, CatalogoUpdate, catalogApi } from '@/lib/api'
import { FormField, FormWrapper } from '@/shared/components/form'
import { catalogoSchema, CatalogoFormValues, catalogoDefaultValues } from '../schema'
import { Plus, Pencil, AlertTriangle } from 'lucide-react'

interface CatalogoModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  item: CatalogoResponse | null
}

export default function CatalogoModal({ isOpen, onClose, onSuccess, item }: CatalogoModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isPending, startTransition] = useTransition()
  const [isPartNumberEditable, setIsPartNumberEditable] = useState(false)
  
  const router = useRouter()
  const { toast } = useToast()

  const form = useForm<CatalogoFormValues>({
    resolver: zodResolver(catalogoSchema),
    defaultValues: catalogoDefaultValues,
  })

  // Popola form quando si apre in modalità modifica
  useEffect(() => {
    if (item) {
      form.reset({
        part_number: item.part_number,
        descrizione: item.descrizione,
        categoria: item.categoria || '',
        sotto_categoria: item.sotto_categoria || '',
        attivo: item.attivo ?? true,
        note: item.note || ''
      })
    } else {
      // Reset form per una nuova creazione
      form.reset(catalogoDefaultValues)
    }
    setIsPartNumberEditable(false)
  }, [item, isOpen, form])

  const handleTogglePartNumberEdit = () => {
    if (!isPartNumberEditable) {
      // Mostra conferma prima di abilitare la modifica
      const confirmed = window.confirm(
        "⚠️ Modificare il Part Number può generare inconsistenze. Verrà aggiornato ovunque nel sistema.\n\nVuoi continuare?"
      )
      if (confirmed) {
        setIsPartNumberEditable(true)
      }
    } else {
      setIsPartNumberEditable(false)
    }
  }

  const onSubmit = async (data: CatalogoFormValues) => {
    setIsSubmitting(true)
    try {
      if (item) {
        // Verifica se il part_number è stato modificato
        const partNumberChanged = item.part_number !== data.part_number
        
        if (partNumberChanged) {
          // Se il part_number è cambiato, usa l'API di propagazione
          await catalogApi.updatePartNumberWithPropagation(item.part_number, data.part_number!)
          toast({
            variant: 'success',
            title: 'Part Number Aggiornato',
            description: `Part Number aggiornato da "${item.part_number}" a "${data.part_number}" con propagazione globale.`
          })
        }
        
        // Modalità modifica - aggiorna gli altri campi
        const updateData: CatalogoUpdate = {
          descrizione: data.descrizione,
          categoria: data.categoria || undefined,
          sotto_categoria: data.sotto_categoria || undefined,
          attivo: data.attivo,
          note: data.note || undefined
        }
        
        // Solo se non abbiamo già aggiornato tramite propagazione
        if (!partNumberChanged) {
          await catalogApi.updateCatalogItem(item.part_number, updateData)
          toast({
            variant: 'success',
            title: 'Aggiornato',
            description: `Part number ${item.part_number} aggiornato con successo.`
          })
        }
      } else {
        // Modalità creazione
        const createData = data as CatalogoCreate
        await catalogApi.createCatalogItem(createData)
        toast({
          variant: 'success',
          title: 'Creato',
          description: `Nuovo part number ${data.part_number} creato con successo.`
        })
      }
      
      // Refresh automatico dopo operazione
      router.refresh()
      
      startTransition(() => {
        onSuccess()
        onClose()
      })
    } catch (error: unknown) {
      console.error('Errore durante il salvataggio:', error)
      let errorMessage = 'Si è verificato un errore durante il salvataggio.'
      if (error instanceof Error) {
        errorMessage = error.message
      }
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSaveAndNew = async (data: CatalogoFormValues) => {
    setIsSubmitting(true)
    try {
      // Solo modalità creazione
      const createData = data as CatalogoCreate
      await catalogApi.createCatalogItem(createData)
      toast({
        variant: 'success',
        title: 'Creato e pronto per il prossimo',
        description: `Part number ${data.part_number} creato con successo. Form resettato per un nuovo inserimento.`
      })
      
      // Reset del form per un nuovo inserimento
      form.reset(catalogoDefaultValues)
      
      // Refresh automatico dopo operazione
      router.refresh()
      
      // Focus sul primo campo
      setTimeout(() => {
        const partNumberInput = document.querySelector('input[name="part_number"]') as HTMLInputElement
        if (partNumberInput) {
          partNumberInput.focus()
        }
      }, 100)
      
    } catch (error: unknown) {
      console.error('Errore durante il salvataggio (Salva e nuovo):', error)
      let errorMessage = 'Si è verificato un errore durante il salvataggio.'
      if (error instanceof Error) {
        errorMessage = error.message
      }
      toast({
        variant: 'destructive',
        title: 'Errore',
        description: errorMessage
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {item ? (
              <>
                <Pencil className="h-5 w-5" />
                Modifica Part Number
              </>
            ) : (
              <>
                <Plus className="h-5 w-5" />
                Nuovo Part Number
              </>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <FormWrapper
          form={form}
          onSubmit={onSubmit}
          isLoading={isSubmitting}
          submitText={item ? "Aggiorna" : "Crea Part Number"}
          showCancel={true}
          onCancel={onClose}
          showSaveAndNew={!item}
          onSaveAndNew={handleSaveAndNew}
          saveAndNewText="Salva e Nuovo"
          cardClassName="border-0 shadow-none"
          headerClassName="hidden"
        >
          <div className="space-y-1">
            <FormField
              label="Part Number"
              name="part_number"
              value={form.watch('part_number')}
              onChange={(value) => form.setValue('part_number', value as string)}
              placeholder="es. PN001"
              required
              disabled={Boolean(item && !isPartNumberEditable)}
              error={form.formState.errors.part_number?.message}
            />
            
            {item && (
              <div className="flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleTogglePartNumberEdit}
                  className="text-xs"
                >
                  {isPartNumberEditable ? 'Blocca modifica' : 'Abilita modifica Part Number'}
                </Button>
              </div>
            )}
            
            {item && isPartNumberEditable && (
              <Alert variant="destructive" className="mt-2">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  ⚠️ Modificare il Part Number aggiornerà tutti i riferimenti nel sistema
                </AlertDescription>
              </Alert>
            )}
          </div>

          <FormField
            label="Descrizione"
            name="descrizione"
            value={form.watch('descrizione')}
            onChange={(value) => form.setValue('descrizione', value as string)}
            placeholder="Descrizione del part number"
            required
            error={form.formState.errors.descrizione?.message}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              label="Categoria"
              name="categoria"
              value={form.watch('categoria')}
              onChange={(value) => form.setValue('categoria', value as string)}
              placeholder="es. Valvole"
              error={form.formState.errors.categoria?.message}
            />

            <FormField
              label="Sotto-categoria"
              name="sotto_categoria"
              value={form.watch('sotto_categoria')}
              onChange={(value) => form.setValue('sotto_categoria', value as string)}
              placeholder="es. Valvole a sfera"
              error={form.formState.errors.sotto_categoria?.message}
            />
          </div>

          <FormField
            label="Note"
            name="note"
            type="textarea"
            value={form.watch('note')}
            onChange={(value) => form.setValue('note', value as string)}
            placeholder="Note aggiuntive (opzionale)"
            rows={3}
            error={form.formState.errors.note?.message}
          />

          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <label className="text-sm font-medium">Attivo</label>
              <p className="text-xs text-muted-foreground">
                Disabilita per nascondere il part number dalle selezioni
              </p>
            </div>
            <Switch
              checked={form.watch('attivo') || false}
              onCheckedChange={(checked) => form.setValue('attivo', Boolean(checked))}
            />
          </div>
        </FormWrapper>
      </DialogContent>
    </Dialog>
  )
} 