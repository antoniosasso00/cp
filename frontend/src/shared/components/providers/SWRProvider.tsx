'use client'

import { SWRConfig } from 'swr'
import { swrConfig } from '@/lib/swrConfig'

interface SWRProviderProps {
  children: React.ReactNode
}

/**
 * Provider SWR globale per CarbonPilot
 * 
 * 🎯 FUNZIONALITÀ:
 * • Cache globale di 15 secondi per tutte le API calls
 * • Rivalidazione intelligente (focus, reconnect)
 * • Gestione errori centralizzata
 * • Retry automatico con backoff
 * • Ottimizzazioni per performance
 * 
 * 💡 USO:
 * Avvolge automaticamente tutta l'applicazione per abilitare
 * la cache SWR su tutti i componenti che usano useSWR
 */
export function SWRProvider({ children }: SWRProviderProps) {
  return (
    <SWRConfig value={swrConfig}>
      {children}
    </SWRConfig>
  )
} 