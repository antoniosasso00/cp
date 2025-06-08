'use client'

import { useEffect } from 'react'
import { showApiError } from '@/shared/services/toast-service'

interface ApiErrorDetail {
  message: string
  status: number
  url: string
  endpoint?: string
}

export function useApiErrorHandler() {
  useEffect(() => {
    const handleApiError = (event: CustomEvent<ApiErrorDetail>) => {
      const { message, status, endpoint, url } = event.detail
      
      // Usa il servizio standardizzato per gestire errori API
      showApiError({
        status,
        message,
        endpoint: endpoint || new URL(url).pathname,
        operation: 'API Request'
      })
    }

    // Ascolta gli eventi di errore API
    window.addEventListener('api-error', handleApiError as EventListener)

    return () => {
      window.removeEventListener('api-error', handleApiError as EventListener)
    }
  }, [])
} 