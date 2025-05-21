import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
// React Query
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CarbonPilot - Gestione Compositi',
  description: 'Sistema di gestione per la produzione di parti in composito',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // QueryClient deve essere creato una sola volta
  const [queryClient] = useState(() => new QueryClient())
  return (
    <html lang="it">
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster />
        </QueryClientProvider>
      </body>
    </html>
  )
} 