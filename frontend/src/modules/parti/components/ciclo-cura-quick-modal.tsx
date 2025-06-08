'use client'

import { useState } from 'react'
import { z } from 'zod'
import { useStandardToast } from '@/shared/hooks/use-standard-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { curingCyclesApi, CicloCura } from '@/lib/api'

interface CicloCuraQuickModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (newCiclo: CicloCura) => void
}

// Schema di validazione per il ciclo di cura
const cicloCuraSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio"),
  temperatura_stasi1: z.number().min(1, "Temperatura deve essere maggiore di 0"),
  pressione_stasi1: z.number().min(0, "Pressione deve essere maggiore o uguale a 0"),
  durata_stasi1: z.number().min(1, "Durata deve essere maggiore di 0"),
  attiva_stasi2: z.boolean(),
  temperatura_stasi2: z.number().optional(),
  pressione_stasi2: z.number().optional(),
  durata_stasi2: z.number().optional()
}).refine((data) => {
  if (data.attiva_stasi2) {
    return data.temperatura_stasi2 !== undefined && 
           data.pressione_stasi2 !== undefined && 
           data.durata_stasi2 !== undefined &&
           data.temperatura_stasi2 > 0 &&
           data.pressione_stasi2 >= 0 &&
           data.durata_stasi2 > 0
  }
  return true
}, {
  message: "Se la stasi 2 è attiva, tutti i suoi parametri sono obbligatori",
  path: ["attiva_stasi2"]
})

interface CicloCuraFormData {
  nome: string;
  temperatura_stasi1: number;
  pressione_stasi1: number;
  durata_stasi1: number;
  attiva_stasi2: boolean;
  temperatura_stasi2: number;
  pressione_stasi2: number;
  durata_stasi2: number;
}

