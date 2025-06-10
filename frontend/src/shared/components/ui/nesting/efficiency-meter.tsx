'use client'

import React from 'react'
import { Progress } from '@/components/ui/progress'
import { TrendingUp, TrendingDown, Target } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { EfficiencyMeterProps } from './types'

// Efficiency thresholds and colors
const EFFICIENCY_THRESHOLDS = {
  excellent: 85, // >= 85%
  good: 70,      // >= 70%
  average: 50,   // >= 50%
  poor: 30       // >= 30%
  // < 30% = very poor
}

const getEfficiencyLevel = (percentage: number) => {
  if (percentage >= EFFICIENCY_THRESHOLDS.excellent) return 'excellent'
  if (percentage >= EFFICIENCY_THRESHOLDS.good) return 'good'
  if (percentage >= EFFICIENCY_THRESHOLDS.average) return 'average'
  if (percentage >= EFFICIENCY_THRESHOLDS.poor) return 'poor'
  return 'very-poor'
}

const EFFICIENCY_CONFIG = {
  'excellent': {
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    progressColor: 'bg-green-500',
    icon: TrendingUp,
    label: 'Eccellente'
  },
  'good': {
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    progressColor: 'bg-blue-500',
    icon: Target,
    label: 'Buona'
  },
  'average': {
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    progressColor: 'bg-yellow-500',
    icon: Target,
    label: 'Media'
  },
  'poor': {
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    progressColor: 'bg-orange-500',
    icon: TrendingDown,
    label: 'Scarsa'
  },
  'very-poor': {
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    progressColor: 'bg-red-500',
    icon: TrendingDown,
    label: 'Molto Scarsa'
  }
}

const SIZE_CONFIG = {
  sm: {
    container: 'w-24',
    height: 'h-2',
    text: 'text-xs',
    icon: 'h-3 w-3'
  },
  md: {
    container: 'w-32',
    height: 'h-3',
    text: 'text-sm',
    icon: 'h-4 w-4'
  },
  lg: {
    container: 'w-48',
    height: 'h-4',
    text: 'text-base',
    icon: 'h-5 w-5'
  }
}

export const EfficiencyMeter: React.FC<EfficiencyMeterProps> = ({
  percentage,
  size = 'md',
  showLabel = true,
  className
}) => {
  // Clamp percentage between 0 and 100
  const clampedPercentage = Math.max(0, Math.min(100, percentage))
  
  const level = getEfficiencyLevel(clampedPercentage)
  const config = EFFICIENCY_CONFIG[level]
  const sizeConfig = SIZE_CONFIG[size]
  const Icon = config.icon

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Progress Bar */}
      <div className={cn('relative', sizeConfig.container)}>
        <Progress 
          value={clampedPercentage} 
          className={cn(sizeConfig.height, 'bg-gray-200')}
        />
        {/* Custom colored fill overlay */}
        <div 
          className={cn(
            'absolute top-0 left-0 rounded-full transition-all duration-300',
            config.progressColor,
            sizeConfig.height
          )}
          style={{ width: `${clampedPercentage}%` }}
        />
      </div>

      {/* Percentage Text */}
      <span className={cn(
        'font-mono font-semibold tabular-nums',
        config.color,
        sizeConfig.text
      )}>
        {clampedPercentage.toFixed(1)}%
      </span>

      {/* Icon and Label */}
      {showLabel && (
        <div className={cn('flex items-center gap-1', config.bgColor, 'px-2 py-1 rounded-full')}>
          <Icon className={cn(sizeConfig.icon, config.color)} />
          <span className={cn(sizeConfig.text, config.color, 'font-medium')}>
            {config.label}
          </span>
        </div>
      )}
    </div>
  )
}

// Utility function to get efficiency color class for external use
export const getEfficiencyColorClass = (percentage: number): string => {
  const level = getEfficiencyLevel(percentage)
  return EFFICIENCY_CONFIG[level].color
}

// Utility function to get efficiency background color for external use
export const getEfficiencyBgColorClass = (percentage: number): string => {
  const level = getEfficiencyLevel(percentage)
  return EFFICIENCY_CONFIG[level].bgColor
}

// Utility function to get efficiency level label for external use
export const getEfficiencyLabel = (percentage: number): string => {
  const level = getEfficiencyLevel(percentage)
  return EFFICIENCY_CONFIG[level].label
} 