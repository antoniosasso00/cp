'use client'

import { useState, useEffect } from 'react'
import { odlApi, autoclavesApi, batchNestingApi } from '@/lib/api'

export interface DashboardKPI {
  odl_totali: number
  odl_finiti: number
  odl_in_cura: number
  odl_attesa_cura: number
  utilizzo_medio_autoclavi: number
  completati_oggi: number
  efficienza_produzione: number
  nesting_attivi: number
  nesting_totali: number
}

export interface KPIStatus {
  loading: boolean
  error: string | null
  data: DashboardKPI | null
  lastUpdated: Date | null
}

export function useDashboardKPI() {
  const [status, setStatus] = useState<KPIStatus>({
    loading: true,
    error: null,
    data: null,
    lastUpdated: null
  })

  const fetchKPI = async () => {
    try {
      setStatus(prev => ({ ...prev, loading: true, error: null }))

      // Recupera tutti gli ODL per calcolare le statistiche
      const allODL = await odlApi.fetchODLs()
      
      // Calcola statistiche ODL con valori di sicurezza
      const odl_totali = allODL?.length ?? 0
      const odl_finiti = allODL?.filter((odl: any) => odl.status === 'Finito')?.length ?? 0
      const odl_in_cura = allODL?.filter((odl: any) => odl.status === 'Cura')?.length ?? 0
      const odl_attesa_cura = allODL?.filter((odl: any) => odl.status === 'Attesa Cura')?.length ?? 0
      
      // Calcola ODL completati oggi
      const oggi = new Date()
      oggi.setHours(0, 0, 0, 0)
      const completati_oggi = allODL?.filter((odl: any) => {
        if (odl.status !== 'Finito') return false
        if (!odl.updated_at) return false
        const dataAggiornamento = new Date(odl.updated_at)
        return dataAggiornamento >= oggi
      })?.length ?? 0

      // Recupera informazioni autoclavi per calcolare utilizzo
      let utilizzo_medio_autoclavi = 0
      try {
        const autoclavi = await autoclavesApi.fetchAutoclaves()
        const autoclavi_disponibili = autoclavi?.filter(a => a.stato === 'DISPONIBILE')?.length ?? 0
        const autoclavi_in_uso = autoclavi?.filter(a => a.stato === 'IN_USO')?.length ?? 0
        const totale_autoclavi = autoclavi?.length ?? 0
        
        if (totale_autoclavi > 0) {
          utilizzo_medio_autoclavi = Math.round((autoclavi_in_uso / totale_autoclavi) * 100)
        }
      } catch (autoclaveError) {
        console.warn('Errore nel recupero statistiche autoclavi:', autoclaveError)
        // Continua senza bloccare il caricamento
      }

      // Calcola efficienza produzione (basata su ODL completati vs totali)
      const efficienza_produzione = odl_totali > 0 
        ? Math.round((odl_finiti / odl_totali) * 100)
        : 0

      // Calcola statistiche nesting
      let nesting_attivi = 0
      let nesting_totali = 0
      try {
        // Recupera tutti i batch nesting per calcolare le statistiche
        const batches = await batchNestingApi.getAll()
        nesting_totali = batches?.length ?? 0
        nesting_attivi = batches?.filter((batch: any) => batch.stato === 'confermato')?.length ?? 0
      } catch (nestingError) {
        console.warn('Errore nel recupero statistiche nesting:', nestingError)
        nesting_attivi = 0
        nesting_totali = 0
      }

      const kpiData: DashboardKPI = {
        odl_totali,
        odl_finiti,
        odl_in_cura,
        odl_attesa_cura,
        utilizzo_medio_autoclavi,
        completati_oggi,
        efficienza_produzione,
        nesting_attivi,
        nesting_totali
      }

      setStatus({
        loading: false,
        error: null,
        data: kpiData,
        lastUpdated: new Date()
      })

    } catch (error) {
      console.error('Errore nel caricamento KPI dashboard:', error)
      setStatus(prev => ({
        ...prev,
        loading: false,
        error: 'Errore nel caricamento dei dati. Riprova più tardi.'
      }))
    }
  }

  const refreshKPI = () => {
    fetchKPI()
  }

  useEffect(() => {
    fetchKPI()
    
    // Aggiorna automaticamente ogni 5 minuti
    const interval = setInterval(fetchKPI, 5 * 60 * 1000)
    
    return () => clearInterval(interval)
  }, [])

  return {
    ...status,
    refresh: refreshKPI
  }
} 