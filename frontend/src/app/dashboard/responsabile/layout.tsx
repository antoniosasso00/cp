import { ReactNode } from 'react'

/**
 * Layout per le pagine del responsabile
 * Eredita dal layout principale del dashboard
 */
export default function ResponsabileLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 