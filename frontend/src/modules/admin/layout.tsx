import { ReactNode } from 'react'

/**
 * Layout per le pagine dell'amministratore
 * Eredita dal layout principale del dashboard
 */
export default function AdminLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 