'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useUserRole } from '@/shared/hooks/useUserRole'
import { Loader2 } from 'lucide-react'

// Caricamento dinamico dei componenti dashboard per ottimizzare il bundle
// Ogni componente viene caricato solo quando necessario
const DashboardAdmin = dynamic(() => import('@/components/dashboard/DashboardAdmin'), {
  loading: () => <DashboardLoading />,
  ssr: false
})

const DashboardManagement = dynamic(() => import('@/components/dashboard/DashboardManagement'), {
  loading: () => <DashboardLoading />,
  ssr: false
})

const DashboardCleanRoom = dynamic(() => import('@/components/dashboard/DashboardCleanRoom'), {
  loading: () => <DashboardLoading />,
  ssr: false
})

const DashboardCuring = dynamic(() => import('@/components/dashboard/DashboardCuring'), {
  loading: () => <DashboardLoading />,
  ssr: false
})

/**
 * Componente di loading mostrato durante il caricamento dinamico
 */
function DashboardLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
        <p className="text-muted-foreground">Caricamento dashboard...</p>
      </div>
    </div>
  )
}

/**
 * Dashboard principale che carica dinamicamente il contenuto
 * in base al ruolo dell'utente salvato in localStorage
 * 
 * Funzionalità:
 * - Legge il ruolo utente tramite useUserRole()
 * - Carica dinamicamente il componente appropriato
 * - Reindirizza a /modules/role se il ruolo non è valido
 * - Ottimizza il bundle caricando solo il componente necessario
 */
export default function DashboardPage() {
  const router = useRouter()
  const { role, isLoading } = useUserRole()

  // Effetto per gestire il reindirizzamento se il ruolo non è valido
  useEffect(() => {
    console.log('Dashboard - stato hook:', { role, isLoading })
    // Aspetta che il caricamento del ruolo sia completato
    if (!isLoading && !role) {
      console.log('Nessun ruolo trovato, reindirizzamento a /modules/role')
      // Aggiungiamo un piccolo delay per assicurarci che localStorage sia stato letto
      setTimeout(() => {
        router.push('/modules/role')
      }, 200)
    }
  }, [role, isLoading, router])

  // Mostra loading durante il caricamento iniziale del ruolo
  if (isLoading) {
    return <DashboardLoading />
  }

  // Se non c'è un ruolo valido, mostra loading (il reindirizzamento è in corso)
  if (!role) {
    return <DashboardLoading />
  }

  // Renderizza il componente dashboard appropriato in base al ruolo
  switch (role) {
    case 'ADMIN':
      return <DashboardAdmin />
    
    case 'Management':
      return <DashboardManagement />
    
    case 'Clean Room':
      return <DashboardCleanRoom />
    
    case 'Curing':
      return <DashboardCuring />
    
    default:
      // Ruolo non riconosciuto, reindirizza alla selezione ruolo
      console.warn(`Ruolo non riconosciuto: ${role}`)
      router.push('/modules/role')
      return <DashboardLoading />
  }
} 