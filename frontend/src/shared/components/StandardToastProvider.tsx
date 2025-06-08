/**
 * Provider standardizzato per tutte le notifiche dell'app
 * Sostituisce ApiErrorToast e centralizza la gestione
 */

'use client'

import { useEffect } from 'react'
import { showApiError } from '@/shared/services/toast-service'

interface ApiError {
  message: string
  status: number
  url: string
  endpoint?: string
}

/**
 * Provider che gestisce automaticamente gli errori API
 * e altri eventi di notifica globali
 */
export default function StandardToastProvider() {
  useEffect(() => {
    // Gestione errori API globali
    const handleApiError = (event: CustomEvent<ApiError>) => {
      const { message, status, url, endpoint } = event.detail
      
      showApiError({
        status,
        message,
        endpoint: endpoint || new URL(url).pathname,
        operation: 'API Request'
      })
    }

    // Gestione notifiche di sistema
    const handleSystemNotification = (event: CustomEvent<{
      type: 'success' | 'error' | 'warning' | 'info'
      title: string
      message?: string
    }>) => {
      const { type, title, message } = event.detail
      
      // Usa il servizio standardizzato
      import('@/shared/services/toast-service').then(({ toastService }) => {
        toastService.show({
          type,
          title,
          message,
          context: 'system-notification'
        })
      })
    }

    // Registra i listener
    window.addEventListener('api-error', handleApiError as EventListener)
    window.addEventListener('system-notification', handleSystemNotification as EventListener)

    return () => {
      window.removeEventListener('api-error', handleApiError as EventListener)
      window.removeEventListener('system-notification', handleSystemNotification as EventListener)
    }
  }, [])

  // Questo componente non renderizza nulla, gestisce solo gli eventi
  return null
}

/**
 * Utility per emettere notifiche di sistema da qualsiasi parte dell'app
 */
export function emitSystemNotification(
  type: 'success' | 'error' | 'warning' | 'info',
  title: string,
  message?: string
) {
  const event = new CustomEvent('system-notification', {
    detail: { type, title, message }
  })
  window.dispatchEvent(event)
}

/**
 * Hook per emettere notifiche di sistema
 */
export function useSystemNotifications() {
  return {
    success: (title: string, message?: string) => emitSystemNotification('success', title, message),
    error: (title: string, message?: string) => emitSystemNotification('error', title, message),
    warning: (title: string, message?: string) => emitSystemNotification('warning', title, message),
    info: (title: string, message?: string) => emitSystemNotification('info', title, message)
  }
} 