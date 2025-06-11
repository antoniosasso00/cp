import { SWRConfiguration } from 'swr'

/**
 * Configurazione globale SWR per ottimizzare le performance
 * 
 * 🎯 CARATTERISTICHE:
 * • Cache dati per 15 secondi (dedupingInterval)
 * • Rivalidazione automatica quando la tab torna in focus
 * • Rivalidazione quando la connessione torna online
 * • Retry ridotti per evitare loop infiniti
 * • Cache infinita per ridurre richieste duplicate
 */
export const swrConfig: SWRConfiguration = {
  // ⚡ PERFORMANCE: Evita richieste duplicate per 15 secondi
  dedupingInterval: 15000,
  
  // 🔄 RIVALIDAZIONE: Comportamenti smart per UX ottimale
  revalidateOnFocus: false,          // ❌ DISABILITATO: evita loop su focus
  revalidateOnReconnect: true,       // Aggiorna quando la connessione torna
  revalidateIfStale: true,           // Aggiorna se i dati sono "vecchi"
  
  // ⏱️ TIMING: Gestione intelligente dei tempi
  errorRetryInterval: 10000,         // ⬆️ INCREMENTATO: 10 secondi invece di 5
  focusThrottleInterval: 10000,      // ⬆️ INCREMENTATO: 10 secondi invece di 5
  
  // 🎛️ RETRY: Gestione errori più conservativa per evitare loop
  errorRetryCount: 1,                // ⬇️ RIDOTTO: Solo 1 tentativo invece di 3
  
  // 📱 RESPONSIVE: Comportamento ottimizzato per mobile
  refreshWhenOffline: false,         // Non fare richieste quando offline
  refreshWhenHidden: false,          // Non fare richieste quando tab nascosta
  
  // 🎨 LOADING: Stati di caricamento ottimizzati
  keepPreviousData: true,            // Mantieni dati precedenti durante ricaricamento
  
  // 🔧 FETCHER di default per API CarbonPilot
  fetcher: async (url: string) => {
    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`) as Error & { name: string }
      error.name = 'FetchError'
      throw error
    }
    
    return response.json()
  },
  
  // 🐛 ERROR HANDLER: Gestione errori centralizzata
  onError: (error: Error, key: string) => {
    console.warn(`[SWR Error] Key: ${key}`, error)
    
    // Log errori critici per debugging
    if (error.name === 'FetchError' && error.message.includes('50')) {
      console.error('🚨 Errore server critico:', { key, error })
    }
  },
  
  // ✅ SUCCESS HANDLER: Log per debugging (solo in development)
  onSuccess: (data: any, key: string) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[SWR Success] Cache updated for: ${key}`)
    }
  }
}

/**
 * Hook personalizzato per ottimizzare fetch di dati pesanti
 * Utile per grafici e tabelle grandi
 */
export const heavyDataConfig: SWRConfiguration = {
  ...swrConfig,
  // 🐌 DATI PESANTI: Cache più lunga per componenti pesanti
  dedupingInterval: 30000,           // 30 secondi per dati pesanti
  refreshWhenHidden: false,          // Mai aggiornare se nascosti
  revalidateOnFocus: false,          // Non rivalidare automaticamente su focus
  
  // 🎯 PERFORMANCE: Meno aggiornamenti per componenti costosi
  errorRetryCount: 0,                // ❌ NESSUN RETRY per dati pesanti
  focusThrottleInterval: 30000,      // Throttle di 30 secondi
}

/**
 * Configurazione per dati real-time (monitoring, stats)
 */
export const realTimeConfig: SWRConfiguration = {
  ...swrConfig,
  // ⚡ REAL-TIME: Aggiornamenti più frequenti
  dedupingInterval: 5000,            // 5 secondi per dati real-time
  refreshInterval: 10000,            // Auto-refresh ogni 10 secondi
  revalidateOnFocus: false,          // ❌ DISABILITATO: evita loop continui
  
  // 🔄 RESPONSIVITA': Più reattivo per dashboard
  errorRetryInterval: 15000,         // ⬆️ INCREMENTATO: Retry più lento
  focusThrottleInterval: 15000,      // ⬆️ INCREMENTATO: Throttle aumentato
  errorRetryCount: 1,                // ⬇️ RIDOTTO: Solo 1 retry
} 