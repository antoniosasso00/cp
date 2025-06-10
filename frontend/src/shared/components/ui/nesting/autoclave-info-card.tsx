'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Thermometer, Gauge, Ruler, Package } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { EfficiencyMeter } from './efficiency-meter'
import type { AutoclaveInfoCardProps } from './types'

export const AutoclaveInfoCard: React.FC<AutoclaveInfoCardProps> = ({
  autoclave,
  efficiency,
  metrics,
  className
}) => {
  // Calculate dimensions
  const areaMm2 = autoclave.lunghezza * autoclave.larghezza_piano
  const areaCm2 = (areaMm2 / 100).toFixed(0)
  const areaM2 = (areaMm2 / 1000000).toFixed(2)

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            {autoclave.nome}
          </CardTitle>
          <Badge variant="outline" className="font-mono text-xs">
            {autoclave.codice}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Efficiency */}
        {efficiency !== undefined && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Efficienza</h4>
            <EfficiencyMeter percentage={efficiency} size="md" showLabel />
          </div>
        )}

        {/* Dimensions */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1">
            <Ruler className="h-4 w-4" />
            Dimensioni Piano
          </h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">Lunghezza:</span>
              <p className="font-mono">{autoclave.lunghezza.toLocaleString()} mm</p>
            </div>
            <div>
              <span className="text-muted-foreground">Larghezza:</span>
              <p className="font-mono">{autoclave.larghezza_piano.toLocaleString()} mm</p>
            </div>
          </div>
          <div className="pt-1">
            <span className="text-muted-foreground text-sm">Area totale:</span>
            <p className="font-mono text-sm">
              {areaCm2} cm² ({areaM2} m²)
            </p>
          </div>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Statistiche Batch</h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {metrics.total_tools !== undefined && (
                <div className="flex items-center gap-1">
                  <Package className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">Tool:</span>
                  <span className="font-mono">{metrics.total_tools}</span>
                </div>
              )}
              
              {metrics.total_weight !== undefined && metrics.total_weight > 0 && (
                <div>
                  <span className="text-muted-foreground">Peso:</span>
                  <p className="font-mono">{metrics.total_weight.toFixed(1)} kg</p>
                </div>
              )}
              
              {metrics.utilized_area !== undefined && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Area utilizzata:</span>
                  <p className="font-mono">{(metrics.utilized_area / 100).toFixed(0)} cm²</p>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Compact version
export const CompactAutoclaveInfoCard: React.FC<AutoclaveInfoCardProps> = ({
  autoclave,
  efficiency,
  className
}) => {
  return (
    <div className={cn(
      'p-3 border rounded-lg bg-card space-y-2',
      className
    )}>
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">{autoclave.nome}</h3>
        <Badge variant="outline" className="text-xs font-mono">
          {autoclave.codice}
        </Badge>
      </div>
      
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-mono">
          {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
        </span>
        {efficiency !== undefined && (
          <span className="font-mono font-semibold">
            {efficiency.toFixed(1)}%
          </span>
        )}
      </div>
      
      {efficiency !== undefined && (
        <EfficiencyMeter 
          percentage={efficiency} 
          size="sm" 
          showLabel={false}
          className="mt-2"
        />
      )}
    </div>
  )
}

// Header version for canvas display
export const AutoclaveHeader: React.FC<{
  autoclave: AutoclaveInfoCardProps['autoclave']
  efficiency?: number
  className?: string
}> = ({ autoclave, efficiency, className }) => {
  const getEfficiencyColor = (eff: number) => {
    if (eff >= 85) return 'text-green-700 bg-green-100'
    if (eff >= 70) return 'text-blue-700 bg-blue-100' 
    if (eff >= 50) return 'text-yellow-700 bg-yellow-100'
    if (eff >= 30) return 'text-orange-700 bg-orange-100'
    return 'text-red-700 bg-red-100'
  }

  return (
    <div className={cn(
      'flex items-center justify-between p-3 bg-white border-b',
      className
    )}>
      <div className="flex items-center gap-3">
        <div>
          <h2 className="font-semibold text-lg">{autoclave.nome}</h2>
          <p className="text-sm text-muted-foreground font-mono">
            {autoclave.lunghezza} × {autoclave.larghezza_piano} mm
          </p>
        </div>
        <Badge variant="outline" className="font-mono">
          {autoclave.codice}
        </Badge>
      </div>
      
      {efficiency !== undefined && (
        <div className={cn(
          'px-3 py-1 rounded-full font-mono font-semibold text-sm',
          getEfficiencyColor(efficiency)
        )}>
          {efficiency.toFixed(1)}%
        </div>
      )}
    </div>
  )
} 