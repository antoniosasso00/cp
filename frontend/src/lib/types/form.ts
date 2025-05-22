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
  temperatura_stasi1: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_stasi1: z.number().min(0, 'La pressione deve essere positiva'),
  durata_stasi1: z.number().min(1, 'La durata deve essere almeno 1 minuto'),
  attiva_stasi2: z.boolean(),
  temperatura_stasi2: z.number().optional(),
  pressione_stasi2: z.number().optional(),
  durata_stasi2: z.number().optional(),
}).refine((data) => {
  // Valida i campi della stasi 2 solo se attiva_stasi2 è true
  if (data.attiva_stasi2) {
    return (
      data.temperatura_stasi2 !== undefined && data.temperatura_stasi2 >= 0 &&
      data.pressione_stasi2 !== undefined && data.pressione_stasi2 >= 0 &&
      data.durata_stasi2 !== undefined && data.durata_stasi2 >= 1
    )
  }
  return true
}, {
  message: "I campi della stasi 2 sono obbligatori quando la stasi 2 è attiva",
  path: ["stasi2"]
})

export type CicloFormValues = z.infer<typeof cicloSchema>

export const autoclaveSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  codice: z.string().min(1, 'Il codice è obbligatorio'),
  lunghezza: z.number().min(0, 'La lunghezza deve essere positiva'),
  larghezza_piano: z.number().min(0, 'La larghezza deve essere positiva'),
  num_linee_vuoto: z.number().min(0, 'Il numero di linee deve essere positivo'),
  temperatura_max: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_max: z.number().min(0, 'La pressione deve essere positiva'),
  stato: z.enum(['DISPONIBILE', 'IN_USO', 'MANUTENZIONE', 'GUASTO', 'SPENTA']),
  produttore: z.string().optional(),
  anno_produzione: z.number().optional(),
  note: z.string().optional(),
})

export type AutoclaveFormValues = z.infer<typeof autoclaveSchema> 