export default function CicloCuraQuickModal({ isOpen, onClose, onSuccess }: CicloCuraQuickModalProps) {
  const [formData, setFormData] = useState<CicloCuraFormData>({
    nome: '',
    temperatura_stasi1: 180,
    pressione_stasi1: 6,
    durata_stasi1: 120,
    attiva_stasi2: false,
    temperatura_stasi2: 200,
    pressione_stasi2: 8,
    durata_stasi2: 60
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useStandardToast()

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

  // Funzione helper per gestire campi numerici migliorati
  const handleNumberChange = (field: string, inputValue: string, defaultValue?: number) => {
    if (inputValue === '') {
      // Permetti campo vuoto temporaneamente
      handleChange(field, '')
    } else {
      const numValue = Number(inputValue)
      if (!isNaN(numValue) && numValue > 0) {
        handleChange(field, numValue)
      } else if (defaultValue !== undefined && numValue === 0) {
        handleChange(field, defaultValue)
      }
    }
  }

  const validateForm = () => {
    try {
      const dataToValidate = {
        ...formData,
        temperatura_stasi1: Number(formData.temperatura_stasi1),
        pressione_stasi1: Number(formData.pressione_stasi1),
        durata_stasi1: Number(formData.durata_stasi1),
        temperatura_stasi2: formData.attiva_stasi2 ? Number(formData.temperatura_stasi2) : undefined,
        pressione_stasi2: formData.attiva_stasi2 ? Number(formData.pressione_stasi2) : undefined,
        durata_stasi2: formData.attiva_stasi2 ? Number(formData.durata_stasi2) : undefined
      }
      
      cicloCuraSchema.parse(dataToValidate)
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
      nome: formData.nome,
      temperatura_stasi1: Number(formData.temperatura_stasi1),
      pressione_stasi1: Number(formData.pressione_stasi1),
      durata_stasi1: Number(formData.durata_stasi1),
      attiva_stasi2: formData.attiva_stasi2,
      ...(formData.attiva_stasi2 && {
        temperatura_stasi2: Number(formData.temperatura_stasi2),
        pressione_stasi2: Number(formData.pressione_stasi2),
        durata_stasi2: Number(formData.durata_stasi2)
      })
    }

    setIsSubmitting(true)
    try {
      const newCiclo = await curingCyclesApi.createCuringCycle(dataToSubmit)
      toast({
        variant: 'success',
        title: 'Ciclo di Cura Creato',
        description: `Ciclo "${newCiclo.nome}" creato con successo.`
      })
      onSuccess(newCiclo)
      // Reset form
      setFormData({
        nome: '',
        temperatura_stasi1: 180,
        pressione_stasi1: 6,
        durata_stasi1: 120,
        attiva_stasi2: false,
        temperatura_stasi2: 200,
        pressione_stasi2: 8,
        durata_stasi2: 60
      })
      setErrors({})
    } catch (error: unknown) {
      console.error('Errore durante la creazione del ciclo di cura:', error)
      let errorMessage = 'Si è verificato un errore durante la creazione del ciclo di cura.'
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
      nome: '',
      temperatura_stasi1: 180,
      pressione_stasi1: 6,
      durata_stasi1: 120,
      attiva_stasi2: false,
      temperatura_stasi2: 200,
      pressione_stasi2: 8,
      durata_stasi2: 60
    })
    setErrors({})
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Crea Nuovo Ciclo di Cura</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="nome" className="text-right">
              Nome
            </Label>
            <Input
              id="nome"
              value={formData.nome}
              onChange={e => handleChange('nome', e.target.value)}
              className="col-span-3"
              placeholder="es. Ciclo Standard"
            />
            {errors.nome && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.nome}</p>
            )}
          </div>

          <div className="col-span-4">
            <h4 className="font-medium mb-2">Stasi 1 (Obbligatoria)</h4>
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="temperatura_stasi1" className="text-right">
              Temperatura (°C)
            </Label>
            <Input
              id="temperatura_stasi1"
              type="number"
              min="1"
              value={formData.temperatura_stasi1 || ''}
              onChange={e => handleNumberChange('temperatura_stasi1', e.target.value)}
              className="col-span-3"
            />
            {errors.temperatura_stasi1 && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.temperatura_stasi1}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="pressione_stasi1" className="text-right">
              Pressione (bar)
            </Label>
            <Input
              id="pressione_stasi1"
              type="number"
              min="0"
              step="0.1"
              value={formData.pressione_stasi1 || ''}
              onChange={e => handleNumberChange('pressione_stasi1', e.target.value)}
              className="col-span-3"
            />
            {errors.pressione_stasi1 && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.pressione_stasi1}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="durata_stasi1" className="text-right">
              Durata (min)
            </Label>
            <Input
              id="durata_stasi1"
              type="number"
              min="1"
              value={formData.durata_stasi1 || ''}
              onChange={e => handleNumberChange('durata_stasi1', e.target.value)}
              className="col-span-3"
            />
            {errors.durata_stasi1 && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.durata_stasi1}</p>
            )}
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="attiva_stasi2" className="text-right">
              Attiva Stasi 2
            </Label>
            <div className="col-span-3">
              <input
                type="checkbox"
                id="attiva_stasi2"
                checked={formData.attiva_stasi2}
                onChange={e => handleChange('attiva_stasi2', e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
            </div>
            {errors.attiva_stasi2 && (
              <p className="col-span-4 text-right text-sm text-destructive">{errors.attiva_stasi2}</p>
            )}
          </div>

          {formData.attiva_stasi2 && (
            <>
              <div className="col-span-4">
                <h4 className="font-medium mb-2">Stasi 2 (Opzionale)</h4>
              </div>

              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="temperatura_stasi2" className="text-right">
                  Temperatura (°C)
                </Label>
                <Input
                  id="temperatura_stasi2"
                  type="number"
                  min="1"
                  value={formData.temperatura_stasi2 || ''}
                  onChange={e => handleNumberChange('temperatura_stasi2', e.target.value)}
                  className="col-span-3"
                />
                {errors.temperatura_stasi2 && (
                  <p className="col-span-4 text-right text-sm text-destructive">{errors.temperatura_stasi2}</p>
                )}
              </div>

              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="pressione_stasi2" className="text-right">
                  Pressione (bar)
                </Label>
                <Input
                  id="pressione_stasi2"
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.pressione_stasi2 || ''}
                  onChange={e => handleNumberChange('pressione_stasi2', e.target.value)}
                  className="col-span-3"
                />
                {errors.pressione_stasi2 && (
                  <p className="col-span-4 text-right text-sm text-destructive">{errors.pressione_stasi2}</p>
                )}
              </div>

              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="durata_stasi2" className="text-right">
                  Durata (min)
                </Label>
                <Input
                  id="durata_stasi2"
                  type="number"
                  min="1"
                  value={formData.durata_stasi2 || ''}
                  onChange={e => handleNumberChange('durata_stasi2', e.target.value)}
                  className="col-span-3"
                />
                {errors.durata_stasi2 && (
                  <p className="col-span-4 text-right text-sm text-destructive">{errors.durata_stasi2}</p>
                )}
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Annulla
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Creazione...' : 'Crea Ciclo'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 