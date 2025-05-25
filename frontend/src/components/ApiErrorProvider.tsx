'use client'

import { useApiErrorHandler } from '@/hooks/useApiErrorHandler'

interface ApiErrorProviderProps {
  children: React.ReactNode
}

export function ApiErrorProvider({ children }: ApiErrorProviderProps) {
  // Attiva il gestore di errori API globale
  useApiErrorHandler()
  
  return <>{children}</>
} 