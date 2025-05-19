'use client'

import { useState, useEffect } from 'react'
import { z } from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { CatalogoResponse, CatalogoCreate, CatalogoUpdate, catalogoApi } from '@/lib/api'

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
  attivo: z.boolean(),
  note: z.string().optional()
})

export default function CatalogoModal({ isOpen, onClose, onSuccess, item }: CatalogoModalProps) {
  const [formData, setFormData] = useState<Partial<CatalogoCreate>>({
    part_number: '',
    descrizione: '',
    categoria: '',
    attivo: true,
    note: ''
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  // Popola form quando si apre in modalità modifica
  useEffect(() => {
    if (item) {
      setFormData({
        part_number: item.part_number,
        descrizione: item.descrizione,
        categoria: item.categoria || '',
        attivo: item.attivo,
        note: item.note || ''
      })
    } else {
      // Reset form per una nuova creazione
      setFormData({
        part_number: '',
        descrizione: '',
        categoria: '',
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
        // Modalità modifica
        const updateData: CatalogoUpdate = {
          descrizione: formData.descrizione,
          categoria: formData.categoria || undefined,
          attivo: formData.attivo,
          note: formData.note || undefined
        }
        await catalogoApi.update(item.part_number, updateData)
        toast({
          variant: 'success',
          title: 'Aggiornato',
          description: `Part number ${item.part_number} aggiornato con successo.`
        })
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
      onSuccess()
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
            <Input
              id="part_number"
              value={formData.part_number || ''}
              onChange={e => handleChange('part_number', e.target.value)}
              disabled={!!item} // Disabilita in modalità modifica
              className="col-span-3"
            />
            {errors.part_number && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.part_number}</p>
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
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Annulla
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Salvataggio...' : item ? 'Aggiorna' : 'Crea'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 