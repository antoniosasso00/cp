'use client'

import React, { ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface NestingTabWrapperProps {
  children: ReactNode
  title?: string
  description?: string
  error?: string | null
  isLoading?: boolean
  onRetry?: () => void
}

/**
 * Wrapper sicuro per i contenuti dei Tab di nesting
 * Gestisce errori, stati di caricamento e fornisce fallback sicuri
 */
export function NestingTabWrapper({ 
  children, 
  title, 
  description, 
  error, 
  isLoading = false,
  onRetry 
}: NestingTabWrapperProps) {
  
  // Gestione errori con fallback sicuro
  if (error) {
    return (
      <Card>
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Errore</AlertTitle>
            <AlertDescription className="space-y-2">
              <p>{error}</p>
              {onRetry && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={onRetry}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Riprova
                </Button>
              )}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  // Stato di caricamento
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Caricamento in corso...</span>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Fallback per children null/undefined
  if (!children) {
    return (
      <Card>
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <span className="text-muted-foreground">Contenuto non disponibile</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Wrapper con gestione errori React
  return (
    <ErrorBoundary>
      {children}
    </ErrorBoundary>
  )
}

/**
 * Error Boundary per catturare errori React nei componenti figli
 */
class ErrorBoundary extends React.Component<
  { children: ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('❌ Errore nel componente Tab:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>Errore Componente</CardTitle>
            <CardDescription>
              Si è verificato un errore nel caricamento di questo tab
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Errore React</AlertTitle>
              <AlertDescription>
                <p>Il componente ha riscontrato un errore e non può essere visualizzato.</p>
                <p className="text-sm mt-2 font-mono">
                  {this.state.error?.message || 'Errore sconosciuto'}
                </p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-2"
                  onClick={() => {
                    this.setState({ hasError: false, error: undefined })
                    window.location.reload()
                  }}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Ricarica Pagina
                </Button>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}

export default NestingTabWrapper 