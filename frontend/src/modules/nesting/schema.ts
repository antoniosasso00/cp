import { z } from 'zod'

// Schema di validazione per i parametri di nesting
export const nestingSchema = z.object({
  padding_mm: z.number().min(0.1).max(100),
  min_distance_mm: z.number().min(0.1).max(50),
  vacuum_lines_capacity: z.number().min(1).max(50),
  use_fallback: z.boolean(),
  allow_heuristic: z.boolean(),
  timeout_override: z.number().optional(),
  
  // Parametri aerospace avanzati
  enable_rotation_optimization: z.boolean(),
  heat_transfer_spacing: z.number().min(0.1).max(5),
  airflow_margin: z.number().min(0.1).max(5),
  composite_cure_pressure: z.number().min(0.1).max(2),
  autoclave_efficiency_target: z.number().min(50).max(95),
  enable_aerospace_constraints: z.boolean(),
  
  // Standard industriali
  boeing_787_mode: z.boolean(),
  airbus_a350_mode: z.boolean(),
  general_aviation_mode: z.boolean(),
})

export type NestingParams = z.infer<typeof nestingSchema>

export const defaultNestingParams: NestingParams = {
  padding_mm: 0.5,
  min_distance_mm: 0.5,
  vacuum_lines_capacity: 25,
  use_fallback: true,
  allow_heuristic: true,
  timeout_override: undefined,
  
  // Parametri aerospace avanzati
  enable_rotation_optimization: true,
  heat_transfer_spacing: 0.3,
  airflow_margin: 0.2,
  composite_cure_pressure: 0.7,
  autoclave_efficiency_target: 85.0,
  enable_aerospace_constraints: true,
  
  // Standard industriali
  boeing_787_mode: false,
  airbus_a350_mode: false,
  general_aviation_mode: true,
}

// Schema per la creazione di un nuovo nesting
export const nestingCreateSchema = z.object({
  odl_ids: z.array(z.string()).min(1, "Seleziona almeno un ODL"),
  autoclave_ids: z.array(z.string()).min(1, "Seleziona almeno un'autoclave"),
  parametri: nestingSchema
})

export type NestingCreateFormValues = z.infer<typeof nestingCreateSchema>

// Removed unused export nestingCreateDefaultValues 