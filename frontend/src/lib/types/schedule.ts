// Definizione dei tipi di schedule per il frontend

// Enum per gli stati di una schedulazione
export enum ScheduleEntryStatus {
  SCHEDULED = "scheduled",  // Schedulato automaticamente
  MANUAL = "manual",        // Schedulato manualmente
  DONE = "done",            // Completato
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
  odl_id: number;
  autoclave_id: number;
  start_datetime: string;
  end_datetime: string;
  status: ScheduleEntryStatus;
  priority_override: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  odl: ODLInSchedule;
  autoclave: AutoclaveInSchedule;
}

// Tipo per la creazione di una schedulazione
export interface ScheduleEntryCreateData {
  odl_id: number;
  autoclave_id: number;
  start_datetime: string;
  end_datetime: string;
  status?: ScheduleEntryStatus;
  priority_override?: boolean;
  created_by?: string;
}

// Tipo per l'aggiornamento di una schedulazione
export interface ScheduleEntryUpdateData {
  odl_id?: number;
  autoclave_id?: number;
  start_datetime?: string;
  end_datetime?: string;
  status?: ScheduleEntryStatus;
  priority_override?: boolean;
  created_by?: string;
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
  scheduleData: ScheduleEntry;
}

// Tipo per rappresentare una risorsa nel calendario (autoclave)
export interface CalendarResource {
  id: number;
  title: string;
  autocode: string;
} 