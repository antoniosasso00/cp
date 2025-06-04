import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from '@/shared/components/ui/toaster'
import { ThemeProvider } from '@/shared/components/theme-provider'
import { ThemeToggle } from '@/shared/components/ui/theme-toggle'
import { ApiErrorProvider } from '@/shared/components/ApiErrorProvider'
import { RoleGuard } from '@/shared/components/RoleGuard'
import { SWRProvider } from '@/shared/components/providers/SWRProvider'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Manta Group - Gestione Compositi',
  description: 'Sistema di gestione per la produzione di parti in composito',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="it" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <SWRProvider>
            <div className="flex justify-end p-4">
              <ThemeToggle />
            </div>
            <ApiErrorProvider>
              <RoleGuard>
                {children}
              </RoleGuard>
              <Toaster />
            </ApiErrorProvider>
          </SWRProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
