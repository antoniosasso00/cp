'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card'
import { Badge } from '@/shared/components/ui/badge'
import { cn } from '@/shared/lib/utils'
import { LucideIcon } from 'lucide-react'

export interface MetricCardProps {
  /** Titolo della metrica */
  title: string
  /** Valore principale della metrica */
  value: string | number
  /** Descrizione o sottotitolo opzionale */
  description?: string
  /** Icona della metrica */
  icon?: LucideIcon
  /** Colore/variant per il badge di stato */
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
  /** Badge di stato opzionale */
  badge?: string
  /** Trend o cambio percentuale */
  trend?: {
    value: number
    label?: string
  }
  /** Click handler */
  onClick?: () => void
  /** Classname aggiuntive */
  className?: string
  /** Se la card è selezionata */
  selected?: boolean
  /** Loading state */
  loading?: boolean
  /** Data attributes per testing */
  'data-testid'?: string
  /** Altri attributi HTML */
  [key: string]: any
}

const getVariantStyles = (variant: MetricCardProps['variant']) => {
  switch (variant) {
    case 'success':
      return 'border-green-200 bg-green-50/50 text-green-900'
    case 'warning':
      return 'border-yellow-200 bg-yellow-50/50 text-yellow-900'
    case 'destructive':
      return 'border-red-200 bg-red-50/50 text-red-900'
    default:
      return 'border-border bg-background text-foreground'
  }
}

const getTrendColor = (value: number) => {
  if (value > 0) return 'text-green-600'
  if (value < 0) return 'text-red-600'
  return 'text-muted-foreground'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  variant = 'default',
  badge,
  trend,
  onClick,
  className,
  selected = false,
  loading = false,
  'data-testid': dataTestId,
  ...rest
}) => {
  const cardStyles = cn(
    'transition-all duration-200 hover:shadow-md',
    getVariantStyles(variant),
    selected && 'ring-2 ring-primary shadow-md',
    onClick && 'cursor-pointer hover:scale-[1.02]',
    className
  )

  return (
    <Card className={cardStyles} onClick={onClick} data-testid={dataTestId}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="flex items-center gap-2">
          {badge && (
            <Badge variant={variant === 'default' ? 'secondary' : variant} className="text-xs">
              {badge}
            </Badge>
          )}
          {Icon && (
            <Icon className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-1">
          {loading ? (
            <div className="h-8 w-20 bg-muted animate-pulse rounded" />
          ) : (
            <div className="text-2xl font-bold">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
          )}
          
          <div className="flex items-center gap-2 text-xs">
            {description && (
              <span className="text-muted-foreground">{description}</span>
            )}
            
            {trend && (
              <span className={cn('font-medium', getTrendColor(trend.value))}>
                {trend.value > 0 ? '+' : ''}{trend.value}%
                {trend.label && ` ${trend.label}`}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Variante compatta per dashboard
export const CompactMetricCard: React.FC<Omit<MetricCardProps, 'description'>> = (props) => {
  return (
    <div className={cn(
      'p-3 rounded-lg border transition-colors',
      getVariantStyles(props.variant),
      props.onClick && 'cursor-pointer hover:bg-accent',
      props.className
    )} onClick={props.onClick}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{props.title}</p>
          <p className="text-lg font-semibold">
            {typeof props.value === 'number' ? props.value.toLocaleString() : props.value}
          </p>
        </div>
        {props.icon && <props.icon className="h-4 w-4 text-muted-foreground" />}
      </div>
    </div>
  )
}

export default MetricCard 