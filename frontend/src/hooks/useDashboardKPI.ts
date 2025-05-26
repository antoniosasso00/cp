'use client'

import { useState, useEffect } from 'react'
import { odlApi, nestingApi, autoclaveApi } from '@/lib/api'

export interface DashboardKPI {
  odl_totali: number
  odl_finiti: number
  odl_in_cura: number
  odl_attesa_nesting: number
  nesting_totali: number
  nesting_attivi: number
  nesting_completati: number
  utilizzo_medio_autoclavi: number
  completati_oggi: number
  efficienza_produzione: number
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
      const allODL = await odlApi.getAll()
      
      // Calcola statistiche ODL
      const odl_totali = allODL.length
      const odl_finiti = allODL.filter(odl => odl.status === 'Finito').length
      const odl_in_cura = allODL.filter(odl => odl.status === 'Cura').length
      const odl_attesa_nesting = allODL.filter(odl => odl.status === 'Attesa Cura').length
      
      // Calcola ODL completati oggi
      const oggi = new Date()
      oggi.setHours(0, 0, 0, 0)
      const completati_oggi = allODL.filter(odl => {
        if (odl.status !== 'Finito') return false
        const dataAggiornamento = new Date(odl.updated_at)
        return dataAggiornamento >= oggi
      }).length

      // Recupera statistiche nesting (se disponibili)
      let nesting_totali = 0
      let nesting_attivi = 0
      let nesting_completati = 0
      
      try {
        const nestingList = await nestingApi.getAll()
        nesting_totali = nestingList.length
        nesting_attivi = nestingList.filter(n => n.stato === 'attivo' || n.stato === 'in_corso').length
        nesting_completati = nestingList.filter(n => n.stato === 'completato').length
      } catch (nestingError) {
        console.warn('Errore nel recupero statistiche nesting:', nestingError)
        // Continua senza bloccare il caricamento
      }

      // Recupera informazioni autoclavi per calcolare utilizzo
      let utilizzo_medio_autoclavi = 0
      try {
        const autoclavi = await autoclaveApi.getAll()
        const autoclavi_disponibili = autoclavi.filter(a => a.stato === 'DISPONIBILE').length
        const autoclavi_in_uso = autoclavi.filter(a => a.stato === 'IN_USO').length
        const totale_autoclavi = autoclavi.length
        
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

      const kpiData: DashboardKPI = {
        odl_totali,
        odl_finiti,
        odl_in_cura,
        odl_attesa_nesting,
        nesting_totali,
        nesting_attivi,
        nesting_completati,
        utilizzo_medio_autoclavi,
        completati_oggi,
        efficienza_produzione
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