import { z } from 'zod'

// Schema di validazione per ODL
export const odlSchema = z.object({
  parte_id: z.number().min(1, "Seleziona una parte valida"),
  tool_id: z.number().min(1, "Seleziona un tool valido"),
  priorita: z.number().min(1, "Priorità minima 1").max(10, "Priorità massima 10"),
  status: z.enum(["Preparazione", "Laminazione", "Attesa Cura", "Cura", "Finito", "In Coda"], {
    required_error: "Status obbligatorio"
  }),
  note: z.string().optional()
})

export type ODLFormValues = z.infer<typeof odlSchema>

export const odlDefaultValues: ODLFormValues = {
  parte_id: 0,
  tool_id: 0,
  priorita: 1,
  status: "Preparazione",
  note: ""
}

// Opzioni per il campo status
export const statusOptions = [
  { value: "Preparazione", label: "Preparazione" },
  { value: "Laminazione", label: "Laminazione" },
  { value: "Attesa Cura", label: "Attesa Cura" },
  { value: "Cura", label: "Cura" },
  { value: "Finito", label: "Finito" },
  { value: "In Coda", label: "In Coda" }
] 