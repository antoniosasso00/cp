import { ReactNode } from 'react'

/**
 * Layout per le pagine dell'autoclavista
 * Eredita dal layout principale del dashboard
 */
export default function AutoclavistaLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 