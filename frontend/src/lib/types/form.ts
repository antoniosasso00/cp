import * as z from 'zod'

export const toolSchema = z.object({
  codice: z.string().min(1, 'Il codice è obbligatorio'),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0, 'La lunghezza deve essere positiva'),
  larghezza_piano: z.number().min(0, 'La larghezza deve essere positiva'),
  disponibile: z.boolean().default(true),
  in_manutenzione: z.boolean().default(false),
})

export type ToolFormValues = z.infer<typeof toolSchema>

export const cicloSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  temperatura_max: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_max: z.number().min(0, 'La pressione deve essere positiva'),
  temperatura_stasi1: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_stasi1: z.number().min(0, 'La pressione deve essere positiva'),
  durata_stasi1: z.number().min(0, 'La durata deve essere positiva'),
  attiva_stasi2: z.boolean(),
  temperatura_stasi2: z.number().min(0, 'La temperatura deve essere positiva').optional(),
  pressione_stasi2: z.number().min(0, 'La pressione deve essere positiva').optional(),
  durata_stasi2: z.number().min(0, 'La durata deve essere positiva').optional(),
})

export type CicloFormValues = z.infer<typeof cicloSchema> 