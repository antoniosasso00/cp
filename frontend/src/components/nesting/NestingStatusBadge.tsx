'use client'

import { Badge } from '@/components/ui/badge'
import { Clock, CheckCircle, XCircle, Package, FileText, Play } from 'lucide-react'

interface NestingStatusBadgeProps {
  stato: string
  confermato_da_ruolo?: string
  className?: string
}

export function NestingStatusBadge({ stato, confermato_da_ruolo, className }: NestingStatusBadgeProps) {
  const getStatusConfig = (stato: string) => {
    switch (stato) {
      case 'bozza':
        return {
          variant: 'outline' as const,
          icon: FileText,
          color: 'bg-gray-50 text-gray-700 border-gray-300',
          label: 'Bozza'
        }
      case 'in_sospeso':
      case 'In sospeso':
        return {
          variant: 'secondary' as const,
          icon: Clock,
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          label: 'In Sospeso'
        }
      case 'confermato':
      case 'Confermato':
        return {
          variant: 'default' as const,
          icon: Play,
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          label: 'Confermato'
        }
      case 'completato':
      case 'Completato':
        return {
          variant: 'default' as const,
          icon: Package,
          color: 'bg-green-100 text-green-800 border-green-200',
          label: 'Completato'
        }
      case 'annullato':
      case 'Annullato':
        return {
          variant: 'destructive' as const,
          icon: XCircle,
          color: 'bg-red-100 text-red-800 border-red-200',
          label: 'Annullato'
        }
      default:
        return {
          variant: 'outline' as const,
          icon: Clock,
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          label: stato
        }
    }
  }

  const config = getStatusConfig(stato)
  const IconComponent = config.icon

  return (
    <div className={`flex flex-col items-center gap-1 ${className}`}>
      <Badge 
        variant={config.variant}
        className={`${config.color} flex items-center gap-1 px-2 py-1`}
      >
        <IconComponent className="h-3 w-3" />
        {config.label}
      </Badge>
      {confermato_da_ruolo && stato === 'Confermato' && (
        <span className="text-xs text-muted-foreground">
          da {confermato_da_ruolo}
        </span>
      )}
    </div>
  )
} 