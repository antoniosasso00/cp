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

  const fetchTools = useCallback(async () => {
    if (!isActiveRef.current) return
    
    try {
      setError(null)
      const data = await toolApi.getAllWithStatus(filters)
      setTools(data)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Errore nel caricamento dei tool:', err)
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }, [filters])

  const syncStatus = useCallback(async () => {
    try {
      setError(null)
      await toolApi.updateStatusFromODL()
      // Dopo la sincronizzazione, ricarica i dati
      await fetchTools()
    } catch (err) {
      console.error('Errore nella sincronizzazione dello stato dei tool:', err)
      setError(err instanceof Error ? err.message : 'Errore nella sincronizzazione')
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