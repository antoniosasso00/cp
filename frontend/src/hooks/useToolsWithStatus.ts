'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { toolApi, ToolWithStatus } from '@/lib/api'

interface UseToolsWithStatusOptions {
  autoRefresh?: boolean
  refreshInterval?: number // in millisecondi
  refreshOnFocus?: boolean
  filters?: {
    skip?: number
    limit?: number
    part_number_tool?: string
    disponibile?: boolean
  }
}

interface UseToolsWithStatusReturn {
  tools: ToolWithStatus[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  syncStatus: () => Promise<void>
  lastUpdated: Date | null
}

export function useToolsWithStatus(options: UseToolsWithStatusOptions = {}): UseToolsWithStatusReturn {
  const {
    autoRefresh = true,
    refreshInterval = 5000, // 5 secondi
    refreshOnFocus = true,
    filters
  } = options

  const [tools, setTools] = useState<ToolWithStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isActiveRef = useRef(true)
  const isFetchingRef = useRef(false)

  const fetchTools = useCallback(async () => {
    if (!isActiveRef.current || isFetchingRef.current) return
    
    try {
      isFetchingRef.current = true
      setError(null)
      console.log('🔄 Fetching tools with status...', filters)
      const data = await toolApi.getAllWithStatus(filters)
      console.log('✅ Tools fetched successfully:', data)
      
      // Validazione dei dati ricevuti
      if (!Array.isArray(data)) {
        throw new Error('I dati ricevuti non sono un array valido')
      }
      
      // Validazione di ogni tool
      const validatedTools = data.map((tool, index) => {
        if (!tool || typeof tool !== 'object') {
          console.warn(`Tool ${index} non è un oggetto valido:`, tool)
          return null
        }
        
        // Assicurati che tutti i campi necessari siano presenti
        return {
          ...tool,
          status_display: tool.status_display || 'Sconosciuto',
          current_odl: tool.current_odl || null
        }
      }).filter(Boolean) as ToolWithStatus[]
      
      setTools(validatedTools)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('❌ Errore nel caricamento dei tool:', err)
      const errorMessage = err instanceof Error ? err.message : 'Errore sconosciuto nel caricamento dei tools'
      setError(errorMessage)
    } finally {
      setLoading(false)
      isFetchingRef.current = false
    }
  }, [filters])

  const syncStatus = useCallback(async () => {
    try {
      setError(null)
      console.log('🔄 Sincronizzazione stato tools...')
      const result = await toolApi.updateStatusFromODL()
      console.log('✅ Sincronizzazione completata:', result)
      
      // Dopo la sincronizzazione, ricarica i dati
      await fetchTools()
    } catch (err: any) {
      console.error('❌ Errore nella sincronizzazione dello stato dei tool:', err)
      
      // Gestione migliorata degli errori
      let errorMessage = 'Errore nella sincronizzazione dello stato dei tools'
      
      if (err?.response?.status === 422) {
        errorMessage = 'Errore di validazione durante la sincronizzazione'
      } else if (err?.response?.status === 500) {
        errorMessage = 'Errore interno del server durante la sincronizzazione'
      } else if (err?.message) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      }
      
      setError(errorMessage)
      throw new Error(errorMessage) // Rilancia l'errore con messaggio leggibile
    }
  }, [fetchTools])

  const refresh = useCallback(async () => {
    setLoading(true)
    await fetchTools()
  }, [fetchTools])

  // Caricamento iniziale
  useEffect(() => {
    fetchTools()
  }, [fetchTools])

  // Auto-refresh con intervallo
  useEffect(() => {
    if (!autoRefresh) return

    intervalRef.current = setInterval(() => {
      if (isActiveRef.current && !document.hidden) {
        fetchTools()
      }
    }, refreshInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoRefresh, refreshInterval, fetchTools])

  // Refresh quando la finestra torna in focus
  useEffect(() => {
    if (!refreshOnFocus) return

    const handleFocus = () => {
      if (isActiveRef.current) {
        fetchTools()
      }
    }

    const handleVisibilityChange = () => {
      if (!document.hidden && isActiveRef.current) {
        fetchTools()
      }
    }

    window.addEventListener('focus', handleFocus)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [refreshOnFocus, fetchTools])

  // Cleanup quando il componente viene smontato
  useEffect(() => {
    return () => {
      isActiveRef.current = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return {
    tools,
    loading,
    error,
    refresh,
    syncStatus,
    lastUpdated
  }
} 