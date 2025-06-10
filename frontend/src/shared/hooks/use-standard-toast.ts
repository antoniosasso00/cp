/**
 * Hook compatibile con useToast che usa il servizio standardizzato
 * Permette di sostituire facilmente le implementazioni esistenti
 */

import { 
  toastService, 
  showSuccess, 
  showError, 
  showWarning, 
  showInfo,
  showOperationResult,
  showApiError,
  showStatusChange,
  type OperationToastOptions
} from '@/shared/services/toast-service'

interface ToastProps {
  title?: string
  description?: string
  variant?: 'default' | 'destructive' | 'success' | 'warning' | 'info'
  duration?: number
}

/**
 * Hook che fornisce un'interfaccia compatibile con useToast
 * ma usa il servizio standardizzato sotto il cofano
 */
export function useStandardToast() {
  const toast = (props: ToastProps) => {
    const { title = '', description, variant = 'default', duration } = props
    
    // Mappa le varianti ai tipi del servizio
    const typeMapping = {
      'default': 'info' as const,
      'destructive': 'error' as const,
      'success': 'success' as const,
      'warning': 'warning' as const,
      'info': 'info' as const
    }
    
    toastService.show({
      type: typeMapping[variant],
      title,
      message: description,
      duration
    })
  }

  return {
    toast,
    // Metodi di convenienza
    success: showSuccess,
    error: showError,
    warning: showWarning,
    info: showInfo,
    // Template methods
    operation: showOperationResult,
    apiError: showApiError,
    statusChange: showStatusChange
  }
}

/**
 * Hook semplificato per operazioni CRUD comuni
 */
export function useCrudToast() {
  return {
    success: (operation: string, entity?: string, entityId?: string | number, details?: string) => {
      showOperationResult('success', { operation, entity, entityId, details })
    },
    error: (operation: string, entity?: string, entityId?: string | number, details?: string) => {
      showOperationResult('error', { operation, entity, entityId, details })
    },
    statusChange: showStatusChange
  }
}

// Removed unused export useQualityToast 