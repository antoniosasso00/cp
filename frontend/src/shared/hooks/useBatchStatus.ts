import React from 'react';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Clock, CheckCircle, Package, Flame, XCircle, AlertTriangle } from 'lucide-react';

// ========== TIPI E INTERFACCE ==========

export type BatchStatus = 
  | 'draft' 
  | 'sospeso' 
  | 'confermato' 
  | 'loaded' 
  | 'cured' 
  | 'terminato' 
  | 'annullato';

export interface BatchStatusInfo {
  label: string;
  description: string;
  color: {
    bg: string;
    text: string;
    border: string;
    hex: string;
    tailwind: string;
  };
  icon: React.ComponentType<{ className?: string }>;
  permissions: {
    canView: string[];
    canTransition: string[];
  };
}

export interface BatchTransition {
  from: BatchStatus;
  to: BatchStatus;
  label: string;
  requiresConfirmation: boolean;
  permissions: string[];
}

export interface BatchStateStore {
  // State
  currentStatus: BatchStatus;
  isTransitioning: boolean;
  lastTransition: BatchTransition | null;
  error: string | null;
  
  // Store per batches multipli
  batchStates: Record<string, BatchStatus>;
  
  // Actions
  setCurrentStatus: (status: BatchStatus) => void;
  canTransition: (from: BatchStatus, to: BatchStatus, userRole?: string) => boolean;
  transition: (batchId: string, from: BatchStatus, to: BatchStatus, userRole?: string) => Promise<boolean>;
  getStatusInfo: (status: BatchStatus) => BatchStatusInfo;
  getValidTransitions: (status: BatchStatus, userRole?: string) => BatchStatus[];
  clearError: () => void;
  reset: () => void;
  
  // Batch-specific actions
  setBatchStatus: (batchId: string, status: BatchStatus) => void;
  getBatchStatus: (batchId: string) => BatchStatus | undefined;
}

// ========== STATE MACHINE CONFIGURATION ==========

export const BATCH_STATUS_CONFIG: Record<BatchStatus, BatchStatusInfo> = {
  draft: {
    label: 'Bozza',
    description: 'Batch in fase di preparazione, non ancora salvato',
    color: {
      bg: 'bg-amber-400',
      text: 'text-amber-800',
      border: 'border-amber-300',
      hex: '#fbbf24',
      tailwind: 'bg-amber-400'
    },
    icon: AlertTriangle,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: ['ADMIN', 'MANAGER']
    }
  },
  sospeso: {
    label: 'In Sospeso',
    description: 'Batch salvato, in attesa di conferma',
    color: {
      bg: 'bg-amber-500',
      text: 'text-amber-800',
      border: 'border-amber-400',
      hex: '#f59e0b',
      tailwind: 'bg-amber-500'
    },
    icon: Clock,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: ['ADMIN', 'MANAGER']
    }
  },
  confermato: {
    label: 'Confermato',
    description: 'Batch approvato, pronto per caricamento',
    color: {
      bg: 'bg-emerald-500',
      text: 'text-emerald-800',
      border: 'border-emerald-400',
      hex: '#10b981',
      tailwind: 'bg-emerald-500'
    },
    icon: CheckCircle,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: ['ADMIN', 'MANAGER', 'OPERATOR']
    }
  },
  loaded: {
    label: 'Caricato',
    description: 'Batch caricato in autoclave, pronto per cura',
    color: {
      bg: 'bg-blue-500',
      text: 'text-blue-800',
      border: 'border-blue-400',
      hex: '#3b82f6',
      tailwind: 'bg-blue-500'
    },
    icon: Package,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: ['ADMIN', 'MANAGER', 'OPERATOR']
    }
  },
  cured: {
    label: 'In Cura',
    description: 'Ciclo di cura attivo, processo in corso',
    color: {
      bg: 'bg-red-500',
      text: 'text-red-800',
      border: 'border-red-400',
      hex: '#ef4444',
      tailwind: 'bg-red-500'
    },
    icon: Flame,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: ['ADMIN', 'MANAGER', 'OPERATOR']
    }
  },
  terminato: {
    label: 'Completato',
    description: 'Batch completato con successo',
    color: {
      bg: 'bg-gray-500',
      text: 'text-gray-800',
      border: 'border-gray-400',
      hex: '#6b7280',
      tailwind: 'bg-gray-500'
    },
    icon: CheckCircle,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: []
    }
  },
  annullato: {
    label: 'Annullato',
    description: 'Batch scartato o annullato',
    color: {
      bg: 'bg-red-600',
      text: 'text-red-800',
      border: 'border-red-500',
      hex: '#dc2626',
      tailwind: 'bg-red-600'
    },
    icon: XCircle,
    permissions: {
      canView: ['ADMIN', 'MANAGER', 'OPERATOR', 'VIEWER'],
      canTransition: []
    }
  }
};

