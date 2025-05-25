'use client'

import { useEffect } from 'react'
import { useToast } from '@/components/ui/use-toast'

interface ApiErrorDetail {
  message: string
  status: number
  url: string
  endpoint?: string
}

export function useApiErrorHandler() {
  const { toast } = useToast()

  useEffect(() => {
    const handleApiError = (event: CustomEvent<ApiErrorDetail>) => {
      const { message, status, endpoint } = event.detail
      
      // Non mostrare toast per errori già gestiti localmente
      if (status === 0) {
        // Errore di rete
        toast({
          variant: 'destructive',
          title: 'Errore di Connessione',
          description: message,
          duration: 5000,
        })
      } else if (status === 422) {
        // Errore di validazione - spesso gestito localmente
        console.warn('Errore di validazione API:', message)
      } else if (status === 404) {
        toast({
          variant: 'destructive',
          title: 'Risorsa Non Trovata',
          description: `Endpoint non disponibile: ${endpoint || 'sconosciuto'}`,
          duration: 4000,
        })
      } else if (status >= 500) {
        toast({
          variant: 'destructive',
          title: 'Errore del Server',
          description: 'Si è verificato un errore interno. Riprova più tardi.',
          duration: 6000,
        })
      } else {
        toast({
          variant: 'destructive',
          title: 'Errore API',
          description: message,
          duration: 4000,
        })
      }
    }

    // Ascolta gli eventi di errore API
    window.addEventListener('api-error', handleApiError as EventListener)

    return () => {
      window.removeEventListener('api-error', handleApiError as EventListener)
    }
  }, [toast])
} 