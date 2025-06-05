/**
 * Tipi centralizzati per l'applicazione CarbonPilot
 * 
 * Questo file contiene tutti i tipi utilizzati nell'applicazione per:
 * - Stati e configurazioni ODL
 * - Stati e configurazioni Batch
 * - Ruoli utente
 * - Stati Schedule e relative configurazioni
 * - Fasi di produzione
 * - Stati Autoclave
 * - Configurazioni di sistema
 */

import type { 
  ODL_STATUSES,
  BATCH_STATUSES,
  SCHEDULE_STATUSES,
  USER_ROLES,
  PRODUCTION_PHASES,
  AUTOCLAVE_STATUSES,
  SCHEDULE_TYPES,
  LOG_LEVELS,
  SCHEDULE_ACTIONS,
  RECURRING_FREQUENCIES,
  PRODUCT_CATEGORIES,
  VALVE_SUBCATEGORIES
} from '@/shared/lib/constants';

// ================================
// TIPI PRINCIPALI
// ================================

/** Tipo per gli stati ODL */
export type ODLStatus = typeof ODL_STATUSES[number];

/** Tipo per gli stati Batch Nesting */
export type BatchStatus = typeof BATCH_STATUSES[number];

/** Tipo per gli stati Schedule */
export type ScheduleStatus = typeof SCHEDULE_STATUSES[number];

/** Tipo per i ruoli utente */
export type UserRole = typeof USER_ROLES[number];

/** Tipo per le fasi di produzione */
export type ProductionPhase = typeof PRODUCTION_PHASES[number];

/** Tipo per gli stati Autoclave */
export type AutoclaveStatus = typeof AUTOCLAVE_STATUSES[number];

/** Tipo per i tipi di Schedule */
export type ScheduleType = typeof SCHEDULE_TYPES[number];

/** Tipo per i livelli di log */
export type LogLevel = typeof LOG_LEVELS[number];

/** Tipo per le azioni del scheduler */
export type ScheduleAction = typeof SCHEDULE_ACTIONS[number];

/** Tipo per le frequenze ricorrenti */
export type RecurringFrequency = typeof RECURRING_FREQUENCIES[number];

/** Tipo per le categorie di prodotti */
export type ProductCategory = typeof PRODUCT_CATEGORIES[number];

/** Tipo per le sotto-categorie valvole */
export type ValveSubcategory = typeof VALVE_SUBCATEGORIES[number];

// ================================
// TIPI COMPOSITI
// ================================

/** Configurazione completa per stato ODL */
export interface ODLStatusConfig {
  status: ODLStatus;
  label: string;
  description: string;
  color: string;
  icon: any;
  canTransitionTo: ODLStatus[];
}

/** Configurazione completa per stato Batch */
export interface BatchStatusConfig {
  status: BatchStatus;
  label: string;
  description: string;
  color: string;
  icon: any;
}

/** Configurazione completa per stato Schedule */
export interface ScheduleStatusConfig {
  status: ScheduleStatus;
  label: string;
  color: string;
}

/** Configurazione completa per ruolo utente */
export interface UserRoleConfig {
  role: UserRole;
  label: string;
  description: string;
  color: string;
}

/** Configurazione completa per stato Autoclave */
export interface AutoclaveStatusConfig {
  status: AutoclaveStatus;
  label: string;
  color: string;
  icon: any;
}

// ================================
// INTERFACCE CORE BUSINESS
// ================================

/** Informazioni base di un ODL */
export interface ODLInfo {
  id: number;
  status: ODLStatus;
  priorita: number;
  note?: string;
  parte: {
    part_number: string;
    descrizione_breve: string;
  };
  tool: {
    part_number_tool: string;
    descrizione?: string;
  };
}

/** Informazioni base di un Batch */
export interface BatchInfo {
  id: string;
  nome?: string;
  stato: BatchStatus;
  autoclave_id: number;
  numero_nesting: number;
  peso_totale_kg: number;
  created_at: string;
  updated_at: string;
}

/** Informazioni base di una Schedule */
export interface ScheduleInfo {
  id: number;
  schedule_type: ScheduleType;
  odl_id?: number;
  autoclave_id: number;
  categoria?: string;
  sotto_categoria?: string;
  start_datetime: string;
  end_datetime?: string;
  status: ScheduleStatus;
  priority_override: boolean;
  created_by?: string;
  is_recurring: boolean;
  pieces_per_month?: number;
  estimated_duration_minutes?: number;
  note?: string;
}

/** Informazioni base di un'Autoclave */
export interface AutoclaveInfo {
  id: number;
  nome: string;
  codice: string;
  lunghezza: number;
  larghezza_piano: number;
  num_linee_vuoto: number;
  stato: AutoclaveStatus;
  temperatura_max: number;
  pressione_max: number;
  max_load_kg?: number;
  produttore?: string;
  anno_produzione?: number;
  note?: string;
}

/** Informazioni base di un Ciclo di Cura */
export interface CicloCuraInfo {
  id: number;
  nome: string;
  temperatura_stasi1: number;
  pressione_stasi1: number;
  durata_stasi1: number;
  attiva_stasi2: boolean;
  temperatura_stasi2?: number;
  pressione_stasi2?: number;
  durata_stasi2?: number;
}

/** Informazioni base di una Parte */
export interface ParteInfo {
  id: number;
  part_number: string;
  descrizione_breve: string;
  num_valvole_richieste: number;
  note_produzione?: string;
  ciclo_cura?: CicloCuraInfo;
}

/** Informazioni base di un Tool */
export interface ToolInfo {
  id: number;
  part_number_tool: string;
  descrizione?: string;
  lunghezza_piano: number;
  larghezza_piano: number;
  peso?: number;
  materiale?: string;
  disponibile: boolean;
  area?: number;
}