// State machine transitions - definisce le transizioni permesse
export const STATE_TRANSITIONS: Record<BatchStatus, BatchStatus[]> = {
  draft: ['sospeso', 'annullato'],
  sospeso: ['confermato', 'annullato'],
  confermato: ['loaded', 'annullato'],
  loaded: ['cured', 'annullato'],
  cured: ['terminato'],
  terminato: [],
  annullato: []
};

// Transizioni configurate con permessi specifici
export const CONFIRMABLE_TRANSITIONS: BatchTransition[] = [
  {
    from: 'draft',
    to: 'sospeso',
    label: 'Salva Batch',
    requiresConfirmation: false,
    permissions: ['ADMIN', 'MANAGER']
  },
  {
    from: 'sospeso',
    to: 'confermato',
    label: 'Conferma Batch',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER']
  },
  {
    from: 'confermato',
    to: 'loaded',
    label: 'Carica in Autoclave',
    requiresConfirmation: false,
    permissions: ['ADMIN', 'MANAGER', 'OPERATOR']
  },
  {
    from: 'loaded',
    to: 'cured',
    label: 'Avvia Cura',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER', 'OPERATOR']
  },
  {
    from: 'cured',
    to: 'terminato',
    label: 'Termina Cura',
    requiresConfirmation: false,
    permissions: ['ADMIN', 'MANAGER', 'OPERATOR']
  },
  // Transizioni di annullamento - permesse da ogni stato non finale
  {
    from: 'draft',
    to: 'annullato',
    label: 'Annulla Batch',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER']
  },
  {
    from: 'sospeso',
    to: 'annullato',
    label: 'Annulla Batch',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER']
  },
  {
    from: 'confermato',
    to: 'annullato',
    label: 'Annulla Batch',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER']
  },
  {
    from: 'loaded',
    to: 'annullato',
    label: 'Annulla Batch',
    requiresConfirmation: true,
    permissions: ['ADMIN', 'MANAGER']
  }
];

// ========== ZUSTAND STORE ==========

export const useBatchStatusStore = create<BatchStateStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentStatus: 'sospeso',
      isTransitioning: false,
      lastTransition: null,
      error: null,
      batchStates: {},

      // Actions
      setCurrentStatus: (status: BatchStatus) => {
        set({ currentStatus: status }, false, 'setCurrentStatus');
      },

      canTransition: (from: BatchStatus, to: BatchStatus, userRole: string = 'VIEWER'): boolean => {
        // Verifica se la transizione è permessa dalla state machine
        const allowedTransitions = STATE_TRANSITIONS[from];
        if (!allowedTransitions.includes(to)) {
          return false;
        }

        // Verifica permessi utente per la transizione specifica
        // Prima controlla se esiste una transizione configurata
        const transition = CONFIRMABLE_TRANSITIONS.find(t => t.from === from && t.to === to);
        if (transition) {
          return transition.permissions.includes(userRole);
        }

        // Per transizioni non configurate (come annullamento), usa i permessi dello stato di partenza
        const fromStatusInfo = BATCH_STATUS_CONFIG[from];
        return fromStatusInfo.permissions.canTransition.includes(userRole);
      },

      transition: async (batchId: string, from: BatchStatus, to: BatchStatus, userRole: string = 'VIEWER'): Promise<boolean> => {
        const { canTransition } = get();
        
        // Verifica se la transizione è possibile
        if (!canTransition(from, to, userRole)) {
          set({ 
            error: `Transizione non permessa da ${BATCH_STATUS_CONFIG[from].label} a ${BATCH_STATUS_CONFIG[to].label}` 
          }, false, 'transition/error');
          return false;
        }

        set({ isTransitioning: true, error: null }, false, 'transition/start');

        try {
          // Qui si dovrebbe chiamare l'API backend
          // Per ora simuliamo con un delay
          await new Promise(resolve => setTimeout(resolve, 500));

          // Aggiorna lo stato del batch specifico
          set((state) => ({
            batchStates: {
              ...state.batchStates,
              [batchId]: to
            },
            currentStatus: to,
            isTransitioning: false,
            lastTransition: {
              from,
              to,
              label: `${BATCH_STATUS_CONFIG[from].label} → ${BATCH_STATUS_CONFIG[to].label}`,
              requiresConfirmation: CONFIRMABLE_TRANSITIONS.some(t => t.from === from && t.to === to && t.requiresConfirmation),
              permissions: BATCH_STATUS_CONFIG[to].permissions.canTransition
            }
          }), false, 'transition/success');

          return true;
        } catch (error) {
          set({ 
            isTransitioning: false, 
            error: error instanceof Error ? error.message : 'Errore durante la transizione' 
          }, false, 'transition/error');
          return false;
        }
      },

      getStatusInfo: (status: BatchStatus): BatchStatusInfo => {
        return BATCH_STATUS_CONFIG[status];
      },

      getValidTransitions: (status: BatchStatus, userRole: string = 'VIEWER'): BatchStatus[] => {
        const { canTransition } = get();
        const allowedTransitions = STATE_TRANSITIONS[status];
        return allowedTransitions.filter(targetStatus => 
          canTransition(status, targetStatus, userRole)
        );
      },

      setBatchStatus: (batchId: string, status: BatchStatus) => {
        set((state) => ({
          batchStates: {
            ...state.batchStates,
            [batchId]: status
          }
        }), false, 'setBatchStatus');
      },

      getBatchStatus: (batchId: string): BatchStatus | undefined => {
        return get().batchStates[batchId];
      },

      clearError: () => {
        set({ error: null }, false, 'clearError');
      },

      reset: () => {
        set({
          currentStatus: 'sospeso',
          isTransitioning: false,
          lastTransition: null,
          error: null,
          batchStates: {}
        }, false, 'reset');
      }
    }),
    {
      name: 'batch-status-store'
    }
  )
);

