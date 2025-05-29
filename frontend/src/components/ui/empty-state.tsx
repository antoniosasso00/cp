import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { AlertCircle, Search, RefreshCw } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description: string
  icon?: React.ReactNode
  action?: {
    label: string
    onClick: () => void
    variant?: 'default' | 'outline' | 'secondary' | 'destructive' | 'ghost' | 'link'
  }
  className?: string
}

export function EmptyState({ 
  title, 
  description, 
  icon, 
  action, 
  className = '' 
}: EmptyStateProps) {
  const defaultIcon = <AlertCircle className="h-12 w-12 text-gray-400" />
  
  return (
    <Card className={className}>
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="mb-4">
          {icon || defaultIcon}
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {title}
        </h3>
        <p className="text-gray-500 text-center mb-4 max-w-md">
          {description}
        </p>
        {action && (
          <Button 
            variant={action.variant || 'outline'} 
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// Varianti predefinite per casi comuni
export function NoDataEmptyState({ 
  onReset, 
  hasFilters = false 
}: { 
  onReset?: () => void
  hasFilters?: boolean 
}) {
  return (
    <EmptyState
      title="Nessun dato disponibile"
      description={
        hasFilters 
          ? "Non ci sono dati per i filtri selezionati. Prova a modificare i criteri di ricerca."
          : "Non ci sono dati da visualizzare al momento."
      }
      icon={<Search className="h-12 w-12 text-gray-400" />}
      action={onReset ? {
        label: hasFilters ? "Resetta filtri" : "Ricarica",
        onClick: onReset,
        variant: "outline"
      } : undefined}
    />
  )
}

export function ErrorEmptyState({ 
  onRetry, 
  errorMessage = "Si è verificato un errore durante il caricamento dei dati." 
}: { 
  onRetry?: () => void
  errorMessage?: string 
}) {
  return (
    <EmptyState
      title="Errore nel caricamento"
      description={errorMessage}
      icon={<AlertCircle className="h-12 w-12 text-red-400" />}
      action={onRetry ? {
        label: "Riprova",
        onClick: onRetry,
        variant: "outline"
      } : undefined}
    />
  )
}

export function LoadingEmptyState() {
  return (
    <EmptyState
      title="Caricamento in corso..."
      description="Attendere mentre i dati vengono caricati."
      icon={<RefreshCw className="h-12 w-12 text-blue-400 animate-spin" />}
    />
  )
} 