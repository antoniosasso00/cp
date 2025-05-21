import * as z from 'zod'

export const toolSchema = z.object({
  codice: z.string().min(1, 'Il codice è obbligatorio'),
  descrizione: z.string().optional(),
  lunghezza_piano: z.number().min(0, 'La lunghezza deve essere positiva'),
  larghezza_piano: z.number().min(0, 'La larghezza deve essere positiva'),
  disponibile: z.boolean().default(true),
})

export type ToolFormValues = z.infer<typeof toolSchema>

export const parteSchema = z.object({
  part_number: z.string().min(1, 'Il part number è obbligatorio'),
  descrizione_breve: z.string().min(1, 'La descrizione è obbligatoria'),
  num_valvole_richieste: z.number().min(1, 'Il numero di valvole deve essere almeno 1'),
  note_produzione: z.string().nullable(),
  ciclo_cura_id: z.number().nullable(),
  tool_ids: z.array(z.number()).min(1, 'Seleziona almeno un tool'),
})

export type ParteFormValues = z.infer<typeof parteSchema>

export const cicloSchema = z.object({
  nome: z.string().min(1, 'Il nome è obbligatorio'),
  temperatura_stasi1: z.number().min(0, 'La temperatura deve essere positiva'),
  pressione_stasi1: z.number().min(0, 'La pressione deve essere positiva'),
  durata_stasi1: z.number().min(1, 'La durata deve essere almeno 1 minuto'),
  attiva_stasi2: z.boolean(),
  temperatura_stasi2: z.number().min(0, 'La temperatura deve essere positiva').optional().nullable(),
  pressione_stasi2: z.number().min(0, 'La pressione deve essere positiva').optional().nullable(),
  durata_stasi2: z.number().min(1, 'La durata deve essere almeno 1 minuto').optional().nullable(),
}).refine((data) => {
  // Se la stasi 2 è attiva, tutti i suoi campi devono essere presenti
  if (data.attiva_stasi2) {
    return data.temperatura_stasi2 != null && 
           data.pressione_stasi2 != null && 
           data.durata_stasi2 != null;
  }
  return true;
}, {
  message: "Tutti i campi della Stasi 2 sono obbligatori quando è attiva",
  path: ["attiva_stasi2"]
});

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