// ========== HOOK PRINCIPALE ==========

export const useBatchStatus = (batchId?: string, initialStatus?: BatchStatus) => {
  const store = useBatchStatusStore();
  
  // Inizializza lo status del batch se fornito
  React.useEffect(() => {
    if (batchId && initialStatus && !store.getBatchStatus(batchId)) {
      store.setBatchStatus(batchId, initialStatus);
    }
  }, [batchId, initialStatus, store]);

  // Funzioni di utilità specifiche per il batch
  const getBatchSpecificStatus = () => {
    if (batchId) {
      return store.getBatchStatus(batchId) || store.currentStatus;
    }
    return store.currentStatus;
  };

  const transitionBatch = async (to: BatchStatus, userRole?: string) => {
    if (!batchId) {
      console.warn('useBatchStatus: batchId non fornito per la transizione');
      return false;
    }
    
    const currentStatus = getBatchSpecificStatus();
    return store.transition(batchId, currentStatus, to, userRole);
  };

  return {
    // State
    state: getBatchSpecificStatus(),
    isTransitioning: store.isTransitioning,
    error: store.error,
    lastTransition: store.lastTransition,
    
    // Computed
    statusInfo: store.getStatusInfo(getBatchSpecificStatus()),
    validTransitions: store.getValidTransitions(getBatchSpecificStatus()),
    
    // Actions
    canTransition: (to: BatchStatus, userRole?: string) => 
      store.canTransition(getBatchSpecificStatus(), to, userRole),
    transition: transitionBatch,
    label: () => store.getStatusInfo(getBatchSpecificStatus()).label,
    color: () => store.getStatusInfo(getBatchSpecificStatus()).color,
    
    // Utilities
    clearError: store.clearError,
    reset: store.reset
  };
};

// ========== UTILITY FUNCTIONS ==========

/**
 * Verifica se una transizione è valida secondo la state machine
 */
export const isValidTransition = (from: BatchStatus, to: BatchStatus): boolean => {
  return STATE_TRANSITIONS[from]?.includes(to) || false;
};

/**
 * Ottiene tutte le transizioni possibili da uno stato
 */
export const getAvailableTransitions = (from: BatchStatus): BatchStatus[] => {
  return STATE_TRANSITIONS[from] || [];
};

/**
 * Verifica se uno stato è finale (non ha transizioni in uscita)
 */
export const isFinalState = (status: BatchStatus): boolean => {
  return STATE_TRANSITIONS[status]?.length === 0;
};

/**
 * Ottiene il colore hex per uno stato
 */
export const getStatusColor = (status: BatchStatus): string => {
  return BATCH_STATUS_CONFIG[status]?.color.hex || '#6b7280';
};

/**
 * Ottiene l'etichetta per uno stato
 */
export const getStatusLabel = (status: BatchStatus): string => {
  return BATCH_STATUS_CONFIG[status]?.label || status;
};

export default useBatchStatus; 