'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StatusCardProps {
  /** Titolo della card */
  title: string;
  /** Valore principale da mostrare */
  value: number;
  /** Icona da mostrare */
  icon: LucideIcon;
  /** Colore del tema (es: 'blue', 'green', 'red', 'yellow') */
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'gray';
  /** Trend giornaliero (Δ today - yesterday) */
  trend?: {
    value: number;
    type: 'increase' | 'decrease' | 'stable';
  };
  /** Callback per il click sulla card */
  onClick?: () => void;
  /** Classe CSS aggiuntiva */
  className?: string;
  /** Mostra come clickable (hover effects) */
  clickable?: boolean;
  /** Descrizione aggiuntiva */
  description?: string;
}

const colorMap = {
  blue: {
    text: 'text-blue-600',
    icon: 'text-blue-500',
    bg: 'bg-blue-50',
    hover: 'hover:bg-blue-100'
  },
  green: {
    text: 'text-green-600',
    icon: 'text-green-500',
    bg: 'bg-green-50',
    hover: 'hover:bg-green-100'
  },
  red: {
    text: 'text-red-600',
    icon: 'text-red-500',
    bg: 'bg-red-50',
    hover: 'hover:bg-red-100'
  },
  yellow: {
    text: 'text-yellow-600',
    icon: 'text-yellow-500',
    bg: 'bg-yellow-50',
    hover: 'hover:bg-yellow-100'
  },
  purple: {
    text: 'text-purple-600',
    icon: 'text-purple-500',
    bg: 'bg-purple-50',
    hover: 'hover:bg-purple-100'
  },
  gray: {
    text: 'text-gray-600',
    icon: 'text-gray-500',
    bg: 'bg-gray-50',
    hover: 'hover:bg-gray-100'
  }
};

const getTrendIcon = (type: 'increase' | 'decrease' | 'stable') => {
  switch (type) {
    case 'increase':
      return TrendingUp;
    case 'decrease':
      return TrendingDown;
    case 'stable':
    default:
      return Minus;
  }
};

const getTrendColor = (type: 'increase' | 'decrease' | 'stable') => {
  switch (type) {
    case 'increase':
      return 'text-green-600';
    case 'decrease':
      return 'text-red-600';
    case 'stable':
    default:
      return 'text-gray-600';
  }
};

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  icon: Icon,
  color = 'blue',
  trend,
  onClick,
  className,
  clickable = !!onClick,
  description
}) => {
  const colorClasses = colorMap[color];
  const TrendIcon = trend ? getTrendIcon(trend.type) : null;
  const trendColor = trend ? getTrendColor(trend.type) : '';

  return (
    <Card 
      className={cn(
        'relative overflow-hidden',
        clickable && 'cursor-pointer transition-all duration-200 hover:shadow-md',
        clickable && colorClasses.hover,
        className
      )}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>
            <div className="flex items-center gap-2">
              <p className={cn("text-2xl font-bold", colorClasses.text)}>
                {value.toLocaleString()}
              </p>
              {trend && (
                <Badge variant="outline" className="flex items-center gap-1">
                  {TrendIcon && <TrendIcon className={cn("h-3 w-3", trendColor)} />}
                  <span className={cn("text-xs", trendColor)}>
                    {trend.value > 0 && '+'}
                    {trend.value}
                  </span>
                </Badge>
              )}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground">
                {description}
              </p>
            )}
          </div>
          <div className={cn("p-2 rounded-full", colorClasses.bg)}>
            <Icon className={cn("h-6 w-6", colorClasses.icon)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Componente helper per creare cards con stati batch predefiniti
import { Activity, Clock, CheckCircle, Package, Flame, ClipboardCheck } from 'lucide-react';

export const BatchStatusCard: React.FC<
  Omit<StatusCardProps, 'color' | 'icon'> & {
    status: 'total' | 'sospeso' | 'confermato' | 'loaded' | 'cured' | 'completato';
  }
> = ({ status, ...props }) => {
  const statusConfig = {
    total: { color: 'blue' as const, icon: Activity },
    sospeso: { color: 'yellow' as const, icon: Clock },
    confermato: { color: 'green' as const, icon: CheckCircle },
    loaded: { color: 'purple' as const, icon: Package },
    cured: { color: 'red' as const, icon: Flame },
    completato: { color: 'gray' as const, icon: ClipboardCheck }
  };

  const config = statusConfig[status];

  return (
    <StatusCard
      {...props}
      color={config.color}
      icon={config.icon}
    />
  );
}; 