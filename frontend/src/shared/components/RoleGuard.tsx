'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useUserRole } from '@/hooks/useUserRole'

interface RoleGuardProps {
  children: React.ReactNode
}

/**
 * Componente che protegge le route verificando se l'utente ha un ruolo impostato
 * 
 * Se l'utente non ha un ruolo e non si trova già nella pagina di selezione ruolo,
 * viene reindirizzato a /select-role
 */
export function RoleGuard({ children }: RoleGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { role, isLoading } = useUserRole()

  useEffect(() => {
    // Non fare nulla durante il caricamento
    if (isLoading) return

    // Se siamo già nella pagina di selezione ruolo, non fare redirect
    if (pathname === '/select-role' || pathname === '/role') return

    // Se siamo nella home page, non fare redirect (permette l'accesso alla landing)
    if (pathname === '/') return

    // Se non c'è un ruolo impostato, reindirizza alla selezione ruolo
    if (!role) {
      router.push('/select-role')
      return
    }
  }, [role, isLoading, pathname, router])

  // Durante il caricamento, mostra uno spinner
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Se non c'è ruolo e non siamo nelle pagine permesse, non renderizzare nulla
  // (il redirect è già in corso)
  if (!role && pathname !== '/select-role' && pathname !== '/role' && pathname !== '/') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Renderizza i children se tutto è ok
  return <>{children}</>
} 