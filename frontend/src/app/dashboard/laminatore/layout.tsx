import { ReactNode } from 'react'

/**
 * Layout per le pagine del laminatore
 * Eredita dal layout principale del dashboard
 */
export default function LaminatoreLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 