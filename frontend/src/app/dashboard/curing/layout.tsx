import { ReactNode } from 'react'

/**
 * Layout per le pagine del Curing
 * Eredita dal layout principale del dashboard
 */
export default function CuringLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 