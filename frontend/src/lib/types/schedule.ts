// Definizione dei tipi di schedule per il frontend

// Enum per gli stati di una schedulazione
export enum ScheduleEntryStatus {
  SCHEDULED = "scheduled",      // Schedulato automaticamente
  MANUAL = "manual",           // Schedulato manualmente
  PREVISIONALE = "previsionale",  // Schedulazione previsionale (da frequenza)
  IN_ATTESA = "in_attesa",     // In attesa di avvio
  IN_CORSO = "in_corso",       // In corso di esecuzione
  DONE = "done",               // Completato
  POSTICIPATO = "posticipato", // Posticipato dall'operatore
}

// Enum per il tipo di schedulazione
export enum ScheduleEntryType {
  ODL_SPECIFICO = "odl_specifico",        // Schedulazione per ODL specifico
  CATEGORIA = "categoria",                // Schedulazione per categoria
  SOTTO_CATEGORIA = "sotto_categoria",    // Schedulazione per sotto-categoria
  RICORRENTE = "ricorrente",             // Schedulazione ricorrente
}

// Tipo per l'ODL nella risposta
export interface ODLInSchedule {
  id: number;
  priorita: number;
  status: string;
  parte_id: number;
  tool_id: number;
}

// Tipo per l'autoclave nella risposta
export interface AutoclaveInSchedule {
  id: number;
  nome: string;
  codice: string;
  num_linee_vuoto: number;
}

// Tipo per una schedulazione
export interface ScheduleEntry {
  id: number;
  schedule_type: ScheduleEntryType;
  odl_id?: number;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  start_datetime: string;
  end_datetime?: string;
  status: ScheduleEntryStatus;
  priority_override: boolean;
  created_by?: string;
  is_recurring: boolean;
  pieces_per_month?: number;
  estimated_duration_minutes?: number;
  note?: string;
  created_at: string;
  updated_at: string;
  odl?: ODLInSchedule;
  autoclave: AutoclaveInSchedule;
}

// Tipo per la creazione di una schedulazione
export interface ScheduleEntryCreateData {
  schedule_type: ScheduleEntryType;
  odl_id?: number;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  start_datetime: string;
  end_datetime?: string;
  status?: ScheduleEntryStatus;
  priority_override?: boolean;
  created_by?: string;
  is_recurring?: boolean;
  recurring_frequency?: string;
  pieces_per_month?: number;
  note?: string;
}

// Tipo per l'aggiornamento di una schedulazione
export interface ScheduleEntryUpdateData {
  schedule_type?: ScheduleEntryType;
  odl_id?: number;
  autoclave_id?: number;
  categoria?: string;
  sotto_categoria?: string;
  start_datetime?: string;
  end_datetime?: string;
  status?: ScheduleEntryStatus;
  priority_override?: boolean;
  created_by?: string;
  note?: string;
}

// Tipo per la creazione di schedulazioni ricorrenti
export interface RecurringScheduleCreateData {
  schedule_type: ScheduleEntryType;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  pieces_per_month: number;
  start_date: string;
  end_date: string;
  created_by?: string;
}

// Tipo per azioni dell'operatore
export interface ScheduleOperatorActionData {
  action: 'avvia' | 'posticipa' | 'completa';
  new_datetime?: string;
  note?: string;
}

// Tipo per la risposta dell'API di auto-generazione
export interface AutoScheduleResponseData {
  schedules: ScheduleEntry[];
  message: string;
  count: number;
}

// Tipo per rappresentare un evento nel calendario
export interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  resourceId: number;
  isManual: boolean;
  isPriority: boolean;
  isRecurring: boolean;
  scheduleType: ScheduleEntryType;
  status: ScheduleEntryStatus;
  scheduleData: ScheduleEntry;
}

// Tipo per rappresentare una risorsa nel calendario (autoclave)
export interface CalendarResource {
  id: number;
  title: string;
  autocode: string;
}

// Tipi per i tempi di produzione
export interface TempoProduzioneData {
  part_number?: string;
  categoria?: string;
  sotto_categoria?: string;
  tempo_medio_minuti: number;
  tempo_minimo_minuti?: number;
  tempo_massimo_minuti?: number;
  numero_osservazioni: number;
  note?: string;
}

export interface TempoProduzione extends TempoProduzioneData {
  id: number;
  ultima_osservazione: string;
  created_at: string;
  updated_at: string;
}

// Tipo per la stima dei tempi di produzione
export interface ProductionTimeEstimate {
  part_number?: string;
  categoria?: string;
  sotto_categoria?: string;
  tempo_stimato_minuti?: number;
  disponibile: boolean;
} 