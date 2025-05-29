'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface NestingStatusBadgeProps {
  stato: string
  className?: string
}

// Funzione per ottenere il colore del badge in base allo stato
const getStatoBadgeVariant = (stato: string) => {
  switch (stato.toLowerCase()) {
    case 'bozza':
      return 'outline' as const
    case 'creato':
      return 'secondary' as const
    case 'in sospeso':
      return 'default' as const
    case 'confermato':
      return 'default' as const
    case 'caricato':
      return 'destructive' as const
    case 'completato':
      return 'default' as const
    case 'errore':
      return 'destructive' as const
    default:
      return 'outline' as const
  }
}

// Funzione per ottenere l'icona dello stato
const getStatoIcon = (stato: string) => {
  switch (stato.toLowerCase()) {
    case 'bozza':
      return '📝'
    case 'creato':
      return '✨'
    case 'in sospeso':
      return '⏳'
    case 'confermato':
      return '✅'
    case 'caricato':
      return '🔥'
    case 'completato':
      return '🎉'
    case 'errore':
      return '❌'
    default:
      return '❓'
  }
}

// Funzione per ottenere la descrizione dello stato
const getStatoDescription = (stato: string) => {
  switch (stato.toLowerCase()) {
    case 'bozza':
      return 'Nesting in fase di creazione'
    case 'creato':
      return 'Nesting creato, pronto per la conferma'
    case 'in sospeso':
      return 'Nesting confermato, pronto per il caricamento'
    case 'confermato':
      return 'Nesting confermato, pronto per il caricamento'
    case 'caricato':
      return 'Nesting caricato in autoclave, cura in corso'
    case 'completato':
      return 'Nesting completato con successo'
    case 'errore':
      return 'Errore durante il processo'
    default:
      return 'Stato sconosciuto'
  }
}

export function NestingStatusBadge({ stato, className }: NestingStatusBadgeProps) {
  const variant = getStatoBadgeVariant(stato)
  const icon = getStatoIcon(stato)
  const description = getStatoDescription(stato)

  return (
    <Badge 
      variant={variant} 
      className={cn("flex items-center gap-1", className)}
      title={description}
    >
      <span className="text-xs">{icon}</span>
      <span>{stato}</span>
    </Badge>
  )
} 