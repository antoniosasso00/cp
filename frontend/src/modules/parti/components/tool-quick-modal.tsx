'use client'

import { useState } from 'react'
import { z } from 'zod'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toolsApi, Tool } from '@/lib/api'

interface ToolQuickModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (newTool: Tool) => void
}

// Schema di validazione per il tool
const toolSchema = z.object({
  part_number_tool: z.string().min(1, "Part Number Tool obbligatorio"),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0.1, "Lunghezza deve essere maggiore di 0"),
  larghezza_piano: z.number().min(0.1, "Larghezza deve essere maggiore di 0"),
  disponibile: z.boolean()
})

interface ToolFormData {
  part_number_tool: string;
  descrizione: string;
  lunghezza_piano: number;
  larghezza_piano: number;
  disponibile: boolean;
}

export default function ToolQuickModal({ isOpen, onClose, onSuccess }: ToolQuickModalProps) {
  const [formData, setFormData] = useState<ToolFormData>({
    part_number_tool: '',
    descrizione: '',
    lunghezza_piano: 100,
    larghezza_piano: 50,
    disponibile: true
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  const handleChange = (field: string, value: any) => {
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
      const dataToValidate = {
        ...formData,
        lunghezza_piano: Number(formData.lunghezza_piano),
        larghezza_piano: Number(formData.larghezza_piano),
        descrizione: formData.descrizione || undefined
      }
      
      toolSchema.parse(dataToValidate)
      return { valid: true, errors: {} }
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errorMap: Record<string, string> = {}
        error.errors.forEach(err => {
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

    const dataToSubmit = {
      part_number_tool: formData.part_number_tool,
      descrizione: formData.descrizione || undefined,
      lunghezza_piano: Number(formData.lunghezza_piano),
      larghezza_piano: Number(formData.larghezza_piano),
      disponibile: formData.disponibile
    }

    setIsSubmitting(true)
    try {
      const newTool = await toolsApi.createTool(dataToSubmit)
      toast({
        variant: 'success',
        title: 'Tool Creato',
        description: `Tool "${newTool.part_number_tool}" creato con successo.`
      })
      onSuccess(newTool)
      // Reset form
      setFormData({
        part_number_tool: '',
        descrizione: '',
        lunghezza_piano: 100,
        larghezza_piano: 50,
        disponibile: true
      })
      setErrors({})
    } catch (error: unknown) {
      console.error('Errore durante la creazione del tool:', error)
      let errorMessage = 'Si è verificato un errore durante la creazione del tool.'
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

  const handleClose = () => {
    // Reset form quando si chiude
    setFormData({
      part_number_tool: '',
      descrizione: '',
      lunghezza_piano: 100,
      larghezza_piano: 50,
      disponibile: true
    })
    setErrors({})
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Crea Nuovo Tool</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="part_number_tool" className="text-right">
              Part Number Tool
            </Label>
            <Input
              id="part_number_tool"
              value={formData.part_number_tool}
              onChange={e => handleChange('part_number_tool', e.target.value)}
              className="col-span-3"
              placeholder="es. T001"
            />
            {errors.part_number_tool && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.part_number_tool}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="descrizione" className="text-right">
              Descrizione
            </Label>
            <Input
              id="descrizione"
              value={formData.descrizione}
              onChange={e => handleChange('descrizione', e.target.value)}
              className="col-span-3"
              placeholder="Descrizione opzionale"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="lunghezza_piano" className="text-right">
              Lunghezza (mm)
            </Label>
            <Input
              id="lunghezza_piano"
              type="number"
              min="0.1"
              step="0.1"
              value={formData.lunghezza_piano || ''}
              onChange={e => {
                const value = e.target.value
                if (value === '') {
                  // Permetti campo vuoto temporaneamente
                  handleChange('lunghezza_piano', '')
                } else {
                  const numValue = Number(value)
                  if (!isNaN(numValue) && numValue > 0) {
                    handleChange('lunghezza_piano', numValue)
                  }
                }
              }}
              className="col-span-3"
            />
            {errors.lunghezza_piano && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.lunghezza_piano}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="larghezza_piano" className="text-right">
              Larghezza (mm)
            </Label>
            <Input
              id="larghezza_piano"
              type="number"
              min="0.1"
              step="0.1"
              value={formData.larghezza_piano || ''}
              onChange={e => {
                const value = e.target.value
                if (value === '') {
                  // Permetti campo vuoto temporaneamente
                  handleChange('larghezza_piano', '')
                } else {
                  const numValue = Number(value)
                  if (!isNaN(numValue) && numValue > 0) {
                    handleChange('larghezza_piano', numValue)
                  }
                }
              }}
              className="col-span-3"
            />
            {errors.larghezza_piano && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.larghezza_piano}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="disponibile" className="text-right">
              Disponibile
            </Label>
            <div className="col-span-3">
              <input
                type="checkbox"
                id="disponibile"
                checked={formData.disponibile}
                onChange={e => handleChange('disponibile', e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Annulla
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Creazione...' : 'Crea Tool'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 