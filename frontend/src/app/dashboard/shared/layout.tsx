import { ReactNode } from 'react'

/**
 * Layout per le pagine condivise tra ruoli
 * Eredita dal layout principale del dashboard
 */
export default function SharedLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 