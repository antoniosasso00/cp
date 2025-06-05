import { z } from 'zod'

// Schema di validazione per il tool
export const toolSchema = z.object({
  part_number_tool: z.string().min(1, "Part Number Tool obbligatorio"),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0.1, "Lunghezza deve essere maggiore di 0"),
  larghezza_piano: z.number().min(0.1, "Larghezza deve essere maggiore di 0"),
  peso: z.number().min(0, "Il peso deve essere positivo").optional().nullable(),
  materiale: z.string().optional(),
  disponibile: z.boolean().default(true)
})

export type ToolFormValues = z.infer<typeof toolSchema>

export const toolDefaultValues: ToolFormValues = {
  part_number_tool: '',
  descrizione: '',
  lunghezza_piano: 100,
  larghezza_piano: 50,
  peso: null,
  materiale: '',
  disponibile: true,
} 