import { ReactNode } from 'react'

/**
 * Layout per le pagine del Clean Room
 * Eredita dal layout principale del dashboard
 */
export default function CleanRoomLayout({
  children,
}: {
  children: ReactNode
}) {
  return <>{children}</>
} 