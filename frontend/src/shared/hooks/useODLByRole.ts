'use client'

import { useState, useEffect } from 'react'
import { odlApi, reportsApi, type ODLResponse } from '@/lib/api'

interface UseODLByRoleOptions {
  role: 'Clean Room' | 'Curing'
  autoRefresh?: boolean
  refreshInterval?: number
}

interface UseODLByRoleReturn {
  odlList: ODLResponse[]
  loading: boolean
  error: string | null
  refresh: () => void
  updateODLStatus: (odlId: number, newStatus: string) => Promise<void>
}

/**
 * Hook per ottenere ODL filtrati per ruolo specifico
 * 
 * Clean Room: ODL in stato "Preparazione" e "Laminazione"
 * Curing: ODL in stato "Attesa Cura" e "Cura"
 */
export function useODLByRole({ 
  role, 
  autoRefresh = false, 
  refreshInterval = 30000 
}: UseODLByRoleOptions): UseODLByRoleReturn {
  const [odlList, setOdlList] = useState<ODLResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Definisce gli stati ODL per ogni ruolo
  const getStatusFilterForRole = (userRole: string): string[] => {
    switch (userRole) {
      case 'Clean Room':
        return ['Preparazione', 'Laminazione']
      case 'Curing':
        return ['Attesa Cura', 'Cura']
      default:
        return []
    }
  }

  const fetchODLByRole = async () => {
    try {
      setLoading(true)
      setError(null)

      // Ottieni tutti gli ODL - l'API non supporta limit/skip, quindi filtriamo localmente
      const allODL = await odlApi.getAll()
      
      // Filtra per stati appropriati al ruolo
      const allowedStatuses = getStatusFilterForRole(role)
      const filteredODL = allODL.filter(odl => 
        odl.status && allowedStatuses.includes(odl.status)
      )

      // Ordina per priorità (alta prima) e poi per data di creazione
      filteredODL.sort((a, b) => {
        // Prima ordina per priorità (numeri più alti = priorità più alta)
        const priorityDiff = (b.priorita || 0) - (a.priorita || 0)
        if (priorityDiff !== 0) return priorityDiff
        
        // Poi per data di creazione (più recenti prima)
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      })

      setOdlList(filteredODL)
      
    } catch (err) {
      console.error(`Errore nel caricamento ODL per ${role}:`, err)
      setError(`Errore nel caricamento degli ODL per ${role}`)
    } finally {
      setLoading(false)
    }
  }

  // Funzione per aggiornare lo stato di un ODL usando la funzione di utilità migliorata
  const updateODLStatus = async (odlId: number, newStatus: string) => {
    try {
      // Validazione per ruolo specifico
      const allowedStatuses = getStatusFilterForRole(role)
      const nextStatuses = getNextStatusesForRole(role, newStatus)
      
      if (!nextStatuses.includes(newStatus)) {
        throw new Error(`Stato ${newStatus} non valido per il ruolo ${role}`)
      }

      // Usa la funzione di utilità migliorata
      const updatedODL = await reportsApi.updateOdlStatus(odlId, newStatus)
      
      // Aggiorna la lista locale
      setOdlList(prevList => 
        prevList.map(odl => 
          odl.id === odlId 
            ? updatedODL
            : odl
        ).filter(odl => {
          // Rimuovi ODL che non sono più rilevanti per questo ruolo
          const allowedStatuses = getStatusFilterForRole(role)
          return allowedStatuses.includes(odl.status || '')
        })
      )
      
    } catch (err) {
      console.error('Errore nell\'aggiornamento dello stato ODL:', err)
      throw new Error('Errore nell\'aggiornamento dello stato')
    }
  }

  // Funzione helper per ottenere gli stati successivi validi per ruolo
  const getNextStatusesForRole = (userRole: string, currentStatus: string): string[] => {
    switch (userRole) {
      case 'Clean Room':
        return ['Laminazione', 'Attesa Cura']
      case 'Curing':
        return ['Cura', 'Finito']
      default:
        return []
    }
  }

  // Effetto per il caricamento iniziale
  useEffect(() => {
    fetchODLByRole()
  }, [role])

  // Effetto per il refresh automatico
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(fetchODLByRole, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, role])

  return {
    odlList,
    loading,
    error,
    refresh: fetchODLByRole,
    updateODLStatus
  }
} 