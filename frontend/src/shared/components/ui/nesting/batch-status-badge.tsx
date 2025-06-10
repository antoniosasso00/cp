'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/shared/lib/utils'
import { 
  BATCH_STATUS_CONFIG, 
  BatchStatus,
  getStatusLabel,
  getStatusColor 
} from '@/shared/hooks/useBatchStatus'
import type { BatchStatusBadgeProps } from './types'

// Size configurations
const SIZE_CONFIG = {
  sm: {
    text: 'text-xs',
    padding: 'px-2 py-1',
    icon: 'h-3 w-3'
  },
  md: {
    text: 'text-sm',
    padding: 'px-2.5 py-1',
    icon: 'h-4 w-4'
  },
  lg: {
    text: 'text-base',
    padding: 'px-3 py-1.5',
    icon: 'h-5 w-5'
  }
}

export const BatchStatusBadge: React.FC<BatchStatusBadgeProps> = ({
  status,
  size = 'md',
  variant = 'default',
  className
}) => {
  const config = BATCH_STATUS_CONFIG[status]
  const sizeConfig = SIZE_CONFIG[size]
  
  if (!config) {
    console.warn(`Unknown batch status: ${status}`)
    return null
  }

  const Icon = config.icon

  // Use custom colors for solid variant, otherwise use badge variants
  const badgeClass = variant === 'solid' 
    ? cn(
        'inline-flex items-center gap-1.5 font-medium border rounded-full',
        `${config.color.bg} ${config.color.text} ${config.color.border}`,
        sizeConfig.text,
        sizeConfig.padding,
        className
      )
    : undefined

  return variant === 'solid' ? (
    <span className={badgeClass}>
      <Icon className={sizeConfig.icon} />
      {config.label}
    </span>
  ) : (
    <Badge 
      variant="outline"
      className={cn(
        'inline-flex items-center gap-1.5',
        `${config.color.bg} ${config.color.text} ${config.color.border}`,
        sizeConfig.text,
        sizeConfig.padding,
        className
      )}
    >
      <Icon className={sizeConfig.icon} />
      {config.label}
    </Badge>
  )
}

// Utility function to get status color for external use
export const getBatchStatusColor = (status: BatchStatus): string => {
  return getStatusColor(status)
}

// Utility function to get status label for external use
export const getBatchStatusLabel = (status: BatchStatus): string => {
  return getStatusLabel(status)
}

// Utility function to get status icon for external use
export const getBatchStatusIcon = (status: BatchStatus) => {
  return BATCH_STATUS_CONFIG[status]?.icon
} 