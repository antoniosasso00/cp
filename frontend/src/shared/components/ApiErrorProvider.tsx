'use client'

import { useApiErrorHandler } from '@/shared/hooks/useApiErrorHandler'

interface ApiErrorProviderProps {
  children: React.ReactNode
}

export function ApiErrorProvider({ children }: ApiErrorProviderProps) {
  // Attiva il gestore di errori API globale
  useApiErrorHandler()
  
  return <>{children}</>
} 