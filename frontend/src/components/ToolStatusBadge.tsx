'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ToolStatusBadgeProps {
  status: string
  className?: string
}

export function ToolStatusBadge({ status, className }: ToolStatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'Disponibile':
        return {
          variant: 'default' as const,
          className: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-100',
          icon: '✅'
        }
      case 'In uso – Preparazione':
        return {
          variant: 'secondary' as const,
          className: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-100',
          icon: '🔧'
        }
      case 'In Laminazione':
        return {
          variant: 'secondary' as const,
          className: 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900 dark:text-orange-100',
          icon: '🏭'
        }
      case 'In Attesa di Cura':
        return {
          variant: 'secondary' as const,
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900 dark:text-yellow-100',
          icon: '⏳'
        }
      case 'In Autoclave':
        return {
          variant: 'destructive' as const,
          className: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900 dark:text-red-100',
          icon: '🔥'
        }
      default:
        return {
          variant: 'outline' as const,
          className: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-100',
          icon: '❓'
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <Badge 
      variant={config.variant}
      className={cn(config.className, className)}
    >
      <span className="mr-1">{config.icon}</span>
      {status}
    </Badge>
  )
} 