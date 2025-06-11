/**
 * Costanti centralizzate per l'applicazione CarbonPilot
 * 
 * Questo file contiene tutte le costanti utilizzate nell'applicazione per:
 * - Stati ODL e relative configurazioni
 * - Stati Batch e colori
 * - Ruoli utente
 * - Stati Schedule
 * - Fasi di produzione
 * - Stati Autoclave
 * - Configurazioni colori per badge
 */

import { 
  Settings, 
  Package, 
  Clock, 
  PlayCircle, 
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

// ================================
// STATI ODL
// ================================

/** Array degli stati ODL disponibili */
export const ODL_STATUSES = [
  'Preparazione',
  'Laminazione', 
  'In Coda',
  'Attesa Cura',
  'Cura',
  'Finito'
] as const;

/** Etichette user-friendly per gli stati ODL */
export const ODL_STATUS_LABELS = {
  'Preparazione': 'Preparazione',
  'Laminazione': 'Laminazione',
  'In Coda': 'In Coda',
  'Attesa Cura': 'Attesa Cura',
  'Cura': 'Cura',
  'Finito': 'Finito'
} as const;

/** Descrizioni dettagliate per gli stati ODL */
export const ODL_STATUS_DESCRIPTIONS = {
  'Preparazione': 'ODL in fase di preparazione iniziale',
  'Laminazione': 'ODL in fase di laminazione',
  'In Coda': 'ODL in coda per la cura',
  'Attesa Cura': 'ODL pronto per il caricamento in autoclave',
  'Cura': 'ODL in fase di cura nell\'autoclave',
  'Finito': 'ODL completato con successo'
} as const;

/** Colori per i badge degli stati ODL */
export const ODL_STATUS_COLORS = {
  'Preparazione': 'bg-gray-100 text-gray-800 border-gray-300',
  'Laminazione': 'bg-blue-100 text-blue-800 border-blue-300',
  'In Coda': 'bg-purple-100 text-purple-800 border-purple-300',
  'Attesa Cura': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'Cura': 'bg-orange-100 text-orange-800 border-orange-300',
  'Finito': 'bg-green-100 text-green-800 border-green-300'
} as const;

/** Icone per gli stati ODL */
export const ODL_STATUS_ICONS = {
  'Preparazione': Settings,
  'Laminazione': Package,
  'In Coda': Clock,
  'Attesa Cura': Clock,
  'Cura': PlayCircle,
  'Finito': CheckCircle
} as const;

/** Transizioni consentite per gli stati ODL */
export const ODL_STATUS_TRANSITIONS = {
  'Preparazione': ['Laminazione'],
  'Laminazione': ['In Coda'],
  'In Coda': ['Attesa Cura'],
  'Attesa Cura': ['Cura'],
  'Cura': ['Finito'],
  'Finito': []
} as const;

// ================================
// STATI BATCH NESTING
// ================================

/** Array degli stati Batch disponibili - FLUSSO MODERNO */
export const BATCH_STATUSES = [
  'draft',
  'sospeso',
  'in_cura', 
  'terminato'
] as const;

/** Etichette user-friendly per gli stati Batch */
export const BATCH_STATUS_LABELS = {
  'draft': 'Bozza',
  'sospeso': 'Sospeso',
  'in_cura': 'In Cura',
  'terminato': 'Terminato'
} as const;

/** Descrizioni dettagliate per gli stati Batch */
export const BATCH_STATUS_DESCRIPTIONS = {
  'draft': 'Risultati generati, non confermati',
  'sospeso': 'Confermato dall\'operatore, pronto per caricamento',
  'in_cura': 'Autoclave caricata, cura in corso, timing attivo',
  'terminato': 'Cura completata, workflow chiuso'
} as const;

/** Colori per i badge degli stati Batch */
export const BATCH_STATUS_COLORS = {
  'draft': 'bg-gray-100 text-gray-800 border-gray-300',
  'sospeso': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'in_cura': 'bg-red-100 text-red-800 border-red-300',
  'terminato': 'bg-green-100 text-green-800 border-green-300'
} as const;

/** Icone per gli stati Batch */
export const BATCH_STATUS_ICONS = {
  'draft': Clock,
  'sospeso': Clock,
  'in_cura': PlayCircle,
  'terminato': CheckCircle
} as const;

// ================================
// STATI SCHEDULE
// ================================

/** Array degli stati Schedule disponibili */
export const SCHEDULE_STATUSES = [
  'scheduled',
  'manual',
  'previsionale',
  'in_attesa',
  'in_corso', 
  'done',
  'posticipato'
] as const;

/** Etichette user-friendly per gli stati Schedule */
export const SCHEDULE_STATUS_LABELS = {
  'scheduled': 'Schedulato',
  'manual': 'Manuale',
  'previsionale': 'Previsionale',
  'in_attesa': 'In Attesa',
  'in_corso': 'In Corso',
  'done': 'Completato',
  'posticipato': 'Posticipato'
} as const;

/** Colori per i badge degli stati Schedule */
export const SCHEDULE_STATUS_COLORS = {
  'scheduled': 'bg-blue-100 text-blue-800 border-blue-300',
  'manual': 'bg-purple-100 text-purple-800 border-purple-300',
  'previsionale': 'bg-cyan-100 text-cyan-800 border-cyan-300',
  'in_attesa': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'in_corso': 'bg-orange-100 text-orange-800 border-orange-300',
  'done': 'bg-green-100 text-green-800 border-green-300',
  'posticipato': 'bg-gray-100 text-gray-800 border-gray-300'
} as const;

// ================================
// RUOLI UTENTE
// ================================

/** Array dei ruoli utente disponibili */
export const USER_ROLES = [
  'ADMIN',
  'Management', 
  'Clean Room',
  'Curing'
] as const;

/** Etichette user-friendly per i ruoli */
export const USER_ROLE_LABELS = {
  'ADMIN': 'Amministratore',
  'Management': 'Management',
  'Clean Room': 'Clean Room',
  'Curing': 'Curing'
} as const;

/** Descrizioni dettagliate per i ruoli */
export const USER_ROLE_DESCRIPTIONS = {
  'ADMIN': 'Accesso completo al sistema',
  'Management': 'Gestione e supervisione',
  'Clean Room': 'Operazioni in camera bianca e laminazione',
  'Curing': 'Gestione autoclave e processi di cura'
} as const;

/** Colori per i badge dei ruoli */
export const USER_ROLE_COLORS = {
  'ADMIN': 'bg-red-100 text-red-800 border-red-300',
  'Management': 'bg-purple-100 text-purple-800 border-purple-300',
  'Clean Room': 'bg-blue-100 text-blue-800 border-blue-300',
  'Curing': 'bg-orange-100 text-orange-800 border-orange-300'
} as const;

// ================================
// FASI DI PRODUZIONE
// ================================

/** Array delle fasi di produzione disponibili */
export const PRODUCTION_PHASES = [
  'laminazione',
  'attesa_cura',
  'cura'
] as const;

/** Etichette user-friendly per le fasi */
export const PRODUCTION_PHASE_LABELS = {
  'laminazione': 'Laminazione',
  'attesa_cura': 'Attesa Cura',
  'cura': 'Cura'
} as const;

/** Descrizioni dettagliate per le fasi */
export const PRODUCTION_PHASE_DESCRIPTIONS = {
  'laminazione': 'Fase di laminazione del componente',
  'attesa_cura': 'Attesa per l\'inizio del processo di cura',
  'cura': 'Processo di cura in autoclave'
} as const;

// ================================
// STATI AUTOCLAVE
// ================================

/** Array degli stati Autoclave disponibili */
export const AUTOCLAVE_STATUSES = [
  'DISPONIBILE',
  'IN_USO',
  'GUASTO',
  'MANUTENZIONE',
  'SPENTA'
] as const;

/** Etichette user-friendly per gli stati Autoclave */
export const AUTOCLAVE_STATUS_LABELS = {
  'DISPONIBILE': 'Disponibile',
  'IN_USO': 'In Uso',
  'GUASTO': 'Guasto',
  'MANUTENZIONE': 'Manutenzione',
  'SPENTA': 'Spenta'
} as const;

/** Colori per i badge degli stati Autoclave */
export const AUTOCLAVE_STATUS_COLORS = {
  'DISPONIBILE': 'bg-green-100 text-green-800 border-green-300',
  'IN_USO': 'bg-orange-100 text-orange-800 border-orange-300',
  'GUASTO': 'bg-red-100 text-red-800 border-red-300',
  'MANUTENZIONE': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'SPENTA': 'bg-gray-100 text-gray-800 border-gray-300'
} as const;

/** Icone per gli stati Autoclave */
export const AUTOCLAVE_STATUS_ICONS = {
  'DISPONIBILE': CheckCircle,
  'IN_USO': PlayCircle,
  'GUASTO': AlertTriangle,
  'MANUTENZIONE': Settings,
  'SPENTA': Clock
} as const;

// ================================
// TIPI DI SCHEDULE
// ================================

/** Array dei tipi di Schedule disponibili */
export const SCHEDULE_TYPES = [
  'odl_specifico',
  'categoria',
  'sotto_categoria',
  'ricorrente'
] as const;

/** Etichette user-friendly per i tipi di Schedule */
export const SCHEDULE_TYPE_LABELS = {
  'odl_specifico': 'ODL Specifico',
  'categoria': 'Categoria',
  'sotto_categoria': 'Sotto-categoria',
  'ricorrente': 'Ricorrente'
} as const;

// ================================
// CONFIGURAZIONI COLORI GENERALI
// ================================

/** Colori per stati generici (successo, warning, errore, info) */
export const GENERIC_STATUS_COLORS = {
  'success': 'bg-green-100 text-green-800 border-green-300',
  'warning': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'error': 'bg-red-100 text-red-800 border-red-300',
  'info': 'bg-blue-100 text-blue-800 border-blue-300',
  'neutral': 'bg-gray-100 text-gray-800 border-gray-300'
} as const;

// ================================
// CATEGORIE E SOTTO-CATEGORIE
// ================================

/** Categorie di prodotti comuni */
export const PRODUCT_CATEGORIES = [
  'Valvole',
  'Componenti',
  'Ricambi',
  'Accessori'
] as const;

/** Sotto-categorie per categoria Valvole */
export const VALVE_SUBCATEGORIES = [
  'Butterfly',
  'Ball',
  'Gate',
  'Check',
  'Control'
] as const;

// ================================
// CONFIGURAZIONI DI SISTEMA
// ================================

/** Livelli di log del sistema */
export const LOG_LEVELS = [
  'INFO',
  'WARNING', 
  'ERROR',
  'CRITICAL'
] as const;

/** Colori per i livelli di log */
export const LOG_LEVEL_COLORS = {
  'INFO': 'bg-blue-100 text-blue-800 border-blue-300',
  'WARNING': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'ERROR': 'bg-red-100 text-red-800 border-red-300',
  'CRITICAL': 'bg-red-200 text-red-900 border-red-400'
} as const;

// ================================
// CONFIGURAZIONI FUNZIONALI
// ================================

/** Azioni possibili per lo scheduler */
export const SCHEDULE_ACTIONS = [
  'avvia',
  'posticipa', 
  'completa'
] as const;

/** Etichette per le azioni scheduler */
export const SCHEDULE_ACTION_LABELS = {
  'avvia': 'Avvia',
  'posticipa': 'Posticipa',
  'completa': 'Completa'
} as const;

/** Frequenze per schedulazioni ricorrenti */
export const RECURRING_FREQUENCIES = [
  'daily',
  'weekly',
  'monthly',
  'quarterly'
] as const;

/** Etichette per le frequenze ricorrenti */
export const RECURRING_FREQUENCY_LABELS = {
  'daily': 'Giornaliero',
  'weekly': 'Settimanale', 
  'monthly': 'Mensile',
  'quarterly': 'Trimestrale'
} as const;

// ================================
// UTILITY FUNCTIONS
// ================================

/**
 * Ottiene il colore di un badge basato sul tipo e valore
 */
export const getBadgeColor = (type: string, value: string): string => {
  switch (type) {
    case 'odl_status':
      return ODL_STATUS_COLORS[value as keyof typeof ODL_STATUS_COLORS] || GENERIC_STATUS_COLORS.neutral;
    case 'batch_status':
      return BATCH_STATUS_COLORS[value as keyof typeof BATCH_STATUS_COLORS] || GENERIC_STATUS_COLORS.neutral;
    case 'schedule_status':
      return SCHEDULE_STATUS_COLORS[value as keyof typeof SCHEDULE_STATUS_COLORS] || GENERIC_STATUS_COLORS.neutral;
    case 'user_role':
      return USER_ROLE_COLORS[value as keyof typeof USER_ROLE_COLORS] || GENERIC_STATUS_COLORS.neutral;
    case 'autoclave_status':
      return AUTOCLAVE_STATUS_COLORS[value as keyof typeof AUTOCLAVE_STATUS_COLORS] || GENERIC_STATUS_COLORS.neutral;
    case 'log_level':
      return LOG_LEVEL_COLORS[value as keyof typeof LOG_LEVEL_COLORS] || GENERIC_STATUS_COLORS.neutral;
    default:
      return GENERIC_STATUS_COLORS.neutral;
  }
};

/**
 * Ottiene l'etichetta di un valore basato sul tipo
 */
export const getLabel = (type: string, value: string): string => {
  switch (type) {
    case 'odl_status':
      return ODL_STATUS_LABELS[value as keyof typeof ODL_STATUS_LABELS] || value;
    case 'batch_status':
      return BATCH_STATUS_LABELS[value as keyof typeof BATCH_STATUS_LABELS] || value;
    case 'schedule_status':
      return SCHEDULE_STATUS_LABELS[value as keyof typeof SCHEDULE_STATUS_LABELS] || value;
    case 'user_role':
      return USER_ROLE_LABELS[value as keyof typeof USER_ROLE_LABELS] || value;
    case 'autoclave_status':
      return AUTOCLAVE_STATUS_LABELS[value as keyof typeof AUTOCLAVE_STATUS_LABELS] || value;
    case 'production_phase':
      return PRODUCTION_PHASE_LABELS[value as keyof typeof PRODUCTION_PHASE_LABELS] || value;
    case 'schedule_type':
      return SCHEDULE_TYPE_LABELS[value as keyof typeof SCHEDULE_TYPE_LABELS] || value;
    case 'schedule_action':
      return SCHEDULE_ACTION_LABELS[value as keyof typeof SCHEDULE_ACTION_LABELS] || value;
    case 'recurring_frequency':
      return RECURRING_FREQUENCY_LABELS[value as keyof typeof RECURRING_FREQUENCY_LABELS] || value;
    default:
      return value;
  }
};

/**
 * Verifica se una transizione di stato è consentita
 */
export const isTransitionAllowed = (
  type: 'odl',
  currentStatus: string,
  newStatus: string
): boolean => {
  if (type === 'odl') {
    const transitions = ODL_STATUS_TRANSITIONS[currentStatus as keyof typeof ODL_STATUS_TRANSITIONS];
    return transitions ? (transitions as readonly string[]).includes(newStatus) : false;
  }
  return false;
}; 