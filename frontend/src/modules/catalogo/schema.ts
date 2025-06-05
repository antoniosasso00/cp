import { z } from 'zod'

// Schema di validazione per il catalogo
export const catalogoSchema = z.object({
  part_number: z.string().min(1, "Part Number obbligatorio").max(50, "Massimo 50 caratteri"),
  descrizione: z.string().min(1, "Descrizione obbligatoria"),
  categoria: z.string().optional(),
  sotto_categoria: z.string().optional(),
  attivo: z.boolean().default(true),
  note: z.string().optional()
})

export type CatalogoFormValues = z.infer<typeof catalogoSchema>

export const catalogoDefaultValues: CatalogoFormValues = {
  part_number: '',
  descrizione: '',
  categoria: '',
  sotto_categoria: '',
  attivo: true,
  note: ''
} 