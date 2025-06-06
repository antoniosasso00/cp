import { z } from 'zod'

// Schema di validazione per i parametri di nesting
export const nestingParametriSchema = z.object({
  padding_mm: z.number().min(1, "Padding minimo 1mm").max(100, "Padding massimo 100mm"),
  min_distance_mm: z.number().min(1, "Distanza minima 1mm").max(50, "Distanza massima 50mm"),
  priorita_area: z.boolean(),
  accorpamento_odl: z.boolean()
})

// Schema per la creazione di un nuovo nesting
export const nestingCreateSchema = z.object({
  odl_ids: z.array(z.string()).min(1, "Seleziona almeno un ODL"),
  autoclave_ids: z.array(z.string()).min(1, "Seleziona almeno un'autoclave"),
  parametri: nestingParametriSchema
})

export type NestingParametriFormValues = z.infer<typeof nestingParametriSchema>
export type NestingCreateFormValues = z.infer<typeof nestingCreateSchema>

// Valori di default ottimizzati per massima efficienza
export const nestingParametriDefaultValues: NestingParametriFormValues = {
  padding_mm: 1,  // 🚀 OTTIMIZZAZIONE: Ultra-aggressivo 1mm
  min_distance_mm: 1,  // 🚀 OTTIMIZZAZIONE: Ultra-aggressivo 1mm
  priorita_area: true,
  accorpamento_odl: false
}

export const nestingCreateDefaultValues: NestingCreateFormValues = {
  odl_ids: [],
  autoclave_ids: [],
  parametri: nestingParametriDefaultValues
} 