// ================================
// TIPI PER TEMPO E FASI
// ================================

/** Informazioni di tempo per una fase */
export interface TempoFaseInfo {
  id: number;
  odl_id: number;
  fase: ProductionPhase;
  inizio_fase: string;
  fine_fase?: string;
  durata_minuti?: number;
  note?: string;
}

/** Previsione tempo per una fase */
export interface PrevisioneTempo {
  fase: ProductionPhase;
  media_minuti: number;
  numero_osservazioni: number;
}

/** Statistiche tempo per fase */
export interface TempoFaseStatistiche {
  fase: ProductionPhase;
  media_minuti: number;
  numero_osservazioni: number;
  tempo_minimo_minuti?: number;
  tempo_massimo_minuti?: number;
}

// ================================
// TIPI PER LOG E AUDIT
// ================================

/** Informazioni di log del sistema */
export interface SystemLogInfo {
  id: number;
  timestamp: string;
  level: LogLevel;
  event_type: string;
  user_role: UserRole;
  user_id?: string;
  action: string;
  entity_type?: string;
  entity_id?: number;
  details?: string;
  old_value?: string;
  new_value?: string;
  ip_address?: string;
}

/** Filtri per i log del sistema */
export interface SystemLogFilters {
  event_type?: string;
  user_role?: UserRole;
  level?: LogLevel;
  entity_type?: string;
  entity_id?: number;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

/** Statistiche dei log del sistema */
export interface SystemLogStats {
  total_logs: number;
  logs_by_type: Record<string, number>;
  logs_by_role: Record<string, number>;
  logs_by_level: Record<string, number>;
  recent_errors: SystemLogInfo[];
}

// ================================
// TIPI PER API E RESPONSES
// ================================

/** Parametri di paginazione */
export interface PaginationParams {
  limit?: number;
  offset?: number;
  page?: number;
}

/** Risposta con paginazione */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/** Filtri generici per liste */
export interface BaseFilters extends PaginationParams {
  search?: string;
  status?: string;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
}

/** Parametri di ordinamento */
export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/** Risposta di creazione/aggiornamento */
export interface MutationResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
}

// ================================
// TIPI PER UI E COMPONENTI
// ================================

/** Configurazione per un badge */
export interface BadgeConfig {
  text: string;
  color: string;
  icon?: any;
  variant?: 'default' | 'outline' | 'secondary';
}

/** Configurazione per una tabella */
export interface TableColumn<T = any> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  className?: string;
}

/** Stato di caricamento per componenti */
export interface LoadingState {
  loading: boolean;
  error?: string;
  lastUpdated?: string;
}

/** Configurazione per modali */
export interface ModalState<T = any> {
  isOpen: boolean;
  mode: 'create' | 'edit' | 'view' | 'delete';
  data?: T;
  title?: string;
}

/** Configurazione per form */
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'textarea' | 'checkbox' | 'date' | 'datetime';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  validation?: any;
  disabled?: boolean;
  className?: string;
}

// ================================
// TIPI PER NESTING E PRODUZIONE
// ================================

/** Parametri per il nesting */
export interface NestingParams {
  autoclave_id: number;
  odl_ids: number[];
  due_piani?: boolean;
  margine_sicurezza?: number;
  peso_massimo?: number;
}

/** Risultato del nesting */
export interface NestingResult {
  piano1: Array<{
    tool_id: number;
    x: number;
    y: number;
    rotazione: number;
  }>;
  piano2?: Array<{
    tool_id: number;
    x: number;
    y: number;
    rotazione: number;
  }>;
  area_utilizzata: number;
  peso_totale: number;
  valvole_totali: number;
  efficienza: number;
}

/** Configurazione per visualizzazione nesting */
export interface NestingVisualization {
  autoclave: AutoclaveInfo;
  tools: ToolInfo[];
  odls: ODLInfo[];
  result: NestingResult;
  scale?: number;
  showLabels?: boolean;
  showGrid?: boolean;
}

// ================================
// TIPI PER REPORT E ANALYTICS
// ================================

/** Tipo di report */
export type ReportType = 'produzione' | 'qualita' | 'tempi' | 'completo';

/** Periodo di report */
export type ReportPeriod = 'giorno' | 'settimana' | 'mese' | 'trimestre' | 'anno';

/** Sezioni da includere nel report */
export type ReportSection = 'odl' | 'tempi' | 'header' | 'nesting' | 'autoclavi';

/** Configurazione per generazione report */
export interface ReportConfig {
  type: ReportType;
  period: ReportPeriod;
  start_date?: string;
  end_date?: string;
  sections: ReportSection[];
  filters?: {
    odl_status?: ODLStatus[];
    autoclave_ids?: number[];
    user_role?: UserRole;
  };
}

/** Informazioni su file di report */
export interface ReportFileInfo {
  id: number;
  filename: string;
  file_path: string;
  report_type: ReportType;
  period_start?: string;
  period_end?: string;
  file_size_bytes?: number;
  created_at: string;
  updated_at: string;
}

// ================================
// UTILITY TYPES
// ================================

/** Rende tutti i campi opzionali */
export type Partial<T> = {
  [P in keyof T]?: T[P];
};

/** Rende tutti i campi richiesti */
export type Required<T> = {
  [P in keyof T]-?: T[P];
};

/** Seleziona solo alcuni campi */
export type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

/** Omette alcuni campi */
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

/** Tipo per chiavi di un oggetto */
export type KeyOf<T> = keyof T;

/** Tipo per valori di un oggetto */
export type ValueOf<T> = T[keyof T];

/** Tipo condizionale */
export type ConditionalType<T, U, Y, N> = T extends U ? Y : N; 