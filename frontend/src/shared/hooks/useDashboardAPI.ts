'use client'

import { useState, useEffect, useCallback } from 'react'
import { API_ENDPOINTS, REFRESH_INTERVALS } from '@/lib/config'

/**
 * 🔄 Hook per gestire le chiamate API del dashboard
 * 
 * Utilizza gli endpoint specifici del dashboard che sono ottimizzati
 * per fornire dati aggregati e statistiche in tempo reale.
 */

export interface ODLStats {
  totali: number
  completati: number
  in_corso: number
  in_sospeso: number
  percentuale_completamento: number
  variazione_giornaliera: number
  trend_ultimi_7_giorni: Array<{
    data: string
    completati: number
    totali: number
  }>
  last_updated: string
}

export interface AutoclaveLoad {
  carico_totale_percentuale: number
  autoclavi_attive: number
  autoclavi_totali: number
  capacita_utilizzata_kg: number
  capacita_massima_kg: number
  variazione_oraria: number
  autoclavi_per_stato: {
    disponibili: number
    occupate: number
    manutenzione: number
    errore: number
  }
  trend_utilizzo_24h: Array<{
    ora: string
    percentuale: number
    autoclavi_attive: number
  }>
  last_updated: string
}

export interface NestingActive {
  nesting_attivi: number
  nesting_in_coda: number
  batch_completati_oggi: number
  batch_totali_oggi: number
  tempo_medio_elaborazione_minuti: number
  variazione_giornaliera: number
  nesting_per_stato: {
    in_elaborazione: number
    in_sospeso: number
    confermati: number
    completati: number
  }
  dettagli_nesting: Array<{
    id: number
    nome: string
    stato: string
    autoclave_nome: string
    odl_count: number
    peso_kg: number
    created_at: string
  }>
  last_updated: string
}

export interface KPISummary {
  odl: ODLStats
  autoclavi: AutoclaveLoad
  nesting: NestingActive
  sistema: {
    uptime_ore: number
    performance_score: number
    errori_ultimi_24h: number
    ultimo_backup: string
  }
  last_updated: string
}

interface APIHookState<T> {
  data: T | null
  loading: boolean
  error: string | null
  lastUpdated: Date | null
}

/**
 * 🔄 Hook generico per chiamate API dashboard
 */
function useDashboardEndpoint<T>(
  endpoint: string,
  refreshInterval: number = REFRESH_INTERVALS.dashboard
) {
  const [state, setState] = useState<APIHookState<T>>({
    data: null,
    loading: true,
    error: null,
    lastUpdated: null
  })

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }))
      
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      setState({
        data,
        loading: false,
        error: null,
        lastUpdated: new Date()
      })
    } catch (error) {
      console.error(`Errore nel caricamento ${endpoint}:`, error)
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Errore sconosciuto'
      }))
    }
  }, [endpoint])

  const refresh = useCallback(() => {
    fetchData()
  }, [fetchData])

  useEffect(() => {
    fetchData()
    
    // Auto-refresh
    const interval = setInterval(fetchData, refreshInterval)
    return () => clearInterval(interval)
  }, [fetchData, refreshInterval])

  return {
    ...state,
    refresh
  }
}

/**
 * 📊 Hook per statistiche ODL (interno)
 */
function useODLStats() {
  return useDashboardEndpoint<ODLStats>(API_ENDPOINTS.dashboard.odlCount)
}

/**
 * 🏭 Hook per carico autoclavi (interno)
 */
function useAutoclaveLoad() {
  return useDashboardEndpoint<AutoclaveLoad>(API_ENDPOINTS.dashboard.autoclaveLoad)
}

/**
 * 📦 Hook per nesting attivi (interno)
 */
function useNestingActive() {
  return useDashboardEndpoint<NestingActive>(API_ENDPOINTS.dashboard.nestingActive)
}

/**
 * 📈 Hook per KPI summary completo
 */
export function useKPISummary() {
  return useDashboardEndpoint<KPISummary>(API_ENDPOINTS.dashboard.kpiSummary)
}

/**
 * 🎯 Hook principale per dashboard KPI (compatibilità con il vecchio hook)
 */
export function useDashboardKPI() {
  const kpiSummary = useKPISummary()
  
  // Trasforma i dati nel formato atteso dal componente esistente
  const transformedData = kpiSummary.data ? {
    odl_totali: kpiSummary.data.odl.totali,
    odl_finiti: kpiSummary.data.odl.completati,
    odl_in_cura: kpiSummary.data.odl.in_corso,
    odl_attesa_cura: kpiSummary.data.odl.in_sospeso,
    utilizzo_medio_autoclavi: kpiSummary.data.autoclavi.carico_totale_percentuale,
    completati_oggi: kpiSummary.data.odl.variazione_giornaliera,
    efficienza_produzione: kpiSummary.data.odl.percentuale_completamento,
    nesting_attivi: kpiSummary.data.nesting.nesting_attivi,
    nesting_totali: kpiSummary.data.nesting.nesting_attivi + kpiSummary.data.nesting.nesting_in_coda
  } : null

  return {
    data: transformedData,
    loading: kpiSummary.loading,
    error: kpiSummary.error,
    refresh: kpiSummary.refresh
  }
} 