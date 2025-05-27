'use client'

import { useState, useEffect, useTransition } from 'react'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CatalogoResponse, CatalogoCreate, CatalogoUpdate, catalogoApi } from '@/lib/api'
import { Plus, Pencil, AlertTriangle } from 'lucide-react'

interface CatalogoModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  item: CatalogoResponse | null
}

// Schema di validazione con zod
const catalogoSchema = z.object({
  part_number: z.string().min(1, "Part Number obbligatorio").max(50, "Massimo 50 caratteri"),
  descrizione: z.string().min(1, "Descrizione obbligatoria"),
  categoria: z.string().optional(),
  sotto_categoria: z.string().optional(),
  attivo: z.boolean(),
  note: z.string().optional()
})

export default function CatalogoModal({ isOpen, onClose, onSuccess, item }: CatalogoModalProps) {
  const [formData, setFormData] = useState<Partial<CatalogoCreate>>({
    part_number: '',
    descrizione: '',
    categoria: '',
    sotto_categoria: '',
    attivo: true,
    note: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isPending, startTransition] = useTransition()
  
  // ✅ FIX 3: Stato per gestire la modifica del part number
  const [isPartNumberEditable, setIsPartNumberEditable] = useState(false)
  
  const router = useRouter()
  const { toast } = useToast()

  // Popola form quando si apre in modalità modifica
  useEffect(() => {
    if (item) {
      setFormData({
        part_number: item.part_number,
        descrizione: item.descrizione,
        categoria: item.categoria || '',
        sotto_categoria: item.sotto_categoria || '',
        attivo: item.attivo,
        note: item.note || ''
      })
    } else {
      // Reset form per una nuova creazione
      setFormData({
        part_number: '',
        descrizione: '',
        categoria: '',
        sotto_categoria: '',
        attivo: true,
        note: ''
      })
    }
    setErrors({})
  }, [item, isOpen])

  const handleChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Rimuovi errore se il campo viene corretto
    if (errors[field]) {
      setErrors(prev => {
        const updated = { ...prev }
        delete updated[field]
        return updated
      })
    }
  }

  // ✅ FIX 6: Gestione focus per sostituzione contenuto
  const handleFocus = (field: string) => {
    // Se il campo ha un valore di default, lo selezioniamo tutto per facilitare la sostituzione
    const input = document.getElementById(field) as HTMLInputElement
    if (input && input.value) {
      input.select()
    }
  }

  // ✅ FIX 3: Toggle per abilitare/disabilitare modifica part number
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

  const validateForm = () => {
    try {
      // Valida solo se usiamo tutti i campi obbligatori
      catalogoSchema.parse(formData)
      return { valid: true, errors: {} }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errorMap: Record<string, string> = {}
        error.errors.forEach((err) => {
          if (err.path[0]) {
            errorMap[err.path[0].toString()] = err.message
          }
        })
        return { valid: false, errors: errorMap }
      }
      return { valid: false, errors: { form: 'Errore di validazione' } }
    }
  }

  const handleSubmit = async () => {
    const validation = validateForm()
    if (!validation.valid) {
      setErrors(validation.errors)
      return
    }

    setIsSubmitting(true)
    try {
      if (item) {
        // ✅ FIX 3: Verifica se il part_number è stato modificato
        const partNumberChanged = item.part_number !== formData.part_number
        
        if (partNumberChanged) {
          // Se il part_number è cambiato, usa l'API di propagazione
          await catalogoApi.updatePartNumberWithPropagation(item.part_number, formData.part_number!)
          toast({
            variant: 'success',
            title: 'Part Number Aggiornato',
            description: `Part Number aggiornato da "${item.part_number}" a "${formData.part_number}" con propagazione globale.`
          })
        }
        
        // Modalità modifica - aggiorna gli altri campi
        const updateData: CatalogoUpdate = {
          descrizione: formData.descrizione,
          categoria: formData.categoria || undefined,
          sotto_categoria: formData.sotto_categoria || undefined,
          attivo: formData.attivo,
          note: formData.note || undefined
        }
        
        // Solo se non abbiamo già aggiornato tramite propagazione
        if (!partNumberChanged) {
          await catalogoApi.update(item.part_number, updateData)
          toast({
            variant: 'success',
            title: 'Aggiornato',
            description: `Part number ${item.part_number} aggiornato con successo.`
          })
        }
      } else {
        // Modalità creazione
        const createData = formData as CatalogoCreate
        await catalogoApi.create(createData)
        toast({
          variant: 'success',
          title: 'Creato',
          description: `Nuovo part number ${formData.part_number} creato con successo.`
        })
      }
      
      // ✅ FIX 1: Refresh automatico dopo operazione
      router.refresh()
      
      startTransition(() => {
        onSuccess()
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

  // ✅ FIX 1: Funzione per salvare e resettare il form (CORRETTA)
  const handleSaveAndNew = async () => {
    const validation = validateForm()
    if (!validation.valid) {
      setErrors(validation.errors)
      return
    }

    setIsSubmitting(true)
    try {
      // Modalità creazione (il pulsante + è visibile solo in creazione)
      const createData = formData as CatalogoCreate
      await catalogoApi.create(createData)
      
      toast({
        variant: 'success',
        title: 'Creato e pronto per il prossimo',
        description: `Part number ${formData.part_number} creato con successo. Form resettato per un nuovo inserimento.`
      })

      // Reset del form per un nuovo inserimento
      setFormData({
        part_number: '',
        descrizione: '',
        categoria: '',
        sotto_categoria: '',
        attivo: true,
        note: ''
      })
      setErrors({})

      // ✅ FIX 1: Refresh automatico dopo operazione
      router.refresh()
      
      // ✅ FIX 2: Aggiorna i dati senza chiudere il modal
      startTransition(() => {
        onSuccess() // Questo aggiorna la lista principale
      })
      
      // NON chiudiamo il modal - rimane aperto per il prossimo inserimento
      // Il focus viene automaticamente messo sul primo campo (part_number)
      setTimeout(() => {
        const partNumberInput = document.getElementById('part_number') as HTMLInputElement
        if (partNumberInput) {
          partNumberInput.focus()
        }
      }, 100)
      
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {item ? `Modifica Part Number: ${item.part_number}` : 'Crea Nuovo Part Number'}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="part_number" className="text-right">
              Part Number
            </Label>
            {item ? (
              <div className="col-span-3 space-y-2">
                <div className="flex gap-2">
                  <Input
                    id="part_number"
                    value={formData.part_number || ''}
                    onChange={e => handleChange('part_number', e.target.value)}
                    onFocus={() => handleFocus('part_number')}
                    disabled={!isPartNumberEditable}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleTogglePartNumberEdit}
                    title={isPartNumberEditable ? "Blocca modifica" : "Abilita modifica"}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </div>
                
                {isPartNumberEditable && (
                  <Alert className="border-orange-200 bg-orange-50">
                    <AlertTriangle className="h-4 w-4 text-orange-600" />
                    <AlertDescription className="text-orange-800">
                      ⚠️ Modificare il Part Number può generare inconsistenze. Verrà aggiornato ovunque nel sistema.
                    </AlertDescription>
                  </Alert>
                )}
                
                {errors.part_number && (
                  <p className="text-sm text-destructive">{errors.part_number}</p>
                )}
              </div>
            ) : (
              <div className="col-span-3">
                <Input
                  id="part_number"
                  value={formData.part_number || ''}
                  onChange={e => handleChange('part_number', e.target.value)}
                  onFocus={() => handleFocus('part_number')}
                  className="w-full"
                />
                {errors.part_number && (
                  <p className="text-sm text-destructive mt-1">{errors.part_number}</p>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="descrizione" className="text-right">
              Descrizione
            </Label>
            <Input
              id="descrizione"
              value={formData.descrizione || ''}
              onChange={e => handleChange('descrizione', e.target.value)}
              onFocus={() => handleFocus('descrizione')}
              className="col-span-3"
            />
            {errors.descrizione && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.descrizione}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="categoria" className="text-right">
              Categoria
            </Label>
            <Input
              id="categoria"
              value={formData.categoria || ''}
              onChange={e => handleChange('categoria', e.target.value)}
              onFocus={() => handleFocus('categoria')}
              className="col-span-3"
              placeholder="Opzionale"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="sotto_categoria" className="text-right">
              Sotto Categoria
            </Label>
            <Input
              id="sotto_categoria"
              value={formData.sotto_categoria || ''}
              onChange={e => handleChange('sotto_categoria', e.target.value)}
              onFocus={() => handleFocus('sotto_categoria')}
              className="col-span-3"
              placeholder="Opzionale"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="note" className="text-right">
              Note
            </Label>
            <Input
              id="note"
              value={formData.note || ''}
              onChange={e => handleChange('note', e.target.value)}
              onFocus={() => handleFocus('note')}
              className="col-span-3"
              placeholder="Opzionale"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="attivo" className="text-right">
              Stato
            </Label>
            <div className="col-span-3">
              <select
                id="attivo"
                value={formData.attivo ? 'true' : 'false'}
                onChange={e => handleChange('attivo', e.target.value === 'true')}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="true">Attivo</option>
                <option value="false">Non attivo</option>
              </select>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting || isPending}>
            Annulla
          </Button>
          
          {/* ✅ FIX 2: Pulsante "+" visibile solo in modalità creazione */}
          {!item && (
            <Button 
              type="button" 
              variant="secondary" 
              onClick={handleSaveAndNew} 
              disabled={isSubmitting || isPending}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Salva e Nuovo
            </Button>
          )}
          
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting || isPending}>
            {isSubmitting || isPending ? 'Salvataggio...' : item ? 'Aggiorna' : 'Salva'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 